# 客户行业分析输出契约

本文定义 `account-industry-analysis` 的独立输出模板和编排调用时的消费契约。HTML 展示形态由 `references/html-report-template.md` 定义，本文件只约束输出结构、字段消费和裁剪边界。

`output-contract.md` 不能替代 `html-report-template.md`。需要 HTML 时，必须先读取并遵守 `references/html-report-template.md`，再渲染 HTML；未读取 HTML 模板时不得生成正式 HTML，也不得宣称 HTML 自检通过。

独立调用专题 skill 时，默认交付方式为：先输出文字业务概要结论，同时交付一份 HTML 行业分析结果作为正式完整结果。若用户未明确要求完整 Markdown/文字长文，不强制再生成整份 Markdown 报告。

## 输出原则

- 只输出与目标客户相关的行业内容。
- 先解释客户行业结论，再展开行业事实。
- 每段都要落到“这对这个客户意味着什么”。
- 没有获取到的信息不强行输出。
- 不固定输出证据缺口或待核实事项。
- 不展示卖方画像原文。
- 不输出销售动作、触达路径、销售话术、跟进节奏或作战计划。
- 事实、推断、待核实必须分开表达。

## 1. 独立输出模板

独立调用模式必须先形成 `references/schemas/standalone-report-data-model.md` 定义的数据模型。该模型沿用客户尽调主报告的数据模型骨架，Markdown 和 HTML 模板都只消费模型中的已有字段，不直接拼接原始 CLI 输出、网页文本或 CRM 记录。

```markdown
# 客户行业分析：<客户名称>

## 1. 行业情报结论
- 行业阶段：
- 对发问方是否值得做：
- 一句话结论：
- 行业锚定来源：
- 行业模板口径：

## 2. 客户行业位置
- 客户所在行业：
- 客户在行业中的位置/类型：
- 业务含义：

## 3. 行业变化对客户的影响
| 维度 | 行业变化 | 对客户的影响 | 证据 |
|:---|:---|:---|:---|

## 4. 行业背景摘要
- 行业趋势：
- 政策或监管变化：
- 竞争格局：
- 行业共性痛点：

## 5. 与发问方业务相关的行业信号
| 信号类型 | 客户事实 | 为什么相关 | 判断 |
|:---|:---|:---|:---|

## 6. 待核实事项
- 

## 7. 证据来源
| 编号 | 来源名称 | 时间 | 支撑内容 |
|:---|:---|:---|:---|
```

## 2. 独立输出写法要求

- `行业情报结论` 消费 `industryContext.summary`、`industryContext.industryStage`、`industryContext.industryStageBasis`、`industryContext.oneSentenceImplication`、`crmContext.industryAnchor`、`industryContext.templateContext`。
- 如存在“是否值得做”判断，必须消费卖方画像、客户行业事实和 `sellerRelevantSignals`；卖方画像不足时不得强行输出投入判断。
- `客户行业位置` 消费 `industryContext.customerPosition`。
- `行业变化对客户的影响` 消费 `industryContext.businessImplications`。
- `行业背景摘要` 消费 `industryContext.trends`、`industryContext.policies`、`industryContext.majorPlayers`、`industryContext.commonPainPoints` 和 `industryContext.trendAndEvents`。
- `与发问方业务相关的行业信号` 消费 `sellerRelevantSignals`。
- `待核实事项` 优先消费 `industryContext.gaps`，必要时合并顶层 `gaps`。
- `证据来源` 消费 `evidence`。
- `行业情报结论` 只放已获取到的核心信息。
- `客户行业位置` 解释客户在行业中的位置，不只写行业标签。
- `行业变化对客户的影响` 是正文核心，不是通用背景。
- `行业背景摘要` 只保留与客户相关的行业摘要，不写完整行业研究。
- `与发问方业务相关的行业信号` 只输出客户侧信号，不展示卖方画像原文。
- 每个一级章节都应按“开头概述结论 -> 明细内容 -> 末尾业务含义总结”组织。
- 每个真实图表下方都必须附对应详细表格；不得把详细表格仅作为 fallback 保留。
- 行业结论、客户行业位置、行业影响强弱、客户匹配度或机会强弱等判断若来自模型归纳，必须在图例、表头、结论句或说明中明确保留归纳口径；不得伪装成原始统计值、市场份额、客观评分或确定排名。
- 如新闻、行业事件、公开动态来源或内部样本只消费首批结果，不得把首批样本写成全量分布、全量竞争格局或全量趋势结论；应在表格、图例、章节结论或 coverage 说明中明确写明覆盖范围。
- CRM 快速检索未命中、仅返回模糊候选或行业锚定未经确认时，不得把内部样本、CRM 行业标签或客户行业位置写成已确认 CRM 事实；应明确降级为“行业未经 CRM 确认”或裁剪相关表达。
- “对发问方是否值得做”只能表达为 `值得重点关注`、`可验证后跟进`、`谨慎观察`、`暂不支持判断` 等情报判断，不输出资源投入计划、触达动作或销售节奏。
- `待核实事项` 只放确实无法确认且会影响理解的点。
- 最终用户可见回复不得打印原始文件对象 JSON，例如 `{"type":"file","path":"..."}`；文件对象只能作为内部返回字段或由前端渲染为附件卡片。

## 3. 编排调用时的消费契约

编排调用模式必须按 `references/schemas/insight-data-model.md` 返回结构化结果。主报告只消费以下字段：

- `summary`
  行业摘要。
- `referenceReadStatus`
  专题 references 读取状态，写入主报告 `topicInsights.industry.referenceReadStatus`。
- `industryStage`
  行业阶段。
- `customerPosition`
  客户行业位置。
- `judgments`
  关键行业判断列表。
- `businessImplications`
  对客户经营、需求、风险和相关信号的影响。
- `evidence`
  关键证据列表。
- `gaps`
  待核实事项列表。

写入关系：

- 整体写入主报告 `topicInsights.industry`。
- `summary` 写入 `industryContext.summary`。
- `industryStage` 写入 `industryContext.industryStage`。
- `customerPosition` 写入 `industryContext.customerPosition`。
- `judgments` 按类型拆入 `industryContext.trends`、`industryContext.policies`、`industryContext.majorPlayers`、`industryContext.commonPainPoints` 或 `industryContext.judgments`。
- `businessImplications` 写入 `industryContext.businessImplications`；与发问方相关的部分进入 `sellerRelevantSignals`。
- `evidence` 归并到主报告顶层 `evidence`，用 `evidenceRefs` 回链。

## 4. 不允许的输出

- 纯行业研究综述。
- 宏观市场容量分析。
- 与客户无关的行业铺陈。
- 具体触达动作。
- 销售话术。
- 跟进节奏。
- 资源投入建议。
- 脱离卖方画像的泛行业“值得/不值得”判断。
