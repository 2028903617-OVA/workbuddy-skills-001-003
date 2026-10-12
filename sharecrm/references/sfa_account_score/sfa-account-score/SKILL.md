---
name: "sfa-account-score"
description: "当用户要求为客户打分、评估客户健康度、判断客户价值或输出客户评分明细时使用。不用于仅查询客户基础信息、输出诊断建议或处理非客户对象。"
apiName: "sfa_account_score"
---
# sfa-account-score

## Goal

为 `AccountObj` 提供独立评分流程：查询客户及关联商机事实，依据输入、远端或本地评分标准保守评分，并按适用模板输出结果。

### 成功标准

- 已确认客户对象、客户及关联商机事实，以及可用评分标准。
- 仅使用 CRM 或用户提供的事实评分；无法核实的事实保留为“缺失”或“待确认”。
- 选择用户评分表、远端标准或本地兜底标准中的一个可用标准完成评分。
- 评分过程不产生诊断、行动建议、阶段判断或 CRM 写回动作。

## WhenToUse

**适合这些表达：**

- 帮我给这个客户打分
- 看下这个客户的健康度评分
- 这个客户值不值得继续投入
- 输出这个客户的评分明细

**不适合这些表达：**

- 只想查询对象基础信息，不需要评分 → 走 `data-read`
- 需要输出诊断、风险、行动建议 → 走 `sfa-account-diagnosis`
- 对象不是客户，或对象类型无法确认 → 先完成对象识别；本 skill 不执行评分

**边界条件：**

- 用户提供的客户名称在 CRM 中不存在 → 提示“未找到该客户”并终止，不执行评分。
- 用户评分表与本 skill 的评分标准不兼容 → 使用本 skill 的适用评分标准，并说明用户评分表格式不兼容。
- 对象类型已确认为非 `AccountObj` → 不触发本 skill，并引导至对应对象的 skill。

## Inputs

| 输入 | 作用 | 必填 |
|:---|:---|:---|
| `object_id` + `object_api_name=AccountObj` | 直接定位客户对象 | 是（与"客户名称"二选一） |
| 客户名称 + 可识别为客户的对象语义 | 通过名称归一为客户 ID | 是（与 `object_id` 二选一） |
| 评分表 | 本次输入明确提供评分表时，作为本次评分标准 | 否 |
| 业务补充事实 | 可作为评分依据，但不得替代 CRM 查询到的客户事实 | 否 |

### 信息不足处理

- 用户既未提供 `object_id` 也未提供客户名称时，主动追问客户名称或 ID，最多 2 轮；仍未提供则提示“缺少客户标识，无法执行评分”并终止。
- 用户提供名称但查询无结果时，展示候选列表并等待确认；无候选时提示“未找到该客户”并终止。

## ToolsList

| 用途 | CLI 命令 | 关键参数 |
| --- | --- | --- |
| 远端业务洞察文档 | sharecrm sales profile fast-query-document --data '{"scene":"business_insight","coreTopics":"<检索主题>"}' | `scene` 固定为 `business_insight`；`coreTopics` 为检索主题。 |
| 按名称定位客户 | sharecrm data record query-id-by-name --data '{"query":"<客户名称>","apiNames":["AccountObj"]}' | `query` 为客户名称；`apiNames` 固定为 `["AccountObj"]`。 |
| 名称归一化兜底查询 | sharecrm data record query-by-name --data '{"object_api_names":["AccountObj"],"name":"<客户名称或关键词>"}' | `object_api_names` 固定为 `["AccountObj"]`；`name` 为客户名称或关键词。 |
| 获取客户详情 | sharecrm data record get-by-id --object_api_name AccountObj --id <account_id> | `object_api_name` 固定为 `AccountObj`；`id` 为客户记录 ID。 |
| 获取字段描述 | sharecrm data describe identify-with-describe --object_api_name AccountObj | `object_api_name` 固定为 `AccountObj`。 |
| 按字段查询客户或关联商机 | sharecrm data record query-by-fields --data '{"object_api_name":"<对象ApiName>","select_fields":["<字段1>","<字段2>"],"filters":[{"field_api_name":"<字段ApiName>","operator":"EQ","values":["<值>"]}],"orders":[{"field_api_name":"<排序字段>","is_asc":false}],"limit":<数量>}' | `object_api_name`、`select_fields`、`filters`、`orders`、`limit` 按 `references/data-query.md` 设置。 |

## Workflow

