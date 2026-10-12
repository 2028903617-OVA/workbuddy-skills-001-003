# R03 博弈编年

## 目标

从 Memory 和 CRM 跟进记录中整理影响交接的关键事件，帮助接手人理解客户关系和商机推进是如何走到今天的。

## 触发条件

存在 Memory、CRM 跟进记录、商机阶段变化、合同/订单、客户健康预警或用户提供的历史信息时执行。Memory 不足时仍执行，但必须输出缺口。

## 输入来源

- Memory 中的交接快照、关键博弈事件、承诺台账、风险记录。
- CRM `ActiveRecordObj`。
- CRM `NewOpportunityObj` 阶段变化和备注。
- full 模式下的合同、订单、回款、CSM 预警和流失原因。
- 用户补充的原 AE 口头交代。

## 输出契约

```yaml
r03_game_timeline:
  time_range:
  events:
    - date:
      event_type: interaction|commitment|stage_change|competitor|budget|delivery|payment|relationship|other
      event:
      our_action:
      customer_reaction:
      commitment_status: kept|partial|overdue|not_applicable|unknown
      relationship_change: warming|cooling|stable|unknown
      handover_impact:
      source:
      confidence: confirmed|inferred|unknown
  turning_points:
    - date:
      turning_point:
      reason:
      handover_note:
  timeline_gaps:
    - gap
```

## 选择规则

- 默认覆盖最近 6-12 个月；老客户要补充影响当前关系的更早关键节点。
- 只保留会改变接手判断的事件：承诺兑现/未兑现、竞品介入、关键人变化、预算变化、POC 成败、交付争议、回款问题、投诉、客户态度转折。
- 不把普通寒暄、例行跟进、无结论会议写入主时间线。
- 每个事件必须说明“对接手人的影响”，否则不进入主表。
- Memory 与 CRM 冲突时，不直接二选一，标注“需原 AE 核对”。

## 结构化文本输出

```markdown
## 3. 博弈编年

| 时间 | 事件 | 我方动作 | 客户反应 | 承诺状态 | 关系变化 | 交接影响 | 置信度 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  | 已兑现/部分/逾期/无/未知 | 升温/降温/稳定/未知 |  | 确认/推断/未知 |

### 关键转折点
- {时间}：{转折点及原因}；接手提醒：{为什么接手人必须知道}

### 时间线缺口
- {缺少最后一次有效沟通、关键承诺、POC 结果、竞品动作等信息}
```
