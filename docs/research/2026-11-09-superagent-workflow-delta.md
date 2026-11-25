# Super-agent 工作流機制：增量查證（相對 2026-11-04 筆記）

資料讀取日：2026-11-09（+08）。只讀查證，未安裝、未執行任何被研究的程式。【推論】＝我的判斷，沒有來源直接支持；方括號 `[S#]` 對應文末來源清單，全部為擁有者自己的網站、repo 或文件（一手），除非標明。引用原文一律改寫。

與既有檔案的關係：不修改 `2026-11-04-deepseek-super-agent.md` 與其 `.zh-Hant.md`。我稍早另寫了 `2026-11-09-deepseek-superagent-workflow.zh-Hant.md`（較長的一版）；其中兩處已在本次查證後更正：①誤寫「Claude Code 的事件觸發不含 GitHub issue」，實際含 Issue 事件；②DSH 的 GitHub 連結分支應為 `master` 而非 `main`。兩者衝突時以本檔為準。

---

## TL;DR：會改變設計的事實

1. **企業微信沒有官方 API 可讓個人讀取私聊內容。** 唯一官方管道是「會話內容存檔／數據與智能專區」，需企業管理員在管理後台開啟並設定範圍、可信 IP、公鑰，員工會看到告知頁，付費訂購，且只能拉最近 5 天 [S28][S29][S30][S31][S33]。所以「讀老師私聊分派」要嘛靠 GUI（computer use），要嘛靠企業層級授權；沒有第三條路。
2. **但「待辦」可以不走 GUI。** 官方開源的 `wecom-cli`（`WecomTeam/wecom-cli`）有 todo 技能：列出「當前用戶創建和參與的待辦」、建立、更新、完成、刪除，截止時間支援日期或時刻 [S42][S43]。它不能讀聊天內容，訊息技能只有查最近會話和發送 [S44]。這與 `wecom-task-intake.md` 中「不使用企業微信 CLI」的既有決定相衝突，是否改變由你定 [S47]。
3. **Codex computer use 不能當成無人值守的排程能力。** 官方文件說排程任務無人值守執行，沙箱為 read-only 或 workspace-write 時，凡需要「操作電腦上的 App」的工具呼叫會失敗；沒有任何一頁說排程任務或 `codex exec` 可使用 computer use [S9][S10]。macOS 前景可背景執行、Windows 會接管前景 [S8]。
4. **Claude Code 的雲端 scheduled tasks 原生支援 GitHub Issue 事件觸發**（opened、edited、closed、reopened、labeled、assigned 等），但跑在 Anthropic 雲端的全新 clone，碰不到你本機的企業微信 [S14]。Codex 的事件觸發只列 PR 活動，且只在網頁／行動版 [S9]。
5. **GitHub 沒有原子認領。** 一個 issue 可有最多 10 位 assignee [S22]；我讀到的 REST 文件中沒有比較並設定（compare-and-set）之類的互斥原語。佇列所需最小 token 權限是「Issues: read/write」加自動附帶的「Metadata: read」，限定單一私有 repo [S23][S24]。
6. DeepSeek 側：原型 repo 自 11-04 **無任何變化**；DSH 本體多了 `rc.1` 預發布版，其中有實驗性的 `subagent_oar`（把任務交給本機 Codex／Claude CLI）[S5][S6]。

---

## 1. 自 2026-11-04 起的變化

| 項目 | 查到的事實 | 來源 |
|---|---|---|
| `dsh-superagent-prototype` commit | **無變化**。全史仍只有 1 個 commit `8c32a9d`（2026-10-31T12:05:39Z）；自 11-04 00:00（+08）起 0 個 commit；`pushed_at` 仍為 2026-11-03T09:29:14Z；根目錄樹 SHA 與該 commit 一致 | [S1][S2] |
| 原型 README | **無變化**（README 檔只有該 1 個 commit 的歷史） | [S2] |
| 原型 release／tag | 0 個 tag；releases 端點本次請求逾時（EOF），11-04 筆記與稍早查詢均為 0，視為無變化 | [S1][S2] |
| 原型熱度 | 21,353 star、2,561 fork（11-04 筆記為約 1.76 萬 star）；Issues 功能仍關閉 | [S1] |
| 原型對 DSH 版本要求 | `engines.dsh` 仍為 `^0.2.1-alpha.2`。【推論】依 npm semver 的預設規則，預發布版只匹配「major.minor.patch 與範圍內某比較子相同」的範圍，`0.2.2-rc.1` 可能不被視為滿足；未驗證 DSH 自身如何檢查 | [S7] |
| `deepseek-harness` commit | 自 11-04 00:00（+08）起 master 上有 97 個 commit，全部落在 2026-11-04（最後一個 2026-11-04T08:40Z）；之後到 11-09 無新 commit（`pushed_at` 2026-11-04T13:06:39Z）。預設分支名為 `master`（`main` 不存在） | [S3][S4] |
| `deepseek-harness` release | 新增預發布 `dsh-v0.2.2-rc.1`（2026-11-04T13:07:14Z，晚於 11-04 筆記所記的 `alpha.3`）；11-04 之後到 11-09 沒有更新的 release | [S3][S5] |

