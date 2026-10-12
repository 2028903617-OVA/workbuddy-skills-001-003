---
name: "sfa-opportunity-diagnosis"
description: "当用户需要对单个商机做诊断、画像、洞察、风险识别、赢单分析或下一步建议时使用。适用于“诊断这个商机”“下一步怎么跟”“风险在哪”“生成商机画像”“值不值得推进”“赢单策略是什么”等场景。不用于仅查询基础信息、仅做 knowhow 查询、只做会议总结，或处理客户 / 非商机对象。如需生成 HTML 报告，必须按流程保存诊断结果。"
apiName: "sfa_opportunity_diagnosis"
---
# sfa-opportunity-diagnosis

## Goal

对一个明确的商机（`NewOpportunityObj`）按统一框架输出可解释、可执行的诊断正文。

硬约束：
- 本 `SKILL.md` 定义对象边界、评分来源优先级、阶段前置、输出边界和 HTML 保存规则。
- `references/` 只提供查询、诊断标准、流程编排和输出模板，不得放宽主文件硬约束。
- 涉及商机金额、联系人、时间、预算等核心事实时，如果有冲突，必须以商机信息为准。

对象已明确是商机时优先使用本 skill，不回退通用入口。

### Success Criteria

- 已确认唯一商机对象，且对象类型为 `NewOpportunityObj`。
- 已确认可用的 `Scoring_Result`、`Opportunity_Data_Package`（复用或新查）和 `AI_Stage` 判断依据；优先使用 `get_profile_score`，无可用结果时回退到 `sfa-opportunity-score`。
- 已优先复用远端返回中的流程、诊断标准和输出模板；远端不可用时才降级到本地 `references/`。
- 输出为可追溯的 Markdown 诊断正文；如用户要求 HTML，则只能通过脚本渲染并在成功后保存诊断结果。
- 不自行评分、不调用 `sfa-biz-router`、不进行 `save_diagnosis` 之外的 CRM 写回。

## WhenToUse

**适合这些表达：**

- 帮我诊断这个商机
- 这个商机下一步怎么跟
- 这个商机的风险在哪里
- 给我一个商机画像
- 这个商机值不值得继续推进
- 这个商机的赢单策略是什么

**不适合这些表达：**

- 只想查询商机基础信息，不需要诊断 → 走 `data-read`
- 只做 knowhow 查询，不需要对象级判断 → 走通用知识检索能力
- 只做会议总结或文本润色 → 走对应总结 / 润色能力
- 对象不是商机，或对象类型无法确认 → 先完成对象识别；本 skill 不执行诊断
- 用户显式说“客户 / AccountObj / 诊断客户 / 客户画像 / 客户经营 / 客户当前状态” → 改用 `sfa-account-diagnosis`

**边界条件：**

- 仅给客户名称、公司名称或客户 ID，未明确指定商机或 `NewOpportunityObj` 时，不得自动升级为商机诊断。
- 商机名称无法定位到唯一记录时，必须展示候选或要求补充信息，不得凭猜测继续诊断。
- `Scoring_Result` 缺失、来源不明，或不能确认来自同一商机的 `get_profile_score` / `sfa-opportunity-score` 时，必须阻断并提示先完成商机评分。

## Supported Object

| Object_Type | 说明 | References_Bundle |
| --- | --- | --- |
| `NewOpportunityObj` | 商机 | `references/` |

本 skill 的本地兜底资料包括：
- `references/data-query.md`
- `references/flow.md`
- `references/global-diagnosis-criteria.md`
- `references/output_template.md`

## Inputs

| 输入 | 作用 | 必填 | 来源 / 缺失处理 |
|:---|:---|:---:|:---|
| `object_id` + `Object_Type=NewOpportunityObj` | 直接定位商机对象，也是数据查询脚本入参 | 是（与商机名称二选一） | 已给 `object_id` 时直接验证对象类型；若对象不是商机则停止。 |
| 商机名称 | 归一为唯一商机 ID | 是（与 `object_id` 二选一） | 仅给名称时按 `references/data-query.md` 第 1 节先查候选；未命中或多候选无法确认时阻断并要求用户补充。 |
| `Opportunity_Data_Package` | 由本 skill 调用 `scripts/query-diagnosis-data.py` 返回的商机数据包 | 否 | 若与当前唯一商机 ID 一致、`status=READY`、包含必要结构且 `queried_at` 距当前时间不超过 30 分钟，则直接复用，不重复查询。 |
| `Scoring_Result` | 评分、维度和评分依据，驱动全局诊断和风险识别 | 是 | 优先来自同一 `NewOpportunityObj` 的 `get_profile_score`；CLI 无可用结果时，来自 `sfa-opportunity-score` 对同一商机的输出。 |
| 业务补充事实 | 补充 CRM 中不可见但用户明确提供的事实 | 否 | 可用于辅助判断；不得覆盖 CRM 已查事实，不得替代评分或阶段判断。 |

