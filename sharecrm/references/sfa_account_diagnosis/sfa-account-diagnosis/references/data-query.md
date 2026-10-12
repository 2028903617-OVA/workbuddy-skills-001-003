# 客户（AccountObj）数据查询配置 — Data_Query_Config

客户经营洞察需读取的数据及查询方式。统一走 `sharecrm` CLI，复杂参数用 `--data '<json>'`，中文确保 UTF-8。字段不确定先用 `describe get` 确认口径，不要编造字段名。

本配置不按“对象字段堆砌”组织，而按“洞察章节要消费哪些数据包”组织。原则是：先明确每一章要回答什么，再明确需要查哪些数据。

## 1. 对象定位

| 用途 | CLI 命令 | 关键参数 |
| --- | --- | --- |
| 按名称定位客户 | `sharecrm data record query-id-by-name --data '{"query":"<客户名称>","apiNames":["AccountObj"]}'` | `query` 为客户名称；`apiNames` 固定为 `["AccountObj"]`。 |
| 名称归一化兜底查询 | `sharecrm data record query-by-name --data '{"object_api_names":["AccountObj"],"name":"<客户名称或关键词>"}'` | `object_api_names` 固定为 `["AccountObj"]`；`name` 为客户名称或关键词。 |

sharecrm data record query-id-by-name --data '{"query":"<客户名称>","apiNames":["AccountObj"]}'

未命中时用名称归一化兜底（候选 ≥2 时展示 `_id` / `name` 及区分字段，等用户选定）：

sharecrm data record query-by-name --data '{"object_api_names":["AccountObj"],"name":"<客户名称或关键词>"}'

## 1.1 章节与数据包映射总表

| 洞察章节 | 回答问题 | 主要数据包 |
| --- | --- | --- |
| 页头摘要 | 这个客户是谁、当前大概状态如何 | A |
| 客户当前状态 | 现在是升温、停滞、低温还是防守 | A + B + C |
| 客户真实关注点 | 客户现在最关心什么、为什么会推动 | D |
| 组织突破口 | 从哪里最容易切进去 | B + E |
| 增长空间 | 这个客户还能不能继续做大 | C + F |
| 经营建议 | 下一阶段到底怎么经营 | A + B + C + D + E + F |
| 经营风险提示 | 哪些风险会影响经营节奏 | B + C |

## 2. 基础字段池

以下基础查询为各数据包共用。

### 2.1 客户主数据

sharecrm data record get-by-id --object_api_name AccountObj --id <account_id>

sharecrm data describe get --data '{"object_api_name":"AccountObj","simple_describe":true}'

> **敏感字段最小化**：`total_amount`（客户累计金额）等商务字段仅用于内部判断客户价值与投入优先级，不在输出正文逐条列示具体数值；如需引用只做定性描述（如“高价值客户”），字段不可见时不得模型补齐。

### 2.2 关联商机

sharecrm data record query-by-fields --data '{"object_api_name":"NewOpportunityObj","select_fields":["_id","name","sales_stage","sales_stage__r","sales_status","sales_status__r","amount","close_date","last_modified_time"],"filters":[{"field_api_name":"account_id","operator":"EQ","values":["<account_id>"]}],"orders":[{"field_api_name":"last_modified_time","is_asc":false}],"limit":20}'

### 2.3 关联联系人

sharecrm data record query-by-fields --data '{"object_api_name":"ContactObj","select_fields":["_id","name","title","department"],"filters":[{"field_api_name":"account_id","operator":"EQ","values":["<account_id>"]}],"limit":30}'

### 2.4 销售记录

sharecrm data record query-by-fields --data '{"object_api_name":"ActiveRecordObj","select_fields":["_id","active_record_content","active_record_type","related_object_id","create_time","created_by__r"],"filters":[{"field_api_name":"related_object_id","operator":"EQ","values":["<account_id>"]}],"orders":[{"field_api_name":"create_time","is_asc":false}],"limit":20}'

## 3. 数据包设计

以下数据包与新版客户经营洞察各章节一一对应。

### 二方数据源接入说明

本 skill 可编排调用 `sfa-account-due-diligence-report`，其结构化结果作为“外部情报增强层”接入，不替代 CRM 主数据，也不直接替代经营判断。