與你的工作流有關的 rc.1 變更（來自 release notes）[S5]：

- **新增實驗性 `subagent_oar` 外掛**：可把獨立任務交給本機的 Codex 或 Claude CLI。README 說明它委派的是一次性的文字任務，使用你已安裝並已登入的原生 CLI 與設定，可在 profile 裡以 `launchArgs` 傳入如 `sandbox_mode="workspace-write"` 的參數 [S6]。
- **新增實驗性「變更請求與工作樹」**：在獨立 Git worktree 中跑 session，檢視本地與 PR 差異，追蹤檢查與評審狀態。
- **「自動化任務」改為 Host 級統一管理**：可手動建立、直接編輯，執行時可選擇複用或新建 session。
- **macOS Computer Use 權限引導改善**：改由獨立應用申請系統權限，應用授權可跨重啟保留。
- **TypeScript／Python SDK** 補齊排程、目標續跑、操作審批等能力。
- 修復「關閉應用時 Auto 會話權限意外變成完全訪問」的問題。

【推論】對你的意義：原型結論不變；DSH 側新增的 `subagent_oar` 與 Host 級自動化是官方元件中最接近「彙整 agent 分派給 Codex／Claude worker」的一塊，但全部標為實驗性，我沒有安裝驗證。

---

## 2. 逐題查證

### 2a. Codex computer use

| 問題 | 查到的事實 | 來源 |
|---|---|---|
| macOS 可用嗎 | 可用。ChatGPT 桌面應用在受支援地區對 macOS 與 Windows 提供 Computer Use，搭配 ChatGPT Work 與 Codex | [S8] |
| 佔用前台螢幕／滑鼠嗎 | macOS：可在你使用其他 App 時於背景執行範圍明確的任務。Windows：在作用中的桌面上執行，會接管指標與鍵盤，無法在同一個 Windows session 背景執行 | [S8] |
| 鎖屏後呢 | macOS 有「Locked use」，需手動啟用並安裝 Apple 授權外掛；只對進行中的受信任 Computer Use 回合短時解鎖；偵測到本機鍵鼠輸入就重新上鎖 | [S8] |
| 權限模型 | 兩層：①macOS 系統權限（Screen Recording、Accessibility）；②逐 App 授權，可選 Always allow，之後可在設定移除。管理員可限制可用 App | [S8] |
| 審批 | 使用前會先詢問 App 權限；執行敏感或破壞性動作前也可能再問。不能自動化終端機 App 與 ChatGPT 自身；不能以管理員身分驗證，也不能核准安全與隱私權限提示 | [S8] |
| 能背景／排程執行嗎 | 桌面應用的排程任務在背景無人值守執行，使用預設沙箱設定；沙箱為 read-only 或 workspace-write 時，需要「操作電腦上的 App」的工具呼叫會失敗；full access 則風險升高。**文件未說明排程任務能否使用 Computer Use** | [S9] |
| 排程任務的前提 | 專案範圍的排程任務需要電腦開機且 ChatGPT 桌面應用運行 | [S9] |
| `codex exec` 能用嗎 | 非互動模式文件通篇沒有提到 Computer Use，**查不到**其支援；預設沙箱為 read-only | [S10] |
| 資料去向 | 截圖等經 Computer Use 處理的內容，適用 ChatGPT 的資料控制設定 | [S8] |
| 官方偏好 | 目標 App 有外掛或 MCP 時，優先用結構化整合；Computer Use 留給必須看畫面的情況 | [S8] |

【推論】把 Computer Use 當「你在場、有人可接管」的互動能力設計較穩；若要定時無人值守讀企業微信，官方文件沒有給保證，需要實測，且很可能要把沙箱放寬到 full access。