### 信息不足处理

- 当前轮与历史上下文都没有 `object_id`、商机名称或可唯一映射的商机线索时，主动追问商机名称或 ID，最多 2 轮；仍未提供则提示“缺少商机标识，无法执行诊断”并终止。
- 只给商机名称但无法唯一定位时，展示候选并等待确认；没有候选时提示“未找到该商机”并终止。
- `Scoring_Result` 缺失、来源不明或与当前商机不一致时，不进入降级模式，直接阻断并提示先完成 `sfa-opportunity-score`。
- `Opportunity_Data_Package` 不可复用时，仅允许重查一次完整数据包，不得拆成多次手工查询补齐。

## ToolsList

| 用途 | 命令 | 关键参数 |
| --- | --- | --- |
| 远端业务洞察文档 | `sharecrm sales profile fast-query-document --data '{"scene":"business_insight","coreTopics":"<检索主题>"}'` | `scene` 固定为 `business_insight`；`coreTopics` 使用“商机诊断流程 / 商机诊断标准 / 商机诊断输出模板”及可选 `<SELLER_INDUSTRY>` 拼接值。 |
| 按名称定位商机 | `sharecrm data record query-id-by-name --data '{"query":"<商机名称>","apiNames":["NewOpportunityObj"]}'` | `query` 为商机名称；`apiNames` 固定为 `["NewOpportunityObj"]`。 |
| 名称模糊兜底定位 | `sharecrm data record query-by-fields --object_api_name NewOpportunityObj --select_fields "_id,name,account_id" --name-like "<关键词>" --limit 10 --sort last_modified_time:desc --raw` | `name-like` 为关键词；用于展示候选，不直接生成诊断。 |
| 查询诊断数据包 | `python scripts/query-diagnosis-data.py --opportunity-id "<opportunity_id>" --pretty` | `opportunity_id` 为已确认的唯一商机 ID；仅在数据包不可复用时调用一次。 |
| 查询商机评分 | `sharecrm sales profile get_profile_score --objectApiName NewOpportunityObj --objectId <opportunity_id>` | `objectApiName` 固定为 `NewOpportunityObj`；`objectId` 为已确认的唯一商机 ID。优先消费非空返回中的综合得分、评级、维度名称、维度得分和评分依据。 |
| 渲染 HTML 诊断 | `python scripts/build-html-report.py --markdown "$DIAGNOSIS_MARKDOWN" --output "tmp/<商机名称>_<当前日期>.html"` | `$DIAGNOSIS_MARKDOWN` 必须是完整诊断 Markdown；`<当前日期>` 为 `YYYY-MM-DD`。 |
| 保存诊断结果 | `sharecrm sales profile save_diagnosis --objectApiName NewOpportunityObj --objectId <商机id> --score "<评分>" --summary <npath> --insightRating "<评级>"` | `--summary` 必须是 `render_content` 返回的 npath，不能是本地路径或 HTML 文本。 |

## Workflow

