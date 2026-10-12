---
name: "customer-profile-insight"
description: "基于当前会话上下文（支持 IM 和邮件渠道）、访客、联系人、客户和历史服务数据生成访客画像洞察报告。"
apiName: "csm_visitor_profile_insight"
---
# 访客画像洞察

## 1. 适用场景

### 1.1 适用场景

- 客户问题较复杂，需要先了解历史处理情况
- 客户提到之前报修过、联系过客服或提交过服务请求
- 客服希望判断当前访客是否存在高频咨询、重复报修或未解决问题
- 客服需要综合当前会话和历史服务信息判断处理重点

### 1.2 不适用场景

- 当前任务只是简单回复，不需要额外背景信息
- 当前没有可用的会话上下文或访客线索
- 当前任务是直接创建案例、查询案例或生成话术

## 2. 执行路径

**第一步：获取当前会话上下文并判断渠道**

使用 `sharecrm service session detail` 获取当前会话上下文，并提取：

| 信息 | 字段 |
|------|------|
| 会话渠道 | `session_channel` |
| 会话记录 ID | `objectData._id` |
| 访客 ID | `webim_visitor_id` |
| 客户 ID | `account_id` |
| 联系人 ID | `contact_id` |

```bash
sharecrm service session detail
```

若 `session_channel` 为 `email`，按邮件会话处理；否则按 IM 会话处理。邮件查询必须使用当前会话记录 ID（`objectData._id`），不得使用 `session_id`。

若 IM 会话缺失 `webim_visitor_id`，停止执行并提示当前缺少访客信息。若为邮件会话但无法获取任何可用于定位邮件线程的会话信息，停止执行并提示当前缺少邮件会话信息。

**第二步：获取当前会话内容**

1. **IM 会话**：必须使用 `sharecrm service session messages` 获取当前会话实时聊天记录，不得用 `CustomerServiceSessionObj.chat_record` 或其它对象查询结果替代。
2. **邮件会话**：使用当前会话记录 ID（`objectData._id`）查询邮件对象 `MailObj`。查询条件为 `MailObj.customer_service_session_id` 等于当前会话记录 ID，必须读取邮件正文 `message_body`，并尽量获取邮件主题、发件人、收件人、抄送人、发送时间等信息。

```bash
sharecrm data record query-by-fields --object_api_name MailObj --select_fields _id,subject,from_address,to_address,cc_address,send_time,message_body,customer_service_session_id --customer_service_session_id-eq {当前会话记录_id} --sort send_time:asc --limit 50
```

```bash
sharecrm service session messages
```

若 IM 当前人工会话实时聊天记录获取失败，可继续查询历史数据，但洞察报告必须标注“当前会话实时聊天记录不可用”。若邮件正文获取失败，可继续基于其它可用信息生成有限洞察，但必须标注邮件内容不可用。

**第三步：并行查询画像背景和服务业务数据**

完成第一步后，尽量并行发起所有可执行的数据查询。固定对象、字段和查询方式如下，不要临时调用 describe，不要改写为 SQL。

| 数据 | 对象 | 查询方式 |
|------|------|----------|
| 访客信息 | `WebImVisitorObj` | `get-by-id --id {webim_visitor_id}` |
| 历史会话 | `CustomerServiceSessionObj` | IM 会话且 `webim_visitor_id` 可用时，`query-by-fields --webim_visitor_id-eq {webim_visitor_id} --sort create_time:desc --limit 10` |
| 客户信息 | `AccountObj` | 当 `account_id` 存在时，`get-by-id --id {account_id}` |
| 联系人信息 | `ContactObj` | 当 `contact_id` 存在时，`get-by-id --id {contact_id}` |

历史会话固定查询命令：

```bash
sharecrm data record query-by-fields --object_api_name CustomerServiceSessionObj --select_fields _id,session_type,session_id,name,create_time,customer_service_session_id --webim_visitor_id-eq {webim_visitor_id} --sort create_time:desc --limit 10
```

服务业务记录仅在 `account_id` 或 `contact_id` 任一存在时查询。优先使用 `--account_id-eq {account_id}`；若仅有 `contact_id`，使用 `--contact_id-eq {contact_id}`。所有服务业务记录均按 `create_time:desc` 排序，限制 10 条。

