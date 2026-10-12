---
name: "sfa-decision-chain-diagnosis"
description: "决策链诊断专属 skill。为已明确属于 NewOpportunityObj 的 CRM 商机对象提供统一诊断流程，并按模板要求生成决策链诊断结果；当请求已经明确是决策链诊断时，使用该 skill。"
apiName: "sfa_decision_chain_diagnosis"
---
# sfa-decision-chain-diagnosis

## Goal

本 skill 只服务于 `NewOpportunityObj`，并只消费决策链诊断所需的 CRM 事实、评分标准和输出模板。

当对象已经明确是商机，且任务属于决策链诊断时，优先使用本 skill。

### 成功标准

- 已确认唯一 `NewOpportunityObj`，并取得诊断所需的商机、客户、联系人、关系和销售记录事实。
- 三底线评分只使用 CRM 事实或用户明确补充事实；无法核实的内容标注为 `待补充`、`无法判断` 或 `⚠️ 推断`。
- 诊断结果必须遵循 `references/output_template.md` 或同等结构的远端模板，且所有评分口径来自 `references/score-standard.md` 或等价远端标准。
- 不输出通用商机评分、完整商机诊断之外的 CRM 写回动作，也不允许模型手工拼接 HTML。

## WhenToUse

**适合这些表达：**

- 帮我诊断这个项目的决策链
- 真假决策者怎么判断
- 这个商机卡在谁那里
- 关键人覆盖是否完整
- 反对者和隐性权力中心怎么处理

**不适合这些表达：**

- 只想查询或修改 CRM 字段 → 使用 `data-read` / `data-edit`
- 只想做需求洞察、竞争分析或首面准备 → 使用 `sfa-needs-discovery` / `sfa-opportunity-competitive-analysis`
- 只想生成会议总结或润色话术 → 不触发本 skill
- 只想做通用商机评分或完整商机诊断 → 使用 `sfa-opportunity-score` / `sfa-opportunity-diagnosis`

**边界条件：**

- 只支持 `NewOpportunityObj` 的决策链诊断；对象确认不是商机时，停止本 skill 并引导到对应对象 skill。
- 商机对象不明确时，先按名称或客户名称定位唯一商机；无法唯一定位时展示候选并等待用户选择，不得自行猜测。
- 行业背景不明确时仍可执行通用诊断，但所有行业特定推断必须降级并显式标注。
- 远端诊断标准或输出模板不可用时，必须回退到本地 `references/`，不得进入无标准状态。

## Supported Object

| Object_Type | 说明 | References_Bundle |
| --- | --- | --- |
| `NewOpportunityObj` | 商机决策链诊断 | `references/` |

本 skill 只读取以下本地兜底资料：

- `references/data-query.md`
- `references/score-standard.md`
- `references/output_template.md`

## What I Need From You

| 输入 | 作用 | 必填 |
|:---|:---|:---|
| `object_id` + `object_api_name=NewOpportunityObj` | 直接定位商机对象 | 是（与“商机名称 / 项目名称”二选一） |
| 商机名称 / 项目名称 | 通过名称归一为商机 ID | 是（与 `object_id` 二选一） |
| 客户名称 | 当未提供商机时，用于先定位 `AccountObj` 再反查关联商机 | 否 |
| 决策链补充事实 | 包括关键人、角色、态度、组织结构、卡点、Coach、反对者等信息 | 否 |
| 当前项目阶段 / 诊断人 / 行业补充信息 | 用于补充诊断上下文，但不得替代 CRM 查询到的商机事实 | 否 |

### 信息不足处理

- 既没有 `object_id` 也没有可识别的商机名称时，先简短追问商机名称或 ID，最多 2 轮；仍无法确认则终止。
- 只提供客户名称时，先按 `references/data-query.md` 定位 `AccountObj`，再反查关联商机；若存在多个候选，展示候选并等待用户选择。
- 行业或关键决策链事实缺失时，可以继续诊断，但必须在相关结论中标注 `待补充`、`无法判断` 或 `⚠️ 推断`。
- 报告人 / 诊断人无法确认时，输出 `待补充`，不得自行补齐。

## ToolsList

详细字段组合、查询顺序和降级规则见 `references/data-query.md`。Workflow 只引用工具用途和参数值，不重复粘贴完整命令。

