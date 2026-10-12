# Enterprise CLI Map

本文件定义客户尽调报告 Skill 可调用的企业情报 CLI。目标是用批量 CLI 减少串行调用和文档上下文，同时保持主体消歧、重要性优先、证据可追溯和按需深挖。本变体额外允许 `sharecrm intelligence market search-mentions` 补充公开动态和舆情提及。

## 1. Core Rules

1. 默认调用范围只限本文件列出的命令；未列入的内部企业情报命令不得自行调用或猜测调用。
2. 企业主体必须先归一化和消歧。用户输入为简称、品牌名、产品名、股票简称或 CRM 页面名时，先用 `sharecrm intelligence company search` 做一次结构化候选召回，再进入批量取数；不要先进入 web search。
3. `sharecrm intelligence company conc`、`risk conc`、`ip conc` 的 `actionTypes` 必须按本文件白名单传入，不得一次性传入全部支持类型。
4. 批量 CLI 是并行取数入口，不是全量展开许可。默认只消费首批关键记录；但分支机构、子公司、项目等用于区域地图的组织分布数据，如果返回 `total <= 100` 或可通过分页在 100 条以内取全，应继续分页取全量明细再聚合，不得用首批样本替代全量区域分布。
5. `pageNum=1` 只是执行参数，不代表业务覆盖范围；当 `total` 或 `isLastPage` 显示未覆盖全量时，写入 `meta.retrievalCoverage`。
6. 风险/司法/处罚默认看近 24-36 个月加当前未结清记录，优先未结清、高金额、失信、被执行、破产、重大处罚。
7. 新闻/动态/公告默认看近 6-12 个月；`search-mentions` 固定按不超过 7 天窗口分段查询，调用前必须读取 `search-mentions-cli.md`。
8. 知识产权研发实力与知识产权出质分开判断：专利、软著、标准、商标、ICP备案用于技术资产和产品支撑；知识产权出质用于融资、担保或风险补充。
9. CLI 返回为空不等于公开世界不存在；公开来源仍无证据时，该类信息动态裁剪不输出。
10. 内部证据追溯可保留完整 CLI 路径；最终报告面向读者展示业务可读来源名称，不直接展示 CLI 代码。

## 2. CLI Map

### 企业基础、股权、组织与业务

| 数据域 | 调用场景 | CLI | 必填入参 | 推荐 actionTypes / 参数 | 关键输出字段 | 报告消费位置 |
|:---|:---|:---|:---|:---|:---|:---|
| 主体候选召回 | 用户输入为简称、品牌名、产品名、股票简称或非完整工商名称时，先召回候选企业 | `sharecrm intelligence company search` | `KeyWord` | 只调用一次；候选不足或冲突时再要求用户确认 | `companyEsObjects` 候选列表，需解析 JSON 字符串；候选含 `Name`、`CreditCode`、`Status`、`OperName`、`No`、`KeyNo`、`updated` | `meta.targetCompany.entityResolution`、客户主体与基础信息 |
| 企业尽调基础批量信息 | 获取主体、变更、曾用名、股东、投资、分支、人员、荣誉、资质、融资、产品、竞品、纳税和行政许可 | `sharecrm intelligence company conc` | `companyName`, `actionTypes` | 默认 `["baseinfo","companychangeinfo","companyhistorynameinfo","partnerinfo","investmentinfo","branchinfo","employeeinfo","honorinfo","tbcertificateintegrateinfo","financinginfo","qimingpianproductinfo","tbprojectjingpininfo","generaltaxpayerinfo","taxcreditinfo","companyallowinfo","companylicenseinfocreditchinainfo"]` | 工商主体、信用代码、状态、行业、经营范围、变更、股东、投资、分支、主要人员、荣誉资质、融资、业务产品、竞品、纳税资质/信用、行政许可 | 客户主体与基础信息 / 集团、股权与组织关系 / 主营业务与商业模式 / 经营动态与业务重点 / 风险与准入信息 |
| 年报与经营补充 | 需要判断资产、社保、网站、担保、年报投资或历史年度口径时按需调用 | `sharecrm intelligence company conc` | `companyName`, `actionTypes` | 按需 `["annualreportbaseinfo","annualreportassetinfo","annualreportsocialsecurityinfo","annualreportwebsiteinfo","annualreportguaranteeinfo","annualreportinvestinfo"]`，可加 `reportYear` | 年报基本、资产、社保、网站、对外担保、年报投资 | 客户主体与基础信息 / 经营动态与业务重点 / 风险与准入信息 |
| 扩展能力和资产补充 | 需要判断核心团队、债券、土地、产能或资质明细时按需调用 | `sharecrm intelligence company conc` | `companyName`, `actionTypes` | 按需 `["qimingpianteammemberinfo","bondbasicinfo","landresultannouncementinfo","landtransferinfo","tbcertificatedetailintegrateinfo"]` | 核心团队、债券、购地、土地转让、证书明细 | 主营业务与商业模式 / 经营动态与业务重点 / 风险与准入信息 |

