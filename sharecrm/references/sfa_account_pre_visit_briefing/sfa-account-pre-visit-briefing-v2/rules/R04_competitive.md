# R04 竞争态势

## 目标

判断竞品是否影响今天的会议策略。本规则产出见客就绪度所需的 `competitor_signal_status`、`competitor_stage`、`relationship_ratio`、`differentiation`、`competition_preparation` 字段。

## 触发条件

CRM、跟进记录、memory、用户上下文或公开线索里出现竞品时执行。若没有竞品信号，返回 `competitor_signal_status: none`，不要把未知竞品当作高风险扣分；若有弱信号但无法确认竞品是否在场，返回 `competitor_signal_status: unknown`，并给出探查问题。

## 竞品阶段

| 阶段 | 含义 |
| --- | --- |
| C0 | 当前没有竞品在场证据 |
| C1 | 有弱信号或传闻 |
| C2 | 客户或 CRM 已确认竞品在场 |
| C3 | 竞品进入演示、POC 或技术评估 |
| C4 | 竞品为现有供应商或已签约 |

## 差异化等级

| 等级 | 含义 |
| --- | --- |
| D1 | 我方具备客户关键场景下竞品难以替代的能力 |
| D2 | 我方至少在两个相关维度明显更强 |
| D3 | 能力大体相当，胜负取决于价格、服务、适配度或关系 |
| D4 | 竞品在客户明确优先事项上有实质优势 |

## 关系比

仅在有证据时估算：

```text
relationship_ratio = 我方关键关系强度 / 竞品关系强度
```

使用标准：

- `>1.5`：我方明显领先。
- `0.8-1.5`：基本均势。
- `0.5-0.8`：我方略弱。
- `<0.5`：竞品可能控盘。

若无法估算，设置 `relationship_ratio: null`，并加入缺失字段。

## 提取契约

先返回以下结构化内容：

```yaml
r04_competitive:
  competitor_signal_status: none|unknown|confirmed
  competitor_stage: C0|C1|C2|C3|C4
  competitors:
    - name:
      stage:
      evidence:
      source:
      confidence: confirmed|inferred|unknown
  relationship_ratio:
  differentiation: D1|D2|D3|D4
  competition_preparation:
    comparison_doc: true|false
    talk_track: true|false
    pricing_known: true|false
  scenario_fit_message:
  discovery_question:
  missing_fields:
    - field_name
  risks:
    - risk:
      source:
      severity: fatal|major|minor
```

## 话术规则

不要说“我们更好”。要说：

```markdown
如果你们的场景是 {customer_scene}，我们在 {specific_capability} 上更合适；
如果你们更看重 {competitor_strength}，竞品可能更省心。
```

这样能把竞品对比锚定在客户场景上，也更可信。

## Markdown 摘要

```markdown
### 竞争态势
- 阶段：{C-stage} | 竞品：{names_or_unknown}
- 竞品信号：{none/unknown/confirmed}
- 我方位置：{relationship_summary}
- 差异化：{D-level} | 场景化说法：{scenario_fit_message}
- 今天要探明：{discovery_question}
```

如果竞品处于 `C3` 或 `C4`，除非 CRM 证据表明我方有强 EB/Coach 支持，否则应标为重大或致命风险。
