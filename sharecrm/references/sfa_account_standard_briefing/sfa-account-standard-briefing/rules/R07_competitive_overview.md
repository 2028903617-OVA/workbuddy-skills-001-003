# R07 竞品全貌

## 目标

还原客户处的竞争格局：哪些竞品在场、推进到什么阶段、客户为什么会比较它们、我方相对位置如何。

## 触发条件

存在竞品明细、商机竞品字段、跟进记录、流失原因、Memory 或用户输入中出现竞品时执行。

## 输入来源

- CRM `CompetitiveLinesObj`。
- CRM `NewOpportunityObj.competitors` 或商机备注。
- CRM 跟进记录中的竞品提及。
- 流失原因对象。
- Memory 中历史竞品博弈。
- `references/competitive_reference.md`。

## 竞品阶段

| 阶段 | 含义 |
| --- | --- |
| C0 未知 | 没有竞品信息 |
| C1 线索 | 客户提过竞品，但无明确动作 |
| C2 在场 | 客户明确在比较竞品 |
| C3 深度评估 | 竞品进入 POC、方案或报价 |
| C4 已选择 | 客户已签竞品或历史被竞品赢走 |

## 输出契约

```yaml
r07_competitive_overview:
  competitors:
    - name:
      stage: C0|C1|C2|C3|C4
      evidence:
      quoted_amount:
      customer_reason_to_compare:
      our_advantage:
      our_weakness:
      confidence: confirmed|inferred|unknown
  competitive_history:
    - date:
      competitor:
      result:
      reason:
  current_position:
    summary:
    confidence:
  data_gaps:
    - gap
```

## 分析规则

- 竞品阶段必须由证据支撑；没有证据时写 C0 或“未知”。
- 报价、优劣势、输赢结果只来自 CRM、Memory 或用户明示，不凭常识补齐。
- `references/competitive_reference.md` 只能用于解释常见强弱项，不能替代客户现场证据。
- 如果客户在比较“自研”，也作为竞品处理，重点分析组织能力、预算和上线周期。
- 竞品分析要服务客户认知，不输出进攻话术，除非用户要求销售话术。
- 竞品证据可以写在“证据”列，但不要扩展成逐条来源说明；最终数据来源统一在档案末尾弱引用。

## Markdown 输出

```markdown
## ⚔️ 竞品全貌

### 当前竞品格局
| 竞品 | 阶段 | 客户比较原因 | 已知报价 | 我方优势 | 我方短板 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
|  | C0-C4 |  |  |  |  |  |

### 历史竞品博弈
- {时间 / 竞品 / 结果 / 原因}

### 当前相对位置
{一句话说明我方领先、持平、落后或未知，并说明证据}

### 竞品信息缺口
- {仍不知道的竞品阶段、报价、评估标准或关键影响人}
```
