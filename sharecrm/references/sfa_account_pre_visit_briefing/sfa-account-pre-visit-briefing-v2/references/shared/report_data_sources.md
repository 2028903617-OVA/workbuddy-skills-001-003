# 共享报告数据源

本文件定义客户简报与周日报可使用的 CRM 对象、核心字段和触发条件。生成报告时先用本文件判断“该查什么”，再按 `sharecrm_cli_min_loop.md` 制定最短查询计划。

## 使用原则

- 默认只查能支撑当前报告结论的对象，不为了填满版面补查；见客前客户简报采用“广覆盖、轻量读取、行动收敛”，尽量读取更多会影响今日打法的数据源。
- 先查基础对象，再按触发条件补查扩展对象。
- 字段 apiName 必须以 `identify-with-describe` 或 `describe get` 返回为准；本文件是业务口径，不替代租户实时 schema。
- `account_id`、`new_opportunity_id`、`contact_id`、`owner` 等引用字段过滤时必须使用 `_id`。
- 查不到扩展对象不代表事实不存在，必须按 `crm_query_status.md` 标注查询状态。

## 常用对象

| 业务对象 | object_api_name | 主要用途 | 核心字段 |
| --- | --- | --- | --- |
| 线索 | `LeadsObj` | 线索新增、线索阶段、下次跟进要点 | `_id,name,create_time,leads_stage,next_followed_remark,owner` |
| 客户 | `AccountObj` | 客户基础信息、成交状态、最后跟进、客户活跃度 | `_id,name,create_time,deal_status,account_source,last_deal_closed_time,last_followed_time,owner` |
| 联系人 | `ContactObj` | 决策链、关键人、人力地图 | `_id,name,job_title,primary_contact,create_time,owner` |
| 商机 | `NewOpportunityObj` | 商机金额、阶段、赢率、结单日期、客户关联 | `_id,name,account_id,create_time,sales_stage,amount,probability,probability_amount,sales_status,close_date,owner` |
| 销售记录 | `ActiveRecordObj` | 跟进动态、客户原话、痛点、承诺、竞品信号 | `_id,account_id,new_opportunity_id,interactive_scenario,interactive_types,interactive_types__o,create_time,active_record_content,owner` |
| 竞品明细 | `CompetitiveLinesObj` | 竞品在场状态、报价、优劣势、输赢结果 | `_id,name,competitor_id,advantage,weaknesses,quotation_amount,is_win` |
| 合同 | `ContractObj` | 历史合作、合同金额、合同周期、续约窗口 | `_id,name,account_id,contract_amount,started_time,expired_time,status,owner` |
| 销售订单 | `SalesOrderObj` | 历史成交、订单金额、客户价值 | `_id,name,account_id,create_time,order_amount,owner` |
| 回款 | `PaymentObj` | 回款金额、到账日期、财务风险 | `_id,name,account_id,create_time,payment_time,amount,owner` |
| 人员 | `PersonnelObj` | 内部负责人、AE/CSM/售前/实施识别 | `_id,name,department,owner` |
| 日程 | `ScheduleObj` | 已约会议、参与人、会议时间 | `_id,participants,content,begin_time,end_time,related_object_data,owner` |
| 高级外勤 | `CheckinsObj` | 现场拜访、外勤沟通记录、拜访计划 | `_id,owner,customer_id,communicate_record,new_stat_date,checkins_scene` |
| 任务 | `MethodologyTaskObj` | 销售方法论任务、过程动作 | `_id,name,short_name,note,task_object_api_name,system_type,owner` |
| 待办 | `ActivityTodoObj` | AI 捕获待办、执行人、状态、承诺来源 | `_id,name,todo_type,task_status,execution_time,executor,active_record_id,related_api_names,related_object_data,related_object,ref_source,ai_summary` |
| 互动问题 | `ActivityQuestionObj` | 客户真实问题、建议问题、回答摘要、态度 | `_id,name,question_content,question_type,question_proposer,proposer_attitude,answer_person,answer_user,answer_time,answer_summary,ai_answer_content,ai_answer_time,tags,account_id,leads_id,new_opportunity_id` |
| 需求 | `RequirementObj` | 客户需求、痛点、优先级、我方响应状态 | `_id,name,code,content,clearance_status,response_status,four_quadrant,kano,contact_id,leads_id,account_id,opportunity_id,partner_id,requirement_solve,assessment_dimension,category` |
| 会议记录 | `AIMeetingObj` | 会议纪要、参会人、会议原文、AI 状态 | `_id,name,initiator,remark,start_time,end_time,inner_participants,location,meeting_content,meeting_file,meeting_file_normal,ai_status,fail_reason` |
| 会议记录明细 | `AIMeetingChunkObj` | 会议分块总结、原文、关联业务对象 | `_id,name,summary,meeting_id,original_content,object_api_name,original_id,status` |

## 枚举提醒

`ActiveRecordObj.interactive_scenario` 常见值：

