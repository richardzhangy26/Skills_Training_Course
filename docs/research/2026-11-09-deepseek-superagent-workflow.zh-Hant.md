# DeepSeek Super-agent 研究：它是什麼，以及對「企業微信 → GitHub 佇列 → 多 worker → 彙整回報」工作流的借鑒

資料讀取日：2026-11-09（+08）。性質：只讀研究，未安裝、未執行任何被研究的程式碼。

標記說明：【一手】＝來源由擁有者自己發布（官方網站、deepseek-ai 組織的 repo、官方文件、廠商自己的文件站）；【二手】＝第三方轉述；【推論】＝我的判斷，沒有來源直接支持。引用原文一律改寫，不照抄。

---

## 0. 與既有筆記的關係

`docs/research/` 已有兩份 2026-11-04 的同題筆記：[簡體版](./2026-11-04-deepseek-super-agent.md)（檔名無語言後綴，內容為簡體中文）與[繁體版](./2026-11-04-deepseek-super-agent.zh-Hant.md)。它們已詳細覆蓋原型的領域模型、授權、執行、風險，本文不重寫，只做四件事：

1. 把關鍵事實在 2026-11-09 重新核對一次（見 §2）。
2. 補上既有筆記沒回答的兩題：它是不是桌面應用、能不能 computer use（§2.2）。
3. 取得設計文章的一手英文版（既有繁體版說「原文未能自行取得」）。X 頁面是機器翻譯，通篇與二手轉述的數字一致。簡體版聲稱讀過微信中文原文，我用普通 HTTP 抓同一網址只得到「環境異常」驗證頁，按規則未嘗試繞過，所以**無法複核簡體版對微信原文的引用**。
4. 補三家官方文件裡對你的工作流有決策價值的機制，並對照你目前的做法（§4、§5）。

---

## 1. 結論摘要

