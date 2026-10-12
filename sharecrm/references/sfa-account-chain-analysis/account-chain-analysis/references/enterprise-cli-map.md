# Enterprise CLI Map

本文件定义产业链分析 Skill 可调用的企业情报 CLI。目标是用批量企业信息识别目标客户在集团、资本、区域、业务、产品、竞品和生态关系中的位置，并用公开项目、新闻和公告补证上下游关系。

## 1. 总原则

- 用户输入为简称、品牌名、产品名、股票简称或 CRM 页面名时，先用 `sharecrm intelligence company search` 做一次结构化候选召回，再决定是否进入批量取数；不要先进入 web search。
- 优先使用 `sharecrm intelligence company conc` 批量获取主体、业务、股东、投资、分支、融资、竞品和证书信息。
- `conc` 的 `actionTypes` 必须按产业链判断目标传入白名单，不得一次性传入全部支持类型。
- 招投标、新闻、上市公告不是 `company conc` 覆盖范围，继续使用 market/listed CLI。
- 股东、分支、对外投资只默认写入集团/资本/组织关系；没有供货、采购、渠道或项目证据时，不写成上下游关系。
- 分页类或长列表结果默认只消费首批关键记录；首批不足时按关系类型定向追加，不机械全量翻页。

## 2. 允许调用命令

| 数据域 | 调用场景 | CLI | 必填入参 | 推荐 actionTypes / 参数 | 关键返回内容 | 写入位置 |
|:---|:---|:---|:---|:---|:---|:---|
| 主体候选召回 | 用户输入为简称、品牌名、产品名、股票简称或非完整工商名称时，先召回候选企业 | `sharecrm intelligence company search` | `KeyWord` | 只调用一次；候选不足或冲突时再要求用户确认 | `companyEsObjects` 候选列表，需解析 JSON 字符串；候选含 `Name`、`CreditCode`、`Status`、`OperName`、`No`、`KeyNo`、`updated` | `meta.targetCompany`、`chainContext.chainStructure.basis`、`gaps` |
| 企业链路批量信息 | 锚定主体、经营范围、产品业务、竞品、股东、投资、分支、融资和资质 | `sharecrm intelligence company conc` | `companyName`, `actionTypes` | 默认 `["baseinfo","qimingpianproductinfo","tbprojectjingpininfo","partnerinfo","investmentinfo","branchinfo","financinginfo","tbcertificateintegrateinfo"]` | 工商主体、业务产品、竞品、股东、对外投资、分支、融资、资质证书 | `meta.targetCompany`、`chainContext.chainPosition`、`chainContext.groupCapitalRelations`、`chainContext.ecosystem`、`chainContext.businessImplications` |
| 经营覆盖补充 | 需要判断区域覆盖、人员扩张、线上经营或土地/产能线索时按需调用 | `sharecrm intelligence company conc` | `companyName`, `actionTypes` | 按需 `["companyemploymentinfo","annualreportwebsiteinfo","landresultannouncementinfo","landtransferinfo"]` | 招聘、年报网站、购地、土地转让 | `chainContext.businessImplications`、`chainContext.keyDependencies`、`evidence` |
| 技术与标准补充 | 技术或制造类客户需要判断产业链技术壁垒时按需调用 | `sharecrm intelligence ip conc` | `companyName`, `actionTypes` | 按需 `["patentinfoinfo","standardinformationinfo"]` | 专利、参与起草标准 | `chainContext.keyDependencies`、`chainContext.valueRole`、`evidence` |
| 招投标主表 | 下游客户或项目关系补证，只作为项目型关系 | `sharecrm intelligence market bidding-pinganzhengxin` | `companyName`, `actionType=companybidmaininfo`, `pageSize` | 近 12-24 个月，优先金额较大或主营业务相关 | 招投标公告、项目、时间 | `chainContext.downstream`、`evidence` |
| 招投标相关方 | 需要区分公告相关方时按需使用 | `sharecrm intelligence market bidding-pinganzhengxin` | `companyName`, `actionType=companybidentityinfo`, `pageSize` | 与主表公告关联时优先 | 招投标相关方 | `chainContext.downstream`、`gaps` |
| 新闻动态 | 生态合作、上下游合作和平台关系补证 | `sharecrm intelligence market get-news` | `companyName` | 近 6-12 个月，优先权威来源 | 标题、来源、链接、发布时间 | `chainContext.ecosystem`、`evidence` |
| 上市公告 | 上市主体重大合同、供应链、客户或生态关系补证 | `sharecrm intelligence listed action-listed-company-announcement` | `companyName` | 上市主体适用 | 公告标题、公告类型、公告时间、原文链接 | `chainContext.downstream`、`chainContext.ecosystem`、`evidence` |

