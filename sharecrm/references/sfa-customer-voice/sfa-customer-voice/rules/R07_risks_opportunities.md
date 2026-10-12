# R07 风险与机会

## 目标

把销售记录（`ActiveRecordObj`）和会议记录/会议记录明细（`AIMeetingObj`/`AIMeetingChunkObj`）中的客户声音转化为经营风险、推进风险、产品机会、服务机会和销售管理动作。

## 触发条件

完成 R03-R06 后执行。

## 风险类型

| 风险 | 判断线索 |
| --- | --- |
| 推进停滞 | 预算未批、决策链不清、客户反复追问、审批延期 |
| 竞品替代 | 客户明确比较竞品、竞品报价、自研替换 |
| 产品缺口 | 高频功能缺口、明确需求、影响上线或验收 |
| 交付服务 | 实施周期、响应慢、接口排期、培训不足 |
| 价格预算 | 报价异议、预算冻结、ROI 不清、付款压力 |
| 使用效果 | 一线不愿用、数据质量差、管理层看不到效果 |
| 负面升级 | 抱怨、投诉、强烈不满、要求升级处理 |
| 记录质量 | AI 分析失败、会议记录明细（AIMeetingChunkObj）原文缺失、摘要不足导致无法判断 |

## 机会类型

| 机会 | 判断线索 |
| --- | --- |
| 产品优化 | 多条记录重复反馈的能力缺口或体验问题 |
| 场景扩展 | 新部门、新流程、新模块、更多使用场景表达需求 |
| 行业方案 | 多场会议出现相似场景和共性诉求 |
| 竞品反击 | 客户对竞品短板有明确反馈 |
| 管理动作 | 部门/人员可通过跟进、验证、复盘降低风险 |
| 记录治理 | 修复 AI 分析失败、补充会议记录明细（AIMeetingChunkObj）原文、规范销售记录（ActiveRecordObj） |

## 输出契约

```yaml
r07_risks_opportunities:
  risks:
    - risk:
      risk_type:
      level: high|medium|low|unknown
      affected_sources:
        - source_object:
          source_record_id:
          meeting_id:
          source_title:
      related_topics:
        - topic:
      impact:
      trigger:
      suggested_owner: AE|sales_manager|department_leader|CEO|product|delivery|service|data_owner|unknown
      mitigation_direction:
      confidence: confirmed|inferred|unknown
  opportunities:
    - opportunity:
      opportunity_type:
      affected_sources:
        - source_object:
          source_record_id:
          meeting_id:
          source_title:
      related_topics:
        - topic:
      business_value:
      suggested_owner:
      next_validation:
      confidence: confirmed|inferred|unknown
  priority_actions:
    - action:
      purpose:
      owner_or_role:
      timing:
      related_risk_or_opportunity:
      confidence: confirmed|inferred|unknown
  data_gaps:
    - gap
```

## 风险等级

| 等级 | 判断标准 |
| --- | --- |
| 高 | 可能影响关键推进、客户关系、上线验收、跨部门经营判断，或出现强烈负面/升级信号 |
| 中 | 影响局部推进、客户满意度、使用效果或短期管理动作 |
| 低 | 需要关注，但短期不改变主要判断 |
| 未知 | 证据不足，无法判断影响级别 |

## 分析规则

- 不把每个客户问题都升级为经营风险。
- 高风险必须有强度、频次、跨部门重复、明确升级、关键会议来源或负责人明确需要处理等证据支撑。
- 机会必须说明业务价值，不输出泛泛的“优化产品/提升服务”。
- 建议动作必须绑定责任角色和目的。
- CEO 视角建议动作不超过 5 条，必须聚焦跨部门和高强度问题。
- 销售管理者/部门负责人视角可输出 5-7 条，强调管理动作和记录闭环。
- AE 视角建议动作围绕客户核对、需求验证、风险跟进和记录补充。
- 记录质量问题可以作为风险，但必须和 `ai_status/fail_reason/original_content` 缺失等字段相关。

## Markdown 输出

```markdown
## 6. ⚠️ 风险与机会

### 风险矩阵
| 等级 | 风险 | 影响来源 | 业务影响 | 触发条件 | 建议责任方 | 置信度 |
| --- | --- | --- | --- | --- | --- | --- |
| 高/中/低 |  | 销售记录（ActiveRecordObj）/会议记录（AIMeetingObj）/会议记录明细（AIMeetingChunkObj） |  |  |  | 确认/推断/未知 |

### 机会信号
| 机会 | 影响来源 | 业务价值 | 下一步验证 | 建议责任方 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
```
