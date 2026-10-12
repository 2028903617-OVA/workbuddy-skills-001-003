# Skill 编排规则

本文件定义 `account-due-diligence-report` 如何调用并消费：

- `account-industry-analysis`
- `account-chain-analysis`
- `account-cooperation-history`

目标不是把专题分析报告整段拼进主报告，而是把与目标客户理解直接相关的摘要、判断和证据，稳定写入主报告的数据模型和章节。

## 1. 总体编排目标

- 让专题 Skill 继续保留独立输出能力。
- 在主报告场景下，强制专题 Skill 进入“编排调用模式”。
- 主报告只消费与目标客户理解相关的结构化结果，不消费完整专题模板。
- 主报告对最终叙事、章节裁剪、证据取舍和冲突处理负责。

## 2. 总体规则

### 2.1 调用模式

- 用户单独提问“行业分析 / 产业链分析 / 合作历史”时，专题 Skill 独立输出完整模板。
- 用户提问“客户尽调报告 / 客户情报报告 / 帮我看看这个客户”时，专题 Skill 只能返回编排消费契约中的字段。
- 主报告不得直接复用专题 Skill 的完整标题、章节顺序、固定表格和完整待核实清单。

### 2.2 消费边界

- 主报告只消费：摘要、关键判断、业务含义、关键证据、必要待核实事项。
- 主报告不消费：触达路径、销售话术、跟进节奏、作战计划、资源投入建议、P0/P1/P2 定档、线索/商机创建建议。
- 专题 Skill 的卖方相关推理只保留“客户侧信号”，不展示卖方画像原文。

### 2.3 事实优先级

- 企业主体、股权、分支、对外投资、风险等基础企业事实，以主报告直接获取的企业情报 CLI / 公开来源为主。
- CRM 内部客户、联系人、商机、合同、订单、回款、活动记录，以主报告直接查询的 CRM 数据为主。
- 专题 Skill 提供的是“围绕某一主题整理后的客户理解结果”，不是替代主报告重新定义基础事实。

### 2.4 冲突处理

专题 Skill 结论冲突时，按以下顺序处理：

1. 证据更直接的优先于二手转述。
2. 时间更新的优先于过期资料。
3. 来源更权威的优先于普通新闻或转载。
4. 明确事实优先于模型推断。

仍无法判定时：

- 不强行合并为单一结论。
- 主报告正文只保留较稳妥表述。
- 仅在该冲突会影响关键判断时，简短写入对应章节的“待进一步确认”表达。

### 2.5 去重原则

- 一个事实只应有一个主归属章节。
- 行业共性内容归 `行业环境与客户位置`。
- 客户上下游、渠道、生态、关键依赖归 `产业链与生态关系`。
- 明确发生过的合作、招投标、供应商、竞品、内部接触归 `合作历史与供应商关系`。
- 集团、股权、控制、分支、对外投资等关系优先归 `集团、股权与组织关系`，不因专题 Skill 提到就重复展开。

## 3. 调用决策总表

在客户尽调报告、客户情报报告、客户背景报告、客户详情页报告场景下，三个专题 Skill 默认都要调用。下表中的“何时可不调用”只适用于用户明确要求窄范围报告、专题 Skill 不可用、目标主体无法支撑判断，或该专题与当前问题无关的情况；不得把“按需”理解为可随意省略。

| 专题 Skill | 何时调用 | 何时可不调用 | 主报告最小消费结果 |
|:---|:---|:---|:---|
| `account-industry-analysis` | 客户尽调正式报告默认调用；用于解释行业趋势、政策、竞争格局、行业痛点、客户行业位置 | 用户明确只关心主体、CRM 历史或风险，且行业因素对问题影响弱；或专题 Skill 不可用 | `summary`、`customerPosition`、`judgments`、`businessImplications`、`evidence` |
| `account-chain-analysis` | 客户尽调正式报告默认调用；用于解释客户卖给谁、依赖谁、处于什么链位、渠道/生态/集团关系如何影响理解 | 用户明确只关心主体、单点风险或内部记录，且上下游/渠道/依赖与问题无关；或专题 Skill 不可用 | `chainPosition`、`relations`、`keyDependencies`、`businessImplications`、`evidence` |
| `account-cooperation-history` | 客户尽调正式报告默认调用；用于解释公开合作、招投标、供应商、竞品、内部历史接触、进入壁垒或合作偏好 | 用户明确只关心主体或单点风险，且合作历史与问题无关；或专题 Skill 不可用 | `summary`、`cooperationItems`、`internalHistory`、`supplierAndCompetitorSignals`、`businessImplications`、`evidence` |

## 4. 编排调用模式统一要求

