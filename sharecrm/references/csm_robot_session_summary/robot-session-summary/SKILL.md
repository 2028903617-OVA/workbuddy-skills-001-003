---
name: "robot-session-summary"
description: "基于当前会话上下文查询同一访客的前序智能客服会话，并从聊天记录中生成客户问题、已处理内容和待跟进事项摘要。"
apiName: "csm_robot_session_summary"
---
# 机器人会话总结

## 1. 适用场景

### 1.1 适用场景

当客服需要快速了解机器人此前与客户的沟通内容时，使用本技能。

典型场景包括：

- 客服接手机器人处理后的会话
- 客服需要快速了解客户问题背景
- 客服需要知道机器人已经做了哪些处理

### 1.2 不适用场景

以下情况不要使用本技能：

- 当前没有可用的会话上下文
- 当前访客没有前序智能客服会话
- 当前不需要了解机器人此前处理情况

## 2. 执行路径

**第一步：获取当前会话上下文**

使用 `sharecrm service session detail` 获取当前会话上下文，并从返回结果中提取 `webim_visitor_id`。

```bash
sharecrm service session detail
```

**第二步：查询同一访客最近会话列表**

使用第一步获取到的 `webim_visitor_id` 查询 `CustomerServiceSessionObj`。必须使用 `query-by-fields` 的 shortcut 参数形式，不使用 `--data` 形式，也不需要临时调用 `sharecrm data describe get` 探索字段。

```bash
sharecrm data record query-by-fields --object_api_name CustomerServiceSessionObj --select_fields _id,session_type,session_id,name,create_time,customer_service_session_id --webim_visitor_id-eq {webim_visitor_id} --sort create_time:desc --limit 5
```

从返回结果中选择最近一条会话类型为“智能客服”的记录。若最近 5 条记录中不存在“智能客服”会话，则停止并输出失败提示。

**第三步：获取智能客服会话完整记录**

基于第二步选中的智能客服会话 `_id`，使用 `get-by-id` 获取该会话完整记录，并从完整记录中读取 `chat_record`。不要仅依赖列表查询返回的 `chat_record` 片段，因为列表查询结果可能被截断。

```bash
sharecrm data record get-by-id --object_api_name CustomerServiceSessionObj --id {智能客服会话_id}
```

若完整记录中的 `chat_record` 为空、无法获取或仍被截断到无法理解完整会话，则停止并输出失败提示。

**第四步：生成会话摘要**

基于智能客服会话的 `chat_record` 内容生成总结。必须包含以下三项：

1. 客户问题摘要
2. 机器人已处理情况
3. 当前待跟进事项

展示原则：

- 客户问题摘要使用 1 段短文本，核心问题、关键状态可使用加粗突出
- 机器人已处理情况可使用表格或短列表展示，重点说明机器人做过什么、结果如何
- 当前待跟进事项可使用短列表展示，并为重要事项标注“高优先级”“中优先级”等文字标签
- 若聊天记录中包含服务请求、报修单、订单、时间、状态等关键记录，可在相关段落中用表格呈现
- 不要输出大段连续文本，不要把聊天记录按时间顺序逐条复述

**第五步：输出摘要**

输出简洁明确的摘要，便于客服快速接手。

## 3. 禁止行为

你不得：

1. 向用户索要当前会话 ID 或访客 ID
2. 自行猜测或编造会话 ID、访客 ID
3. 在未调用 `sharecrm service session detail` 的情况下直接假定当前会话上下文
4. 使用 `sharecrm data record query-by-fields --data` 形式查询会话记录
5. 为了确认字段而临时调用 `sharecrm data describe get`
6. 将会话类型写成未确认的枚举值，如 `robot`、`intelligentCS`
7. 扩展无关历史会话，只查询同一访客最近 5 条会话并选择最近的“智能客服”会话
8. 将内部对象 ID、命令调试过程或原始技术字段直接展示给客服人员
9. 在未找到智能客服会话、未获取完整记录或 `chat_record` 为空时强行生成摘要
10. 编造 `chat_record` 中不存在的内容

## 4. 输出结果

### 4.1 成功输出

输出简洁明确的前序机器人会话摘要，不限制固定标题、固定顺序或固定版式。

必须让客服快速看清：

