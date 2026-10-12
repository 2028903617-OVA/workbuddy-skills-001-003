---
name: "sfa-account-handover-briefing"
description: "当 AE 工作调动、客户转手、团队协作或接手人需要快速继承客户上下文时使用本技能，生成团队交接简报，重点输出交接背景、客户画像、博弈编年、关系温度、关键人地图、待兑现承诺、风险敏感点、竞品历史和接手建议。不要用于见客前行动简报、高层陪访/升级汇报、团队周报或泛客户360认知档案。"
apiName: "sfa_account_handover_briefing"
---
# 团队交接简报

## 技能元信息

- 参数提示：`[客户名称] [--full]`
- 版本：`1.0`
- 更新时间：`2026-07-15`

## 目标

为接手 AE 或团队成员生成一份能直接接手客户的交接档案。交接场景的核心不是“今天怎么见客户”，而是回答：

- 这个客户为什么要交接，当前处在什么状态？
- 过去发生过哪些关键博弈，哪些承诺还没有兑现？
- 客户里谁支持我们、谁阻碍我们、谁需要特别注意？
- 接手人第一周最容易踩什么坑？
- 竞品、交付、回款、客户健康上有没有历史包袱？

默认先在对话中直接输出结构化 Markdown 交接简报正文，再基于同一内容生成 HTML 展示版。Markdown 文件只是归档物，不能替代对话内正文；HTML 用于接手人移动端阅读、团队转发和会前预览，不改变事实、置信度、风险或接手建议。HTML 展示版和 `.md` 归档文件通过系统附件交付；不要在回复正文中输出“文件已生成”、文件名、文件路径或 Markdown/HTML 文件清单。

## 适用场景

使用本技能处理：

- `/handover [客户名称]`
- `/handover [客户名称] --full`
- “把这个客户交接给同事”
- “生成客户交接简报”
- “接手这个客户前需要知道什么”
- “AE 离职/调岗，帮我整理客户历史”

不要用于：

- 见客前 1 分钟行动简报。
- 高层陪访、领导汇报或升级汇报。
- 客户360日常认知档案。
- 团队周报、销售经理 review 或客户组合盘点。
- 接手后的年度/季度/月度客户经营计划；交给 `account-planning`。
- 接手后的存量扩张、增购或跨部门复制路径；交给 `customer-expansion`。
- 长周期项目激活、保温、降频或退出判断；交给 `long-cycle-mgmt`。
- 完整决策链诊断；交给 `decision-chain`。
- 深度需求穿透或竞品攻防；分别交给 `needs-discovery` 或 `competition-intel`。

本技能负责生成团队交接简报，可以汇总客户历史、关系、承诺、风险和接手建议，但不做接手后的深度经营诊断。用户要客户经营计划转 `account-planning`，要存量扩张转 `customer-expansion`，要长周期项目激活转 `long-cycle-mgmt`，要决策链诊断转 `decision-chain`，要需求或竞品诊断分别转 `needs-discovery` 或 `competition-intel`。

## 输出原则

- Memory 优先：交接价值主要来自 CRM 里没有的历史、关系、承诺和敏感点。
- 接手人视角：所有内容都要服务“接手后如何不踩坑、不断档”。
- 事实与建议分开：先写已确认事实，再写接手建议。
- 承诺必须诚实：我方未兑现、客户未兑现、口头承诺都要标注状态。
- 不输出见客前语言：不要写“今日目标”“P0/P1/P2”“确认出发”。
- 不用“关系良好，继续维护”这类空话，必须写具体人、具体背景、具体注意事项。

## 数据优先级

1. Memory：博弈历史、承诺兑现、关系变化、客户内部政治、历史争议。
2. CRM 基础对象：`AccountObj`、`NewOpportunityObj`、`ContactObj`、`ActiveRecordObj`。
3. 交接断档补查：`ActivityTodoObj`、`MethodologyTaskObj`，仅在待兑现承诺、会后动作、任务状态或交接断档会影响接手建议时查询。
4. 需求、问题和会议证据：`RequirementObj`、`ActivityQuestionObj`、`ScheduleObj`、`AIMeetingObj`、`AIMeetingChunkObj`，仅在需求、异议、会议结论或历史高层会影响交接风险时查询。
5. 合同、订单、回款、CSM 预警、流失原因：`--full` 或历史合作客户时使用；订单/回款优先使用 `SalesOrderObj`、`PaymentObj`。
6. References：行业基准、竞品参考、CRM 字段说明。
7. 外部情报：仅在用户要求，或交接连续性、风险敏感点、第一周核对事项明显依赖外部动态时使用。

