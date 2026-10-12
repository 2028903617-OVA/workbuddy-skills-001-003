# R02 博弈时间线

## 目标

从 Memory 和 CRM 跟进记录中还原客户与我方的关键互动历史，帮助 AE 建立上下文。

## 触发条件

存在 memory、销售记录、商机阶段变化、合同/订单或用户提供的历史信息时执行。

## 输入来源

- Memory 关键事件。
- CRM ActiveRecordObj。
- 商机阶段变化。
- 合同、订单、回款记录（full 模式）。

## 输出契约

```yaml
r02_timeline:
  time_range:
  events:
    - date:
      event:
      source:
      our_action:
      customer_reaction:
      relationship_change:
      impact:
      confidence: confirmed|inferred|unknown
  key_turning_points:
    - date:
      turning_point:
      reason:
  trend_insight:
    direction: warming|cooling|stalled|mixed|unknown
    interest_shift:
    evidence:
    confidence: confirmed|inferred|unknown
  data_gaps:
    - gap
```

## 选择规则

- 默认覆盖最近 12 个月。
- 如果客户是老客户，补充影响当前认知的更早关键节点。
- 只保留会改变客户认知的事件：承诺兑现/未兑现、竞品介入、关键人变化、预算变化、POC 成败、交付争议、回款问题。
- 不要把普通寒暄、例行跟进、无结论会议写入主时间线。
- 时间线不是流水账；每个节点必须说明对客户认知、关系温度、决策链或商机判断的影响。
- 时间线后必须给出趋势洞察：客户态度是升温、降温、停滞、分化还是未知；如客户关注点从价格转向交付、从功能转向管理价值，也要说明。
- 趋势洞察只能基于互动频率、客户承诺兑现、关键人参与度、问题深度、会议推进和明确表态，不能凭单次寒暄判断。
- 证据类型在结构化字段中保留，最终 Markdown 不逐条堆叠来源说明。

## Markdown 输出

```markdown
## 📅 博弈时间线

| 时间 | 事件 | 我方动作 | 客户反应 | 关系变化 | 置信度 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  | 升温/降温/不变/未知 | 确认/推断/未知 |

### 关键转折点
- {转折点及原因}

### 趋势洞察
{客户态度/兴趣变化：升温、降温、停滞、分化或未知；说明关注点是否发生变化和判断置信度}

### 时间线缺口
- {缺少哪些关键历史}
```
