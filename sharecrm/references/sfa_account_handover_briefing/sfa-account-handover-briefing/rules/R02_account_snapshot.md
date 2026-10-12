# R02 客户画像与合作状态

## 目标

为接手人提供客户基础画像和当前合作状态，帮助接手人理解“这个客户是谁、对我们是什么价值、当前合作/商机处于什么阶段”。

## 触发条件

完成 R01 后始终执行。

## 输入来源

- CRM `AccountObj`。
- CRM `NewOpportunityObj`。
- full 模式下的 `ContractObj`、`SalesOrderObj`、回款和客户健康数据。
- Memory 中的历史合作、交付体验、客户状态变化。
- `references/crm_schema.md`。
- `references/industry_benchmarks.md`，仅用于形成待核对假设。

## 输出契约

```yaml
r02_account_snapshot:
  account_profile:
    customer_id:
    customer_name:
    industry:
    segment:
    employee_count:
    revenue_band:
    location:
    account_source:
    deal_status:
    last_followed_time:
  cooperation_status:
    lifecycle_stage: prospect|active_opportunity|won_customer|renewal_window|expansion|dormant|churn_risk|unknown
    current_opportunities:
      - name:
        stage:
        status:
        amount:
        probability:
        close_date:
        budget_status:
    historical_cooperation:
      summary:
      evidence:
  handover_value:
    customer_value_level: strategic|key|standard|low|unknown
    reason:
  account_gaps:
    - gap
```

## 判断规则

- CRM 字段优先于公开信息；Memory 可补充 CRM 没有的历史合作感受。
- `probability` 是原 AE 在 CRM 中录入的主观赢率，只能作为商机状态信号。
- 客户价值不能只看金额，还要结合战略客户、行业标杆、续约/增购潜力、历史合作风险。
- 行业基准只能用于“待核对假设”，不能写成客户事实。
- 如果客户是已成交或多次成交客户，必须说明是否存在续约、增购、交付或回款背景。

## 结构化文本输出

```markdown
## 2. 客户画像

### 基础信息
| 维度 | 内容 | 置信度 |
| --- | --- | --- |
| 客户名称 |  | 确认/推断/未知 |
| 行业/赛道 |  |  |
| 规模/营收 |  |  |
| 成交状态 |  |  |
| 客户来源 |  |  |
| 最后跟进 |  |  |

### 当前合作/商机状态
| 商机/合作 | 阶段 | 状态 | 金额 | 预计结单/到期 | 预算/合同状态 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

### 客户价值判断
{客户价值等级及原因，必须标注来源}

### 接手人需要补齐的客户画像信息
- {缺少行业、规模、合同、历史合作、业务背景等信息}
```