以上对象 apiName 只用于内部查询、metadata plan、日志和技术参考。最终 Markdown、HTML、数据覆盖、参考来源和页脚必须使用中文业务口径，不向用户展示 `AccountObj`、`NewOpportunityObj`、字段 apiName 或 query plan。

## 用户可见数据来源口径

将内部对象映射为以下中文标签：

| 内部来源 | 用户可见标签 |
| --- | --- |
| `AccountObj` | 客户 |
| `NewOpportunityObj` | 商机 |
| `ContactObj` | 联系人 |
| `ActiveRecordObj` | 跟进记录 |
| `ActivityTodoObj`、`MethodologyTaskObj` | 待办/任务 |
| `RequirementObj`、`ActivityQuestionObj` | 需求/问题 |
| `ScheduleObj`、`AIMeetingObj`、`AIMeetingChunkObj` | 会议 |
| `CompetitiveLinesObj` | 竞品明细 |
| `ContractObj`、`SalesOrderObj`、`PaymentObj` | 合同/订单/回款 |
| Memory | 客户记忆 |
| 外部风险、新闻、招投标、工商等 CLI | 外部情报 |

## 处理流程

1. 识别客户。
   - 需要从 CRM 查询时，先读取 `references/shared/sharecrm_cli_min_loop.md`，再按需读取 `references/cli_reference.md`。
   - 按最少 loop 规则先形成内部 `query_plan`：本次要查的对象、字段、过滤条件、触发补查条件和停止条件。
   - 按 `references/cli_reference.md` 的多阶段流程识别客户主记录：先完整名称查询，再用 ID 候选召回、别名/关键词/核心词模糊召回和 `_id` 精确查询补充定位。
   - `query-by-name` 未命中只能写为“名称检索未命中”，不得直接判断“CRM 中没有客户”。
   - 用户输入不要求与 CRM 客户名完全一致；如“文易动纷享”应能通过核心词“易动纷享”定位到“易动纷享有限责任公司”这类唯一高置信候选。
   - 多个候选客户或只命中短词候选时，先让用户选择；用户提供截图、链接或客户 ID 时，优先按 `_id` 精确查询。

2. 检查 Memory。
   - 读取 `memory/customers/[客户名称]/` 下已有记忆。
   - 如果 Memory 为空或缺少关键博弈历史，内部记录状态；输出中不得展示 Memory 状态，改在交接缺口或第一周核对事项中写“关键历史与关系信息待补充”，并明确需要原负责人补齐的事实。
   - 只有创建或更新记忆结构时，读取 `memory/template.md`。

3. 拉取交接所需 CRM 数据。
   - 先读取 `references/shared/report_data_sources.md` 判断本次数据源；默认读取客户、商机、联系人、最近互动。
   - 先完成 metadata plan：只 describe 本次需要对象；同一对象本轮只 describe 一次，并只选择已确认字段，不猜字段 apiName、对象 apiName 或枚举值。
   - 再完成 identity plan：客户、商机、联系人、员工、部门等引用过滤必须先解析为 `_id`。
   - 待兑现承诺、会后动作、任务状态或交接断档不清时，查询 `ActivityTodoObj`、`MethodologyTaskObj`。
   - 需求、异议、客户问题或响应状态不清时，查询 `RequirementObj`、`ActivityQuestionObj`。
   - 会议结论、历史高层会或交接关键会议缺证据时，查询 `ScheduleObj`、`AIMeetingObj`、`AIMeetingChunkObj`。
   - 仅在商机、互动记录、Memory 或用户问题中出现竞品/竞争/输赢/替换/报价等信号时，才查询竞品明细；用户明确要求竞品历史时必须查询。
   - `--full` 或已成交/历史合作客户，再读取合同、订单、回款、CSM 预警、流失原因；订单/回款优先使用 `SalesOrderObj`、`PaymentObj`。
   - 字段含义不清时，读取 CRM 字段参考。
   - 按 `references/shared/crm_query_status.md` 记录每类数据状态：`已读取 / 无数据 / 权限不足 / 未触发查询 / 查询失败`。权限不足或不可恢复错误不等于无数据，不要重复查询同一对象。
   - 基础事实和 Memory 已足够支撑交接摘要、承诺台账、风险敏感点和第一周建议后停止补查；缺失项进入交接缺口和数据覆盖摘要，不为了完整感继续 loop。

