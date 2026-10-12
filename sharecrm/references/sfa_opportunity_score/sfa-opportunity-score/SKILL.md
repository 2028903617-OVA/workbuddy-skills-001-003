---
name: "sfa-opportunity-score"
description: "当用户要求为商机打分、评估商机赢率、判断商机是否值得继续推进或输出商机评分明细时使用。不用于仅查询商机基础信息、输出诊断建议或处理非商机对象。"
apiName: "sfa_opportunity_score"
---
# sfa-opportunity-score

## Goal

为 `NewOpportunityObj` 提供独立评分流程：查询商机及关联业务事实，依据输入、远端或本地评分标准保守评分，并按适用模板输出结果。

### 成功标准

- 已确认商机对象、商机及关联业务事实，以及可用评分标准。
- 仅使用 CRM 或用户提供的事实评分；无法核实的事实保留为“缺失”或“待确认”。
- 选择用户评分表、远端标准或本地兜底标准中的一个可用标准完成评分。
- 评分过程不产生诊断、行动建议、阶段判断或 CRM 写回动作。

## WhenToUse

**适合这些表达：**

- 帮我给这个商机打分
- 看下这个商机的赢率评分
- 这个商机值不值得继续推进
- 输出这个商机的评分明细

**不适合这些表达：**

- 只想查询对象基础信息，不需要评分 → 走 `data-read`
- 需要输出诊断、风险、行动建议 → 走 `sfa-opportunity-diagnosis`
- 对象不是商机，或对象类型无法确认 → 先完成对象识别；本 skill 不执行评分

**边界条件：**

- 用户提供的商机名称在 CRM 中不存在 → 提示“未找到该商机”并终止，不执行评分。
- 用户评分表与本 skill 的评分标准不兼容 → 使用本 skill 的适用评分标准，并说明用户评分表格式不兼容。
- 对象类型已确认为非 `NewOpportunityObj` → 不触发本 skill，并引导至对应对象的 skill。

## Inputs

| 输入 | 作用 | 必填 |
|:---|:---|:---|
| `object_id` + `object_api_name=NewOpportunityObj` | 直接定位商机对象 | 是（与"商机名称"二选一） |
| 商机名称 + 可识别为商机的对象语义 | 通过名称归一为商机 ID | 是（与 `object_id` 二选一） |
| `Opportunity_Data_Package` | 已由 `sfa-opportunity-score` 或 `sfa-opportunity-diagnosis` 调用 `scripts/query-diagnosis-data.py` 返回的商机数据包 | 否 |
| 评分表 | 本次输入明确提供评分表时，作为本次评分标准 | 否 |
| 业务补充事实 | 可作为评分依据，但不得替代 CRM 查询到的商机事实 | 否 |

### 信息不足处理

- 用户既未提供 `object_id` 也未提供商机名称时，主动追问商机名称或 ID，最多 2 轮；仍未提供则提示“缺少商机标识，无法执行评分”并终止。
- 商机名称查询未命中时，展示候选商机并等待确认；无候选时提示“未找到该商机”并终止。

## ToolsList

| 用途 | CLI 命令 | 关键参数 |
| --- | --- | --- |
| 远端业务洞察文档 | sharecrm sales profile fast-query-document --data '{"scene":"business_insight","coreTopics":"<检索主题>"}' | `scene` 固定为 `business_insight`；`coreTopics` 为检索主题。 |
| 按名称定位商机 | sharecrm data record query-id-by-name --data '{"query":"<商机名称>","apiNames":["NewOpportunityObj"]}' | `query` 为商机名称；`apiNames` 固定为 `["NewOpportunityObj"]`。 |
| 名称归一化兜底查询 | sharecrm data record query-by-name --data '{"object_api_names":["NewOpportunityObj"],"name":"<商机名称或关键词>"}' | `object_api_names` 固定为 `["NewOpportunityObj"]`；`name` 为商机名称或关键词。 |
| 获取商机详情 | sharecrm data record get-by-id --object_api_name NewOpportunityObj --id <opportunity_id> | `object_api_name` 固定为 `NewOpportunityObj`；`id` 为商机记录 ID。 |
| 获取商机统一数据包 | python scripts/query-diagnosis-data.py --opportunity-id <opportunity_id> --pretty | `opportunity-id` 为已确认的商机 ID；仅在当前上下文没有可复用数据包时调用。 |

## Workflow

