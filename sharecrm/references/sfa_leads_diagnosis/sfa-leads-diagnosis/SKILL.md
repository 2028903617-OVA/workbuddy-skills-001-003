---
name: "sfa-leads-diagnosis"
description: "当用户要求对线索（`LeadsObj`）做诊断、画像、风险识别或下一步跟进建议时使用。评分优先通过 `get_profile_score` CLI 查询，必要时回退 `sfa-leads-score`。如需生成 HTML 诊断报告，必须按本 skill 的串行流程渲染并保存诊断结果。不用于仅查字段或 knowhow、或非线索对象。"
apiName: "sfa_leads_diagnosis"
---
# sfa-leads-diagnosis

## Goal

对一个明确的线索（`LeadsObj`）按统一框架输出可解释、可执行的诊断正文。

### 成功标准

- 已确认线索对象、可用 `Scoring_Result` 来源，以及本次诊断所需的线索事实与销售记录。评分优先使用 `get_profile_score`；仅当 CLI 结果不可用时回退 `sfa-leads-score`。
- 诊断正文以 `Scoring_Result` 为主骨架，并基于本次查询到的线索数据直接生成 `AI_Stage`。
- 输出遵循远端模板或本地兜底模板；如生成 HTML，严格经脚本渲染、`render_content` 获取 `npath`、再调用 `save_diagnosis`。
- 不调用被禁止工具，不把未核实事实写成已确认结论。

## WhenToUse

**适合这些表达：**

- 洞察这个线索
- 诊断当前状态
- 生成线索画像
- 值不值得继续投入
- 下一步怎么跟
- 识别推进卡点与风险

**不适合这些表达：**

- 只提取字段或回填对象 → 走 `data-add` / `data-edit`
- 只做 knowhow 查询，不需要对象级判断
- 只做会议总结或文本润色
- 对象不是线索，或线索无法定位

**边界条件：**

- 用户既未提供 `object_id` 也未提供线索名称时，最多追问 2 轮；仍无法定位则提示“缺少诊断对象，无法执行诊断”并终止。
- `Scoring_Result` 缺失、来源不明或不匹配时，先查询 `get_profile_score`；CLI 不可用时回退 `sfa-leads-score`，两者均不可用才终止。
- 对象类型已确认为非 `LeadsObj` 时，不触发本 skill，并引导到对应对象的诊断 skill。

## Supported Object

| Object_Type | 说明 | References_Bundle |
| --- | --- | --- |
| `LeadsObj` | 线索 | `references/` |

本 skill 的本地兜底资料包括：
- `references/data-query.md`
- `references/flow.md`
- `references/global-diagnosis-criteria.md`
- `references/output_template.md`

## Inputs

| 输入 | 作用 | 必填 |
|:---|:---|:---|
| `object_id` + `Object_Type=LeadsObj` | 直接定位线索对象 | 是（与“线索名称”二选一） |
| 线索名称 | 归一为唯一线索 ID | 是（与 `object_id` 二选一） |
| `Scoring_Result` | 驱动全局诊断和风险识别 | 是 |
| 业务补充事实 | 补充 CRM 中不可见但用户明确提供的事实 | 否 |

### 信息不足处理

- 已给 `object_id` 时直接查询并验证对象类型；记录不存在、无权访问或对象不是线索时立即终止。
- 仅给名称时先查候选；未命中时展示兜底候选并等待确认。多候选仍无法确认时终止，不自动选第一条。
- `Scoring_Result` 必须优先来自 `get_profile_score`（`objectApiName=LeadsObj`）对同一线索的可用结果；CLI 失败、为空、无评分信息或对象不一致时，回退 `sfa-leads-score`。两者均不可用时阻断，不自行评分，也不接受 `sfa-business-score` 或其他通用评分结果替代。
- 业务补充事实可辅助判断，但不得覆盖 CRM 已查事实，不得替代评分或阶段证据。

## ToolsList

