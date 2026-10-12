# R04 决策圈图谱

## 目标

把 R03 的关系温度与完整决策链、组织政治和人力地图合并为“决策圈图谱”，帮助 AE 理解“谁影响谁、谁支持、谁阻碍、谁可能改变局面”。

## 触发条件

存在 CRM 联系人、会议参与人、销售记录或 memory 中的人员信息时执行。

## 角色模型

| 角色 | 含义 |
| --- | --- |
| EB | 预算拍板人/最终决策人 |
| TB | 技术评估人 |
| UX | 业务使用者/需求方 |
| Coach | 内部支持者 |
| Gatekeeper | 守门人/阻碍者 |
| Influencer | 影响者，但不直接拍板 |
| Unknown | 角色未知 |

## 输出契约

```yaml
r04_decision_chain:
  eb:
    name:
    confidence:
    evidence:
  key_people:
    - name:
      title:
      role:
      influence_level: high|medium|low|unknown
      attitude: support|neutral|doubtful|opposed|unknown
      last_seen:
      evidence:
  political_map:
    alliances:
      - description:
    conflicts:
      - description:
    access_paths:
      - path:
  coverage_analysis:
    covered_roles:
      - role:
        people:
    missing_roles:
      - role:
        why_it_matters:
    coverage_ratio:
    key_gap:
    leverage_path:
  risk_kps:
    - name:
      risk:
      impact:
  data_gaps:
    - gap
```

## 分析规则

- 不确定的 EB 必须标为“候选”或“未知”。
- 重点呈现最重要的 10 个 KP；其余人员放入“其他联系人”。
- 组织政治必须有证据，不能凭职位脑补。
- 如果关键人离职、换岗、态度转变，要说明对项目的潜在影响。
- 人力地图不是联系人清单，只呈现对客户认知或机会推进有影响的人。
- 每个关键人必须有“影响判断”：影响谁、受谁影响、可能支持什么、可能阻碍什么。
- 必须输出决策链覆盖分析：已接触哪些关键角色、未覆盖哪些角色、当前最大缺口和可借力路径。
- 覆盖率只能按已确认或强推断的关键角色估算；证据不足时写“覆盖率未知”，不要凑百分比。
- 正文不逐条堆叠来源；证据类型收口到最终档案末尾参考来源，关键不确定项用“推断/未知”标注。

## 人力地图规则

人力地图回答四个问题：谁能拍板、谁能推动、谁会阻碍、谁需要补充验证。

```yaml
people_map:
  core_people:
    - name:
      title:
      role: EB|EB候选|TB|UX|Coach|Gatekeeper|Influencer|Unknown
      attitude: support|neutral|doubtful|opposed|unknown
      influence_level: high|medium|low|unknown
      influence_path:
      risk_or_value:
      confidence: confirmed|inferred|unknown
  missing_people:
    - role:
      why_needed:
      suggested_verification:
```

## Markdown 输出

```markdown
## 👥 决策圈图谱

先展示 R03 产出的“关系温度”，再展示以下决策链与人力地图内容。

### 决策链与人力地图

### 核心决策链
{一句话说明预算、技术、业务、支持者、阻碍者之间的关系}

| 人员 | 职务 | 角色 | 影响力 | 态度 | 证据 |
| --- | --- | --- | --- | --- | --- |

### 人力地图
| 人员 | 角色 | 当前立场 | 影响路径 | 价值/风险 |
| --- | --- | --- | --- | --- |
|  | EB/Coach/TB/UX/Gatekeeper | 支持/中立/摇摆/阻碍/未知 | {影响谁/受谁影响} | {能推动什么/可能卡在哪里} |

### 组织政治
- 支持路径：
- 冲突/阻碍：
- 进入 EB 的路径：

### 决策链覆盖分析
| 维度 | 判断 |
| --- | --- |
| 已覆盖角色 | {EB/TB/UX/Coach/Gatekeeper 中已接触或已确认的角色} |
| 未覆盖角色 | {尚未接触或身份未知的关键角色} |
| 覆盖率 | {如证据充足，写 x/y；否则写未知} |
| 最大缺口 | {当前最影响判断的角色或关系缺口} |
| 可借力路径 | {可通过谁进入关键人或验证关键判断} |

### 风险 KP
- {人名与风险}
```
