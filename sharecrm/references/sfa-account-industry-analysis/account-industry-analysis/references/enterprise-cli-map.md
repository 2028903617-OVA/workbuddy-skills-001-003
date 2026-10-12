# Enterprise CLI Map

本文件定义行业分析 Skill 可调用的企业情报 CLI。目标是用少量批量 CLI 获取与“客户所处行业、行业位置、业务线、竞品和近期变化”相关的事实，不展开无关企业全量资料。

## 1. 总原则

- 用户输入为简称、品牌名、产品名、股票简称或 CRM 页面名时，先用 `sharecrm intelligence company search` 做一次结构化候选召回，再决定是否进入批量取数；不要先进入 web search。
- 优先使用 `sharecrm intelligence company conc` 批量查询企业基础、行业、业务、竞品、融资和招聘等信息。
- `conc` 的 `actionTypes` 必须按业务目标传入白名单，不得为了“数据更全”一次性传入全部支持类型。
- `pageNum=1` 只是执行参数，不代表业务覆盖范围；首批不足时按行业判断需要追加定向查询，不机械翻页。
- 新闻、上市公告和上市公司简介不属于 `company conc`，继续使用 market/listed CLI。
- 实际运行以当前 `sharecrm intelligence <group> --help` 输出和返回结构为准；字段缺失时不得编造。

## 2. 允许调用命令

| 数据域 | 调用场景 | CLI | 必填入参 | 推荐 actionTypes / 参数 | 关键返回内容 | 写入位置 |
|:---|:---|:---|:---|:---|:---|:---|
| 主体候选召回 | 用户输入为简称、品牌名、产品名、股票简称或非完整工商名称时，先召回候选企业 | `sharecrm intelligence company search` | `KeyWord` | 只调用一次；候选不足或冲突时再要求用户确认 | `companyEsObjects` 候选列表，需解析 JSON 字符串；候选含 `Name`、`CreditCode`、`Status`、`OperName`、`No`、`KeyNo`、`updated` | `meta.targetCompany`、`industryContext.customerPosition.basis`、`gaps` |
| 企业行业与业务批量信息 | 锚定客户主体、行业分类、经营范围、产品业务、竞品、融资与招聘信号 | `sharecrm intelligence company conc` | `companyName`, `actionTypes` | 默认 `["baseinfo","industrymodelinfo","qimingpianproductinfo","financinginfo","tbprojectjingpininfo","companyemploymentinfo"]` | 企业名称、统一社会信用代码、登记状态、行业层级、经营范围、产品业务、融资、竞品、招聘方向 | `meta.targetCompany`、`industryContext.customerPosition`、`industryContext.majorPlayers`、`industryContext.businessImplications` |
| 能力与资质补充 | 当客户行业位置需要能力、认证或技术背书时按需补充 | `sharecrm intelligence company conc` | `companyName`, `actionTypes` | 按需 `["honorinfo","tbcertificateintegrateinfo","qimingpianteammemberinfo"]` | 荣誉标签、资质证书、核心团队 | `industryContext.customerPosition`、`industryContext.businessImplications`、`evidence` |
| 技术资产补充 | 当客户为技术、制造、软件、医药、装备等研发驱动企业，且需要判断技术支撑时按需调用 | `sharecrm intelligence ip conc` | `companyName`, `actionTypes` | 按需 `["patentinfoinfo","copyrightsoftwareinfo","standardinformationinfo"]` | 专利、软件著作权、参与起草标准 | `industryContext.customerPosition`、`industryContext.businessImplications`、`evidence` |
| 新闻动态 | 获取近 6-12 个月企业和行业相关动态 | `sharecrm intelligence market get-news` | `companyName` | 近 6-12 个月，优先权威来源 | 标题、来源、链接、发布时间 | `industryContext.trendAndEvents.events`、`evidence` |
| 上市公告 | 上市主体需要从公告解释行业变化和经营重点 | `sharecrm intelligence listed action-listed-company-announcement` | `companyName` | 上市主体适用 | 公告标题、公告类型、公告时间、原文链接 | `industryContext.trendAndEvents.events`、`evidence` |
| 上市公司简介 | 上市主体行业地位和主营口径补充 | `sharecrm intelligence listed action-listed-company-introduction` | `companyName` | 上市主体适用 | 股票代码、交易所、公司简介、员工数量、董事长等 | `industryContext.customerPosition`、`evidence` |

## 3. 推荐调用形态

主体候选召回：

```bash
sharecrm intelligence company search --data '{"KeyWord":"<用户输入的简称/品牌名/产品名>"}'
```

候选确认后再调用批量企业信息：

```bash
sharecrm intelligence company conc --data '{"companyName":"<工商全称>","actionTypes":["baseinfo","industrymodelinfo","qimingpianproductinfo","financinginfo","tbprojectjingpininfo","companyemploymentinfo"],"pageNum":1,"pageSize":20}'
```

如需补充技术资产：

```bash
sharecrm intelligence ip conc --data '{"companyName":"<工商全称>","actionTypes":["patentinfoinfo","copyrightsoftwareinfo","standardinformationinfo"],"pageNum":1,"pageSize":20}'
```

## 4. 批量返回消费规则

- `company search` 的 `companyEsObjects` 返回值是 JSON 字符串，必须先解析成候选数组再使用。
- 高置信候选可自动选中：第一候选为存续企业、非分支/个体/明显噪音，且名称、行业、城市、官网、股票代码或用户上下文无冲突。
- 中置信候选可先选中并在内部记录选择理由；如果后续 `baseinfo` 与候选冲突，应回到候选确认。
- 低置信候选必须让用户确认：多家存续主体都像目标、产品名对应多个企业、候选存在集团/子公司/分公司混杂，或辅助锚点冲突。
- `company search` 无候选或候选无法解释用户输入时，才使用 web search / 官网 / 新闻等公开来源补查主体；不得反复用多个企业 CLI 试错。
- 批量 CLI 返回后，按每个 `actionType` 对应的数据块分别消费；常见结构可能是 `results.<actionType>`、以 actionType 命名的字段或包含 actionType 标识的列表，必须以实际返回为准。
- `baseinfo` 用于主体锚定；主体名称、统一社会信用代码或注册号与目标不一致时，整批结果不得直接写为目标客户事实。
- 产品、融资、竞品、招聘、资质和知识产权只作为客户行业位置、业务重点和能力证据，不自动推导销售机会。
- 对长列表只消费与主营业务、近年变化、行业位置有关的关键记录；如返回总量大于本次记录量，应写入 `meta.retrievalCoverage`。

## 5. 禁止默认调用

- 报告类、销售助手类、自动分析汇总类命令。
- 名称包含 `旧` / `（旧）` / `(旧)` 的操作。
- 未列入本文件的内部搜索类、分析类或补全类命令。
- 任何写操作、审批、分配、转移等管理动作。

## 6. 降级规则

| 情况 | 处理 |
|:---|:---|
| `company conc` 不可用或报错 | 使用当前 `sharecrm intelligence company --help` 中可用的单点 CLI 按同一 actionType 目标最小化补查，并记录降级 |
| 某个 actionType 返回为空 | 不断言该信息不存在；仅说明该数据域本次未返回有效记录 |
| 主体命中不确定 | 先要求用户确认主体，不生成完整行业判断 |
| 企业情报不足以判断行业 | 使用 CRM 行业字段、官网、年报、招股书、公告、权威行业资料和新闻补证 |
| 外部来源与 CLI 冲突 | 优先使用更权威、更近且能解释口径的来源；无法判断时降低结论强度 |