接入原则：

- 只增强 A / D / F 三类数据包。
- B / C / E 仍以 CRM 和内部互动数据为主。
- 二方情报用于补企业背景、业务重点、集团结构和外部风险信号，不直接生成经营建议。

### 二方尽调报告到数据包映射表

以下映射用于把 `sfa-account-due-diligence-report` 编排调用后返回的结构化结果稳定落到客户经营洞察的数据包中。重点不是“把尽调所有内容都搬进来”，而是明确哪些字段能增强 A / D / F。

| 尽调结果位置 | 进入数据包 | 在本 skill 中的业务作用 | 典型可转成的判断 |
| --- | --- | --- | --- |
| `meta.targetCompany` | A | 补齐客户主体识别和工商基础状态 | 客户主体清晰 / 名称需核实 / 存续状态正常 |
| `basicProfile` | A | 补齐客户基础画像和企业体量背景 | 区域龙头 / 集团型客户 / 制造型客户 |
| `ownership` | A、F | 判断是否集团化、是否有分子公司和复制空间 | 集团经营 / 分支复制 / 跨子公司拓展 |
| `businessModel` | D、F | 判断客户当前业务重点和可切入业务场景 | 当前关注增长 / 当前关注交付 / 可从某业务线切入 |
| `industryContext` | D | 判断客户外部压力、行业诉求和关注点背景 | 关注合规 / 关注降本 / 关注产能与交付 |
| `chainContext` | D、F | 判断客户在链条中的位置和上下游带来的扩展机会 | 渠道型客户 / 平台型客户 / 生态扩展空间明显 |
| `operationDynamics` | D | 判断近期是否有经营动作和推动信号 | 新业务启动 / 区域扩张 / 战略调整 |
| `publicCompanyFinancials` | A、F | 判断客户经营稳定度和是否值得持续投入 | 经营稳健 / 扩张承压 / 投入需谨慎 |
| `cooperationContext` | D、F | 判断客户合作偏好、供应商格局和潜在扩展口 | 既有合作格局稳定 / 存在替换窗口 / 可借生态切入 |
| `cooperationHistory` | F | 判断历史合作延展性和复制线索 | 有跨部门复制基础 / 有持续合作惯性 |
| `riskProfile` | A | 只补充客户经营稳定性背景，不直接替代 CRM 风险判断 | 外部经营异常 / 主体稳定但需留意 |
| `sellerRelevantSignals` | D、F | 补充和卖方最相关的客户信号 | 我方相关窗口出现 / 竞争挤压增强 |

### 二方尽调报告落到 A / D / F 的字段明细

#### A 包：客户基础包

| 尽调字段 | 落点用途 | 输出时怎么用 |
| --- | --- | --- |
| `meta.targetCompany.legalName` | 确认客户主体 | 页头摘要中用“客户全称” |
| `meta.targetCompany.creditCode` | 核实主体唯一性 | 仅内部校验，不进入正文 |
| `meta.targetCompany.registrationStatus` | 判断主体是否正常存续 | 可转成“经营主体稳定” |
| `basicProfile.companyType` | 判断客户类型 | 可转成“集团客户 / 民企 / 国企 / 上市公司” |
| `basicProfile.industry` | 补行业归类 | 页头摘要、状态判断使用 |
| `basicProfile.registeredCapital` | 判断客户体量背景 | 只做定性，不直接秀数字 |
| `basicProfile.listedStatus` | 判断公开经营透明度 | 可转成“上市体系客户” |
| `ownership.controllers` | 判断控制关系 | 可转成“决策集中 / 集团主导” |
| `riskProfile[*]` | 补外部稳定性风险 | 只在页头或状态中做一句提醒 |
| `publicCompanyFinancials.revenueSummary` / `profitSummary` | 判断经营稳健度 | 可转成“经营承压 / 增长稳定” |

#### D 包：关注点证据包

