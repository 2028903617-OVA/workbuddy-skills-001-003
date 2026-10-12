# R09 历史合作、财务与客户健康

## 目标

在 `--full` 模式下补充客户生命周期视角：历史合作、合同订单、回款健康、续约/增购信号、客户健康风险和流失原因。

## 触发条件

仅在以下情况执行：

- 用户使用 `/intake [客户名称] --full`。
- 用户明确要求查看历史合作、订单、回款、续约、增购、客户健康或流失原因。
- 客户是已成交、多次成交或历史合作客户。

## 输入来源

| 数据源 | 用途 |
| --- | --- |
| `ContractObj` | 合同签约、起止时间、合同金额、合同状态 |
| `SalesOrderObj` | 订单金额、订单状态、回款金额、应收金额 |
| 已确认字段口径的客户健康、CSM 预警或流失原因数据 | 客户健康风险、服务风险、流失阶段、流失归因 |
| Memory | 历史合作体验、交付争议、客户满意度变化 |
| 当前商机 | 与历史模块、历史团队、历史金额做对照 |

## 输出契约

```yaml
r09_history_financial:
  lifecycle_summary:
    first_contract_date:
    latest_contract_date:
    contract_count:
    total_contract_amount:
    total_order_amount:
    total_payment_amount:
    receivable_amount:
    lifecycle_stage: new|active|renewal|expansion|dormant|churned|unknown
  contracts:
    - name:
      amount:
      started_time:
      expired_time:
      status:
  orders:
    - name:
      order_amount:
      order_status:
      payment_amount:
      receivable_amount:
  financial_health_prompts:
    average_discount:
      value:
      scope:
      confidence: confirmed|inferred|unknown
    payment_cycle:
      value:
      scope:
      confidence: confirmed|inferred|unknown
    receivable_warning:
      signal:
      impact:
      confidence: confirmed|inferred|unknown
  health_risks:
    - risk:
      source:
      severity: high|medium|low|unknown
      impact:
  churn_reasons:
    - reason:
      source:
      confidence: confirmed|inferred|unknown
  renewal_or_expansion_signals:
    - signal:
      source:
      confidence: confirmed|inferred|unknown
  data_gaps:
    - gap
```

## 生命周期判断

| 阶段 | 判断标准 |
| --- | --- |
| new | 无合同或订单记录，仍处首次成交前 |
| active | 有有效合同或近期订单，客户仍在合作期 |
| renewal | 合同临近到期、续费/续签信号明确 |
| expansion | 已合作客户出现新部门、新模块、新区域或新商机 |
| dormant | 历史成交但 12 个月以上无新合作或互动很少 |
| churned | 有明确流失、终止、替换竞品或不续约记录 |
| unknown | 数据不足，无法判断 |

## 分析规则

- 金额和日期只使用 CRM、合同、订单或用户提供的数据。
- 历史平均折扣只有在 CRM 或订单/报价字段可支撑时才计算；必须说明样本范围，不能用单个商机折扣代表客户历史水平。
- 回款周期只在订单、应收、实收或付款日期字段可支撑时计算；数据缺失时写“未知”，不要用行业账期代替客户事实。
- 应收金额大于 0 时，需要说明是否可能影响续约或增购，但不能默认客户不满意。
- CSM 预警是客户健康信号，不等于流失事实；必须区分“风险”和“结果”。
- 流失原因应保留原始归因，不要简化成“价格问题”或“竞品问题”。
- 增购信号必须和历史已购模块、未覆盖组织、当前痛点或新商机相关。
- 若历史合作体验不好，客户360中要如实写入“历史包袱”，不要只写机会。
- 历史合作和财务信息不做美化；风险、流失和回款异常必须保留，数据不足时写“未知/待补充”。
- 来源类型和置信度保留在判断中，最终来源口径收口到档案末尾弱引用。

## Markdown 输出

```markdown
## 🧾 历史合作、财务与客户健康

### 生命周期概览
| 指标 | 内容 |
| --- | --- |
| 首次合作 |  |
| 最近合作 |  |
| 合同数 / 订单数 |  |
| 累计合同金额 |  |
| 累计订单金额 |  |
| 累计回款金额 |  |
| 当前应收 |  |
| 生命周期阶段 | new/active/renewal/expansion/dormant/churned/unknown |

### 财务数据提示
| 指标 | 内容 | 统计口径/样本 | 置信度 |
| --- | --- | --- | --- |
| 历史平均折扣 |  |  | 确认/推断/未知 |
| 回款周期 |  |  |  |
| 应收预警 |  |  |  |

### 合同与订单
| 类型 | 名称 | 金额 | 起止/签订时间 | 状态 | 回款/应收 |
| --- | --- | --- | --- | --- | --- |
| 合同/订单 |  |  |  |  |  |

### 客户健康风险
- {CSM 预警、交付争议、应收异常、长期未互动等；标注严重度和置信度}

### 流失或不续约原因
- {如有明确记录，写原因和置信度}

### 续约 / 增购信号
- {信号、证据类型、置信度}

### full 模式信息缺口
- {缺少的合同、订单、回款、健康或流失字段}
```
