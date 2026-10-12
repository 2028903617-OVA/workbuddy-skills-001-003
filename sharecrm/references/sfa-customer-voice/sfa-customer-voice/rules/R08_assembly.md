# R08 报告组装与开放问题

## ⚠️ 输出完整性强制规则（最高优先级）

以下规则凌驾于所有其他格式规则之上，必须严格执行：

1. **必须完整输出所有章节正文**：报告必须包含选定模板的全部一级目录和子章节的**完整正文内容**，禁止只输出摘要表格后跳过正文。
2. **禁止占位短语**：严禁输出"完整报告文件已生成""完整报告文件：""详见附件""报告正文略""详细内容请查看..."等任何替代正文的短语。报告正文必须在当前回复中直接完整呈现。
3. **一次交互完整输出**：所有章节必须一次连续输出完毕，不得将报告拆分为"摘要+详细"两次回复，也不得在正文前添加自创的"五步结构总览表""核心发现速览""关键结论"等整体性摘要表格来替代正文。
4. **严格遵循模板结构**：必须按本文件定义的章节顺序和标题逐字输出，不得自行增减一级目录、合并章节或改变章节顺序。
5. **每个结论必须有证据**：正文中的每个结论、判断、指标、动作必须附带统计数字、客户分布或原始语录，禁止只写结论不写证据。
6. **严禁使用旧结构**：旧版格式（一级目录为"结论摘要/声音范围与样本/高频声音主题/趋势变化/角色视角归因/代表性客户原文/风险与机会/建议动作/开放问题"）是已废弃的 v1 格式，**在任何情况下都不得使用**，包括但不限于 HTML 输出、Markdown 输出或任何视角输出。当前唯一合法的一级目录结构来自本文件定义的两种模板（VOC 五步闭环 / 经典六章升级）。
7. **报告末尾必须输出引导语**：报告正文输出完毕后，最后一行必须追加：`💡 如需针对特定维度（如痛点、竞品、不满）展开深度分析，或调整时间范围/人员范围重新生成报告，随时告知。输入「展开【维度名】」可查看该维度完整 5 卡片分析。`
8. **严禁编造（评审版新增）**：任何客户名、商机名、提及次数、情感判断、风险原因、客户反馈、行动建议的触发依据，必须来自输入数据。若证据不足，只能写“当前数据不足以支持判断”，不得补猜。
9. **评审版删除项必须生效**：标准报告中不得出现 `声音接收概览`、维度卡片评分/进度条/证据等级、独立 `采取行动（Act）` 章节、独立 `反馈闭环（Feedback）` 章节、`附录` 章节。

---

## 顺序输出检查清单（必须逐条执行，不可跳过）

> 生成报告时，必须按以下顺序逐条检查并输出。每完成一条，才能进入下一条。**禁止跳过任何条目。**

### VOC 评审版模板（report_template=voc_5step）

1. ✅ 输出页头（报告标题 + 元数据行）
2. ✅ 输出 `## 一、听见客户声音（Hear）`
3. ✅ 输出 `### 六维总览`（6 条一句话总结，非表格）
5. ✅ 输出 `## 二、理解客户声音（Understand）`
6. ✅ 输出 `### $APPEALS 八维分析`（8个维度卡片，固定三段式）
7. ✅ 输出 `### 风险/机会信号`（🔴风险/🟢机会，每条附证据）
8. ✅ 输出 `### 客户分层`（认可型/机会型/观望型/风险型）
9. ✅ 输出 `## 三、持续变革（Transform）`
10. ✅ 输出 `### 经营层结论`（2-4条，每条附证据，HTML 中使用带短标题的结论卡片）
11. ✅ 输出 `### 能力升级方向`（HTML 中输出卡片组，不使用表格）
12. ✅ 输出底部引导语（必须原文输出：`💡 如需针对特定维度（如痛点、竞品、不满）展开深度分析，或调整时间范围/人员范围重新生成报告，随时告知。输入「展开【维度名】」可查看该维度完整 5 卡片分析。`）

### 经典六章模板（report_template=classic_6chapter）

