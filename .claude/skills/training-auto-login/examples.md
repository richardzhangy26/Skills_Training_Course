# 智能体课程自动登录 - 使用示例

## 快速开始

### 1. 通过训练剧本文件路径自动登录

```bash
python scripts/auto_login.py /Users/zhangyichi/工作/能力训练/skills_training_course/武夷学院-茶艺学实践/实训任务5/训练剧本配置.md
```

**执行结果：**
```
从路径识别到学校: 武夷学院
匹配到省区: 福建省区
账号: JFFJ1001000000

==================================================
开始执行自动登录流程
==================================================
账号: JFFJ1001000000
目标平台: 智能体课程平台 (Polymas)

[1/6] 正在访问平台首页...
[2/6] 检查登录状态...
[3/6] 等待登录表单加载...
[4/6] 填写登录信息...
  ✓ 已填写账号: JFFJ1001000000
  ✓ 已填写密码
[5/6] 点击登录按钮...
  ✓ 已点击登录按钮
[6/6] 检测验证码...

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
检测到滑块验证码，请手动完成验证
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
完成验证后按回车键继续...

等待登录完成...
✓ 登录成功，已跳转到教学中心

提取认证凭证...
更新 .env 文件...
✓ 已更新环境变量
✓ 会话已保存到 sessions/storage_state.json

==================================================
登录成功！
==================================================

已更新以下环境变量:
  AUTHORIZATION=eyJ0eXAiOiJKV1Q...
  COOKIE=hike-polymas-identity=1;...

✓ 自动登录完成，现在可以使用其他技能进行部署和测试
```

### 2. 直接指定省区登录

```bash
python scripts/auto_login.py --province "天津省区"
```

### 3. 直接指定账号密码登录

```bash
python scripts/auto_login.py --account JFGZ1001000000 --password Zhihuishu@000000
```

## 支持的学校与省区映射

| 学校名称 | 对应省区 | 账号 |
|---------|---------|------|
| 武夷学院 | 福建省区 | JFFJ1001000000 |
| 厦门大学 | 福建省区 | JFFJ1001000000 |
| 天津科技大学 | 天津省区 | JFTJ1001000000 |
| 天津中德 | 天津省区 | JFTJ1001000000 |
| 贵州大学 | 贵州省区 | JFGZ1001000000 |
| 临沂大学 | 山东省区 | JFSD1001000000 |
| 华北理工 | 河北省区 | JFHB1001000000 |
| 湖南中医药大学 | 湖南省区 | JFHN2001000000 |
| 云南农业大学 | 云南省区 | JFYN1001000000 |
| 佳木斯大学 | 黑龙江省区 | JFHLJ1001000000 |

## 使用场景示例

### 场景1：新任务部署前的登录

当你需要部署一个新的训练任务时：

```bash
# 1. 先登录平台
python scripts/auto_login.py /Users/zhangyichi/工作/能力训练/skills_training_course/天津中德-工程图学智能体实训任务-典型零件图识读（传动轴）/训练剧本配置.md

# 2. 登录成功后，运行部署脚本
python auto_script_train.py
```

### 场景2：切换不同省区账号

如果你需要在不同省区的账号之间切换：

```bash
# 切换到福建省区
python scripts/auto_login.py --province "福建省区"

# 切换到贵州省区
python scripts/auto_login.py --province "贵州省区"
```

### 场景3：无头模式（不需要处理验证码时）

如果当前网络环境不需要验证码：

```bash
python scripts/auto_login.py --province "福建省区" --headless
```

## 常见问题

### Q1: 无法识别学校

**问题：** 运行脚本时提示 "无法从路径自动识别省区"

**解决：**
1. 检查文件路径是否包含学校名称
2. 使用 `--province` 参数直接指定省区
3. 在账号表 `智能体课程配置账号情况.xlsx` 里补一行该学校的账号，再用 `--list-accounts 学校名` 确认能查到

### Q2: 验证码自动破解失败

**问题：** 4 次自动破解都没过，脚本转人工

**解决：**
1. 直接重跑即可，滑块每次是新图，单次通过率 60~80%
2. 检查 `scripts/yidun_slider.py` 依赖（opencv-python / numpy）是否正常
3. 仍未过时可手动拖一次，脚本会继续往下走

### Q3: 登录后仍然提示认证失败

**问题：** 登录成功但后续操作提示 401/403

**解决：**
1. 检查 `.env` 文件是否正确更新
2. 重新运行登录脚本
3. 手动从浏览器开发者工具复制最新的 AUTHORIZATION 和 COOKIE

### Q4: 如何查看账号表里的省区 / 学校

```bash
cd .claude/skills/training-auto-login/scripts
python3 auto_login.py --list-accounts            # 全部账号（省份/学校/教工号/密码）
python3 auto_login.py --list-accounts 天津        # 按省份或学校关键字过滤
```

## 集成到工作流

### 在 Python 脚本中调用

```python
import sys
sys.path.insert(0, '/Users/zhangyichi/工作/能力训练/.claude/skills/training-auto-login/scripts')

from auto_login import run_login

# 直接登录
success = run_login(
    account="JFFJ1001000000",
    password="Zhihuishu@000000",
    headless=False
)

if success:
    print("登录成功，继续执行后续操作...")
else:
    print("登录失败")
```

### 在 Shell 脚本中集成

```bash
#!/bin/bash

# 自动登录
python /Users/zhangyichi/工作/能力训练/.claude/skills/training-auto-login/scripts/auto_login.py \
    --province "福建省区"

# 检查登录是否成功
if [ $? -eq 0 ]; then
    echo "登录成功，开始部署任务..."
    python auto_script_train.py
else
    echo "登录失败，请检查错误信息"
    exit 1
fi
```

## 更新账号（唯一来源：账号表）

账号统一维护在根目录 `智能体课程配置账号情况.xlsx` 主段，加一行即可：

```
对应省份 | 教工号 | 学校/机构 | 机构名称 | 默认密码 | 手机号 | 备注
天津     | TJU000000 | 天津大学 | Polymas实验室 | Zhihuishu@000000 | 14950000005 |
```

校验：`python3 auto_login.py --list-accounts 天津大学`；登录：`--school "天津大学"`。

## 注意事项

1. **首次使用需要安装依赖：**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **会话有效期：** 登录状态可能会过期，如遇到问题请重新运行脚本

3. **.env 文件备份：** 脚本会直接修改 `.env` 文件，建议定期备份
