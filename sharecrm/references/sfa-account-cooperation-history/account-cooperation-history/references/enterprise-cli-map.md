# Enterprise CLI Map

本文件定义合作历史分析 Skill 可调用的企业情报 CLI。目标是用少量批量企业信息识别主体、业务、融资、竞品、股东和投资背景，再用招投标、新闻、上市公告和 CRM 记录判断真实合作历史。

## 1. 总原则

- 合作历史的核心证据来自 CRM 内部记录、招投标、公开新闻、公告和可追溯外部来源；结构化招投标 CLI 优先于泛化 web search。
- 用户输入为简称、品牌名、产品名、股票简称或 CRM 页面名时，先用 `sharecrm intelligence company search` 做一次结构化候选召回，再决定是否进入批量取数；不要先进入 web search。
- `sharecrm intelligence company conc` 只用于主体锚定、业务/竞品/融资补证，以及识别集团或关联方，不能单独证明合作关系。
- `conc` 的 `actionTypes` 必须按合作判断目标传入白名单，不得一次性传入全部支持类型。
- 招投标是合作历史证据域，不独立输出投标策略。
- 分页类或长列表结果默认只消费首批关键记录；不足时按合作对象、项目、时间窗定向追加。`total` 只表示接口记录总量，不等于有效合作数量；空字段 item、角色不清或状态不可用的记录不进入正式合作结论。

## 2. 允许调用命令

| 数据域 | 调用场景 | CLI | 必填入参 | 推荐 actionTypes / 参数 | 关键返回内容 | 写入位置 |
|:---|:---|:---|:---|:---|:---|:---|
| 主体候选召回 | 用户输入为简称、品牌名、产品名、股票简称或非完整工商名称时，先召回候选企业 | `sharecrm intelligence company search` | `KeyWord` | 只调用一次；候选不足或冲突时再要求用户确认 | `companyEsObjects` 候选列表，需解析 JSON 字符串；候选含 `Name`、`CreditCode`、`Status`、`OperName`、`No`、`KeyNo`、`updated` | `meta.targetCompany`、`cooperationContext.gaps` |
| 合作背景批量信息 | 锚定客户主体，补充业务、竞品、融资、投资和股东背景 | `sharecrm intelligence company conc` | `companyName`, `actionTypes` | 默认 `["baseinfo","qimingpianproductinfo","tbprojectjingpininfo","financinginfo","investmentinfo","partnerinfo"]` | 工商主体、产品业务、竞品、融资、对外投资、股东 | `meta.targetCompany`、`cooperationContext.supplierAndCompetitorSignals`、`cooperationHistory`、`gaps` |
| 区域与组织补充 | 需要判断区域交付、分支经营或集团关联合作对象时按需调用 | `sharecrm intelligence company conc` | `companyName`, `actionTypes` | 按需 `["branchinfo"]` | 分支机构名称、状态、区域 | `cooperationHistory.partnerType=related_company`、`gaps` |
| 招投标主表 | 发现采购、中标、项目参与和供应商关系 | `sharecrm intelligence market bidding-pinganzhengxin` | `companyName`, `actionType=companybidmaininfo`, `pageSize` | 近 12-24 个月，优先金额较大或主营业务相关 | 招投标公告、项目、时间 | `cooperationHistory`、`evidence` |
| 招投标相关方 | 需要区分招投标相关方时按需使用 | `sharecrm intelligence market bidding-pinganzhengxin` | `companyName`, `actionType=companybidentityinfo`, `pageSize` | 与主表公告关联时优先 | 公告相关方 | `cooperationHistory`、`cooperationContext.supplierAndCompetitorSignals` |
| 新闻动态 | 获取战略合作、签约、项目进展、公开合作新闻 | `sharecrm intelligence market get-news` | `companyName` | 近 6-12 个月，优先权威来源 | 标题、来源、链接、发布时间 | `cooperationHistory`、`evidence` |
| 上市公告 | 上市主体重大合同、合作公告、采购或供应商披露 | `sharecrm intelligence listed action-listed-company-announcement` | `companyName` | 上市主体适用 | 公告标题、公告类型、公告时间、原文链接 | `cooperationHistory`、`evidence` |

## 3. 推荐调用形态

主体候选召回：

```bash
sharecrm intelligence company search --data '{"KeyWord":"<用户输入的简称/品牌名/产品名>"}'
```

候选确认后再调用批量企业信息：

```bash
sharecrm intelligence company conc --data '{"companyName":"<工商全称>","actionTypes":["baseinfo","qimingpianproductinfo","tbprojectjingpininfo","financinginfo","investmentinfo","partnerinfo"],"pageNum":1,"pageSize":20}'
```

## 4. 批量返回消费规则

- `company search` 的 `companyEsObjects` 返回值是 JSON 字符串，必须先解析成候选数组再使用。
- 高置信候选可自动选中：第一候选为存续企业、非分支/个体/明显噪音，且名称、行业、城市、官网、股票代码或用户上下文无冲突。
- 中置信候选可先选中并在内部记录选择理由；如果后续 `baseinfo` 与候选冲突，应回到候选确认。
- 低置信候选必须让用户确认：多家存续主体都像目标、产品名对应多个企业、候选存在集团/子公司/分公司混杂，或辅助锚点冲突。
- `company search` 无候选或候选无法解释用户输入时，才使用 web search / 官网 / 新闻等公开来源补查主体；不得反复用多个企业 CLI 试错。
- 批量 CLI 返回后，按每个 `actionType` 对应的数据块分别消费；字段结构以实际返回为准。
- `baseinfo` 只做主体锚定；`investmentinfo`、`partnerinfo`、`branchinfo` 只帮助识别关联方或集团背景，不能直接写成合作对象。
- `qimingpianproductinfo`、`tbprojectjingpininfo`、`financinginfo` 可解释合作背景、供应商/竞品信号或业务变化，但不能单独证明合作发生。
- 招投标、采购、中标和项目参与事件统一写入 `cooperationHistory[]`，并按 `bidding-merge-rules.md` 区分采购方、中标方、参与方。
- 合作历史优先跑 `market bidding-pinganzhengxin` 主表；需要解释相关方角色时再跑 `companybidentityinfo`。只有招投标、新闻和上市公告无法支撑关键合作事实时，才少量 web search / web fetch 补证。
- 公开合作事件与 CRM 内部记录冲突时，分开表达来源和时间口径，不强行合并。
- 当 `total` 或 `isLastPage` 显示未覆盖全量时，写入 `meta.retrievalCoverage`。

## 5. 禁止默认调用

- 报告类、销售助手类、自动分析类命令。
- 名称包含 `旧` / `（旧）` / `(旧)` 的操作。
- 与合作历史无关的风险、知识产权、税务、年报全量类命令，除非用户明确要求或主报告编排要求。
- 任何写操作、审批、分配、转移等管理动作。

## 6. 降级规则

| 情况 | 处理 |
|:---|:---|
| `company conc` 不可用或报错 | 使用当前可用单点 CLI 按同一数据目标最小化补查，并记录降级 |
| 招投标或新闻为空 | 不断言没有合作，只说明本次未获得公开合作证据 |
| 只获得关联方关系 | 写为集团/关联方背景，不写为合作历史 |
| 供应商、竞品或替代服务商证据不足 | 输出为待核实线索，不写成正式结论 |
| 主体命中不确定 | 先要求用户确认主体 |