1. ✅ 输出页头（报告标题 + 元数据行）
2. ✅ 输出 `## 一、整体判断`（2-4个结论卡片）
3. ✅ 输出 `## 二、关注指标`（4-6个指标 + 关键声音问答）
4. ✅ 输出 `## 三、客户声音主题`（5-8个主题，五列表格）
5. ✅ 输出 `## 四、客户分层`（4种分层类型）
6. ✅ 输出 `## 五、管理动作`（4-6条动作表）
7. ✅ 输出 `## 六、经营层结论`（2-4条结论）
9. ✅ 输出底部引导语（必须原文输出：`💡 如需针对特定维度（如痛点、竞品、不满）展开深度分析，或调整时间范围/人员范围重新生成报告，随时告知。输入「展开【维度名】」可查看该维度完整 5 卡片分析。`）

---

## 目标

把 R01-R07 的结果组装成默认面向 管理层阅读的客户声音报告。支持三种输出模式（报告/Q&A/混合）和两种报告模板（VOC 五步闭环/经典六章），所有输出均为证据驱动格式——每个结论必须附统计、客户分布和可展开原始语录。

## 触发条件

完成前序规则后始终执行。

## 输入来源

- R01 声音范围识别（含 intent_type / interaction_mode / detected_user_dimension / report_template / output_format）
- R02 客户声音抽取
- R03 声音主题聚类（含 appeals_dimensions 标签）
- R04 趋势变化
- R05 角色/部门/人员视角归因
- R06 代表性客户原文
- R07 风险与机会
- R09 交互模式规则
- R10 $APPEALS 映射规则

## 输出模式分支

R08 根据 R01 输出的 interaction_mode 选择输出模式：

| interaction_mode | 输出模式 | 说明 |
|-----------------|---------|------|
| report | 报告模式 | 按 report_template 字段选择模板结构 |
| qa | Q&A 模式（分两步） | 按 R09 定义的分层渐进式输出 |
| report_with_qa | 报告模式 + 聚焦注释 | 报告格式，重点展开 qa_context 中关注的维度 |

## 报告模板选择

R08 根据 R01 输出的 report_template 选择报告结构：

| report_template | 报告结构 | 说明 |
|----------------|---------|------|
| voc_5step | VOC 评审版（**默认**） | 评审后结构：听见→理解→持续变革 |
| classic_6chapter | 经典六章升级 | 保留原六章名称，内容升级为证据驱动格式 |

**模板选择规则**：
- 用户未指定时，默认使用 `voc_5step`
- 用户可通过自然语言指定："用 VOC 五步结构出报告"→ voc_5step；"用经典六章结构出报告"→ classic_6chapter
- R01 识别用户输入中的模板关键词，写入 report_template 字段

## 输出格式选择

R08 根据 R01 输出的 `output_format` 选择输出格式：

| output_format | 说明 |
|--------------|------|
| markdown | 默认，纯 Markdown 文本 |
| html | 用户明确要求 HTML 时，输出完整 HTML 代码 |

**HTML 输出规则**：
- 仅当用户明确说"输出 HTML""生成 HTML""用 HTML 格式"等时才使用 HTML 格式
- HTML 输出必须严格遵循 `references/voc_report_template.html` 的 DOM 结构和 CSS 类名
- HTML 必须包含完整的 `<!DOCTYPE html>` `<html>` `<head>` `<body>` 结构
- HTML 中的 $APPEALS 维度卡片必须使用 `.appeals-dim-card` 类名，并按三段式输出
- HTML 中的风险/机会信号必须使用 `.signal-grid` 包裹，并使用 `.signal-risk` / `.signal-opportunity` 类名
- HTML 中的客户分层必须使用 `.tier-grid` 包裹，并使用 `.customer-tier` / `.tier-title` / `.tier-body` 类名
- HTML 中的持续变革结论必须使用 `.transform-grid` 包裹；每个结论卡片必须包含 `.conclusion-title`、`.conclusion-text`、`.conclusion-evidence`
- HTML 中的能力升级方向必须使用 `.upgrade-card-grid` 卡片组，不再使用表格
- HTML 页头必须使用浅蓝灰专业管理层样式，不得回退为深黑色头图
- HTML 输出不得省略任何章节，必须完整呈现与 Markdown 版同等的内容
- **HTML 禁止旧结构**：即使使用 HTML 格式，一级目录结构也必须使用 VOC 五步闭环（默认）或经典六章升级，严禁使用旧版"结论摘要/声音范围/高频主题..."结构生成 HTML

## 证据驱动通用规则

> **以下规则对两种报告模板均适用。**

