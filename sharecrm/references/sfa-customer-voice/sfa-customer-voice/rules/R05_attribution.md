# R05 角色/部门/人员视角归因

## 目标

把客户声音按用户指定视角进行归因，解释“这些声音主要来自哪些销售记录（ActiveRecordObj）/会议记录（AIMeetingObj）/会议记录明细（AIMeetingChunkObj）、由谁负责、集中在哪个部门或业务类型、为什么值得关注”。

## 触发条件

完成 R03 主题聚类和 R04 趋势判断后执行。

## 归因维度

| 维度 | 用途 |
| --- | --- |
| 角色视角 | CEO、销售管理者、部门负责人、AE 对同一声音关注点不同 |
| 负责人 | 基于 `owner` 识别负责人名下记录和会议中的高频声音 |
| 负责人部门 | 基于 `owner_department` 识别部门声音集中度 |
| 数据归属部门 | 基于 `data_own_department` 识别权限/数据口径下的部门分布 |
| 创建人 | 基于 `created_by` 识别记录创建来源 |
| 会议发起人 | 基于 `initiator` 识别会议组织视角 |
| 内部参与人 | 基于 `inner_participants` 识别参与人相关声音 |
| 业务类型 | 基于 `record_type` 识别不同记录/会议类型下的声音差异 |
| 原业务对象 | 基于 `object_api_name/original_id` 做溯源分组，不自动扩展查询 |
| 会议状态 | 基于 `ai_status/status/fail_reason` 判断样本质量和记录风险 |

## 输出契约

```yaml
r05_attribution:
  view_type:
  attribution_summary:
    main_source:
    main_reason:
    business_interpretation:
    confidence: confirmed|inferred|unknown
  by_owner_department:
    - department:
      voice_count:
      meeting_count:
      sales_record_count:
      top_topics:
        - topic:
      risk_level: high|medium|low|unknown
      interpretation:
  by_owner:
    - owner:
      voice_count:
      meeting_count:
      sales_record_count:
      top_topics:
        - topic:
      key_sources:
        - source_title:
          source_record_id:
      risk_or_opportunity:
      suggested_attention:
  by_initiator:
    - initiator:
      top_topics:
        - topic:
      interpretation:
  by_inner_participant:
    - participant:
      top_topics:
        - topic:
      interpretation:
  by_record_type:
    - record_type:
      top_topics:
        - topic:
      impact:
  by_original_ref:
    - object_api_name:
      original_id_count:
      top_topics:
        - topic:
      interpretation:
  data_quality:
    ai_failed_meetings:
    missing_original_content:
    interpretation:
  data_gaps:
    - gap
```

## 视角化输出规则

### CEO 视角

- 只保留影响经营判断的声音：高频负面、跨部门共性、产品战略信号、强竞品信号、预算/审批卡点、记录质量风险。
- 不展开每个销售人员的琐碎明细，除非存在明显异常。
- 建议动作面向负责人机制：销售管理者、产品、交付、服务团队。

### 销售管理者视角

- 强调部门/人员差异、会议记录（AIMeetingObj）和销售记录（ActiveRecordObj）质量、预算/决策/竞品等推进风险。
- 可输出负责人 Top 风险来源记录和待跟进主题。
- 关注“哪些声音反映销售过程问题”：预算未确认、决策链不清、竞品信息不清、需求未穿透、会议记录缺原文。

### 部门负责人视角

- 强调本部门销售记录（ActiveRecordObj）和会议记录（AIMeetingObj）中的高频问题、重点负责人、短期动作。
- 可与全局或上一周期对比，但不把其他部门作为主要篇幅。

### AE 视角

- 只关注本人负责、创建、发起或参与的记录和会议。
- 输出重点来源记录、声音、风险、建议跟进方向。
- 不输出跨部门经营判断，除非与该 AE 记录直接相关。

### 会议视角

- 强调会议记录（AIMeetingObj）主题、会议记录明细（AIMeetingChunkObj）原文、AI 分析状态、发起人和内部参与人。
- `ai_status` 失败或 `fail_reason` 非空时，必须说明样本质量影响。

## 分析规则

- 归因不是甩锅；必须把客户声音、记录来源和可管理动作连接起来。
- 如果某部门或人员声音多，先判断是否因为会议记录（AIMeetingObj）/销售记录（ActiveRecordObj）更完整，而不是直接判断问题更多。
- 人员排名必须谨慎，样本不足时不做强比较。
- 强负面、跨部门重复、负责人明确需要处理的声音优先级可以高于一般高频声音。
- 不把客户声音归因到产品/交付/销售某一方，除非记录内容证据明确。
- `object_api_name/original_id` 只能用于溯源和分组，不据此推断完整业务状态。

## Markdown 输出

```markdown
## 4. 🧭 角色/部门/人员视角归因

### 归因摘要
{从当前视角解释客户声音主要集中在哪里、为什么值得关注}

### 部门/人员分布
| 维度 | 样本 | 高频主题 | 风险等级 | 解读 |
| --- | --- | --- | --- | --- |
|  |  |  | 高/中/低/未知 |  |

### 会议记录/销售记录类型分布
| 维度 | 高频声音 | 对业务的影响 |
| --- | --- | --- |
| 负责人/部门/会议发起人/内部参与人/业务类型 |  |  |

### 记录质量归因
- {AI 分析失败、会议记录明细（AIMeetingChunkObj）原文缺失、ActiveRecordObj.active_record_content 不足等样本质量问题}

### 归因注意事项
- {样本偏差、记录质量、归因不确定项}
```
