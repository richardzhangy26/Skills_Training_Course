"""网易易盾（Yidun）滑块验证码自动破解模块。

适用：智慧树 / hike-teaching-center 登录页弹出的 "向右拖动滑块填充拼图"（yidun v2/v3）。

依赖：playwright, opencv-python, numpy

用法（Playwright 同步 API）：
    from yidun_slider import solve_yidun
    ok = solve_yidun(page, max_retry=4)

实现要点（实测调过的部分）：
1. 几何：`.yidun_jigsaw` 的<img>与`.yidun_bg-img`左上角对齐，且两图同比例 2x（480x240 -> 400x200）。
   所以 **y 是已知的**，只需要解 x；拖动距离 = (缺口x_native - 拼图内容内边距) * (cssWidth / nativeWidth)。
2. 缺口定位用三路投票（yidun 的背景图会把拼图区域做成"灰色半透明遮罩"）：
   - edge：拼图 alpha 轮廓 vs 背景 Canny 的相关 → 抓形状
   - fog ：缺口=低对比+去饱和+往中灰靠拢 → 抓遮罩特征
   - content：拼图内容 vs 背景的 masked CCOEFF_NORMED → 抓像素
   两路接近取均值；三路都分歧时信 edge。
3. 轨迹：加速段 -> 巡航抖动 -> 减速 -> 过冲回拉，40~80 个点，总时长 ~0.8-1.5s，y ±1px。
4. 结果判定优先读 `api/v3/check` 的 result 字段（最可靠），DOM class 作兜底。
"""

from __future__ import annotations

import base64
import random
import time
from typing import Any

import cv2
import numpy as np

SEL_BG = ".yidun_bg-img, .yidun_bg"
SEL_PIECE = ".yidun_jigsaw"
SEL_SLIDER = ".yidun_slider"
SEL_SLIDER_ICON = ".yidun_slider__icon, .yidun_slider"
SEL_REFRESH = ".yidun_refresh"
SEL_POPUP = ".yidun_popup, .yidun_popup--light"


# ============================ 1. 缺口定位 ============================

def _piece_parts(piece_bgra: np.ndarray):
    if piece_bgra.ndim == 2:
        piece_bgra = cv2.cvtColor(piece_bgra, cv2.COLOR_GRAY2BGRA)
    if piece_bgra.shape[2] == 4:
        alpha = piece_bgra[:, :, 3]
        ys, xs = np.where(alpha > 16)
        if len(xs):
            x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
            tpl = piece_bgra[y0:y1 + 1, x0:x1 + 1, :3]
            msk = (alpha[y0:y1 + 1, x0:x1 + 1] > 16).astype(np.uint8) * 255
            return tpl, msk, (x0, y0, x1, y1)
    tpl = piece_bgra[:, :, :3]
    return tpl, np.full(tpl.shape[:2], 255, np.uint8), (0, 0, tpl.shape[1] - 1, tpl.shape[0] - 1)


def _score_fog(bg_gray: np.ndarray, sat: np.ndarray, msk: np.ndarray, box) -> tuple[int, float]:
    """缺口特征：对比度下降 + 去饱和 + 亮度往中灰(128)靠拢。返回 (x, score)。"""
    x0, y0, x1, y1 = box
    h, w = msk.shape
    ring = cv2.dilate(msk, np.ones((9, 9), np.uint8)) - msk
    best_x, best_s = 0, -1e9
    prof = []
    for x in range(bg_gray.shape[1] - w + 1):
        gi = bg_gray[y0:y1 + 1, x:x + w]
        si = sat[y0:y1 + 1, x:x + w]
        mi = gi[msk > 0]
        mr = gi[ring > 0]
        ms = si[msk > 0]
        sr = si[ring > 0]
        s = ((abs(float(mr.mean()) - 128) - abs(float(mi.mean()) - 128)) / 50.0
             + (float(mr.std()) - float(mi.std())) / 20.0
             + (float(sr.mean()) - float(ms.mean())) / 50.0)
        prof.append(s)
    prof = np.asarray(prof, dtype=np.float32)
    prof = np.convolve(prof, np.ones(3) / 3, mode="same")
    best_x = int(prof.argmax())
    best_s = float(prof[best_x])
    return best_x, best_s


