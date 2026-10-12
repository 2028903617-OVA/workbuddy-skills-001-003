# CRM 常用对象与字段

本文件记录团队日报、团队周报、团队月报常用的 CRM 对象和字段口径。字段来自企业规范中的“CRM中的常用对象及字段”。

## 常用对象 ApiName

| 业务对象 | ApiName |
|----------|---------|
| 线索 | `LeadsObj` |
| 客户 | `AccountObj` |
| 联系人 | `ContactObj` |
| 商机 | `NewOpportunityObj` |
| 销售订单 | `SalesOrderObj` |
| 回款 | `PaymentObj` |
| 人员 | `PersonnelObj` |
| 销售记录 | `ActiveRecordObj` |
| 日程 | `ScheduleObj` |
| 高级外勤 | `CheckinsObj` |
| 任务 | `MethodologyTaskObj` |
| 待办 | `ActivityTodoObj` |
| 互动问题 | `ActivityQuestionObj` |
| 需求 | `RequirementObj` |
| 会议记录 | `AIMeetingObj` |
| 会议记录明细 | `AIMeetingChunkObj` |

## 团队、人员与目标口径说明

企业规范中当前只明确 `PersonnelObj` 是人员对象，但未提供团队、部门、上级主管、销售目标或任务对象的具体字段。

因此团队报表使用这些信息时遵循：

- 团队成员范围：优先由用户提供，或通过实际 CRM 字段定义查询；不假设固定字段名。
- 负责人字段：不同对象可能字段不同，不要默认所有对象都有 `owner`。
- 目标/配额：没有明确 CRM 字段或用户输入时，不计算目标完成率。
- 任务/P0：没有明确任务对象时，优先使用日程、销售记录、CRM 日志和用户输入推断；本地 memory 仅在 CRM/日志不可用时兜底参考，并标注来源。

如果后续企业补充团队、部门、目标、任务对象字段，应在本文件增加对应章节。

## 客户 AccountObj

| 字段 | 含义 |
|------|------|
| `create_time` | 客户记录创建时间 |
| `name` | 客户名称 |
| `_id` | 客户唯一 ID |
| `deal_status` | 成交状态：未成交、已成交、多次成交 |
| `account_source` | 客户来源，如展会、陌拜、转介绍 |
| `last_deal_closed_time` | 最近一次成交日期 |
| `last_followed_time` | 最后一次跟进日期 |

## 商机 NewOpportunityObj

| 字段 | 含义 |
|------|------|
| `account_id` | 关联客户 |
| `create_time` | 商机创建时间 |
| `name` | 商机名称 |
| `_id` | 商机唯一 ID |
| `sales_stage` | 商机阶段 |
| `amount` | 商机金额 |
| `probability` | 赢率 |
| `probability_amount` | 预测金额，通常为 `amount * probability` |
| `sales_status` | 阶段状态：进行中、赢单、输单、无效 |
| `close_date` | 结单日期 |

## 销售记录 ActiveRecordObj

销售记录即跟进动态，用于记录销售与客户或商机的互动。

| 字段 | 含义 |
|------|------|
| `interactive_scenario` | 互动场景 |
| `interactive_types` | 互动类型 |
| `interactive_types__o` | 当互动类型为“其他”时填写的补充内容 |
| `account_id` | 关联客户 |
| `new_opportunity_id` | 关联商机 |
| `create_time` | 互动发生或记录创建时间 |
| `active_record_content` | 销售记录核心内容 |
| `_id` | 销售记录唯一 ID |

互动场景常见枚举：

| 中文 | 枚举 |
|------|------|
| 产品介绍与首面 | `product_introduction` |
| 需求调研 | `requirements_research` |
| 解决方案讲解与 POC | `POC` |
| 投标与商务谈判 | `bidding` |
| 高层汇报 | `high_level_reporting` |
| 项目启动会 | `project_launch` |
| 客户经营会 | `customer_management` |
| 结项会议 | `closing_meeting` |
| 其他 | `default` |

