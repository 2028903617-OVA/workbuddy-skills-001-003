# R01 客户画像

## 目标

提取客户360档案的基础画像，不做见客前行动判断。

## 触发条件

识别客户后始终执行。

## 输入来源

- CRM Account。
- 用户提供的客户背景。
- 公开信息，仅在用户要求或 CRM 信息不足时使用。
- 行业基准参考。

## 输出契约

```yaml
r01_customer_profile:
  customer_id:
  customer_name:
  industry:
  segment:
  employee_count:
  revenue_band:
  location:
  customer_level:
  primary_contacts:
    - name:
      title:
      role:
      confidence: confirmed|inferred|unknown
  cooperation_duration:
    value:
    basis: account_create_time|first_closed_deal|first_contract|user_provided|unknown
    confidence: confirmed|inferred|unknown
  opportunity_total_amount:
    value:
    scope: active_opportunities|all_read_opportunities|unknown
    confidence: confirmed|inferred|unknown
  deal_status:
  account_source:
  create_time:
  last_followed_time:
  last_deal_closed_time:
  basic_info:
    - label: CRM describe 返回的字段名称
      api_name: 仅内部溯源，不展示
      value:
  business_model:
  revenue_sources:
    - source:
      confidence: confirmed|inferred|unknown
  business_description:
  system_motivation:
    - motivation:
      evidence:
      confidence: confirmed|inferred|unknown
  strategic_signals:
    - signal:
      source:
      confidence: confirmed|inferred|unknown
  data_gaps:
    - field_name
```

## 分析规则

- CRM 字段优先于公开信息。
- 公开信息只能补充业务描述和战略动态，不覆盖 CRM 事实。
- 没有证据时写“未知”，不要用行业常识补齐。
- 客户等级只来自 CRM 字段或用户明示；没有字段时写“未知”，不要按规模或金额推断等级。
- 合作时长优先用首次成交/首次合同日期计算；没有历史合作数据时可用客户创建时间作为“建档时长”，但必须标明口径。
- 主要联系人只展示已读取联系人或互动中反复出现的人；角色不清时写“角色未知”。
- 商机总金额只统计已读取商机金额，并标明统计范围；币种不一致或金额缺失时不要强行求和。
- 业务模式/收入来源可由公开信息补充；毛利率、利润率等经营数字只有公开财报、招股书、年报或用户明示时才写。
- 客户画像要回答“这个客户是谁、做什么、处在什么业务状态”，不是销售行动建议。
- 基本信息表的标签必须使用 CRM describe 元数据返回的字段名称；字段 apiName 仅用于内部取数和溯源，不得直接展示给用户。
- 上系统动机必须单独成维度，说明客户为什么考虑采购或更换系统；只能使用客户原话、商机背景、需求、会议、销售记录或已确认的项目触发事件，没有证据时写“未知/待补充”。
- 正文不逐条堆叠来源；如需说明来源类型，使用“证据类型/置信度”，最终来源口径收口到档案末尾弱引用。

## Markdown 输出

```markdown
## 🪪 客户画像

| 维度 | 内容 | 置信度 |
| --- | --- | --- |
| 客户名称 |  | 确认/推断/未知 |
| 行业/赛道 |  |  |
| 规模/营收 |  |  |
| 客户等级 |  |  |
| 主要联系人 |  |  |
| 合作/建档时长 |  |  |
| 商机总金额 |  |  |
| 成交状态 |  |  |
| 客户来源 |  |  |
| 最后跟进 |  |  |

### 业务描述
{客户做什么、客户服务谁、主要市场是什么；如有证据，补充业务模式/收入来源}

### 战略动态
- {最近 1-2 年的重要变化，标注置信度}

### 上系统动机
- {客户为什么考虑采购或更换系统；标注置信度}

### 信息缺口
- {仍缺少的信息}
```
