---
name: "sfa-account-diagnosis"
description: "当用户需要对一个客户（`AccountObj`）进行经营洞察/诊断/客户画像/如何经营/下一步经营建议时，输出客户当前状态、真实关注点、组织突破口、增长空间与下一步经营建议时，应使用此 skill。如生成 HTML 报告，需按流程保存诊断结果。"
apiName: "sfa_account_diagnosis"
---
# sfa-account-diagnosis

## Goal
对一个明确的客户（`AccountObj`）按统一框架输出可解释、可执行的客户经营洞察结果。仅使用本目录客户经营洞察框架，不加载其他对象诊断 knowhow。

### 成功标准

- 已确认单一 `AccountObj`、同一客户的可用 `Scoring_Result` 和 CRM 事实。评分优先使用 `get_profile_score`；仅当 CLI 结果不可用时回退 `sfa-account-score`。
- 每项诊断判断可追溯到评分依据、CRM 事实或明确标注的待确认信息。
- 交付固定经营洞察结构；仅在用户确认后生成 HTML 并保存诊断结果。
- 不自行计算评分、不调用通用路由；仅在 `get_profile_score` 不可用时回退对应的 `sfa-account-score`。

**权威层级（冲突时从高到低）：**

1. 本 `SKILL.md` 的硬约束（对象边界、评分前置、评分驱动判断、Markdown 输出、概要简洁）最高，任何文件不得放宽或覆盖。
2. 本目录 `references/` 中的客户 knowhow，是洞察标准、流程编排与输出结构的内容来源：`flow.md`、`output_template.md`、`global-diagnosis-criteria.md`、`data-query.md`。客户真实关注点、组织突破口、增长空间、经营建议与经营风险提示等分章节诊断标准统一内聚在 `global-diagnosis-criteria.md`。

对象已明确是客户时优先用本 skill，不回退通用入口。

## WhenToUse

**适合这些表达：**

- 帮我洞察这个客户
- 诊断一下这个客户当前状态
- 帮我生成这个客户的画像
- 这个客户值不值得继续投入
- 下一步怎么经营这个客户
- 这个客户还有没有扩展空间

**不适合这些表达：**

- 只提取字段或回填对象 → 使用 `data-add` / `data-edit`
- 只做 knowhow 查询，不需要对象级判断 → 使用知识查询类 skill
- 只做会议总结或文本润色 → 不触发本 skill
- 对象不是客户 → 使用对应对象的诊断 skill

**边界条件：**

- 客户名称无法定位到唯一 `AccountObj` → 阻断并要求补充明确客户标识。
- 多客户同时诊断 → 不支持；每次仅处理一个客户。
- 客户数据严重不足 → 允许输出信息缺口型风险，但不得输出高置信根因判断。
- `Scoring_Result` 缺失、来源不明或与当前客户不匹配 → 先查询 `get_profile_score`；CLI 不可用时回退 `sfa-account-score`，两者均不可用才阻断。

## Inputs

| 输入 | 作用 | 必填 | 来源 / 缺失处理 |
|:---|:---|:---:|:---|
| `object_id` + `Object_Type=AccountObj` | 直接定位客户对象 | 是（与客户名称二选一） | 已给 `object_id` 时直接查询并验证对象类型；若对象不是客户则停止。 |
| 客户名称 | 归一为唯一客户 ID | 是（与 `object_id` 二选一） | 仅给名称时先查候选；未命中或多候选无法确认时阻断并要求用户补充。 |
| `Scoring_Result` | 评分驱动客户当前状态、经营风险和增长判断 | 是 | 首先查询 `get_profile_score`（`objectApiName=AccountObj`）并消费同一客户的非空可用结果；CLI 失败、为空、无可用评分信息或对象不匹配时，回退 `sfa-account-score`。两者均不可用才阻断。 |
| `sfa-account-due-diligence-report` 结构化结果 | 作为外部情报增强层，补齐客户基础画像、当前业务重点与扩展空间判断 | 是（默认编排） | 必须在评分完成后、诊断输出前编排调用；可由调用方直接传入。未传入时，本 skill 必须按客户名称通过 `read_skill` 调用 `sfa-account-due-diligence-report` 获取结构化结果，不得以流程较长或不影响核心输出为由跳过。调用失败时不阻断，仅降低 A / D / F 三类判断的解释深度。 |
| 业务补充事实 | 补充 CRM 中不可见但用户明确提供的事实 | 否 | 可用于辅助判断；不得覆盖 CRM 已查事实，不得替代评分。 |