| 用途 | 命令 / 工具 | 关键参数 |
| --- | --- | --- |
| 远端业务洞察文档 | `sharecrm sales profile fast-query-document --data '{"scene":"business_insight","coreTopics":"<主题>"}'` | `scene` 固定为 `business_insight`；`coreTopics` 取 `线索诊断流程`、`线索诊断标准`、`线索诊断输出模板`，必要时追加 `,<SELLER_INDUSTRY>`。 |
| 按名称定位线索 | `sharecrm data record query-id-by-name --data '{"query":"<线索名称或公司名>","apiNames":["LeadsObj"]}'` | `query` 为线索名称或公司名；`apiNames` 固定为 `["LeadsObj"]`。 |
| 名称归一化兜底查询 | `sharecrm data record query-by-name --data '{"object_api_names":["LeadsObj"],"name":"<线索名称或公司关键词>"}'` | `object_api_names` 固定为 `["LeadsObj"]`；`name` 为线索名称或公司关键词。 |
| 获取线索详情 | `sharecrm data record get-by-id --object_api_name LeadsObj --id <lead_id>` | `object_api_name` 固定为 `LeadsObj`；`id` 为线索记录 ID。 |
| 按字段查询线索或销售记录 | `sharecrm data record query-by-fields --data '{...}'` | 具体 `object_api_name`、`select_fields`、`filters`、`orders`、`limit` 以 `references/data-query.md` 为准。 |
| 读取卖方行业配置 | `sharecrm sales get-config-by-key --data '{"key":"service_models"}'` | `key` 固定为 `service_models`。 |
| 查询线索评分 | `sharecrm sales profile get_profile_score --objectApiName LeadsObj --objectId <lead-id>` | 优先消费同一线索的非空可用 CLI 结果；失败、为空、无评分信息或对象不匹配时，回退 `sfa-leads-score`。 |
| 渲染 HTML 诊断 | `python scripts/build-html-report.py --markdown "$DIAGNOSIS_MARKDOWN" --output tmp/diagnosis_report.html` | `$DIAGNOSIS_MARKDOWN` 必须是 Workflow 第 7 步产出的完整 Markdown 原文。 |
| 上传 HTML 并获取 `npath` | `render_content` | 输入渲染成功的 HTML 文件；必须从返回结果中提取 `path` 字段作为 `npath`。 |
| 保存诊断结果 | `sharecrm sales profile save_diagnosis --objectApiName LeadsObj --objectId <线索id> --score "<评分>" --summary <npath> --insightRating "<评级>"` | `--summary` 只能传 `render_content` 返回的 `npath`，不得传本地路径、`file://` URL 或 HTML 文本。 |

## Workflow

1. 定位线索并验证 `Object_Type=LeadsObj`。定位优先级：①已给 `object_id` 直接定位；②只给名称则先用 ToolsList「按名称定位线索」，未命中时再用「名称归一化兜底查询」归一为唯一 ID；③无 ID 无名称则阻断“缺少诊断对象，无法执行诊断”；④定位结果非线索则停止并提示改用对应对象诊断 skill。
2. 读取 `references/data-query.md`，并按当前意图与其中定义的字段、对象和关联关系查询线索数据（字段、特征、销售记录）。
3. 使用 ToolsList「读取卖方行业配置」并参照 `references/data-query.md` 解释结果，得到 `SELLER_INDUSTRY`；为空时不拼接行业，并在输出中标注“缺少卖方行业信息”。
4. 查询并校验当前线索的 `Scoring_Result`。首先执行 `sharecrm sales profile get_profile_score --objectApiName LeadsObj --objectId <lead-id>`；若返回同一 `LeadsObj` 的非空可用综合得分、评级或至少一个维度，直接消费其结果，保留维度名称、顺序、得分和依据，并记录评分来源为“CLI”，不得调用 `sfa-leads-score`。若 CLI 失败、返回空结果、无可用评分信息或无法确认对象一致，则回退 `sfa-leads-score` 对同一线索评分，记录来源为“sfa-leads-score 回退”；仅当回退也不可用时才阻断。本 skill 不自行计算评分，也不接受 `sfa-business-score` 或其他通用评分结果替代。随后直接基于本次线索数据生成 `AI_Stage`，不得调用、引用或要求调用 `sfa-biz-router`：
   - 读取线索主数据的 `leads_stage` 和 `biz_status`，保留 API 值与显示值作为系统锚点；字段缺失时可用 `leads_status` 作为兼容状态锚点，并如实标注。
   - 再按时间由近到远读取销售记录，并结合线索的意向、需求描述、关键联系人和明确的下一步动作判断成熟度。首次触达或我方单方面发送材料，不得单独作为进入下一阶段的证据。
   - 仅在已验证需求或业务场景、关键联系人或 Sponsor 线索、可执行时间窗口与下一步动作同时满足时，输出“SQL”或“可转商机”；显式无效、拒绝或长期不可达等 CRM 事实才可输出“疑似无效”。证据不足时输出“潜在线索 / 信息不足”，不得因关键词孤立出现跨级推断。
   - `AI_Stage` 必须包含：`系统阶段`（`leads_stage`）、`系统状态`（`biz_status` 或兼容状态）、`AI判定阶段`、`阶段结论`（仅可为“成熟度与 leads_stage/biz_status 基本一致 / 可转商机 / 需继续培育 / 疑似无效 / 信息不足”之一）和一句可追溯的判断说明。
