# 环境安装与快照刷新指引

## 依赖清单

| 依赖 id | 类型 | 必需 | 官方主页 | 官方文档 |
|---|---|---|---|---|
| python-venv | runtime | 是 | https://www.python.org | https://docs.python.org/3/ |
| openpyxl | local-tool | 是 | https://openpyxl.readthedocs.io | https://openpyxl.readthedocs.io/en/stable/ |
| fs-server-mcp | mcp | 否（可选增强） | https://www.fxiaoke.com | https://www.fxiaoke.com |

## python-venv 配置

- 优先使用 WorkBuddy 内置 venv Python：`~/.workbuddy/binaries/python/envs/default` 下的解释器（Windows 为其 `Scripts\python.exe`）
- 若缺失：用内置 Python 执行 `python -m venv` 创建，再安装 openpyxl
- 验证：运行 `check_environment.py`，python 检查项为 ok
- 无凭据，本地解释器

## openpyxl 配置

- 安装：`<venv Python> -m pip install openpyxl`
- 验证：`check_environment.py` 中 openpyxl 检查项为 ok
- 无凭据，纯本地库

## fs-server-mcp 配置（可选增强，当前不可用）

- 入口：WorkBuddy 连接器管理页 → fs-server → 启用并信任
- 当前环境该 MCP 已知长期失效（HTTP 400），skill 默认使用本地快照，不依赖它
- 授权与凭据由 WorkBuddy 宿主管理，skill 不接触任何凭据
- 验证：MCP 工具 get-current-user 可正常返回用户身份

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

## fs-server MCP（可选，当前不可用）

- 状态：连接失效（HTTP 400），已知的长期问题。
- 影响：无法实时读取纷享销客产品与价目表明细，用本地快照替代。
- 恢复后：可改为实时查询，skill 逻辑不变，仅数据源切换。

## 常见问题

| 现象 | 处理 |
|---|---|
| 找不到快照 | 手动导出一份放到 Downloads，或在对话中直接给文件路径 |
| 空壳导出（只有表头） | 重新导出，勾选「含数据」或调大批量 |
| 产品匹配不到 | 先确认金蝶是否已建该产品并同步；未同步的等同步后重跑 |
