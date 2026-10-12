# R05 见客就绪度

## 目标

把 R01-R04 的输出转换为一致的见客就绪度。只要输入能整理成 JSON，优先使用确定性脚本 `scripts/calc_ready_score.py`。

见客就绪度衡量的是“这场会准备得是否充分”，不是赢单预测。

## 触发条件

在 R06 输出最终简报前始终执行。

## 脚本输入契约

根据 R01-R04 组装以下 JSON：

```json
{
  "basic_info": true,
  "decision_chain": true,
  "recent_interactions": true,
  "business_pain": true,
  "financial_or_strategy_signal": false,
  "last_updated": "2026-05-14",
  "pain_points": [
    {
      "product_fit": "P1",
      "evidence": "E1",
      "last_mentioned": "2026-05-10"
    }
  ],
  "competitor_signal_status": "confirmed",
  "competitor_stage": "C2",
  "relationship_ratio": 1.0,
  "differentiation": "D2",
  "competition_preparation": {
    "comparison_doc": false,
    "talk_track": true,
    "pricing_known": false
  },
  "crm_probability": 65
}
```

运行：

```bash
python3 scripts/calc_ready_score.py input.json
```

也可以把 JSON 通过标准输入传给脚本。

## 字段映射

| 脚本字段 | 来源 |
| --- | --- |
| `basic_info` | R01 `scoring_flags.basic_info` |
| `recent_interactions` | R01 `scoring_flags.recent_interactions` |
| `financial_or_strategy_signal` | R01 `scoring_flags.financial_or_strategy_signal`，或 full 模式下的 R09 |
| `decision_chain` | R02 `decision_chain` |
| `business_pain` | R03 `business_pain` |
| `pain_points[]` | R03 `pain_points[]` |
| `competitor_signal_status` | R04 `competitor_signal_status` |
| `competitor_stage` | R04 `competitor_stage` |
| `relationship_ratio` | R04 `relationship_ratio` |
| `differentiation` | R04 `differentiation` |
| `competition_preparation` | R04 `competition_preparation` |
| `crm_probability` | R01 当前商机赢率 |

未知字段按实际情况传 `false`、`null` 或省略。不要为了抬高分数而编造值。竞品字段必须区分：`competitor_signal_status=none` 表示当前没有竞品信号，不按竞品风险重罚；`unknown` 表示存在弱信号或信息未核实，按中度风险处理；`confirmed` 表示竞品已在场，再结合 `C2-C4`、关系比和差异化计算风险。

## 评分逻辑

脚本使用以下权重：

- 信息完整度：35%。
- 痛点匹配度：35%。
- 竞争安全度：30%，按 `100 - competitive_risk` 计算。
- CRM 赢率校准：`+5`、`0`、`-5` 或 `-10`。

信息完整度由五个标志组成：

- 基础信息：10%。
- 决策链：25%。
- 近期互动：25%。
- 业务痛点：20%。
- 财务或战略信号：20%。

痛点匹配度按以下逻辑计算：

```text
产品匹配度 * 证据等级 * 时效系数
```

竞争风险度参考：

- 竞品信号状态：`none | unknown | confirmed`。
- 竞品阶段。
- 关系比。
- 差异化等级。
- 竞争准备资产。

## 输出契约

返回以下结构化内容：

```yaml
r05_readiness:
  information_completeness:
  pain_point_match:
  competitive_risk:
  crm_probability_adjustment:
  readiness:
  readiness_grade:
    color:
    label:
  competitive_grade:
    color:
    label:
  missing_fields:
    - field_name
  weakest_dimension:
  meeting_recommendation:
```

## 会议建议规则

- `80-100`：直接争取下一步明确承诺。
- `60-79`：可以推进，但会议前半段要补齐最大缺口。
- `40-59`：缩小会议目标，优先探需、确认 EB 或验证预算。
- `0-39`：建议延期或先做研究；除非用户明确表示会议不能改。

## Markdown 摘要

```markdown
### 见客就绪度
- 信息完整度：{score}/100
- 痛点匹配度：{score}/100
- 竞争风险度：{score}/100
- 综合就绪度：{score}/100 {grade}
- 最大缺口：{weakest_dimension or missing_fields}
- 会议建议：{recommendation}
```

如果因为脚本无法运行而手工计算，必须说明，并保持同样的输出结构。
