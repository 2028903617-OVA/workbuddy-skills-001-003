---
name: "sfa-opportunity-competitive-analysis"
description: "商机竞争分析专属 skill。为已明确属于 NewOpportunityObj 的 CRM 商机对象，基于竞品名单、产品能力、报价线索、关系覆盖、客户倾向、竞品动作和行业背景，执行 SFA/CRM 竞争分析、竞品对比、赢单路径设计和竞争风险监控；当请求已经明确是商机竞争分析、竞品对比、攻防策略或赢单路径时使用。"
apiName: "sfa_opportunity_competitive_analysis"
---
# 商机竞争分析（Opportunity Competitive Analysis）

## Goal

本 skill 只服务于 `NewOpportunityObj`，并只消费竞争分析相关资料与竞争证据。

当对象已经明确是商机，且任务属于竞争分析、竞品对比、竞争策略制定或竞争风险监控时，优先使用本 skill。

基于商机上下文、客户需求、方案差异、报价线索、关系覆盖、客户倾向、竞品动作和行业背景，识别关键竞争对手与竞争态势，分析我方与对手的优劣势、风险点和突破口，输出面向销售推进的竞争判断、攻防策略与赢单路径建议。

### 成功标准

- 已确认对象为 `NewOpportunityObj`，并完成商机事实、竞品事实和关键竞争证据的读取或缺失标注。
- 三件套完整性、五维竞争分析、竞对企业风险观察和赢单路径建议均基于 CRM 事实或用户明确补充事实。
- 信息不足处统一标注为 `待补充`、`无法判断` 或 `⚠️ 推断`，不得把缺失证据当成正向证据。
- 输出只覆盖竞争情报分析，不输出通用商机评分、完整商机诊断或 CRM 写回动作。

## WhenToUse

**适合这些表达：**

- 帮我分析这个项目的竞品情况
- 我们和竞品怎么对比
- 竞品报价或关系覆盖有什么风险
- 这个商机怎么设计赢单路径
- 帮我整理竞争情报和下一步动作
- 竞品现在压价 / 切高层 / 抢关系，该怎么应对

**不适合这些表达：**

- 只想查询或修改 CRM 字段 → 走 `data-read` 或 `data-edit`
- 只想做需求洞察、决策链诊断或首面准备 → 走 `sfa-needs-discovery`、`sfa-decision-chain-diagnosis` 或对应首访策略 skill
- 只想生成会议总结或润色话术 → 不触发本 skill
- 只想做通用商机评分或完整商机诊断 → 走 `sfa-opportunity-score` 或 `sfa-opportunity-diagnosis`
- 没有任何竞品、客户倾向、价格线索或竞争动作事实，且用户也不希望补充 → 不触发本 skill

**边界条件：**

- 只服务 `NewOpportunityObj`；若对象并非商机，不继续执行。
- 只输出竞争情报分析，不输出通用商机评分、完整商机诊断或 CRM 写回动作。
- 不得编造竞品名单、报价、折扣、客户倾向、关系覆盖、竞品动作或内部评价。
- 不得把 CRM 字段空值写成“没有竞品 / 没有风险 / 没有关系覆盖”。
- 竞争对手报价金额只用于内部判断，输出正文只做定性描述。
- 竞对企业风险只用于内部竞争分析和客户风险验证建议，不得输出诋毁性表述。
- 互联网搜索结果只能作为补充线索，需交叉验证。
- 如需 HTML 输出，必须通过 `scripts/build-html-report.py` 渲染，禁止模型直接拼接 HTML。

## Supported Object

| Object_Type | 说明 | References_Bundle |
| --- | --- | --- |
| `NewOpportunityObj` | 商机竞争情报分析 | `references/` |

本 skill 只读取以下本地竞争情报资料：

- `references/data-query.md`
- `references/diagnosis-criteria.md`
- `references/output-template.md`

## What I Need From You

### Required / 必需提供的信息