| 尽调字段 | 落点用途 | 输出时怎么用 |
| --- | --- | --- |
| `businessModel.mainBusinesses` | 判断客户主要经营主题 | 解释客户到底在做什么 |
| `businessModel.productsOrServices` | 判断业务形态 | 识别与我方方案的贴合点 |
| `businessModel.currentBusinessFocus` | 判断当前最强关注点 | 可直接支持“真实关注点”结论 |
| `industryContext.summary` | 给关注点提供行业背景 | 解释为什么现在会推动 |
| `industryContext.trends` / `policies` / `commonPainPoints` | 提炼外部驱动因素 | 可转成“政策驱动 / 降本驱动 / 合规驱动” |
| `industryContext.customerPosition` | 判断客户所处位置 | 解释其诉求强弱 |
| `chainContext.chainPosition` / `valueRole` | 判断客户链位 | 解释其为何更关注交付、渠道或协同 |
| `operationDynamics[*]` | 判断近期经营动作 | 作为“为什么现在推进”的证据 |
| `cooperationContext.supplierAndCompetitorSignals` | 判断合作偏好和替换窗口 | 解释为什么需求未必只是表层功能诉求 |
| `sellerRelevantSignals[*]` | 判断与我方最相关的经营信号 | 作为关注点结论的补证 |

#### F 包：扩展空间包

| 尽调字段 | 落点用途 | 输出时怎么用 |
| --- | --- | --- |
| `ownership.branches` | 判断区域复制空间 | 可转成“存在异地复制可能” |
| `ownership.investments` | 判断关联公司拓展空间 | 可转成“可向关联主体延展” |
| `ownership.relatedCompanies` | 判断集团协同空间 | 可转成“可做集团横向扩展” |
| `businessModel.targetCustomers` | 判断客户业务外延 | 识别其客户结构是否带来新机会 |
| `businessModel.deliveryModel` | 判断复制难度 | 可转成“标准化复制 / 定制化较重” |
| `chainContext.upstream` / `downstream` / `channels` / `ecosystem` | 判断产业链延展机会 | 可转成“可沿渠道 / 生态 / 上下游扩展” |
| `chainContext.businessImplications` | 判断拓展业务意义 | 解释为什么值得追加投入 |
| `cooperationContext.businessImplications` | 判断合作历史是否可放大 | 可转成“已有合作基础，可放大” |
| `cooperationHistory[*]` | 判断历史复制线索 | 识别是否已有跨场景合作痕迹 |
| `publicCompanyFinancials.cashFlowSummary` / `businessImplications` | 判断投入价值与节奏 | 可转成“值得持续投入 / 暂不宜激进扩展” |

### 数据包A：客户基础包

**服务章节**：页头摘要、客户当前状态

**回答问题**：

- 这个客户是谁
- 客户级别和价值大概怎样
- 当前由谁负责、处于什么基础状态

**主要数据来源**：

- 客户主数据
- 评分结果（上游输入）

**最小字段**：

- `_id`
- `name`
- `account_level`
- `industry`
- `owner`
- `customer_status`
- `deal_status`
- `total_amount`
- `last_followed_time`

**二方数据增强项（来自 `sfa-account-due-diligence-report`）**：

- 企业主体全称
- 工商登记状态
- 统一社会信用代码
- 公司类型
- 注册资本
- 是否上市 / 是否集团化
- 基本经营稳定性信号
- 外部风险摘要（若有重大异常）

**二方数据主要来源位置**：

- `meta.targetCompany`
- `basicProfile`
- `ownership`
- `riskProfile`
- `publicCompanyFinancials`

### 数据包B：关系活跃包

**服务章节**：客户当前状态、组织突破口、经营风险提示

**回答问题**：

- 当前合作温度如何
- 最近有没有持续互动
- 关系是不是过度依赖单点

**主要数据来源**：

- 关联联系人
- 销售记录

**最小字段**：

- 联系人：`name`、`title`、`department`
- 销售记录：`active_record_content`、`active_record_type`、`create_time`

### 数据包C：机会活跃包

**服务章节**：客户当前状态、增长空间、经营风险提示

**回答问题**：

- 当前在跑机会有多少
- 哪些机会在推进，哪些停滞
- 客户经营是否有主线机会支撑

**主要数据来源**：

- 关联商机

**最小字段**：

- `name`
- `sales_stage`
- `amount`
- `close_date`
- `last_modified_time`

### 数据包D：关注点证据包

**服务章节**：客户真实关注点

**回答问题**：

