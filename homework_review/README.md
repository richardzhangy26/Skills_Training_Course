# 作业批改工具

自动化作业上传与 AI 批改工具，支持上传作业文件并调用智能体进行自动批改。

## 前置准备

在 `.env` 文件中配置以下环境变量（可放在当前目录或上级目录）：

```bash
# 平台认证信息（从浏览器开发者工具 Network 标签获取）
AUTHORIZATION=eyJ0eXAiOiJKV1Q...  # JWT token
COOKIE=hike-polymas-identity=1;...  # 完整 cookie 字符串

# 作业批改智能体实例 ID（从平台 URL 获取）
INSTANCE_NID=xxx
```

## 使用步骤

1. 配置好 `.env` 文件

2. 运行批改脚本：
   ```bash
   cd homework_review
   python homework_reviewer.py
   ```

3. 按提示输入要批改的作业文件或者文件夹路径（支持 PDF、Word、图片等格式）

* 文件夹中含有多个学生档位的答案 （推荐） 
* 生成报告可以只生成json格式 速度快（推荐）要好看的话可以生成pdf格式

4. 等待上传和批改完成

## 支持的文件格式

- 图片：`.png`、`.jpg`、`.jpeg`、`.gif`
- 文档：`.pdf`、`.doc`、`.docx`

## 结果查看

批改结果会在终端输出，同时可在平台对应的智能体实例中查看完整批改报告。