调用专题 Skill 时，主报告默认要求其返回以下类型的结果：

- `summary`
  对该主题的客户相关摘要，不是完整报告导语。
- `judgments` / `relations` / `cooperationItems`
  该主题下可直接消费的结构化判断或事实列表。
- `businessImplications`
  这些事实对客户理解、经营判断、需求判断、风险判断的影响。
- `evidence`
  支撑关键结论的证据列表。
- `gaps`
  只有确实影响关键判断的待核实事项。

### 4.1 最小执行门槛

主报告编排专题 Skill 时，不能只读取专题 `SKILL.md` 后基于主报告已采集数据直接推断。`read_skill` 只代表读取入口定义，不等于完成专题 Skill 执行。

每个专题 Skill 在编排调用模式下，至少必须完成：

1. 读取专题 `SKILL.md`，确认触发边界、Core Rules 和 Workflow。
2. 读取专题 `references/00-workflow.md`，按编排调用路径执行关键步骤。
3. 读取专题 `references/output-contract.md`，确认编排消费契约和禁止输出边界。
4. 读取专题 `references/enterprise-cli-map.md`，确认该专题应优先调用和可复用的 `company / market / listed` CLI。
5. 读取专题 `references/schemas/insight-data-model.md`，按结构化字段返回结果。
6. 按专题需要读取必要判断规则或模板路由文件，例如行业模板、链位判断、合作事件分类、外部数据规则等。

编排调用可以保持轻量：不要求专题生成完整独立报告、HTML 模板、长篇行业模板或全部 reference；但只要专题结论涉及企业情报、公开动态、招投标、合作事件、上市公告或外部证据，必须读取专题自己的 `enterprise-cli-map.md`。已由主报告取得且字段足够的数据可以复用；字段不足时按专题 CLI map 补查；web search / web fetch 只能作为 CLI 不可用、返回空、字段不足、需要权威公开原文补证或用户明确要求时的后置手段。

`minimumReferenceSet`：

| 专题 Skill | 必读 reference 集 |
|:---|:---|
| `account-industry-analysis` | `references/00-workflow.md`；`references/output-contract.md`；`references/enterprise-cli-map.md`；`references/schemas/insight-data-model.md`；`references/industry-judgment-criteria.md`；`references/industry-templates/_router.md`；按 `_router.md` 命中的行业模板 |
| `account-chain-analysis` | `references/00-workflow.md`；`references/output-contract.md`；`references/enterprise-cli-map.md`；`references/schemas/insight-data-model.md`；`references/chain-structure.md`；`references/chain-position.md`；`references/relations.md`；`references/external-data-rules.md` |
| `account-cooperation-history` | `references/00-workflow.md`；`references/output-contract.md`；`references/enterprise-cli-map.md`；`references/schemas/insight-data-model.md`；`references/cooperation-types.md`；`references/bidding-merge-rules.md`；`references/external-sources.md`；`references/crm-context.md` |

读取状态必须写入 `topicInsights.<topic>.referenceReadStatus`：

```jsonc
{
  "status": "complete | partial | failed | not_applicable",
  "required": [],
  "read": [],
  "missing": [],
  "downgradeReason": ""
}
```

状态判定：

- `complete`：该专题 `SKILL.md` 与 `minimumReferenceSet` 中适用文件均已读取，并按编排消费契约返回结果。
- `partial`：已读取专题 `SKILL.md`，但存在必读 reference 未读取、命中模板未读取、或 workflow 未完整执行。
- `failed`：专题不可用、关键 reference 缺失、工具失败，无法形成可消费结果。
- `not_applicable`：该专题按允许跳过规则未调用，并已记录原因。

只读取专题 `SKILL.md` 时，必须视为 `partial`，不能把主报告已有资料整理成“专题 Skill 已完整执行”。

如果因为权限、工具或上下文限制无法完整执行专题 workflow，必须在 `topicInsights.<topic>.loadStatus`、`gaps` 或 `meta.retrievalCoverage` 中记录降级原因；不得把“主报告数据已经丰富”当作跳过专题 workflow 的理由。

统一处理要求：

- 专题 Skill 在编排调用模式下返回的结构化结果，先保留到 `topicInsights` 中对应主题下。
- 主报告正式渲染前，再把 `topicInsights` 归并到 `industryContext`、`chainContext`、`cooperationContext` 等消费字段。
- `summary` 可以进入主报告章节开头，也可以折叠进概览摘要，但不得原样复制整段专题分析文字。
- `businessImplications` 只有在与客户理解或与发问方相关性直接有关时才进入正文。
- `evidence` 必须进入主报告顶层 `evidence` 列表；必要时再写入对应子结构的 `evidenceRefs`。
- `gaps` 不单独形成固定章节；只有用户明确关注、或该缺口影响关键判断时，才在对应章节简短表达。