5. 强制使用 ToolsList「远端业务洞察文档」读取线索诊断流程，`scene` 固定为 `business_insight`，`coreTopics` 为 `线索诊断流程,<SELLER_INDUSTRY>`；当 `SELLER_INDUSTRY` 为空时仅使用 `线索诊断流程`。保留返回的 `dataList` / `contentText`，后续优先复用其中已包含的诊断标准或输出模板；远端执行失败、无结果、返回空内容或不可用时，读取 `references/flow.md` 作为本地兜底流程。

   生成线索诊断时，先检查本步骤返回内容是否已包含诊断标准。若已包含，直接复用，不再重复调用远端工具；若未包含，再使用 ToolsList「远端业务洞察文档」读取 `线索诊断标准,<SELLER_INDUSTRY>`，行业为空时只用 `线索诊断标准`。若实际调用了远端诊断标准，保留返回结果供第 7 步复用；远端执行失败、无结果、返回空内容或不可用时，读取 `references/global-diagnosis-criteria.md` 作为本地兜底诊断标准。全局诊断必须以 `Scoring_Result` 为主骨架，不得只复述分数。
6. 使用第 5 步获得或兜底的线索诊断流程与诊断标准完成正文判断；若仅获得本地兜底资料，需显式说明远端 knowhow 不可用导致解释深度降低。
7. 先检查第 5 步已取得的远端返回内容是否包含诊断输出模板。若任一返回已包含，直接复用其中模板，不再重复调用远端工具；若均未包含，再使用 ToolsList「远端业务洞察文档」读取 `线索诊断输出模板,<SELLER_INDUSTRY>`，行业为空时只用 `线索诊断输出模板`。远端执行失败、无结果、返回空内容或不可用时，读取 `references/output_template.md` 作为本地兜底模板，并按模板要求输出 Markdown 诊断正文。
8. 仅当用户明确需要 HTML 诊断时，按以下三步**串行执行**，不得跳步、并行或调整顺序，**禁止模型直接拼接 HTML**：
   1. 使用 ToolsList「渲染 HTML 诊断」生成 `tmp/diagnosis_report.html`。脚本会校验 Markdown 结构是否符合 `references/output_template.md`，并从 `assets/output.html` 提取 `<style>` 作为唯一样式来源；非零退出码即视为失败，必须立即停止，不得进入保存诊断结果步骤，也不得由模型补齐或重写 HTML。
   2. 使用 ToolsList「上传 HTML 并获取 `npath`」输出渲染成功的 HTML 文件；必须从返回结果中提取 `path` 字段值作为 `npath`。严禁跳过此步骤直接传入本地文件路径。
   3. 仅当已获得 HTML 文件 `npath` 后，才允许使用 ToolsList「保存诊断结果」保存诊断结果。调用前必须逐项完成以下自检，不满足任一项都不得执行命令：

      | # | 参数 | 正确值来源 | 常见错误（禁止） | ✅ |
      |:---:|:---|:---|:---|:---:|
      | 1 | `--objectApiName` | 固定值 `LeadsObj` | 写成 `LeadObj`、`Leads` 等变体 | ☐ |
      | 2 | `--objectId` | Workflow 第 1 步定位到的线索 `_id` | 写成线索名称、公司名 | ☐ |
      | 3 | `--score` | Workflow 第 4 步 `Scoring_Result` 中的综合得分（数字字符串，如 `"35.05"`） | 写成评级字母、百分比符号 | ☐ |
      | 4 | `--summary` | **Workflow 8.2 `render_content` 返回的 `npath`**（格式如 `N_202607_23_xxxxxxxx`） | 评级文本、本地路径、`file://` URL、HTML 文本内容 | ☐ |
      | 5 | `--insightRating` | Workflow 第 4 步 `Scoring_Result` 中的评级字母（如 `"A"` / `"B"` / `"C"` / `"D"`） | `npath`、中文评级（如 `"C级"`） | ☐ |

