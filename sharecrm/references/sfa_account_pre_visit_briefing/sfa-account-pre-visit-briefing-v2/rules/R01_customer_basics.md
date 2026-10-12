# R01 客户与商机基础信息

## 目标

提取见客前简报所需的客户基础信息和当前商机上下文。本规则为 R02-R06 提供事实底座，并产出见客就绪度计算所需的 `basic_info`、`recent_interactions`、`financial_or_strategy_signal` 字段。

## 触发条件

识别出客户后始终执行。

## 输入来源

- CRM 客户记录。
- 该客户下的进行中商机。
- 最近跟进记录。
- 用户或 CRM webhook 提供的会议上下文。
- 已有或用户要求补充的公开财务/战略信号。

## 提取契约

先返回以下结构化内容：

```yaml
r01_customer_context:
  customer:
    account_id:
    name:
    industry:
    employee_count:
    revenue_band:
    deal_status:
    account_source:
    location:
    last_followed_time:
    data_freshness: current|stale|unknown
  active_opportunity:
    opportunity_id:
    name:
    stage:
    status:
    amount:
    probability:
    close_date:
    budget_status:
    approval_flow:
    origin:
    trigger_event:
    last_commitment:
    commitment_status: kept|partial|missed|unknown
  recent_context:
    last_3_interactions:
      - date:
        type:
        participants:
        conclusion:
        sentiment:
    meeting_purpose:
    meeting_attendees:
  scoring_flags:
    basic_info: true|false
    recent_interactions: true|false
    financial_or_strategy_signal: true|false
  missing_fields:
    - field_name
  immediate_risks:
    - risk:
      source:
      severity: fatal|major|minor
```

## 字段规则

- 只有客户名称、行业或细分领域、规模、CRM 客户 ID 都可用时，`basic_info=true`。
- 最近 90 天内至少有一条有效互动记录时，`recent_interactions=true`。优先提取最近 3-5 条。
- 只有存在明确的营收趋势、公开公告、组织变化、扩张/收缩、政策压力或年报线索时，`financial_or_strategy_signal=true`。
- 若有多个进行中商机，选择与今天会议最相关或最近活跃的商机；其他商机只有在影响今天策略时才提及。
- `close_date` 距今不足 30 天，或商机阶段超过 30 天未推进时，加入即时风险。
- 预算状态未知时，加入风险，并把“探测预算”作为候选会议目标。

## 证据标签

每个关键事实必须使用一个证据标签：

- `CRM`：CRM 直接记录。
- `User`：用户提供的会议上下文。
- `Memory`：客户长期记忆。
- `公开信息`：公开渠道获得的信息。
- `推断`：需要现场验证的判断。

不要把公开信息或推断写成 CRM 事实。

## Markdown 摘要

结构化内容之后，只输出简短摘要：

```markdown
### 客户与商机基础
- 客户：{name} | {industry} | {scale/revenue} | 来源：{source}
- 商机：{stage} | 金额：{amount} | 赢率：{probability} | 预算：{budget_status}
- 最近互动：{last_interaction_summary}
- 当前最大基础风险：{risk_or_none}
- 缺失字段：{missing_fields_or_none}
```

本节保持简短。决策链、痛点、竞品和见客就绪度分析交给后续规则。
