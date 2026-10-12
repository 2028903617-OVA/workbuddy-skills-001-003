# 商机竞争分析数据查询配置 — Data_Query_Config

定义竞争情报分析需要读取的 CRM 数据。主对象为 `NewOpportunityObj`；竞争事实主要来自商机主数据、关联客户、报价单 / 报价明细、竞争对手明细、竞对企业风险、联系人关系、销售记录和用户明确补充事实。

所有 CLI 只在 `SKILL.md` 的 `ToolsList` 中集中声明；本文件只说明调用时机、参数值、字段范围和解释规则。字段不确定时，先使用 ToolsList「获取对象字段描述」确认实际口径，不要编造字段名。

## 0. 卖方行业配置

| 项目 | 内容 |
| --- | --- |
| 调用工具 | `获取卖方配置` |
| 参数 | `key="service_models"` |
| 读取规则 | `service_models` 通常返回 `{"value":"逗号分隔字符串"}`；取其中代表卖方主营行业的值作为 `SELLER_INDUSTRY`。 |
| 异常处理 | `service_models` 为空时，`SELLER_INDUSTRY` 留空；远端文档检索 `coreTopics` 不拼接行业，并在输出标注“缺少卖方行业信息”。 |

## 1. 对象定位

| 项目 | 内容 |
| --- | --- |
| 首选调用工具 | `按名称查询记录 ID` |
| 参数 | `query="<商机名称或项目名称>"`；`apiNames=["NewOpportunityObj"]` |
| 未命中兜底 | 改用 `按字段条件查询数据`，`object_api_name=NewOpportunityObj`，`select_fields="_id,name,account_id,account_id__r,sales_stage,sales_stage__r,competitor,amount,last_modified_time"`，`name-like="<关键词>"`，`limit=10`，`sort=last_modified_time:desc`。 |
| 选择规则 | 候选 `>=2` 时，必须展示 `_id`、`name`、`account_id__r`、`competitor`、`sales_stage__r` 供用户选择。 |

## 2. 只给客户名称时的定位

| 项目 | 内容 |
| --- | --- |
| 首选调用工具 | `按名称查询记录 ID` |
| 参数 | `query="<客户名称>"`；`apiNames=["AccountObj"]` |
| 反查商机 | 使用 `按字段条件查询数据`，`object_api_name=NewOpportunityObj`，`select_fields="_id,name,account_id,account_id__r,sales_stage,sales_stage__r,competitor,amount,last_modified_time"`，`account_id-eq="<account_id>"`，`limit=10`，`sort=last_modified_time:desc`。 |
| 选择规则 | 客户下存在多个商机时，必须展示候选并等待用户选择唯一商机。 |

## 3. 商机主数据（必须查询）

| 项目 | 内容 |
| --- | --- |
| 全量读取 | 使用 `按 ID 获取单条记录`，`object_api_name="NewOpportunityObj"`，`id="<opportunity_id>"`。 |
| 部分字段读取 | 使用 `按字段条件查询数据`，`object_api_name=NewOpportunityObj`，`select_fields="_id,name,account_id,account_id__r,sales_stage,sales_stage__r,amount,win_rate,close_date,owner,owner__r,competitor,customer_budget,last_followed_time,last_modified_time,create_time"`，`_id-eq="<opportunity_id>"`，`limit=1`。 |
| 字段确认 | 字段不确定时，先调用 `获取对象字段描述`，`object_api_name="NewOpportunityObj"`。 |
| 使用规则 | `get-by-id` 返回整条记录；若只想控制返回体量，应优先使用 `query-by-fields`。 |

## 4. 关联客户背景（必须查询）

| 项目 | 内容 |
| --- | --- |
| 全量读取 | 使用 `按 ID 获取单条记录`，`object_api_name="AccountObj"`，`id="<account_id>"`。 |
| 部分字段读取 | 使用 `按字段条件查询数据`，`object_api_name=AccountObj`，`select_fields="_id,name,account_level,account_level__r,industry,industry__r,industry_level1,industry_level1__r,industry_level2,industry_level2__r,owner,owner__r,customer_status,customer_status__r,region,total_amount,last_followed_time,last_modified_time,create_time"`，`_id-eq="<account_id>"`，`limit=1`。 |
| 关键解释 | 必须读取行业字段；优先使用 `industry_level1` / `industry_level2` 作为 `BUYER_INDUSTRY`。若前两者为空，有其他显式行业字段时也可使用。 |
| 使用边界 | 买方行业只用于判断客户关注点和权重，不替代商机竞争事实。 |