## 5. 行业分析 Skill 消费规则

### 5.1 调用条件

满足以下任一条件即可调用：

- 需要解释客户所属行业、赛道或客户行业位置。
- 行业趋势、政策、监管或竞争格局会影响客户当前业务重点。
- 主报告需要说明“为什么这个客户当前会出现这些经营动态或需求信号”。

### 5.2 只消费的字段

- `summary`
- `industryStage`
- `customerPosition`
- `judgments`
- `businessImplications`
- `evidence`
- `gaps`

### 5.3 写入主报告数据模型

| 专题 Skill 字段 | 写入位置 | 处理方式 |
|:---|:---|:---|
| `summary` | `topicInsights.industry.summary` + `industryContext.summary` | 作为第 5 章开头摘要；必要时压缩后写入概览摘要“客户是谁 / 当前业务重点” |
| `industryStage` | `topicInsights.industry.industryStage` + `industryContext.industryStage` | 记录行业阶段；阶段依据写入 `industryContext.industryStageBasis` |
| `customerPosition` | `industryContext.customerPosition` | 直接写入 |
| `judgments` | `industryContext.trends` / `industryContext.policies` / `industryContext.majorPlayers` / `industryContext.commonPainPoints` | 按判断类型拆分，不整段塞进一个字段 |
| `businessImplications` | `industryContext.businessImplications` + `operationDynamics` 或 `sellerRelevantSignals` | 行业影响先写入行业上下文；只有与客户当前变化或与发问方相关性直接有关时再写入动态或相关信号 |
| `evidence` | 顶层 `evidence` + `industryContext.evidenceRefs` | 主报告保留关键证据，不要求保留专题 Skill 返回的全部证据 |
| `gaps` | `industryContext.gaps` | 仅保留影响关键判断的缺口；正文中按需表达 |

### 5.4 写入主报告章节

- 主要进入第 5 章 `行业环境与客户位置`。
- 与客户近期动作强相关的判断，可进入第 7 章 `经营动态与业务重点`。
- 与发问方业务相关的行业信号，可进入第 11 章 `与发问方业务相关的情报信号`。

### 5.5 不消费的内容

- 完整行业研究框架。
- 市场容量、份额、宏观综述等与客户无直接关系的铺陈。
- 独立行业报告中的完整模板结构。

## 6. 产业链分析 Skill 消费规则

### 6.1 调用条件

满足以下任一条件即可调用：

- 需要解释客户卖给谁、依赖谁、由谁供给。
- 需要识别上下游、渠道、生态、平台、服务商、集成商等关系。
- 需要判断关键依赖、集团/资本关系对客户经营或采购归口的影响。

### 6.2 只消费的字段

- `chainPosition`
- `summary`
- `relations`
- `groupCapital`
- `keyDependencies`
- `businessImplications`
- `evidence`
- `gaps`

### 6.3 写入主报告数据模型

| 专题 Skill 字段 | 写入位置 | 处理方式 |
|:---|:---|:---|
| `chainPosition` | `chainContext.chainPosition` | 直接写入 |
| `summary` | `topicInsights.chain.summary` + `chainContext.summary` | 作为第 6 章章节导语 |
| `relations` | `chainContext.upstream` / `chainContext.downstream` / `chainContext.channels` / `chainContext.ecosystem` | 按关系类型拆分 |
| `groupCapital` | `chainContext.groupCapitalRelations` + `ownership.relatedCompanies` / `ownership.investments` / `ownership.businessImplications` | 只有影响控制、采购、区域覆盖、组织复杂度时写入；不重复写成合作事件 |
| `keyDependencies` | `chainContext.keyDependencies` | 直接写入 |
| `businessImplications` | `chainContext.businessImplications` + `sellerRelevantSignals` | 客户经营含义写前者；与发问方相关的信号写后者 |
| `evidence` | 顶层 `evidence` + `chainContext.evidenceRefs` | 主报告保留关键证据，不要求保留专题 Skill 返回的全部证据 |
| `gaps` | `chainContext.gaps` | 仅保留会改变链位、依赖或关系判断的缺口 |

### 6.4 写入主报告章节

- 主要进入第 6 章 `产业链与生态关系`。
- 涉及集团控制、采购归口、区域独立经营的内容，可补入第 3 章 `集团、股权与组织关系`。
- 涉及与发问方业务相关的关系信号，可进入第 11 章。

### 6.5 不消费的内容

- 候选客户池。
- 二跳扩展。
- CRM 查重。
- P0/P1/P2 定档。
- 线索创建、客户挂接、销售动作建议。

## 7. 合作历史 Skill 消费规则