### 2b. 非互動／排程執行能否被 issue 觸發或輪詢

**Codex**

| 機制 | 事實 | 來源 |
|---|---|---|
| `codex exec` | 單次非互動執行；預設 read-only 沙箱，可用 `--sandbox workspace-write` 或 `danger-full-access`；`--json` 輸出 JSONL 事件；`-o` 寫出最後訊息；`--output-schema` 要求結構化輸出；`--ephemeral` 不留 session 檔；`--full-auto` 已不再支援，可用 `--approve-for-me` 走自動審核。文件定位是給 CI 與腳本呼叫，**本身沒有觸發器或輪詢功能** | [S10] |
| 桌面排程任務 | 可用 RRULE 自訂排程；可在本機專案或獨立 worktree 跑；結果集中在 Scheduled 視圖（相當於收件匣） | [S9] |
| 事件觸發 | Gmail、Slack、GitHub 的 **Pull request 活動**；只在網頁與行動版，桌面應用、CLI、IDE 擴充都沒有；一個任務不能同時用事件觸發與時間排程。文件列的 GitHub 觸發不含 issue | [S9] |
| GitHub Action | `openai/codex-action@v1` 在 Actions 的 Linux／macOS runner 上跑 `codex exec`（Windows 須設 `safety-strategy: unsafe`）；範例是 PR 審查。GitHub 側 `issues` 事件可觸發 workflow [S27]，所以【推論】可組出「issue 事件 → Action → codex exec」，但它跑在 runner 上，不是你的 Mac | [S11][S27] |

**Claude Code**

| 機制 | 事實 | 來源 |
|---|---|---|
| `claude -p` | 程式化執行：`--allowedTools` 預先核准工具、`--output-format` 結構化輸出、`--continue` 延續對話。建議腳本場景加 `--bare`：略過 hooks、skills、MCP、CLAUDE.md 的自動發現，且**不讀 OAuth／keychain**，須設 `ANTHROPIC_API_KEY`。不加 `--bare` 時 `-p` 會執行專案 `.claude/settings.json` 的 hooks 並連 `.mcp.json` 的伺服器，且不顯示信任對話框 | [S17] |
| CLI computer use | macOS 研究預覽；需 Pro／Max／Ultra，Team／Enterprise 不可用；**必須互動 session，不能用 `-p`** | [S12] |
| Desktop computer use | macOS 與 Windows 研究預覽；需 Pro／Max／Ultra，Team／Enterprise 不可用；桌面應用須在運行；macOS 14+；App 授權只持續該 session（Dispatch 衍生 session 為 30 分鐘）；瀏覽器僅可檢視、終端機與 IDE 僅可點擊；macOS 可背景執行 | [S13] |
| 雲端 scheduled tasks（舊稱 routines） | 三種觸發：排程（最短 1 小時）、API（HTTP POST 加 bearer token）、**GitHub 事件：Pull request、Release、Issue**（須安裝 Claude GitHub App）。每個事件開一個新 session，不複用。GitHub 事件有每任務與每帳號的小時上限，超過的事件直接丟棄（文件未列具體數字）。在雲端全新 clone 上跑，預設 auto mode；研究預覽 | [S14][S15] |
| 雲端任務限額 | 排程執行每帳號 100 次／小時；「Run now」與 API 觸發每任務 30 次／小時、每帳號各 100 次／小時；無超量 | [S14] |
| 桌面排程 | 跑在本機，只在應用開啟且電腦醒著時觸發；可選獨立 worktree；權限模式可逐任務設定；表單最短 1 小時 | [S15][S16] |
| `/loop` | 綁在開著的 session，最短 1 分鐘；週期任務 7 天後自動到期 | [S15] |
| Channels | 用 MCP server 把事件推進**執行中**的 session，可雙向；研究預覽；事件只在 session 開著時送達 | [S18] |

【推論】結論：
- 雲端側：Claude Code 能由 issue 事件原生觸發，但碰不到本機企業微信與本機檔案。
- 本機側：兩家都沒有「issue 一出現就喚醒本機 session」的原生功能；本機 worker 領任務只能靠輪詢（桌面排程最短 1 分鐘由 Claude 設定、cron 加 `codex exec`／`claude -p`）或自建 channel。

### 2c. GitHub issues 作為佇列

