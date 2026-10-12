# R06 代表性客户原文

## 目标

从销售记录（`ActiveRecordObj`）和会议记录明细（`AIMeetingChunkObj`）中选择少量代表性原文或高保真摘要，让报告保留真实客户语感，同时避免堆砌长篇记录。

## 触发条件

完成 R02 客户声音抽取后执行。若没有 E1/E2 证据，输出“暂无可靠客户原文”。

## 输出契约

```yaml
r06_quotes:
  representative_quotes:
    - source_object: ActiveRecordObj|AIMeetingObj|AIMeetingChunkObj|memory|user_input
      source_record_id:
      meeting_id:
      source_title:
      source_date:
      owner:
      owner_department:
      initiator:
      topic:
      quote_or_summary:
      why_selected:
      evidence_level: E1|E2|E3|E4
      sentiment: positive|neutral|negative|mixed|unknown
      intensity: high|medium|low|unknown
      object_api_name:
      original_id:
      confidence: confirmed|inferred|unknown
  omitted_quote_reasons:
    - reason:
      count:
  data_gaps:
    - gap
```

## 选择规则

- 默认输出 5-8 条；summary 模式 3-5 条，full 模式最多 12 条。
- 优先选择会议记录明细（`AIMeetingChunkObj`）的 `original_content`、强度高、最近发生、能代表高频主题的声音。
- 同一会议或销售记录同一主题最多保留 1 条，避免重复。
- 负面、正向和中性声音都可以保留，但负面高风险不能被美化或隐藏。
- 如果原文过长，用高保真摘要；摘要不能改变客户态度和语义强度。
- 不展示手机号、邮箱、隐私信息或无关人名。
- 不为制造冲击力而夸大客户措辞。

## 原文处理规范

- 客户原文短且清晰：可直接引用。
- 原文较长或记录夹杂销售判断：改写为“客户表达/客户反馈/客户担心”。
- 会议记录明细（AIMeetingChunkObj）摘要：标注为“摘要”，不得写成直接原话。
- 销售观察：标注为“销售观察”，不得写成客户原文。
- 争议信息：保留“需核对”，不要只采纳单方说法。

## Markdown 输出

```markdown
## 5. 🗣️ 代表性客户原文

| 来源 | 时间 | 主题 | 原文/高保真摘要 | 强度 | 为什么重要 |
| --- | --- | --- | --- | --- | --- |
| 销售记录（ActiveRecordObj）/会议记录（AIMeetingObj）/会议记录明细（AIMeetingChunkObj） |  |  |  | 高/中/低 |  |

### 原文口径说明
- {哪些是会议记录明细（AIMeetingChunkObj）原文，哪些是摘要、销售观察或行为推断}
```