1. 确认对象并验证 `Object_Type=AccountObj`。有 ID 时使用 ToolsList「获取客户详情」验证；记录不存在或无权访问时提示“无法访问该客户记录”并终止。只有名称时先使用「按名称定位客户」，未命中再使用「名称归一化兜底查询」。多个候选时展示候选并等待用户确认；没有候选时提示“未找到该客户”并终止。
2. 使用 ToolsList「远端业务洞察文档」查询 `scene="business_insight"`、`coreTopics="客户评分流程"`。保留返回的 `dataList` / `contentText`；后续步骤优先复用其中已有的评分标准或输出模板。远端调用失败、无结果、内容为空或不可用时继续使用本地流程。
3. 读取 `references/data-query.md`，仅使用其中定义的对象、字段和关联关系。
4. 使用 ToolsList「获取客户详情」「获取字段描述」和「按字段查询客户或关联商机」获取评分所需客户事实与关联商机事实。字段不足时先确认描述后缩小字段集重查；字段不存在或记录未体现时保留缺失，不猜测。字段查询全部失败且没有任何可用事实时，提示“无法获取客户事实，评分无法执行”并终止。
5. 优先使用用户本次提供的评分表。未提供时先检查第 2 步结果是否已包含评分标准；若未包含，使用 ToolsList「远端业务洞察文档」查询 `coreTopics="客户评分标准"`。远端标准不可用时读取 `references/score-standard.md` 作为兜底；若本地标准也缺失或不可用，提示“缺少评分标准，无法执行评分”并终止。
6. 先检查第 2、5 步结果是否已包含输出模板；若均未包含，使用 ToolsList「远端业务洞察文档」查询 `coreTopics="客户评分输出模板"`。远端模板不可用时读取 `references/output_template.md`。
7. 按选定标准评分并生成结果：只对有 CRM 或用户提供事实支撑的维度给分；缺失维度按标准保守给分并写明缺失原因；校验维度分不超过满分、总分与评级符合选定标准。不得输出诊断、行动建议、阶段判断或 CRM 写回动作。

### 回滚与重试

- 远端业务洞察文档查询（第 2、5、6 步）失败时：不重试，直接降级到本地 `references/` 文件。
- 客户详情查询（第 1 步）失败时：重试 1 次，最多 2 次；仍失败则提示“无法访问该客户记录”并终止。
- 关联商机查询（第 4 步）失败时：不重试，标注“关联商机数据暂不可用”，继续使用已有客户事实评分。
- 字段描述查询（第 4 步）失败时：不重试，使用 `references/data-query.md` 中预定义的字段集直接查询。

## Output

### 交付载体

以 Markdown 输出客户评分结果。优先使用 Workflow 第 6 步复用或获取到的远端模板；远端模板不可用时使用 `references/output_template.md`。

### 交付方式

- 默认以 Markdown 格式直接在对话中展示评分结果。
- 仅当用户明确要求“导出”或“保存”时，将结果写入当前工作目录的 `{客户名称}-评分报告.md`。

### 最小输出结构

1. 输入摘要：客户名称、`object_id`、对象类型、评分模式、是否使用用户评分表与记录人。
2. 总分：客户总分、当前评级、总体结论、最强维度和最弱维度。
3. 维度分：每个已使用维度的“得分/满分”与评分依据。
4. 评分依据与结论：关键事实、关键推断、最主要加分项、最主要减分项和当前投入优先级结论（不列行动）。

### 验收标准

- 每个维度分以“得分/满分”呈现，且得分不超过该维度满分。
- 每个给分点引用 CRM 字段名或用户提供事实来源。
- 总分与评级符合选定评分标准的换算规则。
- 使用远端模板时遵循其结构；使用本地兜底模板时包含四部分最小结构。

## Edge Cases

- 客户详情查询失败或字段不足：按 `references/data-query.md` 缩小字段集补查；仍不足时，缺失维度保守给分并标注"字段暂不可见"。
- 输入评分表、远端评分标准与 `references/score-standard.md` 均不可用：阻断评分，提示"缺少评分标准，无法执行评分"。
- 输出模板不可用：按 Output 的四部分最小结构输出。
- 证据缺失时保守给分，并在评分依据中说明"当前记录暂未体现……"。
- 经营健康度模式但缺少存量经营数据：降低经营健康度维度权重，标注"经营数据暂不可见"。

## Boundaries

- 只服务 `AccountObj`。
- 若对象并非客户，不继续执行本 skill。
- 只输出评分，不输出诊断、建议、阶段判断或 CRM 写回动作。
- 不得把未验证结论写成已确认事实；字段不可见时不得用模型推断补齐。

## References

- `references/data-query.md`
- `references/score-standard.md`
- `references/output_template.md`

## Related Skills

- `sfa-account-diagnosis`：用户需要诊断、风险或行动建议时使用；本 skill 只输出评分。
- `data-read`：用户只需查询客户基础信息而不需要评分时使用。
