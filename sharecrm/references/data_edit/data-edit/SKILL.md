---
name: "data-edit"
description: "自然语言编辑、修改、更新、变更或调整 CRM 主对象已有记录的字段值；禁止修改从对象、子对象、明细行或 details。用于修改客户信息、变更联系人电话、调整商机主对象金额、编辑主对象字段等业务对象，或用户表达 帮我改一下/把XX改成/更新一下/修改这条记录/调整字段值/编辑一下XX 等意图。线索状态流转或线索专属动作不走本 skill，包括把线索改为跟进中、将线索修改为无效/作废/关闭、记录线索跟进结果、设置下次跟进时间等，应优先走线索专属 skill 或 CLI 专用命令。"
apiName: "data_edit"
---
# data-edit

把用户的自然语言变成一次安全的 CRM 主对象记录更新。整条链路是一个串行的解析过程：

```
准备编辑表单 → 组装 object_data → 保存 → 返回结果
```

每一步都依赖上一步的真实返回值。这条 skill 的核心风险只有一个：**在信息还没确定时就往下猜**——猜错对象、改错记录、给只读字段回填值、编造关联记录 ID、把展示名当提交值写进枚举。编辑比新建更危险，因为它直接覆盖一条已经存在、用户正在用的真实数据，改错往往要事后才被发现。所以下面每一步的约束，本质都是在回答同一个问题：*“我现在掌握的信息，足够让我安全地改下一步吗？”* 信息不足时，宁可停下来问用户，也不要编造。

一个贯穿全程的原则：**用户中途改了任何会影响结果的信息（对象、目标记录、字段值、关联记录），就从受影响的最早步骤重新走一遍，不要复用旧的表单上下文。** 那些旧数据是针对旧输入算出来的，复用就等于拿过期的真相去覆盖一条真实记录。

## 不适用场景 / 路由排除

本 skill 只处理通用主对象字段编辑。**进入流程前，核查当前业务对象是否存在与用户意图完全匹配的专属命令；有则直接走专属命令，不启用本能力。**

### 专属操作路由表

以下操作有专属 CLI 或 skill，不走本 skill：

| 操作 | 路由目标 | 类型 |
|---|---|---|
| 客户/线索分配 | `sharecrm sales AllocateAction` | CLI |
| 客户/线索退回 | `sharecrm sales ReturnAction` | CLI |
| 客户/线索收回 | `sharecrm sales TakeBack` | CLI |
| 客户/线索转移 | `sharecrm sales MoveAction` | CLI |
| 客户/线索移除 | `sharecrm sales RemoveAction` | CLI |
| 客户/线索领取 | `sharecrm sales ChooseAction` | CLI |
| 线索无效 | `sharecrm sales lead leads-close` | CLI |
| 线索跟进 | `sharecrm sales lead leads-follow-up` | CLI |
| 线索转换 | `sfa_leads_convert` | Skill |

### 从对象排除

本 skill 只改主对象字段。**用户要求修改从对象、子对象、明细行或 `details` 时，停下来说明本能力只支持主对象字段编辑。**

## 工作流总览

| 步骤 | 目的 | 走下一步的前提 |
|---|---|---|
| 0 路由核查 | 确认没有更合适的专属命令 | `sharecrm data record -h` 中无完全匹配的专属命令 |
| 1 准备编辑表单 | 一步完成识别对象、定位唯一记录、拉编辑表单 | `prepare_edit_form.py` 返回 `status=READY` |
| 2 组装 object_data | 在原记录基础上构造修改后快照 | 命中对象有专属引用文件时已读；关联字段已解析到唯一 ID |
| 3 保存 | 写入系统 | object_data 已组装完成 |
| 4 返回结果 | 回传更新卡片 | — |

---

## 步骤 1：准备编辑表单

识别对象、定位唯一记录、拉编辑表单这三件事强依赖、串行执行，且都是确定性的 CLI 调用，所以合并成一个脚本一次跑完，省掉中间几轮往返。