互动类型常见枚举：

| 中文 | 枚举 |
|------|------|
| 打电话 | `call` |
| 在线会议 | `meeting` |
| 在线聊天 | `chat` |
| 邮件 | `email` |
| 现场拜访 | `visit` |
| 其他 | `other` |

## 销售订单 SalesOrderObj

| 字段 | 含义 |
|------|------|
| `account_id` | 关联客户 |
| `create_time` | 订单创建时间 |
| `name` | 销售订单编号或名称 |
| `order_amount` | 销售订单金额 |

## 回款 PaymentObj

| 字段 | 含义 |
|------|------|
| `account_id` | 关联客户 |
| `create_time` | 回款记录创建时间 |
| `name` | 回款编号或名称 |
| `payment_time` | 实际到账日期 |
| `amount` | 本次实际到账金额 |

## 线索 LeadsObj

| 字段 | 含义 |
|------|------|
| `create_time` | 线索创建时间 |
| `name` | 线索名称 |
| `leads_stage` | 线索阶段：潜在线索、市场认可线索、销售认可线索、转商机 |
| `next_followed_remark` | 下次跟进要点 |

## 联系人 ContactObj

| 字段 | 含义 |
|------|------|
| `create_time` | 联系人创建时间 |
| `name` | 联系人姓名 |
| `job_title` | 职务 |
| `primary_contact` | 是否关键决策人 |

## 日程 ScheduleObj

| 字段 | 含义 |
|------|------|
| `participants` | 参与人 |
| `content` | 日程内容 |
| `begin_time` | 开始时间 |
| `end_time` | 结束时间 |
| `related_object_data` | 关联业务模块 |

## 高级外勤 CheckinsObj

| 字段 | 含义 |
|------|------|
| `owner` | 负责人 |
| `customer_id` | 客户 |
| `communicate_record` | 沟通记录 |
| `new_stat_date` | 计划日期 |
| `checkins_scene` | 外勤场景 |

## 任务 MethodologyTaskObj

任务用于补充方法论、推进动作或任务模板类信息；只有团队 P0/P1 管理动作、承诺来源或任务闭环无法从日志、销售记录、日程、待办中判断时才查询。

| 字段 | 含义 |
|------|------|
| `name` | 任务名称 |
| `short_name` | 任务简称 |
| `note` | 任务描述 |
| `task_object_api_name` | 任务作用的业务对象 |
| `system_type` | 数据系统类型或来源类型 |

## 待办 ActivityTodoObj

待办可用于核对 AI 抽取或销售创建的待执行事项，也可辅助判断 AE/主管动作是否兑现。

| 字段 | 含义 |
|------|------|
| `name` | 待办名称 |
| `todo_type` | 待办类型 |
| `task_status` | 待办状态 |
| `execution_time` | 计划执行或应完成时间 |
| `executor` | 执行人 |
| `active_record_id` | 关联销售记录 |
| `related_api_names` | 关联业务对象 |
| `related_object_data` | 关联业务数据对象信息 |
| `related_object` | 关联具体业务数据 |
| `ref_source` | 原文出处 |
| `ai_summary` | AI 生成的来源摘要 |

## 互动问题 ActivityQuestionObj

互动问题用于补充客户会议或沟通中的真实问题、客户态度和 AI 建议问题；只有风险、需求、异议或主管介入话术缺证据时才查询。

| 字段 | 含义 |
|------|------|
| `name` | 主展示名 |
| `question_content` | 问题内容 |
| `question_type` | 问题类型：互动问题、建议问题 |
| `question_proposer` | 问题提出人 |
| `proposer_attitude` | 问题提出人态度 |
| `answer_person` | 回答人文本 |
| `answer_user` | 回答用户，可关联到联系人或员工 |
| `answer_time` | 回答时间 |
| `answer_summary` | 回答总结 |
| `ai_answer_content` | AI 建议回答内容 |
| `ai_answer_time` | AI 建议回答时间 |
| `tags` | 话题维度 |
| `account_id` | 关联客户 |
| `leads_id` | 关联线索 |
| `new_opportunity_id` | 关联商机 |

