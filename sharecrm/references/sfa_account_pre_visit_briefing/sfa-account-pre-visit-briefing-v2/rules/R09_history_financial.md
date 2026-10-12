# R09 历史合作与财务信号

## 目标

在 `full` 模式下补充历史订单、回款、续约和客户价值信号。本规则也可在当前公开信息不足时，为 R05 的 `financial_or_strategy_signal` 提供依据。

## 触发条件

仅在以下情况执行：

- 用户要求 `--style=full`、`expand` 或历史合作/回款分析。
- 当前客户是已有客户或曾经合作过的客户。
- 回款、订单或交付历史会直接影响今天会议。

normal 或 lite 输出不要包含本节，除非它构成重大预警。

## 输入来源

- 该客户的 CRM 订单。
- 该客户的 CRM 回款或应收账款。
- 续约或增购记录。
- 与合同、回款、交付、满意度有关的 memory 事件。

## 提取契约

返回以下结构化内容：

```yaml
r09_history_financial:
  has_history: true|false
  first_order_date:
  latest_order_date:
  total_order_count:
  total_contract_amount:
  total_paid_amount:
  overdue_amount:
  average_payment_days:
  customer_value_tier: strategic|value|nurture|low|unknown
  renewal_or_expansion_signal:
  financial_or_strategy_signal: true|false
  risks:
    - risk:
      source:
      severity: fatal|major|minor
      meeting_impact:
  meeting_note:
```

## 客户价值分层

- `strategic`：累计合同金额 >= 1,000,000。
- `value`：200,000-999,999。
- `nurture`：50,000-199,999。
- `low`：低于 50,000。
- `unknown`：金额缺失或不可靠。

如果 CRM 使用的币种或金额单位不同，需说明假设。

## 风险规则

以下情况标为重大或致命风险：

- 存在逾期应收，今天继续销售会显得不合时宜。
- 上次合作交付有争议或满意度差。
- 客户超过 12 个月未活跃，但 AE 假设关系仍然热。
- 续约/增购依赖过去失败过的模块。

## 对见客就绪度的影响

- 当历史数据提供了明确的时机、预算、续约、回款或增购信号时，设置 `financial_or_strategy_signal=true`。
- 如果存在逾期回款，即使关系看起来不错，也要在 R06 加入预警，并提高交易风险判断。
- 如果没有历史合作，不单独扣分；只表示 R09 不提供额外信号。

## Markdown 摘要

仅在 full 模式或财务重大相关时使用：

```markdown
### 历史合作/财务信号
- 历史合作：{has_history_summary}
- 累计合同：{amount} | 回款：{paid} | 逾期：{overdue}
- 价值分层：{tier}
- 对今天的影响：{meeting_note}
```

保持事实表达。除非近期证据支持，不要把历史合作等同于当前信任。