**同一对象 + 同一条记录、且尚未保存过，可复用上一份表单，不要重复请求。** 如果本轮对话里刚刚已经为某条记录拉过 `READY` 表单，用户接着又要改**同一个对象、同一条记录**（同一 `object_api_name` + 同一 `data_id`）的其它字段，就直接复用上一次返回的那份 `form`（`form_fields` / `field_metadata` / `object_data`），不要再跑 `prepare_edit_form.py`——对同一条记录，可改字段布局和当前记录快照是一致的，重跑只会拿到相同内容、白白多一轮往返。只有在下列任一情况成立时才重新跑脚本：对象变了、目标记录变了、还没定位到唯一记录、上一份表单不存在（本轮还没拉过），**或已经对这条记录执行过保存**——保存后记录已变更，上一份 `object_data` 已是过期快照，必须重新拉取才能拿到最新底座，否则会拿旧值覆盖刚改的内容。

**先拿到记录关键词和表单，再做任何其他事。** 在脚本返回 `READY` 之前（且无可复用的上一份表单时），不要去解析关联记录、不要查任何关联 ID、也不要凭空向用户罗列“能改哪些字段”。

这一步只需要两样输入：**对象名** 和 **记录关键词**（名称/编号/标题/记录 ID 等，用来定位是哪一条记录）。`prepare_edit_form.py` 的 `--object-name` 只接受**对象类型名**（如"客户/商机/联系人"），它走的是对象识别（identify-with-describe）；要定位的那条记录的名称/编号走 `--record-query`，绝不要把记录关键词或要改的字段值塞进 `--object-name`——传错了脚本会拿记录名去匹配对象，零命中返回 `OBJECT_NOT_FOUND`。所以进脚本前，先从用户输入里把它们拆开：

| 用户输入 | `--object-name` 传 | `--record-query` 传 |
|---|---|---|
| 把客户大麦网的来源改成线上注册 | `客户` | 大麦网 |
| 修改联系人张三的电话 | `联系人` | 张三 |

- 缺记录关键词时，先用 `AskUserQuestion` 问用户"要编辑哪一条记录"——没有它无法定位，也就无法继续。
- 一句话里**识别不出明确的对象类型词**时，不要把记录关键词硬当对象名传进去——先用 `AskUserQuestion` 问用户"要编辑哪一类对象"，确认后再调脚本。
- 用户要改的**字段和新值**留到步骤 2 再用，它不影响定位，不必在这一步凑齐。但如果用户连改什么都没说，那就只能先定位/展示记录，不要构造或保存任何数据。

为什么不能先查关联记录：拿到表单前，你并不知道这条记录到底有没有那个关联字段、它真实的 `field_name` 和关联对象 `apiName` 是什么、是否只读。先查到的 ID 可能根本无处可写、或写错字段、或对应了错误的关联对象。表单才是“这条记录这次能改哪些字段、关联哪个对象”的权威真相，必须先有它。

```
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_edit_form.py --object-name '<对象名称>' --record-query '<记录关键词>'
```

如果上下文已明确对象 apiName，就直接传 `--object-api-name` 跳过对象识别（避免拿口语名去匹配时零命中或多命中）；`--object-name` 只在你还不知道 apiName、手上只有口语名时才用。

记录侧同理：已知 data_id 传 `--data-id` 跳过查询直达就绪，只知道记录关键词就配 `--record-query`：

```
# apiName + data_id 都已知（如用户给了记录 URL 或现成记录 ID）：直达就绪
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_edit_form.py --object-api-name '<apiName>' --data-id '<选定的 data_id>'
# 只确定 apiName（如本 skill 绑定固定对象，或已从对照表知道 日程→ScheduleObj）、记录仍按名定位：
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_edit_form.py --object-api-name '<已确定的对象 apiName>' --record-query '<记录关键词>'
```

脚本内部依次跑 `identify-with-describe` → `query-id-by-name` → `get-edit-form`（传了 `--object-api-name` 时跳过第一步识别），并用 stdout 里的 `status` 字段告诉你下一步怎么走。它不会替用户做“猜”的决定，遇到不确定就把球踢回来：

