# R06 痛点地图

## 目标

把客户痛点分成“已确认、可推断、待验证”三层，避免把行业通用问题写成客户事实。

## 触发条件

存在需求调研、跟进记录、商机备注、CSM 预警、流失原因、用户输入或行业参考时执行。

## 输入来源

- CRM `ActiveRecordObj.active_record_content`。
- CRM `NewOpportunityObj.notes`。
- CSM 预警和流失原因对象。
- Memory 中的客户原话、POC 反馈、交付争议。
- `references/industry_benchmarks.md`，仅用于形成假设。

## 证据等级

| 等级 | 含义 | 可写法 |
| --- | --- | --- |
| E1 | 客户明确表达或 CRM 原话 | “客户明确提到...” |
| E2 | 客户行为或项目动作反映 | “从 POC/审批/反复追问看...” |
| E3 | 公开信息、财务或组织变化推断 | “结合公开信息推断...” |
| E4 | 行业基准假设 | “行业常见问题，需验证...” |

## 输出契约

```yaml
r06_pain_map:
  confirmed_pains:
    - pain:
      business_impact:
      evidence:
      source:
      evidence_level: E1|E2
      owner:
  inferred_pains:
    - pain:
      reasoning:
      source:
      confidence: inferred
      validation_question:
  assumptions:
    - assumption:
      benchmark_source:
      validation_question:
  non_pains:
    - item:
      reason:
  data_gaps:
    - gap
```

## 分析规则

- E1/E2 才能进入“已确认痛点”。
- E3/E4 只能进入“推断痛点”或“待验证假设”。
- 痛点要写业务影响：效率、成本、收入、风险、客户体验、合规、管理可视化。
- 同一痛点出现多次时合并，保留最强证据。
- 如果客户只表达“想上 CRM”，必须继续拆成具体业务问题，不把“上系统”本身当痛点。
- 不输出产品功能清单；产品能力只能作为后续匹配参考。
- 标准版可完整保留痛点分层，但不要把来源说明铺满正文；用证据等级和置信度表达强弱。

## Markdown 输出

```markdown
## 🎯 痛点地图

### 已确认痛点
| 痛点 | 业务影响 | 证据 | 证据等级 | 关联人员 |
| --- | --- | --- | --- | --- |
|  |  | 客户原话/CRM记录 | E1/E2 |  |

### 推断痛点
- {痛点}：{推断链路}（置信度：推断）

### 待验证假设
| 假设 | 假设依据 | 验证问题 |
| --- | --- | --- |
|  | 行业基准/公开信息/组织变化 |  |

### 明确不是痛点
- {客户否认或证据不足的问题}
```