- 每个结论、判断、指标、动作**必须附证据**，禁止只输出结论而无证据
- 证据格式统一为：`结论 + 统计（提及次数/客户数）+ 客户分布 + 可展开原始语录（含证据等级）`
- 原始语录按证据等级 E1→E4 排序，E1（客户原话）优先展示
- 统计数据必须包含：提及客户数/总客户数、提及率、情感分布
- $APPEALS 归属维度必须标注在每个结论/主题的动作依据中
- 样本量、时间范围、信息完整度、置信度保留在页头
- 证据、原文默认弱化展示（折叠/展开）；当用户要求"详细版""完整分析""附证据"时再全部展开

## 脱敏规则

> **默认规则**：默认输出**不脱敏**，保留所有真实信息，便于管理层直接识别客户和竞品。
> 仅对**内部系统/项目代号**进行脱敏。若客户后续需要启用脱敏，可在配置中自行设置。

| 信息类型 | 默认是否脱敏 | 处理方式 |
|---------|--------------|---------|
| 客户名称 | ❌ 不脱敏 | 保留真实客户名称，便于管理层直接识别 |
| 联系人姓名 | ❌ 不脱敏 | 保留真实联系人姓名 |
| 商机名称 | ❌ 不脱敏 | 保留真实商机名称 |
| 具体金额 | ❌ 不脱敏 | 保留真实金额（客户可自行配置是否脱敏） |
| 竞品名称 | ❌ 不脱敏 | 保留真实竞品名称，如 `Salesforce`、`华为云`、`阿里云` 等 |
| 产品名称 | ❌ 不脱敏 | 保留真实产品名称 |
| 内部系统/项目代号 | ✅ 必须脱敏 | 用 `项目A`、`系统X`、`代号Alpha`… 替代；此类信息为客户内部敏感信息 |

**客户自定义脱敏配置（预留）**：

若客户需要在输出中脱敏部分信息，可在技能配置中设置 `desensitization_rules` 字段，指定需要脱敏的字段列表。配置示例：

```yaml
desensitization_rules:
  enable: true
  mask_fields:
    - customer_name      # 客户名称 → 客户A/客户B
    - contact_name       # 联系人姓名 → 联系人A/联系人B
    - opportunity_name   # 商机名称 → 商机A/商机B
    - amount             # 具体金额 → 约XX万区间
    - competitor_name    # 竞品名称 → 竞品A/竞品B（一般不需开启）
    - product_name       # 产品名称 → 产品A/产品B（仅战略产品建议开启）
    - project_code       # 内部系统/项目代号 → 始终脱敏（默认开启）
```

> 当前版本默认 `enable: false`，即全部不脱敏。仅 `project_code` 类型始终脱敏。

---

## 报告输出顺序与结构

### 页头信息（两种模板通用，必须在正文前输出）

```markdown
# 客户声音报告 — {scope_label}

> 数据时间范围：{start_date} 至 {end_date}
> 分析视角：CEO/管理层
> 报告模板：VOC 五步闭环 / 经典六章
> 覆盖范围：{scope}
> 样本量：{sales_record_count} 条销售记录 / {meeting_count} 场会议 / {voice_item_count} 条声音
> 信息完整度：{information_completeness}
> 置信度说明：{confidence_note}
{聚焦注释：本报告重点展开【{dimensions}】维度（report_with_qa 模式专用）}
```

**页头之后必须立即开始输出一级目录正文，中间不得插入任何摘要表格或过渡语。**

---

### 模板 A：VOC 五步闭环（默认）

> 评审版结构：Hear → Understand → Transform。
> 必须按以下3个一级目录顺序完整输出，标题逐字一致。

#### `一、听见客户声音（Hear）`

**目标**：回答「我们听到了什么？从哪里听到的？覆盖够不够？」

必须包含：
- **六维总览**：6条一句话总结，六维=痛点/期望/不满/认可/竞品/趋势
- **主要问题清单**：按提及频率排序列出 5 条最高频客户问题
- 每条总结必须包含：提及次数、核心内容、积极/消极判断、风险提示、风险原因
- 6条展示顺序固定为：`新需求（痛点）`、`不满`、`竞品`、`趋势`、`认可`、`期望`
- 不输出表格
- 不输出 `声音接收概览`