| 数据 | 对象 | 查询字段 |
|------|------|----------|
| 服务请求 | `ServiceRequestObj` | `_id,name,service_request_status,subject,create_time,appointment_processing_time,problem_desc` |
| 案例 | `ServiceCaseObj` | `_id,name,status,subject,create_time,handler,last_modified_time` |
| 工单 | `CasesObj` | `_id,name,cases_status,subject,create_time,owner` |

示例命令格式：

```bash
sharecrm data record query-by-fields --object_api_name {对象名} --select_fields {查询字段} --account_id-eq {account_id} --sort create_time:desc --limit 10
```

```bash
sharecrm data record query-by-fields --object_api_name {对象名} --select_fields {查询字段} --contact_id-eq {contact_id} --sort create_time:desc --limit 10
```

若 `account_id` 与 `contact_id` 均缺失，不查询客户、联系人和服务业务记录，仅基于当前会话、可用历史会话和可用邮件内容生成有限洞察。

**第四步：综合生成洞察报告**

围绕以下维度生成洞察，不限制固定标题、固定顺序或固定版式，最终展现由 Agent 根据数据丰富度和当前场景自行组织：

1. 客户当前诉求、情绪状态和已提供线索
2. 访客、客户、联系人等可识别背景
3. 历史交互频次和近期服务业务概况
4. 未关闭服务请求/案例、进行中工单、重复报修或长期未解决问题
5. 当前最值得客服关注的处理重点和风险提示

若 `account_id` 与 `contact_id` 均缺失，仅输出有限洞察，不得编造客户、联系人、案例、服务请求、工单或邮件相关背景信息。

输出应以结论和重点为主，不要按查询结果逐条罗列历史会话、工单、案例或服务请求。历史记录较多时，只展示与当前问题最相关或风险最高的 3 到 5 条，其余内容归纳为数量、状态和趋势。

输出时不要展示数据来源、对象名、字段名、查询过程或内部检查过程；不得在报告末尾追加来源类说明，也不得输出检查点、数据源完成状态或工具调用完成状态等过程性提示。

## 3. 禁止行为

- ❌ 缺少必要会话标识时编造访客画像
- ❌ 向用户索要当前会话 ID
- ❌ 将 ID 字段改写为其它名称；IM 会话固定使用 `webim_visitor_id`、`account_id`、`contact_id`，邮件会话必须使用当前会话记录 ID（`objectData._id`）查询 `MailObj`
- ❌ 邮件会话使用 `session_id` 查询 `MailObj.customer_service_session_id`
- ❌ 将对象改写为其它对象；固定使用 `WebImVisitorObj`、`AccountObj`、`ContactObj`、`CustomerServiceSessionObj`、`ServiceRequestObj`、`ServiceCaseObj`、`CasesObj`
- ❌ 使用 `CustomerServiceSessionObj.chat_record` 替代 `sharecrm service session messages`
- ❌ IM 会话未获取实时聊天记录就直接做画像
- ❌ 邮件会话未获取 `MailObj.message_body` 就直接做画像
- ❌ 在 `account_id` 与 `contact_id` 均缺失时查询服务请求、案例或工单
- ❌ 查询订单对象或输出订单信息
- ❌ 将固定的 `query-by-fields` 查询改写为 SQL，或使用 `SELECT *`
- ❌ 为确认字段而调用 describe
- ❌ 直接堆砌原始记录，不做摘要和重点提炼
- ❌ 将内部对象名、字段名或调试过程直接展示给客服
- ❌ 在最终回复中输出来源类说明或 `WebImVisitorObj + AccountObj + ...` 这类对象链
- ❌ 在最终回复中输出检查点、工具调用信息、过程消息或数据源完成状态等内部状态

## 4. 输出结果

### 4.1 成功输出

输出一份便于客服快速阅读的画像洞察。版式可以使用短段落、表格、加粗重点、风险标记或分组标题，但必须满足以下要求：

- 先突出当前最重要的结论或处理重点
- 说明客户当前诉求和关键背景
- 概括历史服务情况，不按流水账堆砌全部记录
- 明确未关闭、重复、超期、投诉、催促等风险信号
- 给出客服下一步需要优先关注的事项

