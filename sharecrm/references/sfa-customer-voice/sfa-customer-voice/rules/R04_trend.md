# R04 趋势变化

## 目标

判断客户声音在当前周期相对上一周期或历史基线的变化：哪些声音升温、降温、新出现、消失或保持稳定。

## 触发条件

完成 R03 主题聚类后执行。若存在上一周期三对象数据、历史 Memory 或用户要求趋势分析，则必须执行；否则输出“无可靠对比基线”。

## 输入来源

- 当前周期销售记录（`ActiveRecordObj`）、会议记录（`AIMeetingObj`）、会议记录明细（`AIMeetingChunkObj`）中的客户声音主题和明细。
- 上一等长周期销售记录（`ActiveRecordObj`）、会议记录（`AIMeetingObj`）、会议记录明细（`AIMeetingChunkObj`）。
- Memory 中历史客户声音快照。

## 趋势定义

| 趋势 | 判断标准 |
| --- | --- |
| up | 当前周期声音数、来源记录数或强度明显上升 |
| down | 当前周期声音数、来源记录数或强度明显下降 |
| stable | 变化不明显，主题持续存在 |
| new | 上一周期几乎没有，本周期首次明显出现 |
| disappeared | 上一周期明显存在，本周期基本消失 |
| unknown | 样本不足或无法对比 |

## 输出契约

```yaml
r04_trend:
  baseline:
    current_range:
    compare_range:
    current_voice_count:
    compare_voice_count:
    current_sales_record_count:
    compare_sales_record_count:
    current_meeting_count:
    compare_meeting_count:
    current_meeting_chunk_count:
    compare_meeting_chunk_count:
    reliability: high|medium|low|unknown
  topic_trends:
    - topic_name:
      trend: up|down|stable|new|disappeared|unknown
      current_count:
      compare_count:
      current_source_count:
      compare_source_count:
      intensity_change: stronger|weaker|same|unknown
      reason:
      confidence: confirmed|inferred|unknown
  emerging_signals:
    - signal:
      why_it_matters:
      representative_source:
  cooling_signals:
    - signal:
      interpretation:
  data_gaps:
    - gap
```

## 分析规则

- 趋势必须说明比较周期，不能只写“最近上升”。
- 样本量太小时，不做强趋势结论；写“样本不足，仅作观察”。
- 只看频次可能误导，必须同时考虑来源记录数、会议记录（AIMeetingObj）数、强度、跨部门重复程度和记录完整度。
- 如果本周期记录数整体变少，需要提醒样本偏差。
- 新出现的高强度声音即使只有 1-2 条记录，也可列为“新兴信号”，但不能写成普遍趋势。
- 下降不一定代表问题解决，可能是记录缺失、会议减少、AI 分析失败或客户沉默，需要标注解释。
- `ai_status` 失败率上升应作为“记录质量趋势”，不要混同为客户态度趋势。

## Markdown 输出

```markdown
## 3. 📈 趋势变化

| 主题 | 当前周期 | 对比周期 | 趋势 | 强度变化 | 判断 |
| --- | --- | --- | --- | --- | --- |
|  |  |  | 上升/下降/稳定/新出现/消失/未知 | 变强/变弱/持平/未知 |  |

### 新兴信号
- {新出现或突然变强的声音}

### 降温信号
- {下降或消失的声音，以及可能解释}

### 趋势可信度
- {销售记录（ActiveRecordObj）、会议记录（AIMeetingObj）、会议记录明细（AIMeetingChunkObj）的样本量、记录完整度、对比基线是否可靠}
```