1. 确认对象并验证 `Object_Type=NewOpportunityObj`。有 ID 时使用 ToolsList「获取商机详情」验证；记录不存在或无权访问时提示“无法访问该商机记录”并终止。只有名称时先使用「按名称定位商机」，未命中再使用「名称归一化兜底查询」。多个候选时展示候选并等待用户确认；没有候选时提示“未找到该商机”并终止。
2. 使用 ToolsList「远端业务洞察文档」，设置 `scene="business_insight"`、`coreTopics="商机评分流程"`。保留返回的 `dataList` / `contentText`；后续步骤优先复用其中已有的评分标准或输出模板。远端调用失败、无结果、内容为空或不可用时继续使用本地流程。
3. 读取 `references/data-query.md`。确认唯一商机 ID 后，优先复用当前上下文中同一商机且未过期的 `Opportunity_Data_Package`。仅在上下文不存在、`opportunity_id` 不一致、`status` 非 `READY`、缺少 `queried_at` / `data` / `seller_context`、`queried_at` 距当前时间超过 30 分钟，或用户明确要求最新数据 / 重新查询时，使用 ToolsList「获取商机统一数据包」查询商机主数据、关联客户、报价单、报价明细、商机联系人、联系人关系、竞争对手明细、销售记录和卖方行业配置。主商机不可用时提示“商机主数据不可用，无法执行评分”并终止；关联数据失败时保留 `errors`，仅对受影响维度降级评分并说明可信度影响。
4. 优先使用用户本次提供的评分表。未提供时先检查第 2 步结果是否已包含评分标准；若未包含，使用 ToolsList「远端业务洞察文档」，设置 `coreTopics="商机评分标准"`。远端标准不可用时读取 `references/score-standard.md`；本地标准也缺失或不可用时，提示“缺少评分标准，无法执行评分”并终止。
5. 先检查第 2、4 步结果是否已包含输出模板；若均未包含，使用 ToolsList「远端业务洞察文档」，设置 `coreTopics="商机评分输出模板"`。远端模板不可用时读取 `references/output_template.md`。
6. 按选定标准评分并生成结果：每个维度只对有 CRM 或用户事实支撑的内容给分；缺失维度保守给分并写明原因；校验每项原始分不超过 10、总分与评级符合八维权重换算。不得输出诊断、行动建议、阶段判断或 CRM 写回动作。

### 回滚与重试

- 远端业务洞察文档查询（第 2、4、5 步）失败时：不重试，直接降级到本地 `references/` 文件。
- 商机详情查询（第 1 步）失败时：重试 1 次，最多 2 次；仍失败则提示“无法访问该商机记录”并终止。
- 商机统一数据包查询（第 3 步）失败时：不重试；主商机不可用则终止，关联数据失败则保留 `errors` 并只对受影响维度降级评分、说明可信度影响。

## Output

### 交付载体

以 Markdown 输出商机评分结果。优先使用 Workflow 第 5 步复用或获取到的远端模板；远端模板不可用时使用 `references/output_template.md`。

### 交付方式

- 默认以 Markdown 格式直接在对话中展示评分结果。
- 仅当用户明确要求“导出”或“保存”时，将结果写入当前工作目录的 `{商机名称}-评分报告.md`。

### 最小输出结构

1. 输入摘要：商机名称、`object_id`、对象类型、评分模式、是否使用用户评分表与记录人。
2. 总分：商机总分、当前评级、总体结论、优势维度和劣势维度。
3. 维度分：八个维度的“得分/10”与评分依据。
4. 评分依据与结论：关键事实、关键推断、最主要加分项、最主要减分项和当前投入优先级结论（不列行动）。

### 验收标准

- 每个维度分以“得分/10”呈现，且原始分不超过 10。
- 每个给分点引用 CRM 字段名或用户提供事实来源；敏感商务信息仅作定性描述。
- 总分与评级符合选定评分标准的八维权重换算规则。
- 使用远端模板时遵循其结构；使用本地兜底模板时包含四部分最小结构。

## Edge Cases

- 商机主数据查询失败：阻断评分，提示"商机主数据不可用，无法执行评分"。
- 脚本返回 `errors` 非空：不得忽略；若主商机可用但关联数据失败，允许降级评分，并在对应维度标注缺失数据包与可信度影响。
- 输入评分表、远端评分标准与 `references/score-standard.md` 均不可用：阻断评分，提示"缺少评分标准，无法执行评分"。
- 证据缺失时保守给分，并在评分依据中说明"当前记录暂未体现……"。
- 仅有部分维度得分：缺失维度按保守低分或 0 分计入，并标注"数据暂不可见"；总分仍按八维权重合计 90 的固定加权口径计算，不得因字段不可见缩小分母。

## Boundaries

- 只服务 `NewOpportunityObj`。
- 若对象并非商机，不继续执行本 skill。
- 只输出评分，不输出诊断、建议、阶段判断或 CRM 写回动作。
- 不得把未验证结论写成已确认事实；字段不可见时不得用模型推断补齐。
- 报价金额、单价、折扣等敏感商务信息仅用于内部判断商务成熟度、预算风险和竞争风险；评分依据只做定性描述，不逐条列示具体数值。

## References

- `references/data-query.md`
- `references/score-standard.md`
- `references/output_template.md`

## Related Skills

- `sfa-opportunity-diagnosis`：用户需要诊断、风险或行动建议时使用；本 skill 只输出评分。
- `data-read`：用户只需查询商机基础信息而不需要评分时使用。

## Scripts

- `scripts/query-diagnosis-data.py`：Workflow 第 3 步的 CRM 数据查询入口。
  - 唯一调用方式：`python scripts/query-diagnosis-data.py --opportunity-id <id> --pretty`。
  - 复用规则：若当前上下文已存在同一 `opportunity_id`、`status=READY`、包含 `queried_at` / `data` / `seller_context`、且 `queried_at` 距当前时间不超过 30 分钟的脚本返回 JSON，直接作为 `Opportunity_Data_Package` 消费，不重复调用脚本。
  - 行为：查询卖方行业配置、商机主数据、关联客户、商机联系人、联系人关系、报价/报价明细、销售记录、竞争对手明细，并输出统一 JSON 数据包；关联数据查询失败写入 `errors`。
  - 调用方必须消费返回的 `status` 与 `errors`：主商机不可用时阻断，关联数据失败时按评分维度显式降级，不得编造缺失事实。
