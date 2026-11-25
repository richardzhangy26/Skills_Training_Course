# 任務佇列與 Router／Worker 流水線 實施計劃

> **給執行的 agent：** 逐個任務執行，每個任務做完先跑它的驗證步驟再往下。確定性邏輯一律先寫測試。

**設計文檔：** `docs/superpowers/specs/2026-11-10-agent-task-queue-design.md`

**Goal：** 交付第一階段（中段）：私有任務 repo、`task_queue.py`、Router skill、Worker 指令模板，並用一張真實的能力訓練任務驗收。第二階段（Codex「拉任務」）在第一階段驗收後做。

**Architecture：** GitHub issue 是唯一的事實來源。`task_queue.py` 承擔所有確定性操作（狀態流轉、門禁、發布、看板）。Router 和 Worker 是提示詞驅動的 agent，只透過這個腳本改狀態和發布。

**Tech Stack：** Python 3 標準庫、`gh` CLI、pytest、herdr、Playwright（僅課程檢索，複用已有登入態）。

## Global Constraints

- 所有 `gh` 命令顯式帶 `-R richardzhangy26/agent-task-queue`。執行前確認當前帳號是 `richardzhangy26`。
- issue、留言和日誌裡不出現密鑰、token、學生樣本和原件內容。
- 不讀寫根 `.env`。憑證只經環境變數注入。
- 不觸發登入流程。只用 `--list-sessions`、`--export-env` 和已存的 storage_state。
- 改動工作樹裡已有未提交修改的檔案前，先看 `git diff`，只做最小改動，不重排格式。
- 不做 git commit，除非用戶明確要求。
- 寫 GitHub 的操作串行執行，間隔至少 1 秒。
- 腳本的 stdout 只輸出 JSON；拒絕執行時退出碼非 0。

---

## 第一階段：中段

### Task 1: 私有 repo、標籤與看板

**Files:**
- Create: `.claude/skills/task-router/scripts/task_queue.py`（本任務只做 `init` 子命令）

**Interfaces:**
- `gh repo create richardzhangy26/agent-task-queue --private`（一次性，手動執行）
- `task_queue.py init`：建 12 個標籤，建標題為「看板」的 issue 並置頂。可重複執行，已存在就跳過。

- [ ] **Step 1:** 確認 `gh auth status` 的當前帳號。
- [ ] **Step 2:** 建私有 repo。這是第一個對外動作。
- [ ] **Step 3:** 實作並執行 `init`。
- [ ] **驗證:** `gh repo view --json visibility` 回傳 `PRIVATE`；`gh label list` 有 12 個標籤；看板 issue 已置頂；再跑一次 `init` 沒有重複項。

### Task 2: `task_queue.py` 的純函式與單元測試

**Files:**
- Modify: `.claude/skills/task-router/scripts/task_queue.py`
- Create: `tests/test_task_queue.py`

**Interfaces:**
- `dedup_key(school_course, biz_type, assigner, date) -> str`：全角和半角括號、空格視為相同。
- `parse_task_book(body) -> dict`：取出防重複鍵、本機目錄、DDL 等欄位。
- `recompute_total(report) -> int`：`dimensions[].score` 相加。
- `gate(good_report, medium_report) -> {"pass": bool, "scores": {...}, "reasons": [...]}`
- `check_transition(labels, event) -> None`：不合法的流轉拋出例外。
- `render_board(issues, today) -> str`

- [ ] **Step 1:** 先寫測試：
  - 門禁：兩份都 ≥80 通過；恰好 80 通過；任一份 <80 不通過；`total_score` 與重算不一致時以重算為準；一票否決不通過；報告缺失或解析失敗不通過。
  - 流轉：設計文檔狀態表裡的每一條都允許；表外的都拒絕（例如從 `status:in-progress` 直接到 `status:ready`）。
  - 看板：五個區塊齊全；DDL 升序；剩餘天數和逾期標示正確。
  - 任務書解析和防重複鍵的正規化。
- [ ] **Step 2:** 跑 `python3 -m pytest -q tests/test_task_queue.py`，確認因函式不存在而失敗。
- [ ] **Step 3:** 實作，不發網路請求。
- [ ] **驗證:** 定向測試全部通過。

### Task 3: `task_queue.py` 的 GitHub 操作

**Files:**
- Modify: `.claude/skills/task-router/scripts/task_queue.py`
- Modify: `tests/test_task_queue.py`