1. 确认对象并验证 `Object_Type=NewOpportunityObj`。定位优先级：①已给 `object_id` 直接验证；②只给名称则按 `references/data-query.md` 第 1 节归一为唯一 ID；③无 ID 无名称则按“信息不足处理”追问并最终阻断；④定位结果非商机则停止并提示改用对应对象诊断 skill。若用户原话显式指定“客户 / AccountObj”，必须停止本 skill 并提示改用 `sfa-account-diagnosis`，不得继续查询或诊断该客户下的关联商机。
2. 确认唯一商机 ID 后，优先按 `references/data-query.md` 第 2 节复用当前上下文中同一商机且未过期的 `Opportunity_Data_Package`。只有上下文不存在、`opportunity_id` 不一致、`status` 非 `READY`、缺少 `queried_at` / `data` / `seller_context` 等必要结构、`queried_at` 距当前时间超过 30 分钟，或用户明确要求最新数据 / 重新查询时，才调用 ToolsList「查询诊断数据包」，一次性查询商机主数据、关联客户、报价单、报价明细、商机联系人、联系人关系、竞争对手明细、销售记录和卖方行业配置。
3. 从数据包返回的 `seller_context.seller_industry` 读取 `SELLER_INDUSTRY`；为空时不拼接行业，并在输出标注“缺少卖方行业信息”。
4. 取买方行业 `BUYER_INDUSTRY`：优先从关联客户（`AccountObj`）的 `industry_level1`、`industry_level2` 提取；两者为空时，只能使用数据包中明确存在的其他行业字段。用于需要买方行业上下文的诊断判断和行动建议。
5. 使用 ToolsList「查询商机评分」执行 `sharecrm sales profile get_profile_score --objectApiName NewOpportunityObj --objectId <商机id>`。若返回对象与当前商机一致，且结果非空并包含可用评分信息（综合得分、评级或至少一个维度），将返回的综合得分、评级、维度名称、维度得分和评分依据原样作为 `Scoring_Result`，不调用 `sfa-opportunity-score`。若 CLI 调用失败、返回空结果、未包含任何评分信息或无法确认对象一致，则调用 `sfa-opportunity-score` 为当前同一商机评分，并将其输出作为 `Scoring_Result`；仅当该 fallback 也无法得到可用评分时才阻断。全局诊断必须记录评分来源为“CLI”或“sfa-opportunity-score 回退”。随后直接基于 `Opportunity_Data_Package` 生成 `AI_Stage`，不得调用、引用或要求调用 `sfa-biz-router`：
   - 先读取 `data.opportunity_full` 的 `sales_stage` 和 `sales_status`，保留 API 值与显示值作为系统锚点；字段缺失时如实标注缺失。
   - 再按时间由近到远读取 `data.active_records`，并结合 `data.quotes`、联系人及联系人关系中的已发生或客户明确承诺判断真实推进信号。仅我方发送材料、内部准备方案或创建报价，不得单独作为客户推进到下一阶段的证据。
   - 真实推进信号按由浅至深判断：需求 / 范围已确认；方案、技术评审或 POC 已由客户参与；预算、采购、招标、报价评审或商务谈判已由客户确认；法务、合同、审批、PO 或签约排期已由客户确认。不得因关键词孤立出现跨级推断。
   - 输出的 `AI_Stage` 必须包含：`系统阶段`（`sales_stage`）、`系统状态`（`sales_status`）、`AI判定阶段`、`阶段一致性`（仅可为“阶段锚点基本一致 / 阶段偏早 / 阶段偏晚 / 状态矛盾 / 信息不足”之一）和一句可追溯的判断说明。
   - 仅当系统阶段与已验证的真实推进信号可以明确比较时，才输出“阶段偏早”或“阶段偏晚”；系统阶段、状态与证据互相冲突时输出“状态矛盾”；销售记录为空、过期或没有客户侧推进证据时输出“信息不足”，并以系统阶段作为诊断的保守锚点。
6. 使用 ToolsList「远端业务洞察文档」读取 ShareCRM 远端商机诊断流程：`coreTopics="商机诊断流程,<SELLER_INDUSTRY>"`。保留返回的 `dataList` / `contentText`；后续步骤先检查并复用其中已包含的诊断标准或输出模板。远端执行失败、无结果、返回空内容或不可用时，读取 `references/flow.md` 作为本地兜底流程。
7. 生成全局诊断时，先检查第 6 步返回是否已包含诊断标准。若已包含，直接复用；若未包含，再使用 ToolsList「远端业务洞察文档」读取 `coreTopics="商机诊断标准,<SELLER_INDUSTRY>"`。若实际调用本步骤的远端诊断标准，保留该命令返回的 `dataList` / `contentText` 供下一步复用；远端执行失败、无结果、返回空内容或不可用时，读取 `references/global-diagnosis-criteria.md` 作为本地兜底诊断标准。按诊断流程加载所需 knowhow 与模板：
   - **概要**为摘要式，不拆“事实 / 判断 / 待确认问题”。
   - **全局诊断**严格使用所选 `Scoring_Result` 的维度名称及顺序作为主骨架：CLI 成功时使用 `get_profile_score` 返回维度；CLI 无可用结果时使用 `sfa-opportunity-score` 输出维度。不得补充、删除或改名；逐项结合维度分、评分依据与商机事实。评分只是暴露短板方向的线索，所有强判断必须解释“为什么”，并回到 CRM 事实、销售记录、联系人角色、报价 / 商务动作与评分依据交叉验证，不只复述分数。
   - **风险识别、赢单策略、行动建议**以评分为参考，结合商机、客户、销售记录、联系人、竞争对手明细等事实深入推理，继承全局诊断暴露的短板。