| 输入 | 作用 | 必填 |
|:---|:---|:---|
| `object_id` + `object_api_name=NewOpportunityObj` | 直接定位商机对象 | 是（与“商机名称 / 项目名称”二选一） |
| 商机名称 / 项目名称 | 通过名称归一为商机 ID | 是（与 `object_id` 二选一） |

### Optional / 可选提供的信息

| 输入 | 作用 | 必填 |
|:---|:---|:---|
| 客户名称 | 当未提供商机时，用于先定位 `AccountObj` 再反查关联商机 | 否 |
| 竞品事实 | 竞品名单、产品能力、报价线索、关系覆盖、客户倾向、竞品动作 | 否 |
| 我方事实 | 我方优势、短板、报价、交付、行业案例、关系覆盖 | 否 |
| 当前项目阶段 / 报告人 / 行业补充信息 | 用于补充竞争上下文，但不得替代 CRM 查询到的商机事实 | 否 |

### 信息不足处理

- 竞品名称、关键竞争动作或客户倾向完全缺失时，先简短反问，最多追问 2 轮；仍无法补齐时提示“竞争事实不足，无法完成可靠分析”并终止。
- 无法定位唯一商机时，必须展示候选列表并等待用户选择，不得自行猜测。
- 报价单 / 报价明细不可见或不存在时，不阻断分析，但价格 / 商务成本相关判断必须降级为 `待补充` 或 `无法判断`。
- 竞品关系覆盖 / 客户倾向证据稀疏时，保守评分，不得把缺失证据当成正向证据。
- `报告人` 无法确认时，输出 `待补充`。
- 行业背景不明确时，可简短确认；若仍无法确认，允许执行通用竞争情报分析，但限制行业特定推断。

## ToolsList

| 用途 | CLI 命令 | 关键参数 |
| --- | --- | --- |
| 按字段条件查询数据 | sharecrm data record query-by-fields --object_api_name <对象ApiName> --select_fields "<字段1>,<字段2>,..." --<字段>-eq <值> --<字段>-like <关键词> --limit <数量> --sort <字段>:desc\|asc --raw | `object_api_name` 为对象 API 名；`select_fields` 为字段列表；过滤条件根据业务场景替换。 |
| 按 ID 获取单条记录 | sharecrm data record get-by-id --data '{"object_api_name":"<对象ApiName>","id":"<记录ID>"}' --raw | `object_api_name` 为对象 API 名；`id` 为记录 ID。 |
| 获取对象字段描述 | sharecrm data describe get --data '{"object_api_name":"<对象ApiName>","simple_describe":true}' | `object_api_name` 为对象 API 名；字段不确定时先调用。 |
| 按名称查询记录 ID | sharecrm data record query-id-by-name --data '{"query":"<名称>","apiNames":["<对象ApiName>"]}' | `query` 为名称关键词；`apiNames` 为目标对象列表。 |
| 获取卖方配置 | sharecrm sales get-config-by-key --data '{"key":"<配置键>"}' | `key` 固定使用 `service_models` 获取卖方行业配置。 |
| 查询竞对企业风险 | sharecrm intelligence risk enterprise-risk --data '{"companyName":"<企业名称>","actionType":"<风险类型>"}' | `companyName` 为竞对公司名称；`actionType` 为企业风险类型。 |
| 互联网搜索 | sharecrm knowledge web-search --data '{"query":"<搜索关键词>"}' | `query` 为竞对公司与风险关键词组合。 |
| 获取远端诊断文档 | sharecrm sales profile fast-query-document --data '{"scene":"business_insight","coreTopics":"<主题>"}' | `scene` 固定为 `business_insight`；`coreTopics` 为竞争分析标准、模板或行业专题。 |

## Workflow

