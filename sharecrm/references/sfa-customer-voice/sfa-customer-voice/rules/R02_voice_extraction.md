# R02 客户声音抽取

## 目标

从销售记录（`ActiveRecordObj`）、会议记录（`AIMeetingObj`）、会议记录明细（`AIMeetingChunkObj`）中抽取可分析的客户声音单元。

客户声音单元不是完整记录，而是一条能够表达客户反馈、需求、疑问、异议、抱怨、认可、风险或购买信号的片段。

## 触发条件

完成 R01 范围识别并取得三对象记录后执行。

## 输入来源

- `ActiveRecordObj.active_record_content`。
- `ActiveRecordObj.interactive_content`。
- `ActiveRecordObj.active_record_type`、`interactive_types`、`interaction_channels`、`meeting_objectives`、`interactive_processes`。
- `AIMeetingObj.remark`、`name`、`ai_status`、`fail_reason`。
- `AIMeetingChunkObj.summary`、`original_content`、`name`、`status`。
- Memory 中的客户声音快照、高风险声音事件、新兴声音信号。
- 用户粘贴的销售记录（ActiveRecordObj）、会议纪要、会议记录明细（AIMeetingChunkObj）或客户反馈。

## 声音类型

| 类型 | 含义 | 示例 |
| --- | --- | --- |
| demand | 明确需求 | “想要打通 ERP”“需要移动端审批” |
| pain | 痛点/困难 | “销售过程看不清”“报表靠人工整理” |
| objection | 异议/顾虑 | “价格太高”“实施周期太长” |
| complaint | 投诉/负面反馈 | “服务响应慢”“系统不好用” |
| question | 疑问/追问 | “能不能支持私有化”“如何迁移数据” |
| praise | 正向认可 | “试用效果不错”“一线愿意用” |
| competitor | 竞品相关 | “也在看销售易”“自研系统已经上线” |
| budget | 预算/价格 | “预算还没批”“希望再降价” |
| approval | 审批/决策 | “需要老板拍板”“采购流程要走两个月” |
| usage | 使用效果 | “一线销售不愿填”“管理层看报表” |
| delivery | 交付/服务 | “上线太慢”“接口排期不确定” |
| data_quality | 记录/会议质量 | “会议 AI 分析失败”“原文缺失导致无法判断” |

## 证据等级

| 等级 | 含义 |
| --- | --- |
| E1 | 会议记录明细（AIMeetingChunkObj）原文或销售记录（ActiveRecordObj）中客户明确表达 |
| E2 | 会议记录明细（AIMeetingChunkObj）摘要、会议记录（AIMeetingObj）备注或记录行为反映，例如反复追问、明确异议、升级 |
| E3 | 销售观察，有具体记录内容支撑 |
| E4 | 经验假设或主题推断，只能作为待验证声音背景 |

## 输出契约

```yaml
r02_voice_extraction:
  sample:
    sales_record_count:
    meeting_count:
    meeting_chunk_count:
    voice_item_count:
    date_range:
  voice_items:
    - voice_id:
      source_object: ActiveRecordObj|AIMeetingObj|AIMeetingChunkObj|memory|user_input
      source_record_id:
      meeting_id:
      source_date:
      owner:
      owner_department:
      data_own_department:
      created_by:
      initiator:
      inner_participants:
      record_type:
      active_record_type:
      interactive_types:
      interaction_channels:
      related_object:
      account_id:
      leads_id:
      new_opportunity_id:
      object_api_name:
      original_id:
      source_title:
      original_text:
      concise_voice:
      voice_type:
      sentiment: positive|neutral|negative|mixed|unknown
      intensity: high|medium|low|unknown
      evidence_level: E1|E2|E3|E4
      business_impact:
      confidence: confirmed|inferred|unknown
  excluded_records:
    - reason:
      count:
  data_gaps:
    - gap
```

## 分析规则

- 一条销售记录（`ActiveRecordObj`）或会议记录明细（`AIMeetingChunkObj`）可拆出多条客户声音，但不要重复拆同义内容。
- `ActiveRecordObj.active_record_content` 是销售记录最高优先级正文。
- `ActiveRecordObj.interactive_content` 可作为互动内容补充。
- `active_record_type`、`interactive_types`、`interaction_channels`、`meeting_objectives`、`interactive_processes` 只能作为场景和归因信号，不替代正文。
- `account_id`、`leads_id`、`new_opportunity_id`、`related_object` 只做溯源和分组，不自动扩展查询。
- `AIMeetingChunkObj.original_content` 优先保留短句；长原文改写为高保真摘要。
- `AIMeetingChunkObj.summary` 可作为摘要证据，但不能夸大成客户原话。
- 销售自述必须区分为“销售观察”，不能当成客户原话。
- 普通寒暄、例行同步、无结论会议不进入主声音样本。
- 同一会议同一主题多次出现时，应合并为同一声音的多次出现，而不是堆叠重复文字。
- 对每条声音标记情绪、强度、证据等级和业务影响。
- `intensity=high` 必须满足至少一个条件：强烈负面、明确升级、阻塞关键推进、多个会议重复出现、跨部门重复出现、负责人明确需要处理。
- `ai_status` 异常或 `fail_reason` 非空时，记录为样本质量风险，不直接当客户负面声音。

## Markdown 输出

本规则默认不单独完整输出明细，只把样本量和抽取口径提供给 R08 组装。若用户要求“列出所有客户声音明细”，也只能作为附录输出，不能替换六个一级目录中的任何主结构，尤其不能替换“三、客户声音主题”的主题矩阵。附录明细使用以下格式：

```markdown
### 客户声音明细

| 时间 | 来源 | 负责人/部门 | 声音摘要 | 类型 | 情绪 | 强度 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 销售记录（ActiveRecordObj）/会议记录（AIMeetingObj）/会议记录明细（AIMeetingChunkObj） |  |  | demand/pain/... | 正/中/负/混合 | 高/中/低 | E1-E4 |
```