8. 先检查第 6、7 步已调用的 `fast-query-document` 返回内容是否包含诊断输出模板。若任一返回已包含，直接复用；若均未包含，再使用 ToolsList「远端业务洞察文档」读取 `coreTopics="商机诊断输出模板,<SELLER_INDUSTRY>"`。远端执行失败、无结果、返回空内容或不可用时，读取 `references/output_template.md` 作为本地兜底模板，并按模板要求输出 Markdown 格式的诊断。
9. 询问用户是否需要输出 HTML 诊断；若需要，按以下顺序串行执行，禁止跳步、并行或调整顺序，禁止模型直接拼接 HTML：
   1. 使用 ToolsList「渲染 HTML 诊断」把第 8 步产出的完整 Markdown 渲染为 `tmp/<商机名称>_<当前日期>.html`。脚本会校验 Markdown 结构，并从 `assets/output.html` 提取 `<style>` 作为唯一样式来源。脚本失败时立即停止，不得由模型补齐或重写 HTML。
   2. 将渲染成功的 HTML 文件通过 `render_content` 输出，由系统自动上传并返回 npath；必须从返回结果中提取 `path` 字段值作为唯一文件标识。
   3. 仅当已获得 HTML 文件的 npath 后，才允许使用 ToolsList「保存诊断结果」。`--summary` 必须是 npath，严禁传入本地文件路径、`file://` URL 或 HTML 文本内容。保存失败时必须向用户说明失败原因，不得声称已保存成功。
   4. 调用保存命令前，逐项自检：`--objectApiName=NewOpportunityObj`、`--objectId=<商机id>`、`--score=<综合得分数字字符串>`、`--summary=<npath>`、`--insightRating=<评级字母或数字>`。

### 回滚与重试

- 远端业务洞察文档查询（Workflow 第 6~8 步）失败时：不重试，直接降级到对应本地 `references/` 文件。
- 商机定位精确查询未命中时：转入 ToolsList「名称模糊兜底定位」；若命令执行错误可重试 1 次，仍失败则提示“无法定位该商机”并终止。
- 诊断数据包脚本（Workflow 第 2 步）返回 `ERROR` 时：仅重试 1 次；若仍失败则阻断诊断并说明查询失败。返回 `OPPORTUNITY_NOT_FOUND` 时不重试。
- HTML 渲染脚本（Workflow 第 9.1 步）失败时：不自动重试，不进入保存诊断结果步骤，直接向用户反馈渲染失败原因。
- 保存诊断结果（Workflow 第 9.3 步）失败时：不自动重试，向用户说明失败原因，并保留已生成的 Markdown / HTML 结果。

## Output

### 交付载体

以 Markdown 输出商机诊断正文。优先使用 Workflow 第 8 步复用或获取到的远端模板；远端模板不可用时使用 `references/output_template.md`。

### 交付方式

- 默认以 Markdown 直接在对话中展示诊断结果。
- 仅当用户明确要求 HTML 诊断时，才执行 Workflow 第 9 步生成 HTML、获取 npath，并在成功后保存诊断结果。

### 最小输出结构

1. 输入摘要：商机名称、`object_id`、对象类型、是否复用 `Opportunity_Data_Package`、评分结果来源与是否进入降级模式。
2. 概要：总体判断、当前推进状态、最主要风险与赢单可行性结论。
3. 核心诊断结论：`AI_Stage`、阶段一致性和一句可追溯说明。
4. 全局诊断结果：按评分维度逐项解释得分、证据和核心短板。
5. 关键卡点与风险暴露：明确 `P0 / P1 / P2` 风险及其事实依据。
6. 核心打法策略与行动建议：把关键短板转成赢单策略、下一步动作和待补证据。
7. 需求地图分析、竞争态势分析、决策链分析：按模板保留相关章节，不得缺省关键对象洞察。

### 验收标准

- 每个强判断都能追溯到评分依据、CRM 事实、销售记录、联系人 / 竞争 / 报价证据之一或其组合。
- `AI_Stage` 必须显式包含系统阶段、系统状态、AI 判定阶段、阶段一致性和判断说明。
- 使用远端模板时遵循其结构；使用本地兜底模板时至少满足本节最小输出结构。
- 用户要求 HTML 时，只有在渲染成功并拿到 npath 后才能执行保存诊断结果。