def _score_edge(bg_gray: np.ndarray, msk: np.ndarray, box) -> tuple[int, float]:
    x0, y0, x1, y1 = box
    outline = cv2.subtract(msk, cv2.erode(msk, np.ones((2, 2), np.uint8)))
    outline = cv2.dilate(outline, np.ones((3, 3), np.uint8))
    band = bg_gray[y0:y1 + 1, :]
    e = cv2.Canny(cv2.GaussianBlur(band, (3, 3), 0), 40, 120)
    e = cv2.dilate(e, np.ones((2, 2), np.uint8))
    r = cv2.matchTemplate(e, outline, cv2.TM_CCORR_NORMED, mask=outline)
    r = np.nan_to_num(r, nan=-1, posinf=-1, neginf=-1)
    _, s, _, loc = cv2.minMaxLoc(r)
    return int(loc[0]), float(s)


def _score_content(bg_gray: np.ndarray, tpl: np.ndarray, msk: np.ndarray, box) -> tuple[int, float]:
    x0, y0, x1, y1 = box
    band = bg_gray[y0:y1 + 1, :]
    gt = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
    r = cv2.matchTemplate(band, gt, cv2.TM_CCOEFF_NORMED, mask=msk)
    r = np.nan_to_num(r, nan=-1, posinf=-1, neginf=-1)
    _, s, _, loc = cv2.minMaxLoc(r)
    return int(loc[0]), float(s)


def detect_gap(bg_bgr: np.ndarray, piece_bgra: np.ndarray) -> dict[str, Any]:
    tpl, msk, box = _piece_parts(piece_bgra)
    if msk.sum() == 0:
        raise RuntimeError("前景图 alpha 全透明")
    x0, y0, x1, y1 = box
    g = cv2.cvtColor(bg_bgr, cv2.COLOR_BGR2GRAY)
    sat = cv2.cvtColor(bg_bgr, cv2.COLOR_BGR2HSV)[:, :, 1]

    ex, es = _score_edge(g, msk, box)
    fx, fs = _score_fog(g, sat, msk, box)
    cx, cs = _score_content(g, tpl, msk, box)

    pairs = [("edge", ex), ("fog", fx), ("content", cx)]
    best = None
    for i in range(3):
        for j in range(i + 1, 3):
            if abs(pairs[i][1] - pairs[j][1]) <= 6:
                best = (pairs[i][1] + pairs[j][1]) / 2.0
                src = f"{pairs[i][0]}+{pairs[j][0]}"
                break
        if best is not None:
            break
    if best is None:
        best = float(ex)          # 三路分歧：以形状(edge)为准
        src = "edge(fallback)"

    return {
        "native_x": int(round(best)),
        "piece_off": x0,
        "piece_box": box,
        "bg_size": (int(bg_bgr.shape[1]), int(bg_bgr.shape[0])),
        "cand": {"edge": ex, "fog": fx, "content": cx},
        "score": {"edge": round(es, 3), "fog": round(fs, 3), "content": round(cs, 3)},
        "picked": src,
    }


def _fetch_image(page, selector: str) -> np.ndarray | None:
    try:
        loc = page.locator(selector).first
        if not loc.count():
            return None
        src = loc.evaluate(
            "el => el.tagName === 'CANVAS' ? el.toDataURL('image/png') : (el.currentSrc || el.src || '')"
        )
    except Exception:
        return None
    if not src:
        return None
    if src.startswith("data:"):
        raw = base64.b64decode(src.split(",", 1)[1])
    else:
        try:
            raw = page.request.get(src, timeout=15000).body()
        except Exception:
            raw = loc.screenshot()
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_UNCHANGED)


# ============================ 2. 轨迹生成 ============================

