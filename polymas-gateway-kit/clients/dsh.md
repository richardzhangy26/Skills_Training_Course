# 把 polymas 网关接进 DeepSeek Harness (DSH)

DSH 用 `@deepseek-ai/dsh-llm-pi-ai` 这个适配器接自定义网关，配置写在 profile 的
补丁层里：`~/.dsh/profiles/<profile>/cordis.patch.yml`（改完热加载，无需重启）。

## 配置

在 `llm-pi-ai` 条目的 `providers` 下加一条（或用 `install.sh` 生成的端口）：

```yaml
- id: llm-pi-ai
  name: "@deepseek-ai/dsh-llm-pi-ai"
  config:
    providers:
      polymas:
        displayName: polymas
        apiKeyEnv: POLYMAS_API_KEY      # 密钥存在 DSH 凭据库里，不写在配置文件
        api: openai-completions
        # 指向反代：网关流式分片用 message 而非 delta，直连会拿到空响应
        # 直连写法（网关修好后）：https://llm-service.polymas.com/api/openai/v1/
        baseURL: http://127.0.0.1:8787/v1/
        defaultContextWindow: 262144    # 未单独声明的模型用这个
        defaultMaxTokens: 32768
        models:
          - id: claude-opus-5
          - id: claude-sonnet-5
          - id: claude-opus-4-8
          - id: gpt-5.6-sol
          - id: kimi-k3
          - id: glm-5.2
          - id: deepseek-v4-pro
          - id: qwen3.8-max
```

密钥放进 DSH 凭据库（**不要**写进 YAML）：

- GUI：**设置 → 模型 → 该 provider 的 API 密钥**框里粘贴，保存即可；
- 或者让 `apiKeyEnv` 指向环境变量（`POLYMAS_API_KEY`）。

模型 id 必须是网关里真实存在的，可以列一下：

```bash
curl -s http://127.0.0.1:8787/v1/models -H "Authorization: Bearer $LLM_API_KEY" | head -c 300
```

## 验收

模型选择器里切到该模型发一句；或看会话日志里解析出的上下文窗口：

```bash
# 新建一个会话说句话，然后
zstd -d -c ~/.dsh/sessions/*/session-*/session.v4.jsonl.zstd | grep -o '"contextWindow":[0-9]*' | tail -1
```

## 注意

DSH 自己也会发工具定义。如果网关那边还有「大整数被写成字符串」的问题，
这里同样会撞 `JSON schema is invalid` —— 反代的数值钳制顺带把 DSH 也修了，
所以 DSH 也建议指向反代。

`contextWindow` 先按 256K 设；网关真实上限未确认前不要盲目调到 1M，
否则不会在到顶前优雅压缩，而是直接报上下文超限。
