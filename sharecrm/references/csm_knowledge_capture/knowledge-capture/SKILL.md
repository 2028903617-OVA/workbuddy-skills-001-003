---
name: "knowledge-capture"
description: "基于当前会话内容（支持 IM 和邮件渠道）提炼知识候选，并创建标准问答对或知识文章。"
apiName: "csm_knowledge_capture"
---
# 知识沉淀

## 1. 适用场景

### 1.1 适用场景

当客服希望把当前会话中的处理经验、标准答复或可复用内容沉淀为知识时，使用本技能。

典型场景包括：

- 当前会话中出现了可复用的标准问答
- 当前会话中形成了较完整的处理说明或操作指引
- 客服希望把当前问题整理成后续可复用的知识内容

### 1.2 不适用场景

以下情况不要使用本技能：

- 当前聊天内容不足以形成稳定知识
- 当前任务只是查询知识，而不是沉淀知识
- 当前用户尚未准备对知识候选进行确认和创建

## 2. 执行路径


**第一步：获取当前会话上下文并判断渠道** — 使用 `sharecrm service session detail` 获取当前会话上下文，提取当前会话记录 ID（`objectData._id`）和 `session_channel`。若 `session_channel` 返回 `email`，按邮件会话处理；否则按 IM 会话处理。邮件查询必须使用 `objectData._id`，不得使用 `session_id`。

```bash
sharecrm service session detail
```

**第二步：获取当前会话内容** — 基于第一步识别的渠道获取上下文内容。

1. **IM 会话**

   必须使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录，不得用查询 `CustomerServiceSessionObj` 或读取对象 `chat_record` 替代。

   ```bash
   sharecrm service session messages
   ```

2. **邮件会话**

   使用当前会话记录 ID（`objectData._id`）查询邮件对象 `MailObj`。查询条件为 `MailObj.customer_service_session_id` 等于当前会话记录 ID，必须读取邮件正文 `message_body`，并尽量获取邮件主题、发件人、收件人、抄送人、发送时间等信息。

   ```bash
   sharecrm data record query-by-fields --object_api_name MailObj --select_fields _id,subject,from_address,to_address,cc_address,send_time,message_body,customer_service_session_id --customer_service_session_id-eq {当前会话记录_id} --sort send_time:asc --limit 50
   ```

**第三步：提炼知识候选** — 基于当前 IM 实时聊天记录或邮件正文，提炼所有可能的新知识候选。应优先提炼可复用的标准问题、常见相似问法、稳定明确的答案、操作说明和流程说明。若当前会话内容获取失败或内容不足，不得编造知识候选。

**第四步：检索相似知识** — 基于每条候选知识的主题搜索知识库，检查是否已有相似内容。使用以下命令：
```bash
sharecrm knowledge expertise rag-search-knowledge --content "{候选知识的主题关键词}"
```
若 rag-search-knowledge 不可用，使用标准知识检索命令搜索知识库。


**第五步：输出候选总结** — 对每条候选知识输出总结结果，并在该条结果下标注：
- 知识摘要
- 是否存在相似知识（若有则列出标题或摘要）
- 建议创建类型

**第六步：判断创建类型** — 根据知识内容判断：
- 短问短答型内容 → 创建为标准问答对（QuestionAnswerPairObj）
- 图文说明、步骤说明、文章型内容 → 创建为知识文章（KnowledgeArticleObj）

**第七步：询问用户选择** — 明确询问用户：
- 要创建哪一条候选知识
- 创建为标准问答对还是知识文章

**第八步：执行创建** — 只有在用户给出明确指令后，才按用户实际选择执行知识对象创建。

创建标准问答对时，对象名为 `QuestionAnswerPairObj`，`object_data` 固定使用 `standard_question`、`similar_questions`、`answer`、`category`、`publication_status`，其中 `category` 固定为"-40"，`publication_status` 默认值为"unpublished"。

创建知识文章时，对象名为 `KnowledgeArticleObj`，`object_data` 固定使用 `title`、`graphic_text`、`category`、`public_status`，其中 `category` 固定为"-36"，`public_status` 默认值为"2"。

```bash
sharecrm data record create --data '{"object_api_name":"QuestionAnswerPairObj","object_data":{"standard_question":"标准问题","similar_questions":"相似问题","answer":"答案","category":"-40","publication_status":"unpublished"}}'

sharecrm data record create --data '{"object_api_name":"KnowledgeArticleObj","object_data":{"title":"标题","graphic_text":"图文内容","category":"-36","public_status":"2"}}'
```

## 3. 禁止行为

你不得：

- 在没有足够当前会话内容和上下文的情况下编造知识
- IM 渠道未获取 `sharecrm service session messages` 返回的当前实时聊天记录就提炼知识
- 邮件渠道未获取 `MailObj.message_body` 就提炼知识
- 邮件渠道使用 `session_id` 查询 `MailObj.customer_service_session_id`
- 在未检查相似知识前直接创建知识对象
- 在用户未明确选择知识条目和对象类型前直接创建
- 将多条候选知识一次性全部自动创建
- 混淆标准问答对和知识文章的对象结构
- 自行更改 `QuestionAnswerPairObj` 或 `KnowledgeArticleObj` 的字段结构
- 将内部对象名、字段名或调试过程展示给用户

## 4. 输出结果

### 4.1 成功输出

成功时，应先输出 AI 提炼出的知识候选结果，再等待用户选择创建。不限制固定模板。

