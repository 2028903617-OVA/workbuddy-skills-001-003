# 外部情报数据源与最少 Loop 规则

本文件定义客户简报中可用的 `sharecrm intelligence` 外部情报 CLI、触发条件和最少查询路径。外部情报用于补充企业背景、市场动态、风险、上市公司、招投标、知识产权和特殊组织信息，不替代 CRM 与 Memory。

## 使用原则

- CRM 与 Memory 是客户事实主源；外部情报只能补充公开背景、外部风险和战略动态。
- 未确认唯一客户前，不查询下游外部明细；若只为企业主体归一，可先用 `company search` 找候选，并让用户确认。
- 外部情报默认不触发；只有用户明确要求、CRM/Memory 存在信息缺口，或外部动态会改变核心判断时才查询。
- 优先使用聚合命令 `conc` 或一级摘要命令；只有摘要出现明确风险、上市、招投标、知识产权等信号时再下钻明细。
- 每条外部情报写入报告前必须保留：来源分类、CLI 名称、发布日期或查询时间、置信度、是否需要 AE/CRM 核对。
- 外部情报与 CRM 冲突时，不直接覆盖 CRM；写为“外部信息显示...，需核对 CRM/AE”。
- 查询状态使用：`已读取 / 无数据 / 权限不足 / 未触发查询 / 查询失败`。
- 基础事实足够支撑简报核心结论后停止补查；不要为了填满版面继续查询外部情报。

## 可用 CLI 分类

| 分类 | 优先命令 | 明细命令 | 适用信息 |
| --- | --- | --- | --- |
| 企业信息 | `sharecrm intelligence company search`、`sharecrm intelligence company conc` | `enterprise-basic-information`、`obtain-registration-information`、`obtain-business-information`、`action-enterprise-shareholder-info`、`action-sales-assistantenterprise-basic-info`、`action-enterprise-basic-report`、`action-enterprise-outward-investment-info`、`get-main-personnel`、`get-funding`、`get-branch`、`get-honor-qualification`、`obtain-tax-payer`、`obtain-tax-credit-evaluation`、`get-basic-info`、`internet-search` | 企业主体、工商、经营、股东、高管、融资、分支机构、荣誉资质、税务资质 |
| 市场信息 | `sharecrm intelligence market get-news`、`sharecrm intelligence market search-mentions` | `bidding-pinganzhengxin`、`customs-import-and-export`、`get-baseEaNews` | 新闻舆情、社媒提及、招投标、海关进出口、企业动态 |
| 风险信息 | `sharecrm intelligence risk conc`、`sharecrm intelligence risk enterprise-risk` | `action-sales-assistant-enterprise-judicial-risk`、`action-enterprise-risk-report`、`action-serious-illegal-info-of-enterprise`、`action-judicial-risk-legal-case`、`action-judicial-risk-executed-person`、`action-judicial-risk-exit-restriction-info`、`action-judicial-risk-restricting-high-consumption`、`action-judicial-risk-judgment-documents`、`action-judicial-risk-finalized-case`、`action-judicial-risk-dishonest-executor`、`action-judicial-risk-court-announcement`、`action-judicial-risk-hearing-announcement`、`obtain-abnormal-operation`、`obtain-administrative-penalty`、`get-bankruptcy`、`get-environmental-punishment`、`get-major-tax-violation` | 经营异常、司法、执行、限制高消费、行政处罚、破产、环保处罚、重大税违 |
| 上市公司信息 | `sharecrm intelligence listed listed_company` | `action-sales-assistant-financial-indicators`、`action-listed-company-executive-info`、`action-company-profit-statement`、`action-listed-company-introduction`、`action-stock-company-financial-analysis`、`action-listed-company-announcement`、`action-company-balance-sheet`、`action-cash-flow-statement`、`action-listed-company-financial-report` | 上市身份、财务指标、高管、公告、财报、利润表、资产负债表、现金流量表 |
| 企业知识产权 | `sharecrm intelligence ip conc` | `sharecrm intelligence ip intellectual-property`、`sharecrm intelligence company get-intellectual-property-pledge` | 专利、商标、软著、知识产权质押 |
| 特殊组织信息 | `sharecrm intelligence s-organization special-organization` | 无 | 政府、事业单位、社会组织等特殊主体信息 |

## 最少 Loop 查询路径

1. 先用 CRM 客户名、统一社会信用代码、官网或用户提供的全称确定外部查询关键词。
2. 如企业主体不明确，先执行 `company search`，多候选时让用户确认。
3. 需要企业基本背景时，优先执行 `company conc`，不直接展开全部工商明细。
4. 需要近期动态时，在 `market get-news` 与 `market search-mentions` 中择一；新闻优先用 `get-news`，舆情/社媒优先用 `search-mentions`。
5. 需要风险时，先执行 `risk conc` 或 `risk enterprise-risk`；只有发现明确风险类型时再查对应明细。
6. 判断为上市公司时，先执行 `listed listed_company`；再按场景选择公告、财务指标、财报或高管信息。
7. 仅当客户行业、商机、竞品或采购窗口需要时，查询招投标、知识产权、进出口或特殊组织信息。

## 四类客户简报路由

| 简报 | 触发条件 | 推荐查询 | 默认上限 |
| --- | --- | --- | --- |
| 标准版客户简报 | 用户要求外部信息；CRM/Memory 无法解释客户画像、业务状态、战略动态或风险；`--full` | `company conc`；必要时 `market get-news`、`risk conc`、`listed listed_company`、`ip conc`、`market bidding-pinganzhengxin` | 标准 3 次；`--full` 5 次 |
| 见客前客户简报 | 用户明确要求外部动态；今天会议目标依赖近期新闻、舆情、招投标或突发风险 | `market get-news` 或 `market search-mentions`；采购窗口明显时用 `market bidding-pinganzhengxin`；重大风险才用 `risk conc` | 默认 1 次；强触发 2 次 |
| 高层陪访简报 | 陪访价值判断依赖新闻、融资、财报、政策、上市信息、招投标、司法风险或重大舆情 | 上市客户用 `listed listed_company` 后选公告/财务/高管；非上市用 `company conc`、`market get-news`、`risk conc`、`company get-funding`、`market bidding-pinganzhengxin` | 简洁版 2 次；详细版或 `--full` 4 次 |
| 团队交接简报 | 外部动态会影响接手连续性、风险敏感点、第一周核对事项或历史包袱 | `risk conc`、`risk enterprise-risk`；必要时查破产、经营异常、行政处罚、重大税违；交接空窗期用 `market get-news`；采购窗口用 `market bidding-pinganzhengxin` | 标准 2 次；`--full` 3 次 |

## 输出位置

- 标准版：写入客户画像、战略动态、风险矩阵、开放问题和参考来源。
- 见客前：只写入会前预警、现场验证问题或“绝对不要做”，不要扩成长篇背景。
- 高层陪访：写入关键价值、最大风险与敏感点、领导可介入点、领导不能做什么。
- 团队交接：写入交接缺口、风险敏感点、第一周核对事项和接手建议。

## 禁止行为

- 不因为公开新闻或舆情直接推断客户真实痛点、预算状态、决策链或商机阶段。
- 不用工商风险直接否定商机；只能提示需核对的风险和可能影响。
- 不把外部“无数据”写成客户不存在、无风险、无招投标或无上市关系。
- 不为了样式完整查询所有外部 CLI。
- 不把外部情报原文大段复制进简报；只保留与当前销售判断相关的摘要。
