# GitHub Fork 工作流程指南

## 概述

Fork 工作流程是开源协作的标准模式，适用于：
- 为开源项目贡献代码
- 在保持上游更新的同时进行自定义开发
- 多人协作时的分支管理

```
┌─────────────────────────────────────────────────────────────────┐
│                        上游仓库 (upstream)                        │
│                    github.com/原作者/项目                         │
│                          只读权限                                │
└──────────────────────────────▲──────────────────────────────────┘
                               │
                               │ Pull Request
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                              │                                  │
│   ┌──────────────────┐       │       ┌──────────────────┐      │
│   │   你的 Fork       │◄──────┘──────►│   其他贡献者      │      │
│   │  (origin)        │               │   的 Fork        │      │
│   │  完全控制        │               │                 │      │
│   └────────┬─────────┘               └─────────────────┘      │
│            │                                                   │
│            │ clone / push / pull                               │
│            ▼                                                   │
│   ┌──────────────────┐                                         │
│   │    本地仓库       │                                         │
│   │  日常开发工作     │                                         │
│   └──────────────────┘                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 初始设置

### 1. Fork 仓库

在 GitHub 网页上点击 **Fork** 按钮，将仓库复制到你的账号下。

### 2. 克隆你的 Fork

```bash
# 克隆你的 fork（不是原始仓库）
git clone https://github.com/你的用户名/项目名.git
cd 项目名
```

### 3. 添加上游仓库

```bash
# 添加原始仓库作为 upstream
git remote add upstream https://github.com/原作者/项目名.git

# 验证配置
git remote -v
# origin    https://github.com/你的用户名/项目名.git (fetch/push)
# upstream  https://github.com/原作者/项目名.git (fetch/push)
```

---

## 日常开发流程

### 1. 同步上游更新

在开始新功能前，确保你的 fork 是最新的：

```bash
# 获取上游更新
git fetch upstream

# 切换到 main 分支
git checkout main

# 合并上游更新到本地 main
git merge upstream/main

# 推送到你的 fork
git push origin main
```

### 2. 创建功能分支

```bash
# 基于最新的 main 创建分支
git checkout -b feature/your-feature-name

# 或使用前缀区分类型
git checkout -b feat/new-login
git checkout -b fix/memory-leak
git checkout -b docs/api-reference
```

### 3. 开发与提交

```bash
# 开发代码...

# 添加和提交
git add .
git commit -m "feat: 添加新功能 X

- 实现核心逻辑
- 添加单元测试
- 更新文档"

# 推送到你的 fork
git push -u origin feature/your-feature-name
```

### 4. 创建 Pull Request

1. 访问 GitHub 你的 fork 页面
2. 点击 **Compare & pull request**
3. 填写 PR 描述：
   - 标题清晰描述变更
   - 说明改动原因和实现方式
   - 关联相关 Issue

```markdown
## 描述
修复了登录页面的内存泄漏问题

## 改动
- 修复了未正确释放的事件监听器
- 添加了组件卸载时的清理逻辑

## 测试
- [x] 本地测试通过
- [x] 单元测试通过

Fixes #123
```

---

## 处理审查反馈

### 1. 本地修改

```bash
# 在功能分支上修改代码
git checkout feature/your-feature-name

# 修改后提交（使用 --amend 保持提交历史整洁，或新建提交）
git add .
git commit --amend --no-edit  # 修改最后一次提交
git push -f origin feature/your-feature-name  # 强制推送
```

### 2. 多轮审查后的整理

```bash
# 交互式 rebase 整理提交历史
git rebase -i main

# 推送（强制）
git push -f origin feature/your-feature-name
```

---

## 高级场景

### 同步 fork 的 main 分支（推荐）

```bash
# 方法1：直接合并上游
git checkout main
git fetch upstream
git rebase upstream/main  # 或使用 merge
git push origin main
```

### 处理上游冲突

```bash
# 在功能分支上同步上游
git checkout feature/your-feature
git fetch upstream
git rebase upstream/main

# 解决冲突后继续
git add .
git rebase --continue
git push -f origin feature/your-feature
```

### Cherry-pick 提交

```bash
# 从其他分支挑选特定 commit
git cherry-pick <commit-hash>
```

---

## 分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能 | `feat/user-auth` |
| `fix/` | Bug 修复 | `fix/login-crash` |
| `docs/` | 文档更新 | `docs/api-guide` |
| `refactor/` | 代码重构 | `refactor/split-utils` |
| `test/` | 测试相关 | `test/add-e2e` |
| `chore/` | 杂项/工具 | `chore/update-deps` |

---

## 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type):**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档
- `style`: 格式调整
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例:**
```
feat(auth): 添加 OAuth2 登录支持

- 集成 GitHub OAuth
- 添加用户会话管理
- 更新登录页面 UI

Closes #456
```

---

## 常见问题

### Q: 为什么 push 到 origin 被拒绝？

```bash
# 检查当前 remote
git remote -v

# 确保 origin 是你的 fork，不是原始仓库
git remote set-url origin https://github.com/你的用户名/项目.git
```

### Q: 如何更新已存在的功能分支？

```bash
git checkout feature-branch
git fetch upstream
git rebase upstream/main
git push -f origin feature-branch
```

### Q: PR 合并后如何清理？

```bash
# 删除本地分支
git branch -d feature/your-feature

# 删除远程分支
git push origin --delete feature/your-feature

# 同步 main
git checkout main
git pull upstream main
git push origin main
```

---

## 最佳实践

1. **一个 PR 只做一件事** - 保持变更范围小而清晰
2. **保持提交历史整洁** - 使用 rebase 整理提交
3. **及时同步上游** - 避免长期分支产生大量冲突
4. **写清晰的 PR 描述** - 帮助审查者理解改动
5. **关联 Issue** - 使用 `Fixes #123` 自动关闭相关 Issue

---

## 速查表

```bash
# 初始设置
git clone https://github.com/你的用户名/项目.git
git remote add upstream https://github.com/原作者/项目.git

# 同步上游
git fetch upstream
git checkout main
git merge upstream/main
git push origin main

# 新功能
git checkout -b feat/new-feature
git commit -m "feat: 描述"
git push -u origin feat/new-feature

# 更新 PR
git add .
git commit --amend --no-edit
git push -f origin feat/new-feature
```
