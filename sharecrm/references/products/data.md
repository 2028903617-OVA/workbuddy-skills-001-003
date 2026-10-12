---
name: sharecrm-data
version: 2.0.0
description: "sharecrm 对象数据处理：对象数据查询（QueryRecords）、对象数据聚合（QueryRecordsWithAggregate）、对象数据创建/维护（CreateRecords）、对象识别（IdentifyObject）、按名称查ID（QueryRecordIdByName）。当用户需要查询/创建/更新 CRM 对象数据时触发。"
metadata:
  requires:
    bins: ["sharecrm"]
  cliHelp: "sharecrm data -h"
---

# sharecrm 对象数据处理

本技能指导你如何通过 sharecrm 操作纷享 CRM 对象数据，包括查询、聚合统计、创建/维护和对象识别。

## 前置条件

- 已通过 `sharecrm auth login` 完成登录授权
- **CRITICAL — 开始前 MUST 先用 Read 工具读取 [`userAuth.md`](../userAuth.md)，其中包含登录授权、身份认证**
- 登录用户具有对应数据操作的权限 scope

## 查看可用命令

```bash
# 查看 data 命令组下所有子命令
sharecrm data -h

# 查看具体子命令的帮助
sharecrm help data QueryRecords
```

## 子命令一览

### QueryRecords — 对象数据查询

根据用户请求和特定条件查找和检索 CRM 对象数据，自动识别正确的对象类型或对象数据记录。也支持聚合查询（如有多少、总和、最大值、最小值、平均值）。

```bash
sharecrm data QueryRecords -d '{"userInput":"查找过去 5 天内创建的所有商机"}'
sharecrm data QueryRecords --data '{"userInput":"查找过去 5 天内创建的所有商机"}'
sharecrm data QueryRecords '{"userInput":"查找客户A下所有未成交的商机"}'
```

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `userInput` | string | 是 | 用户输入的问题或请求，需提及对象类型（如客户、线索、联系人、商机等） |

### QueryRecordsWithAggregate — 对象数据聚合查询

专门回答 CRM 数据的聚合问题：计数、总和、最大值、最小值或平均值。

```bash
sharecrm data QueryRecordsWithAggregate -d '{"userInput":"客户 A 下已成交的商机总金额有多少"}'
```

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `userInput` | string | 是 | 用户输入的聚合问题，需提及对象类型或对象数据记录 |

### CreateRecords — 对象数据创建与维护

用于 CRM 主对象及明细数据的录入与维护（含增删改）：

- **新建对象**：必须先执行 `IdentifyObject` 确定对象 ApiName
- **修改/补充**：从历史消息获取 `master_object_api_name`，无需再次识别

```bash
sharecrm data CreateRecords -d '{
  "master_object_api_name": "AccountObj",
  "user_input": "创建一个新的客户对象，名称为客户A",
  "is_refinement": false
}'
```

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `master_object_api_name` | string | 是 | 对象的 ApiName，指定要操作的对象 |
| `user_input` | string | 是 | 自然语言内容，用于提取字段值 |
| `previous_full_data` | object | 否 | 多轮对话场景下，上一次返回的完整对象数据 |
| `is_refinement` | boolean | 否 | 是否为修改/纠错/补充意图，新建或 `previous_full_data` 为空时设为 false |

**使用流程：**

1. 首次创建时，先执行 `IdentifyObject` 获取对象 ApiName
2. 将 ApiName 作为 `master_object_api_name` 传入 `CreateRecords`
3. 多轮修改时，将上一次返回的 `previous_full_data` 回传

### IdentifyObject — 识别对象名称

从用户输入中提取对象名称，并匹配对应的对象 API 名称。返回三种结果：

| `resultType` | 含义 | 处理方式 |
|---|---|---|
| `singleObject` | 精确匹配 | 直接使用 `suggestObject` 作为目标对象 ApiName |
| `multiObject` | 模糊匹配 | 返回多个候选项，**必须**向用户展示并等待选择后继续 |
| `noneObject` | 未命中 | 告知用户无法识别，引导确认名称或手动输入 |

```bash
sharecrm data IdentifyObject -d '{"objectName":"客户","currentObjectApiName":""}'
```

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `objectName` | string | 是 | 用户输入中提及的对象名称 |
| `currentObjectApiName` | string | 是 | 用户当前操作对象的 ApiName（从上下文获取），无则传空字符串 |

### QueryRecordIdByName — 按名称查询对象 ID

根据名称查询纷享对象数据，返回对象数据的 ID 列表。

```bash
sharecrm data QueryRecordIdByName -d '{"query":"客户A"}'
```

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `query` | string | 是 | 要查询的对象数据名称或标题 |
| `apiNames` | array | 否 | 要查询的对象 ApiName 列表；不传则默认查询客户、商机、联系人、产品、部门、人员 |

## 调用方式总结

远程命令的标准调用方式：

```bash
# 方式一：使用 -d / --data 传入 JSON
sharecrm data <子命令> -d '{"key":"value"}'

# 方式二：将 JSON 放在命令最后一个参数
sharecrm data <子命令> '{"key":"value"}'
```

**参数规则：**
- `-d` 与 `--data` 等价
- 如果最后一个参数看起来像 JSON（`{...}` 或 `[...]`），会被识别为请求参数
- 如果都没有提供，则默认使用 `{}`

## 典型使用流程

### 创建一条新的 CRM 记录

```
1. sharecrm data IdentifyObject -d '{"objectName":"客户","currentObjectApiName":""}'
   → 返回 resultType=singleObject, suggestObject="Account__c"

2. sharecrm data CreateRecords -d '{
     "master_object_api_name": "Account__c",
     "user_input": "名称为客户A，行业为互联网",
     "is_refinement": false
   }'
   → 返回创建结果
```

### 查询 CRM 对象数据

```
sharecrm data QueryRecords -d '{"userInput":"查找客户A下所有未成交的商机"}'
→ 返回匹配的商机列表
```

## 输出格式

命令执行结果的格式由服务端决定：

| `outputType` | 输出格式 |
|---|---|
| `json` | 格式化 JSON 输出 |
| `text` / `markdown` | 纯文本直接输出；对象以 JSON 形式展示 |
| 其他 | 对象以格式化 JSON 输出，字符串直接输出 |

## 错误处理

### 权限不足

错误响应中包含 `permission_violations`（缺失的权限 scope）和 `console_url`（后台配置链接）。将链接提供给用户，引导去开发者后台开通对应权限。

### 参数错误

```
执行命令：sharecrm data QueryRecords
错误编码：INVALID_ARGUMENT
错误原因：<具体原因>
执行命令：sharecrm data QueryRecords --help 查看命令帮助信息
```

### 认证失败
当 sharecrm 命令输出包含以下任一内容时，表示认证失败：

```
登录状态已失效，请重新登录授权。
```
或
```
You must login before executing remote commands.
```

**处理流程（MUST 严格执行）：**

1. 执行 `sharecrm auth login` 完成重新登录
2. 登录成功后，**自动重试之前失败的命令**，无需用户再次请求
3. 将重试结果返回给用户

## 调试

使用 `--debug` 查看远程请求和响应的详细信息：

```bash
sharecrm --debug data QueryRecords -d '{"userInput":"test"}'
```

- `--debug` 是全局参数，建议放在命令前面
- 正常结果输出到 `stdout`，调试信息输出到 `stderr`



## 详细参考 (按需读取)

- [登录认证](../userAuth.md) — 全局标志、认证、输出格式
- [纷享CRM对象清单](../objectApiNames.md) — CRM对象/数据对象 API 名称