## 5. 报价单与报价明细（条件必须查询）

| 项目 | 内容 |
| --- | --- |
| 触发条件 | 用户提到价格、报价、折扣、压价、竞品低价、商务成本、ROI 或商务谈判时，本节必须查询；其他场景建议查询最新报价作为竞争态势证据。 |
| 报价单查询 | 使用 `按字段条件查询数据`，`object_api_name=QuoteObj`，`select_fields="_id,name,new_opportunity_id,account_id,owner,owner__r,quote_time,quote_amount,record_type,record_type__r,last_modified_time"`，`new_opportunity_id-eq="<opportunity_id>"`，`limit=5`，`sort=last_modified_time:desc`。 |
| 报价明细查询 | 使用 `按字段条件查询数据`，`object_api_name=QuoteLinesObj`，`select_fields="_id,quote_id,product_id,product_id__r,quantity,price,selling_price,sales_price,discount,total_discount,sales_amount,total_amount,last_modified_time"`，`quote_id-eq="<quote_id>"`，`limit=30`，`sort=last_modified_time:desc`。 |
| 字段确认 | 对象或字段不确定时，先对 `QuoteObj`、`QuoteLinesObj` 分别调用 `获取对象字段描述`。 |
| 异常处理 | 查不到报价时不阻断，但必须标注“报价事实缺失”，不得编造价格结论。 |

## 6. 联系人、关系覆盖与客户倾向线索（建议查询）

| 项目 | 内容 |
| --- | --- |
| 商机关联联系人 | 使用 `按字段条件查询数据`，`object_api_name=NewOpportunityContactsObj`，`select_fields="_id,new_opportunity_id,contact_id,contact_id__r,role,role__r,is_key_person,decision_role,decision_role__r,influence_direction,report_to,support_degree,last_modified_time"`，`new_opportunity_id-eq="<opportunity_id>"`，`limit=20`，`sort=last_modified_time:desc`。 |
| 联系人详情 | 如需职位 / 部门详情，使用 `按 ID 获取单条记录`，`object_api_name="ContactObj"`，`id="<contact_id>"`。 |
| 联系人关系对象 | 使用 `按字段条件查询数据`，`object_api_name=NewOpportunityContactRelationshipObj`，`select_fields="_id,name,new_opportunity_id,contact_id,contact_id__r,related_contact_id,related_contact_id__r,relationship_type,relationship_type__r,influence_direction,support_degree,support_degree__r,report_to,decision_role,decision_role__r,remark,last_modified_time"`，`new_opportunity_id-eq="<opportunity_id>"`，`limit=50`，`sort=last_modified_time:desc`。 |
| 字段确认 | 关系对象 API 名与字段以实际环境 `describe get` 为准；若字段不存在，按 `describe` 返回结果调整到实际字段或归入 `ContactObj` / `ActiveRecordObj`。 |
| 使用边界 | 无联系人或关系记录不等于我方关系弱、竞品关系强；只能标注“关系覆盖证据不足”。 |

## 7. 关联竞争对手明细（必须查询）

| 项目 | 内容 |
| --- | --- |
| 先确认口径 | 先使用 `获取对象字段描述`，`object_api_name="CompetitiveLinesObj"`，确认对象与字段定义。 |
| 明细查询 | 使用 `按字段条件查询数据`，`object_api_name=CompetitiveLinesObj`，`select_fields="_id,name,new_opportunity_id,competitor,competitor__r,our_advantage,our_disadvantage,competitor_quote_amount,competitive_product,competitive_product__r,remark,last_modified_time"`，`new_opportunity_id-eq="<opportunity_id>"`，`limit=20`，`sort=last_modified_time:desc`。 |
| 变体适配 | 若环境无 `CompetitiveLinesObj`，按 `describe` 返回的实际关系对象调整 `object_api_name` 与关联字段，不要跳过竞争对手明细查询。 |
| 敏感信息规则 | 竞争对手报价金额属敏感商务信息，仅用于内部判断竞争 / 预算风险；输出正文只做定性描述。 |
| 空结果解释 | 查询为空时按“暂未发现明确竞品信息”处理，并结合销售记录、客户反馈继续核实隐性竞品、自建替代或历史供应商延续，不得直接断言“没有竞争对手”。 |