格式：
```markdown
## 一、听见客户声音（Hear）

### 六维总览

1. **新需求（痛点）**：共提及 {count} 次，核心聚焦 {core_message}，整体以 {positive_or_negative} 信号为主；当前主要风险是 {risk}，原因是 {risk_reason}。
2. **不满**：...
3. **竞品**：...
4. **趋势**：...
5. **认可**：...
6. **期望**：...

### 主要问题清单

1. **{问题分类1}**：{问题描述1}；（至少 {问题客户数1} 个客户累计提出 {问题次数1} 次）。
2. **{问题分类2}**：{问题描述2}；（至少 {问题客户数2} 个客户累计提出 {问题次数2} 次）。
3. **{问题分类3}**：{问题描述3}；（至少 {问题客户数3} 个客户累计提出 {问题次数3} 次）。
4. **{问题分类4}**：{问题描述4}；（至少 {问题客户数4} 个客户累计提出 {问题次数4} 次）。
5. **{问题分类5}**：{问题描述5}；（至少 {问题客户数5} 个客户累计提出 {问题次数5} 次）。
```

#### `二、理解客户声音（Understand）`

**目标**：回答「客户在说什么？意味着什么？风险和机会在哪里？」

**核心变更（评审版）**：本章节使用 **$APPEALS 八维分析卡片** 作为核心展示方式。每个 $APPEALS 维度独立成卡，但卡片固定为三段式，不再展示评分、进度条、证据等级和证据盒子。

必须包含：
- **$APPEALS 八维分析**（8 个维度卡片，见下方格式说明）
- **风险/机会信号**（🔴风险/🟢机会，从八维分析中推导，每条附证据描述、客户数、受影响客户列表、$APPEALS 归属）
- **客户分层**（认可型/机会型/观望型/风险型，含分层依据、代表客户、典型声音）

**$APPEALS 八维分析卡片格式**：

```markdown
## 二、理解客户声音（Understand）

### $APPEALS 八维分析

> 以下按 $APPEALS 八维度逐一展示客户声音。每个维度卡片固定为三段：第一段统计与信号判断；第二段 2-3 条真实客户或商机反馈；第三段行动建议。

---

**价格竞争与价值感知（Price）** — {风险或机会标签，如 🔴风险信号 / 🟢机会信号 / — 平稳}

第一段：本周期该维度共提及 {voice_count} 次，涉及 {customer_count} 个客户/商机，当前以 {positive_or_negative} 信号为主；核心关注点是 {core_message}，当前风险为 {risk}，主要原因是 {risk_reason}。

第二段：
- {客户或商机A}：{真实反馈声音1}
- {客户或商机B}：{真实反馈声音2}
- {客户或商机C}：{真实反馈声音3，可选}

第三段：建议 {action_advice}。

---

**项目可得性与推进时效（Availability）** — {标签}

第一段：...
第二段：...
第三段：...

---

**品牌认知与方案呈现（Packaging）** — {标签}

> ...

---

**产品能力匹配度（Performance）** — {标签}

> ...

---

**使用体验与落地顺畅度（Ease of Use）** — {标签}

> ...

---

**交付可信度与合作确定性（Assurances）** — {标签}

> ...

---

**长期投入与回报预期（Life Cycle Cost）** — {标签}

> ...

---

**行业认同与外部参照影响（Social Acceptance）** — {标签}

> ...

---

### 风险/机会信号

🔴 **{风险标题}**
{风险描述}
> 证据：{evidence_description}（{customer_count} 个客户 / {voice_count} 条声音）
> 受影响客户：{customer_list}
> $APPEALS 归属：{dimension}

🟢 **{机会标题}**
{机会描述}
> 证据：{evidence_description}（{customer_count} 个客户 / {voice_count} 条声音）
> 相关客户：{customer_list}
> $APPEALS 归属：{dimension}

### 客户分层

**{segment_type}：{segment_title}**
{segment_summary}
> 分层依据：{voice_pattern} + {sentiment_distribution} + {risk_signal}
> 代表客户：{representative_customers}
> 典型声音（展开）：
> - {customer}："{typical_voice}" 情感：{sentiment} | 风险：{risk_level}
```

**$APPEALS 维度卡片规则**：
- 8 个维度必须全部输出，不得跳过任何维度。若某维度无声音数据，仍输出该维度卡片，写“当前样本未检测到该维度的有效客户声音”
- 每个维度固定三段式，不能新增第四段
- 第一段必须先写提及统计，再写信号判断
- 第二段必须列举 2-3 个客户或商机的真实反馈，不得编造，不得使用空泛归纳代替
- 第三段必须给出当前维度的行动建议
- 不输出得分、进度条、E1/E2/E3/E4 标签、证据盒子
- 风险/机会标签只能基于已有证据判断；若证据不足，写“当前数据不足以支持明确风险判断”

