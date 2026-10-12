# 客户产业链分析输出契约

本文定义 `account-chain-analysis` 的独立输出模板和编排调用时的消费契约。HTML 展示形态由 `references/html-report-template.md` 定义，本文件只约束输出结构、字段消费和裁剪边界。

独立输出前，必须先形成 `references/schemas/standalone-report-data-model.md` 中定义的结构化数据；本文件只负责把该数据模型映射成结构化章节，HTML 展示规则另见 `references/html-report-template.md`。

`output-contract.md` 不能替代 `html-report-template.md`。需要 HTML 时，必须先读取并遵守 `references/html-report-template.md`，再渲染 HTML；未读取 HTML 模板时不得生成正式 HTML，也不得宣称 HTML 自检通过。

独立调用专题 skill 时，默认交付方式为：先输出文字业务概要结论，同时交付一份 HTML 产业链分析结果作为正式完整结果。若用户未明确要求完整 Markdown/文字长文，不强制再生成整份 Markdown 报告。

## 输出原则

- 只输出与目标客户相关的产业链内容。
- 先解释客户产业链位置，再展开关系事实。
- 每段都要落到“这对这个客户意味着什么”。
- 没有获取到的信息不强行输出。
- 不固定输出证据缺口或待核实事项。
- 不展示卖方画像原文。
- 不输出拓客动作、触达路径、销售话术、跟进节奏或作战计划。
- 事实、推断、待核实必须分开表达。

## 1. 独立输出模板

```markdown
# 客户产业链分析：<客户名称>

## 1. 产业链情报结论
- 客户产业链位置：
- 一句话结论：
- 主体锚定来源：
- 结构判断口径：

## 2. 客户产业链位置
- 所处环节：
- 价值角色：
- 主营业务与目标客户：
- 业务含义：

## 3. 上游、下游、渠道与生态关系
| 关系类型 | 关系对象 | 关系性质 | 业务含义 | 证据 |
|:---|:---|:---|:---|:---|

## 4. 集团 / 资本关系
| 关系类型 | 关系对象 | 关系性质 | 业务含义 | 证据 |
|:---|:---|:---|:---|:---|

## 5. 关键依赖与业务含义
| 依赖类型 | 依赖事实 | 对客户的影响 | 证据 |
|:---|:---|:---|:---|

## 6. 与发问方业务相关的产业链信号
| 信号类型 | 客户事实 | 为什么相关 | 判断 |
|:---|:---|:---|:---|

## 7. 待核实事项
- 

## 8. 证据来源
| 编号 | 来源名称 | 时间 | 支撑内容 |
|:---|:---|:---|:---|
```

## 2. 独立输出写法要求

- `产业链情报结论` 只放已获取到的核心信息。
- `客户产业链位置` 解释价值角色，不只写上游/中游/下游。
- `上游、下游、渠道与生态关系` 只保留与客户相关的关系，不展开候选池。
- `上游、下游、渠道与生态关系` 应优先输出具名代表企业或机构；没有具名证据时只写环节类型并标注推断/待核实，不伪造成确定关系。
- `集团 / 资本关系` 只解释与客户控制、区域覆盖、采购归口或组织复杂度有关的内容。
- `关键依赖与业务含义` 是正文核心，不是附录。
- `与发问方业务相关的产业链信号` 只输出客户侧信号，不展示卖方画像原文。
- 每个一级章节都应按“开头概述结论 -> 明细内容 -> 末尾业务含义总结”组织。
- 每个真实图表下方都必须附对应详细表格；Sankey、关系网络图、分层流向图下方的明细表应覆盖关系对象、关系类型、业务含义和证据来源。
- 链位、关键依赖、关系强弱、Sankey 布局值或上下游场景分组若来自模型归纳，必须在图例、表头、结论句或说明中明确保留归纳口径；不得伪装成原始交易规模、市场份额、真实流量或确定性供应链事实。
- 如项目关系、下游样本、公开合作或内部样本只消费首批结果，不得把首批样本写成全量关系网络、全量客户结构或整体产业链分布；应在表格、图例、章节结论或 coverage 说明中明确写明覆盖范围。
- CRM 快速检索未命中、仅返回模糊候选或客户主体未在 CRM 侧确认时，不得把内部覆盖、CRM 样本、渠道模式或组织复杂度写成已确认 CRM 事实；应明确降级或裁剪相关表达。
- 独立输出章节应优先消费 `chainContext`、`sellerRelevantSignals`、`gaps` 和 `evidence`，不要直接跳过数据模型即兴生成文本。
- 最终用户可见回复不得打印原始文件对象 JSON，例如 `{"type":"file","path":"..."}`；文件对象只能作为内部返回字段或由前端渲染为附件卡片。

## 3. 编排调用时的消费契约

编排调用模式必须按 `references/schemas/insight-data-model.md` 返回结构化结果。主报告只消费以下字段：

- `chainPosition`
  客户产业链位置。
- `summary`
  产业链摘要。
- `referenceReadStatus`
  专题 references 读取状态，写入主报告 `topicInsights.chain.referenceReadStatus`。
- `relations`
  上游、下游、渠道、生态关系摘要。
- `groupCapital`
  集团/资本关系摘要。
- `keyDependencies`
  关键依赖。
- `businessImplications`
  对客户经营、需求、风险和相关信号的影响。
- `evidence`
  关键证据列表。
- `gaps`
  待核实事项列表。

写入关系：

- 整体写入主报告 `topicInsights.chain`。
- `summary` 写入 `chainContext.summary`。
- `chainPosition` 写入 `chainContext.chainPosition`。
- `relations` 按类型拆入 `chainContext.upstream`、`chainContext.downstream`、`chainContext.channels`、`chainContext.ecosystem`。
- `groupCapital` 写入 `chainContext.groupCapitalRelations`，必要时同步到 `ownership.businessImplications`。
- `keyDependencies` 写入 `chainContext.keyDependencies`。
- `businessImplications` 写入 `chainContext.businessImplications`；与发问方相关的部分进入 `sellerRelevantSignals`。
- `evidence` 归并到主报告顶层 `evidence`，用 `evidenceRefs` 回链。

## 4. 不允许的输出

- 拓客对象清单。
- 二跳关系扩展。
- CRM 查重或去重驱动的结果。
- P0/P1/P2 定档。
- 创建线索、挂接客户、销售动作建议。
- 将代表企业清单作为 CRM 写入、拓客或销售动作依据。