### 7.1 调用条件

满足以下任一条件即可调用：

- 需要解释公开合作、供应商、竞品、招投标或项目参与关系。
- 需要判断客户是否存在长期供应商、竞品占位、合作偏好、进入壁垒。
- 需要读取 CRM 历史接触、历史商机、历史合同/订单/活动对当前判断的影响。

### 7.2 只消费的字段

- `summary`
- `cooperationItems`
- `supplierAndCompetitorSignals`
- `internalHistory`
- `businessImplications`
- `evidence`
- `gaps`

### 7.3 写入主报告数据模型

| 专题 Skill 字段 | 写入位置 | 处理方式 |
|:---|:---|:---|
| `summary` | `topicInsights.cooperation.summary` + `cooperationContext.summary` | 作为合作历史章节导语；必要时压缩后进入概览摘要 |
| `cooperationItems` | `cooperationHistory[]` | 每条合作事项按时间、对象、角色、类型、内容、业务含义写入 |
| `supplierAndCompetitorSignals` | `cooperationContext.supplierAndCompetitorSignals` + `cooperationHistory[]` + `sellerRelevantSignals` | 明确合作/占位事实进入合作历史；与发问方相关的关系信号进入相关信号 |
| `internalHistory` | `cooperationContext.internalHistory` + `crmContext.activities` / `crmContext.opportunities` / `crmContext.contracts` / `crmContext.orders` / `crmContext.payments` | 以主报告直接查到的 CRM 记录为准；专题 Skill 结果只做整理和解释，不覆盖原始记录 |
| `businessImplications` | `cooperationContext.businessImplications` + `cooperationHistory[].businessImplication` + `sellerRelevantSignals` | 只保留对客户理解、进入壁垒、替换难度、合作窗口有价值的含义 |
| `evidence` | 顶层 `evidence` + `cooperationContext.evidenceRefs` + `cooperationHistory[].evidenceRefs` | 有明确合作事件时优先挂到对应合作项 |
| `gaps` | `cooperationContext.gaps` | 只有影响长期供应商、竞品占位或关键合作判断时表达 |

### 7.4 写入主报告章节

- 主要进入第 9 章 `合作历史与供应商关系`。
- 涉及近期招投标、中标、战略合作、项目建设等动态时，可补入第 7 章 `经营动态与业务重点`。
- 与发问方相关的合作机会、壁垒、竞品信号，可进入第 11 章。

### 7.5 不消费的内容

- 投标推进方案。
- CRM 动作建议。
- 新建商机、线索、联系人建议。
- 触达路径、销售话术、跟进节奏、作战计划。

## 8. 章节归属优先级

同一事实可能同时被多个专题 Skill 提到时，按以下规则定归属：

1. 行业趋势、政策、行业痛点：
   只放第 5 章。
2. 客户链位、上下游、渠道、生态、依赖：
   只放第 6 章。
3. 明确发生过的合作、招投标、供应商、竞品、历史接触：
   只放第 9 章。
4. 集团、股权、控制、分支、对外投资：
   优先放第 3 章。
5. 近期变化、扩张、项目建设、公开中标、战略合作：
   先判断是否构成“当前业务重点”，成立时可放第 7 章，但不重复展开其关系细节。
6. 与发问方相关的机会/风险/关系信号：
   统一收敛到第 11 章，不重复复述基础事实。

## 9. 专题 Skill 结果为空或不充分时的处理

- 客户尽调正式报告中，某个专题 Skill 未调用必须有明确原因；原因写入 `topicInsights.<topic>.loadStatus`、`gaps` 或 `meta.retrievalCoverage`。
- 某个专题 Skill 调用后结果为空，不得自动推导为“该领域不存在事实”。
- 某个专题 Skill 结果证据不足时，主报告可以降级为只写主报告直接获取到的事实，不强行输出主题判断。
- 不因专题 Skill 结果为空而固定输出“暂无行业分析 / 暂无合作历史 / 暂无产业链信息”。

## 10. 给专题 Skill 的调用口径

主报告调用专题 Skill 时，应明确要求：

- 只围绕目标客户输出。
- 返回编排调用模式字段，不返回完整独立模板。
- 事实、推断、待核实分开。
- 每个判断尽量附关键证据。
- 不输出动作建议、话术、节奏、资源投入建议。

## 11. 当前与后续的衔接

- 本文件先把“编排消费契约”定稳。
- `report-data-model.md` 已为编排调用结果提供 `topicInsights`，并为主报告消费提供 `industryContext`、`chainContext`、`cooperationContext`。
- 后续补三个专题 Skill 自身的 schema 时，应与本文件的编排消费字段保持兼容，不反向扩大主报告消费边界。
