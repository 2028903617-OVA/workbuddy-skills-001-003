---
name: "agent-kb-qa"
description: "基于当前会话内容（支持 IM 和邮件渠道）及知识库检索，为客服生成问题解答、处理依据和回复参考。"
apiName: "csm_agent_knowledge_base_qa"
---
# 客服知识库问答

## 1. 适用场景

### 1.1 适用场景

- 客服需要根据客户问题查找知识依据
- 客服需要查询产品功能、使用方法、故障排查、服务流程或保修政策
- 客服希望基于知识库内容组织更准确的回复

### 1.2 不适用场景

- 当前任务是直接创建案例、查询案例或生成最终发送话术
- 当前输入内容无法形成明确的知识查询问题

## 2. 执行路径

**第一步：获取当前会话上下文并判断渠道**

使用 `sharecrm service session detail` 获取当前会话上下文，提取当前会话记录 ID（`objectData._id`）和 `session_channel`。若 `session_channel` 返回 `email`，按邮件会话处理；否则按 IM 会话处理。邮件查询必须使用 `objectData._id`，不得使用 `session_id`。

```bash
sharecrm service session detail
```

**第二步：获取当前会话内容**

基于第一步识别的渠道获取上下文内容：

1. **IM 会话**：使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录。
2. **邮件会话**：使用当前会话记录 ID（`objectData._id`）查询邮件对象 `MailObj`。查询条件为 `MailObj.customer_service_session_id` 等于当前会话记录 ID，必须读取邮件正文 `message_body`，并尽量获取邮件主题、发件人、收件人、抄送人、发送时间等信息。

```bash
sharecrm data record query-by-fields --object_api_name MailObj --select_fields _id,subject,from_address,to_address,cc_address,send_time,message_body,customer_service_session_id --customer_service_session_id-eq {当前会话记录_id} --sort send_time:asc --limit 50
```

若当前会话内容获取失败，不得自行扩展客户问题背景，只能基于客服明确输入检索，或提示客服补充问题描述。

**第三步：理解客服输入和客户问题**

结合客服输入与当前 IM 实时聊天记录或邮件正文，提取适合知识检索的查询问题。客服输入很短时，优先用当前会话内容补足客户问题背景；当前会话内容不可用时，不得凭空猜测。

**第四步：知识检索**

固定使用 `--content` 调用知识检索，不得改用 `--query`，也不得调用 help 重新判断参数格式。

```bash
sharecrm knowledge expertise rag-search-knowledge --content "{客服当前需要查询的问题}"
```

**第五步：输出结果**

- 检索结果足够支撑：输出知识结论、处理依据、回复参考和参考资料
- 检索结果部分匹配：输出可用部分，并标注需要进一步核实
- 未命中、冲突或不足：明确提示当前未检索到足够相关知识，不得编造答案

## 3. 禁止行为

- 不得跳过知识检索直接给出知识结论
- 不得在当前会话内容不可用时自行猜测客户问题背景
- IM 渠道未获取 `sharecrm service session messages` 返回的当前实时聊天记录时，不得声称已结合当前会话
- 邮件渠道未获取 `MailObj.message_body` 时，不得声称已结合邮件内容
- 邮件渠道不得使用 `session_id` 查询 `MailObj.customer_service_session_id`
- 不得偏离客服输入内容，生成无关知识问题
- 不得在知识不足时编造答案、参考资料或来源引用
- 不得使用 `--query`、调用 help 或临时探索参数格式
- 不得输出内部命令、调试过程、技术字段或 CHECKPOINT
- 不得以终端客户口吻输出唯一答案；本技能输出应面向客服辅助处理

## 4. 输出结果

### 4.1 成功输出

成功时输出适合客服使用的知识辅助结果，不限制固定模板。必须覆盖以下内容：

1. **问题理解**：对客服输入和当前客户问题的理解摘要
2. **知识结论**：从知识库提取的核心结论
3. **处理依据**：支撑结论的具体依据
4. **回复参考**：适合客服场景的回复方向，非最终话术
5. **参考资料**：本次检索命中的知识条目

参考资料必须来自本次检索命中的知识条目，且使用可点击链接格式。参考资料区的展示方式可由 Agent 根据结果数量自行组织。

若某条处理依据直接引用知识内容，可在该依据后标注来源编号，格式如下：

```html
<sup><a href="url" title="文档标题" target="_blank"><b>[N]</b></a></sup>
```

### 4.2 失败输出

- "当前未检索到足够相关的知识内容，暂时无法提供可靠的处理依据。"
- "建议结合当前会话进一步确认客户问题，或转入后续业务处理。"

## 失败模式

| 失败场景 | 处理方式 |
|---------|---------|
| IM 当前人工会话聊天记录获取失败 | 仅基于客服明确输入检索，或提示补充客户问题描述 |
| 邮件正文获取失败 | 仅基于客服明确输入检索，或提示补充客户问题描述 |
| 输入过于模糊 | 提示客服提供具体产品名称、故障现象或流程问题 |
| 检索无结果或执行失败 | 明确提示未检索到足够相关知识或服务暂不可用 |
| 检索结果冲突或部分匹配 | 输出可用部分，并提示需要进一步核实 |
| 知识不足 | 不编造结论，建议客服结合当前会话继续判断或转入后续流程 |

## 验证清单

### 测试用例

**测试用例 1：命中知识**

输入：客服输入“客户问空调不制冷是什么原因”

预期行为：
1. 调用 `sharecrm service session detail` 并识别当前会话渠道
2. IM 渠道使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
3. 结合客服输入和当前会话提取查询问题“空调不制冷”
4. 调用 `sharecrm knowledge expertise rag-search-knowledge --content "空调不制冷"`
5. 输出知识结论、处理依据、回复参考和参考资料

**测试用例 2：邮件会话命中知识**

输入：客服在邮件会话中输入“客户邮件里的 E01 是什么原因”

预期行为：
1. 调用 `sharecrm service session detail` 并识别 `session_channel=email`
2. 使用当前会话记录 ID（`objectData._id`）查询 `MailObj`
3. 查询条件为 `--customer_service_session_id-eq {当前会话记录_id}`
4. 读取邮件正文 `message_body`
5. 结合客服输入和邮件正文提取知识查询问题并执行知识检索
6. 输出知识结论、处理依据、回复参考和参考资料

**测试用例 3：未命中知识**

输入：客服输入“客户问一个很冷门的产品故障”

预期行为：
1. 获取当前人工会话实时聊天记录
2. 提取查询问题并调用知识检索
3. 判断检索结果不足
4. 输出未检索到足够相关知识，并建议客服结合经验或转入后续流程

### 验证检查清单

- [ ] 已调用 `sharecrm service session detail` 并根据 `session_channel` 判断当前会话是 IM 还是邮件
- [ ] IM 渠道已使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
- [ ] 邮件渠道已使用当前会话记录 ID（`objectData._id`）查询 `MailObj`，读取 `message_body`
- [ ] 查询 `MailObj` 时使用的是 `objectData._id`，不是 `session_id`
- [ ] 已结合客服输入和当前会话内容提取明确的知识查询问题
- [ ] 已调用 `rag-search-knowledge --content`，未使用 `--query` 或 help
- [ ] 已判断检索结果是否足够支撑处理，是否存在冲突或不足
- [ ] 检索不足时未编造知识结论、参考资料或来源引用
- [ ] 输出面向客服辅助处理，不是终端客户最终话术
- [ ] 输出包含知识结论、处理依据、回复参考和参考资料
- [ ] 参考资料来自本次检索命中的知识条目
- [ ] 输出不包含内部命令、调试过程、技术字段或 CHECKPOINT
