# CLI 调用规范

## 使用场景

当客户360档案需要从纷享销客 CRM 拉取客户、联系人、商机、销售记录、竞品明细、合同、订单、回款、客户健康预警或流失原因时，读取本文件并按企业 CLI 规范执行查询。

## 目录

- 查询原则
- Step 1：识别客户主记录
- Step 2：查询关联对象
- 标准模式基础查询
- 条件查询
- full 模式扩展查询
- 可选补充对象
- 查询结果状态
- 查询结果使用规则

## 查询原则

- 先查 `AccountObj`，拿到客户 `_id`，再查询关联对象。
- 只使用已记录命令：`query-by-name`、`query-id-by-name`、`describe get`、`query-by-fields`。不要尝试未记录快捷命令、`sharecrm sales ...` 或 `--data` JSON 查询。
- 用户未指定时间范围时，不主动添加时间过滤条件。
- `query-by-name` 不保证完整模糊召回；未命中只代表该查询方式未返回，不能据此判断 CRM 没有该客户。
- 客户识别必须区分状态：`名称检索未命中`、`候选检索未命中`、`已定位唯一客户`、`需要用户确认`、`查询失败`。
- 名称未命中时，继续执行 ID 候选召回、别名召回和核心词模糊召回；仍未定位时，请用户补充 CRM 客户全称、截图中的客户 ID、负责人或更多上下文。不要写“CRM 中没有客户”，除非用户确认且已完成可用查询路径。
- 查到多个候选客户时，展示候选的客户名、`_id`、行业/地址/最近跟进等可确认字段，让用户选择目标客户。
- 用户提供 CRM 截图、链接或记录 ID 时，优先用 `_id` 精确查询，不要再依赖名称模糊检索。
- 单短词命中不能自动视为同一客户。例：用户输入“通州农业局”时，只命中包含“通州”但不包含“农业局”的客户，应标为低置信候选，不得自动选中。
- 查询要先定位、再扩展：未确认 `<accountId>` 前，不查询商机、联系人、销售记录或扩展对象。
- 为保证效率，确认客户后只 describe 本轮计划查询的对象；同一对象本轮只 describe 一次，互不依赖的基础对象可并行查询。
- 标准版客户360采用广覆盖策略：确认唯一客户后，尽量轻量读取客户360相关对象并记录状态。广覆盖不是为了凑字段，而是为了避免遗漏需求、会议、承诺、竞品、历史合作和回款风险；每个对象只做必要查询，失败后记录状态并停止重复 loop。
- 查询结果不足时，写入“信息缺口”，不要编造 CRM 数据。
- 相对时间按 `currentDateTime` 解析；“我”“我负责的”按 `currentEmployeeName` 解析。
- 区分“查询成功但 0 条记录”和“权限不足/查询失败”。权限不足不得写成无数据。
- 同一对象本轮已经查询失败且原因是权限不足、describe 失败或不可恢复错误时，不要重复查询该对象。
- 同一对象本轮已经 describe 过，可以复用已确认字段，不要反复 describe。

## Step 1：识别客户主记录

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



## Step 2：查询关联对象

首次查询每个关联对象前，先 describe 并只使用已确认字段。已确认唯一 `<accountId>` 后，标准版客户360应尽量覆盖基础对象、过程对象、竞争对象和历史合作对象；互不依赖的对象可并行查询，同一对象本轮只 describe 一次。

```bash
sharecrm data describe get --object_api_name <objectApiName> --simple_describe true
```

```bash
sharecrm data record query-by-fields \
  --object_api_name <objectApiName> \
  --select_fields <confirmed_fields> \
  --account_id-eq <accountId> \
  --sort last_modified_time:desc \
  --limit 50
```

如果用户明确指定时间范围，再追加：

```bash
--last_modified_time-gte <startTime> --last_modified_time-lte <endTime>
```

时间格式：`yyyy-MM-dd HH:mm:ss`。

## 标准模式基础查询

| 对象 | 查询字段 | 用途 |
| --- | --- | --- |
| `NewOpportunityObj` | `_id,name,sales_stage,amount,probability,close_date,sales_status` | 当前商机、历史商机、阶段、金额、赢率、预计结单 |
| `ContactObj` | `_id,name,job_title,primary_contact` | 联系人、关键联系人、决策链候选 |
| `ActiveRecordObj` | `interactive_scenario,interactive_types,active_record_content,create_time` | 跟进记录、客户原话、关系变化、痛点证据 |

## 标准版广覆盖扩展查询

确认 `<accountId>` 后，在字段和权限允许时尽量轻量查询以下对象；若对象不存在、字段不可用、权限不足或查询失败，记录数据覆盖状态，不继续反复查询。