def build_track(distance: float, rng: random.Random | None = None) -> list[tuple[float, float, float]]:
    rng = rng or random.Random()
    track: list[tuple[float, float, float]] = []
    cur = 0.0
    t_acc = rng.randint(10, 18)
    t_dec = rng.randint(6, 10)
    overshoot = rng.uniform(1.5, 4.0)
    total = distance + overshoot

    for i in range(1, t_acc + 1):
        p = i / t_acc
        cur += (total * 0.62) / t_acc * (0.45 + 0.55 * p) * rng.uniform(0.92, 1.08)
        track.append((cur, rng.uniform(-0.6, 0.6), rng.uniform(0.010, 0.020)))

    while cur < total - max(6.0, total * 0.12):
        cur += rng.uniform(3.0, 6.0)
        track.append((cur, rng.uniform(-0.9, 0.9), rng.uniform(0.012, 0.024)))

    remaining = total - cur
    for i in range(1, t_dec + 1):
        cur += remaining * (1 / t_dec) * rng.uniform(0.85, 1.15)
        track.append((cur, rng.uniform(-0.5, 0.5), rng.uniform(0.022, 0.045)))

    track.append((distance + rng.uniform(1.0, 2.5), rng.uniform(-0.4, 0.4), rng.uniform(0.03, 0.06)))
    track.append((distance + rng.uniform(0.0, 0.6), 0.0, rng.uniform(0.02, 0.04)))
    track.append((distance, 0.0, rng.uniform(0.05, 0.09)))
    return track


JS_PIECE_X = """() => {
    const j = document.querySelector('.yidun_jigsaw');
    const b = document.querySelector('.yidun_bg-img, .yidun_bg');
    if (!j || !b) return null;
    return {jig: j.getBoundingClientRect().x, bg: b.getBoundingClientRect().x};
}"""


def _piece_delta(page) -> float | None:
    """拼图元素相对背景原点的水平位移（css px）。"""
    try:
        d = page.evaluate(JS_PIECE_X)
    except Exception:
        return None
    if not d:
        return None
    return float(d["jig"]) - float(d["bg"])


def _drag(page, sx: float, sy: float, target_piece_dx: float, rng: random.Random,
          verbose: bool = False) -> float:
    """把拼图推进 target_piece_dx(css px)，返回手柄实际行程。

    实测规律（智慧树登录页 yidun v3）：拼图不跟手柄 1:1，
        piece_left = knob_dx - DEAD_ZONE      (DEAD_ZONE ≈ 18px，来自手柄内边距)
    所以先按住走一小段标定 DEAD_ZONE，再补足剩余距离。
    """
    page.mouse.move(sx, sy)
    time.sleep(rng.uniform(0.08, 0.15))
    page.mouse.down()
    time.sleep(rng.uniform(0.10, 0.20))

    base = _piece_delta(page) or 0.0
    d0 = rng.uniform(26.0, 34.0)
    for i in range(1, 6):
        page.mouse.move(sx + d0 * i / 5, sy + rng.uniform(-0.4, 0.4))
        time.sleep(rng.uniform(0.014, 0.024))
    # 等动画/回写稳定后读两次，取较大值（位移单调）
    moved = 0.0
    for _ in range(3):
        time.sleep(0.15)
        cur = _piece_delta(page)
        if cur is not None:
            moved = max(moved, cur - base)
    dead = max(0.0, d0 - moved)
    total = max(target_piece_dx, 0.0) + dead
    if verbose:
        print(f"  [yidun] 标定: d0={d0:.1f} 拼图位移={moved:.1f} 死区={dead:.1f} "
              f"=> 手柄总行程={total:.1f}")

    for dx, dy, dt in build_track(total, rng):
        if dx <= d0:
            continue
        page.mouse.move(sx + dx, sy + dy)
        time.sleep(dt)
    time.sleep(rng.uniform(0.18, 0.30))
    page.mouse.up()
    return total


# ============================ 3. 判定与主流程 ============================