### 研发与知识产权实力

| 数据域 | 调用场景 | CLI | 必填入参 | 推荐 actionTypes / 参数 | 关键输出字段 | 报告消费位置 |
|:---|:---|:---|:---|:---|:---|:---|
| 知识产权与研发实力 | 判断研发能力、技术资产、产品支撑和线上经营痕迹 | `sharecrm intelligence ip conc` | `companyName`, `actionTypes` | 默认 `["patentinfoinfo","copyrightsoftwareinfo","standardinformationinfo","trademarkinfo","tbicpbaseinfo"]` | 专利、软件著作权、参与起草标准、商标、ICP备案 | 主营业务与商业模式 / 研发与知识产权实力 / 经营动态与业务重点 / 证据来源 |
| 知识产权深挖 | 用户要求核心专利、技术壁垒、权利要求或指定专利号时按需调用 | `sharecrm intelligence ip conc` | `companyName`, `actionTypes` | 按需 `["patentannouncementinfo","patentaffairstatusinfo","patentclaiminstrinfo","copyrightworksinfo"]`，优先带专利号/关键词过滤 | 专利公告、专利事务、权利要求书与说明书、作品著作权 | 研发与知识产权实力 / 待核实事项 |

### 风险信息

| 数据域 | 调用场景 | CLI | 必填入参 | 推荐 actionTypes / 参数 | 关键输出字段 | 报告消费位置 |
|:---|:---|:---|:---|:---|:---|:---|
| 重大风险与合规批量信息 | 判断经营异常、处罚、严重违法、执行、失信、破产、税务、环保、质押和知识产权出质风险 | `sharecrm intelligence risk conc` | `companyName`, `actionTypes` | 默认 `["abnormalinfo","punishinfo","illegalinfo","companypunishmentinfocreditchinainfo","dishonestinfo","zhixinginfo","xianxiaoinfo","zhongbeninfo","bankruptcyinfo","taxpunishinfo","taxstatusinfo","environmentpunishinfo","intellectualinfo","pledgeinfo"]` | 经营异常、行政处罚、严重违法、信用中国处罚、失信/被执行/限高/终本、破产、重大税收违法、税务非正常、环保处罚、知识产权出质、股权出质 | 风险与准入信息 / 经营动态与业务重点 |
| 司法动态批量信息 | 判断近期涉诉、开庭、法院公告和立案趋势 | `sharecrm intelligence risk conc` | `companyName`, `actionTypes` | 默认 `["courtfiledcaseinfo","courtannouncement","courtnotice"]`，按需加 `filedYear`、`filedMonth`、`publishYear` | 法院立案、法院公告、开庭公告 | 风险与准入信息 |
| 裁判文书深挖 | 首批风险显示重大诉讼、用户要求诉讼详情，或需要判断历史裁判结果时调用 | `sharecrm intelligence risk conc` | `companyName`, `actionTypes` | 按需 `["lawsuitinfo"]`，优先用案号、案由、法院、年份或关键词过滤 | 裁判文书、裁判日期、案由、法院、文书类型 | 风险与准入信息 / 待核实事项 |
| 监管检查和司法协助补充 | 风控/签约场景需要更细监管、抽查、冻结、拍卖或动产抵押时按需调用 | `sharecrm intelligence risk conc` | `companyName`, `actionTypes` | 按需 `["companychattelinfo","companyjusticeinfo","companyjusticefreezeinfo","companyjusticekeepfreezeinfo","companyjusticeunfreezeinfo","judicialsaleinfo","companycheckinfo","companyrandomcheckinfo","productcheckinfo","certsupervisioncheckinfo"]` | 动产抵押、司法协助/冻结/解冻、司法拍卖、抽查检查、产品质检、认证监管检查 | 风险与准入信息 |