| 用途 | CLI 命令 | 关键参数 |
| --- | --- | --- |
| 远端决策链标准 / 模板检索 | `sharecrm sales profile fast-query-document --data '{"scene":"business_insight","coreTopics":"<主题>"}'` | `scene` 固定为 `business_insight`；`coreTopics` 为“决策链诊断标准”或“决策链诊断输出模板”，有卖方行业时在主题后拼接 `,<SELLER_INDUSTRY>`。 |
| 读取卖方行业配置 | `sharecrm sales get-config-by-key --data '{"key":"service_models"}'` | `key` 固定为 `service_models`。 |
| 按名称定位商机 | `sharecrm data record query-id-by-name --data '{"query":"<商机名称>","apiNames":["NewOpportunityObj"]}'` | `query` 为商机名称；`apiNames` 固定为 `["NewOpportunityObj"]`。 |
| 按字段查询记录 | `sharecrm data record query-by-fields --object_api_name <对象ApiName> --select_fields "<字段1>,<字段2>" --<字段>-eq <值> --limit <数量> --sort <字段>:desc|asc --raw` | `object_api_name`、`select_fields`、过滤条件和排序字段按当前查询场景填充。 |
| 按 ID 获取记录 | `sharecrm data record get-by-id --data '{"object_api_name":"<对象ApiName>","id":"<记录ID>"}' --raw` | `object_api_name` 为目标对象 API 名；`id` 为记录 ID。 |
| 获取对象字段描述 | `sharecrm data describe get --data '{"object_api_name":"<对象ApiName>","simple_describe":true}'` | 字段或关系对象不确定时先执行。 |

## Workflow

1. 确认对象并验证 `Object_Type=NewOpportunityObj`。已有 `object_id` 时先用 ToolsList「按 ID 获取记录」验证；只有商机名称时先用「按名称定位商机」，未命中再按 `references/data-query.md` 的名称兜底规则查询；只有客户名称时先定位 `AccountObj` 再反查关联商机。无法定位唯一商机时展示候选并等待用户选择。
2. 读取 `references/data-query.md`，并按其中约定查询卖方行业配置、商机主数据、关联客户、联系人、联系人关系和销售记录。字段或关系对象不确定时先用 ToolsList「获取对象字段描述」确认；关系对象不存在时降级为联系人加销售记录路径，并在结果中标注证据不足。
3. 优先使用 ToolsList「远端决策链标准 / 模板检索」读取决策链诊断标准：有 `SELLER_INDUSTRY` 时设置 `coreTopics="决策链诊断标准,<SELLER_INDUSTRY>"`，否则使用 `coreTopics="决策链诊断标准"`。远端失败、无结果或不可用时，回退到 `references/score-standard.md`。
4. 依据第 3 步标准执行决策链诊断，完成真假决策者判断、隐性权力中心识别、六类角色覆盖分析和三底线量化评分。所有分数必须来自选定标准；证据缺失时保守给分，不得缩小分母。
5. 优先使用 ToolsList「远端决策链标准 / 模板检索」读取输出模板：有 `SELLER_INDUSTRY` 时设置 `coreTopics="决策链诊断输出模板,<SELLER_INDUSTRY>"`，否则使用 `coreTopics="决策链诊断输出模板"`。远端模板失败、为空或不可用时，回退到 `references/output_template.md`。
6. 按第 5 步模板生成 Markdown 诊断结果。正文至少包含概要、核心诊断结论、三底线量化评分、决策链覆盖地图、真假决策者校验、隐性权力中心观察、根因分析、关键风险与应对策略、建议动作。
7. 如用户明确需要 HTML 诊断，通过 `scripts/build-html-report.py` 从第 6 步的完整 Markdown 正文渲染 HTML 文件，并返回生成路径；脚本失败时立即停止，不得由模型手工拼接 HTML。

### 回滚与重试

- 远端标准 / 模板检索（第 3、5 步）失败时：不重试，直接回退到本地 `references/`。
- 主商机定位或主记录查询失败时：允许重试 1 次；仍失败则终止，并说明无法定位或访问该商机。
- 关联数据查询失败时：不阻断主流程，但必须保留缺口并仅对受影响结论降级，不得把缺失证据写成正向事实。
- HTML 渲染失败时：不输出 HTML，不做手工兜底；保留 Markdown 结果并说明脚本失败。

