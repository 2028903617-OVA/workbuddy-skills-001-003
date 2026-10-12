# CLI 调用规范

## 使用场景

当客户声音洞察需要从纷享销客 CRM 拉取原始声音数据时，读取本文件并按企业 CLI 规范执行查询。

本技能只查询三类业务对象：

| 对象 | 用途 |
| --- | --- |
| 销售记录（`ActiveRecordObj`） | 跟进类型、记录内容、互动内容、负责人、部门、创建时间 |
| 会议记录（`AIMeetingObj`） | 会议主题、会议参与人、会议时间、会议 AI 状态 |
| 会议记录明细（`AIMeetingChunkObj`） | 分块主题、摘要、原文、原业务对象溯源 |

不查询客户、商机、联系人、合同、订单、回款、CSM 预警、流失原因等 L2C 全对象。

## 查询原则

- 以 `ActiveRecordObj.active_record_content`、`ActiveRecordObj.interactive_content`、`AIMeetingObj.remark`、`AIMeetingChunkObj.summary`、`AIMeetingChunkObj.original_content` 为核心。
- 需要归因时，只使用三对象内已有的 `owner`、`owner_department`、`data_own_department`、`created_by`、`initiator`、`inner_participants`、`record_type` 等字段。
- 用户未指定时间范围时，默认最近 30 天。
- 用户指定“上周/月/季度”时，按当前日期解析为绝对日期。
- 查询不到部门、人员、销售记录（`ActiveRecordObj`）或会议记录（`AIMeetingObj`）时，先让用户确认名称。
- 查询结果不足时，写入“信息缺口/样本偏差”，不要编造客户声音。
- `object_api_name` 和 `original_id` 只作为溯源字段，不自动继续查询对应业务对象。

## Step 1：识别范围

范围可以来自用户输入，也可以来自三对象字段：

| 范围 | 推荐字段 |
| --- | --- |
| 负责人 | `owner` |
| 负责人部门 | `owner_department` |
| 数据归属部门 | `data_own_department` |
| 创建人 | `created_by` |
| 会议发起人 | `initiator` |
| 内部参与人 | `inner_participants` |
| 业务类型 | `record_type` |
| 会议状态 | `ai_status`、`status`、`life_status` |
| 原业务对象 | `AIMeetingChunkObj.object_api_name`、`AIMeetingChunkObj.original_id` |

如果需要按人员或部门名称过滤，但当前 CLI 不支持名称直查，可先对三对象按时间范围查询，再在返回结果中根据显示值或 ID 做二次筛选。

## Step 2：查询销售记录（`ActiveRecordObj`）

销售记录（`ActiveRecordObj`）对象描述为“销售记录基本信息”。

推荐查询：

```bash
sharecrm data record query-by-fields \
  --object_api_name ActiveRecordObj \
  --select_fields _id,name,active_record_type,active_record_content,interactive_types,interaction_channels,leads_id,new_opportunity_id,related_object,interactive_content,account_id,interaction_records,owner_department,data_own_department,lock_status,life_status,record_type,owner,out_owner,last_modified_time,create_time,last_modified_by,created_by,meeting_objectives,interactive_processes \
  --create_time-gte <startTime> \
  --create_time-lte <endTime> \
  --sort create_time:desc \
  --limit 200
```

常见过滤：

```bash
--owner-eq <employeeId>
--owner_department-eq <departmentId>
--data_own_department-eq <departmentId>
--created_by-eq <employeeId>
--record_type-eq <recordType>
--active_record_type-eq <activeRecordType>
--interactive_types-eq <interactiveType>
--interaction_channels-eq <interactionChannel>
```

关联字段使用规则：

- `account_id`、`leads_id`、`new_opportunity_id`、`related_object` 只用于溯源、去重和分组，不自动查询客户、线索、商机或关联业务对象。
- `active_record_content` 是 `ActiveRecordObj` 正文的最高优先级字段。
- `interactive_content` 可补充互动过程中的长文本内容。
- `meeting_objectives` 和 `interactive_processes` 可作为会议目标/互动过程的弱信号，不替代正文。

## Step 3：查询会议记录（`AIMeetingObj`）

```bash
sharecrm data record query-by-fields \
  --object_api_name AIMeetingObj \
  --select_fields _id,name,out_owner,last_modified_time,create_time,last_modified_by,created_by,data_own_department,initiator,remark,meeting_file,meeting_file_normal,owner_department,inner_participants,owner,lock_status,life_status,end_time,record_type,ai_status,start_time,ai_meeting_template_id,interactive_render_type,location,fail_reason \
  --create_time-gte <startTime> \
  --create_time-lte <endTime> \
  --sort create_time:desc \
  --limit 200
```