| 項目 | 事實 | 來源 |
|---|---|---|
| assignee 認領 | 一個 issue 或 PR 最多 10 位 assignee；可被指派者包含自己、評論過者、有寫入權限者。所以「有 assignee」不等於獨占 | [S22] |
| 原子性 | 我讀到的 REST／CLI 文件中**查不到**任何比較並設定、樂觀鎖或原子認領的功能。【推論】認領協議須容忍競爭，例如指派後重讀並確認自己是唯一認領者，或以 label 加留言順序仲裁 | [S21][S26] |
| sub-issues | 每個父 issue 最多 100 個子項、最多 8 層；需 triage 以上權限 | [S19] |
| 依賴（blocked by／blocking） | 每種關係最多連 50 個 issue；Free、Pro、Team、Enterprise Cloud 都可用；需 triage 以上權限；REST 有 `GET／POST …/issues/{n}/dependencies/blocked_by`、`DELETE …/blocked_by/{issue_id}`、`GET …/blocking` | [S20][S21][S21b] |
| fine-grained PAT 最小權限 | 「Issues」repository 權限的 write 涵蓋：建立 issue、評論、增刪 assignee、增刪 label、建立依賴、sub-issues；讀取需 read。「Metadata: read」自動附帶。評論、assignee、label 端點標註「需多個權限或可能用其他權限」（涉及 PR 時要 Pull requests 權限）。僅管理 issue 佇列不需要 Contents 與 Pull requests | [S23] |
| token 範圍 | fine-grained PAT 只能限定在單一使用者或組織名下，可進一步限定到指定 repo；一律附帶所有公開 repo 的唯讀；只有 classic PAT 能對「不屬於你或你所在組織」的公開 repo 寫入；建議設有效期；一年未使用會被自動移除 | [S24] |
| gh 認證 | 本機 gh 可用環境變數 `GH_TOKEN`／`GITHUB_TOKEN` 提供 token，優先於已存的憑證 | 本機 `gh help environment`（gh 2.91.0） |
| 速率（主限制） | 個人 token 5,000 次／小時；`GITHUB_TOKEN` 每 repo 1,000 次／小時 | [S25] |
| 速率（次級限制） | 同時請求不超過 100；REST 端點每分鐘不超過 900 點，GET＝1 點，POST／PATCH／PUT／DELETE＝5 點 | [S25] |
| 官方輪詢建議 | 優先用 webhook；必須輪詢時用條件請求（ETag，未變更回 304 且不計主限制）；寫入請求應串行，大量寫入之間至少等 1 秒 | [S26] |
| 私有 repo | 以上限制與權限對私有 repo 同樣適用；公開 repo 的排程 workflow 在 60 天無活動後被停用。**私有 repo 的 Actions 免費額度**我沒有查，查不到 | [S27] |
| `issues` 事件 | 可觸發 workflow 的活動類型含 opened、edited、assigned、labeled 等；workflow 檔須在預設分支 | [S27] |
| gh 旗標 | 文件稱 gh 有 `--parent`、`--add-sub-issue`、`--blocked-by` 等旗標；本機 gh 2.91.0 的 `gh issue create／edit --help` 沒有這些旗標。你的 `issue-tracker.md` 本來就以 `gh api` 操作依賴，不受影響 | [S19][S20]；本機實測 |

### 2d. 企業微信官方開放能力（developer.work.weixin.qq.com）

**待辦（Todo）**

| 問題 | 事實 | 來源 |
|---|---|---|
| 服務端 API | 目錄裡「待辦」只有兩個：獲取待辦詳情（`todo/get`）、更新待辦狀態（`todo/update`，可改整體狀態與最多 20 位參與人）。**僅能操作「當前應用創建的待辦」**；`update` 要求調用應用的可見範圍包含根部門。服務端沒有「建立待辦」與「列出我的待辦」 | [S34][S35] |
| 建立待辦 | 只有客戶端 JS-SDK `createTodo`：它只調起企業微信原生的建立面板，由使用者確認（使用者取消會回 `createTodo:cancel`）；須先 `ww.register`；應用須是**全員可見的自建應用**；第三方與代開發應用不支援 | [S36] |
| 官方 CLI | `WecomTeam/wecom-cli`（MIT，組織帳號，2026-11-02 仍有更新）：todo 技能可建立、查詢、篩選、更新、完成、刪除或退出待辦；`todo list` 拉取「當前用戶創建和參與的待辦」，可依創建時間、截止時間、狀態、關鍵字篩選，單次最多 20 筆並可自動分頁；截止時間用 `deadline` 物件（`date` 或 `datetime`）。官方歸屬依據是 repo 組織與 README 自述；開發者中心「待辦」總覽頁我抓不到內容，無法由官方文件站直接證實 | [S42][S43] |
| CLI 授權 | `wecom-cli auth init` 預設用企業微信掃碼建立綁定，或手動輸入智能機器人（API 模式、長連接）的 Bot ID 與 Secret；Bot 在客戶端「工作台 → 智能機器人 → 創建機器人 → 手動創建 → API 模式」中建立，說明文章未提管理員要求，**是否需管理員先開啟智能機器人能力：查不到** | [S41][S42] |
| CLI 的隱私行為 | 預編譯的 npm 版本預設回傳「呼叫它的 Agent 程式名稱與調用鏈路」到企業微信雲端；需從原始碼關閉特性重新建置才能停用 | [S45] |

