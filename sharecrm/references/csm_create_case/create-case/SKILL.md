---
name: "create-case"
description: "基于当前会话上下文（支持 IM 和邮件渠道）提取案例关键信息，并创建案例对象。"
apiName: "csm_create_case"
---
# 创建案例

## 1. 适用场景

### 1.1 适用场景

当客服需要将当前客户问题登记为案例时，使用本技能。

典型场景包括：

- 客户问题需要正式记录和跟进
- 当前问题已进入售后处理阶段
- 客服需要基于当前会话快速创建案例

### 1.2 不适用场景

以下情况不要使用本技能：

- 当前问题只是普通咨询，不需要登记案例
- 当前会话信息不足，无法提取基础案例字段
- 当前任务只是查询案例，而不是创建案例

## 2. 执行路径

**第一步：获取当前会话上下文并判断渠道** — 使用 `sharecrm service session detail` 获取当前会话上下文，提取当前会话记录 ID（`objectData._id`）、`session_channel`、`owner`、`webim_visitor_id` 等信息。若 `session_channel` 返回 `email`，按邮件会话处理；否则按 IM 会话处理。邮件查询必须使用 `objectData._id`，不得使用 `session_id`。

```bash
sharecrm service session detail
```

**第二步：获取当前会话内容** — 基于第一步识别的渠道获取上下文内容。

1. **IM 会话**：必须使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录；同时可从 `webim_visitor_id` 查询前序智能客服会话作为补充背景。
2. **邮件会话**：使用当前会话记录 ID（`objectData._id`）查询邮件对象 `MailObj`。查询条件为 `MailObj.customer_service_session_id` 等于当前会话记录 ID，必须读取邮件正文 `message_body`，并尽量获取邮件主题、发件人、收件人、抄送人、发送时间等信息。

邮件会话查询固定使用以下命令：

```bash
sharecrm data record query-by-fields --object_api_name MailObj --select_fields _id,subject,from_address,to_address,cc_address,send_time,message_body,customer_service_session_id --customer_service_session_id-eq {当前会话记录_id} --sort send_time:asc --limit 50
```

IM 会话查询同一访客最近会话列表时，固定使用以下命令：

```bash
sharecrm data record query-by-fields --object_api_name CustomerServiceSessionObj --select_fields _id,session_type,session_id,name,create_time --webim_visitor_id-eq {webim_visitor_id} --sort create_time:desc --limit 5
```

从返回结果中选择最近一条“会话类型”为“智能客服”的记录，取其 `_id`，再使用 `get-by-id` 获取完整记录：

```bash
sharecrm data record get-by-id --object_api_name CustomerServiceSessionObj --id {智能客服会话_id}
```

当前 IM 人工会话实时聊天记录或邮件会话 `message_body` 是提取案例字段的主要依据；前序智能客服会话仅作为 IM 渠道的补充背景。若当前主上下文获取失败，不得仅基于补充背景创建案例。

**第三步：提取案例字段信息** — 基于获取到的当前会话内容提取案例字段信息。

| 字段名 | 必填 | 提取来源 | 说明 |
|-------|------|---------|------|
| subject | 是 | 从当前会话内容中提取问题摘要 | 案例主题 |
| description | 否 | 从当前会话内容中提取详细描述 | 案例描述 |
| priority | 是 | 从当前会话内容中判断 | 优先级，仅允许 `URGENT`、`HIGH`、`MEDIUM`、`LOW` |
| contact_tel | 否 | 从当前会话内容中提取 | 联系电话，仅在当前会话内容中明确出现时写入 |
| owner | 否 | 默认取当前会话上下文中的 `owner` | 负责人 |
| status | 否 | 默认为"新建" | 案例状态 |

**第四步：判断是否满足创建条件** — 判断提取的字段是否满足创建案例的条件。