### 信息不足处理

- 用户既未提供 `object_id` 也未提供客户名称时，直接提示“缺少诊断对象，无法执行诊断”并终止。
- 用户提供客户名称但无法归一到唯一客户时，展示候选并等待澄清；仍无法确认时终止。
- `Scoring_Result` 缺失、来源不明或与当前客户不匹配时，先按评分来源优先级查询 CLI，再回退 `sfa-account-score`；两者均不可用时阻断，不做降级诊断。
- `sfa-account-due-diligence-report` 缺失时必须先编排调用；调用失败可降级继续，但必须标注“外部情报增强缺失”。

## ToolsList

| 用途 | CLI 命令 | 关键参数 |
| --- | --- | --- |
| 远端客户经营洞察文档 | `sharecrm sales profile fast-query-document --data '{"scene":"business_insight","coreTopics":"<检索主题>"}'` | `scene` 固定为 `business_insight`；`coreTopics` 为 `客户经营洞察流程` / `客户经营洞察标准` / `客户经营洞察输出模板`。 |
| 按名称定位客户 | `sharecrm data record query-id-by-name --data '{"query":"<客户名称>","apiNames":["AccountObj"]}'` | `query` 为客户名称；`apiNames` 固定为 `["AccountObj"]`。 |
| 名称归一化兜底查询 | `sharecrm data record query-by-name --data '{"object_api_names":["AccountObj"],"name":"<客户名称或关键词>"}'` | `object_api_names` 固定为 `["AccountObj"]`；`name` 为客户名称或关键词。 |
| 获取客户详情 | `sharecrm data record get-by-id --object_api_name AccountObj --id <account_id>` | `object_api_name` 固定为 `AccountObj`；`id` 为客户记录 ID。 |
| 获取字段描述 | `sharecrm data describe get --data '{"object_api_name":"AccountObj","simple_describe":true}'` | `object_api_name` 固定为 `AccountObj`；`simple_describe` 固定为 `true`。 |
| 按字段查询客户、联系人、商机或销售记录 | `sharecrm data record query-by-fields --data '{"object_api_name":"<对象ApiName>","select_fields":["<字段1>","<字段2>"],"filters":[{"field_api_name":"<字段ApiName>","operator":"EQ","values":["<值>"]}],"orders":[{"field_api_name":"<排序字段>","is_asc":false}],"limit":<数量>}'` | `object_api_name`、`select_fields`、`filters`、`orders`、`limit` 按 `references/data-query.md` 设置。 |
| 查询客户评分 | `sharecrm sales profile get_profile_score --objectApiName AccountObj --objectId <account-id>` | 优先消费同一客户的非空可用 CLI 结果；失败、为空、无评分信息或对象不匹配时，回退 `sfa-account-score`。 |
| 保存诊断结果 | `sharecrm sales profile save_diagnosis --objectApiName AccountObj --objectId <客户id> --score "<评分>" --summary <npath> --insightRating "<评级>"` | 仅允许在 HTML 渲染成功并拿到 `npath` 后执行。 |

## Output

### 交付载体

以 Markdown 输出客户经营洞察正文。优先使用 Workflow 第 7 步复用或获取到的远端模板；远端模板不可用时使用 `references/output_template.md` 本地兜底模板。

### 交付方式

- 默认以 Markdown 直接在对话中展示客户经营洞察结果。
- 仅当用户明确要求 HTML 报告时，才通过 `scripts/build-html-report.py` 生成 HTML，并按 Workflow 第 8 步保存诊断结果。

### 最小输出结构

输出必须围绕已评分客户形成可解释、可执行的经营判断，至少覆盖以下部分：

1. 页头摘要：客户名称、当前状态、评分总分、评分结论、本轮洞察主题。
2. 客户当前状态：严格按选定 `Scoring_Result.dimension` 的名称、顺序和分数展开，并结合客户事实明确事实、判断和待确认点；不得固定套用客户价值、关系温度等预设维度。
3. 客户真实关注点：客户表面关注点、深层驱动、当前约束和我方当前错位。
4. 组织突破口：入口条线、杠杆角色、拍板关键、隐性阻力和推荐突破路径。
5. 增长空间：当前主机会、扩展方向、复制可能性与是否值得继续投入。
6. 经营建议：经营策略和关键动作。
7. 经营风险提示：按 `P0/P1/P2` 列出风险点、来源、影响和优先化解方向。

