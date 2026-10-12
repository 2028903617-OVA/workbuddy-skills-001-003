# CLI 调用规范

## 使用场景

当本技能需要从 CRM 拉取客户、商机、联系人、销售记录、合同、订单、回款、CSM 预警、流失原因或竞品明细时，读取本文件并按企业 CLI 规范查询。

## 查询原则

- 先查询客户 `AccountObj`，拿到客户记录 `_id`。
- 再使用客户 `_id` 查询关联对象。
- 用户未指定时间范围时，不主动添加时间过滤条件。
- 查询不到客户时，先让用户确认客户名称。
- 查到多个客户时，先让用户选择目标客户。
- 查询结果不足时，明确写入缺失字段，不要编造 CRM 数据。
- 区分“查询成功但 0 条”和“权限不足/查询失败”。权限不足只能说明本轮无法读取，不能说明对象没有数据。
- 同一对象出现权限不足或不可恢复错误后，本轮不要重复查询该对象，也不要继续查询依赖该对象结果的扩展对象。
- 同一轮已经确认过对象字段时，复用已确认字段，不要重复 describe。
- 见客前简报采用广覆盖轻量读取：确认唯一客户后，尽量读取会影响今日打法的 CRM 对象；广覆盖不是全量导出，每个对象只做必要查询，失败后记录状态并停止重复 loop。

## Step 1：查询客户

客户定位按确定性从高到低执行：CRM 客户 ID、客户编号、客户名称字段模糊查询、名称归一化候选。只要上下文、用户输入或页面选中记录里已经有 CRM 客户 `_id`，必须直接按 ID 查询，不要再把客户名称拿去二次解析。

如果已有 CRM 客户 `_id`，直接查询：

```bash
sharecrm data record get-by-id --object_api_name AccountObj --id "<客户_id>"
```

如需控制返回字段，也可以用 `_id` 精确字段查询：

```bash
sharecrm data record query-by-fields \
  --object_api_name AccountObj \
  --select_fields "_id,name,account_no,deal_status,last_deal_closed_time,last_followed_time,last_modified_time" \
  --_id-eq "<客户_id>" \
  --limit 1 \
  --raw
```

如果用户提供了客户编号，或截图中能看到客户编号，用客户编号精确查询：

```bash
sharecrm data record query-by-fields \
  --object_api_name AccountObj \
  --select_fields "_id,name,account_no,deal_status,last_deal_closed_time,last_followed_time,last_modified_time" \
  --account_no-eq "<客户编号>" \
  --limit 10 \
  --raw
```

只有在没有客户 `_id` 和客户编号、只能使用客户名称或名称片段时，才执行客户名称查询。客户名称识别必须优先贴近 CRM 列表页的“客户名称”搜索语义：用户输入“易动纷享”这类客户名称片段时，先查 `AccountObj.name LIKE <关键词>`，不要先把关键词交给 `query-by-name` 做语义归一化。`query-by-name` 适合在不知道实体属于哪条记录、需要候选归一时使用，但它的召回结果不等同于客户名称字段的模糊查询，可能漏掉“北京易动纷享科技有限责任公司”这类包含关键词的客户。

客户名称字段模糊查询：

```bash
sharecrm data record query-by-fields \
  --object_api_name AccountObj \
  --select_fields "_id,name,account_no,deal_status,last_deal_closed_time,last_followed_time,last_modified_time" \
  --name-like "<客户名称关键词>" \
  --limit 20 \
  --sort last_modified_time:desc \
  --raw
```

只有当字段模糊查询未命中、用户给的是简称/别名/口语化实体名，或需要从多个对象候选中做名称归一时，才补充使用 `query-by-name`：

```bash
sharecrm data record query-by-name --name <客户名称> --object_api_names AccountObj
```

处理规则：

- 字段查询或 `query-by-name` 只返回 1 条明确客户时，取 `_id` 作为后续 `<accountId>`。
- 字段查询或 `query-by-name` 返回多条候选时，不要自行排除“看起来不像”的候选，也不要直接说 CRM 没有该客户；必须把候选客户名称、客户编号、`_id` 展示给用户确认。
- 如果按 `_id` 能查到、但按具体名称查不到，后续必须使用 `_id` 查询到的记录作为准，不要继续否定该客户存在；同时在查询状态中说明“名称查询未召回，已按 ID 读取”。
- 字段查询和 `query-by-name` 都查不到时，只能说明“当前查询条件下未查到该客户”；不得表述为“CRM 中没有该客户记录”。如果用户提供的网页截图显示存在，应优先核对查询字段、客户编号、列表页筛选条件、数据权限或名称索引同步状态。

## Step 2：查询关联 CRM 数据

确认唯一客户后，先查询 normal 模式基础数据源，再对会前过程层和风险补充层做轻量广覆盖；full 模式或用户明确要求时再展开历史/财务明细。对每个关联对象分别执行 `query-by-fields`：

```bash
sharecrm data record query-by-fields \
  --object_api_name <objectApiName> \
  --select_fields <fields> \
  --account_id-eq <accountId> \
  --sort last_modified_time:desc \
  --limit 50
```

关联客户字段统一使用 `account_id`，不要把前端字段、展示字段或猜测字段拼成 `accountId`、`_accountId`、`customer_id` 等条件。商机对象统一使用 `NewOpportunityObj`，不要改写成 `SalesOpportunityObj`。如果字段或对象不确定，先查询对象描述，不要凭记忆改字段名。

如用户明确指定时间范围，再追加：

```bash
--last_modified_time-gte <startTime> --last_modified_time-lte <endTime>
```

时间格式：`yyyy-MM-dd HH:mm:ss`。

