# 05 Skill 开发、安装与双机同步

## 5.1 SKILL.md 规范

**frontmatter 至少含四个字段**：
```yaml
---
name: my-skill
description: 一句话说明 + 触发词（把用户真实口语写进来）
version: 1.0.0
agent_created: true
---
```

| 坑 | 现象 | 做法 |
|---|---|---|
| **E01 版本强校验** | install 报"更新安装要求新版 version 严格高于旧版" | 覆盖安装前**先查已装 version**；新增兼容能力→MINOR，纯修复→PATCH |
| **E02 漏写 version** | 备份目录名变 `_vunknown_before-xxx` | frontmatter 必含 `version` |
| **E05 触发不命中** | skill 装了不被调用 | 把用户口语（"加进价目表""处理价目表"）写进 `description` |

**目录结构**：`resources-dir` 根级只允许 `scripts/` `references/` `assets/`。
`skill-dependencies.json`（E03）须 render 后**手动放入 skill 根目录**，schema 要求能力闭环（依赖能力 ⊆ 顶层能力、每能力有降级覆盖、setup 8 字段必填、setup-guide.md 覆盖全部依赖 id 与官方 URL）。

## 5.2 打包与分享前检查

- `skill_ops.py validate` 结构校验过
- 全包 grep 无 `C:/Users` 等绝对路径残留（E04：**脚本只写相对路径**）
- 分享前再跑业务词脱敏

## 5.3 ★ 变更须经用户确认（C08）

skill 的修改、删除、口径变更**必须先向用户说明改什么、为什么、影响范围，等确认再执行**，绝不静默更新。
已确认的旧口径被推翻时，保留「原口径（已废止于 日期）→ 新口径」轨迹，不直接删除。

installed 文件有 bug 时：用 monkey-patch wrapper 临时绕过，**正式修复走版本升级**。

## 5.4 版本更新与回退（E12 / E11）

✅ **先备份再改**（顺序不能反）：
```
~/.workbuddy/skills/_backups/{skill}_v{x}_before-{改动}_{date}/
```

❌ 反例：备份是"改完代码、清文档之前"的中途快照，SKILL.md 仍是旧措辞 → **无法回滚到 v1.2.x**。

⚠️ **E11 别用旧版覆盖新版**：覆盖脚本前先 grep 目标文件的关键函数名，确认是"新覆盖旧"不是"旧覆盖新"。手误覆盖曾导致功能丢失。

⚠️ **E10 install 后源目录被清**：`skill-build/` 会被清掉，升级前**先从 installed 反向拷贝一份当 source**。
⚠️ **`.skill-smith/backups/` 是混合快照**，不能当回滚点，需自建干净备份。

## 5.5 ★ 双机同步（001 / 003）

### 同步架构
| 内容 | 通道 |
|---|---|
| **记忆** | 「资料库」共享枢纽（同账号即见），文档型、行并集 |
| **skills** | **Git 私有库中转**（非直连、不走资料库） |

⚠️ **E08**：记忆枢纽只适合文档型，**整目录镜像会撑爆**（单节点 >160KB 触发网关 524、目录结构被破坏）。

### 首次接入
```bash
# 空目录
git clone <私有库> %USERPROFILE%\.workbuddy\skills
# 已有内容
git init && git remote add origin <url> && git fetch
git reset --hard origin/master
git branch --set-upstream-to=origin/master master   # ★ 必须，否则后续 pull 无上游
```
前置备份（`reset --hard` 会丢弃本地改动）：
```cmd
xcopy "%USERPROFILE%\.workbuddy\skills" "D:\skills_backup_003\" /E /I /Y
```

### 排程
- 两机时间**错开 30 分钟**（001 用 17:10、003 用 17:40）避免并发冲突
- 对端关机不影响（拉的是已推送的版本）
- 排程要落在**开机窗口内**，留 30 分钟余量

### 超大 skill 走手动（被 .gitignore 排除）
如 7.5MB / 474KB / 170KB 的目录 git 不传 → 打包 zip（**跳过 `.git`**）手工拷一次。

### 同步后验证
跑 `skill_sync.py --machine 003 --status`，应显示本机 003 / 对端 001、远端已配置、工作区 clean、无冲突。
**跨机闭环 = "在 A 上做 + 在 B 上验证"**，缺 B 验证就是半截流程。

### ⚠️ E13 记忆同步窗口写死 3 天
只处理**最近 3 天每日文件 + 全局 MEMORY.md**。改回全量遍历会把共享节点撑爆——**改一次事故一次**。长节假日用 `--days 7` 临时放宽。

## 5.6 ★ 机器身份必须硬件取证（E09 / F8）

**现象**：凭"上次在哪台做的"猜机器，猜反后所有路径、排程、同步全盘做反。

**根因**：hostname / 用户名 / device-id 是不可信随机值，机器编号是**用户自贴标签**，OS 不知道。

✅ 跨机任务第一步取证并与预先固化的**硬件锚点**比对：
```cmd
hostname
wmic baseboard get Manufacturer,Product
wmic cpu get Name
wmic os get Version
```
全部吻合才继续。

## 5.7 skill 内脚本的路径与输出

- **只写相对路径**（E04）
- 输出到**副本**，不覆盖用户桌面原件
- 测试：TDD + 真实回归（先写测试跑红→改代码→全绿→用真实源表回归）
- 回归出现差异先怀疑**源表被改动**
- 无目标运行时（如本机无 JVM）→ 用 Python 1:1 复刻断言，另附桩测试供真实环境跑
