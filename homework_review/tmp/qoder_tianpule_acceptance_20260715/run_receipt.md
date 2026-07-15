# Loopy 运行收据：天谱乐作业批阅 Skill 优化

## 定义

观察当前 skill、媒体提取结果和 QoderCLI 基线；每轮选择一个有证据支持的最小可逆修改，运行本地测试和同附件 QoderCLI 验收并记录结果；当原始 stdout 可直接解析、结构正确且总分不低于 90 时成功停止，修改无改善时以无进展停止，外部故障无法由 skill 修复时以阻塞停止。

## 范围

- 修改：`grade-low-carbon-ai-voiceover` 的媒体支持、评分规则、ASR 降级和 JSON 输出契约。
- 测试附件：`作业.mp4`。
- 模型：`qmodel_latest`。
- 未修改学生作业或其他项目文件。

## 验收条件

1. QoderCLI 退出码为 0。
2. 原始 stdout 可直接由 `json.loads` 解析。
3. 顶层只有 `score`、`evaluations`。
4. 总分不低于 90。
5. 五维标识、满分、得分之和与边界正确。
6. 四个评价项格式正确。
7. 不因 MP4 格式、ASR 不可用、独立音乐长于成品或独立配音为单声道本身扣分。

## 轮次

| 轮次 | 修改 | 得分 | 原始 JSON | 结果 |
|---|---|---:|---|---|
| 基线 | 未修改 skill | 83 | 失败 | MP4 被标记不支持，ASR失败后保守扣分 |
| 第1轮 | 支持 MP4/MOV，加入80分保底、新五维和ASR降级 | 86 | 失败 | JSON有英文前缀且字符串含未转义双引号 |
| 第2轮 | 增加 JSON 正向组合配方 | 86 | 通过 | 输出结构通过，分数不足90 |
| 第3轮 | 要求所有扣分基于可复核缺陷 | 90 | 通过 | 全部验收条件通过 |

## 最终结果

**Success**

- QoderCLI 退出码：0。
- 总分：90。
- 五维得分：23/25、17/20、22/25、15/15、13/15。
- 原始 stdout：可直接 `json.loads`。
- 本地测试：8项全部通过。

## 证据位置

- 第1轮：`round1/stdout.json`、`round1/stderr.log`。
- 第2轮：`round2/stdout.json`、`round2/stderr.log`。
- 第3轮：`round3/stdout.json`、`round3/stderr.log`、`round3/validation.json`。