**消息拉取（讀私聊）**

| 問題 | 事實 | 來源 |
|---|---|---|
| 官方能讀聊天內容的唯一管道 | 會話內容存檔。管理後台開啟前須設定開啟範圍、IP 位址與訊息加密公鑰；員工企業微信版本須 ≥2.8.9；開啟後員工進入企業會看到告知頁；可獲取「已開啟員工」與「未開啟員工」之間的會話，**不能獲取兩位未開啟員工之間的會話**；員工與外部聯繫人的會話須外部聯繫人同意 | [S28] |
| 經典 SDK 路徑 | 用 C 語言 SDK（Linux、Windows）加 corpid 與存檔 Secret 拉取；單次最多 1000 筆，頻率不超過 4000 次／分鐘；只能拉最近 5 天，須定期拉取才能留存；調用方公網 IP 須與管理端登記的 IP 一致；消息以企業上傳的 RSA 公鑰加密，自行用私鑰解密。頁面最後更新 2026-01-19，FAQ 為 2022 年 | [S29] |
| 新路徑「數據與智能專區」 | 在「管理後台 → 安全與管理 → 管理工具 → 數據與智能專區」上傳企業自有程式、授權應用使用數據與工具、開啟會話內容並設定公鑰；程式在專區內以專區 SDK 取會話記錄。限制同樣是只能拉最近 5 天、單次最多 1000 筆、發送者或接收者須在授權範圍內；應用須具備「數據與智能專區權限」。頁面最後更新 2026-09-10 | [S30][S31] |
| 兩條路徑哪條是現行 | 兩套文件並存，我無法判定新開通企業只能走哪一條，**查不到** | [S29][S31] |
| 費用與部署 | 服務協議：按訂購的「使用權」數量計費，足額支付後才開通；會話內容須存儲在中國大陸境內，由企業自行採購、部署、維護本地存檔伺服器。專區會話數據介面對服務商是增值介面，授權後免費試用 30 天，之後付費；對**自建應用**的價格**查不到** | [S33][S32] |
| 誰能做 | 開啟、設定範圍、IP、公鑰都在管理後台；自建應用也須在管理端配置可信 IP 才能呼叫介面（2022-06-20 起）。需要企業管理員 | [S28][S30][S46] |

**機器人／Webhook**

| 類型 | 事實 | 來源 |
|---|---|---|
| 消息推送（原「群機器人」webhook） | 只能向其所屬的那一個群**發送**消息；每個推送每分鐘不超過 20 條；webhook 地址等同密鑰，不可公開；支援文字、markdown、圖片、圖文、文件、語音、模板卡片 | [S37] |
| 智能機器人 | 只在「使用者在群裡 @ 機器人」或「與機器人單聊」時觸發回調（文字、圖文混排、引用；單聊另可收圖片、語音、文件、視頻）；同一使用者與同一機器人最多同時 3 條交互；流式回覆最長等待 6 分鐘；另有 WebSocket 長連接模式。**它不會收到其他人之間的私聊** | [S38][S39] |
| 自建應用接收消息 | 只推送「使用者在應用裡發給應用」的消息和事件，需提供回調 URL | [S40] |

【推論】對「取代 GUI 讀私聊」的判斷：
- 純個人、不經管理員：做不到，GUI 是唯一路徑。
- 折衷一：把老師的分派轉發給你自建的智能機器人（單聊），機器人用長連接收，可取代 GUI 讀取，但每則都要你手動轉。
- 折衷二：若老師同時用企業微信「待辦」派任務，`wecom-cli todo list` 可直接讀，不需 GUI。
- 企業層級：請管理員開啟會話內容存檔／專區，成本、告知義務與保存地點限制見上。