### 市场、动态和上市公司信息

| 数据域 | 调用场景 | CLI | 必填入参 | 推荐参数 | 关键输出字段 | 报告消费位置 |
|:---|:---|:---|:---|:---|:---|:---|
| 新闻动态 | 获取企业公开动态 | `sharecrm intelligence market get-news` | `companyName` | 近 6-12 个月，优先权威来源 | 标题、发布时间、来源、摘要、链接 | 经营动态与业务重点 |
| 公开动态/舆情提及 | 补充企业相关新闻、平媒、App、论坛、博客、微博、微信、视频、电视等公开提及 | `sharecrm intelligence market search-mentions` | `keyword` | 固定按不超过 7 天窗口分段查询；`keyword` 是普通搜索词 | 标题、正文/摘要、发布时间、来源、链接、互动量、情感、站点、用户、地域 | 经营动态与业务重点 / 风险与准入信息 / 与发问方业务相关的情报信号 |
| 招投标 | 获取采购、中标、项目参与和供应商关系 | `sharecrm intelligence market bidding-pinganzhengxin` | `companyName`, `actionType`, `pageSize` | `companybidmaininfo`；需要相关方时再查 `companybidentityinfo` | 招投标公告、项目、金额、时间、相关方 | 合作历史与供应商关系 / 经营动态与业务重点 |
| 上市公司简介 | 判断上市主体和公开资本市场身份 | `sharecrm intelligence listed action-listed-company-introduction` | `companyName` | 上市主体适用 | 股票代码、交易所、主营业务、上市日期 | 客户主体与基础信息 |
| 上市公司高管 | 获取上市公司公开高管信息 | `sharecrm intelligence listed action-listed-company-executive-info` | `companyName` | 上市主体适用 | 姓名、职位、任职日期、简历摘要 | 客户主体与基础信息 / 组织关系 |
| 上市公司公告 | 获取上市公司公告动态 | `sharecrm intelligence listed action-listed-company-announcement` | `companyName` | 上市主体适用 | 公告标题、公告日期、公告类型、链接 | 经营动态与业务重点 |
| 利润表 | 获取上市公司利润表 | `sharecrm intelligence listed action-company-profit-statement` | `companyName` | 默认不传 `reportYear`，返回后按期间筛选 | 营业收入、营业成本、利润、净利润、期间、审计状态 | 上市主体公开财务与经营摘要 |
| 资产负债表 | 获取上市公司资产负债表 | `sharecrm intelligence listed action-company-balance-sheet` | `companyName` | 默认不传 `reportYear`，返回后按期间筛选 | 资产、负债、所有者权益、期间、审计状态 | 上市主体公开财务与经营摘要 |
| 现金流量表 | 获取上市公司现金流量表 | `sharecrm intelligence listed action-cash-flow-statement` | `companyName` | 默认不传 `reportYear`，返回后按期间筛选 | 经营、投资、筹资现金流、期间、审计状态 | 上市主体公开财务与经营摘要 |

### 谨慎按需使用

| 场景 | CLI | 使用规则 |
|:---|:---|:---|
| 用户明确要求上市公司财务指标，且原始三表不足 | `sharecrm intelligence listed action-stock-company-financial-analysis` | 该命令带分析属性，不进入默认事实采集链路；使用时需保留 CLI 来源并避免照搬结论 |