常见过滤：

```bash
--owner-eq <employeeId>
--owner_department-eq <departmentId>
--data_own_department-eq <departmentId>
--created_by-eq <employeeId>
--initiator-eq <employeeId>
--record_type-eq <recordType>
--ai_status-eq <status>
```

如果用户要求“会议开始时间”口径，可将时间过滤字段从 `create_time` 改为 `start_time`。

## Step 4：查询会议记录明细（`AIMeetingChunkObj`）

会议记录明细通过 `meeting_id` 关联会议记录。

```bash
sharecrm data record query-by-fields \
  --object_api_name AIMeetingChunkObj \
  --select_fields _id,name,out_owner,last_modified_time,create_time,last_modified_by,created_by,data_own_department,meeting_id,owner_department,owner,summary,lock_status,life_status,record_type,original_content,object_api_name,original_id,status \
  --create_time-gte <startTime> \
  --create_time-lte <endTime> \
  --sort create_time:desc \
  --limit 500
```

如果已取得会议 ID 列表，优先按会议关联过滤：

```bash
--meeting_id-in <meetingIds>
```

常见过滤：

```bash
--owner-eq <employeeId>
--owner_department-eq <departmentId>
--data_own_department-eq <departmentId>
--created_by-eq <employeeId>
--record_type-eq <recordType>
--status-eq <status>
--object_api_name-eq <objectApiName>
```

## Step 5：趋势对比查询

如果当前周期为 `<startTime> - <endTime>`，默认取上一等长周期作为对比。对销售记录（`ActiveRecordObj`）、会议记录（`AIMeetingObj`）、会议记录明细（`AIMeetingChunkObj`）分别执行同类查询。

销售记录（`ActiveRecordObj`）对比示例：

```bash
sharecrm data record query-by-fields \
  --object_api_name ActiveRecordObj \
  --select_fields _id,name,active_record_type,active_record_content,interactive_types,interaction_channels,related_object,interactive_content,owner,owner_department,data_own_department,record_type,create_time \
  --create_time-gte <compareStartTime> \
  --create_time-lte <compareEndTime> \
  --sort create_time:desc \
  --limit 200
```

会议记录（`AIMeetingObj`）对比示例：

```bash
sharecrm data record query-by-fields \
  --object_api_name AIMeetingObj \
  --select_fields _id,name,owner,owner_department,data_own_department,initiator,inner_participants,remark,record_type,ai_status,start_time,create_time \
  --create_time-gte <compareStartTime> \
  --create_time-lte <compareEndTime> \
  --sort create_time:desc \
  --limit 200
```

会议记录明细（`AIMeetingChunkObj`）对比示例：

```bash
sharecrm data record query-by-fields \
  --object_api_name AIMeetingChunkObj \
  --select_fields _id,name,meeting_id,owner,owner_department,data_own_department,summary,original_content,object_api_name,original_id,status,create_time \
  --create_time-gte <compareStartTime> \
  --create_time-lte <compareEndTime> \
  --sort create_time:desc \
  --limit 500
```

## 查询结果使用规则

- `AIMeetingChunkObj.original_content` 是客户原文的最高价值来源。
- `AIMeetingChunkObj.summary` 适合做高保真摘要和主题聚类。
- `AIMeetingObj.remark` 可补充会议背景，但不替代会议记录明细（AIMeetingChunkObj）原文。
- `ActiveRecordObj.active_record_content` 是销售记录（`ActiveRecordObj`）中的客户声音核心来源。
- `ActiveRecordObj.interactive_content` 可作为互动内容补充，但必须区分客户表达和销售观察。
- `ActiveRecordObj.interactive_types`、`interaction_channels`、`active_record_type` 只能作为场景和类型信号，不替代正文。
- `AIMeetingObj.ai_status`、`AIMeetingObj.fail_reason` 可用于判断样本完整度，不直接代表客户态度。
- `owner_department` 或 `data_own_department` 缺失时，不要强行做部门对比。
- 会议多的部门不一定问题多，可能只是记录更完整；最终报告需标注样本偏差。
- `ActiveRecordObj.account_id/leads_id/new_opportunity_id/related_object` 与 `AIMeetingChunkObj.object_api_name/original_id` 只能说明记录关联来源，不自动扩展查询。
