---
name: "data-add"
description: "自然语言创建、录入、登记、添加、保存、生成或写入 CRM 对象数据记录。用于新建客户、创建线索、录入联系人、登记商机、添加订单/报价/产品/产品组合/组合/等业务对象，或用户表达“帮我建一条/新增一条/写入一条/保存到系统/创建记录/录入数据”等意图。"
apiName: "data_add"
---
# data-add

把用户的自然语言变成一条可落库的 CRM 记录。整条链路是一个串行的解析过程：

```
准备新建表单 → 组装 object_data → 保存 → 返回结果
```

每一步都依赖上一步的真实返回值。这条 skill 的核心风险只有一个：**在信息还没确定时就往下猜**——猜错对象、猜错业务类型、给只读字段回填值、编造关联记录 ID。这些都会写出一条错误的脏数据，而且用户往往要事后才发现。所以下面每一步的约束，本质都是在回答同一个问题：*“我现在掌握的信息，足够让我安全地走下一步吗？”* 信息不足时，宁可停下来问用户，也不要编造。

## 工作流总览

| 步骤 | 目的 | 走下一步的前提 |
|---|---|---|
| 1 准备新建表单 | 一步完成识别对象、确定业务类型、拉新建表单 | `prepare_create_form.py` 返回 `status=READY` |
| 2 组装 object_data | 构造提交数据 | 命中对象有专属引用文件时已读；关联字段已解析到唯一 ID |
| 3 保存 | 写入系统 | object_data 已组装完成 |
| 4 返回结果 | 回传创建卡片 | — |

一个贯穿全程的原则：**用户中途改了任何会影响结果的信息（对象、业务类型、字段值、关联记录、明细），就从受影响的最早步骤重新走一遍，不要复用旧的表单元数据。** 因为那些旧数据是针对旧输入算出来的，复用就等于拿过期的真相去提交。

---


## 步骤 1：准备新建表单

**调脚本前先做语义拆分。** 用户一句话里常同时含两类信息：①对象类型（要建哪类记录，如"客户/商机/联系人"），②记录本身的名称或字段值（如"大麦网""王小二"）。`prepare_create_form.py` 的 `--object-name` 只接受**对象类型名**，它走的是对象识别（identify-with-describe），不是用来传记录名的。所以调脚本前，先把输入拆成两半：对象类型传给 `--object-name`；记录名称/字段值先记着，留到步骤 2 处理。`--object-name` 里**只放对象名称**，绝不要放记录名称、冒号/破折号/"叫做"等后面跟的内容、或任何字段值——传错了脚本会拿记录名去匹配对象，零命中返回 `OBJECT_NOT_FOUND`，白跑一轮还会把用户绕晕。

| 用户输入 | `--object-name` 传 |
|---|---|
| 新建一个客户：大麦网 | `客户` |
| 录入联系人张三 | `联系人` |

非对象类型的信息怎么写入各字段，见步骤 2，这里不展开。如果一句话里**识别不出明确的对象类型词**，不要把记录名硬当对象名传进去——先用 `AskUserQuestion` 问用户"要建哪一类对象"，确认后再调脚本。

识别对象、确定业务类型、拉新建表单这三件事强依赖、串行执行，且都是确定性的 CLI 调用，所以合并成一个脚本一次跑完，省掉中间几轮往返。

**同一对象 + 同一业务类型可复用上一份表单，不要重复请求。** 如果本轮对话里刚刚已经为某个对象拉过 `READY` 表单，用户接着又要建**同一个对象、同一个业务类型**的另一条记录（哪怕只是换了字段值、换了记录名），就直接复用上一次返回的那份 `form`（`form_fields` / `field_metadata` / `initial_object_data`），不要再跑 `prepare_create_form.py`——对同一 `object_api_name` + `record_type`，表单结构和系统默认底座是稳定不变的，重跑只会拿到完全相同的内容、白白多一轮往返。只有在下列任一情况成立时才重新跑脚本：对象变了、业务类型变了、还没确定唯一对象或唯一业务类型、或上一份表单不存在（本轮还没拉过）。复用时记得以 `initial_object_data` 为全新底座重新组装（每条新记录从干净的默认值开始，不要带上一条已填的值）。

