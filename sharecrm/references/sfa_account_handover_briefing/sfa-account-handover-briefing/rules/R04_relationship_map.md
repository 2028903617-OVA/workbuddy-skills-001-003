# R04 关系温度与关键人地图

## 目标

整理客户组织中的关键人、角色、关系温度、联络注意事项和内部政治，确保接手人知道“先找谁、别绕过谁、哪些关系有历史包袱”。

## 触发条件

存在 CRM 联系人、会议参与人、Memory 关系卡、跟进记录或用户描述的关键人信息时执行。

## 输入来源

- CRM `ContactObj`。
- CRM `ActiveRecordObj` 中的参与人和客户原话。
- Memory 中的关键人关系卡、关系温度变化、关键事件。
- 商机审批链、合同签署人、客户健康/投诉记录中的人员信息。

## 角色模型

| 角色 | 含义 |
| --- | --- |
| EB | 预算拍板人/最终决策人 |
| TB | 技术评估人 |
| UX | 业务使用者/需求方 |
| Coach | 内部支持者，会提供信息或推动事项 |
| Gatekeeper | 守门人/阻碍者，会影响访问、审批或节奏 |
| Influencer | 影响者，不直接拍板但能改变判断 |
| Unknown | 角色未知 |

## 关系温度

| 温度 | 含义 |
| --- | --- |
| +5 | 铁杆支持，主动推动内部决策 |
| +3 | 信任，愿意提供内部信息 |
| +1 | 中性偏正，正常配合 |
| 0 | 中立，无明显支持或阻碍 |
| -1 | 冷淡，需要重新经营 |
| -3 | 有成见或明显保留 |
| -5 | 敌对，主动阻碍推进 |

## 输出契约

```yaml
r04_relationship_map:
  overall_relationship:
    temperature:
    trend: warming|cooling|stable|unknown
    reason:
  key_people:
    - name:
      title:
      role:
      influence_level: high|medium|low|unknown
      attitude: support|neutral|doubtful|opposed|unknown
      temperature:
      trend:
      evidence:
      contact_note:
      do_not:
      needs_original_ae_intro: true|false|unknown
      confidence: confirmed|inferred|unknown
  political_map:
    alliances:
      - description:
    conflicts:
      - description:
    access_paths:
      - path:
  receiver_first_contacts:
    - name:
      reason:
      suggested_sequence:
  relationship_gaps:
    - gap
```

## 分析规则

- 关系温度必须由具体行为支撑，不能只写“关系不错”。
- Coach 必须有支持行为：提供内部信息、安排会议、推动审批、帮忙协调资源。
- Gatekeeper 必须有阻碍行为：拖延、卡流程、反复要求材料、限制访问、影响审批。
- CRM 主联系人不等于 EB；EB 不明确时标注“未知/候选”。
- 如果需要原 AE 引荐，必须写明原因和引荐对象。
- 展示最重要的 10 个关键人即可；其余人员可归入“其他联系人”。
- 涉及联系方式时，只用于交接内部流转，不要写成对外可分享内容。

## 结构化文本输出

```markdown
## 4. 关系温度与关键人地图

### 总体关系
{总体温度、趋势和原因}

### 关键人交接卡
| 人员 | 职务 | 角色 | 影响力 | 态度 | 温度 | 联络注意事项 | 绝对不要 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | EB/TB/UX/Coach/Gatekeeper/Influencer/Unknown | 高/中/低/未知 | 支持/中立/反对/未知 | -5 到 +5 |  |  |  |

### 客户内部政治
- 支持路径：
- 冲突/阻碍：
- 进入 EB 的路径：

### 接手人优先联系顺序
1. {人名}：{原因}
2. {人名}：{原因}

### 关系缺口
- {缺少 EB、Coach、Gatekeeper、联络习惯、原 AE 引荐信息等}
```
