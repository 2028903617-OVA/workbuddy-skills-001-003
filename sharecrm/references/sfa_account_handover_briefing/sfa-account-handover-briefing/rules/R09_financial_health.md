# R09 历史合作、财务与客户健康

## 目标

在 `--full` 模式下整理客户历史合作、合同订单、回款应收、客户健康、流失原因和续约/增购信号。该规则服务交接，不做财务审计；重点是让接手人知道历史包袱、价值判断和经营风险。

## 触发条件

满足任一条件时执行：

- 用户使用 `/handover [客户名称] --full`。
- 客户为已成交、历史合作、续约、增购、沉默唤醒或流失挽回场景。
- R06 出现回款、交付、服务、客户健康、流失风险。
- 用户明确要求查看合同、订单、回款、续约、增购或客户健康。

标准模式不输出本区块，但如果出现重大回款/交付/流失风险，应摘要进入 R06。

## 输入来源

- CRM `ContractObj`：合同金额、合同周期、合同状态、到期时间。
- CRM `SalesOrderObj`：订单金额、订单状态、已回款金额、应收金额。
- CRM `PaymentObj`：回款流水，若环境中存在独立回款对象。
- CRM 中已确认字段口径的客户健康、CSM 预警、流失原因、服务反馈或使用情况数据；不得硬编码未经确认的自定义对象或自定义字段。
- Memory 中的历史合作评价、交付争议、续约阻力、增购线索。
- R03 博弈编年和 R06 风险敏感点。

## 输出契约

```yaml
r09_financial_health:
  cooperation_summary:
    first_contract_date:
    latest_contract_date:
    lifecycle_stage: new|active|renewal|silent|churned|unknown
    total_contract_amount:
    total_order_amount:
    total_paid_amount:
    total_receivable_amount:
    contract_count:
    order_count:
    value_tier: strategic|growth|nurture|low|unknown
    confidence: confirmed|inferred|unknown
  contracts:
    - contract_id:
      name:
      amount:
      start_date:
      end_date:
      status:
      renewal_window:
      receiver_note:
  orders:
    - order_id:
      name:
      amount:
      status:
      paid_amount:
      receivable_amount:
      payment_risk:
      receiver_note:
  health_signals:
    - signal:
      type: service|delivery|payment|usage|relationship|renewal|churn|unknown
      evidence:
      impact:
      receiver_action:
  renewal_expansion_signals:
    - signal:
      evidence:
      prerequisite:
      suggested_next_step:
  data_gaps:
    - gap
```

## 判断规则

- 合同、订单、回款金额必须来自 CRM、用户输入或 Memory，不能估算。
- `SalesOrderObj.payment_amount` 与 `receivable_amount` 同时存在时，优先判断回款健康和应收风险。
- 合同到期、沉默时间长、应收未清、CSM 预警、流失原因，必须写入接手影响。
- 续约/增购信号必须写前提条件；例如先解决交付争议或回款问题，再谈新增需求。
- 客户健康不能只看金额；还要结合服务投诉、使用活跃、关键人变化、历史承诺兑现。
- 已流失客户必须写清楚流失原因是否仍影响本次接手。
- 不输出就绪度评分，也不把财务数据折算成见客前行动分。

## 价值分层

| 层级 | 判断方式 | 接手含义 |
| --- | --- | --- |
| strategic | 合同/订单金额高、组织影响大、可复制标杆或集团化机会 | 需要高优先级经营和跨部门协同 |
| growth | 有持续合作、续约或增购空间 | 接手后优先维护关系和识别扩展机会 |
| nurture | 金额较小但行业、场景或关系有潜力 | 控制投入，补齐真实需求 |
| low | 历史金额低、沉默久、增购信号弱 | 谨慎投入，先确认客户意愿 |
| unknown | 信息不足 | 进入交接缺口 |

## 结构化文本输出

```markdown
## 9. 历史合作、财务与客户健康

### 合作总览
| 指标 | 结果 | 接手含义 | 置信度 |
| --- | --- | --- | --- |
| 生命周期阶段 | 新客户/活跃合作/续约期/沉默/已流失/未知 |  | 确认/推断/未知 |
| 首次合作 |  |  |  |
| 最近合作 |  |  |  |
| 合同/订单数量 |  |  |  |
| 累计合同金额 |  |  |  |
| 累计订单金额 |  |  |  |
| 已回款金额 |  |  |  |
| 应收金额 |  |  |  |
| 客户价值层级 | 战略型/成长型/培育型/低价值/未知 |  |  |

### 合同与订单
| 类型 | 名称 | 金额 | 周期/时间 | 状态 | 回款/应收 | 接手注意 |
| --- | --- | --- | --- | --- | --- | --- |
| 合同/订单 |  |  |  |  |  |  |

### 客户健康信号
| 信号 | 类型 | 证据 | 影响 | 接手处理 |
| --- | --- | --- | --- | --- |
|  | 服务/交付/回款/使用/关系/续约/流失/未知 |  |  |  |

### 续约与增购信号
| 信号 | 证据 | 前提条件 | 建议下一步 |
| --- | --- | --- | --- |
|  |  |  |  |

### 财务与健康缺口
- {缺少合同周期、订单状态、已回款、应收、CSM 预警、流失原因或客户使用情况等信息}
```