**先拿表单，再做任何其他事。** 这一步（步骤 1）必须是整条链路的第一个动作——在它返回 `READY` 之前（且无可复用的上一份表单时），不要做任何别的调用：不要先去 `query-id-by-name` 解析“关联客户/关联商机/负责人”等关联记录，不要先查任何 ID，也不要凭空向用户罗列“需要填哪些信息”。哪怕用户一句话里同时给了对象和关联信息（例如“帮我新建商机，关联客户王小二”），也先只用对象名（“商机”）把表单拉回来，关联记录的解析留到步骤 2.2 再做。
为什么不能先查关联记录：在拿到表单前，你并不知道这个对象到底有没有那个关联字段、它的真实 `field_name` 和关联对象 `apiName` 是什么、是否只读、是否必填。先查到的 ID 可能根本无处可写、或写错字段、或对应了错误的关联对象，等于拿没根据的结果往下猜。表单才是“这次能写哪些字段、关联哪个对象”的权威真相，必须先有它。
即使用户一开始只给了零散信息、甚至只说“帮我创建客户”，也先把这一步跑完拿到真实表单，再根据表单里的字段判断缺什么、要不要问用户。不要在拿到表单前就凭空向用户罗列“需要填哪些信息”——那时你还不知道这个对象到底有哪些字段、哪些必填、哪些已经有默认值，凭空问既可能漏掉关键字段，也可能问一堆其实有默认值或根本不存在的字段，反而打断用户。

```
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_create_form.py --object-name '<对象名称>'
```

**已经确定 apiName 时，首次调用就直接传 `--object-api-name`，不要再用 `--object-name` 绕一圈识别。** 当你在调脚本前就已明确目标对象的 apiName——例如本 skill 本就绑定固定对象，或你已从对象专属引用文件/对照表里读到它的 apiName（如「日程」对应 `ScheduleObj`）——直接用 `--object-api-name` 传这个确定的 apiName 作为首次调用。这样会跳过 `identify-with-describe`，既省一轮，也避免拿口语名去匹配时零命中或多命中。`--object-name` 只在你**还不知道 apiName、手上只有口语对象名**时才用；两者二选一，apiName 已知就优先用 `--object-api-name`：

```
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_create_form.py --object-api-name '<已确定的对象 apiName>'
```

脚本内部依次跑 `identify-with-describe` → `record-list` → `get-create-form`（传了 `--object-api-name` 时跳过第一步识别），并用 stdout 里的 `status` 字段告诉你下一步怎么走。它不会替用户做"猜"的决定，遇到不确定就把球踢回来：

- **`status="OBJECT_NOT_FOUND"`**：一个可用对象都没匹配到——要么对象名没命中任何候选，要么命中的候选在查业务类型时全部失败/为空被剔除。结果里带明确提示（未匹配到任何可用对象）。这是死路，不要硬选：请用户更换对象名称或确认该对象是否存在，再重跑。收到这个状态时先回头检查一件事：你传给 `--object-name` 的是不是误把**记录名称**当成了对象类型（例如把"大麦网"当对象传了）。若是，改回真正的对象类型（如"客户"）重跑，而不是反复换词。它与 `OBJECT_NOT_RESOLVED`（有多个候选、等用户挑一个）语义不同，别混用。
- **`status="OBJECT_NOT_RESOLVED"`**：对象命中了多个候选，没唯一确定。结果里带 `object_candidates`，且每个候选现在已附带它自己的 `record_types`（每项有 `label`/`value`）——脚本一次性把各候选对象的业务类型都查回来了，你可以在一轮交互里把「建哪个对象、对应哪些业务类型」一并呈现给用户确认，别自己挑最像的。用户确认后，用候选里那个对象的真实 `object_api_name` 重跑（不要再传模糊的 `--object-name`，否则又会触发识别、再次多命中）；若业务类型也已一并确认，连 `--record-type` 一起带上直接就绪：

  ```
  # 只确认了对象的apiName，业务类型还没选定时：
  cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_create_form.py --object-api-name '<确认的 apiName>'
  # 业务类型也已选定时：
  cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_create_form.py --object-api-name '<确认的 apiName>' --record-type '<选定的 value>'
  ```