当信息有限时，直接说明“当前仅能基于有限信息判断”，并基于已获取内容给出有限洞察。

### 4.2 失败输出

- "当前缺少访客信息，暂时无法生成访客画像洞察。"
- "当前可获取的客户背景信息有限，暂时无法形成完整画像洞察。"
- "当前仅能基于部分历史信息提供有限参考，请结合当前会话继续判断。"

## 失败模式

| 失败场景 | 处理方式 |
|---------|---------|
| 会话详情查询失败或 `webim_visitor_id` 缺失 | 停止执行，提示当前缺少访客信息 |
| 当前人工会话聊天记录获取失败 | 可继续查询历史数据，但输出必须标注当前会话实时聊天记录不可用 |
| 访客、客户或联系人查询失败 | 基于已获取数据继续输出，不编造背景信息 |
| `account_id` 与 `contact_id` 均缺失 | 跳过服务请求、案例、工单查询，输出有限洞察 |
| 服务业务记录查询失败或为空 | 基于已获取数据输出，说明相关历史服务记录不可用或未查询到 |
| 权限不足或查询超时 | 基于已获取部分数据输出，并提示数据不完整 |

## 验证清单

### 测试用例

**测试用例 1：完整画像洞察**

**输入**：当前会话返回 `session_channel=im`，并返回 `webim_visitor_id`、`account_id` 和 `contact_id`

**预期行为**：
1. 调用 `sharecrm service session detail` 并提取三个 ID
2. 调用 `sharecrm service session messages` 获取当前实时聊天记录
3. 并行查询访客、历史会话、客户、联系人、服务请求、案例和工单
4. 服务业务记录优先使用 `account_id` 查询
5. 不查询订单对象
6. 输出完整洞察报告

**测试用例 2：邮件会话画像洞察**

**输入**：当前会话返回 `session_channel=email`，并返回 `account_id`

**预期行为**：
1. 调用 `sharecrm service session detail` 并识别 `session_channel=email`
2. 使用当前会话记录 ID（`objectData._id`）查询 `MailObj`
3. 读取 `message_body`
4. 结合 `account_id` 查询客户信息及服务业务记录
5. 若 `contact_id` 存在则同时查询联系人信息
6. 输出完整或有限洞察，并明确基于邮件会话生成

**测试用例 3：有限画像洞察**

**输入**：当前会话仅返回 `webim_visitor_id`

**预期行为**：
1. 调用 `sharecrm service session detail` 并提取 `webim_visitor_id`
2. 调用 `sharecrm service session messages` 获取当前实时聊天记录
3. 并行查询访客信息和历史会话
4. 跳过客户、联系人、服务请求、案例和工单查询
5. 输出有限洞察并标注关联信息缺失

### 验证检查清单

- [ ] 已调用 `sharecrm service session detail` 并根据 `session_channel` 判断当前会话是 IM 还是邮件
- [ ] IM 渠道已使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
- [ ] 邮件渠道已使用当前会话记录 ID（`objectData._id`）查询 `MailObj`，读取 `message_body`
- [ ] 查询 `MailObj` 时使用的是 `objectData._id`，不是 `session_id`
- [ ] 已根据可用 ID 并行查询访客、历史会话、客户、联系人和服务业务记录
- [ ] 对象固定为 `WebImVisitorObj`、`CustomerServiceSessionObj`、`AccountObj`、`ContactObj`、`ServiceRequestObj`、`ServiceCaseObj`、`CasesObj`
- [ ] IM 渠道历史会话使用 `--webim_visitor_id-eq {webim_visitor_id}` 查询
- [ ] 邮件渠道已基于邮件正文和可用客户/联系人信息生成洞察
- [ ] 服务业务记录仅在 `account_id` 或 `contact_id` 存在时查询，优先使用 `--account_id-eq`
- [ ] 未查询订单对象，未使用 SQL、`SELECT *` 或 describe
- [ ] `account_id` 与 `contact_id` 均缺失时，已跳过服务业务记录并输出有限洞察
- [ ] 输出内容基于已获取数据，不直接堆砌原始记录，不编造客户、联系人或服务记录
- [ ] 最终回复未输出来源类说明、对象名、字段名、查询过程、检查点、工具调用信息或内部状态