| 业务含义 | 枚举值 |
| --- | --- |
| 产品介绍与首面 | `product_introduction` |
| 需求调研 | `requirements_research` |
| 解决方案讲解与 POC | `POC` |
| 投标与商务谈判 | `bidding` |
| 高层汇报 | `high_level_reporting` |
| 项目启动会 | `project_launch` |
| 客户经营会 | `customer_management` |
| 结项会议 | `closing_meeting` |
| 其他 | `default` |

`ActiveRecordObj.interactive_types` 常见值：

| 业务含义 | 枚举值 |
| --- | --- |
| 电话 | `call` |
| 在线会议 | `meeting` |
| 在线聊天 | `chat` |
| 邮件 | `email` |
| 现场拜访 | `visit` |
| 其他 | `other`，补充内容通常在 `interactive_types__o` |

## 客户简报默认数据源

四类客户简报默认优先查询：

| 对象 | 用途 |
| --- | --- |
| `AccountObj` | 客户基础画像、成交状态、最后跟进 |
| `NewOpportunityObj` | 当前/历史商机、阶段、金额、结单时间 |
| `ContactObj` | 联系人、关键人、决策链候选 |
| `ActiveRecordObj` | 近 3-12 个月互动、客户原话、承诺、痛点、竞品信号 |

## 见客前客户简报广覆盖策略

见客前简报仍然输出短行动简报，但数据源应尽量广覆盖，以免漏掉会影响今日打法的会议、需求、承诺、竞品和历史合作风险。确认唯一客户后，每个对象只做一次字段确认和一次必要查询，失败即记录状态，不反复 loop。

| 覆盖层级 | 对象 | 状态要求 |
| --- | --- | --- |
| 必查基础层 | `AccountObj`、`NewOpportunityObj`、`ContactObj`、`ActiveRecordObj` | 必须读取或明确 `无数据/权限不足/查询失败` |
| 会前过程层 | `ScheduleObj`、`RequirementObj`、`ActivityQuestionObj`、`ActivityTodoObj`、`MethodologyTaskObj`、`AIMeetingObj`、`AIMeetingChunkObj`、`CheckinsObj` | 能确认对象和字段时尽量读取；只提炼今日目标、风险、人、问题和动作所需信息 |
| 风险补充层 | `CompetitiveLinesObj`、`ContractObj`、`SalesOrderObj`、`PaymentObj` | 标准模式轻量读取关键字段；`full` 可展开明细 |

广覆盖不是全量导出：见客前主简报仍只保留结构化会前判断、第一句话、就绪度和行动建议；历史信息只进入条件触发的博弈编年，会后事项只进入拜访后行动清单。

## 客户简报触发补查

| 触发信号 | 补查对象 | 用途 |
| --- | --- | --- |
| 痛点、需求、必选条件不足 | `RequirementObj` | 补充客户需求、优先级、澄清和响应状态 |
| 客户提问、反对意见、现场问答不足 | `ActivityQuestionObj` | 补充真实问题、态度、回答摘要和话题标签 |
| 用户提到今天会议、已约会议、高层会、陪访时间 | `ScheduleObj` | 补充参与人、会议内容、开始/结束时间 |
| 有会议纪要、AI 会议、复盘、高层汇报 | `AIMeetingObj`、`AIMeetingChunkObj` | 补充会议总结、原文、参会信息和业务分块 |
| 待办、承诺、会后动作、交接断档 | `ActivityTodoObj`、`MethodologyTaskObj` | 补充执行人、状态、截止时间和来源摘要 |
| 现场拜访、外勤活跃度、客户触达证明 | `CheckinsObj` | 补充拜访计划、现场沟通和外勤场景 |
| 竞品、竞争、替换、输赢、报价、POC、自研 | `CompetitiveLinesObj` | 补充竞品在场、报价、优劣势和输赢结果 |
| 已成交、历史合作、full、回款/财务/续约风险 | `ContractObj`、`SalesOrderObj`、`PaymentObj` | 补充合同、订单金额、回款金额、回款时间和客户价值 |

## 场景差异

| 场景 | 默认对象 | 常用补查 |
| --- | --- | --- |
| 标准版客户简报 | 客户、商机、联系人、销售记录 | 需求、互动问题、会议、订单、回款 |
| 见客前客户简报 | 客户、商机、联系人、最近销售记录、日程、需求、互动问题、待办/任务、会议、现场拜访、竞品明细、合同、订单、回款 | 外部情报、客户健康/流失字段（仅字段口径可确认时） |
| 高层陪访简报 | 商机、客户、联系人、销售记录 | 日程、会议、互动问题、需求、订单、回款 |
| 团队交接简报 | 客户、商机、联系人、销售记录 | 待办、任务、需求、互动问题、会议、订单、回款 |

## 周日报提示

周日报类报告优先使用聚合查询获取指标，明细只取 Top N、异常项和证据样本。不要用大量明细查询硬算汇总指标。