#### `三、持续变革（Transform）`

**目标**：回答「从客户声音中，我们应该在产品/服务/组织能力上做什么升级？」

必须包含：
- **经营层结论**（2-4 条，每条含数据证据 + 客户证据 + $APPEALS 维度）
- **能力升级方向**（升级方向/依据/优先级；Markdown 可用表格，HTML 必须用卡片）

**经营层结论短标题规则（新增，强制）**：
- 每条经营层结论都必须额外提炼一个 4-8 字的短标题，放在结论正文前
- 短标题只允许概括判断主旨，不重复整句结论
- 短标题必须来自现有证据和结论内容，不得为了“好看”扩写或编造
- 推荐风格：`竞品风险上升`、`增长底盘仍在`、`原声数据待补`

输出格式：
```markdown
## 三、持续变革（Transform）

### 经营层结论

**{tag} {结论标题}**
{结论摘要}

> 支撑证据：
> - 数据证据：{data_evidence}（{time_range}，{sample_size}）
> - 客户证据：{customer_quotes_summary}（{customer_count} 个客户）
> - $APPEALS 维度：{dimensions}

### 能力升级方向

| 升级方向 | 依据 | 优先级 |
| --- | --- | --- |
| {direction} | {rationale} | {priority} |

> 依据来源：{customer_evidence} + {data_evidence}
> $APPEALS 归属：{dimension}
```

**HTML 呈现补充规则（新增，强制）**：
- `六维总览` 在当前评审版 HTML 中改为纵向条目式卡片，非宫格卡片；每条前有小圆点，正文按固定顺序输出
- `主要问题清单` 必须作为 `六维总览` 后的独立小章节输出，展示 5 条高频问题，每条使用“分类加粗 + 问题描述 + 客户数/次数统计”的格式
- `$APPEALS 八维分析` 必须为 2 列卡片布局（移动端 1 列），卡片标题条有浅色背景，正文白底；仅允许通过标题条、关键词、列表圆点、行动建议左侧细色条做强调
- `$APPEALS 八维标题` 必须固定使用以下 8 个中文专业名，并在后面保留原 VOC 英文维度名：`价格竞争与价值感知（Price）`、`项目可得性与推进时效（Availability）`、`品牌认知与方案呈现（Packaging）`、`产品能力匹配度（Performance）`、`使用体验与落地顺畅度（Ease of Use）`、`交付可信度与合作确定性（Assurances）`、`长期投入与回报预期（Life Cycle Cost）`、`行业认同与外部参照影响（Social Acceptance）`
- `风险 / 机会信号` 必须为 2 张并列卡片（移动端 1 列），标题条有浅色背景，正文区白底
- `客户分层` 必须为 2 列卡片布局（移动端 1 列），每张卡片使用“彩色标题条 + 白色正文区”
- `持续变革` 必须为 3 张并列结论卡片（移动端 1 列），每张卡片都必须展示短标题
- `能力升级方向` 必须为 3 张并列卡片（移动端 1 列），优先级以文字颜色区分，不使用色块标签

---

### 模板 B：经典六章升级

> 当用户选择经典六章或兼容旧版时使用。保留原六章名称，内容升级为证据驱动格式。
> 必须按以下6个一级目录顺序完整输出，标题逐字一致。

#### `一、整体判断`

- 用 2 到 4 个卡片表达客户声音的经营级结论
- 每个结论卡片必须包含：结论标题 + 摘要 + 支撑统计（客户数/声音数）+ 主要客户 + $APPEALS 归属 + 可展开原始语录
- 常用标签：`价值`、`增长`、`风险`、`机会`

#### `二、关注指标`

- 默认 4-6 个管理指标，每个必须含：评级/分数 + 含义 + 推导依据 + 争议点/置信度
- 推荐指标：价值认可度、收入健康度、产品匹配度、交付规模化、战略机会
- 关键客户声音问答：每个指标关联一个典型客户声音问答

#### `三、客户声音主题`

- 默认 5-8 个主题，五列表格（主题/客户典型表达/经营含义/优先动作/$APPEALS 归属）
- 每个主题必须含可展开详情：典型表达 + 经营含义 + 优先动作 + 原始语录
- 主题名称使用管理层可读业务词

#### `四、客户分层`