每条候选知识需让用户看清：

1. 知识摘要
2. 是否存在相似知识（若有则列出相似知识标题或摘要）
3. 创建类型建议

然后明确询问用户需要创建哪一条，以及创建为标准问答对还是知识文章。不要把多条候选一次性全部自动创建。

在用户明确确认后，说明对应知识对象已创建成功。

### 4.2 失败输出

如果当前内容不足以形成稳定知识，或不足以支持相似知识检查，则明确说明当前暂不建议沉淀。

输出可由 Agent 根据实际原因自行组织，但必须说明当前为什么不适合沉淀。

- "当前聊天内容暂时不足以整理为稳定可复用的知识，请补充更完整的信息后再进行沉淀。"
- "当前未识别出适合沉淀的标准问答对或知识文章。"

## 失败模式

| 失败场景 | 触发条件 | 处理方式 |
|---------|---------|---------|
| IM 当前人工会话聊天记录获取失败 | sharecrm service session messages 返回错误 | 提示"当前会话聊天记录暂不可用，无法进行知识沉淀" |
| 邮件正文获取失败 | 未查询到关联 MailObj 或 message_body 为空 | 提示"当前会话关联邮件内容暂不可用，无法进行知识沉淀" |
| 内容不足以形成知识 | 当前会话内容太短或不完整 | 明确说明"当前内容不足以整理为稳定可复用的知识"，请用户补充信息 |
| 相似知识检查失败 | rag-search-knowledge 返回错误或超时 | 跳过相似度标记，在候选知识上标注"相似知识检查暂不可用，请人工核实" |
| 创建 API 返回异常 | sharecrm data record create 返回非 200 状态码 | 提示"知识对象创建失败，请稍后重试"，记录错误信息和请求参数 |
| 用户长时间未选择 | 超过 3 轮对话用户未明确指定候选条目或类型 | 提示"您可以稍后通过本技能继续完成知识沉淀" |
| 相似知识已存在但用户仍确认创建 | 知识库含 ≥2 条高度相似内容，用户仍要求创建 | 在创建成功后增加提示"已创建成功，请注意知识库中已有相似内容，建议后续去重整理" |
| 对象字段定义与预期不符 | 创建时接口返回字段不存在错误 | 先查询对象结构定义再重试，若仍失败则提示"当前对象字段结构有变更，请联系管理员" |

## 验证清单

### 测试用例

**测试用例 1：完整知识沉淀流程**
- 输入：客服通过 IM 会话完整解答了客户关于"如何重置密码"的问题，客服说"把这个沉淀为知识"
- 预期行为：
  1. 调用 `sharecrm service session detail` 并识别为 IM 会话
  2. 使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
  3. 提炼知识候选：提取"如何重置密码"标准问答
  4. 检索相似知识：搜索知识库是否已有重置密码相关文章
  5. 若无相似内容，标注"未发现相似"
  6. 判断类型：短问短答型 → 推荐标准问答对
  7. 询问用户选择
  8. 用户确认后，调用 `sharecrm data record create` 创建 QuestionAnswerPairObj
  9. 输出"知识对象已创建成功"

**测试用例 2：邮件会话知识沉淀**
- 输入：客服在邮件会话中收到完整的设备复位处理步骤，希望沉淀为知识
- 预期行为：
  1. 调用 `sharecrm service session detail` 并识别 `session_channel=email`
  2. 使用当前会话记录 ID（`objectData._id`）查询 `MailObj`
  3. 查询条件为 `--customer_service_session_id-eq {当前会话记录_id}`
  4. 读取邮件正文 `message_body`
  5. 基于邮件内容提炼知识候选并检索相似知识
  6. 等待用户选择候选条目和创建类型后再创建

**测试用例 3：内容不足以沉淀**
- 输入：客服只说了"好的""明白了"等简单对话，然后说"帮忙沉淀知识"
- 预期行为：
  1. 获取当前会话上下文并按渠道获取当前会话内容
  2. 尝试提炼知识候选 → 无法提取稳定内容
  3. 输出失败："当前聊天内容暂时不足以整理为稳定可复用的知识"
  4. 请用户补充更完整的信息

### 验证检查清单

- [ ] 已调用 `sharecrm service session detail` 并根据 `session_channel` 判断当前会话是 IM 还是邮件
- [ ] IM 渠道已使用 `sharecrm service session messages` 获取当前人工会话实时聊天记录
- [ ] 邮件渠道已使用当前会话记录 ID（`objectData._id`）查询 `MailObj`，读取 `message_body`
- [ ] 查询 `MailObj` 时使用的是 `objectData._id`，不是 `session_id`
- [ ] 已基于当前 IM 实时聊天记录或邮件正文提炼知识候选，未编造内容
- [ ] 每条候选知识均包含知识摘要、相似知识情况和建议创建类型
- [ ] 已使用 `rag-search-knowledge --content` 检索相似知识
- [ ] 发现高度相似知识时，已提示用户核实，未直接创建
- [ ] 已判断候选知识适合标准问答对还是知识文章
- [ ] 用户未明确选择候选条目和创建类型前，未执行创建
- [ ] 创建标准问答对使用 `QuestionAnswerPairObj` 及固定字段；创建知识文章使用 `KnowledgeArticleObj` 及固定字段
- [ ] 已使用 `sharecrm data record create --data` 创建知识对象
- [ ] 未使用未定义创建 action，未输出内部对象字段或调试过程
