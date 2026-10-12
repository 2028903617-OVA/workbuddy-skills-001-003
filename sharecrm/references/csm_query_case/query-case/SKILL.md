---
name: "query-case"
description: "基于当前会话上下文（支持 IM 和邮件渠道）及访客/客户关联信息查询案例记录，并输出匹配案例列表。"
apiName: "csm_query_case"
---
# 查询案例

## 1. 适用场景

### 1.1 适用场景

- 客户提到之前报修过、反馈过、提交过问题
- 客服需要先查询历史案例再决定是否新建案例
- 客服需要根据当前问题找到已有处理记录

### 1.2 不适用场景

- 当前任务是创建案例，而不是查询案例
- 当前问题只是普通知识咨询
- 当前会话信息不足，无法判断查询条件

## 2. 执行路径


**第一步：获取当前会话上下文并判断渠道**

使用 `sharecrm service session detail` 获取当前会话上下文。提取当前会话记录 ID（`objectData._id`）、`session_channel`、访客、客户和联系人等信息。若 `session_channel` 返回 `email`，按邮件会话处理；否则按 IM 会话处理。邮件查询必须使用 `objectData._id`，不得使用 `session_id`。

```bash
sharecrm service session detail
```

**第二步：获取当前会话内容**

基于第一步识别的渠道获取上下文内容：

1. **IM 会话**：必须使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录；可基于 `webim_visitor_id` 查询前序智能客服会话作为补充背景。
2. **邮件会话**：使用当前会话记录 ID（`objectData._id`）查询邮件对象 `MailObj`。查询条件为 `MailObj.customer_service_session_id` 等于当前会话记录 ID，必须读取邮件正文 `message_body`，并尽量获取邮件主题、发件人、收件人、抄送人、发送时间等信息。

邮件会话查询固定使用以下命令：

```bash
sharecrm data record query-by-fields --object_api_name MailObj --select_fields _id,subject,from_address,to_address,cc_address,send_time,message_body,customer_service_session_id --customer_service_session_id-eq {当前会话记录_id} --sort send_time:asc --limit 50
```

当前 IM 人工会话实时聊天记录或邮件会话 `message_body` 是整理查询条件的主要依据；前序智能客服会话仅作为 IM 渠道的补充背景。不得只获取补充背景后直接整理查询条件。

**第三步：整理查询条件**

基于前两步获取的信息，提取以下关键词：
1. 当前会话内容中的问题描述（核心关键词 2-3 个）
2. IM 前序智能客服会话中的问题背景（如有）
3. 客户名称和联系人名称
4. 客户电话
5. 案例编号

---

**第四步：查询案例对象**

基于已有查询条件，使用 `sharecrm data record query-by-sql` 查询案例对象，对象固定为 `ServiceCaseObj`。字段已确认，不要调用 `sharecrm data describe get` 探索字段。

固定查询字段如下：

- `_id`
- `name`
- `subject`
- `status`
- `description`
- `create_time`
- `last_modified_time`
- `account_id`
- `contact_id`
- `priority`

按以下优先级选择查询条件：

| 可用条件 | 查询方式 |
|---------|----------|
| 同时存在关联客户和关联联系人 | 使用 `account_id`，并追加 `contact_id` 收窄范围 |
| 仅有关联客户 | 使用 `account_id` 查询 |
| 仅有关联联系人 | 使用 `contact_id` 查询 |
| 无客户/联系人但有案例编号 | 使用 `name` 精确查询 |
| 仅有明确问题关键词 | 使用 `subject` 或 `description` 有限模糊查询 |

标准 SQL 模板如下，实际执行时只替换 WHERE 条件：

```bash
sharecrm data record query-by-sql --sql "SELECT _id, name, subject, status, description, create_time, last_modified_time, account_id, contact_id, priority FROM ServiceCaseObj WHERE <查询条件> ORDER BY last_modified_time DESC LIMIT 10"
```

WHERE 条件示例：

- `account_id = '<客户ID>' AND contact_id = '<联系人ID>'`
- `account_id = '<客户ID>'`
- `contact_id = '<联系人ID>'`
- `name = '<案例编号>'`
- `subject LIKE '%<问题关键词>%' OR description LIKE '%<问题关键词>%'`

无关联客户、关联联系人、案例编号或明确问题关键词时，不要随意扩大查询范围。

**第五步：返回结果**

输出与当前问题相关的案例列表，包含：
- 查询到的案例数量
- 每条案例的主题、状态、最近处理时间
- 与当前问题的关联说明

## 3. 禁止行为

- ❌ 在没有当前会话内容的情况下查询案例
- ❌ 向用户索要当前会话 ID；邮件渠道使用的当前会话记录 ID 必须从 `sharecrm service session detail` 返回的 `objectData._id` 中提取
- ❌ 在没有前序智能客服会话内容或邮件正文的情况下编造历史背景
- ❌ IM 渠道使用 `CustomerServiceSessionObj.chat_record` 或其它对象查询结果替代 `sharecrm service session messages` 获取当前会话实时聊天记录
- ❌ 邮件渠道未获取 `MailObj.message_body` 就直接整理查询条件
- ❌ 邮件渠道使用 `session_id` 查询 `MailObj.customer_service_session_id`
- ❌ IM 渠道只获取前序智能客服会话聊天记录，而未获取当前人工会话聊天记录，就直接查询案例
- ❌ 在没有客户或联系人线索时随意扩大案例查询范围
- ❌ 自行改用其他未指定案例查询命令
- ❌ 为确认 `ServiceCaseObj` 字段而调用 `sharecrm data describe get`
- ❌ 将客户字段写成 `customerId`、`customer_id` 或其它未确认字段；客户字段固定使用 `account_id`
- ❌ 将联系人字段写成 `contactId`、`customer_contact_id` 或其它未确认字段；联系人字段固定使用 `contact_id`
- ❌ 编造查询结果
- ❌ 将内部 SQL、字段名或调试过程直接展示给客服
- ❌ 在 SQL 中使用 `SELECT *`