- 客户表面上在关心什么
- 真正驱动当前经营动作的是什么
- 现在为什么还没更快推进

**主要数据来源**：

- 销售记录
- 在跑商机主题
- 联系人角色分布
- 上游需求分析结果（若有）

**最小字段**：

- 销售记录内容：`active_record_content`
- 商机名称和阶段：`name`、`sales_stage`
- 联系人职务和部门：`title`、`department`

**说明**：

- 若已提供上游 `Needs_Discovery_Result`，优先消费其“结论 + 简短依据”。

**二方数据增强项（来自 `sfa-account-due-diligence-report`）**：

- 主营业务
- 产品 / 服务类型
- 当前业务重点
- 行业环境摘要
- 产业链位置
- 与卖方业务相关的客户侧情报信号
- 公开合作 / 供应链 / 上下游关系中与当前经营相关的内容

**二方数据主要来源位置**：

- `businessModel`
- `industryContext`
- `chainContext`
- `cooperationContext`
- `operationDynamics`
- `sellerRelevantSignals`

### 数据包E：组织突破包

**服务章节**：组织突破口

**回答问题**：

- 当前从哪条线最容易切进去
- 谁是杠杆角色
- 谁是拍板关键
- 隐性阻力在哪里

**主要数据来源**：

- 关联联系人
- 销售记录
- 关联商机
- 上游决策链 / Coach 结果（若有）

**最小字段**：

- 联系人：`name`、`title`、`department`
- 销售记录：`active_record_content`、`create_time`
- 商机：`name`、`sales_stage`

### 数据包F：扩展空间包

**服务章节**：增长空间

**回答问题**：

- 当前主机会是什么
- 还有哪些扩展方向
- 有没有复制可能性
- 值不值得继续追加投入

**主要数据来源**：

- 客户主数据
- 关联商机
- 历史合作线索
- 联系人和部门覆盖范围

**最小字段**：

- `account_level`
- `industry`
- `total_amount`
- 商机：`name`、`sales_stage`、`amount`
- 联系人：`department`

**二方数据增强项（来自 `sfa-account-due-diligence-report`）**：

- 分支机构
- 关联公司
- 投资关系
- 集团结构
- 公开合作关系
- 产业链上下游关系
- 潜在可复制业务单元

**二方数据主要来源位置**：

- `ownership.branches`
- `ownership.investments`
- `ownership.relatedCompanies`
- `chainContext`
- `cooperationContext`

## 4. 按章节的最小查询范围

| 章节 | 必需数据包 |
| --- | --- |
| 页头摘要 | A |
| 客户当前状态 | A + B + C |
| 客户真实关注点 | D |
| 组织突破口 | B + E |
| 增长空间 | C + F |
| 经营建议 | A + B + C + D + E + F |
| 经营风险提示 | B + C |

## 5. 按意图的最小查询范围

| 意图 | 需查询 |
| --- | --- |
| 生成画像 | A + B + D |
| 下一步怎么跟 | B + C + D + E + F |
| 洞察（默认） | A + B + C + D + E + F |

> `Scoring_Result`（必需）优先来自 `get_profile_score --objectApiName AccountObj`；仅当 CLI 失败、为空、无可用评分信息或对象不匹配时，才回退上游 `sfa-account-score`。`AI_Stage` 不由其他 skill 提供，调用方必须根据本次查询到的 `deal_status`、关联商机、联系人和销售记录，按 `SKILL.md` Flow 第 4 步直接判断；`sfa-account-due-diligence-report` 则可由本 skill 编排调用，作为可选增强输入；详见 `SKILL.md`。

## 6. 二方数据接入边界

- 二方情报主要服务于“客户是谁”“客户当前业务重点是什么”“这个客户还能不能继续做大”三个问题。
- 二方情报不直接定义“组织突破口”与“经营建议”，这两章仍以 CRM 内部互动、联系人和在跑机会为主。
- 如果二方情报缺失，不阻断客户经营洞察；仅降低 A / D / F 三类数据包的解释深度。

## 7. 下游组装示例

以下不是强制 schema，而是建议编排层在把 CRM 与尽调结果汇总后，至少整理成下面三个可消费对象。这样下游模板不必自己再理解原始尽调字段。

### 7.1 A 包组装示例：客户基础包