- **`status="OBJECT_NOT_FOUND"`**：一个可用对象都没匹配到。不要硬选，用 `AskUserQuestion` 请用户更换对象名称或确认该对象是否存在后重跑。收到这个状态时先回头检查一件事：你传给 `--object-name` 的是不是误把**记录关键词**当成了对象类型（例如把"大麦网"当对象传了）。若是，改回真正的对象类型（如"客户"）、把记录关键词放回 `--record-query` 重跑，而不是反复换词。
- **`status="OBJECT_NOT_RESOLVED"`**：对象命中多个候选。结果里带 `object_candidates`，用 `AskUserQuestion` 把候选交用户确认，别自己挑最像的。确认后用真实 `object_api_name` 重跑（不要再传模糊的 `--object-name`，否则又会触发识别、再次多命中）：

  ```
  cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_edit_form.py --object-api-name '<确认的 apiName>' --record-query '<记录关键词>'
  ```

- **`status="RECORD_NOT_FOUND"`**：按该关键词没查到记录。用 `AskUserQuestion` 请用户提供更准确的名称/编号后重跑，不要编造记录。
- **`status="RECORD_NOT_RESOLVED"`**：记录命中多条。结果里带 `record_candidates`（每项含 `name`/`data_id`），用 `AskUserQuestion` 把列表交用户选——**选定前绝不写入任何候选 ID，也不要继续往下**。选错记录等于改错人。用户选定后带上 `--data-id` 直接进就绪：

  ```
  cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_edit_form.py --object-api-name '<apiName>' --data-id '<选定的 data_id>'
  ```

- **`status="READY"`**：已就绪，可以组装 object_data。结果里带 `object_api_name`、`data_id` 和 `form`。**这一步到此为止，不要为了“看完整表单”再重跑脚本**——`form` 已经是组装数据所需的全部真相。**同样地，紧接着如果用户要改同一对象、同一条记录的其它字段、且这条记录还没被保存过，直接复用这份 `form`，不要重跑脚本**（见本步骤开头的复用规则；一旦保存过就必须重新拉取）。

  `form` 含三部分，是“这条记录这次到底能改哪些字段”的权威真相，组装时只认这一份（见步骤 2）：

  - `form_fields`：本次可改的字段布局。每项含 `field_name`、`is_required`、`is_readonly`、`render_type` 等。
  - `field_metadata`：每个字段对应的描述——含义、类型、选项的合法提交值、关联信息。
  - `object_data`：**当前记录的完整数据**，是构造修改后快照的基础底座，原样复制再改。

  脚本已剔除 `details`/从对象数据。即使底层接口返回 `details`，也不读取、不修改、不校验、不提交——本 skill 只处理主对象 `object_data`。

  关于业务类型：编辑沿用记录已有的 `record_type`，不主动选择。如 `object_data` 已含 `record_type`，原样保留；除非字段元数据和对象专属规则都明确允许、且用户明确要求，否则不新增、删除或改写它。

## 步骤 2：组装 object_data

以 `form.object_data`（当前记录完整数据）为基础**复制一份**，再合并用户要求修改的字段。只认步骤 1 返回的这份表单，几条铁律：

1. **保留未改动的一切。** 保留 `_id` 或数据主键，保留用户没要求改的原值——你是在改一条记录的局部，不是重建它。不要从空对象或旧轮次快照重建。
2. **只读字段是雷区。** `form_fields` 中 `is_readonly=true` 的字段保留原值，绝不写入用户值、推断值或计算值——它们由系统或公式维护，强行回填会被拒绝或写出矛盾数据。
3. **必填以 `is_required` 为准。** 不删除已有必填字段值，除非用户明确要求清空且该字段允许为空。
4. **选项字段只认提交值。** `field_metadata` 里带 `options` 的字段（如 `select_one`/`select_many`），必须写合法 value 而非展示名；用户给中文名/`label` 时先映射成 value，映射不唯一或找不到时先确认，别猜。
5. **不碰从对象。** 不构造、不修改、不提交 `details`，不修改从对象、子对象或明细行。
6. 除接口或对象专属规则明确要求外，只写 `form_fields` 中存在且非只读的字段。