- 客户主要问题和当前状态
- 机器人已经提供过的处理内容、查询结果或引导动作
- 当前仍需要客服跟进、确认或推进的事项

可根据内容复杂度使用短段落、列表、表格或重点加粗。若历史记录较多，只展示最关键的处理节点，不要按时间顺序逐条复述聊天记录。

### 4.2 失败输出

明确提示当前无法完成总结：

- 当前缺少必要的会话上下文，暂时无法获取机器人前序会话总结。
- 当前未找到同一访客的前序智能客服会话，无法生成机器人会话总结。
- 当前未能成功获取智能客服会话聊天记录，请稍后重试。

## 失败模式

| 失败场景 | 处理方式 |
|---------|---------|
| `sharecrm service session detail` 未返回当前会话上下文或 `webim_visitor_id` | 不得向用户索要 ID；提示“当前缺少会话上下文，无法查询前序智能客服会话，请在会话工作台内重试” |
| 同一访客最近 5 条会话中没有“智能客服”会话 | 提示“当前未找到同一访客的前序智能客服会话，无法生成机器人会话总结” |
| `query-by-fields` 查询失败或超时 | 提示“查询前序智能客服会话失败，请稍后重试” |
| 通过 `get-by-id` 获取完整记录失败 | 提示“当前未能成功获取智能客服会话完整记录，请稍后重试” |
| 完整记录中的 `chat_record` 内容为空或不可用 | 提示“前序智能客服会话无聊天记录，无法生成总结” |
| 权限不足无法访问会话记录 | 提示“当前账号无权限访问该会话记录” |

## 验证清单

### 测试用例

**测试用例 1：成功获取前序智能客服会话**

用户输入：客服进入当前会话，请求查看机器人前序内容

预期行为：
1. 调用 `sharecrm service session detail` 获取当前会话上下文，并从返回中提取 `webim_visitor_id`
2. 使用 `query-by-fields` shortcut 形式查询 `CustomerServiceSessionObj`，查询条件为 `--webim_visitor_id-eq {webim_visitor_id}`，排序为 `--sort create_time:desc`，限制为 `--limit 5`
3. 从返回结果中识别最近一条会话类型为“智能客服”的记录
4. 基于该智能客服会话 `_id` 调用 `sharecrm data record get-by-id` 获取完整记录
5. 从完整记录中读取 `chat_record`，不要使用列表查询中被截断的聊天记录片段
6. 基于 `chat_record` 生成摘要：客户问题摘要、机器人已处理情况、待跟进事项
7. 输出使用短段落、表格和待跟进短列表，且无内部 ID、命令调试信息或原始技术字段

**测试用例 2：同一访客最近会话中无智能客服会话**

用户输入：客服请求查看机器人前序内容，但同一访客最近 5 条会话均不是“智能客服”会话

预期行为：
1. 调用 `sharecrm service session detail` 获取当前会话上下文，并提取 `webim_visitor_id`
2. 使用 `query-by-fields` shortcut 形式查询同一访客最近 5 条会话
3. 未发现会话类型为“智能客服”的记录
4. 输出失败提示：“当前未找到同一访客的前序智能客服会话，无法生成机器人会话总结”
5. 不编造任何机器人处理内容

### 验证检查清单

- [ ] 已调用 `sharecrm service session detail` 并提取 `webim_visitor_id`
- [ ] 已使用 `query-by-fields` shortcut 形式查询同一访客最近 5 条 `CustomerServiceSessionObj`
- [ ] 查询使用了 `--webim_visitor_id-eq {webim_visitor_id}`、`--sort create_time:desc` 和 `--limit 5`
- [ ] 未使用 `query-by-fields --data`，未调用 `sharecrm data describe get`
- [ ] 已选择最近一条“智能客服”会话，并通过 `get-by-id` 获取完整记录
- [ ] 已从完整记录读取 `chat_record`，未使用列表查询中被截断的聊天记录片段
- [ ] 摘要仅基于智能客服会话 `chat_record` 生成
- [ ] 成功摘要包含客户问题摘要、机器人已处理情况、当前待跟进事项
- [ ] 输出使用短段落、表格和待跟进短列表，未逐条复述聊天记录
- [ ] 失败场景有明确提示，输出不包含内部对象 ID、命令调试过程或原始技术字段
