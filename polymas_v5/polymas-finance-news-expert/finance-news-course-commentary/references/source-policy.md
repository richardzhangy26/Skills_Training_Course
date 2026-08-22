# 公开来源策略

只使用无需绕过访问控制即可核验的公开来源。按以下顺序收集和排序，且每条新闻保留来源名称、URL、发布时间和检索时间。

## 三级优先级

1. **监管/政府/交易所/公司公告**：监管机构、政府部门、交易所、上市公司和发行人的正式公告。作为一级来源，优先用于事实确认。
2. **权威财经媒体**：有明确编辑责任、原始报道或透明署名的财经媒体。作为二级来源，可用于补充背景并应尽量与一级来源交叉核对。
3. **其他公开页面仅作线索**：博客、聚合页、社交转述、搜索摘要和来源不清晰页面只能提供检索线索；必须找到独立的一、二级公开来源后才可进入候选。

## 官方优先域/机构名单

一级来源优先核验以下官方域或机构发布的原始材料：国务院、人民银行、财政部、国家统计局、金融监管总局、证监会、上交所、深交所、北交所、公司公告。常见官方域包括 `www.gov.cn`、`pbc.gov.cn`、`mof.gov.cn`、`stats.gov.cn`、`nfra.gov.cn`、`csrc.gov.cn`、`sse.com.cn`、`szse.cn`、`bse.cn` 与法定信息披露渠道；域名仅用于识别线索，仍以公开正文、发布主体和发布时间核验为准。

二级媒体补充名单为新华社、央视财经、中国证券报、上海证券报、证券时报。它们可补充背景，不替代可获得的一级原始公告。

来源等级相同时，优先发布时间更明确、原始材料更完整且与课程知识点更贴近的页面。重复 URL 或同一新闻的相似标题由 normalizer 按确定性规则保留一个候选。

平台通用工具返回候选后，编排方必须在 normalizer 前为每条候选声明 `source_tier`：一级使用 `official`、`primary`、`regulator`、`government`、`exchange` 或 `company_announcement`；二级使用 `authoritative_media` 或 `media`；三级使用 `other`。但声明不是信任依据：normalizer 使用内部 hostname allowlist 推导等级，声明与推导不一致时返回 `source_tier_mismatch`；未列入域名返回 `untrusted_source`。

内部 hostname allowlist 的一级根域为 `gov.cn`、`pbc.gov.cn`、`mof.gov.cn`、`stats.gov.cn`、`nfra.gov.cn`、`csrc.gov.cn`、`sse.com.cn`、`szse.cn`、`bse.cn`、`cninfo.com.cn`；二级根域为 `news.cn`、`xinhuanet.com`、`cctv.com`、`cs.com.cn`、`cnstock.com`、`stcn.com`。只匹配根域本身或真实子域，不使用字符串后缀猜测。不得传入 `source_level`。

normalizer 强制拒绝三级来源：它先强制校验 `source_tier`，无论 `other` 页面是否被误传入，都会进入 `rejected` 并标记 `untrusted_source`，不得成为最终 `source`、`url` 或 `items`。三级页面可保留在检索笔记中，但事实结论仍需由一级或二级允许来源支撑。

## 允许与禁止

- 允许：直接访问公开正文、公告、公开新闻稿和无需登录的媒体页面。
- 禁止：要求账号、Cookie、付费订阅、验证码或反爬验证的内容；不得绕过登录墙、付费墙、安全页或反爬机制。
- 禁止：把搜索结果摘要、转述或无法确认发布时间的页面当成事实依据。
- 禁止：私网/本机 IP、`localhost`、内部域、URL userinfo 或未列入域名；域名尾点和 URL dot-segment 会在匹配前规范化。
- 禁止：使用实时行情接口、付费数据账户、第三方 API Key 或任何真实用户凭证。

## 记录与不确定性

每条最终候选必须记录来源名称、规范化 URL、发布时间、检索时间和来源等级。事实无法由允许来源确认时拒绝该候选；课程证据无法确认时交由 normalizer 标为课程证据不足，不以常识代替课程材料。