### 2.1 对象专属逻辑（命中即先读）

有些对象有超出通用规则的特殊构造逻辑。组装前先按下表判断是否需要读引用文件：

| 目标对象 `apiName` | 必须先读的引用文件 |
|---|---|
| `ActiveRecordObj` | `{Current agent directory}/skill/{skillApiName}/references/ActiveRecordObj.md` |

命中时先读对应文件并应用其约束，再构造 `object_data`。引用文件里的特殊构造逻辑优先于通用规则；但可改字段、必填状态、枚举提交值仍以本次 `get-edit-form` 返回为准（引用文件管“怎么算”，表单返回管“能改什么”）。

### 2.2 关联对象字段（必须解析到唯一 ID）

关联记录的解析只在这一步做，前提是步骤 1 已返回 `READY`、表单里确实存在这个关联字段。**不要在拿到表单前就抢跑查询**：先在 `form_fields`/`field_metadata` 里确认该字段存在、拿到真实 `field_name` 和关联对象 `apiName`，再据此解析。

当字段类型是 `object_reference`、`master_detail`、`object_reference_many`，或元数据/对象专属规则表明该字段要关联已有记录时，必须先解析成唯一可提交的记录 ID 再写入。编造一个 ID 会让记录挂到错误的客户/商机上，是最难被发现的脏数据之一。

必填关联字段在用户未提供、或用户明确表示"待定/以后再说/不确定"时，必须停下来用 `AskUserQuestion` 让用户提供或选择，禁止自行用 query-by-fields 等方式列举候选并默认选取（如选最近一条）。没有用户给的关键词就不要发起关联查询。

解析路径：

- 用户直接给了符合字段要求的明确 ID → 可直接用。
- 用户给的是名称/编号/手机号/公司名/联系人名等文本 → **关联对象的 apiName 直接从该字段的 `field_metadata` 里读**（元数据已返回这个字段确认的关联对象 apiName），不必再跑 `identify-with-describe`。拿到关联对象 apiName 后，用批量脚本解析记录 ID（入参是 Map，key 为关联对象 apiName，value 为关键词；只有一个关联字段就传一个 key，多个字段一次传多个 key 并发查完）：

  ```
  cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_id_by_name_batch.py --data '{"<关联对象apiName1>":"<关键词1>","<关联对象apiName2>":"<关键词2>"}'
  ```

  当多个关联字段指向**同一个关联对象**（apiName 相同），不能用重复 key（JSON 会互相覆盖），要把 value 写成**关键词数组**，一次查完：

  ```
  cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_id_by_name_batch.py --data '{"<同一关联对象apiName>":["<关键词1>","<关键词2>"]}'
  ```

  该对象下多个关键词的命中会合并进同一个 `name2IdPos`，按 `name` 把记录回填到对应字段。

  返回按对象汇总，每个对象的命中记录在 `name2IdPos` 里（含 `name` 和 `id`）。Map 的 key 取自各关联字段 `field_metadata` 中的关联对象 target_api_name，不是当前正在编辑的对象。常用关联对象 apiName 速查：人员 `PersonnelObj`、部门 `DepartmentObj`。

  若命中多条、需要看候选记录的其他字段来辨别是哪一条，再用 `query-by-name`（它返回记录全量值）：

  ```
  sharecrm data record query-by-name --data '{"name":"<名称或关键词>","object_api_names":["<关联对象apiName>"]}'
  ```

  命中后的处置规则：

  - 查到 1 条 → 可用，并记下记录名称/编号与 ID。
  - 查到多条 → 用 `AskUserQuestion` 让用户选；选定前不要写入任何候选 ID，也不要继续保存。
  - 查不到 / 无法判断 → 停下来，不要编造 ID 或默认选第一条。
  - 用户改了关联条件 → 重新查、重新确认。