- **`status="RECORD_TYPE_SELECTION_REQUIRED"`**：业务类型有多个候选。结果里带 `object_api_name` 和 `record_types`（每项有 `label`/`value`）。把候选列给用户选——不同业务类型的字段差异可能很大，选错会让整条记录建错类别。用户选定后，带上结果里返回的 `object_api_name`（已是真实 apiName）和选定的 `--record-type` 重跑，直接进就绪：

  ```
  cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_create_form.py --object-api-name '<返回的 object_api_name>' --record-type '<选定的 value>'
  ```

- **`status="READY"`**：已就绪，可以组装 object_data。结果里带 `object_api_name`、`record_type` 和 `form`。**这一步到此为止，不要再为了"看完整表单"或"拿字段细节"重跑脚本**——`form` 已经是组装数据所需的全部真相，二次调用只会浪费一轮往返且拿到完全相同的内容。**同样地，紧接着如果用户要建同一对象、同一业务类型的下一条记录，直接复用这份 `form`，不要重跑脚本**（见本步骤开头的复用规则）。

  `form` 含三部分，是"本次创建到底能写哪些字段"的权威真相，组装时只认这一份（见步骤 2）：

  - `form_fields`：本次可写的字段布局。每项含 `field_name`、`is_required`（是否必填）、`is_readonly`（是否只读）、`render_type`（输入类型）等。
  - `field_metadata`：`form_fields` 里每个字段对应的描述——字段含义、类型、选项的合法提交值、关联信息。
  - `initial_object_data`：构造 `object_data` 的基础底座（含系统默认值），原样保留。

  拿到表单后，先对照 `form_fields` 看必填字段（`is_required=true`）哪些用户还没给、且 `initial_object_data` 里也没有默认值——这些才是真正需要回头问用户的缺口。用 `AskUserQuestion` 把缺口讲清楚再问，别问表单里没有的字段。

补充：用户说“合同 / 销售合同”时，对象名称按 `销售合同`（`SaleContractObj`）传。

## 步骤 2：组装 object_data

以 `initial_object_data` 为初始值，写入步骤 1 已确定的 `record_type`，再合并从用户输入解析出的字段值。只认步骤 1 返回的这份表单，三条铁律：

1. **只读字段是雷区。** `form_fields` 中 `is_readonly=true` 的字段原样保留 `initial_object_data` 里的值，绝不写入用户值、默认补值、推断值或计算值——它们由系统或公式维护，强行回填会被拒绝或写出矛盾数据。同理也不要删已有默认值，除非用户明确要求覆盖且该字段可编辑。
2. **必填以 `is_required` 为准。** 必填字段缺用户输入又没有默认值时不要编造，用 `AskUserQuestion` 问用户补。
3. **选项字段只认提交值。** `field_metadata` 里带 `options` 的是选项类字段（如 `select_one`/`select_many`），必须写其中的合法 value 而非展示名；用户给的是中文名 / 展示值 / `label` 时先映射成 value，映射不唯一或找不到时先确认，别猜。除接口或对象规则明确要求额外字段外，只写 `form_fields` 中存在且非只读的字段。

### 2.1 对象专属逻辑（命中即先读）

有些对象有超出通用规则的特殊构造逻辑（比如取价、明细处理）。组装前先按下表判断是否需要读引用文件：

| 目标对象 `apiName` | 必须先读的引用文件 |
|---|---|
| `NewOpportunityObj` | `{Current agent directory}/skill/{skillApiName}/references/NewOpportunityObj.md` |
| `QuoteObj` | `{Current agent directory}/skill/{skillApiName}/references/QuoteObj.md` |
| `SaleContractObj` | `{Current agent directory}/skill/{skillApiName}/references/SaleContractObj.md` |
| `SalesOrderObj` | `{Current agent directory}/skill/{skillApiName}/references/SalesOrderObj.md` |
| `BomCoreObj` | `{Current agent directory}/skill/{skillApiName}/references/BomCoreObj.md` |

