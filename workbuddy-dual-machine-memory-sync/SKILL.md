---
name: workbuddy-dual-machine-memory-sync
description: 两台 WorkBuddy 机器（如 001/003）本地记忆与 skill 双向自动同步的可复用方案。记忆走「资料库」共享枢纽（文档型、行并集）；skill 走 Git 中转（整目录镜像、大文件豁免、冲突合并）。覆盖架构、已踩坑清单、合并膨胀修复、路径自动探测、自动化配置、Git 仓库初始化与一键 push/pull。当需要在多台 PC 之间同步 WorkBuddy 本地记忆与用户级 skills 时使用。
agent_created: true
---

# 两台 WorkBuddy 机器记忆双向自同步

## 何时用
- 用户有两台（或多台）WorkBuddy PC，希望本地记忆自动互相同步，不再手工当传话人。
- 枢纽选型：**资料库（skill-library）** 的文档节点当共享存储（不是网盘同步，是脚本推送/拉取）。
- 关键前提：两台机器各自有独立的 **工作区 id 目录**（`C:\Users\Administrator\WorkBuddy\<wsid>\`），且全局记忆都在 `C:\Users\Administrator\.workbuddy\MEMORY.md`（用户级，两台路径一致）。

## 架构（已验证可行）
1. 每台机器把本机记忆拆成小片段：
   - 全局 `MEMORY.md` 单独 1 个节点（≈29KB）；
   - 每个每日文件 `YYYY-MM-DD.md` 各 1 个节点（几 KB）。
2. 推送节点命名：`sync-<机器>-<时间戳>-global` / `sync-<机器>-<时间戳>-daily-<日期>`。
   - 父目录固定（如 `ppKKSZHTReh1biczEokyJM`）、空间固定（如 `0F1IiYtSfK29W0zTDJJG9d`）。
3. 拉取对方**最新一次批次**（按时间戳分组），解析后做**并集**写回本机：
   - 全局：按 `##` 二级标题并集（保留本机段落，补对方独有段落）；
   - 每日：按行并集（保留本机行，补对方独有行）。
4. 时序错开：001(17:00) 先推 → 003(17:30) 后拉 → 双向闭环。

## 已踩坑清单（必读，避免重蹈）

### 鉴权 / 资料库 API（B 类）
- **B1 token 注入**：官方脚本客户端模式必须运行时调 `connect_open_platform` 取 `op_xxx` token，经 `--token-stdin` 注入。裸跑 = `INVALID_PARAMS` / `NETWORK_ERROR`。沙箱模式（`X_IDE_IS_CLOUDSTUDIO=true` 走 auth-proxy）在本地 PC 不可达。
- **B2 HTTP_524 网关超时**：单文档 >~160KB 触发。必须拆分推送（全局 1 节点 + 每每日文件 1 节点）。
- **B3 无删除 API**：资料库节点不支持删除，只能 `rename-node` 改名（如 `zzz-ignore-*`）规避匹配，或在 UI 手动删。
- **B4 参数用驼峰**：`get-doc-review` 用 `--space-id` + `--page-id`，不是 `--space_id` / `--page_id`。
- **B5 submit-doc-edit 的 action.type 是【字符串数字】**：`"2"`=insert_after、`"1"`=insert_before、`"3"`=delete，不是枚举名。传错会被置零成 Unspecified，导致"整篇覆盖"从未成功。
- **B6 524 幽灵节点**：网关超时但服务端已建节点 → 用 `move-node` 移出父节点到空间根，再 UI 手动删。

### 同步脚本（C 类，核心）
- **C1 路径硬编码（已根治）**：脚本绝不能写死某台机器的工作区 id。改为**运行时自动探测**：优先 `cwd/.workbuddy/memory`，否则扫描 `C:\Users\Administrator\WorkBuddy\*` 取最近修改的含 `.workbuddy/memory` 的目录。`LOG_PATH`/`DEBUG_DIR` 按实际工作区根（`ws_dir.parent.parent`）落地。这样 001/003 跑**同一份字节一致脚本**。
- **C2 error 误判 bug（已修）**：原 `'"error"' in 响应` 判错会把正文含英文 "error" 的文档（纷享 APL 文档常含）当 API 报错返回空、导致还原跳过。改为「仅响应以 `{` 开头且含 `"error"` 才判错」。
- **C3 合并膨胀（核心 bug，已修，见下）**：同日期逐行并集时，资料库往返造成换行/缩进/标题空格差异 → 把"同一行不同格式"当"对方独有行"又贴一遍 → 文件膨胀（旧逻辑 +63 行，新逻辑只 +2 行）。
- **C4 合并本质**：003≈001 备份 + 003 最近几天独有 → 大部分相同，只有少数独有行需合入。

### 自动化（D 类）
- **D1 nextRunAt 脏值**：`update` 改 FREQ/BYHOUR 不重算 `nextRunAt`（锚定午夜）。必须**删旧建新**让新 rrule 生效。
- **D2 BYHOUR rrule 存疑**：框架可能不支持 RRULE 的 `BYHOUR`（仍跑午夜）。跑后看 `memory_sync_log.txt` 时间戳确认；真不支持需 once/兜底。
- **D3 运行时 token**：自动化 prompt 必须内置"先 `connect_open_platform` 取 token 再跑脚本"。