## 时间与人员解析

- `currentDateTime` 用于解析“今天”“本周”“最近三个月”等相对时间。
- `currentEmployeeName` 用于解析“我”“我负责的”“分配给我的”等当前人员语义。
- 用户显式提供具体时间或具体人员时，以用户输入为准。

## 默认数据源

normal 模式基础查询：

| 对象 | 查询字段 | 用途 |
| --- | --- | --- |
| `NewOpportunityObj` | `_id,name,sales_stage,amount,probability,close_date,sales_status` | 当前商机、阶段、金额、赢率、结单日期 |
| `ContactObj` | `_id,name,job_title,primary_contact` | 联系人和关键决策人 |
| `ActiveRecordObj` | `interactive_scenario,interactive_types,active_record_content,create_time` | 最近互动记录、结论、情绪、承诺 |

normal 模式广覆盖轻量查询：

| 对象 | 查询字段 | 用途 |
| --- | --- | --- |
| `ScheduleObj` | `_id,participants,content,begin_time,end_time,related_object_data,owner` | 今日会议、计划拜访、参会人 |
| `RequirementObj` | `_id,name,content,clearance_status,response_status,four_quadrant,kano,account_id,opportunity_id,requirement_solve,category` | 需求、痛点、必选条件、响应状态 |
| `ActivityQuestionObj` | `_id,name,question_content,question_type,question_proposer,proposer_attitude,answer_summary,tags,account_id,new_opportunity_id` | 客户问题、异议、态度、回答摘要 |
| `ActivityTodoObj` | `_id,name,todo_type,task_status,execution_time,executor,active_record_id,related_object_data,ref_source,ai_summary` | 待办、承诺、执行人、状态 |
| `MethodologyTaskObj` | `_id,name,short_name,note,task_object_api_name,system_type,owner` | 销售方法论任务、过程动作 |
| `AIMeetingObj` | `_id,name,initiator,remark,start_time,end_time,inner_participants,meeting_content,ai_status` | 会议纪要、参会人、会议总结 |
| `AIMeetingChunkObj` | `_id,name,summary,meeting_id,original_content,object_api_name,original_id,status` | 会议分块、原文摘要、关联业务对象 |
| `CheckinsObj` | `_id,owner,customer_id,communicate_record,new_stat_date,checkins_scene` | 现场拜访、外勤沟通、触达证明 |
| `CompetitiveLinesObj` | `_id,name,competitor_id,advantage,weaknesses,quotation_amount,is_win` | 竞品明细、报价、优劣势 |
| `ContractObj` | `_id,name,contract_amount,started_time,expired_time,status` | 合同签约历史、续约窗口 |
| `SalesOrderObj` | `_id,name,order_amount,order_status,payment_amount,receivable_amount` | 订单与回款情况 |
| `PaymentObj` | `_id,name,payment_time,amount,account_id,owner` | 独立回款记录、到账日期、回款金额 |

full 模式或用户要求历史/财务/风险分析时再查询：

| 对象 | 查询字段 | 用途 |
| --- | --- | --- |
| `ContractObj` | `_id,name,contract_amount,started_time,expired_time,status` | 合同签约历史 |
| `SalesOrderObj` | `_id,name,order_amount,order_status,payment_amount,receivable_amount` | 订单与回款情况 |

客户健康、CSM 预警、流失原因等如依赖企业自定义对象或字段，不在本通用规范中硬编码；仅在用户提供字段口径、租户 schema 可确认，或企业标准 reference 已明确时再查询。无法确认时，应通过合同、订单、回款、互动记录和 Memory 交叉判断，并在简报中标注缺失字段。

## 查询结果状态

每个对象查询后都要记录状态，并用于最终数据覆盖摘要：

| 状态 | 含义 | 生成策略 |
| --- | --- | --- |
| `已读取` | 查询成功且返回至少 1 条 | 可作为 CRM 事实使用 |
| `无数据` | 查询成功但返回 0 条 | 可写“未查到相关记录” |
| `权限不足` | 返回无查看列表权限、无字段权限或类似授权错误 | 写“权限不足未读取”，不得推断没有数据 |
| `未触发查询` | 条件查询或扩展查询不满足触发条件 | 写“未触发查询”，不得推断没有数据 |
| `查询失败` | 网络、接口、字段等非权限错误 | 写明失败类型并降级生成 |

如果 `NewOpportunityObj`、`ContactObj` 或 `ActiveRecordObj` 均因权限不足失败，见客前简报仍可对广覆盖对象做一次轻量 describe/查询尝试；若缺少可用关联字段、权限不足或查询失败，立即记录状态并停止，不要反复尝试。

## 对见客就绪度的影响

- `ContractObj` / `SalesOrderObj`：补充 L1 营收/签约金额，补充 L5 财务信号。
- 已确认字段口径的 CSM 预警或客户健康数据：可补充 L4 业务痛点和 L5 战略/健康信号。
- 已确认字段口径的流失原因数据：可补充 L4 业务痛点和 L5 战略/健康信号。
- `CompetitiveLinesObj`：直接补充竞品渗透阶段、差异化、关系对比和准备度。

## 竞品风险补充规则

- `CompetitiveLinesObj.competitor_id` 非空时，竞品阶段至少为 C2。
- `CompetitiveLinesObj.quotation_amount` 非空时，表示已知竞品报价，可计入竞争准备度。
- 已确认字段口径的流失原因中含“竞争”“自研”等信息时，竞品阶段至少为 C2。
- 已确认字段口径的客户健康数据持续下降时，应作为潜在风险写入预警，但不能直接推断有竞品。