### 兜底输出示例

当远端模板和本地模板都不可用时，按以下最小结构输出：

```markdown
# 客户经营洞察：{客户名称}

## 页头摘要
- 客户名称：{name}
- 当前状态：{状态描述}
- 评分总分：{score}
- 评分结论：{结论}
- 本轮洞察主题：{主题}

## 一、客户当前状态
{基于评分维度和客户事实的状态判断，标注事实 / 判断 / 待确认问题}

## 二、客户真实关注点
{表面关注点、深层驱动、当前约束、当前错位}

## 三、组织突破口
{当前入口条线、杠杆角色、拍板关键、隐性阻力、推荐突破路径}

## 四、增长空间
{当前主机会、潜在扩展方向、复制可能性、是否值得追加投入}

## 五、经营建议
{经营策略 + 关键动作}

## 附：经营风险提示
| 优先级 | 风险点 | 来源 | 影响 | 优先化解方向 |
|:---:|:---|:---|:---|:---|
| P0 | ... | ... | ... | ... |
```

### 验收标准

- 最终输出必须是 Markdown，除非用户明确要求 HTML 派生交付。
- 使用远端模板时遵循其结构；使用本地或兜底结构时必须覆盖七个最小输出部分。
- 页头摘要必须保持摘要式表达，不拆成完整诊断章节。
- 风险提示只能作为附加提醒，不替代主判断章节。

如用户明确需要 HTML 报告，额外通过 `scripts/build-html-report.py` 从 Markdown 洞察正文渲染 HTML 文件；脚本失败时不输出 HTML，不由模型手工拼接。HTML 渲染阶段只允许执行脚本并读取退出码 / stderr 摘要，禁止把 `scripts/build-html-report.py` 或 `assets/output.html` 全文读入模型上下文。保存诊断结果必须严格发生在 HTML 脚本渲染成功、且通过 `render_content` 获得 HTML 文件 npath 之后；未拿到 npath 前，禁止调用 `sharecrm sales profile save_diagnosis`。

## 意图路由

| 意图 | 示例 | 输出部分 |
| --- | --- | --- |
| 洞察（默认） | 帮我洞察这个客户 / 诊断当前状态 | 页头摘要 + 五个经营判断模块 + 风险提示 |
| 生成画像 | 帮我生成这个客户的画像 | 页头摘要 + 客户当前状态 + 客户真实关注点 |
| 下一步怎么跟 | 下一步怎么经营 / 怎么跟 | 组织突破口 + 增长空间 + 经营建议 |

## Workflow

洞察结果固定结构为：页头摘要、客户当前状态、客户真实关注点、组织突破口、增长空间、经营建议，以及附加的经营风险提示。

1. 定位客户并验证 `Object_Type=AccountObj`。定位优先级：①已给 `object_id` 直接定位；②只给名称则归一为唯一 ID；③无 ID 无名称则阻断“缺少诊断对象，无法执行诊断”；④定位结果非客户则停止并提示改用对应对象诊断 skill。
2. 按 `references/data-query.md` 与当前意图查询客户数据（字段、特征、销售记录）。
3. 优先检查是否已提供 `sfa-account-due-diligence-report` 的结构化结果；若未提供，必须通过 `read_skill` 调用仓库中的 `sfa-account-due-diligence-report` skill，并按当前客户名称获取客户尽调结构化结果。只消费其与客户经营洞察相关的结构化结果，不展开完整尽调报告正文。不得以流程较长、结果只是增强项或不影响核心输出为由跳过本次编排。若尽调调用失败、无权限、无结果或返回不完整，不阻断本 skill，仅标注“外部情报增强缺失”，继续基于 CRM 与评分结果输出。
4. 查询并校验当前客户的 `Scoring_Result`。首先执行 `sharecrm sales profile get_profile_score --objectApiName AccountObj --objectId <account-id>`；若返回同一 `AccountObj` 的非空可用综合得分、评级或至少一个维度，直接消费其结果，保留维度名称、顺序、得分和依据，并记录评分来源为“CLI”，不得调用 `sfa-account-score`。若 CLI 失败、返回空结果、无可用评分信息或无法确认对象一致，则回退 `sfa-account-score` 对同一客户评分，记录来源为“sfa-account-score 回退”；仅当回退也不可用时才阻断。本 skill 不自行计算评分，也不接受 `sfa-object-score` 或其他通用评分结果替代。随后直接基于本次客户数据生成 `AI_Stage`，不得调用、引用或要求调用 `sfa-biz-router`：
   - 读取客户主数据的 `deal_status`，并保留 API 值与显示值作为系统经营状态锚点；字段缺失时如实标注缺失。
   - 结合关联商机的阶段/状态、近期销售记录、联系人覆盖和最近跟进，判断客户处于“合作维护 / 经营活跃 / 扩展推进 / 风险或待激活 / 信息不足”之一。已成交状态本身不等于经营活跃；仅存在商机记录也不等于客户已形成扩展机会。
   - `AI_Stage` 必须包含：`系统经营状态`（`deal_status`）、`AI判定经营状态`、`阶段结论`（仅可为“客户经营状态与 deal_status 基本一致 / deal_status 偏粗 / 存在活跃商机但客户状态偏旧 / 信息不足”之一）和一句可追溯的判断说明。
   - 只有销售记录或关联商机显示近期、可验证的客户侧推进时，才输出“经营活跃”或“扩展推进”；联系人、销售记录和在跑商机证据不足时输出“信息不足”，不得把 CRM 状态字段直接写成真实经营状态。