## 3. 推荐调用形态

主体候选召回：

```bash
sharecrm intelligence company search --data '{"KeyWord":"<用户输入的简称/品牌名/产品名>"}'
```

候选确认后再调用批量企业信息：

```bash
sharecrm intelligence company conc --data '{"companyName":"<工商全称>","actionTypes":["baseinfo","companychangeinfo","companyhistorynameinfo","partnerinfo","investmentinfo","branchinfo","employeeinfo","honorinfo","tbcertificateintegrateinfo","financinginfo","qimingpianproductinfo","tbprojectjingpininfo","generaltaxpayerinfo","taxcreditinfo","companyallowinfo","companylicenseinfocreditchinainfo"],"pageNum":1,"pageSize":20}'
```

```bash
sharecrm intelligence ip conc --data '{"companyName":"<工商全称>","actionTypes":["patentinfoinfo","copyrightsoftwareinfo","standardinformationinfo","trademarkinfo","tbicpbaseinfo"],"pageNum":1,"pageSize":20}'
```

```bash
sharecrm intelligence risk conc --data '{"companyName":"<工商全称>","actionTypes":["abnormalinfo","punishinfo","illegalinfo","companypunishmentinfocreditchinainfo","dishonestinfo","zhixinginfo","xianxiaoinfo","zhongbeninfo","bankruptcyinfo","taxpunishinfo","taxstatusinfo","environmentpunishinfo","intellectualinfo","pledgeinfo"],"pageNum":1,"pageSize":20}'
```

```bash
sharecrm intelligence risk conc --data '{"companyName":"<工商全称>","actionTypes":["courtfiledcaseinfo","courtannouncement","courtnotice"],"pageNum":1,"pageSize":20}'
```

## 4. 批量返回消费规则

- `company search` 的 `companyEsObjects` 返回值是 JSON 字符串，必须先解析成候选数组再使用。
- 高置信候选可自动选中：第一候选为存续企业、非分支/个体/明显噪音，且名称、行业、城市、官网、股票代码或用户上下文无冲突。
- 中置信候选可先选中并在 `meta.targetCompany.entityResolution` 记录候选和选择理由；如果后续 `baseinfo` 与候选冲突，应回到候选确认。
- 低置信候选必须让用户确认：多家存续主体都像目标、产品名对应多个企业、候选存在集团/子公司/分公司混杂，或辅助锚点冲突。
- `company search` 无候选或候选无法解释用户输入时，才使用 web search / 官网 / 新闻等公开来源补查主体；不得反复用多个企业 CLI 试错。
- 批量 CLI 返回后，按每个 `actionType` 对应的数据块分别消费；常见结构可能是 `results.<actionType>`、以 actionType 命名的字段或包含 actionType 标识的列表，必须以实际返回为准。
- `branchinfo` 等组织分布数据用于地图时，若总量不超过 100 条，应通过 `pageNum/pageSize` 分页取全；超过 100 条时可只展示总量、重点区域和明细样本，并在 `meta.retrievalCoverage` 与图表 `coverageNote` 中说明未全量展开原因。
- `baseinfo` 是主体锚点；如果批量结果中的主体名称、信用代码、注册号或上市身份与锚点冲突，相关数据不得写入目标客户事实。
- 企业基础批量结果用于“主体、组织、业务、经营能力”判断；风险批量结果用于“准入和履约风险”判断；知识产权批量结果用于“研发与技术资产”判断。
- `total` 是接口返回的记录总量，不等于有效数量或当前经营覆盖；首批返回不等于全量结论。列表型结果进入结论或图表前，应区分 `returnedCount`、`total`、`isLastPage` 和状态字段。
- 有 item 但核心字段为空、角色不明或状态不可用时，不算有效事实；可写入 `meta.retrievalCoverage` / `gaps`，不得写成“已获得产品/竞品/合作/资质事实”。
- 主体基础字段以 `company conc` 的 `baseinfo` 为最高优先级，包括工商全称、统一社会信用代码、成立日期、法定代表人、登记状态和注册资本。web、百科、新闻只能补充背景；若与工商口径冲突，应写“公开来源存在不同口径”或降低使用强度，不得直接覆盖工商字段。
- 资质、许可和证书进入能力标签前必须看状态和类型；食品经营许可、营业执照、特种设备使用登记等只作为合规/经营许可，不默认写成技术能力或行业地位亮点。荣誉能力类优先使用 `honorinfo` 和明确资质证书，例如国家企业技术中心、高新技术企业、专精特新等。
- 荣誉资质重点保留专精特新、高新技术企业、制造业单项冠军、行业准入、政府或协会认定等记录。
- 专利、软著、标准、商标和 ICP 需要与主营业务、产品、官网或公告交叉解释；数量多但与业务不匹配时，应降低技术实力结论强度。
- 裁判文书、专利权利要求书与说明书可能返回大段正文，默认不进入首批全量上下文；只有需要深挖时再定向调用并摘要消费。
- `search-mentions` 结果进入 `operationDynamics` 和 `evidence` 前，必须与新闻、公告、招投标、官网动态按 `report-data-model.md` 的动态去重规则合并。
- 追加查询默认不超过 2-3 页或 20-50 条关键记录；超过上限时输出总量、关键记录和业务含义，不展开全量明细。

