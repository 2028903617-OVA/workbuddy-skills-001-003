# R02 决策链识别

## 目标

识别当前商机里“谁说了算、谁影响推进、今天必须问谁”。本规则产出见客就绪度所需的 `decision_chain` 字段，并为 R06 提供风险预警和人力地图，为 R07 提供条件触发的博弈编年人物与关系信号。

## 触发条件

只要 CRM 联系人、会议参与人或跟进记录里出现人物，就执行。即使信息很少，也要返回未知项，不要跳过。

## 角色模型

| 角色 | 含义 | 证据 |
| --- | --- | --- |
| EB | Economic Buyer，预算拍板人/最终决策人 | 签字、批预算、关注 ROI 和成本 |
| TB | Technical Buyer，技术评估人 | 关注安全、集成、实施、API |
| UX | User，业务使用者/需求方 | 描述日常流程和使用痛点 |
| Coach | 内部支持者/教练 | 提供内部情报、安排会议、帮助推动 |
| Gatekeeper | 守门人/阻碍者 | 拖延、过滤信息、反复要求补材料 |

## 识别规则

- CRM `primary_contact=true` 是最强 EB 候选信号，但除非能证明其掌握预算，否则只能标为“EB 候选”。
- 不要臆测 EB、Coach 或 Gatekeeper。不明确就标 `unknown`，并把识别角色作为会议目标。
- Coach 必须有具体支持行为；“态度友好”不等于 Coach。
- Gatekeeper 必须有具体阻碍行为；“不热情”不等于 Gatekeeper。
- 如果今天见的人不是 EB，且 EB 未知，这是重大就绪度缺口。

## 提取契约

先返回以下结构化内容：

```yaml
r02_decision_chain:
  decision_chain: true|false
  eb_known: true|false
  coach_known: true|false
  gatekeeper_known: true|false
  today_attendees:
    - name:
      title:
      inferred_role:
      evidence:
      confidence: confirmed|inferred|unknown
  key_people:
    - name:
      title:
      role: EB|TB|UX|Coach|Gatekeeper|unknown
      relationship: strong_support|neutral|doubtful|opposed|unknown
      first_seen:
      recent_signal:
      evidence:
      confidence: confirmed|inferred|unknown
  decision_path:
    known_path:
    unknown_nodes:
    likely_blockers:
  meeting_objectives:
    - objective:
      reason:
      verification_question:
  risks:
    - risk:
      source:
      severity: fatal|major|minor
```

## 关系信号

- `strong_support`：曾帮助安排关键人、提供内部决策逻辑或主动推动。
- `neutral`：正常参与，但没有帮助或阻碍。
- `doubtful`：提出质疑、拖延承诺或态度摇摆。
- `opposed`：否定价值、阻碍接触或明显偏向竞品。
- `unknown`：没有足够证据。

## 人力地图规则

人力地图回答四个问题：今天影响谁、借力谁、绕开谁、验证谁。

- 默认只保留 3-5 个会影响本次会议推进的人，不输出客户通讯录。
- 优先展示：今天参会人、EB/EB 候选、Coach、Gatekeeper、TB、关键 UX。
- 每个人必须有“今天打法”，即 AE 现场能说或能做的一句话动作。
- 不明确的人物可以写“未知”，但必须说明今天如何识别。
- 人力地图不重复长证据；证据类型收口到 R06 末尾参考来源。

输出字段：

```yaml
people_map:
  - name:
    title:
    role: EB|EB候选|TB|UX|Coach|Gatekeeper|unknown
    stance: 支持|中立|摇摆|阻碍|未知
    today_play:
    verify_question:
```

## 博弈编年衔接

R02 只提供关键人、关系信号、决策路径和角色变化事实。将这些事实交给 `rules/R07_game_timeline_follow_up.md`，由 R07 与互动、承诺、竞品、预算和阶段变化合并为可切换“摘要 / 明细”的博弈编年。不要在 R02 提前截断为 3-5 个节点。

## Markdown 摘要

```markdown
### 👥 人力地图
| 人物 | 角色 | 当前立场 | 今天打法 |
| --- | --- | --- | --- |
| {name_or_unknown} | EB/EB候选 | 支持/中立/未知 | {现场动作或识别问题} |
| {name_or_unknown} | Coach | 支持/未知 | {如何借力} |
| {name_or_unknown} | Gatekeeper | 阻碍/摇摆/未知 | {如何绕开或化解} |

今天必须确认：{top_unknown}
```

如果决策链薄弱，要直接说明，不要用泛泛的“加强关系”掩盖。
