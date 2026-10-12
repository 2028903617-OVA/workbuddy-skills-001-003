---
name: "next-best-action"
description: "基于当前会话上下文（支持 IM 和邮件渠道）生成下一步行动建议，并输出建议动作、原因和优先级。"
apiName: "csm_next_best_action"
---
# 行动建议

## 1. 适用场景

### 1.1 适用场景

当客服需要判断当前会话下一步最适合做什么时，使用本技能。

典型场景包括：

- 客服已了解客户问题，但不确定下一步该执行什么动作
- 客户问题需要进一步推进处理
- 客服需要在多个处理动作中选择更合适的一项

### 1.2 不适用场景

以下情况不要使用本技能：

- 当前缺少可用的会话上下文
- 当前客服已经明确知道下一步动作
- 当前任务只是生成回复话术，而不是判断下一步动作

## 2. 执行路径


**第一步：获取当前会话上下文并判断渠道**

使用 `sharecrm service session detail` 获取当前会话上下文。提取当前会话记录 ID（`objectData._id`）、`session_channel`、线索、访客、客户和联系人等信息。若 `session_channel` 返回 `email`，按邮件会话处理；否则按 IM 会话处理。邮件查询必须使用 `objectData._id`，不得使用 `session_id`。

```bash
sharecrm service session detail
```

**第二步：获取当前会话内容**

基于第一步识别的渠道获取上下文内容。当前 IM 实时聊天记录或邮件正文是判断下一步行动的主要依据；前序智能客服会话仅作为 IM 渠道的补充背景。

1. **IM 会话**：必须使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录；可从 `webim_visitor_id` 查询前序智能客服会话作为补充背景。
2. **邮件会话**：使用当前会话记录 ID（`objectData._id`）查询邮件对象 `MailObj`。查询条件为 `MailObj.customer_service_session_id` 等于当前会话记录 ID，必须读取邮件正文 `message_body`，并尽量获取邮件主题、发件人、收件人、抄送人、发送时间等信息。

邮件会话查询固定使用以下命令：

```bash
sharecrm data record query-by-fields --object_api_name MailObj --select_fields _id,subject,from_address,to_address,cc_address,send_time,message_body,customer_service_session_id --customer_service_session_id-eq {当前会话记录_id} --sort send_time:asc --limit 50
```

固定使用以下命令查询同一访客最近会话列表，不使用 `--data`，不调用 `sharecrm data describe get`：

```bash
sharecrm data record query-by-fields --object_api_name CustomerServiceSessionObj --select_fields _id,session_type,session_id,name,create_time,customer_service_session_id --webim_visitor_id-eq {webim_visitor_id} --sort create_time:desc --limit 5
```

从返回结果中选择最近一条“会话类型”为“智能客服”的记录，取其 `_id`，再使用 `get-by-id` 获取完整记录：

```bash
sharecrm data record get-by-id --object_api_name CustomerServiceSessionObj --id {智能客服会话_id}
```

若前序智能客服会话不可用，可仅基于当前人工会话生成行动建议；若当前主上下文不可用，不得仅基于补充背景生成行动建议。

**第三步：判断客户问题所处阶段**

基于第一步和第二步获取的会话内容，分析：

- 客户当前问题处于哪个阶段（咨询/故障/投诉/售后等）
- 当前已获取的信息是否足够推进
- 存在哪些可行的下一步动作

**第四步：输出行动建议**

基于判断结果输出行动建议，不限制固定模板。必须让客服快速看清最推荐的下一步动作、推荐原因，以及是否需要备选动作。

输出时优先给出一个最建议执行的动作；只有在当前信息不足、存在多条合理路径或主路径失败时，才补充备选动作。不要把当前渠道可用的所有技能平铺成清单。


**行动建议范围**

行动建议只允许在当前会话渠道已具备的能力范围内推荐。

IM 会话可推荐的动作包括：

1. 使用知识库问答继续回复客户
2. 生成一版更合适的话术推荐
3. 创建案例
4. 查询案例
5. 查看用户画像洞察
6. 沉淀为知识候选

邮件会话可推荐的动作包括：

1. 使用知识库问答查询处理依据
2. 生成邮件撰写建议
3. 查看邮件线程摘要
4. 创建案例
5. 查询案例
6. 查看访客画像洞察
7. 沉淀为知识候选

## 3. 禁止行为

- 禁止在没有当前会话上下文的情况下生成行动建议
- 禁止向用户索要当前会话 ID 或访客 ID；当前会话信息必须从 `sharecrm service session detail` 返回结果中获取
- 禁止自行猜测或编造前序智能客服会话内容
- 禁止扩展更多无关历史会话；前序智能客服会话只查询同一访客最近 5 条会话并选择最近的“智能客服”会话
- 禁止 IM 渠道只获取前序智能客服会话聊天记录，而未获取当前人工会话实时聊天记录，就直接生成行动建议
- 禁止邮件渠道未获取 `MailObj.message_body` 就直接生成行动建议
- 禁止邮件渠道使用 `session_id` 查询 `MailObj.customer_service_session_id`
- 禁止输出与当前会话无关的泛化建议
- 禁止推荐超出 IM 会话助手当前能力范围之外的动作
- 禁止将技术字段、调试过程或内部命令展示给客服
- 禁止使用"应尽量"等模糊表述，须使用具体明确的建议

## 4. 输出结果

### 4.1 成功输出