5. 使用 ToolsList「远端客户经营洞察文档」查询 `scene="business_insight"`、`coreTopics="客户经营洞察流程"`，并按其内部分析视角与执行顺序生成各部分洞察。保留返回的 `dataList` / `contentText`，后续步骤先检查并复用其中已包含的诊断标准或输出模板；远端执行失败、无结果、返回空内容或不可用时，读取 `references/flow.md` 作为本地兜底流程。

   生成客户经营洞察时，先检查本步骤返回内容是否已包含诊断标准。若已包含，直接复用第 5 步返回的诊断标准；若未包含，使用 ToolsList「远端客户经营洞察文档」查询 `coreTopics="客户经营洞察标准"`。
   若实际调用本步骤的远端诊断标准，保留该命令返回的 `dataList` / `contentText`，供执行流程第 7 步复用；远端执行失败、无结果、返回空内容或不可用时，读取 `references/global-diagnosis-criteria.md` 作为本地兜底诊断标准。按诊断流程加载所需 knowhow 与模板：
   - **页头摘要**为摘要式，不拆「事实 / 判断 / 待确认问题」。
   - **客户当前状态**以评分维度为主骨架，逐项结合维度分、评分依据、客户事实与 knowhow；必须解释“为什么是这个判断”并落回数据/销售记录/评分依据，不只复述分数。
   - **客户真实关注点**要回答客户表面关注点、深层驱动、当前约束和我方当前错位。
   - **组织突破口**要回答当前入口条线、杠杆角色、拍板关键、隐性阻力和推荐突破路径。
   - **增长空间**要回答当前主机会、扩展方向、复制可能性与是否值得追加投入。
   - **经营建议**要先给经营策略，再给关键动作。
   - **经营风险提示**按 `P0/P1/P2` 输出，作为经营判断的附加提醒，而不是主章节。
6. 使用第 5 步获得或兜底的客户经营洞察流程与诊断标准完成正文判断；若仅获得本地兜底资料，需显式说明远端 knowhow 不可用导致解释深度降低。
7. 先检查 Workflow 第 5 步已调用的远端文档返回内容是否包含诊断输出模板。若任一返回已包含，直接复用其中的输出模板；若均未包含，使用 ToolsList「远端客户经营洞察文档」查询 `coreTopics="客户经营洞察输出模板"`，并按模板要求组织为 **Markdown**（与硬约束冲突以本文件为准）。
   远端执行失败、无结果、返回空内容或不可用时，读取 `references/output_template.md` 作为本地兜底模板。