---

## 3. 對原設計構想的影響（【推論】，供取捨）

| 原構想 | 查證後 | 建議 |
|---|---|---|
| Codex computer use 定時讀企業微信 | 排程無人值守下 App 操作在受限沙箱會失敗；`codex exec` 無 computer use 說明；Windows 會接管前景 | 當作「你在場時觸發」的互動步驟；或改走 `wecom-cli todo list`（若分派有建成待辦） |
| 任務寫進 GitHub issue | 完全可行；最小權限已明確；無原子認領 | 用私有 repo，Issues read/write 的 fine-grained PAT；認領協議自建並容忍競爭 |
| worker 領取 | 雲端側 Claude Code 可由 Issue 事件觸發但碰不到本機；本機側無原生喚醒 | 本機 worker 輪詢（條件請求、串行寫入）；需要雲端自足的任務才用雲端觸發 |
| reporter 彙整 | 無現成開關；OpenAI Scheduled 視圖、Claude Code agent view／Projects 各有「收件匣式」呈現 | 沿用 11-04 結論：彙整 agent 只讀寫 issue，先列需要人的 |
| 寫回企業微信待辦 | 服務端無建立介面；JS-SDK 需人工確認；官方 CLI 可建立並設截止時間 | 若仍堅持不用 CLI，維持 GUI 寫入並保留現有回讀驗證 |

---

## 4. 查不到或不確定

1. 原型 releases 端點本次請求逾時，未取得該次回應；依 tag 為 0 與 11-04 筆記判定無 release。
2. `0.2.2-rc.1` 是否滿足原型的 `engines.dsh` 範圍：只有 semver 規則的推論，未驗證。
3. Codex 排程任務或 `codex exec` 是否可使用 Computer Use：官方文件**未說明**；排程無人值守時 App 權限提示會怎麼處理，**查不到**。
4. Claude Code GitHub 事件觸發的每任務與每帳號小時上限的具體數字：文件只說有上限，**查不到**。
5. GitHub REST 是否有原子認領或條件寫入：我讀到的文件沒有，不能排除其他頁面有。
6. 私有 repo 的 GitHub Actions 免費額度：未查。
7. 企業微信：①會話內容存檔經典 SDK 與「數據與智能專區」哪條是新開通企業的現行路徑；②對自建應用的價格；③個人建立智能機器人是否需管理員開啟能力；④`wecom-cli` 的官方歸屬在開發者中心文件站的直接佐證（「待辦」總覽頁抓不到內容）；⑤待辦服務端 API 的呼叫頻率限制，本次未逐項查。
8. 企業微信桌面端能否被 computer use 穩定操作：沒有任何一手文件涵蓋，需實測。
9. 我沒有安裝或執行任何東西，所有行為結論只來自文件。

---

## 來源

**DeepSeek**
- **[S1]** 原型 repo 元資料 API：https://api.github.com/repos/deepseek-ai/dsh-superagent-prototype
- **[S2]** 原型 commits／README 歷史／根目錄樹：https://api.github.com/repos/deepseek-ai/dsh-superagent-prototype/commits 、 https://api.github.com/repos/deepseek-ai/dsh-superagent-prototype/git/trees/HEAD
- **[S3]** DSH repo 元資料與 releases：https://api.github.com/repos/deepseek-ai/deepseek-harness 、 https://github.com/deepseek-ai/deepseek-harness/releases
- **[S4]** DSH commits（自 2026-11-03T16:00Z 起）：https://api.github.com/repos/deepseek-ai/deepseek-harness/commits
- **[S5]** release notes：https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.2.2-rc.1
- **[S6]** `subagent_oar` README：https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/experimental/subagent-oar/README.md
- **[S7]** 原型 package.json：https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/package.json

**OpenAI（ChatGPT 桌面應用與 Codex；`developers.openai.com/codex/...` 與 `learn.chatgpt.com/docs/...` 同源）**
- **[S8]** Computer Use：https://developers.openai.com/codex/app/computer-use （Markdown：https://learn.chatgpt.com/docs/computer-use.md ）
- **[S9]** Scheduled tasks：https://developers.openai.com/codex/app/automations （https://learn.chatgpt.com/docs/automations.md ）
- **[S10]** Non-interactive mode：https://learn.chatgpt.com/docs/non-interactive-mode.md
- **[S11]** Codex GitHub Action：https://learn.chatgpt.com/docs/github-action.md