def _dom_state(page) -> str:
    try:
        st = page.evaluate(
            """() => {
                const p = document.querySelector('.yidun_popup, .yidun_popup--light');
                const c = document.querySelector('.yidun_control');
                return {
                    popup: p ? p.className : '',
                    control: c ? c.className : '',
                    tips: (document.querySelector('.yidun_tips__text') || {}).textContent || '',
                    visible: !!(p && p.offsetParent !== null)
                };
            }"""
        )
    except Exception:
        return "pending"
    cls = f"{st.get('popup','')} {st.get('control','')}"
    if "success" in cls:
        return "success"
    tips = str(st.get("tips", ""))
    if any(k in tips for k in ("失败", "重试", "异常")):
        return "fail"
    if not st.get("visible"):
        return "closed"
    return "pending"


def solve_yidun(page, max_retry: int = 4, verbose: bool = True, wait_net: bool = True) -> bool:
    """完成滑块。返回 True = 服务端 check 通过（或组件已消失）。"""
    verdict: dict[str, Any] = {"result": None}

    def on_resp(resp):
        if "dun.163.com" in resp.url and "/check" in resp.url:
            try:
                body = resp.text()
            except Exception:
                return
            if '"result":true' in body:
                verdict["result"] = True
            elif '"result":false' in body:
                verdict["result"] = False

    try:
        page.on("response", on_resp)
    except Exception:
        wait_net = False

    for attempt in range(1, max_retry + 1):
        rng = random.Random()
        try:
            page.wait_for_selector(SEL_BG, state="visible", timeout=15000)
        except Exception:
            if verbose:
                print("  [yidun] 无滑块组件（可能已通过/无需验证）")
            return True
        time.sleep(rng.uniform(0.5, 1.0))

        bg = _fetch_image(page, SEL_BG)
        piece = _fetch_image(page, SEL_PIECE)
        if bg is None or piece is None:
            if verbose:
                print("  [yidun] 取图失败")
            return False

        info = detect_gap(bg, piece)
        try:
            bg_box = page.locator(SEL_BG).first.bounding_box()
            scale = bg_box["width"] / info["bg_size"][0] if bg_box else 1.0
        except Exception:
            scale = 1.0
        piece_dx = (info["native_x"] - info["piece_off"]) * scale

        if verbose:
            print(f"  [yidun] #{attempt} 缺口={info['native_x']}(native/{info['bg_size'][0]}) "
                  f"三路={info['cand']} 选中={info['picked']} "
                  f"内边距={info['piece_off']} scale={scale:.3f} => 拼图需移动 {piece_dx:.1f}px(css)")
        if piece_dx <= 3:
            _refresh(page)
            continue

        try:
            box = page.locator(SEL_SLIDER).first.bounding_box() or \
                  page.locator(SEL_SLIDER_ICON).first.bounding_box()
        except Exception:
            box = None
        if not box:
            if verbose:
                print("  [yidun] 找不到手柄")
            return False

        verdict["result"] = None
        knob = _drag(page, box["x"] + box["width"] / 2, box["y"] + box["height"] / 2,
                     piece_dx, rng, verbose=verbose)
        if verbose:
            print(f"  [yidun] 手柄位移={knob:.1f}px")

        ok = False
        deadline = time.time() + 6
        while time.time() < deadline:
            if verdict["result"] is True:
                ok = True
                break
            if verdict["result"] is False:
                break
            if _dom_state(page) == "success":
                ok = True
                break
            time.sleep(0.1)

        if ok:
            if verbose:
                print("  [yidun] ✓ 验证通过")
            return True
        if verbose:
            print(f"  [yidun] ✗ 未通过 (check={verdict['result']})")
        if attempt < max_retry:
            _refresh(page)
            time.sleep(rng.uniform(0.7, 1.3))
    return False


def _refresh(page) -> None:
    try:
        page.locator(SEL_REFRESH).first.click(timeout=3000)
    except Exception:
        pass


def captcha_visible(page) -> bool:
    try:
        loc = page.locator(SEL_BG).first
        return bool(loc.count() and loc.is_visible())
    except Exception:
        return False


if __name__ == "__main__":
    import sys
    bg = cv2.imread(sys.argv[1])
    piece = cv2.imread(sys.argv[2], cv2.IMREAD_UNCHANGED)
    print(detect_gap(bg, piece))