8. Markdown 洞察正文完成后，追加一句明确询问：是否需要进一步生成 HTML 报告；若需要，按以下四步**串行执行**，不得跳步、并行或调整顺序，**禁止模型直接拼接 HTML**：
   1. **脚本渲染（唯一入口）**：执行 `python scripts/build-html-report.py --markdown "$DIAGNOSIS_MARKDOWN" --output tmp/account_diagnosis_report.html`，其中 `$DIAGNOSIS_MARKDOWN` 必须是第 7 步产出的完整 Markdown 原文；脚本会校验 Markdown 结构是否符合 `references/output_template.md`，并从 `assets/output.html` 提取 `<style>` 作为唯一样式来源（**禁止使用样式文件里的数据**）；脚本以非零退出码失败时必须立即停止流水线，不得进入保存诊断结果步骤，不得由模型补齐或重写 HTML。执行前后禁止读取 `scripts/build-html-report.py` 或 `assets/output.html` 全文；失败时只回填退出码与必要的 stderr 摘要。
   2. **获取 npath（必须在 8.1 成功之后）**：将渲染成功的 HTML 文件通过 `render_content` 工具输出，**系统会自动上传文件到文件服务并返回 npath**。从 `render_content` 返回结果中提取 `path` 字段值（即 npath），作为后续保存诊断的唯一文件标识。严禁跳过此步骤直接传入本地文件路径。
   3. **保存诊断结果（必须在 8.2 成功之后）**：仅当已获得 HTML 文件的 npath 后，才允许调用 `sharecrm sales profile save_diagnosis --objectApiName AccountObj --objectId <客户id> --score "<评分>" --summary <npath> --insightRating "<评级>"` 保存诊断结果。`--summary` 参数值必须是 npath，严禁传入本地文件路径、file:// URL 或 HTML 文本内容。严禁在生成 HTML 前、脚本失败后、或仅有 Markdown 正文时调用保存命令；保存命令失败时必须向用户说明失败原因，不得声称已保存成功。
      **调用前强制自检（必须逐项确认后才能执行命令）：**
   | # | 参数 | 正确值来源 | 常见错误（禁止） | ✅ |
   |:---:|:---|:---|:---|:---:|
   | 1 | `--objectApiName` | 固定值 `AccountObj` | 写成 `Account` 等变体 | ☐ |
   | 2 | `--objectId` | Workflow 第 1 步定位到的客户 `_id` | 写成客户名称 | ☐ |
   | 3 | `--score` | Workflow 第 4 步 `Scoring_Result` 中的综合得分（数字字符串，如 `"35.05"`） | 写成评级字母、百分比符号 | ☐ |
   | 4 | `--summary` | **Workflow 8.2 `render_content` 返回的 npath**（格式如 `N_202607_23_xxxxxxxx`） | ❌ 评级文本（如 `"C级"`）❌ 本地路径（如 `/tmp/xxx.html`）❌ HTML 内容 | ☐ |
   | 5 | `--insightRating` | Workflow 第 4 步 `Scoring_Result` 中的评级字母或者数字（如 `"A"`/`"B"`/`"C"`/`"D"`） | ❌ npath ❌ 中文评级（如 `"C级"`） | ☐ |

### 回滚与重试

- 远端客户经营洞察文档查询（Workflow 第 5、7 步）失败时：不重试，直接回退到本地 `references/` 文件。
- `sfa-account-due-diligence-report` 编排调用失败时：不重试，标注“外部情报增强缺失”并继续输出降级洞察。
- HTML 渲染脚本失败时：不重试，不进入保存诊断结果步骤，仅返回 Markdown 正文并说明 HTML 生成失败。
- `save_diagnosis` 失败时：不重试，明确说明保存失败原因，不得声称已保存成功。

## 降级规则

进入降级须显式说明对可信度的影响并列出需补齐项。降级适用于评分不完整、阶段证据不足或客户数据不足，**不适用于完全未评分**。

- `Scoring_Result` 缺失或来源无法确认：先执行 `get_profile_score --objectApiName AccountObj`；CLI 不可用时执行 `sfa-account-score`。两者均不可用才阻断。
- 仅有总分：标注解释性不足，只输出整体健康度概览，不做高置信根因判断。
- 有维度分缺评分依据/特征原值：做方向性判断，标注解释性受限，不把低分当已证实事实。
- 阶段证据不足：`AI_Stage` 输出“信息不足”，保留 `deal_status` 原值；不得阻断洞察或把系统经营状态直接写成真实经营状态。
- `sfa-account-due-diligence-report` 编排调用失败：标注“外部情报增强缺失”，A / D / F 三类判断仅基于 CRM 与评分事实保守输出。未调用不属于流程降级，不得跳过调用。
- 客户数据不足：页头摘要标注信息不足，允许输出信息缺口型风险。

评分不完整时风险识别只能输出保守型或信息缺口型风险，不得输出高置信根因型风险。

## Boundaries