## 4. 输出结果

### 4.1 成功输出

输出可由 Agent 根据查询结果自行组织，不限制固定模板。必须让客服快速看清：

- 查询到的相关案例数量
- 最相关案例的主题、状态和最近处理时间
- 每条结果与当前问题的关联原因
- 若结果较多，仅展示最相关的前 10 条，并避免堆砌无关字段

### 4.2 失败输出

- "当前未查询到与该问题相关的历史案例。"
- "当前案例查询条件不足，暂时无法准确查询相关案例。"

## 失败模式

| 场景 | 处理方式 |
|------|---------|
| SQL 报错 | 提示"案例查询异常，请稍后重试" |
| 查询结果为空 | 输出"未找到与当前问题相关的历史案例" |
| 查询到多条（>10） | 返回最相关的前 10 条，按时间倒序排列 |
| IM 当前人工会话聊天记录获取失败 | 不得仅基于前序智能客服会话查询案例；提示"当前会话聊天记录暂不可用，无法准确查询相关案例" |
| 邮件正文获取失败 | 未查询到关联 MailObj 或 message_body 为空，提示"当前会话关联邮件内容暂不可用，无法准确查询相关案例" |
| 条件不足（无客户/无联系人） | 仅基于当前 IM 实时聊天记录或邮件正文中的明确关键词做有限模糊匹配 |
| 字段不确定 | 不调用 describe；使用固定字段 `account_id`、`contact_id` 和固定查询字段列表 |

## 验证清单

### 测试用例

**测试用例 1：IM 会话查询到匹配案例**

**输入**：客服在当前会话中触发查询案例，客户说"我上次报修过空调"，关联客户"张三"

**预期行为**：
1. 调用 `sharecrm service session detail` 获取当前会话上下文
2. 使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
3. 基于前序会话信息或同一访客最近会话获取前序智能客服会话聊天记录
4. 使用 `account_id` 查询 `ServiceCaseObj`
5. SQL 查询字段为 `_id, name, subject, status, description, create_time, last_modified_time, account_id, contact_id, priority`
6. SQL 使用 `ORDER BY last_modified_time DESC LIMIT 10`
7. 查询到 3 条 ServiceCaseObj 记录
8. 输出案例列表，包含主题、状态、时间、关联说明

**测试用例 2：IM 会话未查询到案例**

**输入**：客服在当前会话中触发查询案例，客户说"我的冰箱坏了"，新客户无关联数据

**预期行为**：
1. 调用 `sharecrm service session detail` 获取当前会话上下文
2. 使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
3. 尝试获取前序智能客服会话聊天记录，或明确前序不可用
4. 无关联客户、联系人或案例编号时，仅基于当前人工会话中的明确问题关键词做有限模糊查询
5. 查询 ServiceCaseObj 返回空结果
6. 输出"未找到与当前问题相关的历史案例"
7. 建议客户新建案例

**测试用例 3：邮件会话查询案例**

**输入**：客服在邮件会话中触发查询案例，客户邮件中提到"之前提交过设备无法启动的问题"

**预期行为**：
1. 调用 `sharecrm service session detail` 获取当前会话上下文，并识别 `session_channel=email`
2. 使用当前会话记录 ID（`objectData._id`）查询 `MailObj`
3. 查询条件为 `--customer_service_session_id-eq {当前会话记录_id}`
4. 读取邮件正文 `message_body`，从邮件内容中整理案例编号、客户/联系人、问题关键词等查询条件
5. 按既有 ServiceCaseObj 查询逻辑查询案例记录
6. 输出案例列表或未查询到提示

### 验证检查清单

- [ ] 已调用 `sharecrm service session detail` 获取当前会话上下文
- [ ] 已根据 `session_channel` 判断当前会话是 IM 还是邮件
- [ ] IM 渠道已使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
- [ ] 邮件渠道已使用当前会话记录 ID（`objectData._id`）查询 `MailObj`，读取 `message_body`
- [ ] 查询 `MailObj` 时使用的是 `objectData._id`，不是 `session_id`
- [ ] 当前 IM 实时聊天记录或邮件 `message_body` 是查询条件整理的主要依据
- [ ] IM 渠道已尝试获取前序智能客服会话聊天记录，或明确前序不可用
- [ ] 查询对象固定为 `ServiceCaseObj`，查询方式固定为 `query-by-sql`
- [ ] SQL 查询字段固定包含 `_id, name, subject, status, description, create_time, last_modified_time, account_id, contact_id, priority`
- [ ] 查询条件使用 `account_id`、`contact_id`、案例编号或明确问题关键词，未随意扩大范围
- [ ] 查询结果按 `last_modified_time DESC` 排列，并限制返回前 10 条
- [ ] 未调用 `describe`，未使用 `SELECT *`
- [ ] 输出案例结果包含主题、状态、最近处理时间和与当前问题的关联说明