命中时先读对应文件并应用其约束，再构造 `object_data`。引用文件里的特殊构造逻辑优先于通用规则；但可写字段、必填状态、枚举提交值仍以本次 `get-create-form` 返回为准（引用文件管“怎么算”，表单返回管“能写什么”）。

#### `ActiveRecordObj` / `ScheduleObj` 的 `what_list_type` 赋值逻辑

这两个对象比较常用，规则直接内联在本文件中。目标对象为 `ActiveRecordObj` 或 `ScheduleObj`，且需要填写“关联业务模块”/`related_object`/`what_list` 类型字段时，不要写入 `related_object`，也不要使用 `{ObjectApiName: ["id"]}` 简写；必须同时写入 `related_object_data` 和 `related_api_names`。

- 先按步骤 2.2 的关联对象字段规则解析每条关联记录，取得唯一的关联对象 `apiName`、记录 `id` 和记录 `name`。
- `related_object_data` 写数组；每个元素必须包含 `describe_api_name`、`id`、`name`。
- `related_api_names` 写数组；值来自 `related_object_data[].describe_api_name` 去重后的对象 apiName，保留首次出现顺序。
- 多条同对象记录可同时写入 `related_object_data`；`related_api_names` 中该对象 apiName 只保留一次。
- 任何关联记录未唯一确认前，不得构造、校验或保存 `related_object_data` / `related_api_names`。

示例：

```json
{
  "related_object_data": [
    {
      "describe_api_name": "AccountObj",
      "id": "6a0697de42275d000745a6ba",
      "name": "抚州影视文化公司"
    },
    {
      "describe_api_name": "AccountObj",
      "id": "6a057a8844cdb1000740a08d",
      "name": "小鹏"
    }
  ],
  "related_api_names": [
    "AccountObj"
  ]
}
```

### 2.2 关联对象字段（必须解析到唯一 ID）

关联记录的解析只在这一步做，前提是步骤 1 已返回 `READY`、表单里确实存在这个关联字段。**不要在拿到表单前就抢跑 `query-id-by-name`**：要先在 `form_fields`/`field_metadata` 里确认该字段存在、拿到它的真实 `field_name` 和关联对象 `apiName`，再据此解析。

当字段类型是 `object_reference`，或元数据/对象专属引用表明该字段要关联已有记录时，必须先解析成唯一可提交的记录 ID 再写入。编造一个 ID 会让记录挂到错误的客户/商机上，是最难被发现的脏数据之一。

必填关联字段在用户未提供、或用户明确表示"待定/以后再说/不确定"时，必须停下来用 `AskUserQuestion` 让用户提供或选择，禁止自行用 query-by-fields 等方式列举候选并默认选取（如选最近一条）。没有用户给的关键词就不要发起关联查询。

解析路径：

- 用户直接给了符合字段要求的明确 ID → 可直接用。
- 用户给的是名称/编号/手机号/公司名/联系人名等文本 → **关联对象的 apiName 直接从该字段的 `field_metadata` 里读**（元数据已返回这个字段确认的关联对象 apiName），不必再单独识别对象。拿到关联对象 apiName 后，用批量脚本解析记录 ID（入参是 Map，key 为关联对象 apiName，value 为查询关键词；只有一个关联字段就传一个 key，多个字段一次传多个 key 并发查完）：

  ```
  cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_id_by_name_batch.py --data '{"<关联对象apiName1>":"<关键词1>","<关联对象apiName2>":"<关键词2>"}'
  ```

  当多个关联字段指向**同一个关联对象**（apiName 相同），不能用重复 key（JSON 会互相覆盖），要把 value 写成**关键词数组**，一次查完：

  ```
  cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_id_by_name_batch.py --data '{"<同一关联对象apiName>":["<关键词1>","<关键词2>"]}'
  ```

  该对象下多个关键词的命中会合并进同一个 `name2IdPos`，按 `name` 把记录回填到对应字段。

  返回按对象汇总，每个对象的命中记录在 `name2IdPos` 里（含 `name` 和 `id`）。Map 的 key 用的都是**关联对象**的 apiName，不是当前正在创建的对象。常用关联对象 apiName 速查：人员 `PersonnelObj`、部门 `DepartmentObj`。

  - 查到 1 条 → 可用，并记下记录名称/编号与 ID。
  - 查到多条 → 用 `AskUserQuestion` 让用户选；选定前不要写入任何候选 ID，也不要继续保存。
  - 查不到 / 无法判断 → 停下来，不要编造 ID 或默认选第一条。
  - 用户改了关联条件 → 重新查、重新确认。