## 需求 RequirementObj

需求用于补充客户痛点、需求明确度、响应状态和优先级；不要把产品需求状态直接写成销售推进结果。

| 字段 | 含义 |
|------|------|
| `name` | 需求标题 |
| `code` | 需求编号 |
| `content` | 需求内容 |
| `clearance_status` | 需求明确状态 |
| `response_status` | 我方应答状态 |
| `four_quadrant` | 客方四象限优先级 |
| `kano` | 客方 KANO 优先级 |
| `contact_id` | 需求提出人 |
| `leads_id` | 所属线索 |
| `account_id` | 关联客户 |
| `opportunity_id` | 所属商机 |
| `partner_id` | 所属合作伙伴 |
| `requirement_solve` | 需求解决内容 |
| `assessment_dimension` | 我方评估维度 |
| `category` | 需求分类 |

## 会议记录 AIMeetingObj

会议记录用于补充线上/线下会议纪要、参与人和 AI 分析状态；不要用会议记录替代销售记录事实，除非销售记录缺失且会议记录明确关联客户或商机。

| 字段 | 含义 |
|------|------|
| `name` | 会议主题 |
| `initiator` | 会议发起人 |
| `remark` | 备注 |
| `start_time` | 会议开始时间 |
| `end_time` | 会议结束时间 |
| `ai_status` | AI 分析状态 |
| `meeting_file` | 会议语音附件 |
| `meeting_file_normal` | 会议普通附件 |
| `inner_participants` | 内部参与人 |
| `location` | 会议地点 |
| `fail_reason` | AI 分析失败原因 |
| `meeting_content` | 会议内容 |

## 会议记录明细 AIMeetingChunkObj

会议记录明细用于补充会议原文转写、分段总结和关联业务对象。

| 字段 | 含义 |
|------|------|
| `name` | 明细主题 |
| `summary` | 总结 |
| `meeting_id` | 关联会议记录 |
| `original_content` | 原始语音转写或原始对话内容 |
| `object_api_name` | 明细关联的业务对象名称 |
| `original_id` | 原始数据源唯一标识 |
| `status` | 明细处理或展示状态 |

## 通用字段

| 字段 | 含义 |
|------|------|
| `create_time` | 创建时间 |
| `last_modified_time` | 最后修改时间 |
| `_id` | 记录唯一 ID |
| `created_by` | 创建人 |
| `last_modified_by` | 最后修改人 |
| `owner` | 负责人 |
| `owner_department` | 负责人所在部门 |
| `data_own_department` | 数据归属部门 |
| `relevant_team` | 相关团队 |
| `origin_source` | 数据来源 |
| `record_type` | 业务类型 |
| `life_status` | 生命周期状态 |
| `lock_status` | 锁定状态 |
| `lock_rule` | 锁定规则 |
| `lock_user` | 加锁人 |
| `out_owner` | 外部负责人 |
| `out_tenant_id` | 外部企业或外部租户 |

## 字段使用约束

- 查询字段必须以 CRM 实际字段为准。
- 不确定字段是否存在时，先查询对象字段定义或要求用户补充。
- 不要把中文字段名直接当作 CLI 字段名。
- 不要假设所有对象都有同名负责人字段、团队字段或管理者字段；人员与团队过滤字段必须以实际 CRM 字段定义为准。
- PDF 中被截断或省略号展示的字段名不得直接使用，必须以 `describe get` 返回为准。
- 通用系统字段只用于权限、过滤、审计或数据口径判断；不要在用户可见报表中展示记录 ID、锁定状态、生命周期状态或内部对象名。