1. 确认用户意图属于 `竞争分析`，并验证 `Object_Type=NewOpportunityObj`；若对象不是商机，终止本 skill。
2. 读取 `references/data-query.md` 第 0-4 节，使用 ToolsList 中的数据查询能力确认卖方行业、唯一商机、商机主数据、关联客户和报价事实；只给客户名称时先定位 `AccountObj`，再反查关联商机。
3. 按 `references/data-query.md` 第 5-7 节查询联系人 / 关系覆盖线索、竞争对手明细和销售记录；涉及价格、折扣、压价、商务博弈时，第 4 节报价数据为必查项。
4. 能确认竞对公司实体时，按 `references/data-query.md` 第 8 节查询竞对企业风险，并用互联网搜索做补充验证；无法确认主体时标注 `竞对主体待确认`。
5. 读取 `references/diagnosis-criteria.md`，先判断竞争情报三件套完整性，再执行五维竞品量化分析和竞对企业风险观察；如用户明确要求补充最新远端 knowhow，可使用 ToolsList「获取远端诊断文档」补充，但本地 `references/diagnosis-criteria.md` 仍为稳定兜底。
6. 基于三件套、五维结果、企业风险观察、客户关注点和竞争证据，形成竞争态势、差异化定位、攻防策略、赢单路径和情报缺口计划。
7. 读取 `references/output-template.md` 并生成中文竞争情报结果；如用户明确要求 HTML 报告，再通过 `scripts/build-html-report.py` 从完整 Markdown 正文渲染 HTML 文件。
8. 信息不足处统一标注 `待补充` 或 `无法判断`；推断性判断标注 `⚠️ 推断`，并说明对结论可信度的影响。

### 回滚与重试

- 卖方配置、对象定位、主数据或关键关联数据查询失败时：重试 1 次，最多 2 次；仍失败则按阻断规则终止或按受影响维度降级分析。
- 报价、联系人关系、竞对明细、企业风险或互联网搜索失败时：不重试；标注对应证据不足，并仅对受影响维度降级。
- 远端诊断文档查询失败时：不重试，直接继续使用本地 `references/diagnosis-criteria.md` 或 `references/output-template.md`。
- HTML 渲染失败时：不重试，不输出 HTML，仅保留 Markdown 结果并说明脚本失败。

## Output

### Delivery Format

按 `references/output-template.md` 输出 Markdown 竞争情报分析结果。仅当用户明确要求 HTML 报告时，额外通过 `scripts/build-html-report.py` 生成 HTML 文件。

### Delivery Method

- 默认以 Markdown 直接在对话中展示竞争分析结果。
- 用户明确要求“导出”“保存”或“生成 HTML 报告”时，将 Markdown 或 HTML 结果写入当前工作目录，并返回生成文件路径。
- HTML 输出必须来自脚本渲染结果；脚本失败时不输出 HTML，也不由模型手工拼接。

### 最小输出结构

1. 输入摘要与证据完整性提示
2. 三件套收集状态
3. 五维竞品分析与竞争态势
4. 竞争对手画像
5. 竞对企业风险观察
6. 差异化定位
7. 攻防策略
8. 赢单路径
9. 情报缺口与补充计划

### 验收标准

- 九个最小输出结构必须齐全，且每一部分都要标明事实来源或缺失状态。
- 报价金额、折扣和敏感商务信息只做定性描述，不逐条列示具体数值，除非用户明确要求展示。
- 信息不足处必须标注 `待补充`、`无法判断` 或 `⚠️ 推断`，不得把缺失记录写成负面或正面结论。
- 使用 HTML 输出时，必须由 `scripts/build-html-report.py` 成功生成；失败时不得伪造 HTML 成果。

## Edge Cases

