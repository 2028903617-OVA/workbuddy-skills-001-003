# R05 待兑现承诺台账

## 目标

整理我方和客户双方的承诺、兑现状态、逾期影响和接手处理建议。交接场景里，承诺台账是防止客户体验断档和信任受损的核心模块。

## 触发条件

完成 R01-R04 后始终执行。即使没有承诺记录，也必须输出“暂无明确承诺记录”并列出需要原 AE 核对的问题。

## 输入来源

- Memory 中的承诺台账、交接快照、关键博弈事件。
- CRM `ActiveRecordObj.active_record_content`。
- CRM `NewOpportunityObj.notes`、阶段备注、下一步记录。
- 合同、订单、交付、回款、CSM 预警记录。
- 用户补充的原 AE 口头交代。

## 承诺类型

| 类型 | 说明 |
| --- | --- |
| our_commitment | 我方承诺，如材料、方案、报价、POC、交付、回款协调 |
| customer_commitment | 客户承诺，如反馈、预算批复、材料提供、下一次会议 |
| internal_commitment | 内部协同承诺，如售前、CSM、实施、财务支持 |
| implicit_commitment | 非正式但客户已经形成期待的承诺 |

## 输出契约

```yaml
r05_commitment_ledger:
  commitments:
    - commitment_id:
      type: our_commitment|customer_commitment|internal_commitment|implicit_commitment
      owner:
      commitment:
      promised_at:
      due_date:
      status: not_started|in_progress|kept|partial|overdue|cancelled|unknown
      evidence:
      impact_if_missed:
      receiver_action:
      priority: high|medium|low|unknown
      confidence: confirmed|inferred|unknown
  overdue_commitments:
    - commitment_id:
      overdue_days:
      relationship_impact:
      recommended_repair:
  commitments_to_confirm:
    - question:
      why_it_matters:
      suggested_owner: original_ae|receiver|csm|se|finance|customer|unknown
  data_gaps:
    - gap
```

## 判断规则

- 承诺必须有来源：CRM 记录、Memory、客户原话、会议纪要或用户明确输入。
- “客户期待我们会做”但没有正式承诺时，标为 `implicit_commitment`，不能写成已确认承诺。
- 逾期承诺必须写清楚逾期影响：关系、商机、交付、续约、回款或客户健康。
- 我方逾期承诺要给“修复建议”，不要只写“需跟进”。
- 客户承诺逾期时，不默认客户不配合；先写需要接手人核对的原因。
- 不使用 P0/P1/P2。优先级用 `high/medium/low/unknown`。

## 结构化文本输出

```markdown
## 5. 待兑现承诺

### 承诺总览
| 承诺方 | 承诺内容 | 承诺时间 | 截止日期 | 当前状态 | 影响 | 接手处理 |
| --- | --- | --- | --- | --- | --- | --- |
| 我方/客户/内部 |  |  |  | 未开始/进行中/已兑现/部分兑现/逾期/取消/未知 |  |  |

### 逾期或高风险承诺
| 承诺 | 逾期/风险 | 关系影响 | 修复建议 |
| --- | --- | --- | --- |
|  |  |  |  |

### 接手前必须核对的承诺
| 问题 | 为什么重要 | 建议找谁核对 |
| --- | --- | --- |
|  |  | 原AE/接手人/CSM/售前/财务/客户 |

### 承诺缺口
- {缺少承诺时间、责任人、截止日期、兑现状态或客户反馈等信息}
```
