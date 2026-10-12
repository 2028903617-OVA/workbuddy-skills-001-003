---
name: "data-read"
description: |
  `sharecrm data` 只读命令的最终兜底执行技能（最低优先级），覆盖对象识别、对象/字段描述、关系查看与记录读取。
  自然语言 CRM 查询、语义解析与统计报表优先使用 semantic-interpreter，本技能仅在其不可用、或请求已是包含 apiName 的结构化读取、或已选能力明确要求回退时使用。
  不处理语义解释、统计聚合、报表分析、多跳关系推断及写操作。
apiName: "sharecrm_data_reference"
---
# `sharecrm data` 基础只读操作

## 路由与使用原则

读取本技能不代表允许执行。在调用任何 `sharecrm` 命令前，先完成以下检查：

1. 自然语言 CRM 数据查询默认由 semantic-interpreter 承担；若其在当前技能清单中，优先使用之，不得直接调用下方命令。
2. 只根据当前会话已提供的技能 name 和 description 判断，不逐个加载候选技能试探；存在其他明确覆盖本次请求的查询/分析能力时，改用该能力。
3. 仅当技能清单中无更匹配能力、或已选能力已尝试但明确无法完成、或请求已是包含 apiName 的结构化读取时，才执行下方命令。
4. 仅处理对象识别、对象描述、直接关系查看与记录读取；不执行或发现写操作和 SQL；语义解释、统计聚合、报表分析、多跳关系推断、原因分析均不属于本技能。
5. 使用最短有效调用链，当前结果已经能够回答用户时立即停止。

## 使用原则

1. 仅处理对象识别、对象描述、直接关系查看和记录读取；不执行或发现写操作和 SQL。
2. 只做单步或短链路基础读取；需要多跳拼装、跨记录证据核对或解释性结论时，不属于本技能。
3. 使用最短有效调用链，当前结果已经能够回答用户时立即停止。

## 复用已有上下文

按以下顺序确定对象：

1. 用户当前请求明确提供 `objectApiName` 时，直接使用。
2. 用户只提供业务对象名称时，只有当前对话、已有工具结果或运行时上下文中存在该名称到 `objectApiName` 的精确映射，才直接复用；否则将该名称作为 `identify-with-describe` 的线索，且最多识别一次。
3. 未提供对象信息时，使用用户原始问题调用一次 `identify-with-describe`。

用户当前输入优先于已有上下文。存在多个候选或对象指代无法唯一确定时，向用户澄清，不猜测。

已知 `objectApiName` 时，不再调用 `identify-with-describe`。只有后续查询需要字段信息且现有描述不足时，才调用 `describe get`。已有描述包含所需字段时，不重复获取描述。

## 选择最短命令

| 查询目标 | 命令 |
|---|---|
| 识别业务对象 | `sharecrm data describe identify-with-describe` |
| 获取对象描述 | `sharecrm data describe get` |
| 查看对象关联范围 | `sharecrm data describe list-related` |
| 查询两个对象的关系路径 | `sharecrm data describe query-relation-paths` |
| 按名称查询候选记录 | `sharecrm data record query-by-name` |
| 按名称查询记录 ID | `sharecrm data record query-id-by-name` |
| 按对象和 ID 获取详情 | `sharecrm data record get-by-id` |
| 按字段条件查询记录 | `sharecrm data record query-by-fields` |

前一个命令的结果已经能够回答用户时，不调用后续命令。

## 对象描述与关系

对象无法从已有上下文确定时，使用用户原始问题识别对象。对象已知但缺少下一步所需字段信息时，获取简版描述。

```bash
sharecrm data describe identify-with-describe --query "<用户原始问题>" --include_simple_describe true
sharecrm data describe get --object_api_name <ObjectApiName> --simple_describe true
sharecrm data describe list-related --objectApiName <ObjectApiName>
sharecrm data describe query-relation-paths --source_object_api_name <SourceObjectApiName> --target_object_api_name <TargetObjectApiName> --question "<用户原始问题>"
```

## 记录读取

按名称查询记录时，优先传入已经确认的对象范围。对象范围未知时，先识别对象。

```bash
sharecrm data record query-by-name --data '{"name":"<记录名称>","object_api_names":["<ObjectApiName>"]}'
sharecrm data record query-id-by-name --data '{"apiNames":["<ObjectApiName>"],"query":"<名称关键词>"}'
sharecrm data record get-by-id --object_api_name <ObjectApiName> --id <记录ID>
```

`query-by-name` 返回的信息已经能够回答用户时，不再调用 `get-by-id`。只需要记录 ID 时，使用 `query-id-by-name`。

## 按字段条件查询

字段名称必须来自已有对象描述的 `field_list[].api_name`。只选择用户需要的字段，并设置较小且合理的 `limit`（建议默认 10）。

```text
text: eq/n/like/in
number/date/datetime: eq/n/gt/gte/lt/lte/between/in
boolean: eq/n
array: in
```

`n` 表示不等于。`in` 使用逗号分隔多个值，`between` 按“起始值,结束值”传入。多个字段条件默认使用 AND。

```bash
sharecrm data record query-by-fields --object_api_name <ObjectApiName> --select_fields <field1,field2> [--<field>-<operator> <value>] [--sort <field:asc|desc>] [--limit <数量>] [--offset <偏移量>] [--need_count true]
sharecrm data record query-by-fields --object_api_name AccountObj --select_fields name,owner --name-like 华为 --limit 10
```

关联对象、人员和部门字段应先解析为可用 ID。枚举字段值必须来自对象描述中的合法选项。

## Help 与错误处理

正文已经提供所需参数时，直接执行命令，不预先调用 `--help`。

只有目标命令返回未知参数、不支持的格式或运行时版本不兼容错误时，才查看该目标命令的 `--help`。不得查看根命令或父命令 help 来枚举其他能力。

查询成功但没有结果时，报告空结果并停止。不得放宽条件、更换对象、扩大时间范围或为了探索而重试。命令执行失败时，只针对明确错误修正参数，不得盲目重试。
