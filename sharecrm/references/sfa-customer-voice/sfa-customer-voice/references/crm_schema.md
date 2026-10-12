# CRM 字段映射参考

仅在需要解释原始 CRM 字段、用户粘贴数据或 CLI 查询结果时读取本文件。

## 客户声音业务对象

本技能只使用三类原始业务对象：

| 中文名称 | 对象 API Name | 对应规则 |
| --- | --- | --- |
| 销售记录 | `ActiveRecordObj` | R02 客户声音抽取、R03 主题聚类、R04 趋势 |
| 会议记录 | `AIMeetingObj` | R01 范围、R02 声音抽取、R05 归因 |
| 会议记录明细 | `AIMeetingChunkObj` | R02 声音抽取、R03 主题聚类、R06 代表性原文 |

不查询客户、商机、联系人、合同、订单、回款、CSM 预警、流失原因等 L2C 全对象。

## 销售记录（ActiveRecordObj）字段

销售记录（`ActiveRecordObj`）对象描述为“销售记录基本信息”。

| 字段 | 含义 | 使用方式 |
| --- | --- | --- |
| `_id` | 销售记录系统 ID | 溯源 |
| `name` | 记录 ID/自增编号 | 记录识别，不作为声音内容 |
| `active_record_type` | 跟进类型 | 跟进类型归因 |
| `active_record_content` | 记录内容 | 销售记录客户声音核心字段 |
| `interactive_types` | 互动类型 | 互动场景弱信号 |
| `interaction_channels` | 互动渠道 | 渠道归因，如电话、会议、拜访等 |
| `leads_id` | 关联线索 | 溯源和分组，不自动查询线索对象 |
| `new_opportunity_id` | 关联商机 | 溯源和分组，不自动查询商机对象 |
| `related_object` | 关联业务模块 | 溯源和分组，不自动查询关联对象 |
| `interactive_content` | 互动内容 | 长文本补充字段，可抽取客户声音 |
| `account_id` | 关联客户 | 溯源和分组，不自动查询客户对象 |
| `interaction_records` | 互动语料 | 附件/语料线索，通常不直接作为文本结论 |
| `owner_department` | 负责人主属部门 | 部门归因 |
| `data_own_department` | 归属部门 | 部门归因、权限口径 |
| `lock_status` | 锁定状态 | 数据状态 |
| `life_status` | 生命状态 | 数据有效性 |
| `record_type` | 业务类型 | 业务类型归因 |
| `owner` | 负责人 | 负责人归因 |
| `out_owner` | 外部负责人 | 如有值，可作为外部参与/客户侧线索 |
| `last_modified_time` | 最后修改时间 | 数据时效 |
| `create_time` | 创建时间 | 时间范围和趋势 |
| `last_modified_by` | 最后修改人 | 数据维护人 |
| `created_by` | 创建人 | 记录创建人归因 |
| `meeting_objectives` | 会议目标 | 目标/场景弱信号 |
| `interactive_processes` | 互动过程 | 互动过程弱信号 |

## 会议记录（AIMeetingObj）字段

| 字段 | 含义 | 使用方式 |
| --- | --- | --- |
| `_id` | 会议记录 ID | 与会议记录明细（AIMeetingChunkObj）的 `meeting_id` 关联 |
| `name` | 会议主题 | 主题弱信号、会议识别 |
| `out_owner` | 外部负责人 | 如有值，可作为外部参与/客户侧线索 |
| `last_modified_time` | 最后修改时间 | 数据时效 |
| `create_time` | 创建时间 | 默认时间范围 |
| `last_modified_by` | 最后修改人 | 数据维护人 |
| `created_by` | 创建人 | 记录创建人归因 |
| `data_own_department` | 归属部门 | 部门归因、权限口径 |
| `initiator` | 会议发起人 | 会议视角归因 |
| `remark` | 备注 | 会议背景、客户声音补充 |
| `meeting_file` | 会议语音附件 | 原始材料线索 |
| `meeting_file_normal` | 会议附件 | 原始材料线索 |
| `owner_department` | 负责人所在部门 | 部门归因 |
| `inner_participants` | 内部参与人 | 内部参与视角归因 |
| `owner` | 负责人 | 负责人归因 |
| `lock_status` | 锁定状态 | 数据状态 |
| `life_status` | 生命状态 | 数据有效性 |
| `end_time` | 会议结束时间 | 会议时间范围 |
| `record_type` | 业务类型 | 业务类型归因 |
| `ai_status` | AI 分析状态 | 样本完整度、失败风险 |
| `start_time` | 会议开始时间 | 会议时间范围 |
| `ai_meeting_template_id` | 会议模板 | 会议类型弱信号 |
| `interactive_render_type` | 会议内容渲染类型 | 内容形态 |
| `location` | 会议地点 | 场景补充 |
| `fail_reason` | AI 分析失败原因 | 样本缺口和处理风险 |

## 会议记录明细（AIMeetingChunkObj）字段

| 字段 | 含义 | 使用方式 |
| --- | --- | --- |
| `_id` | 明细 ID | 溯源 |
| `name` | 分块主题 | 主题弱信号 |
| `out_owner` | 外部负责人 | 如有值，可作为外部参与/客户侧线索 |
| `last_modified_time` | 最后修改时间 | 数据时效 |
| `create_time` | 创建时间 | 时间范围和趋势 |
| `last_modified_by` | 最后修改人 | 数据维护人 |
| `created_by` | 创建人 | 记录创建人归因 |
| `data_own_department` | 归属部门 | 部门归因、权限口径 |
| `meeting_id` | 会议记录 | 关联 `AIMeetingObj._id` |
| `owner_department` | 负责人所在部门 | 部门归因 |
| `owner` | 负责人 | 负责人归因 |
| `summary` | 总结 | 高保真摘要、主题聚类 |
| `lock_status` | 锁定状态 | 数据状态 |
| `life_status` | 生命状态 | 数据有效性 |
| `record_type` | 业务类型 | 业务类型归因 |
| `original_content` | 原文 | 客户声音最高价值字段 |
| `object_api_name` | 业务记录对象 | 原业务对象溯源，不自动扩展查询 |
| `original_id` | 原文 ID/原记录 ID | 原业务记录溯源，不自动扩展查询 |
| `status` | 状态 | 明细处理状态 |

## 三对象关联

| 关系 | 说明 |
| --- | --- |
| `AIMeetingChunkObj.meeting_id` -> `AIMeetingObj._id` | 会议记录明细归属会议记录 |
| `AIMeetingChunkObj.object_api_name` + `original_id` | 指向原业务记录，仅用于溯源和分组 |
| `AIMeetingChunkObj.object_api_name/original_id` -> `ActiveRecordObj._id` | 若会议记录明细指向销售记录（ActiveRecordObj），可作为同源声音合并依据 |

## 最小可用输入

没有 CLI 或 CRM 工具输出时，最小输入为：

```text
分析视角：
时间范围：
负责人/部门/会议发起人/内部参与人：
销售记录（ActiveRecordObj）active_record_content：
销售记录（ActiveRecordObj）interactive_content：
会议记录（AIMeetingObj）：
会议记录明细（AIMeetingChunkObj）summary：
会议记录明细（AIMeetingChunkObj）original_content：
业务类型：
仍不确定的信息：
```

缺失项进入 R08 开放问题，不要静默补齐。