### 回滚与重试

- 远端业务洞察文档读取（Workflow 第 5、7 步）失败时：不重试，直接降级到本地 `references/` 文件。
- 线索详情查询（Workflow 第 1 步）失败时：重试 1 次，最多 2 次；仍失败则提示“无法访问该线索记录”并终止。
- 卖方行业配置读取（Workflow 第 3 步）失败时：不重试，`SELLER_INDUSTRY` 置空并继续执行。
- HTML 渲染脚本（Workflow 第 8.1 步）失败时：不重试，不输出 HTML，也不调用保存命令。
- `render_content` 或 `save_diagnosis`（Workflow 第 8.2~8.3 步）失败时：各重试 1 次；仍失败则明确说明失败原因，不得声称已保存成功。

## Output

### 交付载体

以 Markdown 输出线索诊断正文。优先使用 Workflow 第 7 步复用或获取到的远端模板；远端模板不可用时使用 `references/output_template.md`。如用户明确需要 HTML 诊断，再按 Workflow 第 8 步串行生成并保存 HTML 诊断结果。

### 交付方式

- 默认直接在对话中展示 Markdown 诊断正文。
- 仅当用户明确需要 HTML 诊断时，执行 HTML 渲染、上传与保存流程；若任一步失败，保留 Markdown 结果并明确说明 HTML 未生成或未保存。

### 最小输出结构

1. 概要：线索名称、诊断日期、系统阶段、`AI_Stage`、综合评分、综合评级、需求描述。
2. 核心诊断结论：一句话结论、转化三要素、核心跟进策略、关键行动项。
3. 全局诊断结果：选定评分来源返回的综合得分，以及按 `Scoring_Result.dimension` 原样顺序展开的每个评分维度、分数和评分依据。
4. 关键缺失项、跟进策略与跟进建议：缺失项表、策略裁决、当前打法 vs 建议打法、`P0 / P1 / P2` 动作建议。

### 验收标准

- 诊断正文必须以 `Scoring_Result` 为主骨架，不得只复述总分或评级。
- `AI_Stage` 必须包含系统阶段、系统状态、AI 判定阶段、阶段结论和一句可追溯说明。
- 关键判断必须区分已知事实、判断结论和待确认问题；不能把经验推断写成 CRM 已证实事实。
- HTML 保存链路只有在脚本渲染成功且已获得 `npath` 时才允许执行。

## Edge Cases

### 降级模式

进入降级须显式说明可信度影响并列出需补齐项。降级仅适用于评分不完整、阶段信息不足、线索数据不足或卖方行业缺失；不适用于缺少 `Scoring_Result`。

- `Scoring_Result` 缺失或来源无法确认：先执行 `get_profile_score --objectApiName LeadsObj`；CLI 不可用时执行 `sfa-leads-score`。两者均不可用才阻断。
- 仅有总分：标注解释性不足，只输出整体健康度概览，不做高置信根因判断。
- 有维度分但缺评分依据或特征原值：做方向性判断，标注解释性受限，不把低分当已证实事实。
- 阶段证据不足：`AI_Stage` 输出“信息不足”，保留系统阶段或状态原值；不得阻断诊断或把系统字段直接写成真实阶段。
- 线索数据不足：概要标注信息不足，允许输出信息缺口型风险。

评分不完整时，风险识别只能输出保守型或信息缺口型风险，不得输出高置信根因型风险。

- 输出模板不可用：按 Output 的四部分最小结构输出。
- 远端 knowhow 全部不可用：使用 `references/flow.md`、`references/global-diagnosis-criteria.md` 与 `references/output_template.md` 兜底，并显式说明解释深度降低。

## Boundaries