### 2.3 各字段类型的写法

| 字段类型 | 写法 | 示例 |
|---|---|---|
| `owner` | 数组 | `{"owner": ["1016"]}` |
| `date` | 日期字符串 `yyyy-MM-dd` | `"close_date": "2026-06-08"` |
| `date_time` | 日期时间字符串 `yyyy-MM-dd HH:mm:ss` | `"meeting_time": "2026-06-08 14:30:00"` |
| `select_one` | 元数据中的合法提交值 | `"sales_stage": "1"` |
| `select_many` | 数组，元素为合法提交值 | `"crm__c": ["Salesforce"]` |
| `percentile` | 提交值是百分号前的数值（可小数），不要换算成 0–1 比例。九折/9折/90% 写 `90`，0.9% 写 `0.9` | `"discount_rate": 90` |
| `rich_text` | 使用纯文本内容，不要写入 HTML 标签或富文本源码；用户给 HTML 时先转成可读纯文本 | `"description": "客户希望下周二沟通方案"` |
| `object_reference` | 唯一命中或用户确认后的记录 ID 字符串 | `"account_id": "69e9a174..."` |
| `record_type` | 步骤 1 已确定的业务类型提交值 | `"record_type": "default__c"` |

## 步骤 3：保存数据

object_data 组装完成后，直接保存——格式校验、必填校验等都交给保存接口负责。

**`sharecrm` 是独立注册的工具（tool），必须直接以工具方式调用，绝不要用 bash/shell 执行，绝不要加 `cd ... &&` 前缀或任何 shell 包裹。** （只有 `scripts/*.py` 这类脚本才需要 `cd` 到 skill 目录后用 bash 跑；`sharecrm ...` 命令本身就是工具调用，原样作为工具输入即可。）

```
sharecrm data record create --data '{"object_api_name": "<apiName>", "object_data": <已构造的 object_data>}'
```

```
sharecrm data record create --data '{"object_api_name": "<apiName>", "object_data": <已构造的 object_data>, "details": <已构造的 details>}'
```

## 步骤 4：返回结果

调用 `create` 后，**先判断接口返回，只有记录确实创建成功时才用 `render_content` 输出**，且成功时不要再附加任何文字总结。

返回不是「创建成功」时（例如系统返回需要二次确认的状态——重复校验/防重提示等，或返回报错），**不要调用 `render_content`**，也不要凭空生成一张「已创建」的结果卡或成功话术：

- **需要二次确认**：把系统要求确认的内容如实转达给用户（用 `AskUserQuestion`），等用户确认后再按系统要求重新提交；只有最终真正创建成功，才走 `render_content`。
- **返回 `User declined to create or update this record.`**：用户已明确拒绝本次创建，**立即终止整个操作**——不重试、不换方式重新提交、不再追问、不渲染结果卡，如实告知用户本次创建已取消即可。
- **返回 `errorCode=EXECUTE_FAILED`（或类似"当前对象不支持执行该操作/无权限/操作被禁止"的错误）**：这类错误表示**操作本身不被允许或不被支持**，不是字段写法问题，**立即终止，绝对不要重试、不要换字段或换参数重新提交**。如实把错误信息告诉用户即可。
- **保存失败 / 报错**：把失败原因如实告诉用户，不要伪装成成功，也不要渲染结果卡。**不要自动反复重试、不要换着花样重复提交。** 仅当错误信息明确指出某个可修正的字段问题（如枚举提交值非法、关联 ID 写错、必填缺失）时，回到对应步骤修正后**至多重试一次**；若重试仍失败、或错误原因不明确/不可由你自行修正（如权限、流程校验、系统异常、`EXECUTE_FAILED`），立即停下来把错误如实告知用户并等待用户指示，禁止继续循环提交。
