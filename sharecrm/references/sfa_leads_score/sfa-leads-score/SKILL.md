---
name: "sfa-leads-score"
description: "当用户要求为线索打分、评估线索质量、判断线索是否值得继续投入或输出线索评分明细时使用。不用于仅查询线索基础信息、输出诊断建议或处理非线索对象。"
apiName: "sfa_leads_score"
---
# sfa-leads-score

## Goal

为 `LeadsObj` 提供独立评分流程：查询线索事实，依据输入、远端或本地评分标准保守评分，并按适用模板输出结果。

### 成功标准

- 已确认线索对象、线索评分事实，以及可用评分标准。
- 仅使用 CRM 或用户提供的事实评分；无法核实的事实保留为“缺失”或“待确认”。
- 选择用户评分表、远端标准或本地兜底标准中的一个可用标准完成评分。
- 评分过程不产生诊断、行动建议、阶段判断或 CRM 写回动作。

## WhenToUse

**适合这些表达：**

- 帮我给这个线索打分
- 这条线索值不值得继续投入
- 看下这个线索的质量评分
- 输出这个线索的评分明细
- 评估一下这条线索的质量
- 这条线索值不值得继续跟
- 生成线索评分报告
- 帮我看看这个线索能打几分
- 这条线索的准入评估

**不适合这些表达：**

- 只想查询对象基础信息，不需要评分 → 走 `data-read`
- 需要输出诊断、风险、行动建议 → 走 `sfa-leads-diagnosis`
- 对象不是线索，或对象类型无法确认 → 先完成对象识别；本 skill 不执行评分

**边界条件：**

- 用户提供的线索名称在 CRM 中不存在 → 提示“未找到该线索”并终止，不执行评分。
- 用户评分表与本 skill 的评分标准不兼容 → 使用本 skill 的适用评分标准，并说明用户评分表格式不兼容。
- 对象类型已确认为非 `LeadsObj` → 不触发本 skill，并引导至对应对象的 skill。

## Inputs

| 输入 | 作用 | 必填 |
|:---|:---|:---|
| `object_id` + `object_api_name=LeadsObj` | 直接定位线索对象 | 是（与"线索名称"二选一） |
| 线索名称 + 可识别为线索的对象语义 | 通过名称归一为线索 ID | 是（与 `object_id` 二选一） |
| 评分表 | 本次输入明确提供评分表时，作为本次评分标准 | 否 |
| 业务补充事实 | 可作为评分依据，但不得替代 CRM 查询到的线索事实 | 否 |

### 信息不足处理

- 线索名称模糊匹配返回多个候选时，展示候选的 `_id`、`name`、`company`、`owner__r` 供用户选择，不自动选取第一条。
- 线索名称无法匹配任何记录时，提示“未找到该线索”并终止。
- 既未提供 `object_id` 也未提供线索名称时，主动追问线索名称或 ID，最多 2 轮；仍未提供则提示“缺少线索标识，无法执行评分”并终止。

## ToolsList

| 用途 | CLI 命令 | 关键参数 |
| --- | --- | --- |
| 远端知识检索 | sharecrm sales profile fast-query-document --data '{"scene":"<场景>","coreTopics":"<检索主题>"}' | `scene` 固定为 `business_insight`；`coreTopics` 为检索主题。 |
| 按名称查询记录 ID | sharecrm data record query-id-by-name --data '{"query":"<线索名称或公司名>","apiNames":["LeadsObj"]}' | `query` 为线索名称或公司名；`apiNames` 固定为 `["LeadsObj"]`。 |
| 名称归一化兜底查询 | sharecrm data record query-by-name --data '{"object_api_names":["LeadsObj"],"name":"<线索名称或关键词>"}' | `object_api_names` 固定为 `["LeadsObj"]`；`name` 为线索名称或关键词。 |
| 按字段条件查询记录 | sharecrm data record query-by-fields --object_api_name <对象ApiName> --select_fields "<字段1>,<字段2>" --<条件字段>-<操作符> "<值>" --limit <数量> --sort <字段:asc\|desc> --raw | 对象、字段、过滤条件、排序与数量按 `references/data-query.md` 设置。 |
| 按 ID 获取记录详情 | sharecrm data record get-by-id --object_api_name LeadsObj --id <线索ID> --raw | `object_api_name` 固定为 `LeadsObj`；`id` 为线索记录 ID。 |
| 获取对象描述 | sharecrm data describe get --object_api_name <对象ApiName> --simple_describe true | `object_api_name` 为 `LeadsObj` 或 `ActiveRecordObj`。 |

## Workflow

1. 确认对象并验证 `Object_Type=LeadsObj`。
   - 已提供 `object_id` 时，使用 ToolsList「按 ID 获取记录详情」查询并验证对象类型；记录不存在或无权访问时提示“无法访问该线索记录”并终止。
   - 仅提供线索名称时，先使用 ToolsList「按名称查询记录 ID」，未命中再使用「名称归一化兜底查询」归一为唯一线索 ID；未命中或存在多个候选时，按“信息不足处理”阻断并要求用户补充。