| 对象 | 查询字段 | 用途 |
| --- | --- | --- |
| `RequirementObj` | `_id,name,content,clearance_status,response_status,four_quadrant,kano,account_id,opportunity_id,requirement_solve,category` | 需求、痛点、必选条件、响应状态 |
| `ActivityQuestionObj` | `_id,name,question_content,question_type,question_proposer,proposer_attitude,answer_summary,tags,account_id,new_opportunity_id` | 客户问题、异议、态度、回答摘要 |
| `ScheduleObj` | `_id,participants,content,begin_time,end_time,related_object_data,owner` | 日程、计划会议、参会信息 |
| `AIMeetingObj` | `_id,name,initiator,remark,start_time,end_time,inner_participants,meeting_content,ai_status` | 会议纪要、参会人、会议总结 |
| `AIMeetingChunkObj` | `_id,name,summary,meeting_id,original_content,object_api_name,original_id,status` | 会议分块、原文摘要、关联业务对象 |
| `ActivityTodoObj` | `_id,name,todo_type,task_status,execution_time,executor,active_record_id,related_object_data,ref_source,ai_summary` | 待办、承诺、执行人、状态 |
| `MethodologyTaskObj` | `_id,name,short_name,note,task_object_api_name,system_type,owner` | 销售方法论任务、过程动作 |
| `CheckinsObj` | `_id,owner,customer_id,communicate_record,new_stat_date,checkins_scene` | 现场拜访、外勤沟通、触达证明 |
| `CompetitiveLinesObj` | `_id,name,competitor_id,advantage,weaknesses,quotation_amount,is_win` | 竞品在场状态、报价、优劣势、输赢结果 |
| `ContractObj` | `_id,name,contract_amount,started_time,expired_time,status` | 合同金额、合同周期、续约窗口、合同状态 |
| `SalesOrderObj` | `_id,name,order_amount,order_status,payment_amount,receivable_amount` | 订单金额、订单状态、回款金额、应收金额 |
| `PaymentObj` | `_id,name,payment_time,amount,account_id,owner` | 独立回款记录、到账日期、回款金额 |

## full 模式扩展查询

`--full`、历史客户、已成交客户或用户要求历史/财务/客户健康时，允许在已轻量查询对象基础上进一步展开明细：

| 对象 | 查询字段 | 用途 |
| --- | --- | --- |
| `ContractObj` | `_id,name,contract_amount,started_time,expired_time,status` | 合同金额、合同周期、续约窗口、合同状态 |
| `SalesOrderObj` | `_id,name,order_amount,order_status,payment_amount,receivable_amount` | 订单金额、订单状态、回款金额、应收金额 |

客户健康、CSM 预警、流失原因等如依赖企业自定义对象或字段，不在本通用规范中硬编码；仅在用户提供字段口径、租户 schema 可确认，或企业标准 reference 已明确时再查询。无法确认时，应通过合同、订单、回款、互动记录和 Memory 交叉判断，并在简报中标注信息缺口。

## 可选补充对象

以下对象在标准版客户360中已纳入广覆盖扩展查询；若执行的是更轻量的客户问答或用户明确限制查询范围，才按“用户要求或主数据不足”作为触发条件。

| 对象 | 用途 |
| --- | --- |
| `ScheduleObj` | 日程、会议安排、计划拜访 |
| `CheckinsObj` | 外勤拜访、签到、现场拜访轨迹 |
| `PaymentObj` | 若环境中有独立回款对象，可用于补充订单回款 |
| `PersonnelObj` | AE、CSM、售前、实施等内部负责人信息 |

## 查询结果状态

输出客户360前，必须维护每类数据状态：

| 状态 | 含义 | 输出处理 |
| --- | --- | --- |
| 已读取 | 查询成功且有可用记录 | 可用于确认事实 |
| 无数据 | 查询成功但返回 0 条记录 | 只能说明 CRM 未记录，不代表事实不存在 |
| 权限不足 | CLI 返回无对象、列表、字段或数据权限 | 标注“权限不足未读取”，不要写成无数据 |
| 未触发查询 | 条件查询对象未满足触发条件 | 标注“未触发查询”，不要写成无竞品/无合同 |
| 查询失败 | 非权限类错误、字段不支持或命令失败 | 标注失败原因并降低相关结论置信度 |

如果商机、联系人和销售记录均为权限不足，标准版仍可对 `CompetitiveLinesObj` 做一次轻量 describe/查询尝试；若缺少可用关联字段、权限不足或查询失败，立即记录状态并停止，不要反复尝试。

## 查询结果使用规则

- `ActiveRecordObj.active_record_content` 是痛点、承诺、关系温度和竞品线索的高价值来源。
- `ContactObj.primary_contact` 只能表示 CRM 主联系人，不等于 EB；EB 必须由职位、审批链或互动证据确认。
- `NewOpportunityObj.probability` 是 AE 主观赢率，只作为商机信号，不作为结果预测。
- `CompetitiveLinesObj.competitor_id` 非空时，竞品阶段至少为 C2“在场”。
- `CompetitiveLinesObj.quotation_amount` 非空时，说明已知竞品报价，可写入竞品全貌。
- 客户健康或流失风险不能依赖未经确认的自定义字段；需结合互动记录、合同状态、订单回款、服务反馈和 Memory 综合判断。