## 8. 竞对企业风险查询（建议查询）

### 8.1 结构化企业风险

| 项目 | 内容 |
| --- | --- |
| 调用工具 | `查询竞对企业风险` |
| 参数 | `companyName="<竞对公司名称>"`；`actionType="<风险类型>"`。 |
| 公司名来源 | 优先取自 `CompetitiveLinesObj.competitor__r` / `competitor`；若明细为空，可从商机主数据 `competitor`、销售记录或用户明确输入中提取。 |
| 默认优先风险类型 | `abnormalinfo`、`illegalinfo`、`punishinfo`、`dishonestinfo`、`xianxiaoinfo`、`zhixinginfo`、`zhongbeninfo`、`courtfiledcaseinfo`、`courtnotice`、`lawsuitinfo`、`bankruptcyinfo`、`environmentpunishinfo`、`taxpunishinfo`、`taxstatusinfo`、`companypunishmentinfocreditchinainfo`。 |
| 选择规则 | 若竞对超过 2 家，优先查询当前影响最大的 1-2 家，其他竞对列入情报缺口。 |
| 异常处理 | 某类风险结果为空时，只能写“该类风险当前未检索到记录”，不得写成“无风险”；无法确认竞对公司实体时，标注“竞对主体待确认”，不执行该查询。 |

### 8.2 互联网搜索交叉验证

| 项目 | 内容 |
| --- | --- |
| 调用工具 | `互联网搜索` |
| 参数 | `query="<竞对公司名称> 风险 行政处罚 诉讼 失信 经营异常"` |
| 使用规则 | 互联网搜索只作为结构化风险的补充线索；必须与企业风险、销售记录或客户反馈交叉验证。 |
| 风险边界 | 不得把未经核实的搜索摘要写成确定事实。 |

## 9. 销售记录（必须查询）

| 项目 | 内容 |
| --- | --- |
| 调用工具 | `按字段条件查询数据` |
| 参数 | `object_api_name=ActiveRecordObj`，`select_fields="_id,active_record_content,active_record_type,new_opportunity_id,related_object_id,create_time,created_by__r"`，`new_opportunity_id-eq="<opportunity_id>"`，`limit=20`，`sort=create_time:desc`。 |
| 使用规则 | 销售记录用于识别竞品动作、客户评价、竞品报价线索、选型偏好、关系覆盖、卡点和下一步动作。 |

## 10. 使用规则

- 必须查询第 0 / 1 / 3 / 4 / 7 / 9 节；只给客户名称时先执行第 2 节；涉及价格或商务成本时必须执行第 5 节；需要判断关系覆盖或客户倾向时执行第 6 节；能确认竞对公司实体时建议执行第 8 节。
- 竞品名称、报价、折扣、关系覆盖、客户倾向、竞品动作必须来自 CRM 字段、报价记录、竞争对手明细、销售记录、联系人关系或用户明确输入。
- 竞对企业风险必须来自结构化企业风险查询、互联网搜索、销售记录或用户明确输入；只作为风险观察和验证建议，不作为产品能力或商务成本评分的直接替代。
- 查询不到报价单时，不阻断；标注“报价事实缺失”，不得编造价格结论。
- 查询不到联系人或关系对象时，不阻断；标注“关系覆盖证据不足”，不得把缺失记录当作我方或竞品关系强弱结论。
- 企业风险查询失败、无权限或结果为空时，不阻断；标注“企业风险证据不足”或“当前未检索到记录”，不得断言“无风险”。
- CRM 与用户输入冲突时，在输出中列明冲突并按证据来源分层判断，不得静默覆盖。