- 评分来源优先级固定为：先查询 `get_profile_score --objectApiName AccountObj`，返回同一客户的非空可用结果时直接消费；仅在 CLI 失败、为空、无评分信息或对象不匹配时回退 `sfa-account-score`。不自行计算评分；全局判断必须动态沿用所选来源返回的 `dimension` 名称、顺序、分数和依据，不得固定套用客户价值、关系温度或其他预设维度。`AI_Stage` 必须根据本 skill 查询到的客户数据直接判断，不调用 `sfa-biz-router`。不接受 `sfa-object-score` 或其他通用评分结果作为替代。
- 可直接编排调用仓库中的 `sfa-account-due-diligence-report` 作为外部情报增强层，但只消费与本 skill 相关的结构化结果，不替代 CRM 主数据与评分结论。
- 只消费本目录客户 knowhow，不加载线索、商机或通用业务诊断 knowhow。
- HTML 报告生成成功后必须保存诊断结果；除执行流程指定的 `sharecrm sales profile save_diagnosis` 外，不做其他 CRM 写回；未完成 HTML 渲染并获得保存命令所需 npath 前，禁止调用保存命令。
- 默认最终输出必须是 Markdown；HTML 仅作为用户明确要求时的派生交付，且必须通过 `scripts/build-html-report.py` 从本次 Markdown 正文渲染，不得模型手工拼接，不得复用样式文件示例数据，不得为生成或调试 HTML 而读取脚本或样式文件全文；HTML 成功生成并获得保存命令所需 npath 后，才允许调用 `sharecrm sales profile save_diagnosis` 保存诊断结果。

## Forbidden Tools

本 skill 执行期间，以下工具**绝对禁止使用**。Agent 在工具选择阶段必须优先检查本清单，命中即阻断，不得以任何理由调用：
| 禁止工具 | 禁止原因 | 正确替代 |
|:---|:---|:---|
| `biz_object_memory` | 该工具将内容写入对象的通用 memory 字段，不是诊断专用通道，无法关联 npath、评分等诊断元数据 | `sharecrm sales profile save_diagnosis`（Workflow 8.3） |
| 任何形式的直接 CRM 写回（`data-add`、`data-edit`、`record update`、`record create` 等） | 本 skill 是只读诊断 skill，唯一允许的写操作是 Workflow 8.3 的 `save_diagnosis` | 无。如需回写线索字段，应退出本 skill 使用对应工具 |

## Related Skills

| Skill | 关系 | 说明 |
|:---|:---|:---|
| `get_profile_score` | 首选评分来源 | 使用 `objectApiName=AccountObj` 查询同一客户；结果非空且可用时直接消费，并保留其维度、得分、评级和依据。 |
| `sfa-account-score` | 回退评分来源 | 仅在 `get_profile_score` 失败、为空、无评分信息或对象不匹配时使用，其结果成为 `Scoring_Result`。 |
| `sfa-account-due-diligence-report` | 编排调用 | 作为外部情报增强层，在评分完成后、诊断输出前调用；调用失败不阻断。 |
| `sfa-biz-router` | 明确不调用 | `AI_Stage` 必须由本 skill 基于当前查询结果直接判断。 |
| `sfa-object-score` | 明确不接受 | 其通用评分结果不能替代本 skill 要求的 `Scoring_Result`。 |
| `data-add` / `data-edit` | 互斥 | 本 skill 默认只读；除 Workflow 8.3 的 `save_diagnosis` 外不做 CRM 写回。 |

## References

- `references/data-query.md`
- `references/global-diagnosis-criteria.md`
- `references/flow.md`
- `references/output_template.md`

## Scripts

- `scripts/build-html-report.py`：执行流程第 8 步唯一 HTML 渲染入口。
  - 入参：`--markdown <markdown>`（第 7 步产出的完整 Markdown 原文）、`--input <path>`（兼容文件输入）、`--output <html>`（缺省写 stdout）、`--schema` 打印 Markdown 结构提示；未传 `--markdown/--input` 时从 stdin 读取。
  - 行为：先按 `references/output_template.md` 固定结构校验并解析 Markdown；最后输出完整 HTML。
  - 退出码：Markdown 结构校验失败、样式文件缺失均以退出码 1 终止；调用方必须在失败时停止流水线，不得手工拼接 HTML。
  - Token 约束：调用方只执行脚本，不读取脚本源码或 `assets/output.html` 全文；失败排查只消费 stderr 摘要和必要的结构校验信息。