- 评分来源优先级固定为：先查询 `get_profile_score --objectApiName LeadsObj`，返回同一线索的非空可用结果时直接消费；仅在 CLI 失败、为空、无评分信息或对象不匹配时回退 `sfa-leads-score`。不自行计算评分；全局诊断必须动态沿用所选来源返回的 `dimension` 名称、顺序、分数和依据，不得固定套用七问、三要素或其他预设维度。`AI_Stage` 必须根据本 skill 查询到的线索数据直接判断，不接受 `sfa-business-score` 或其他通用评分结果作为替代。
- 只消费本目录线索 knowhow，不加载客户或商机 knowhow。
- `flow.md`、`output_template.md`、`global-diagnosis-criteria.md` 与 `data-query.md` 不得覆盖主文件硬约束。线索风险识别、阶段不达标推进动作与跟进策略标准统一内聚在 `global-diagnosis-criteria.md`。
- 除执行流程指定的 `sharecrm sales profile save_diagnosis` 外，不做其他 CRM 写回；未完成 HTML 渲染并获得保存命令所需 `npath` 前，禁止调用保存命令。

## Forbidden Tools

本 skill 执行期间，以下工具**绝对禁止使用**。Agent 在工具选择阶段必须优先检查本清单，命中即阻断，不得以任何理由调用：

| 禁止工具 | 禁止原因 | 正确替代 |
|:---|:---|:---|
| `biz_object_memory` | 该工具将内容写入对象的通用 memory 字段，不是诊断专用通道，无法关联 `npath`、评分等诊断元数据 | `sharecrm sales profile save_diagnosis`（Workflow 8.3） |
| 任何形式的直接 CRM 写回（`data-add`、`data-edit`、`record update`、`record create` 等） | 本 skill 是只读诊断 skill，唯一允许的写操作是 Workflow 8.3 的 `save_diagnosis` | 无。如需回写线索字段，应退出本 skill 使用对应工具 |

## References

`references/` 必须包含以下文件，按加载条件读取：

- `references/data-query.md`：Workflow 第 2~3 步加载，定位线索并查询线索主数据、特征、销售记录、卖方行业配置。
- `references/global-diagnosis-criteria.md`：Workflow 第 5 步远端诊断标准不可用时加载，按 `output_template.md` 章节顺序提供全局诊断、关键缺失项、跟进策略、风险识别与行动建议标准；是诊断标准，不是对象事实。
- `references/flow.md`：Workflow 第 5 步远端诊断流程不可用时加载，提供内部分析视角（洞察 / 画像 / 推进）与执行顺序，只编排不放宽硬约束。
- `references/output_template.md`：Workflow 第 7 步远端诊断输出模板不可用时加载，提供最终 Markdown 输出结构与字段；只约束呈现，不改变结论与硬约束。

## Scripts

- `scripts/build-html-report.py`：Workflow 第 8 步唯一 HTML 渲染入口。
  - 入参：`--markdown <markdown>`（Workflow 第 7 步产出的诊断 Markdown 原文）、`--input <path>`（兼容文件输入）、`--output <html>`（缺省写 stdout）、`--schema` 打印 Markdown 结构提示；未传 `--markdown` / `--input` 时从 stdin 读取。
  - 行为：先按 `references/output_template.md` 固定结构校验并解析 Markdown；再读取 `assets/output.html` 的 `<style>` 作为唯一样式来源；最后输出完整 HTML。
  - 退出码：Markdown 结构校验失败、样式文件缺失均以退出码 1 终止；调用方必须在失败时停止流水线，不得手工拼接 HTML。

## Related Skills

| 关系 | Skill | 接口契约 | 触发场景 |
| --- | --- | --- | --- |
| 首选评分来源 | `get_profile_score` | 使用 `objectApiName=LeadsObj` 查询同一线索；结果非空且可用时直接消费，并保留其维度、得分、评级和依据 | 任何线索诊断前 |
| 回退评分来源 | `sfa-leads-score` | 仅在 `get_profile_score` 失败、为空、无评分信息或对象不匹配时使用，其结果成为 `Scoring_Result` | CLI 不可用时 |
| 下游 | `sfa-leads-convert` | 当 `AI_Stage` 判定为 SQL 且满足转商机标准时，由该 skill 执行转商机 | 诊断建议进入转化推进时 |
| 互斥 | `sfa-biz-router` | 本 skill 不调用、不引用 `sfa-biz-router`；`AI_Stage` 必须由本 skill 直接判断 | 全程 |
| 通用工具（仅线索写回场景） | `data-add` / `data-edit` | 本 skill 只允许 `save_diagnosis` 写入；如需回写线索字段，应退出本 skill | 仅字段更新场景 |