4. 补充外部情报。
   - 只有用户要求，或外部动态会影响接手连续性、风险敏感点、第一周核对事项、采购窗口或历史包袱时，读取 `references/shared/external_intelligence_sources.md`。
   - 标准模式外部情报最多 2 次查询；`--full` 最多 3 次。
   - 优先使用 `risk conc` 或 `risk enterprise-risk`；明确发现破产、经营异常、行政处罚、重大税违等风险时再查明细。交接空窗期有重大动态时用 `market get-news`，采购窗口明显时用 `market bidding-pinganzhengxin`。
   - 外部情报只写入交接缺口、风险敏感点、第一周核对事项和接手建议，不覆盖 CRM/Memory 中的关系、承诺、互动、订单或回款事实。
   - 外部情报状态记录为：`已读取 / 无数据 / 权限不足 / 未触发查询 / 查询失败`。

5. 加载规则。
   - 目标规则集应为：
     - `rules/R01_handover_context.md`
     - `rules/R02_account_snapshot.md`
     - `rules/R03_game_timeline.md`
     - `rules/R04_relationship_map.md`
     - `rules/R05_commitment_ledger.md`
     - `rules/R06_risk_sensitive_points.md`
     - `rules/R08_handover_output.md`
     - `rules/R09_financial_health.md`
   - 仅在竞品明细已读取、Memory/互动/商机中存在竞品信号，或用户明确要求竞品历史时，加载 `rules/R07_competitive_history.md`。

6. 生成交接简报。
   - 标准模式先在对话中直接输出 Markdown 格式化交接简报正文，不包进代码块，不只提供 `.md` 文件或路径；内容包含接手人必读摘要、交接背景、客户画像、博弈编年、关系温度、待兑现承诺、风险敏感点、竞品历史、接手建议。
   - Markdown 正文完成后，读取 `references/shared/html_output_quality_gate.md`、`references/html_render_contract.md` 和 `rules/R08_handover_output.md`，把 Markdown 使用的同一组事实整理为 `handover_facts_bundle.json`。
   - 必须调用 `scripts/render_handover_briefing.py` 生成 HTML；不得手写整份 HTML、重新设计 DOM、分别生成桌面端和移动端事实，或把 `assets/templates/handover.html` 仅当作视觉参考。
   - 渲染器必须使用模板标识 `sfa-account-handover-briefing-v1`，自动内联 `assets/styles/handover.css`，并执行 `scripts/validate_handover_briefing.py`；校验失败时不得交付 HTML。
   - 视觉样式沿用 0703 的团队交接简报：顶部信息栏、卡片分区、分页标签和移动端单列。页签固定为“概览、历程与竞争、交接备注、数据质量”，数据质量单独承载数据覆盖、来源、置信度和数据截止，不在每个业务页签重复展示。移动端顶部使用内容驱动的自适应高度，长客户名、长商机状态和长交接判断必须自然换行，不能互相挤压；分页标签独立吸顶。Markdown 和 HTML 不得出现事实、人员、承诺、风险、接手建议、置信度或数据覆盖不一致。
   - 交接质量信号只展示“完整/部分/不足”“升温/稳定/降温”“高/中/低”等有证据的定性状态，不编造交接准备度百分制；关系温度仍可使用 R04 已定义的 `-5` 到 `+5` 口径。
   - 校验通过的 HTML 和 `.md` 归档文件通过系统附件交付；不要在回复正文中输出“文件已生成”、文件名、文件路径或 Markdown/HTML 文件清单。
   - `--full` 模式追加历史合作、合同订单、回款、客户健康和流失原因。

## 资源路由

- 需要判断本次该查哪些对象和触发补查条件时，读取 `references/shared/report_data_sources.md`。
- 需要从 CRM 拉取数据时，先读取 `references/shared/sharecrm_cli_min_loop.md`，再按需读取 `references/cli_reference.md`。
- 需要统一数据覆盖状态、权限不足和降级生成口径时，读取 `references/shared/crm_query_status.md`。
- 需要补充外部风险、新闻动态、招投标、破产、经营异常、行政处罚、重大税违或其他影响交接连续性的外部信息时，读取 `references/shared/external_intelligence_sources.md`。
- 生成 HTML 展示版前，读取 `references/shared/html_output_quality_gate.md` 和 `references/html_render_contract.md`。
- 需要解释 CRM 对象或字段时，读取 `references/crm_schema.md`。
- 需要行业背景、采购周期或常见风险假设时，读取 `references/industry_benchmarks.md`。
- 已知或疑似竞品时，读取 `references/competitive_reference.md`。
- 对话内 Markdown 正文完成后，必须调用 `scripts/render_handover_briefing.py`；该脚本使用 `assets/templates/handover.html`、内联 `assets/styles/handover.css` 并自动完成校验。
- Markdown 正文、`.md` 归档文件与 HTML 展开版是默认交付形态；Word、PDF 或其他文件格式必须由用户明确提出。
- 不从 `rules/` 加载 HTML 或 CSS；`rules/` 只放交接简报的分析和输出规则。HTML/CSS 只从 `assets/` 加载。