2. 使用 ToolsList 的“远端知识检索”，设置 `scene=business_insight`、`coreTopics=线索评分标准`，强制读取 ShareCRM 远端评分流程 / 评分标准并按此流程执行。保留返回的 `dataList` / `contentText`，供后续评分标准和输出模板选择复用；远端执行失败、无结果、返回空内容或不可用时，继续使用本 skill 的本地流程。
3. 读取 `references/data-query.md`，使用 ToolsList「按字段条件查询记录」「按 ID 获取记录详情」和「获取对象描述」查询线索事实。字段查询全部失败且没有任何可用事实时，提示“无法获取线索事实，评分无法执行”并终止。
4. 按以下优先级确定评分标准并完成保守评分：
   1. 用户本次输入的评分表。
   2. Workflow 第 2 步返回的评分标准。
   3. 第 2 步远端结果不可用时，读取 `references/score-standard.md` 作为本地兜底评分标准；本地标准也缺失或不可用时，提示“缺少评分标准，无法执行评分”并终止。
5. 先检查 Workflow 第 2 步返回内容是否包含评分输出模板；若包含则直接复用。若不包含，使用 ToolsList 的“远端知识检索”，设置 `scene=business_insight`、`coreTopics=线索评分输出模板`，强制读取远端模板并按模板生成评分结果；远端执行失败、无结果、返回空内容或不可用时，读取 `references/output_template.md` 作为本地兜底模板。
6. 按选定标准评分并生成结果：每项给分都引用 CRM 或用户事实；缺失维度保守给分并写明原因；校验总分、评级及七问 `/70`、三要素 `/30` 的换算符合选定标准。不得输出诊断、行动建议、阶段判断或 CRM 写回动作。

### 回滚与重试

- 远端知识检索（第 2、5 步）失败时：不重试，直接降级到本地 `references/` 文件。
- 线索详情查询（第 1 步）失败时：重试 1 次，最多 2 次；仍失败则提示“无法访问该线索记录”并终止。
- 销售记录或其他关联事实查询（第 3 步）失败时：不重试，标注“关联跟进数据暂不可用”，继续使用已有线索事实评分。
- 字段描述查询（第 3 步）失败时：不重试，使用 `references/data-query.md` 中预定义的字段集直接查询。

## Output

### 交付载体

以 Markdown 输出线索评分结果。优先使用 Workflow 第 5 步复用或获取到的远端模板；远端模板不可用时使用 `references/output_template.md`。

### 交付方式

- 默认以 Markdown 格式直接在对话中展示评分结果。
- 仅当用户明确要求“导出”或“保存”时，将结果写入当前工作目录的 `{线索名称}-评分报告.md`。

### 输出结构

- 基本信息：客户名称、行业、线索来源与验证时间。
- 综合准入评估：综合得分（`/100`）、线索评级（A/B/C/D）、准入结论和判断依据。
- 七问量化评估：7 项逐项得分、总分（`/70`）和每项说明。
- 三要素评估：Timeline、Sponsor、现场拜访逐项得分、总分（`/30`）和每项说明。

完整 Markdown 示例见 `references/output_template.md` 中的“线索验证报告”。

### 验收标准

- 每项评分都附带明确证据来源，如 CRM 字段值或销售记录内容。
- 证据缺失时保守给分，并在说明中标注“当前记录暂未体现”。
- 不回显联系人手机号、邮箱等敏感信息。
- 综合得分必须按选定标准计算；本地七问/三要素标准下，使用 `(七问总分/70×100)×40% + (三要素总分/30×100)×60%`。

## Edge Cases

- 线索详情查询失败或字段不足：按 `references/data-query.md` 缩小字段集补查；仍不足时，缺失维度保守给分并标注"字段暂不可见"。
- 输入评分表、远端评分标准与 `references/score-standard.md` 均不可用：阻断评分，提示"缺少评分标准，无法执行评分"。
- 证据缺失时保守给分，并在评分依据中说明"当前记录暂未体现……"。
- 仅有部分维度得分：缺失维度按保守低分或 0 分计入，并标注"数据暂不可见"；总分仍按七问 `/70`、三要素 `/30` 的固定满分计算，不得因字段不可见缩小分母。

## Boundaries

- 只服务 `LeadsObj`。
- 若对象并非线索，不继续执行本 skill。
- 只输出评分，不输出诊断、建议、阶段判断或 CRM 写回动作。
- 不得把未验证结论写成已确认事实；字段不可见时不得用模型推断补齐。

## References

- `references/data-query.md`
- `references/score-standard.md`
- `references/output_template.md`

## Related Skills

| Skill | 关系 | 说明 |
|:---|:---|:---|
| `data-read` | 上游 / 替代 | 仅查询对象基础信息、不需要评分时使用 |
| `sfa-leads-diagnosis` | 下游 | 评分后如需输出诊断、风险或行动建议，使用该 skill |
| `01-lead-discovery` | 协同 | 线索发现与验证可与本 skill 的评分结果配合使用 |
