# 标准版 HTML 渲染契约

生成标准版客户简报 HTML 时读取本文件。HTML 必须由 `scripts/render_standard_briefing.py` 渲染，不得由 agent 手写或重新设计。

## 执行命令

```bash
python3 scripts/render_standard_briefing.py \
  --input <briefing_facts_bundle.json> \
  --output <客户名称>_客户360简报_<日期>.html
```

渲染器会自动调用 `scripts/validate_standard_briefing.py`；校验失败时不得交付 HTML。需要额外防止旧客户内容残留时，重复传入：

```bash
--forbid-text "<旧客户名称>" --forbid-text "<旧联系人名称>"
```

正式 HTML 使用顶部横向页签，每次只展示一个一级章节。“数据质量”必须是最后一个独立页签，集中承载数据覆盖、数据截止、下次更新、参考来源和置信度说明，不在业务页签重复展示。移动端所有主要容器使用内容驱动的自适应高度，长客户名、长状态、长结论和数据覆盖标签必须自然换行，页签与表格分别支持横向滑动。

固定页签顺序为：结论摘要、客户画像、决策圈图谱、博弈时间线、项目与商机、痛点地图、竞品全貌、开放问题、后续建议动作、可选的历史合作与财务、数据质量。关系温度和决策链在“决策圈图谱”中合并展示。页签内容标题不显示序号。

## 顶层结构

```json
{
  "metadata": {},
  "data_coverage": {},
  "kpis": [],
  "executive_summary": {},
  "sections": {},
  "references": {}
}
```

## metadata

| 字段 | 含义 |
| --- | --- |
| `customer_name` | 客户名称，必填 |
| `report_date` | 生成日期 |
| `briefing_status` | 固定写“标准版客户档案”或实际状态 |
| `mode` | 标准模式写 `standard`，full 模式写 `full` |
| `customer_status` | 客户当前状态 |
| `industry_or_segment` | 行业或客群 |
| `owner` | 负责人 |
| `information_completeness` | 完整 / 部分 / 不足 |
| `health_score` | 0-100；证据不足时省略，不编造分数 |
| `health_grade` | 健康度文字判断 |
| `health_signal` | 拉高或拉低健康度的关键证据 |
| `data_cutoff` | 数据截止时间 |
| `next_update` | 下次更新日期或触发条件 |

## data_coverage

使用中文业务标签作为 key，只允许以下状态：`已读取 / 无数据 / 权限不足 / 未触发查询 / 查询失败`。

```json
{
  "客户": "已读取",
  "商机": "已读取",
  "联系人": "已读取",
  "销售记录": "已读取",
  "需求": "无数据",
  "会议": "权限不足",
  "外部情报": "未触发查询"
}
```

用户可见内容不得出现 `AccountObj`、`NewOpportunityObj` 等 apiName。渲染器会执行一次兜底转换，但事实包仍应直接使用中文标签。

## kpis 与结论摘要

```json
{
  "kpis": [
    {"label": "进行中商机", "value": "3 个", "note": "合计 810 万元"}
  ],
  "executive_summary": {
    "one_sentence_conclusion": "一句话客户判断",
    "rows": [
      {"item": "客户状态", "conclusion": "结论", "confidence": "确认"}
    ],
    "priority_items": ["最多 3 条客户认知或后续关注点"]
  }
}
```

## sections

字段与 R01-R09 一一对应：

| 字段 | 主要内容 |
| --- | --- |
| `customer_profile` | `basic_info`、`business_status`、`strategy`、`system_motivation` |
| `timeline` | `items`、`trend` |
| `relationship_temperature` | `cards`、`summary`；与 `decision_chain` 合并渲染为“决策圈图谱” |
| `decision_chain` | `people`、`coverage_analysis`；与 `relationship_temperature` 合并渲染为“决策圈图谱” |
| `opportunity_overview` | 项目起源、目标、硬门槛、预算审批、使用规模、信息化现状、商机 |
| `pain_map` | `confirmed`、`inferred`、`to_verify` |
| `competitive_overview` | `competitors`、`advantages`、`weaknesses` |
| `open_questions` | 风险、开放问题、最大缺口、数据预警、建议动作；其中 `data_alerts` 和 `actions` 一起独立渲染为“后续建议动作”页签 |
| `history_financial` | 仅 full 模式使用；`enabled`、`summary`、`records`、`health_notes` |

`customer_profile.basic_info` 必须使用结构化数组，每项包含 `label / api_name / value`。`label` 取 CRM describe 元数据返回的字段名称并用于展示；`api_name` 仅用于内部溯源，不展示。旧事实包仍可传入对象形式，渲染器只对已知标准字段做兼容映射，无法映射的 apiName 会被校验器拦截。

```json
{
  "customer_profile": {
    "basic_info": [
      {"label": "客户名称", "api_name": "name", "value": "示例客户"},
      {"label": "客户编号", "api_name": "customer_no", "value": "C-00001"}
    ],
    "system_motivation": ["统一客户数据与销售过程", "提升销售预测准确率"]
  }
}
```

数组中的结构化行使用以下字段：

- `timeline.items`：`date / counterpart / channel / content / commitment / impact / confidence`
- `relationship_temperature.cards`：`title / temperature / evidence / confidence`
- `decision_chain.people`：`name / title / role / attitude / evidence / confidence`
- `opportunity_overview.usage_scope`：`group / scale / need / priority`
- `opportunity_overview.it_landscape`：`system / purpose / status / impact`
- `opportunity_overview.opportunities`：`name / stage / amount / expected_close / stage_age / confidence`
- `competitive_overview.competitors`：`name / status / reason / our_advantage / our_weakness / confidence`
- `open_questions.risks`：`severity / risk / impact / trigger / mitigation`
- `open_questions.questions`：`question / why / confidence`
- `open_questions.actions`：`action / purpose / timing / owner_or_role / confidence`，最多 5 条，独立显示在“后续建议动作”页签
- `history_financial.records`：`type / name / status / amount / date / note`

数据不足时保留字段并写“未知/待补充”，不要为了填满页面生成事实。`history_financial` 仅在 `metadata.mode=full` 或 `enabled=true` 时由渲染器加入页面。

## references

```json
{
  "references": {
    "sources": ["CRM 客户、商机、联系人和互动记录", "必要外部情报"],
    "confidence_note": "确认：有直接证据；推断：有行为证据；未知：无充分证据。"
  }
}
```

来源只展示中文业务口径和来源类别，不展示查询命令、query plan 或字段 apiName。