- 商机重名或匹配到多个候选：按 `references/data-query.md` 展示候选并等待用户确认，不得自行猜测。
- 只有客户名称、没有商机名称：先定位 `AccountObj`，再反查关联 `NewOpportunityObj`。
- CRM 中未记录竞品，但用户明确提供竞品事实：可继续分析，但必须标注竞品来源为用户补充。
- CRM 与用户输入冲突：优先列出冲突，不得直接覆盖；结论按证据可信度分层。
- 报价单、报价明细不可见或不存在：不阻断，但价格 / 商务成本相关判断必须降级为 `待补充` 或 `无法判断`。
- 竞品关系覆盖、客户倾向或竞品动作证据稀疏：保守分析，不得把缺失证据当成正向证据。
- `报告人` 无法从 CRM owner 或用户输入确认：输出 `待补充`。
- 远端诊断标准或输出模板不可用：使用本地 `references/` 作为兜底，不得中断到无规则状态。
- 行业背景不明确：可简短确认；若无法确认，仍可执行通用竞争情报分析，但需限制行业特定推断。

## Boundaries

- 只服务 `NewOpportunityObj`。
- 若对象并非商机，不继续执行本 skill。
- 只输出竞争情报分析，不输出通用商机评分、完整商机诊断或 CRM 写回动作。
- 不得编造竞品名单、报价、折扣、客户倾向、关系覆盖、竞品动作或内部评价。
- 不得把 CRM 字段空值、未查询到记录或销售未记录，写成“没有竞品 / 没有风险 / 没有关系覆盖”。
- 不得把职位头衔、厂商品牌或行业常识直接等同于实际竞争优势、客户倾向或赢单概率。
- 不得把未验证结论写成已确认事实；信息不足时必须标注 `待补充` / `无法判断` / `⚠️ 推断`。
- 竞争对手报价金额、折扣和敏感商务金额只用于内部判断竞争 / 预算风险；输出正文只做定性描述，不逐条列示具体数值，除非用户明确要求展示。
- 竞对企业风险只用于内部竞争分析、供应商稳定性观察和客户风险验证建议；不得输出诋毁性表述，不得把企业风险直接等同于产品能力、价格能力、关系能力或赢单概率。
- 互联网搜索结果只能作为补充线索；未经结构化风险、销售记录、客户反馈或用户输入交叉验证，不得写成确定事实。
- 不加载本 skill 目录外的行业场景资料。
- 不把诊断标准当作项目竞争事实输出。
- 如需 HTML 输出，必须通过 `scripts/build-html-report.py` 渲染，禁止模型直接拼接 HTML。

## References

- `references/data-query.md`
- `references/diagnosis-criteria.md`
- `references/output-template.md`

## Related Skills

- `sfa-needs-discovery`：客户需求、关注点和痛点不清晰时先补齐需求事实，再回到本 skill 做竞争分析。
- `sfa-decision-chain-diagnosis`：关系覆盖、支持度和关键人态度判断需要更系统的决策链证据时协同使用。
- `sfa-opportunity-score`：用户只想看商机评分或赢率评分时使用；本 skill 不输出评分结果。
- `sfa-opportunity-diagnosis`：用户需要完整商机诊断、风险归因或行动建议时使用；本 skill 只聚焦竞争情报分析。

## Scripts

- `scripts/build-html-report.py`：Workflow 第 7 步后可选 HTML 渲染入口。
  - 入参：`--markdown <markdown>`（第 7 步产出的完整 Markdown 原文）、`--input <path>`（兼容文件输入）、`--output <html>`（缺省写 stdout）、`--schema` 打印 Markdown 结构提示；未传 `--markdown/--input` 时从 stdin 读取。
  - 行为：先按 `references/output-template.md` 固定结构校验并解析 Markdown；再读取 `assets/output.html` 的 `<style>` 作为唯一样式来源；最后输出完整 HTML。若 Markdown 使用单竞品模式，脚本会按真实竞品名称渲染，并省略竞品 B 列。
  - 退出码：Markdown 结构校验失败、样式文件缺失均以退出码 1 终止；调用方必须在失败时停止流水线，不得手工拼接 HTML。
  - 输出的 HTML 名称建议为 `<商机名称>_竞争分析报告.html`，如有同名文件，按 `<商机名称>_竞争分析报告_1.html`、`<商机名称>_竞争分析报告_2.html` 递增。