## 输出契约

以下契约描述 Markdown 交接简报结构。实际交付时必须在对话中直接渲染 Markdown 正文，不要把完整正文包进代码块；下面代码块仅用于说明结构。完成 Markdown 正文后必须生成同内容 HTML 展示版，HTML 只做展示层，不改变事实、置信度、风险或接手建议。

```markdown
# 客户交接简报 — {客户名称}

> 交接日期：{date}
> 原负责人：{原 AE/未知}
> 接手人：{接手 AE/未知}
> 数据更新时间：{date}
> 数据覆盖：客户 {已读取/无数据/权限不足/查询失败}；商机 {...}；联系人 {...}；跟进记录 {...}；待办/任务 {...}；需求/问题 {...}；会议 {...}；竞品明细 {已读取/无数据/权限不足/未触发查询/查询失败}；订单/回款 {仅 --full 或触发财务风险时展示状态}；外部情报 {已读取/无数据/权限不足/未触发查询/查询失败}。
> 置信度说明：确认 / 推断 / 未知

## 0. 接手人必读摘要
**一句话交接结论：** {客户当前状态 + 最大历史包袱 + 接手优先级}

| 摘要项 | 结论 | 置信度 |
| --- | --- | --- |
| 当前客户状态 |  | 确认/推断/未知 |
| 交接原因 |  |  |
| 最大风险 |  |  |
| 最关键关系 |  |  |
| 待兑现承诺 |  |  |
| 接手第一周重点 |  |  |

## 1. 交接背景
{为什么交接、当前商机/合作状态、交接紧急程度}

## 2. 客户画像
{客户基础信息、业务状态、历史合作情况}

## 3. 博弈编年
{关键事件、关系转折、承诺兑现/未兑现、客户态度变化}

## 4. 关系温度与关键人地图
{EB/TB/UX/Coach/Gatekeeper/Influencer、关系温度、联络注意事项}

## 5. 待兑现承诺
{我方承诺、客户承诺、截止时间、当前状态、接手处理建议}

## 6. 风险与敏感点
{客户内部政治、历史争议、交付/回款/服务风险、不能踩的坑}

## 7. 竞品历史
{历史竞品、当前竞品阶段、输赢原因、接手人需了解的竞争背景}

## 8. 接手建议
{第一周需要补齐的信息、建议联系顺序、需要原 AE 当面交代的问题}

## 9. 历史合作、财务与客户健康（仅 --full）
{合同、订单、回款、CSM 预警、流失原因、续约/增购信号}

> 📎 参考来源：CRM 客户/商机/联系人/跟进记录、原负责人交接信息、必要外部情报、订单/回款及行业/竞品参考。正文中的“推断/未知”仅用于交接准备，需接手后核对。
```

## 禁止行为

- 关键历史与关系信息不足时，不写入交接缺口就生成完整交接结论。
- 只罗列 CRM 字段，不写博弈历史、关系变化和承诺状态。
- 把未兑现承诺写成已完成。
- 输出见客前简报语言，如“今日目标”“P0/P1/P2”“确认出发”。
- 只交付 `.md` 文档、附件、文件卡片或本地导出文件，用文件路径替代对话内 Markdown 正文。
- 写“关系良好，继续维护”这类不可执行的空话。
- 用外部情报覆盖 CRM 或 Memory 已确认事实；外部信息冲突时必须写成接手后需核对事项。
- 新增外部情报独立章节、工商风险专区或新闻专区；外部风险只能写入交接缺口、风险敏感点或第一周核对事项。
- 隐瞒竞品、交付、回款、客户投诉或流失风险。
- CRM 权限不足时，不得写成“无商机/无联系人/无互动/无竞品”；必须标注“权限不足未读取”并降低相关结论置信度。