### 2.3 各字段类型的写法

| 字段类型 | 写法 | 示例 |
|---|---|---|
| `owner` / `employee` / `department` / `dimension` | 按元数据要求用 ID 数组 | `{"owner": ["1016"]}` |
| `date` | 日期字符串 `yyyy-MM-dd` | `"close_date": "2026-06-08"` |
| `date_time` | 日期时间字符串 `yyyy-MM-dd HH:mm:ss` | `"meeting_time": "2026-06-08 14:30:00"` |
| `select_one` | 元数据中的合法提交值 | `"sales_stage": "1"` |
| `select_many` | 数组，元素为合法提交值 | `"crm__c": ["Salesforce"]` |
| `percentile` | 提交值是百分号前的数值（可小数），不要换算成 0–1 比例。九折/9折/90% 写 `90`，0.9% 写 `0.9` | `"discount_rate": 90` |
| `rich_text` | 使用纯文本内容，不要写入 HTML 标签或富文本源码；用户给 HTML 时先转成可读纯文本 | `"description": "客户希望下周二沟通方案"` |
| `object_reference` / `master_detail` | 唯一命中或用户确认后的记录 ID 字符串 | `"account_id": "69e9a174..."` |
| `object_reference_many` | 唯一命中或用户确认后的记录 ID 数组 | `"contact_ids": ["69e9a174..."]` |

## 步骤 3：保存数据

object_data 组装完成后，直接保存——格式校验、必填校验等都交给保存接口负责。

**`sharecrm` 是独立注册的工具（tool），必须直接以工具方式调用，绝不要用 bash/shell 执行，绝不要加 `cd ... &&` 前缀或任何 shell 包裹。** （只有 `scripts/*.py` 这类脚本才需要 `cd` 到 skill 目录后用 bash 跑；`sharecrm ...` 命令本身就是工具调用，原样作为工具输入即可。）

```
sharecrm data record update --data '{"object_api_name": "<object_api_name>", "object_data": <已组装的 object_data>}'
```

保存 payload 中不得包含 `details`。保存失败时读错误信息，仅在错误明确指向可修正的字段问题时回到字段映射步骤修正后**至多重试一次**，不要盲目重复提交；具体失败处置见步骤 4。

## 步骤 4：返回结果

调用保存后，**先判断接口返回，只有记录确实更新成功时才用 `render_content` 输出**，且成功时不要再附加任何文字总结。

返回不是「更新成功」时（例如系统返回需要二次确认的状态——重复校验/防重提示等，或返回报错），**不要调用 `render_content`**，也不要凭空生成一张「已更新」的结果卡或成功话术：

- **需要二次确认**：把系统要求确认的内容如实转达给用户（用 `AskUserQuestion`），等用户确认后再按系统要求重新提交；只有最终真正更新成功，才走 `render_content`。
- **返回 `User declined to create or update this record.`**：用户已明确拒绝本次更新，**立即终止整个操作**——不重试、不换方式重新提交、不再追问、不渲染结果卡，如实告知用户本次更新已取消即可。
- **返回 `errorCode=EXECUTE_FAILED`（或类似"当前对象不支持执行该操作/无权限/操作被禁止"的错误）**：这类错误表示**操作本身不被允许或不被支持**，不是字段写法问题，**立即终止，绝对不要重试、不要换字段或换参数重新提交**。如实把错误信息告诉用户即可。
- **保存失败 / 报错**：把失败原因如实告诉用户，不要伪装成成功，也不要渲染结果卡。**不要自动反复重试、不要换着花样重复提交。** 仅当错误信息明确指出某个可修正的字段问题（如枚举提交值非法、关联 ID 写错、必填缺失）时，回到对应步骤修正后**至多重试一次**；若重试仍失败、或错误原因不明确/不可由你自行修正（如权限、流程校验、系统异常、`EXECUTE_FAILED`），立即停下来把错误如实告知用户并等待用户指示，禁止继续循环提交。
