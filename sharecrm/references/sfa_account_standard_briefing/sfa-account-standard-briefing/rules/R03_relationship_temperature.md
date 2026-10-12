# R03 关系温度

## 目标

评估客户总体关系温度和关键人关系变化趋势，并作为“决策圈图谱”的关系维度。客户360场景关注“关系为什么是这样”，不是马上怎么行动。

## 触发条件

存在联系人、销售记录、memory 或用户描述的关键人互动时执行。

## 温度定义

| 温度 | 含义 |
| --- | --- |
| +5 | 铁杆支持，主动推动内部决策 |
| +3 | 信任，愿意提供内部信息 |
| +1 | 中性偏正，正常配合 |
| 0 | 中立，无明显支持或阻碍 |
| -1 | 冷淡，需要额外经营 |
| -3 | 有成见或明显保留 |
| -5 | 敌对，主动阻碍推进 |

## 输出契约

```yaml
r03_relationship_temperature:
  overall_temperature:
  trend: warming|cooling|stable|unknown
  reason:
  key_people:
    - name:
      title:
      role:
      temperature:
      trend:
      evidence:
      last_contact_time:
      confidence: confirmed|inferred|unknown
  risk_people:
    - name:
      reason:
      impact:
```

## 分析规则

- 关系温度必须由具体行为支撑。
- Coach 不是“聊得来”，而是提供过内部情报或推动过事项。
- Gatekeeper 不是“不热情”，而是实际阻碍过访问、审批或推进。
- 关系趋势比单次态度更重要：最近 3 个月升温、降温还是持平。
- 关系温度要服务客户认知，不输出见客前行动指令。
- 不确定时写“未知/推断”，不要把友好互动写成强关系。

## Markdown 输出

```markdown
### 关系温度

### 总体关系
{温度与趋势，说明原因}

### 关键人关系
| 人员 | 职务 | 角色 | 温度 | 趋势 | 证据 |
| --- | --- | --- | --- | --- | --- |

### 风险关系
- {可能影响未来推进的关系风险}
```