### 协作模型（E 类）
- **E1 单向→双向演进**：任一侧拉完不要反向无脑推，否则用旧版覆盖全集（竞态）。脚本设计为"推自己快照 + 拉对方最新批次做并集"，逻辑安全。
- **E2 多端同步不同步脚本文件**：WorkBuddy 多端同步只同步任务/对话/产物，**不**同步脚本文件。必须手动拷 kit（U盘/网盘/微信文件）。

## 合并膨胀修复（方向 A：格式感知去重 + 膨胀保护网）
不需要统一两台机器各自的记忆**格式**（那是高风险的 B 路径）。只修合并层：
- `_norm_key(line)`：归一化判断键——折叠所有空白、标题 `##` 后空格统一、无序符号统一为 `-`。用归一化键判重，"同一内容不同格式"不再重复贴。
- `union_daily` / `union_global` 改用归一化键判重，保留本机原文、只合入对方真正独有内容。
- `_safe_write(path, local, merged, label)` 膨胀保护网：任一次合并若把文件撑到本机 **1.5 倍以上**（且本机>20 行），**立即中止写入并告警**，绝不再静默写爆文件（两台都受保护）。

本地验证法（见 `test_union_fix.py`）：
- 拿真实每日文件，模拟资料库空白/缩进/标题空格往返（**只改缩进/空行/标题空格，不改行数**——块 XML 每段落块还原成一行，行数基本不变）；
- 旧逻辑误追加 ~63 行（膨胀根因），新逻辑只合入 003 真正独有 2 行（净增 3 行）；
- `_safe_write` 在 30→100 行场景正确中止。

## 部署流程（照做）
1. 把 kit（含 `memory_sync.py` + 两份配置说明 txt）拷到本机工作区根。
2. 建每日自动化：名称 `记忆自同步-<机器>`、频率每天（001 17:00 / 003 17:30 错开）、cwds=本机工作区根、状态先 **PAUSED**。
3. prompt：先 `connect_open_platform` 取 token → `python memory_sync.py --machine <机器> --token <token>` → 读 `memory_sync_log.txt` 末尾回报。
4. **双侧都用修复版脚本、确认都 PAUSED 后，再双双改回 ACTIVE**。
5. 每次跑完看 `memory_sync_log.txt` 有无红色报错；枢纽 `sync-*` 节点会累积，偶尔清理。

## 关键文件（本工作区）
- `memory_sync.py`（修复版，含 `_norm_key`/`_safe_write`/`_autodetect_ws_dir`）
- `memory_sync_kit_001/` 与 `memory_sync_kit_003/`（部署包，已同步修复版）
- `restore_001_from_hub.py`（从指定批次枢纽节点还原本机记忆，止损用）
- `test_union_fix.py`（合并修复本地验证）
- `给003_同步问题通报与待确认事项.txt`（转发 003 的通报模板）

## Skill 目录 Git 中转同步（扩展 · 整目录镜像）

### 为什么不复用记忆枢纽
记忆同步走「资料库 markdown 文档枢纽」：拆片段→文档节点→行并集。该通道**不适用于 skill**：
- 枢纽是文档型，单节点 >~160KB 触发网关 524 超时（B2 已验证）；
- skill 含超大目录：`fxiaoke-apl-testground` 7.5MB、`talking-video-auto-edit` 474KB、`wps-office-automation-skill` 170KB；
- skill 是「SKILL.md+脚本+资产」多文件目录，塞进单个文档节点会破坏结构。
→ skill 改用 **Git 中转**：整目录镜像、大文件友好、冲突由 git 合并。

### 架构
1. 把用户级 `~/.workbuddy/skills/` 初始化为 git 仓库（本机 `git init` + `.gitignore`）。
2. 推送远端：GitHub / 工蜂 / 内部 git 私有仓库（不托管凭证）。
3. 两台机器：001/003 各自 `git pull` 拿对方最新 → `git push` 推自己改动；冲突走 `git merge`。
4. 调度：复用自动化框架，与记忆同步错开时段（如记忆 17:00/17:30，skill 17:10/17:40）。

### 超大项豁免（.gitignore 黑名单 · 本机实测体积）
以下直接排除（手动/网盘同步，不进 git），其余 skill（均 <200KB）正常版本化：
- `fxiaoke-apl-testground/`（7.5MB）
- `talking-video-auto-edit/`（474KB）
- `wps-office-automation-skill/`（170KB）

### 冲突策略
- 两台各自改了同一 skill：git 天然标记冲突，脚本检测到 `git status` 含 `both modified` 即**中止自动 push 并告警**，由人工 `git mergetool` 解决，绝不无脑覆盖（对应记忆同步的 E1 竞态教训）。
- 仅一侧改动：自动 fast-forward，无冲突。

### 关键文件（新增）
- `skill_sync.py`：封装 `git add -A` / `commit` / `push` / `pull` + 超大项豁免提示 + 冲突检测。
- `skills/.gitignore`：排除超大项与元数据（`*.json` 迁移文件等）。
- `skill_sync_kit/`：部署包。

### 部署步骤
1. 本机 `git init` skills 目录 → 写 `.gitignore` → 初始 `commit`。
2. 配远端：`git remote add origin <私有仓库 URL>`（用户提供）。
3. 首次 `git push -u origin main`。
4. 另一台机器在 `~/.workbuddy/skills/` 内 `git clone` 或 `git pull` 对齐（注意保留各自已装内置 skill 不冲突）。
5. 两台建自动化（错开时段），prompt：`python skill_sync.py --machine <机器> --pull && python skill_sync.py --machine <机器> --push`。
