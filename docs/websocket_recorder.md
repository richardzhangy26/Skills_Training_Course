# WebSocket 对话录制脚本

`websocket_recorder.py` 用于监听网页端 WebSocket 帧，并生成项目现有可用的对话日志：

- `*_raw_ws_frames.jsonl`: 原始 WebSocket 帧，默认脱敏。
- `*_parsed_messages.jsonl`: 解析出的候选对话消息。
- `*_dialogue.json`: 兼容现有评测/回放的 JSON 对话日志。
- `*_dialogue.txt`: 人可读对话日志。

## 安装依赖

```bash
pip install playwright
python -m playwright install chromium
```

## 最小运行

```bash
python websocket_recorder.py \
  --url "https://你的训练网页地址" \
  --task-id "任务ID" \
  --profile manual
```

脚本会打开浏览器。你在页面里完成一次训练对话后，回到终端按 Enter 结束录制。

默认输出到：

```text
log/task_<任务ID>/manual/
```

## 常用参数

只录制某个 WebSocket：

```bash
python websocket_recorder.py \
  --url "https://你的训练网页地址" \
  --task-id "任务ID" \
  --ws-url-filter "/websocket"
```

固定录制 120 秒：

```bash
python websocket_recorder.py \
  --url "https://你的训练网页地址" \
  --task-id "任务ID" \
  --duration 120
```

如果启发式解析不准，可以显式指定字段路径：

```bash
python websocket_recorder.py \
  --url "https://你的训练网页地址" \
  --task-id "任务ID" \
  --sent-content-path "data.userAnswer,data.content" \
  --received-content-path "data.questionText,data.content" \
  --step-id-path "data.stepId" \
  --step-name-path "data.stepName"
```

字段路径使用点号访问 JSON，例如 `data.message.content`。

## 用已有 Chrome 登录态

如果页面必须使用你当前 Chrome 的登录态，可以用远程调试端口启动 Chrome：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-ws-recorder
```

在这个 Chrome 里登录平台后运行：

```bash
python websocket_recorder.py \
  --cdp-url "http://127.0.0.1:9222" \
  --url "https://你的训练网页地址" \
  --task-id "任务ID"
```

## 需要提供的信息

第一轮只需要：

1. 训练网页 URL。
2. `task_id`。
3. 页面是否需要登录；如果需要，建议用上面的 Chrome 远程调试方式登录。

如果自动解析出来的 `*_dialogue.json` 不准，再提供：

1. 一小段 `*_raw_ws_frames.jsonl` 样例，保留 1 条发送消息和 1 条接收消息即可。
2. 哪个字段是用户回答，例如 `data.userAnswer`。
3. 哪个字段是 AI 回复，例如 `data.questionText`。
4. 哪个字段是 `step_id`，例如 `data.stepId`。

注意：原始帧默认会脱敏，但发送样例前仍建议检查是否包含 Cookie、Authorization、手机号等敏感信息。