**Interfaces:**
```
task_queue.py find-dup --key <key>
task_queue.py list-ready
task_queue.py claim <N> --agent <kind> --pane <name>
task_queue.py record <N> --set key=value ...
task_queue.py gate <N>
task_queue.py set-status <N> <waiting|blocked|ready> --comment-file <path>
task_queue.py board
```
- 運行記錄寫在 `<本機目錄>/.task-queue/run-<N>.json`：TASK_ID、COURSE_ID、劇本路徑、兩份對話和兩份評測報告的路徑、門禁結果、重做輪次。
- `gate` 的留言固定以一行開頭：`GATE: PASS good=88 medium=83` 或 `GATE: FAIL …`。
- `claim` 遇到已有 `status:*` 的 issue 時拒絕。

- [ ] **Step 1:** 先寫測試，用假的 `gh` 執行器注入，不連網路。覆蓋：`claim` 的拒絕條件、`set-status` 走 `check_transition`、`list-ready` 的篩選。
- [ ] **Step 2:** 實作。
- [ ] **驗證:** 單元測試通過。再對真實 repo 做一次冒煙：建一張測試 issue，依序 `claim`、`set-status blocked`、`board`，核對標籤和看板，然後關閉它。

### Task 4: 禁止回寫根 `.env` 的開關

**Files:**
- Modify: `.claude/skills/training-deploy-and-test/scripts/run_pipeline.py`（`write_task_id_to_env`）
- Modify: `skill_training_build/create_configuration_from_markdown.py`（`write_root_task_id`）
- Modify: `skill_training_build/test/test_create_configuration_from_markdown.py`
- Create: `tests/test_run_pipeline_env_write.py`

**Interfaces:**
- 環境變數 `POLYMAS_NO_ENV_WRITE=1` 時，兩個函式只更新 `os.environ["TASK_ID"]`，不寫檔。不設時行為不變。

- [ ] **Step 1:** 看兩個檔案的 `git diff`，了解你正在做的修改。
- [ ] **Step 2:** 先寫測試：開關開啟時臨時 env 檔的內容不變；開關關閉時照舊寫入。
- [ ] **Step 3:** 各加一個判斷，不動其他行。
- [ ] **Step 4:** 審計讀取側：列出技能鏈上每個腳本載入 `.env` 的方式，找出不讓行程環境變數優先的地方，記在 `references/worker-prompt.md` 的「必須顯式傳參」清單裡。
- [ ] **驗證:** 新測試通過；這兩個檔案原有的測試照舊通過。

### Task 5: COURSE_ID 檢索

**Files:**
- Create: `.claude/skills/task-router/scripts/course_lookup.py`
- Modify: `tests/test_task_queue.py` 或另建測試檔

**Interfaces:**
- `course_lookup.py --school <學校> --course <課程關鍵詞>`，輸出 `{"course_id": "...", "course_name": "..."}`。
- 匯入 `auto_login.py` 現有的檢索函式，用已存的 storage_state 開瀏覽器。不修改 `auto_login.py`。
- 登入態不可用時直接以非 0 退出，不進入登入流程。匹配不到唯一課程時同樣以非 0 退出。

- [ ] **Step 1:** 確認匯入 `auto_login.py` 沒有副作用。有的話改成子行程呼叫，或退回備選方案。
- [ ] **Step 2:** 先寫測試：登入態不可用時不啟動瀏覽器。
- [ ] **Step 3:** 實作。
- [ ] **驗證:** 用一門已知 COURSE_ID 的課程實跑一次，結果相符；跑完後根 `.env` 的 SHA-256 不變。
- **備選:** 檢索不穩定時，任務書加一欄 COURSE_ID，由你在升級標籤時填。

### Task 6: 發布入口

**Files:**
- Modify: `.claude/skills/task-router/scripts/task_queue.py`
- Modify: `tests/test_task_queue.py`

**Interfaces:**
- `task_queue.py publish <N> [--approved-by-user]`
- 不帶旗標：重新讀運行記錄裡的兩份報告再算一次門禁，通過才發布。
- 帶旗標：issue 必須是 `status:ready`，跳過分數門檻。
- 兩種情況都只發布運行記錄裡的 TASK_ID。發布後回讀，成功才改成 `status:published`。

