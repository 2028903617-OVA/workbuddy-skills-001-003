# R01 交接背景

## 目标

先确认这次交接为什么发生、谁交给谁、客户当前处于什么状态，以及 Memory 是否足以支撑交接。这个规则决定整份交接简报的可信度和紧急程度。

## 触发条件

团队交接简报始终执行。

## 输入来源

- 用户输入的交接原因、原负责人、接手人。
- Memory 中的客户历史、交接快照、关键事件。
- CRM `AccountObj`、`NewOpportunityObj`、`ActiveRecordObj`。
- `references/cli_reference.md` 和 `references/crm_schema.md`。
- `PersonnelObj`、`ScheduleObj`，仅在需要识别内部负责人或近期安排时使用。

## 输出契约

```yaml
r01_handover_context:
  customer_id:
  customer_name:
  original_owner:
  receiver:
  handover_reason: resignation|transfer|team_collaboration|customer_upgrade|temporary_cover|unknown
  handover_date:
  current_customer_status: new|active_opportunity|won_customer|renewal_window|dormant|churn_risk|unknown
  handover_urgency: high|medium|low|unknown
  memory_status: complete|partial|insufficient
  memory_warning:
  active_context:
    active_opportunity:
    stage:
    amount:
    close_date:
    last_interaction_time:
  must_confirm_before_handover:
    - item:
      reason:
      owner: original_ae|receiver|manager|csm|unknown
  data_gaps:
    - gap
```

## 判断规则

- 交接原因必须来自用户、CRM 归属变化或 Memory，不要臆测。
- Memory 为空或只有零散 CRM 字段时，内部记录 `memory_status=insufficient`；不要展示技术状态，在交接缺口中写“关键历史与关系信息待补充”。
- 只要存在进行中商机、临近结单、逾期承诺、客户投诉、CSM 预警、回款异常或竞品深度评估，交接紧急度至少为 `medium`。
- 如果预计结单在 30 天内、客户已在续约窗口、或存在高严重度未处理风险，交接紧急度为 `high`。
- 没有原负责人或接手人信息时，不阻塞生成，但必须写入“交接缺口”。
- 不输出见客前“今日目标”或 P0/P1/P2；只写交接背景和待确认项。

## 结构化文本输出

```markdown
## 1. 交接背景

| 字段 | 内容 | 置信度 |
| --- | --- | --- |
| 原负责人 |  | 确认/推断/未知 |
| 接手人 |  | 确认/推断/未知 |
| 交接原因 |  | 确认/推断/未知 |
| 当前客户状态 |  | 确认/推断/未知 |
| 交接紧急度 | 高/中/低/未知 |  |

### 当前上下文
- 当前主要商机：
- 最近一次有效互动：
- 仍在推进的关键事项：

### 交接前必须确认
| 事项 | 为什么重要 | 建议负责人 |
| --- | --- | --- |
|  |  | 原 AE/接手人/经理/CSM/未知 |

### 交接缺口
- {缺少原负责人、接手人、交接原因、Memory 历史或最近互动等信息}
```