**Anthropic（Claude Code）**
- **[S12]** CLI computer use：https://code.claude.com/docs/en/computer-use.md
- **[S13]** Desktop computer use：https://code.claude.com/docs/en/desktop.md
- **[S14]** Scheduled tasks（雲端，舊稱 routines）：https://code.claude.com/docs/en/routines.md
- **[S15]** 排程方式比較與 `/loop`：https://code.claude.com/docs/en/scheduled-tasks.md
- **[S16]** Desktop 排程：https://code.claude.com/docs/en/desktop-scheduled-tasks.md
- **[S17]** 程式化執行（`claude -p`）：https://code.claude.com/docs/en/headless
- **[S18]** Channels：https://code.claude.com/docs/en/channels.md

**GitHub**
- **[S19]** Sub-issues：https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues
- **[S20]** Issue 依賴：https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies 、上限 50：https://github.blog/changelog/2025-08-21-dependencies-on-issues/
- **[S21]** REST 依賴端點：https://docs.github.com/en/rest/issues/issue-dependencies ；**[S21b]** sub-issues 端點：https://docs.github.com/en/rest/issues/sub-issues
- **[S22]** 指派：https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users
- **[S23]** fine-grained PAT 所需權限：https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens
- **[S24]** 管理 PAT：https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- **[S25]** 速率限制：https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- **[S26]** REST 最佳實踐：https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- **[S27]** Actions 觸發事件：https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

**企業微信（developer.work.weixin.qq.com 與 work.weixin.qq.com／open.work.weixin.qq.com）**
- **[S28]** 會話內容存檔「使用前幫助」：https://developer.work.weixin.qq.com/document/path/91361
- **[S29]** 會話內容存檔「獲取會話內容」（SDK）：https://developer.work.weixin.qq.com/document/path/91774 ；FAQ：https://developer.work.weixin.qq.com/document/path/91552
- **[S30]** 數據與智能專區「接入指引」：https://developer.work.weixin.qq.com/document/path/99871
- **[S31]** 專區「獲取會話記錄」：https://developer.work.weixin.qq.com/document/path/99968
- **[S32]** 專區「收費方案」（服務商）：https://developer.work.weixin.qq.com/document/path/100099
- **[S33]** 會話內容存檔功能服務協議（PDF）：https://work.weixin.qq.com/wework_admin/financial/trialApplyNorm
- **[S34]** 獲取待辦詳情：https://developer.work.weixin.qq.com/document/path/101524
- **[S35]** 更新待辦狀態：https://developer.work.weixin.qq.com/document/path/101534
- **[S36]** 創建待辦（JS-SDK）：https://developer.work.weixin.qq.com/document/path/101530 ；查看待辦詳情：https://developer.work.weixin.qq.com/document/path/101531
- **[S37]** 消息推送配置說明（原群機器人）：https://developer.work.weixin.qq.com/document/path/99110
- **[S38]** 智能機器人「接收消息」：https://developer.work.weixin.qq.com/document/path/100719
- **[S39]** 智能機器人長連接：https://developer.work.weixin.qq.com/document/path/101463
- **[S40]** 自建應用「接收消息與事件」概述：https://developer.work.weixin.qq.com/document/path/90238
- **[S41]** 如何獲取 Bot ID 和 Secret：https://open.work.weixin.qq.com/help2/pc/cat?doc_id=21677
- **[S42]** `wecom-cli` README：https://github.com/WecomTeam/wecom-cli
- **[S43]** `wecomcli-todo` 技能與 `todo list` 參考：https://github.com/WecomTeam/wecom-cli/blob/main/skills/wecomcli-todo/SKILL.md
- **[S44]** `wecom-cli` 技能總覽（含 message 技能說明）：https://github.com/WecomTeam/wecom-cli/blob/main/docs/skills.md
- **[S45]** `wecom-cli` 數據收集說明：https://github.com/WecomTeam/wecom-cli/blob/main/docs/data-collection.md
- **[S46]** 開發前必讀（可信 IP）：https://developer.work.weixin.qq.com/document/path/90664

**本專案（只讀）**
- **[S47]** `docs/agents/wecom-task-intake.md` 第 31 行（「用戶明確不使用企業微信 CLI時，全程沿用應用界面及本地文件操作」）。