## Degraded Mode

进入降级须显式说明可信度影响并列出需补齐项。降级仅适用于评分不完整、商机数据不足、阶段证据不足或买方行业缺失；不适用于缺少 `Scoring_Result`。

- 仅有总分：标注解释性不足，只输出整体健康度概览，不按维度拆根因。
- 有维度分缺评分依据 / 特征原值：做方向性判断，标注解释性受限，不把低分当已证实事实。
- 商机数据不足：概要标注信息不足，允许输出信息缺口型风险。
- 阶段证据不足：`AI_Stage` 输出“信息不足”，保留系统阶段 / 状态原值；不得阻断诊断或把系统阶段直接写成真实阶段。
- `BUYER_INDUSTRY` 缺失：行动建议退化为卖方通用模板，不输出行业案例，并标注“缺少买方行业信息”。

评分不完整时，风险识别只能输出保守型或信息缺口型风险，不得输出高置信根因型风险。

## Boundaries

- 评分来源优先级固定为：先查询 `get_profile_score`，有可用结果即直接消费；仅在 CLI 调用失败、结果为空、无评分信息或对象不一致时调用 `sfa-opportunity-score` 回退评分。全局诊断维度必须使用所选评分来源返回的名称和顺序。`AI_Stage` 必须在本 skill 内根据商机数据包直接判断，不调用 `sfa-biz-router`。
- 只消费本目录商机 knowhow，不加载线索或客户 knowhow。
- `flow.md` / `output_template.md` / `global-diagnosis-criteria.md` / `data-query.md` 不得覆盖主文件硬约束。
- 报价金额、单价、折扣等敏感商务信息仅用于内部判断商务成熟度与竞争 / 预算风险，不在输出正文中逐条列示具体数值；如需引用，只做定性描述。
- HTML 报告生成成功后必须保存诊断结果；除执行流程指定的 `sharecrm sales profile save_diagnosis` 外，不做其他 CRM 写回。

## Forbidden Tools

本 skill 执行期间，以下工具绝对禁止使用。Agent 在工具选择阶段必须优先检查本清单，命中即阻断，不得以任何理由调用：

| 禁止工具 | 禁止原因 | 正确替代 |
|:---|:---|:---|
| `biz_object_memory` | 该工具写入对象通用 memory 字段，不是诊断专用通道，无法关联 npath、评分等诊断元数据 | `sharecrm sales profile save_diagnosis`（Workflow 第 9.3 步） |
| 任何形式的直接 CRM 写回（`data-add`、`data-edit`、`record update`、`record create` 等） | 本 skill 是只读诊断 skill，唯一允许的写操作是 Workflow 第 9.3 步的 `save_diagnosis` | 无。如需回写字段，应退出本 skill 使用对应工具 |

## Scripts And Assets

- `scripts/query-diagnosis-data.py`：Workflow 第 2 步唯一的数据包查询入口。调用方必须消费返回的 `status`、`errors`、`notes` 和完整 `data` 结构。
- `scripts/build-html-report.py`：Workflow 第 9 步唯一的 HTML 渲染入口。脚本失败时必须停止流水线，不得手工拼接 HTML 或继续保存诊断结果。
- `assets/output.html`：HTML 诊断的唯一样式来源，只允许提取 `<style>`，不得把模板中的示例数据当作诊断内容使用。

## References

- `references/data-query.md`
- `references/flow.md`
- `references/global-diagnosis-criteria.md`
- `references/output_template.md`

## Related Skills

| Skill | 关系 | 说明 |
| --- | --- | --- |
| `get_profile_score` | 首选评分来源 | 对同一商机返回非空且可用的评分信息时直接消费，其维度决定全局诊断维度。 |
| `sfa-opportunity-score` | 回退评分来源 | 仅在 `get_profile_score` 调用失败、结果为空、无评分信息或对象不一致时调用；其输出成为 `Scoring_Result`。 |
| `sfa-account-diagnosis` | 对象错配时改用 | 用户显式指定客户 / `AccountObj` 时，必须停止本 skill 并切换。 |
| `sfa-biz-router` | 明确禁止调用 | `AI_Stage` 必须在本 skill 内直接判断，不调用、不引用、也不要求调用该 skill。 |