输出可由 Agent 根据当前场景自行组织，不限制固定标题或字段名。必须包含：

- 当前最推荐的下一步动作
- 推荐该动作的原因
- 如有必要，说明备选动作和触发条件

表达应简洁直接，避免输出流程分析、工具调用过程或泛化建议。

### 4.2 失败输出

```
当前缺少必要的会话上下文，暂时无法生成准确的行动建议。
```

```
当前未能成功获取前序智能客服会话内容，已基于当前会话生成建议。
```

## 失败模式

| 场景 | 表现 | 处理方式 |
|------|------|----------|
| 当前会话信息获取失败 | session detail 返回空，或邮件渠道未返回 `objectData._id` | 终止执行，提示"无法获取当前会话信息，请在会话工作台内重试"，不得向用户索要会话 ID |
| IM 当前会话消息内容为空 | `sharecrm service session messages` 无聊天记录 | 提示"当前会话暂无消息内容，无法分析行动建议" |
| IM 当前人工会话聊天记录获取失败 | `sharecrm service session messages` 返回错误 | 不得仅基于前序智能客服会话生成行动建议；提示"当前会话聊天记录暂不可用，无法分析行动建议" |
| 邮件正文获取失败 | 未查询到关联 MailObj 或 message_body 为空 | 提示"当前会话关联邮件内容暂不可用，无法分析行动建议" |
| 当前会话上下文缺少 `webim_visitor_id` | 无法查询同一访客最近会话 | 仅基于当前会话内容生成建议，标注"前序智能客服会话不可用" |
| 同一访客最近 5 条会话中没有“智能客服”会话 | 前序智能客服会话不存在 | 仅基于当前会话内容生成建议，标注"无前序智能客服会话数据" |
| `query-by-fields` 查询失败或超时 | 接口报错或无返回 | 跳过前序智能客服会话查询，仅使用当前会话内容 |
| `get-by-id` 获取完整记录失败或 `chat_record` 为空 | 无法读取完整前序智能客服聊天记录 | 仅基于当前会话内容生成建议 |
| 无法识别客户问题所处阶段 | 会话内容模糊或无关 | 建议客服补充关键信息后再判断下一步动作 |

## 验证清单

### 测试用例

**测试用例 1：IM 有前序智能客服会话的正常场景**

**用户输入**：客户说之前报修过空调但还没修好

**预期行为**：
1. 调用 `sharecrm service session detail` 获取当前会话上下文
2. 使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
3. 从会话上下文中提取 `webim_visitor_id`
4. 使用 `query-by-fields` shortcut 形式查询同一访客最近 5 条 `CustomerServiceSessionObj` 会话
5. 选择最近一条会话类型为“智能客服”的记录，并基于 `_id` 调用 `get-by-id` 获取完整记录
6. 从完整记录中读取前序智能客服会话 `chat_record`
7. 判断客户处于"维修跟进"阶段
8. 输出应明确建议先查询历史案例，并说明原因是客户提到已报修过，需要先确认已有处理记录

**测试用例 2：IM 无前序智能客服会话的场景**

**用户输入**：新客户咨询产品功能

**预期行为**：
1. 调用 `sharecrm service session detail` 获取当前会话上下文
2. 使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
3. 使用 `webim_visitor_id` 查询同一访客最近 5 条会话
4. 未找到会话类型为“智能客服”的记录，明确前序智能客服会话不可用
5. 明确前序智能客服会话不可用后，仅基于当前会话内容生成
6. 输出应明确建议使用知识库问答查询处理依据，并说明原因是客户在咨询产品功能

**测试用例 3：邮件会话行动建议**

**用户输入**：客户邮件催促售后处理进展

**预期行为**：
1. 调用 `sharecrm service session detail` 获取当前会话上下文，并识别 `session_channel=email`
2. 使用当前会话记录 ID（`objectData._id`）查询 `MailObj`
3. 查询条件为 `--customer_service_session_id-eq {当前会话记录_id}`
4. 读取邮件正文 `message_body`
5. 判断客户处于"售后进度跟进"阶段
6. 输出邮件渠道可执行的行动建议，如查询案例、生成邮件撰写建议或查看访客画像洞察


### 验证检查清单

- [ ] 已调用 `sharecrm service session detail` 获取当前会话上下文
- [ ] 已根据 `session_channel` 判断当前会话是 IM 还是邮件
- [ ] IM 渠道已使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
- [ ] 邮件渠道已使用当前会话记录 ID（`objectData._id`）查询 `MailObj`，读取 `message_body`
- [ ] 查询 `MailObj` 时使用的是 `objectData._id`，不是 `session_id`
- [ ] 当前 IM 实时聊天记录或邮件 `message_body` 是行动建议的主要依据
- [ ] IM 渠道若 `webim_visitor_id` 可用，已按最近 5 条会话查询前序智能客服会话，并通过 `get-by-id` 读取完整 `chat_record`
- [ ] 若前序智能客服会话不可用，IM 渠道已仅基于当前人工会话继续处理
- [ ] 未在缺少当前主上下文时仅基于补充背景生成行动建议
- [ ] 已分析客户问题所处阶段、信息是否足够推进和可行下一步动作
- [ ] 行动建议仅在当前渠道已具备的能力范围内推荐
- [ ] 输出明确给出最推荐的下一步动作和推荐原因
- [ ] 未把所有可用技能平铺成列表
- [ ] 未输出泛化建议、技术字段、调试过程或内部命令