```json
{
  "accountName": "某制造集团有限公司",
  "legalName": "某制造集团股份有限公司",
  "industry": "高端装备制造",
  "accountLevel": "战略客户",
  "owner": "张三",
  "customerStatus": "持续经营",
  "businessScale": "集团型客户，体量较大",
  "listedStatus": "上市公司",
  "ownershipSignal": "集团决策特征明显",
  "operationHealth": "经营整体稳定",
  "externalRiskNote": "存在少量司法风险记录，暂未见重大经营中断信号",
  "evidence": [
    "CRM客户主数据",
    "basicProfile.companyType",
    "basicProfile.listedStatus",
    "ownership.controllers",
    "riskProfile"
  ]
}
```

**组装说明**：

- `accountName / accountLevel / owner / customerStatus` 主要来自 CRM。
- `legalName / listedStatus / businessScale / ownershipSignal / operationHealth` 主要来自尽调增强。
- `externalRiskNote` 只保留一句话，不展开风险明细。

### 7.2 D 包组装示例：关注点证据包

```json
{
  "surfaceFocus": "客户当前表面上重点关注交付稳定与成本控制",
  "realFocus": "真实关注点是新产线投产后的交付连续性和管理协同效率",
  "pushReason": "近期产能扩张和重点项目交付压力上升，推动相关能力补齐",
  "blockingReason": "当前仍缺少可落地的跨部门协同方案，关注点尚未完全收口",
  "businessContext": "客户主营高端装备制造，当前业务重点向新产线和重点区域复制倾斜",
  "industryPressure": "行业处于提效和交付稳定双重压力期",
  "chainRole": "客户处于产业链核心制造与交付节点，对上下游协同较敏感",
  "recentSignals": [
    "近两个月多次提到产线交付节奏",
    "公开信息显示客户推进重点产能布局",
    "拜访记录反复出现成本与协同关键词"
  ],
  "evidence": [
    "active_record_content",
    "businessModel.currentBusinessFocus",
    "industryContext.summary",
    "operationDynamics",
    "sellerRelevantSignals"
  ]
}
```

**组装说明**：

- `surfaceFocus` 尽量从 CRM 记录和商机主题中提炼。
- `realFocus / pushReason / blockingReason` 由 CRM 互动证据和尽调上下文共同判断。
- `businessContext / industryPressure / chainRole` 是解释层，不宜写成长段背景介绍。
- `recentSignals` 建议保留 2 到 3 条短证据，便于模板直接引用。

### 7.3 F 包组装示例：扩展空间包

```json
{
  "currentMainOpportunity": "当前主线仍是核心产线相关机会",
  "expansionDirections": [
    "向关联工厂复制",
    "向区域子公司延展",
    "沿上下游协同场景扩展"
  ],
  "groupExpansionSignal": "客户存在分支机构与关联主体，具备集团横向复制基础",
  "industryExpansionSignal": "客户在产业链中连接上下游，存在生态延展可能",
  "investmentAdvice": "值得继续投入，但应优先围绕已验证场景做复制",
  "difficultyNote": "部分场景标准化程度一般，复制节奏不宜过快",
  "evidence": [
    "ownership.branches",
    "ownership.relatedCompanies",
    "chainContext.upstream/downstream/channels",
    "cooperationHistory",
    "publicCompanyFinancials.businessImplications"
  ]
}
```

**组装说明**：

- `currentMainOpportunity` 仍以 CRM 商机主线为主。
- `expansionDirections` 建议只保留 2 到 3 个，不要发散成机会池。
- `groupExpansionSignal / industryExpansionSignal` 用于说明为什么有空间，不直接替代行动建议。
- `investmentAdvice` 只回答“值不值得继续做大”，不要提前写成详细行动计划。

### 7.4 组装原则

- 下游拿到的应是“已整理结论 + 简短证据”，而不是尽调原始字段清单。
- 每个数据包最多保留 1 个主结论、2 到 3 个辅助判断、2 到 3 条证据。
- CRM 负责回答“现在内部经营到哪了”，尽调负责回答“这个客户外部到底是什么样”，两者不要互相替代。
- 如果尽调与 CRM 结论冲突，优先在数据包中显式写出“需进一步核实”，不要强行合并。
