# 环境安装与数据源指引

> ★ **v1.9.0 起能力 1（价目表明细维护）不再需要快照**：改为经连接器/CLI **实时查**系统，确认后直写。
> 快照只服务**能力 2 / 3**（我方物料匹配、物料名生成）。

## 依赖清单

| 依赖 id | 类型 | 必需 | 用途 | 官方主页 |
|---|---|---|---|---|
| python-venv | runtime | 是 | 跑全部脚本 | https://www.python.org |
| openpyxl | local-tool | 是 | 读源表 / 生成文件 | https://openpyxl.readthedocs.io |
| sharecrm CLI | local-tool | **能力 1 必需** | 实时查产品/明细（底层 = 连接器服务） | https://www.fxiaoke.com |
| openapi_client.py | local-tool | **能力 1 写操作必需** | 直写价目表明细 | 见 `openapi-direct-write.md` |
| fs-server-mcp | mcp | 否（已失效） | 旧渠道，勿用 | — |

## python-venv 配置

- 优先使用 WorkBuddy 内置 venv Python：`~/.workbuddy/binaries/python/envs/default` 下的解释器（Windows 为其 `Scripts\python.exe`）
- 若缺失：用内置 Python 执行 `python -m venv` 创建，再安装 openpyxl
- 验证：运行 `check_environment.py`，python 检查项为 ok
- 无凭据，本地解释器

## openpyxl 配置

- 安装：`<venv Python> -m pip install openpyxl`
- 验证：`check_environment.py` 中 openpyxl 检查项为 ok
- 无凭据，纯本地库

## 纷享销客连接器配置（可选增强）

- 入口：WorkBuddy 连接器管理页 → 纷享销客连接器 → 启用并信任
- 授权与凭据由 WorkBuddy 宿主管理，skill 不接触任何凭据
- 验证：调用 `get-current-user`，能返回 `ea / tenantId / employeeId` 即为可用
- 用途：给「金蝶未同步」做兜底复核（按名称查产品记录、看相似度）

> ⚠️ **别把「某条渠道不可用」记成「连接器不可用」**（2026-09-28 踩过）：
> 失效的是 **fs-server** 那条渠道（代理网关 / SSE 直连 / API 写三路都返回 HTTP 400），
> 而 WorkBuddy 里挂的另一条纷享销客连接器是通的（实测 `get-current-user` 正常返回）。
> **判定连接器状态前先调一次 `get-current-user`**，不要凭记忆下结论。

## 两类快照（数据源文件）

默认扫描目录由 `--downloads` 参数指定（默认为用户常用的 Downloads 目录）。

### 产品主数据快照
- 来源：纷享销客 → 产品对象 → 导出（全量、含数据）
- 命名：`产品对象导出结果_*.xlsx`
- 用途：把源表型号匹配到系统产品名称
- 关键列：产品名称（必填）/ 物料名称 / 型号规格 / 物料编号 / 产品大类 / 产品品相

### 价目表明细快照
- 来源：纷享销客 → 价目表明细对象 → 导出（按品牌价目表过滤更佳）
- 命名：`价目表明细对象导出结果_*.xlsx`
- 用途：判断某产品在某价目表下是否已有明细（决定走新建还是更新）
- 关键列：唯一性ID（必填）/ 价目表明细编号 / 产品（必填）/ 价目表（必填）/ 价目表_唯一性ID（必填）

### 快照自动发现规则
脚本按文件名日期降序遍历 Downloads 下对应前缀的文件，跳过表头行以下无数据的空壳导出（首 sheet 仅 1 行表头），取第一个有数据的文件。发现结果与快照日期会写进核对清单顶部。

### 刷新时机
- 每次正式生成导入文件前，建议重新导出一次两类快照（金蝶 → 纷享同步有延迟，快照越新匹配越准）。
- 快照日期距今超过 7 天时，脚本在核对清单标注「快照较旧，建议重新导出」。

## 能力 1 的运行依赖（实时查 + 直写）

| 组件 | 位置 | 检查 |
|---|---|---|
| node.exe | `~/.workbuddy/binaries/node/versions/22.22.2-6/node.exe` | 存在即可 |
| sharecrm CLI | `~/.workbuddy/binaries/node/workspace/node_modules/@share-crm/sharecrm-cli/dist/index.js` | 跑一次 `data record query-by-fields` 返回 JSON |
| 凭证文件 | `C:\Users\Administrator\.workbuddy\fxiaoke-app-003.json` | `openapi_client.py token --cred-file <该文件>` → `errorCode=0` |
| 出口 IP 白名单 | 自建应用后台 | 变了会报 `20014`，需重配 |

```bash
# 一次跑通能力 1 的阶段 1（只读）
python scripts/query_pricebook.py --source <源表.xlsx> --org <组织>
```

连接器 / CLI 不可用 → **停止**（实时查不了的不能靠猜），不要退回去读快照。

## 能力 2 / 3 的数据源优先级：本地快照 → 连接器兜底

> **仅适用于能力 2 / 3。** 能力 1 已改为实时查（见上节）。

**先用本地快照；只有快照没命中的行才走连接器**（用户 2026-09-28 明确）。不要一上来就查连接器。

### 第 1 步：本地快照（主路径）

- `check_environment.py` 确认两类快照存在且非过期 → 跑脚本匹配 → 命中的行直接出结果。
- 快照滞后 1–3 天是常态，但这**不构成每次都去查连接器的理由**。

### 第 2 步：连接器兜底（仅对快照未命中的行）

1. 先调 `get-current-user` 确认连接器可用；不可用才退回纯快照模式，并在核对清单标注「未经连接器复核」。
2. 用 `按名称查询记录`（`apiNames: ["ProductObj"]`）查源表型号，看返回的候选与相似度。
3. **只有相似度 ≥0.98 且型号主体一致才算命中**；型号主体只差前后缀时取 id 最新的。
4. 连接器也确认不存在 → 才真正判「金蝶未同步」。

> 实测教训（2026-09-28 天猫库存物料价目表）：抽查 2 条待同步，
> `美的冷柜BD/BC-200KEM(E)` 对上系统 `BD/BC-200KGEM(E)`（**差一个字母 G**，相似度 0.9686）、
> `奥普热能环浴霸Q360X` 对上系统 `Q360X-PRO`（0.9671）。都够不上 0.98 → **是真没有这个产品，
> 不是快照滞后**。不要因为"连接器通了"就把够不上线的候选硬认成命中。

## 常见问题

| 现象 | 处理 |
|---|---|
| 找不到快照 | 手动导出一份放到 Downloads，或在对话中直接给文件路径 |
| 空壳导出（只有表头） | 重新导出，勾选「含数据」或调大批量 |
| 产品匹配不到 | 先确认金蝶是否已建该产品并同步；未同步的等同步后重跑 |