- 必填字段 `subject`、`priority` 必须完整
- `priority` 仅允许 `URGENT`、`HIGH`、`MEDIUM`、`LOW`
- `owner` 必须可从当前会话上下文中获取
- `contact_tel` 仅在当前会话内容中明确出现时写入，不得编造
- 若不满足创建条件，引导用户提供相关信息；若满足创建条件，执行第五步

**第五步：创建案例对象** — 使用以下操作创建案例对象。

```bash
sharecrm data record create --data '{"object_api_name":"ServiceCaseObj","object_data":{"subject":"主题","description":"描述","priority":"优先级","contact_tel":"电话","owner":["当前用户ID"]}}'
```

## 3. 禁止行为

你不得：

- 编造 IM 前序智能客服会话内容或邮件正文内容
- IM 渠道只获取前序智能客服会话聊天记录，而未获取当前人工会话实时聊天记录，就直接创建案例
- 邮件渠道未获取 `MailObj.message_body` 就直接创建案例
- 邮件渠道使用 `session_id` 查询 `MailObj.customer_service_session_id`
- 在没有调用 `sharecrm service session detail` 的情况下自行猜测 `owner`
- 编造 `subject`、`priority`、`contact_tel`
- 使用未定义的优先级值（仅允许 URGENT/HIGH/MEDIUM/LOW）
- 将内部字段名、对象名或调试过程展示给客服

## 4. 输出结果

### 4.1 成功输出

成功时，应明确说明案例已创建，并给出简洁结果说明，不限制固定模板。

输出需让客服清楚以下信息：

- 案例已成功创建
- 当前案例主题
- 当前案例优先级

### 4.2 失败输出

如果当前信息不足以创建案例，明确说明当前无法完成创建，并指出缺失的关键字段。

输出可由 Agent 根据缺失情况自行组织，但必须说明缺失的关键字段或失败原因。

- "当前缺少创建案例所需的关键信息（缺失字段：{字段列表}），暂时无法完成案例创建。"
- "当前未能成功提取完整的案例字段，请补充必要信息后再继续创建。"

## 失败模式

| 失败场景 | 触发条件 | 处理方式 |
|---------|---------|---------|
| 必填字段不完整 | subject 或 priority 缺失 | 明确提示缺失字段，不创建案例。基于会话内容补齐或提示用户补充 |
| 会话详情获取失败 | sharecrm service session detail 返回错误 | 提示"会话详情获取失败，无法确定案例负责人，请在会话工作台内重试" |
| IM 当前人工会话聊天记录获取失败 | sharecrm service session messages 返回错误或为空 | 不得仅基于前序智能客服会话创建案例；提示"当前会话聊天记录暂不可用，无法准确创建案例" |
| 邮件正文获取失败 | 未查询到关联 MailObj 或 message_body 为空 | 提示"当前会话关联邮件内容暂不可用，无法准确创建案例" |
| 前序智能客服会话查询失败或不存在 | 最近 5 条同访客会话中无智能客服会话，或 get-by-id 获取失败 | 前序信息作为补充背景，可仅基于当前人工会话实时聊天记录继续提取字段 |
| 权限不足 | 当前用户无 ServiceCaseObj 创建权限 | 提示"当前账号无案例创建权限，请联系管理员开通" |
| 字段校验不通过 | priority 使用未定义值 | 修正为合法值后重试，若仍失败则提示用户重新选择优先级 |

## 验证清单

### 测试用例

**测试用例 1：IM 会话完整创建流程**
- 输入：客服在 IM 会话中完整处理了客户关于"空调不制冷"的问题，说"帮我创建案例"
- 预期行为：
  1. 调用 `sharecrm service session detail` 获取当前会话上下文
  2. 使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
  3. 从会话上下文中提取 `webim_visitor_id`
  4. 使用 `query-by-fields` shortcut 形式查询同一访客最近 5 条 `CustomerServiceSessionObj` 会话
  5. 选择最近一条会话类型为“智能客服”的记录，并基于 `_id` 调用 `get-by-id` 获取完整记录
  6. 从完整记录中读取前序智能客服会话 `chat_record`
  7. 提取字段：subject="空调不制冷问题记录"，priority="MEDIUM"，owner=会话详情中的 owner
  8. 验证字段完整性和合法性
  9. 调用 `sharecrm data record create` 创建 ServiceCaseObj
  10. 输出"案例已成功创建，主题：空调不制冷问题记录，优先级：MEDIUM"