- [ ] **Step 1:** 找出回讀發布狀態的接口。找不到時，以發布接口回傳成功為準，並在留言裡寫明沒有回讀。
- [ ] **Step 2:** 先寫測試，用假的發布函式：門禁不通過時拒絕；運行記錄沒有 TASK_ID 時拒絕；帶旗標但不是 `status:ready` 時拒絕。
- [ ] **Step 3:** 實作，發布呼叫現有的 `publish_training`。
- [ ] **驗證:** 單元測試通過。真實發布留到 Task 9。

### Task 7: 任務書模板與 Worker 指令模板

**Files:**
- Create: `.claude/skills/task-router/references/issue-template.md`
- Create: `.claude/skills/task-router/references/worker-prompt.md`

- [ ] **Step 1:** 載入 `writing-for-agents` skill，照它的要求寫。
- [ ] **Step 2:** 任務書模板照設計文檔第 2 節。
- [ ] **Step 3:** Worker 模板包含：範圍邊界、七個步驟、收尾留言格式、「必須顯式傳參」清單、只能用 `task_queue.py` 改狀態和發布。
- [ ] **驗證:** 對照設計文檔第 6 節逐條核對，沒有遺漏。實際效果在 Task 9 檢驗。

### Task 8: Router skill 與文件

**Files:**
- Create: `.claude/skills/task-router/SKILL.md`
- Modify: `.claude/skills/AGENTS.md`（加一行索引）
- Modify: `docs/agents/issue-tracker.md`（加一行：任務 issue 在私有 repo）

- [ ] **Step 1:** 載入 `herdr` skill，確認開 pane、啟動 agent、送提示詞、等待結束的確切命令。
- [ ] **Step 2:** 寫 SKILL.md，涵蓋「派工」「彙報」「重做」「接受」「發布」五條指令。內容包括登入態預檢、COURSE_ID 檢索、認領、並行上限 3、`--export-env` 注入、監看、結尾摘要、macOS 通知。
- [ ] **Step 3:** 補兩處文件。
- [ ] **驗證:** 用一張測試 issue 演練「派工」，worker 指令換成只留言不幹活的假任務，確認 pane 開得起來、狀態改得對、Router 的摘要正確。

### Task 9: 第一階段驗收

**需要你參與：** 提供一張真實的能力訓練分派（或由我根據已有台賬起草，你確認後建 issue），把它升成 `ready-for-agent`，並確保對應帳號的登入態有效。這一步通過門禁後會真的發布一個平台任務。

- [ ] **驗收 1:** 這張任務從 issue 走到 `status:published`，留言裡的證據路徑都能打開。
- [ ] **驗收 2:** 一張不達標的任務走到 `status:waiting`，「重做」「接受」「發布」各走通一次。若真實任務一次就達標，改用一份舊的低分報告在測試 issue 上演練，不做真實發布。
- [ ] **驗收 3:** 登入態過期的任務被跳過，摘要列出命令。
- [ ] **驗收 4:** 兩張任務並行時，根 `.env` 的 SHA-256 前後一致。
- [ ] **驗收 5:** 看板內容與 issue 的實際狀態一致。
- [ ] **驗收 6:** `python3 -m pytest -q tests/test_task_queue.py` 全部通過。

---

## 第二階段：拉任務（第一階段驗收後開始）

### Task 10: Codex 的 `wecom-task-pull` skill

**Files:**
- Create: `.agents/skills/wecom-task-pull/SKILL.md`
- Create: `.agents/skills/wecom-task-pull/exclude.txt`
- Modify: `docs/agents/wecom-task-intake.md`（加一段指向新流程）

- [ ] **Step 1:** 先由你在 Codex 桌面版試一次：能否列出近 7 天的單聊並區分群聊。結果決定 skill 怎麼寫。
- [ ] **Step 2:** 寫 skill：讀取範圍、排除名單、歸檔規則（引用 `wecom-task-intake.md`）、用 `task_queue.py find-dup` 防重複、用任務書模板建 `needs-triage` 的 issue、輸出兩份清單。
- [ ] **驗收 1:** 指名一位聯系人，建出的 issue 欄位齊全，原件 SHA-256 相符。
- [ ] **驗收 2:** 不指名時輸出掃過的對話清單；重跑一次不產生重複 issue。
- [ ] **驗收 3:** 排除名單上的對話沒有出現在清單裡。

### Task 11: 兩週後回顧

- [ ] 看「門禁通過即發布」的實際結果，決定「彙報」是否改定時。
- [ ] 為下一類任務（作業批閱、專家智能體或 HTML）開一輪需求對齊。