## 3. 推荐调用形态

主体候选召回：

```bash
sharecrm intelligence company search --data '{"KeyWord":"<用户输入的简称/品牌名/产品名>"}'
```

候选确认后再调用批量企业信息：

```bash
sharecrm intelligence company conc --data '{"companyName":"<工商全称>","actionTypes":["baseinfo","qimingpianproductinfo","tbprojectjingpininfo","partnerinfo","investmentinfo","branchinfo","financinginfo","tbcertificateintegrateinfo"],"pageNum":1,"pageSize":20}'
```

技术壁垒补充：

```bash
sharecrm intelligence ip conc --data '{"companyName":"<工商全称>","actionTypes":["patentinfoinfo","standardinformationinfo"],"pageNum":1,"pageSize":20}'
```

## 4. 批量返回消费规则

- `company search` 的 `companyEsObjects` 返回值是 JSON 字符串，必须先解析成候选数组再使用。
- 高置信候选可自动选中：第一候选为存续企业、非分支/个体/明显噪音，且名称、行业、城市、官网、股票代码或用户上下文无冲突。
- 中置信候选可先选中并在内部记录选择理由；如果后续 `baseinfo` 与候选冲突，应回到候选确认。
- 低置信候选必须让用户确认：多家存续主体都像目标、产品名对应多个企业、候选存在集团/子公司/分公司混杂，或辅助锚点冲突。
- `company search` 无候选或候选无法解释用户输入时，才使用 web search / 官网 / 新闻等公开来源补查主体；不得反复用多个企业 CLI 试错。
- 批量 CLI 返回后，按每个 `actionType` 对应的数据块分别消费；字段结构以实际返回为准。
- `baseinfo` 只用于主体锚定和经营范围解释；股东、投资、分支默认是组织/资本关系，不等同于供应链关系。
- 产品、竞品、融资、资质和技术资产可解释客户产业链角色，但必须结合招投标、新闻、公告、官网或年报等证据才能写成明确上下游关系。
- 招投标反推关系只能作为项目型客户/供应商线索，不自动写成长期稳定客户。
- 当 `total` 或 `isLastPage` 显示未覆盖全量时，写入 `meta.retrievalCoverage`。

## 5. 禁止默认调用

- 报告类、销售助手类、自动分析类命令。
- 名称包含 `旧` / `（旧）` / `(旧)` 的命令。
- 未列入本文件的内部分析、搜索、推荐、补全类命令。
- 任何写操作、审批、分配、转移等管理动作。

## 6. 降级规则

| 情况 | 处理 |
|:---|:---|
| `company conc` 不可用或报错 | 使用当前可用单点 CLI 按同一数据目标最小化补查，并记录降级 |
| 招投标为空 | 不断言没有客户或供应商，只说明本次未获得公开项目证据 |
| 投资/分支/股东信息过多 | 优先当前有效、持股高、主营相关、区域重要对象 |
| 上下游证据不足 | 输出为待核实线索，不写成确定关系 |
| 主体命中不确定 | 先要求用户确认主体 |