## 5. Listed Financial CLI Rules

1. 先调用 `action-listed-company-introduction`，确认目标主体本身是上市公司，或用户明确要求上市主体/集团口径。
2. 三表默认只传 `companyName`；需要年度口径时先从返回列表中按 `reportYear/endDate/reportDateType/isAudit` 筛选。
3. 带 `reportYear` 调用失败时，不要在字符串/数字、`--data`/显式 flag 之间反复试；改用不带年份列表、上市公告、交易所公告、年报或公开来源补证。
4. 财务字段进入报告前必须转成业务可读指标和期间说明，不输出证券投资建议、股价判断或估值判断。

## 6. Failure Handling

| 情况 | 处理 |
|:---|:---|
| 批量 CLI 不存在或报错 | 使用当前 `--help` 中可用的单点 CLI 按同一数据目标最小化补查，并记录降级 |
| 某个 actionType 返回为空 | 不断言该事项不存在；公开来源仍无证据时动态裁剪 |
| CLI 字段缺失 | 只使用已返回字段；缺失字段可通过公开来源补查 |
| 多主体命中或主体偏移 | 优先展示 `company search` 的前 3-5 个候选让用户确认，确认前不生成完整报告 |
| 结果过多 | 先按时间窗、状态、金额、案由、权威性和主营相关性筛选 |

## 7. Web Search Fallback

公开来源补查优先级：

1. 企业官网、年报、公告、招股书、ESG 报告等企业一手资料。
2. 监管、法院、税务、政府采购、招投标、交易所等权威来源。
3. 主流新闻、行业媒体、协会或园区公开信息。
4. 其他可追溯网页。

补查结果进入报告时必须保留来源名称、链接或可追溯标识。公开来源与 CLI 冲突时，优先使用更权威、更近且能解释时间口径的来源；无法判断时降低结论强度。

web search / web fetch 控制：

- 已有内部 `company / risk / ip / market / listed` CLI 能覆盖的数据域，不为补充文字发散 web search。
- 专题阶段默认每个主题最多 1-2 个精准 query，每个 query 只消费前 3-5 条高质量结果；避免泛搜“行业地位、竞争格局、新闻”等带来大量无关结果。
- web fetch 只抓官网、公告、监管、交易所、招投标原文、权威新闻等高价值页面。遇到“操作过于频繁”、访问受限、登录/验证码、403、404、加载失败、明显反爬或长时间无正文时立即降级，不反复等待或换同类页面重试。
- `market get-news`、招投标 CLI、上市公告或 `search-mentions` 已能支撑事实时，不为获取二手网页正文长时间 fetch。