**测试用例 2：必填字段缺失**
- 输入：会话内容很短，无法提取有效的 subject 和 priority
- 预期行为：
  1. 调用 `sharecrm service session detail` 获取当前会话上下文
  2. 使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
  3. 使用 `webim_visitor_id` 查询同一访客最近 5 条会话，并尝试获取前序智能客服会话完整记录
  4. 提取字段：subject=无法确定，priority=无法确定
  5. 判断必填字段不完整
  6. 提示"当前缺少创建案例所需的关键信息（缺少主题、优先级），暂时无法完成案例创建"
  7. 提示客服补充必要信息后再试

**测试用例 3：无前序智能客服会话但当前会话信息完整**
- 输入：客服在当前人工会话中已完整处理客户问题，但同一访客最近 5 条会话中没有“智能客服”会话
- 预期行为：
  1. 调用 `sharecrm service session detail` 获取当前会话上下文
  2. 使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
  3. 使用 `webim_visitor_id` 查询同一访客最近 5 条会话
  4. 未找到会话类型为“智能客服”的记录，明确前序智能客服会话不可用
  5. 仅基于当前人工会话实时聊天记录提取案例字段
  6. 若 `subject`、`priority`、`owner` 满足创建条件，调用 `sharecrm data record create` 创建 ServiceCaseObj
  7. 不编造前序智能客服会话内容

**测试用例 4：邮件会话完整创建流程**
- 输入：客服在邮件会话中收到客户关于"设备无法启动"的邮件，说"帮我创建案例"
- 预期行为：
  1. 调用 `sharecrm service session detail` 获取当前会话上下文，并识别 `session_channel=email`
  2. 使用当前会话记录 ID（`objectData._id`）查询 `MailObj`
  3. 查询条件为 `--customer_service_session_id-eq {当前会话记录_id}`
  4. 读取邮件正文 `message_body`，并基于邮件内容提取 subject、description、priority、contact_tel 等字段
  5. 若 `subject`、`priority`、`owner` 满足创建条件，调用 `sharecrm data record create` 创建 ServiceCaseObj

### 验证检查清单

- [ ] 已调用 `sharecrm service session detail` 获取当前会话上下文
- [ ] 已根据 `session_channel` 判断当前会话是 IM 还是邮件
- [ ] IM 渠道已使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
- [ ] 邮件渠道已使用当前会话记录 ID（`objectData._id`）查询 `MailObj`，读取 `message_body`
- [ ] 查询 `MailObj` 时使用的是 `objectData._id`，不是 `session_id`
- [ ] 当前 IM 实时聊天记录或邮件 `message_body` 是案例字段提取的主要依据
- [ ] 若 `webim_visitor_id` 可用，已按最近 5 条会话查询前序智能客服会话，并通过 `get-by-id` 读取完整 `chat_record`
- [ ] 若前序智能客服会话不可用，IM 渠道已仅基于当前人工会话实时聊天记录继续处理
- [ ] 未在缺少当前主上下文时仅基于补充背景创建案例
- [ ] 已提取并校验 `subject`、`description`、`priority`、`contact_tel`、`owner`
- [ ] `subject` 和 `priority` 缺失时未执行创建
- [ ] `priority` 仅使用 `URGENT`、`HIGH`、`MEDIUM`、`LOW`
- [ ] `owner` 来自当前会话上下文，`contact_tel` 仅在当前会话内容明确出现时写入
- [ ] 创建对象固定为 `ServiceCaseObj`，并使用 `sharecrm data record create --data`
- [ ] 未在调用 create 前额外展示字段或要求二次确认