1. **真實存在，但不是 DeepSeek 的產品。** 正確名稱是 Super-agent（一套設計）加 `dsh-superagent-prototype`（開源研究原型）。原型 README 自稱是研究原型、僅供參考，不是官方 DeepSeek 產品 [README](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/README.md)【一手】。deepseek.com 首頁、Research & News 清單、Harness 頁面、API 文件 changelog 中都沒有 Super Agent 字樣（§2.1）。
2. **不是桌面應用，也不做 computer use。** 它是 DeepSeek Harness（簡稱 DSH）的一個外掛包：跑在專用的 DSH Web profile，用 tmux 常駐，管理面板綁 `127.0.0.1`，事件來源只有 GitHub（可選飛書）。DSH 本身另有官方桌面版（macOS Apple silicon／Windows x64）和實驗性 computer use（以 macOS 為主），但在我讀到的 superagent 文件與設定中，worker 的工具集不含 computer use。
3. **核心思想一句話：** 把「人要盯幾個 session」換成「人只面對一個常駐 Router，Router 不做事、只收事件和派工，每個任務交給隔離的 Worker，Worker 不直接對人、只向 Router 回報狀態」。配套有事件兩段過濾（程式規則先、模型後）、Thread 訂閱直通、結構化回報狀態、少打擾規則。這些來自 DeepSeek Harness 團隊 2026-11-01（X 頁面顯示日期）的設計文章 [X 英文機器翻譯版](https://x.com/DeepSeekHarness/article/2116857257245987236)【一手，帳號歸屬見 §6】。
4. **對你的工作流：整套導入不合適，設計思想高度同構、值得借。** 你設想的流程幾乎就是 Source → Trigger → Ticket → Worker → Router 統一回報。最值得借的是：Router 不執行、Worker 不直接對人、結構化回報加「只列需要人的」視圖、先 observe 後放權。
5. **三個要先處理的硬事實**（§5.3）：存放任務的 GitHub repo 是 PUBLIC；文件規定的五個 triage label 在遠端只存在 `wontfix`；computer use 的螢幕截圖會送到模型方，企業微信私聊內容會被帶出機器。

---

## 2. 證據表

### 2.1 它是什麼、真不真

| # | 論斷 | 來源 | 等級 |
|---|---|---|---|
| 1 | `deepseek-ai/dsh-superagent-prototype`：組織帳號、MIT、TypeScript、建立於 2026-10-31T09:32:46Z；全史只有 1 個 commit `8c32a9d`（2026-10-31T12:05:39Z，作者 DeepSeek Harness Team）；0 release、0 tag；Issues 功能關閉；2026-11-09 讀到 21,347 star、2,560 fork | [GitHub API：repo](https://api.github.com/repos/deepseek-ai/dsh-superagent-prototype)、[commits](https://api.github.com/repos/deepseek-ai/dsh-superagent-prototype/commits) | 一手 |
| 2 | README 自述：研究原型、僅供參考、不是官方產品；公開版為發布做過改寫，與內部版及設計文章不同；文章中有些設計是未來方向，原型沒有實作 | [README](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/README.md) | 一手 |
| 3 | 設計文章標題 *Exploring Super-agent Design: Towards a More Autonomous Agent System*，X 頁面標示「原文為中文，此為機器翻譯」；開頭聲明討論的是架構想法，不是 DSH 現有功能介紹；結尾說明 dsh-superagent-prototype 只是驗證技術方案的原型 | [X 文章頁](https://x.com/DeepSeekHarness/article/2116857257245987236) | 一手（機器翻譯） |
| 4 | deepseek.com 首頁的產品入口是 DeepSeek Web、DeepSeek Harness、API Platform、Harness Desktop，沒有 Super Agent；Research & News 清單最新一則是 2026-09-10 的 V4.1-Flash | [首頁](https://www.deepseek.com/en)、[News](https://www.deepseek.com/en/news) | 一手（缺席證據） |
| 5 | Harness 官方頁面、API 文件首頁與 changelog（最新條目 2026-10-17）全文檢索 `super`，0 次命中 | [Harness 頁](https://www.deepseek.com/en/harness/)、[API 文件](https://api-docs.deepseek.com/)、[changelog](https://api-docs.deepseek.com/updates) | 一手（缺席證據） |
| 6 | 官方 App 商店頁面：我嘗試的 Apple App Store 連結只回傳了 App Store 首頁，未取得 DeepSeek App 的頁面，**此項未檢查** | [嘗試的連結](https://apps.apple.com/us/app/deepseek-ai-assistant/id6737597349) | — |
| 7 | 社群衍生專案如 `thefullgc/opensuperagent`、`vicfei/dsh-super-agent`，擁有者是個人帳號，名稱借用但非官方 | [GitHub 搜尋](https://github.com/search?q=dsh-super-agent&type=repositories) | 一手（擁有者類型）|
| 8 | 同名不同物：`superagent-ai/superagent`（AI 應用的提示注入／資料外洩防護，6,856 star）、`forwardemail/superagent`（Node HTTP 用戶端）。與 DeepSeek 無關 | [superagent-ai](https://github.com/superagent-ai/superagent)、[forwardemail](https://github.com/forwardemail/superagent) | 一手 |
| 9 | DSH 本體：`deepseek-ai/deepseek-harness`，MIT，276,734 star，最新 release 為預發布 `dsh-v0.2.2-rc.1`（2026-11-04），README 寫明處於開發者預覽、會有破壞相容性的變更 | [repo](https://github.com/deepseek-ai/deepseek-harness)、[README](https://github.com/deepseek-ai/deepseek-harness/blob/master/README.md)、[releases](https://github.com/deepseek-ai/deepseek-harness/releases) | 一手 |
| 10 | 官方 API 目前的模型名是 `deepseek-flash`（V4.1-Flash-1017）和 `deepseek-v4-pro`；官方文件提供把 DeepSeek 模型接進 Codex 與 Claude Code 的設定頁 | [API 首頁](https://api-docs.deepseek.com/)、[Codex 整合](https://api-docs.deepseek.com/quick_start/agent_integrations/codex)、[Claude Code 整合](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code) | 一手 |

### 2.2 形態：桌面應用？computer use？

| # | 論斷 | 來源 | 等級 |
|---|---|---|---|
| 1 | superagent 是 DSH 的 bundle，需要一個專用 DSH profile（由 Web profile 模板建立），面板服務在 `127.0.0.1`；`start` 指令把它放進 tmux session 常駐；前置條件含 Node 22.19+/24+、pnpm、git 2.32+、tmux、gh 2.48+ | [docs/006](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/006-deployment.md) | 一手 |
| 2 | 事件來源：github.com（不支援 GitHub Enterprise Server）加可選飛書；GitHub 以輪詢取事件，預設一分鐘一次 | 同上 | 一手 |
| 3 | 兩個 preset（Router、Worker）都以 `danger-full-access`、操作者的 OS 使用者身分執行；帳號包裝腳本不是隔離，worker 可用絕對路徑執行程式、讀家目錄；要隔離須另建 OS 帳號 | 同上 | 一手 |
| 4 | DSH 有官方桌面版：Harness 頁面提供 macOS（Apple silicon）與 Windows（64-bit）下載，連結在 `download.deepseek.com`；頁面稱 DSH 為全球公開預覽、開源 | [Harness 頁](https://www.deepseek.com/en/harness/) | 一手 |
| 5 | 桌面版是包著完整 Web 應用的 Electron 外殼；關閉視窗只是隱藏，Host 與任務繼續跑；退出時若有執行中任務或已排程提醒會先詢問 | [apps/desktop/README](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/desktop/README.md) | 一手 |
| 6 | DSH 的 Agent teams、Scheduled tasks、Voice input、Auto approval review 在官方頁面標為 Experimental；桌面版預設不啟用排程任務 | [Harness 頁](https://www.deepseek.com/en/harness/)、同上 README | 一手 |
| 7 | DSH 的 computer use：讓模型觀察並操作本機桌面，需明確掛載 `dsh-computer-use` 加一個提供者（Cua Driver 的 MCP 或 native 版）；兩者都是實驗性 npm 套件 | [docs/subsystems/computer-use](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/computer-use.md) | 一手 |
| 8 | macOS 提供者需要 Accessibility 與 Screen Recording 權限，要求 macOS 14+，Windows 支援開發中；桌面版 Windows 安裝包不含 macOS 的 computer use 套件 | [cua-macos README](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/experimental/cua-macos/README.md)、桌面 README | 一手 |
| 9 | computer use 不替任何 Session 預留桌面，跨 Session 的「觀察→動作→驗證」要呼叫端自己協調；被取消的呼叫無法撤回桌面已收到的輸入 | computer-use 文件（同 #7） | 一手 |
| 10 | cua-macos 的 `agentPreset` 預設是 `ptc`，只對綁定該 preset 的 agent 註冊工具 | cua-macos README（同 #8） | 一手 |
| 11 | 在 superagent 的 README、SETUP、docs/000–008、`cordis.patch.yml`、`policy.ts`、`package.json` 中檢索 computer、cua、browser、desktop：沒有相關內容（僅 docs/004 有一句要求 UI 變更附前後截圖）。worker preset 的工具清單是 shell、檔案、job、skill 等 | [cordis.patch.yml](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/cordis.patch.yml) 及上列文件 | 一手（缺席證據；我沒讀 `src/` 全部檔案） |
| 12 | 【推論】若要讓 superagent 的 worker 操作 GUI，須自行改 preset 並掛 computer use，這已超出原型的設計範圍，原型文件也沒有提這件事 | — | 推論 |
| 13 | 第三方「DeepSeek Harness Desktop」站點（如 dshdesktop.cn）與 GitHub 上的 Electron 封裝是社群作品，官方下載只認 `download.deepseek.com` | [Harness 頁](https://www.deepseek.com/en/harness/)（官方連結）；社群頁僅作線索 | 官方連結一手 |

### 2.3 核心思想（設計文章，一手但為機器翻譯）

來源均為 [X 英文機器翻譯版](https://x.com/DeepSeekHarness/article/2116857257245987236)。作者自述實驗用合成負載、「僅供參考」；「內部實例已持續運行」是自述，無法外部驗證。

| # | 論斷 | 備註 |
|---|---|---|
| 1 | 動機：作者經驗是一個人通常只能同時跟 3–5 個活躍 session；單任務受模型能力限制，多任務受人的注意力限制 | 經驗陳述，不是量測 |
| 2 | 兩層架構：**Router** 長壽，接所有人類互動與全局協調，自己不執行任務（可以不給 Bash），文章稱較輕的模型往往夠用；**Worker** 各自隔離 context、專做一個任務、用最強模型，**不直接與人互動**，只向 Router 回報狀態，由 Router 統一回覆 | 與 Agent Team 的差別：Router 不拆解單一任務、只做派工與高層追蹤 |
| 3 | 事件（Trigger）先過兩段過濾：程式規則（來源、群組、使用者／機器人白名單，每個來源可設「只回應明確請求／視為候選／忽略」），再由模型依 prompt 政策判斷候選 | Fast Path／Slow Path |
| 4 | 同一 Thread（同一 PR、同一 IM 話題）的後續事件由程式直送已訂閱的 Worker，不再經 Router；Router 只管新任務冷啟動與跨任務協調；Worker 與 Thread 是多對多訂閱 | 稱可讓 Workers 在共用 Thread 中自行發現並化解衝突 |
| 5 | Inline & Spill、Chain of Recall：把 context window 當快取，先放 ID 與摘要，按局部性逐步內嵌，超限部分留指標；物件以 ID 互連，可逐跳回溯 | 原型 README 稱此類設計並非都已實作 |
| 6 | 投機執行：看到環境訊號就先在背景試做，確認有用才交付，否則保持安靜 | 內部使用者群的「默默重現並修復」為例 |
| 7 | 非同步 ReAct：用 `start()`／`stop()` 取代阻塞呼叫；文章稱 DSH 已實作但尚未預設開啟 | |
| 8 | 分通道風格：IM 求輕、只在需要決策或簽核時打擾、只問直接問題、給短結論，作者驗證過的硬規則是每則回覆不超過 100 字；GitHub／信件這類非同步通道給結構化高密度內容 | |
| 9 | 算存分離與 BYOM（自帶機器）：Agent Loop 放雲端、狀態放資料庫、本機端只裝輕量 daemon；另設獨立 Watchdog session 監看 worker 是否真有進展 | 原型是本地單機，沒有實作 |
| 10 | 實驗（合成負載，約 300 則訊息、約 20 則工作請求，工作用「只耗時間的工具」模擬，每組跑 5 次）：Super-agent 完成時間 p50／p95＝12.4／15.7 分鐘；單 Session＋subagent 工具（中性 prompt）20.4／29.5；委派優先 prompt 13.8／29.0；去掉訂閱直通後完成時間相近，但 cache-read token 由 23.2M 升到 31.8M（約 +37%） | 作者自述「僅供參考」，並說明測的是調度而非單任務執行力 |
| 11 | 開放問題之一是安全：事件驅動讓更多不可信輸入驅動 agent；雲端 Agent Loop 與握有本機憑證的端點互信，一旦被提示注入，所有已連端點都有風險；作者認為 agent 需要「使用憑證卻不看見憑證」的方式 | 這是未解問題，不是已有解法 |
| 12 | 原型中確有的對應：Router／Worker 兩種 Session、Trigger→Eval→Ticket、兩層授權、Subscription 直通、Worker 回報狀態（至少含 progress、ready、waiting、blocked、failed、dropped）、面板先列「需要人」的票 | [docs/001](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/001-domain.md)、[docs/003](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/003-execution.md)、[docs/005](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/005-panel.md) |

---

## 3. 可借鑒的機制，與你的場景的對應

原型和文章的哲學一句話：盡量少占用人的注意力、盡量多給價值，只在被要求或有書面規則許可時行動，只在人必須行動或能用上結果時才開口 [docs/000](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/8c32a9dc5d72c033816c6a8110b37f40cf94fba4/docs/000-philosophy.md)【一手】。下表右兩欄是【推論】。

| 機制 | 一手出處 | 在你的流程裡對應什麼 | 借鑒方式 |
|---|---|---|---|
| Router 只派工與回報，不執行、不需要 Bash | 文章 §2.1 | 「彙整 agent」 | 彙整 agent 的工具只給：讀寫 GitHub issue／label／comment。不給 Polymas、不給 repo 寫入、不給 computer use |
| Worker 不直接對人，唯一出口是回報 | 文章 §2.2 | 做能力訓練／批閱／專家智能體的各 worker | worker 只在自己的 issue 留結構化回報；使用者只讀彙整 agent 的一份報告 |
| 結構化回報狀態＋「先列需要人的」視圖 | docs/003、docs/005 | 你現在要逐個 session 看進度 | 用 label 表達 ready／waiting／blocked／failed／dropped；彙整報告第一段永遠是「需要你決定的」 |
| 兩段過濾，先程式後模型 | 文章 §3.1、docs/002 | 企業微信裡大量閒聊、咨詢 | 第一段用程式規則（安排人白名單、是否含附件或 DDL 字樣），第二段才讓模型判斷是否為明確分派 |
| `observe` 模式：先只記錄「本來會接」，確認準了再放權 | docs/002 | 初期不信任自動建單 | 初期讀取結果只建 `needs-triage` 的 issue，不派 worker |
| Trigger 不可變、同一事件只建一張票 | docs/001 | 同一則分派不能重複建 issue | 去重鍵＝安排人＋原消息日期＋附件 SHA-256（你的歸檔清單本來就記 SHA-256） |
| 每票獨立目錄／工作樹（準備指令通常是 `git worktree`） | docs/003 | 你多次踩到並行互相覆蓋（見 §5.1 的記憶條目） | 每個 worker 一個 worktree，所有 ID 顯式傳入，不讀根目錄共用的 `.env` |
| Mandate：授權範圍不可變，擴大範圍須開新票 | docs/001、docs/002 | 子代理越界、同名檔案覆蓋 | issue 正文固定欄位：範圍邊界、輸出檔名、禁止自行部署 |
| 一次確認、一次一問、短訊息（IM ≤100 字） | 文章 §4.2、docs/000 | 彙整報告的格式 | 報告「先結論、再列等你的事項」，每事項一個具體問題 |
| 誠實交付：開 PR 不等於完成、失敗如實報告 | docs/000 | tester 假通過、任務「完成」的判定 | 彙整只採信證據欄（平台回讀結果、對話紀錄校驗），不採信 worker 自報 |
| 桌面不預留：跨 Session 的 observe-act-verify 由呼叫端協調 | computer-use 文件 | 企業微信只有一個桌面 | 只允許一個 Source worker 持有 GUI；其他 worker 永不碰桌面 |
| 外部文字只是資料，不能改變權限 | docs/002、docs/004 | 企業微信訊息與附件內容 | 提示詞注入防線寫進程式（白名單、動作白名單），不寫在提示詞裡 |

---

## 4. 補充：三家官方文件中對該工作流有決策價值的事實

### 4.1 OpenAI（ChatGPT 桌面應用與 Codex）

我抓取 `developers.openai.com/codex/...` 時，頁面標題顯示為 ChatGPT Learn，內容與 `learn.chatgpt.com/docs/...` 的 Markdown 版同源。

| 論斷 | 來源 | 等級 |
|---|---|---|
| Computer Use 在受支援地區可用於 macOS 與 Windows。macOS 可在你使用其他 App 時於背景執行範圍明確的任務；**Windows 在前景作用桌面上執行**，會接管指標與鍵盤，要離開時建議用手機遙控或放進 VM | [Computer Use](https://developers.openai.com/codex/app/computer-use) | 一手 |
| 系統權限（macOS 的 Screen Recording、Accessibility）與 App 授權是兩層；每個 App 會先詢問，可選 Always allow；管理員可限制可用 App | 同上 | 一手 |
| 不能自動化終端機 App 與 ChatGPT 自身，不能以管理員身分驗證，也不能核准安全／隱私權限提示；Computer Use 擷取的螢幕截圖適用 ChatGPT 的資料控制設定 | 同上 | 一手 |
| 官方建議：目標 App 有外掛或 MCP 時優先用結構化整合；Computer Use 留給必須看畫面才能做的事 | 同上 | 一手 |
| 桌面應用的排程任務在背景執行，本機專案需要電腦開著且 App 運行；任務可在本機專案或隔離 worktree 跑；**Scheduled 視圖相當於收件匣**，有發現的 run 會標未讀 | [Scheduled tasks](https://developers.openai.com/codex/app/automations) | 一手 |
| 事件觸發（Gmail、Slack 新訊息、GitHub 的 PR 活動）只在網頁／行動版，**桌面應用、CLI、IDE 擴充都沒有**；單一任務不能同時用事件觸發與時間排程；文件所列 GitHub 觸發是 PR 活動，沒有 issue | 同上 | 一手 |
| Subagents：目前 Codex 版本預設啟用，但要在你明確要求、或 AGENTS.md／skill 指示要求時才會委派；token 消耗高於單一 agent；文件提醒寫入密集的並行工作要更小心 | [Subagents](https://developers.openai.com/codex/subagents) | 一手 |
| `/goal`：把結果、限制、驗證方式寫成完成條件讓 agent 自檢；網頁版文件提醒避免讓兩個任務對同一個連接來源有寫入權 | [Long-running work](https://learn.chatgpt.com/docs/long-running-work.md) | 一手 |
| Activity 視圖集中顯示未讀、執行中、等待你回應的 chat；浮動 pet 顯示 Running／Needs input／Ready／Blocked | [Notifications](https://learn.chatgpt.com/docs/notifications.md) | 一手 |
| 手機可對已連線的 Mac／PC 啟動、引導、批准任務，電腦須保持喚醒且連網 | [Codex on mobile](https://learn.chatgpt.com/docs/mobile.md) | 一手 |
| 「dot」：常駐雲端的助理，可開 Codex 工作、跟進既有 Codex thread、把工作分給背景 agent 並彙整；文件提醒 run 完成不代表結果真的達成或送達。**我沒有驗證你的帳號是否有此功能** | [Tasks and memory](https://learn.chatgpt.com/docs/dots/tasks-and-memory.md)、[2026-10-09 更新說明](https://learn.chatgpt.com/docs/whats-new/dots-october-9-2026.md) | 一手 |
| Linear 整合：把 issue 指派給 Codex 或 @Codex，Codex 開雲端 chat 並回報進度。這是一手的「issue 即任務佇列」範例，但對象是 Linear，不是 GitHub issue | [Codex in Linear](https://learn.chatgpt.com/docs/third-party/linear.md) | 一手 |
| `openai/codex-action@v1`：在 GitHub Actions 中跑 `codex exec`，可指定 sandbox，範例是 PR 審查 | [Codex GitHub Action](https://learn.chatgpt.com/docs/github-action.md) | 一手 |

### 4.2 Anthropic（Claude Code）

| 論斷 | 來源 | 等級 |
|---|---|---|
| 官方列出五種並行方式：subagents、agent view、agent teams、projects、dynamic workflows；agent view 的 session 只向你回報結果，要在 session 之間傳遞發現須另用 cross-session messaging | [Run agents in parallel](https://code.claude.com/docs/en/agents.md) | 一手 |
| Agent view（`claude agents`）：一個畫面派發與監看背景 session，分「需要你」「執行中」「已完成」；研究預覽；session 在本機，電腦關機就停；每個 session 獨立耗訂閱額度；派發的 session 在改檔前會進入自己的 worktree | [Agent view](https://code.claude.com/docs/en/agent-view.md) | 一手 |
| Agent teams：實驗性、預設關閉；共享 task list（pending／in progress／completed，可設 blockedBy），認領任務用檔案鎖防競爭；限制含不支援 resume in-process 隊友、每個 session 只有一個 team、不可巢狀；token 隨隊友數線性增加 | [Agent teams](https://code.claude.com/docs/en/agent-teams.md) | 一手 |
| Projects：一個長期對話，由 Claude 開並行 thread（預設為雲端 session），Overview 面板顯示哪些 thread 在「Waiting on you」；需要本機資源時可讓 thread 經 Remote Control 跑在你的電腦上。公開 beta，限 Pro／Max／Ultra，**Team／Enterprise 方案暫不提供**，逐步推出 | [Projects](https://code.claude.com/docs/en/claude-projects.md) | 一手 |
| Scheduled tasks（舊稱 routines）：在雲端依排程、API 呼叫或 GitHub 事件（Pull request、Release、**Issue**）觸發；研究預覽；另有桌面排程與 `/loop` 在本機跑 | [Scheduled tasks](https://code.claude.com/docs/en/routines.md) | 一手 |
| Channels：用 MCP server 把訊息、webhook 推進**執行中**的 session，可雙向回覆；研究預覽，內建 Telegram／Discord／iMessage，可自建；事件只在 session 開著時送達 | [Channels](https://code.claude.com/docs/en/channels.md) | 一手 |
| CLI computer use：macOS、研究預覽，需 Pro／Max／Ultra，**Team／Enterprise 不可用**，且需互動 session（不能用 `-p`）；選用順序是 MCP → Bash → Claude in Chrome → computer use | [Computer use](https://code.claude.com/docs/en/computer-use.md) | 一手 |
| GitHub Actions 整合：回應 `@claude` 提及，可把 issue 變成 PR | [GitHub Actions](https://code.claude.com/docs/en/github-actions.md)（僅讀頁面索引描述） | 一手 |

### 4.3 GitHub

| 論斷 | 來源 | 等級 |
|---|---|---|
| Sub-issues：每個父 issue 最多 100 個子項，最多 8 層，需 triage 以上權限 | [Adding sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues) | 一手 |
| Issue 依賴（blocked by／blocking）：每種關係最多連 50 個 issue；REST 有 `GET/POST .../issues/{n}/dependencies/blocked_by` 等端點 | [Creating issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)、[changelog](https://github.blog/changelog/2025-08-21-dependencies-on-issues/)、[REST](https://docs.github.com/en/rest/issues/issue-dependencies) | 一手 |
| 一個 issue 最多可有 10 位 assignee，所以「assignee 非空」不等於獨占認領 | [Assigning issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users) | 一手 |
| `issues` 事件可觸發 Actions（含 opened、assigned、labeled 等類型）；workflow 檔須在預設分支；公開 repo 的排程 workflow 在 60 天無活動後自動停用 | [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) | 一手 |
| 速率：個人 token 5,000 次／小時；`GITHUB_TOKEN` 每 repo 1,000 次／小時；次級限制含同時請求不超過 100 | [Rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) | 一手 |
| Projects 可加自訂欄位（含內建共最多 50 個）、表格／看板／路線圖視圖，並可自動化 | [About Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects) | 一手 |
| 文件稱 gh CLI 有 `gh issue create --parent`、`gh issue edit --add-sub-issue／--add-blocked-by`；我本機的 gh 2.91.0 說明中**沒有**這些旗標 | [Adding sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues)；本機 `gh issue create --help` | 一手＋本機實測 |

---

## 5. 對你的工作流的含意

### 5.1 現有做法與設計思想的差距

現有做法來自 `docs/agents/wecom-task-intake.md`、`docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md`、`docs/task-intake/` 與專案記憶索引（均只讀）。

| 面向 | 你現在 | 設計思想 | 差距 |
|---|---|---|---|
| 讀企業微信 | 全程用應用界面與本地檔案操作；明確不用企業微信 CLI；原件用 Spotlight 定位已下載附件 | Source 把事件變成不可變 Trigger，去重、記讀取位置 | 沒有自動讀取；也沒有穩定的去重鍵 |
| 任務佇列 | 本機 `docs/task-intake/<日期>-<名稱>/任務台賬.json`（欄位含標題、安排人、截止依據、截止字段、待辦、原件、待確認），目錄目前未入 git | Ticket 加 Mandate | 佇列載體是本機 JSON，不是 GitHub issue |
| GitHub issue | 文件已定義 `gh`＋`wayfinder` 地圖／子 issue／原生依賴／`--add-assignee @me` 認領 | 同構 | **文件有、實際幾乎未用**：全史只有 1 個 issue（#3，已關閉），無 `.github/` |
| Label | 文件規定五個 triage label | 狀態要機器可讀 | 遠端只有 GitHub 預設 9 個 label，五個中只有 `wontfix` 存在 |
| 派工 | herdr 多 pane 手動下發、子代理指令要手動寫範圍邊界（記憶索引多條教訓） | Router 派工，Mandate 固定範圍 | 派工靠人 |
| 回報 | 逐 session 查看 | 單一出口、先列需要人的 | 沒有彙整層 |
| 完成判定 | 台賬已區分「任務已記錄／附件已歸檔／原件校驗通過／待辦已保存／截止字段已核對」五個狀態 | 誠實交付 | **已有雛形**，可直接變成回報欄位 |

### 5.2 組件分工草圖（【推論】）

```
[企業微信]  ──(唯一持有 GUI 的 Source worker：Codex computer use，只讀)──▶ 台賬／去重
                                                                          │
                                                                          ▼
                                         [私有 GitHub repo：issue = Ticket；label = 狀態]
                                                   ▲            │ 領取（label＋comment 協議）
                              結構化回報(comment)  │            ▼
                                         [Worker×N：各自 worktree，不碰 GUI、不對人說話]
                                                   │
                                                   ▼ 讀 issue 狀態
                                     [彙整 agent：只讀寫 issue，定時產出一份報告]
```

各格的一手支持程度：

- **Source worker（computer use 讀企業微信）**：Codex 與 Claude Code 都有官方 computer use，但都是「範圍明確的任務、你在場可接管」的定位；Codex 在 macOS 可背景執行，Claude Code CLI 的 computer use 限 Pro／Max／Ultra 且必須互動 session（§4.1、§4.2）。**沒有任何一份官方文件示範「無人值守、定時、讀即時通訊軟體」**。
- **issue 作佇列**：GitHub 一手提供 sub-issues、依賴、label、assignee、Actions 的 `issues` 事件；Codex 的事件觸發只列 GitHub PR 活動、不含 issue；**Claude Code 的雲端 scheduled tasks 支援 Issue 事件觸發**（opened、edited、closed、reopened、labeled、assigned 等，須安裝 Claude GitHub App，雲端執行、只有新 clone，碰不到本機企業微信）。若要本機 worker 在 issue 出現時啟動，仍需自己輪詢（原型自己就是輪詢，預設一分鐘）或自架 Actions。此處我在初稿中曾誤寫「Claude Code 也不含 issue」，已更正，細節見 [增量查證檔](./2026-11-09-superagent-workflow-delta.md)。
- **認領協議**：assignee 可多人，不能當互斥鎖（§4.3）；Claude Code agent teams 用檔案鎖認領是本機 task list，不是 GitHub。需要自訂協議，例如「加 `claimed` label 後再讀一次確認自己是唯一認領者」。
- **彙整 agent**：沒有任何一份一手文件把「彙整回報」做成現成開關。最接近的是 Claude Code Projects 的 Overview（Team／Enterprise 不提供）和 OpenAI 的 dot（我未驗證可用性）；其餘可用 Codex 桌面的排程任務（Scheduled 視圖當收件匣，但機器要開著）或 Claude Code 的排程自行實作。

### 5.3 風險（依嚴重度）

1. **公開 repo 放任務內容。** `richardzhangy26/Skills_Training_Course` 是 PUBLIC（`gh repo view` 實測）。企業微信分派含學校名、課程名、老師要求與 DDL，不應進公開 issue。佇列請另開私有 repo。
2. **截圖外送。** Computer use 的截圖屬模型方資料控制範圍（OpenAI 文件明說）；企業微信私聊與附件會被截圖處理。DSH 的 computer use 同樣把截圖交給所選模型路由（見 computer-use 文件的「Results」段）。這是流程設計上的資料外送決定，需要你自己拍板。
3. **提示注入。** 企業微信訊息與附件是不可信輸入。設計文章 §8.4 把這列為未解問題。原型的做法是讓權限由程式判定、外部文字只當資料；若 worker 帶有部署權或平台寫入權，被誘導的代價高（你的腳本會寫正式平台）。
4. **GUI 讀取的穩定性。** Claude Code 文件稱 computer use 是最廣也最慢的手段，OpenAI 文件建議有結構化整合時優先使用；你已明確不用企業微信 CLI（`wecom-task-intake.md` 第 31 行），所以這是你已作的取捨，但應預期它會偶發失誤，必須靠「讀回驗證」與冪等去重兜底。
5. **成本。** Codex subagents 與 Claude Code agent view／teams 的文件都明說 token 或額度隨並行數近似線性上升。設計文章自己的實驗也顯示多 session 用較多 cache-read token，換取更短更穩的完成時間。

### 5.4 最小下一步（【推論】，不是要現在做）

1. 先決定佇列放哪：新建**私有**專用 repo，並在該 repo 實際建立五個 triage label 與狀態 label（ready／waiting／blocked／failed／dropped）。
2. 把現有台賬 JSON 欄位對映成 issue 範本，其中加「範圍邊界、輸出檔名、禁止自行部署」與 SHA-256 去重鍵。
3. 先不接 computer use：手動貼任務建 issue，跑通「worker 回報 → 彙整報告」這一段，再評估 Source 自動化是否值得。
4. 彙整 agent 初版做成定時讀 issue 的單一排程任務，輸出固定格式：先列需要你的，再列進度。
5. 若之後接 Source，採 `observe` 思路：前兩週只建 `needs-triage`，不派 worker。

不建議：直接部署 `dsh-superagent-prototype`。它的事件源是 GitHub／飛書、worker 以 `danger-full-access` 跑在你的 OS 使用者下、原型自稱研究代碼；你的機器上有 `secrets.json`、可解密 Chrome Cookie 的流程，風險評估見 [既有繁體筆記 §4–§5](./2026-11-04-deepseek-super-agent.zh-Hant.md)。

---

## 6. 查不到或不確定的事項

1. **微信中文原文**：我的抓取只得到「環境異常」驗證頁，未讀到。以 X 英文機器翻譯版為準；翻譯可能有措辭偏差。簡體版筆記對微信原文的引用我無法複核。
2. **X 帳號歸屬**：`@DeepSeekHarness` 發布的文章標題與原型 README 所引一致、內容末段直指原型。但 deepseek.com 官方頁面連結的 X 帳號是 `@deepseek_ai`，沒有直接連到 `@DeepSeekHarness`，所以「官方」是由內容佐證而非連結佐證。
3. **DeepSeek 官方 App 商店頁面**：未取得（見 §2.1 #6）。
4. **官方是否有「Super Agent」產品或 API 能力**：在上述官方頁面都查無；這是缺席證據，不能排除只在未檢查的頁面出現。
5. **「R2」**：官方 Research 清單列出的是 V4.1、V4、V3.2、V3.1、R1、V3，沒有 R2。
6. **superagent 是否真的不能用 computer use**：我只讀了文件與設定，沒讀 `src/` 全部檔案，也沒運行；§2.2 #11 是「在已讀範圍內查無」。
7. **Super-agent 的實際運行行為、成本、與最新 DSH 預發布的相容性**：均未運行驗證。
8. **OpenAI dot 與 Claude Code Projects 對你的帳號是否可用**：未驗證；後者文件寫明 Team／Enterprise 方案暫不提供。
9. **你的 Codex 版本是否已有 Computer Use 的 Any App 設定**：未檢查你的機器。
10. **企業微信桌面端本身能否被上述 computer use 穩定操作**：無任何一手文件涵蓋，需實測。
11. 本機已有一個名為 `wecom-unified` 的技能（技能清單可見），我沒有讀它的內容，不知道它與本文流程的關係。
12. 星標數、release 版本會變動，僅代表 2026-11-09 的快照。
