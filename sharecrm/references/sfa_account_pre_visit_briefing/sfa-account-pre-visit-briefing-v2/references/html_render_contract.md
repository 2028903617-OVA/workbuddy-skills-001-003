# 见客前 HTML 渲染契约

生成见客前客户简报 HTML 时读取本文件。HTML 必须由 `scripts/render_pre_visit_briefing.py` 渲染，不得由 agent 手写或重新设计。

## 执行顺序

1. 按 R01-R04 整理就绪度输入，调用 `scripts/calc_ready_score.py`。
2. 把评分结果放入事实包的 `readiness`。
3. 让 Markdown 和 HTML 共用同一份 `pre_visit_facts_bundle.json`。
4. 执行：

```bash
python3 scripts/render_pre_visit_briefing.py \
  --input <pre_visit_facts_bundle.json> \
  --output <客户名称>_见客前简报_<日期>.html
```

渲染器会自动调用 `scripts/validate_pre_visit_briefing.py`。校验失败时不得交付 HTML。需要排除旧客户残留时，重复传入 `--forbid-text "<旧内容>"`。

## 顶层结构

```json
{
  "metadata": {},
  "meeting": {},
  "readiness": {},
  "risks": [],
  "actions": [],
  "post_visit_actions": [],
  "sections": {},
  "data_coverage": {},
  "references": {}
}
```

## metadata

| 字段 | 含义 |
| --- | --- |
| `customer_name` | 客户名称，必填 |
| `mode` | `lite / normal / full`，默认 `normal` |
| `customer_type` | 客户类型或 10 秒身份标签 |
| `current_stage` | 当前会议或商机阶段 |
| `meeting_time` | 会议时间或数据更新时间 |

## meeting

```json
{
  "meeting": {
    "one_sentence_judgement": "普通正文尺度的一行局面摘要",
    "context_summary": "简短会议背景",
    "first_question": "AE 可以直接照着问的一句话",
    "today_goal": "只写一个目标",
    "biggest_risk": "只写一个最高风险",
    "recommended_play": "一个明确的现场打法",
    "key_person": "能改变局面的关键人",
    "meeting_boundary": "不能承诺或不能让步的事项",
    "do_not_do": "明确禁忌动作"
  }
}
```

## readiness

直接使用 `calc_ready_score.py` 的输出字段：

- `information_completeness`
- `pain_point_match`
- `competitive_risk`
- `readiness`
- `readiness_grade`
- `missing_fields`

允许补充：

- `weakest_gap`
- `meeting_recommendation`
- `information_note`
- `pain_note`
- `competition_note`

证据不足时保留未知，不得为了环形图或分项卡片编造分数。

## risks 与 actions

```json
{
  "risks": [
    {"title": "风险", "response": "现场应对动作"}
  ],
  "actions": [
    {"priority": "P0", "title": "动作", "detail": "5 分钟内可完成的问题或动作"}
  ]
}
```

`lite` 只渲染 1 条最高风险和 1 条 P0；`normal/full` 最多各渲染 3 条。`post_visit_actions` 不放在当日 actions 中，结构如下：

```json
{
  "post_visit_actions": [
    {
      "priority": "P0",
      "action": "会后动作",
      "owner": "负责人或待确认",
      "due": "会后30分钟内/当日/约定日期",
      "trigger": "与会议结果绑定的触发条件",
      "completion_standard": "可验证的交付物或客户确认"
    }
  ]
}
```

`lite` 渲染 1 项会后必做；`normal/full` 渲染 3-5 项。渲染清单不代表动作已经执行。

## sections

| 字段 | 结构 |
| --- | --- |
| `people` | `name / title / role / stance / tactic`，最多 6 人 |
| `timeline` | `triggered / time_range / summary_items[] / detail_items[] / turning_points[] / timeline_gaps[]`；摘要含 `date / event / impact`，明细含 `date / event_type / event / our_action / customer_reaction / commitment_status / relationship_change / visit_impact / source / confidence` |
| `pains` | `pain / product_fit / evidence / detail` |
| `competition` | full 模式；`tag / title / detail` |
| `history_financial` | full 模式；`tag / title / detail` |

兼容旧事实包时，可从 `timeline.items[]` 生成摘要和明细占位，但新事实包必须使用 `summary_items[] / detail_items[]`。

明细视图在关键事件之后继续展示 `turning_points[]` 和 `timeline_gaps[]`；没有证据时允许省略，不得用模板文字凑数。

`normal` 固定输出人力地图、痛点矩阵、拜访后行动和最后的“数据质量”页签；博弈编年仅在 `triggered=true` 或存在节点时展示，并在同一页签提供“摘要 / 明细”切换。`full` 追加竞品分析和历史合作与财务页签，但“数据质量”仍必须是最后一个页签。`lite` 不输出补充页签，但必须保留一个会后必做和精简来源区。

## data_coverage

使用中文业务标签作为 key，只允许：`已读取 / 无数据 / 权限不足 / 未触发查询 / 查询失败`。

必须覆盖客户、商机、联系人、跟进记录、日程、需求/问题、会议、待办/任务、现场拜访、竞品明细、合同、订单/回款、外部情报。用户可见区域不得出现对象或字段 apiName。

## references

```json
{
  "references": {
    "sources": ["CRM 客户、商机、联系人和跟进记录", "必要外部情报"],
    "confidence_note": "确认：有直接证据；推断：有行为证据；猜测：必须现场验证。"
  }
}
```

来源只展示中文业务类别，不展示 query plan、CLI 命令或字段 apiName。

## 移动端展示

- 动态正文容器必须使用自然高度，不能用固定 `height` 或 `max-height` 截断长客户名、风险、问题和数据来源。
- 640px 及以下自动单列；420px 及以下进一步收紧内边距，但不得压缩或遮挡正文。
- 页签栏允许触控横向滚动；页签名称不能被挤压，页签内容中的长文本必须自然换行。博弈编年的“摘要 / 明细”分段切换必须可键盘操作，并在移动端保持可见。
- 输出后应检查顶部信息、会前判断、就绪度和行动看板之间没有重叠或横向溢出。
