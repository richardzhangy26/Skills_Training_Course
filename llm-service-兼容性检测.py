#!/usr/bin/env python3
"""
llm-service 网关 OpenAI 兼容性检测

检测两个问题：
  1) 流式响应使用 choices[].message 而非 OpenAI 标准的 choices[].delta
  2) usage 里的 token 计数是 JSON 字符串而非 number

用法：
    LLM_API_KEY=sk-xxx python3 llm-service-兼容性检测.py
    # 或从同目录 .env 读取 LLM_API_KEY
    python3 llm-service-兼容性检测.py --base-url http://llm-service.polymas.com/api/openai/v1

退出码：0 = 两个问题都不存在；1 = 至少一个问题存在
无第三方依赖（仅标准库）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

DEFAULT_BASE = "http://llm-service.polymas.com/api/openai/v1"
DEFAULT_MODELS = [
    "claude-opus-5", "claude-opus-4-8", "claude-sonnet-5",
    "gpt-5.6-sol", "gpt-5.5", "gpt-5.4",
    "deepseek-v4-pro", "deepseek-v4.1-flash",
    "kimi-k3", "glm-5.2", "qwen3.8-max",
    "gemini-3.1-pro-preview", "gemini-3.0", "grok-4",
    "Doubao-Seed-2.1-pro", "Doubao-Seed-2.0-Code",
]

PROMPT = "Reply with exactly one word: PONG"
NUMERIC_KEYS = ("prompt_tokens", "completion_tokens", "total_tokens")


def load_key(explicit: str | None) -> str:
    if explicit:
        return explicit
    key = os.environ.get("LLM_API_KEY")
    if key:
        return key
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            m = re.match(r"\s*LLM_API_KEY\s*=\s*(\S+)", line)
            if m:
                return m.group(1)
    sys.exit("找不到 API key：请设置 LLM_API_KEY 环境变量，或用 --api-key 传入。")


def post(url: str, key: str, body: dict, timeout: int = 120) -> str:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def parse_sse(raw: str) -> list[dict]:
    out = []
    for line in raw.splitlines():
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload in ("", "[DONE]"):
            continue
        try:
            out.append(json.loads(payload))
        except json.JSONDecodeError:
            pass
    return out


def probe_stream(url: str, key: str, model: str) -> dict:
    """发一次流式请求，报告用的是 delta 还是 message、内容、usage 类型。"""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 32,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    try:
        raw = post(url, key, body)
    except urllib.error.HTTPError as exc:
        return {"model": model, "error": f"HTTP {exc.code}: {exc.read()[:200].decode('utf-8','replace')}"}
    except Exception as exc:  # noqa: BLE001
        return {"model": model, "error": f"{type(exc).__name__}: {exc}"}

    chunks = parse_sse(raw)
    uses_delta = uses_message = False
    text = ""
    usage_values: dict[str, object] = {}
    for chunk in chunks:
        for choice in chunk.get("choices") or []:
            if "delta" in choice:
                uses_delta = True
                text += (choice["delta"] or {}).get("content") or ""
            if "message" in choice:
                uses_message = True
                text += (choice["message"] or {}).get("content") or ""
            if choice.get("finish_reason"):
                pass
        if chunk.get("usage"):
            usage_values = chunk["usage"]
    return {
        "model": model,
        "uses_delta": uses_delta,
        "uses_message": uses_message,
        "text": text[:40],
        "usage": usage_values,
        "string_usage": [k for k in NUMERIC_KEYS if isinstance(usage_values.get(k), str)],
    }


def probe_tool_call_stream(url: str, key: str, model: str) -> dict:
    """工具调用场景：delta 还是 message。"""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "What is the weather in Beijing? Use the tool."}],
        "max_tokens": 128,
        "stream": True,
        "tools": [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
            },
        }],
    }
    try:
        chunks = parse_sse(post(url, key, body))
    except Exception as exc:  # noqa: BLE001
        return {"model": model, "error": str(exc)[:120]}
    delta_tc = msg_tc = False
    for chunk in chunks:
        for choice in chunk.get("choices") or []:
            if "delta" in choice and (choice["delta"] or {}).get("tool_calls"):
                delta_tc = True
            if "message" in choice and (choice["message"] or {}).get("tool_calls"):
                msg_tc = True
    return {"model": model, "delta_tool_calls": delta_tc, "message_tool_calls": msg_tc}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.environ.get("LLM_API_BASE", DEFAULT_BASE))
    ap.add_argument("--api-key")
    ap.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    args = ap.parse_args()

    key = load_key(args.api_key)
    url = args.base_url.rstrip("/") + "/chat/completions"
    print(f"网关: {url}")
    print(f"模型: {len(args.models)} 个\n")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda m: probe_stream(url, key, m), args.models))

    print("【问题 1】流式字段：delta（标准） vs message（非标准）")
    print(f"{'model':28} {'delta':>7} {'message':>9}  文本           usage 类型")
    bug1 = []
    for r in results:
        if r.get("error"):
            print(f"{r['model']:28} {'-':>7} {'-':>9}  {r['error'][:40]}")
            continue
        bad = r["uses_message"] and not r["uses_delta"]
        if bad:
            bug1.append(r["model"])
        usage_kind = "字符串 ✗" if r["string_usage"] else "number ✓"
        print(f"{r['model']:28} {str(r['uses_delta']):>7} {str(r['uses_message']):>9}  {r['text'][:12]!r:14} {usage_kind}")

    print("\n【问题 2】usage 计数类型")
    bug2 = sorted({m for r in results if r.get("string_usage") for m in [r["model"]]})
    print(f"  返回字符串计数的模型: {len(bug2)}/{len(results)}")
    sample = next((r for r in results if r.get("usage")), None)
    if sample:
        print(f"  实际报文: {json.dumps(sample['usage'], ensure_ascii=False)}")
        print( '  期望报文: ' + json.dumps({k: int(v) if str(v).lstrip("-").isdigit() else v for k, v in sample["usage"].items()}))

    print("\n【工具调用流式字段】")
    with ThreadPoolExecutor(max_workers=4) as pool:
        tcs = list(pool.map(lambda m: probe_tool_call_stream(url, key, m), args.models[:4]))
    for r in tcs:
        if r.get("error"):
            print(f"  {r['model']:28} {r['error'][:50]}")
        else:
            flag = "非标准 ✗" if r["message_tool_calls"] and not r["delta_tool_calls"] else "标准 ✓"
            print(f"  {r['model']:28} delta={r['delta_tool_calls']} message={r['message_tool_calls']}  {flag}")

    print("\n【非流式对照】")
    try:
        raw = post(url, key, {"model": args.models[0], "messages": [{"role": "user", "content": PROMPT}], "max_tokens": 32})
        obj = json.loads(raw)
        msg = (obj.get("choices") or [{}])[0].get("message") or {}
        print(f"  非流式 content = {msg.get('content')!r}   （非流式是标准形态，正常）")
        print(f"  非流式 usage   = {json.dumps(obj.get('usage'), ensure_ascii=False)}")
    except Exception as exc:  # noqa: BLE001
        print(f"  非流式请求失败: {exc}")

    print("\n" + "=" * 72)
    if bug1:
        print(f"结论：阻塞性问题存在 —— {len(bug1)}/{len(results)} 个模型的流式响应使用 message 而非 delta。")
        print("      任何按 OpenAI 规范解析流式的客户端都拿不到内容（表现为空响应/EMPTY_RESPONSE）。")
    else:
        print("结论：流式字段符合 OpenAI 规范。")
    if bug2:
        print(f"      另：{len(bug2)}/{len(results)} 个模型的 usage 计数为字符串，客户端累加会变成字符串拼接。")
    print("=" * 72)
    return 1 if (bug1 or bug2) else 0


if __name__ == "__main__":
    sys.exit(main())