- 每个分层段含：分层依据 + 代表客户 + 可展开声音摘要
- 推荐分层：认可型/机会型/观望型/风险型

#### `五、管理动作`

- 默认 4-6 条，每个动作含：目的 + 责任角色 + 时机 + 触发原因 + 关联客户原话

#### `六、经营层结论`

- 2-4 条结论，每条含：数据证据 + 客户证据 + $APPEALS 维度

---

## Q&A 模式输出规则

### Q&A 第一步输出（概况 + 信号 + 行动）

当 interaction_mode=qa 且 step=1 时，输出 3 张卡片：

1. **维度概况**：提及率、情感分布、趋势方向、风险标签
2. **风险/机会信号**：该维度推导出的具体信号，每条附证据客户
3. **建议行动**：分立即/短期/长期，绑定责任角色

输出底部固定附加：
- "💬 回复「看原始语录」查看支撑证据 | 回复「看客户分布」查看哪些客户在说"
- "💡 你可能还想了解：[推荐维度]"
- "📧 输入「生成报告」可获取完整 报告"

```markdown
### 📊 {维度名称}概况
- 提及客户：{n}/{total}（{rate}%）
- 情感分布：负面 {neg}% / 正面 {pos}%
- 趋势：{趋势方向}
- 风险标签：{风险等级}

### 📢 风险/机会信号
🔴 **{风险标题}**
   {风险描述}
   证据：{客户列表}

🟢 **{机会标题}**
   {机会描述}
   证据：{客户列表}

### 🎯 建议行动
**立即**：{行动}
**短期**：{行动}
**长期**：{行动}

---
💬 回复「看原始语录」查看支撑证据 | 回复「看客户分布」查看哪些客户在说
💡 你可能还想了解：[{推荐维度}近期信号增强，建议深钻]
📧 输入「生成报告」可获取完整 报告
```

### Q&A 第二步输出（原始语录 + 客户分布）

当用户在第一步后说"看原始语录"或"哪些客户说的"，输出 2 张卡片：

1. **客户分布**：哪些客户提及、各自的情感、可展开原话
2. **原始语录**：按证据等级 E1→E4 排序

```markdown
### 👥 客户分布

**{客户名}** — 提及 {n} 次 — {情感}
  > "{原话}"
  > 来源：{来源类型} {日期} | {证据等级}

### 💬 原始语录（按证据等级排序）

**{证据等级} {证据等级说明}**
"{原话}"
— {客户名} · {联系人} · {日期}
```

### report_with_qa 模式

当 interaction_mode=report_with_qa 时，输出格式与选定模板一致，但：

1. 报告页头新增聚焦注释：「本报告重点展开您关注的【{维度列表}】维度」
2. qa_context 中 dimensions_explored 对应的章节展开深度 +1（更多客户细节和原始语录）
3. dimensions_unexplored 对应的章节保持标准深度

---

## 维度下钻（两种模板通用）

用户在六维总览表中点击某维度后，输出该维度的完整 5 张卡片。按维度类型分两种：

- **常规五维（痛点/期望/不满/认可/竞品）**：概况 → 客户分布 → 原始语录 → 风险/机会信号 → 建议行动
- **趋势维度**：趋势列表 → 趋势详情（含演进时间线） → 原始语录 → 风险/机会信号 → 建议行动

---

## 详细展开规则

- 当用户要求详细版时，只能在已有章节内展开证据和客户反馈，不新增附录章节
- 详细展开不能推翻主结论；若证据与主结论冲突，必须在正文中显式标注“当前数据不足以支持判断”

## 建议动作规则

- CEO/管理层默认不超过 6 条
- 每条建议必须包含目的、责任角色和适合时机
- 动作优先指向跨部门机制、产品/交付/服务优先级、风险治理和经营节奏

## 样本偏差规则

- 管理层主视图默认不展开样本偏差明细，但若偏差已经可能影响主结论，必须在页头或附录中提示
- 典型偏差包括：
  - 某部门会议记录明显更完整
  - 当前周期只有负面反馈沉淀
  - 原文缺失，主要依赖摘要
  - 趋势基线不足

---

## 输出数据结构参考（YAML）

> 以下 YAML 仅用于理解内部数据结构，**不作为直接输出格式**。实际输出必须按上述 Markdown 模板顺序完整输出。