## Output

### 交付格式

默认交付为 Markdown 决策链诊断报告。优先使用 Workflow 第 5 步获取到的远端模板；远端模板不可用时，使用 `references/output_template.md`。

### 交付方式

- 默认直接在对话中展示 Markdown 诊断结果。
- 仅当用户明确要求导出或保存时，将 Markdown 写入当前工作目录的 `{商机名称}-决策链诊断.md`。
- 仅当用户明确要求 HTML 诊断时，通过 `scripts/build-html-report.py` 生成 `{商机名称}-决策链诊断.html`，并返回文件路径。

### 验收标准

- 必须包含：概要、核心诊断结论、三底线量化评分表、决策链覆盖地图、真假决策者校验、隐性权力中心观察、根因分析、关键风险与应对策略、P0/P1/P2 建议动作。
- 所有评分必须来自 `references/score-standard.md` 或等价远端标准，综合评分固定为三底线总分 `0-30`。
- 所有关键判断必须尽量引用 CRM 事实或用户明确补充事实；无证据时只能写 `待补充`、`无法判断` 或 `⚠️ 推断`。
- 输出只允许是决策链诊断，不扩展为通用商机评分、完整商机诊断或 CRM 写回建议。
- HTML 只允许由 `scripts/build-html-report.py` 生成，禁止模型直接拼接。

## Edge Cases

- 商机重名或匹配到多个候选：按 `references/data-query.md` 展示候选并等待用户确认，不得自行猜测。
- 只有客户名称、没有商机名称：先定位 `AccountObj`，再反查关联 `NewOpportunityObj`。
- 商机联系人关系对象不存在、字段不确定或不可见：先 describe 校验；若仍不可用，降级为 `ContactObj + ActiveRecordObj` 路径，并标注证据不足。
- 关键人、Coach、反对者证据稀疏：保守评分，不得把缺失证据当成正向证据。
- `诊断人` 无法从 CRM owner 或用户输入确认：输出 `待补充`。
- 行业背景不明确：仍可执行通用诊断，但所有行业特定判断必须降级并显式标注。

## Boundaries

- 只服务 `NewOpportunityObj`。
- 若对象并非商机，不继续执行本 skill。
- 只输出决策链诊断，不输出通用商机评分、完整商机诊断或 CRM 写回动作。
- 不得把职位头衔直接等同于真实决策权、支持度或影响力。
- 不得编造人物关系、权力结构、决策角色、内部态度或隐性权力中心。
- 不得把未验证结论写成已确认事实；信息不足时必须标注 `待补充` / `无法判断` / `⚠️ 推断`。
- 不加载本 skill 目录外的行业场景资料。
- 不把诊断方法论当作项目事实输出。
- 如需 HTML 输出，必须通过 `scripts/build-html-report.py` 渲染，禁止模型直接拼接 HTML。

## References

- `references/data-query.md`
- `references/score-standard.md`
- `references/output_template.md`

## Related Skills

- `sfa-opportunity-score`：当用户只需要三底线之外的商机评分结果、不需要诊断结论时使用。
- `sfa-opportunity-diagnosis`：当用户需要完整商机诊断、阶段判断或更宽范围的风险与行动建议时使用。
- `sfa-needs-discovery`：决策链诊断可复用其需求背景；当问题核心是需求洞察而非关键人结构时优先使用。
- `sfa-opportunity-competitive-analysis`：当风险主要来自竞品、报价或客户倾向竞争时，与本 skill 协同使用。

## Scripts

- `scripts/build-html-report.py`：Workflow 第 7 步的可选 HTML 渲染入口。
  - 入参：`--markdown <markdown>`（第 6 步产出的完整 Markdown 原文）、`--input <path>`（兼容旧文件输入）、`--output <html>`（缺省写 stdout）、`--schema` 打印 Markdown 结构提示；未传 `--markdown/--input` 时从 stdin 读取。
  - 行为：先按 `references/output_template.md` 固定结构校验并解析 Markdown；再读取 `assets/output.html` 的 `<style>` 作为唯一样式来源；最后输出完整 HTML。
  - 退出码：Markdown 结构校验失败、样式文件缺失均以退出码 1 终止；调用方必须在失败时停止流水线，不得手工拼接 HTML。