```yaml
r08_assembly:
  default_view: ceo
  output_mode: report|qa|report_with_qa
  report_template: voc_5step|classic_6chapter
  output_format: markdown|html
  information_completeness: complete|partial|insufficient
  report_header:
    scope_label:
    view_type: CEO|sales_manager|department_leader|ae|meeting|sales_record|single_record|unknown
    start_date:
    end_date:
    scope:
    sample_size:
      sales_record_count:
      meeting_count:
      meeting_chunk_count:
      voice_item_count:
    confidence_note:
    focus_note:
  dimension_overview:
    - dimension: 痛点|期望|不满|认可|竞品|趋势
      customer_count:
      total_customer_count:
      mention_rate:
      sentiment_negative_ratio:
      sentiment_positive_ratio:
      risk_level: high|medium|low|none
      trend_direction: rising|stable|declining|new|unknown
      trend_change_rate:
  voc_5step_content:
    hear:
      voice_overview:
      data_coverage:
      sample_quality:
    understand:
      appeals_dimensions:
        - dimension: $价格|A可获得性|P包装|P性能|E易用性|A保证|L生命周期成本|S社会接受度
          score: 0-100
          risk_tag: risk|opportunity|stable
          voice_count:
          customer_count:
          sentiment_negative_ratio:
          sentiment_positive_ratio:
          trend_change:
          business_meaning:
          original_quotes:
            - text:
              evidence_level: E1|E2|E3|E4
              source:
              customer:
              date:
      risk_opportunity_signals:
        - signal_type: risk|opportunity
          title:
          description:
          evidence_customers: []
          appeals_dimension:
      account_segments:
        - segment: 认可型|机会型|观望型|风险型|自定义
          title:
          summary:
          voice_basis:
          representative_customers: []
    act:
      actions:
        - action:
          purpose:
          owner_or_role:
          timing: 立即|短期|长期
          priority: high|medium|low
          trigger_reason:
          trigger_customers: []
          trigger_quotes: []
    feedback:
      trend_changes:
        - dimension:
          direction: improving|worsening|stable|new
          evidence:
      customer_response_tracking:
        - customer:
          adopted: yes|partial|no
          evidence:
    transform:
      conclusions:
        - tag:
          title:
          summary:
          data_evidence:
          customer_evidence:
          appeals_dimensions: []
      capability_upgrades:
        - direction:
          rationale:
          priority: high|medium|low
  classic_6chapter_content:
    overall_judgment:
      cards:
        - tag: value|growth|risk|opportunity|delivery|strategy
          title:
          summary:
          evidence_stats:
          customer_list: []
          appeals_dimension:
          original_quotes: []
    ceo_metrics:
      metrics:
        - label:
          score:
          meaning:
          derivation_basis:
          uncertainty:
      key_voice_answers:
        - question:
          answer:
          evidence_customers: []
    voice_topics:
      topics:
        - topic:
          customer_expression:
          business_meaning:
          priority_action:
          signal_type: risk|opportunity|neutral
          appeals_dimensions:
            primary:
            secondary: []
          voice_count:
          customer_count:
          original_quotes: []
    account_segments:
      segments:
        - segment: 认可型|机会型|观望型|风险型|自定义
          title:
          summary:
          voice_basis:
          representative_customers: []
    management_actions:
      actions:
        - action:
          purpose:
          owner_or_role:
          timing:
          priority: high|medium|low
          trigger_reason:
          trigger_customers: []
          trigger_quotes: []
    executive_conclusions:
      conclusions:
        - tag:
          title:
          summary:
          data_evidence:
          customer_evidence:
          appeals_dimensions: []
  qa_output:
    step: 1|2
    dimension:
    dimension_overview_card:
      mention_rate:
      sentiment_distribution:
      trend:
      risk_tags: []
    risk_opportunity_signals:
      - signal_type: risk|opportunity
        title:
        description:
        evidence_customers: []
    suggested_actions:
      - action:
        timing: 立即|短期|长期
        description:
    customer_distribution_card:
      customers:
        - customer_name:
          mention_count:
          sentiment:
          quotes: []
    original_quotes_card:
      quotes:
        - text:
          evidence_level: E1|E2|E3|E4
          source:
          customer:
          date:
    suggested_follow_ups:
      - dimension:
        reason:
  appendix:
    sample_bias:
      - bias:
        possible_impact:
    open_questions:
      - question:
        why_it_matters:
        suggested_source:
    representative_quotes:
      - quote:
        source:
        confidence:
```
