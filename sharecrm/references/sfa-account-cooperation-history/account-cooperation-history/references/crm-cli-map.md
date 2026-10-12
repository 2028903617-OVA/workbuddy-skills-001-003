# 客户合作历史分析 CRM CLI Map

本文定义 `account-cooperation-history` 可使用的 CRM 读命令。CRM 字段允许租户自定义，因此本文件只固定对象识别、对象描述、记录查询流程和禁止边界，不固定业务字段 API 名。

## Core Rules

1. CRM 数据只用于补充内部接触、商机、合同、订单、回款、活动和失败原因，不替代外部公开合作事实。
2. 先识别对象，再获取对象描述，再基于字段 `label`、类型、选项和关联关系选择字段；不得直接写死字段 API 名。
3. 默认调用范围只限于本文列出的 CRM 读操作；不得调用写操作、表单操作、自动化操作或管理动作。
4. CRM 查询结果可能使用中文 label 作为 key；报告消费时保留业务可读字段名，不展示 SQL、对象 API 名、字段 API 名或内部记录 ID。
5. 查询失败、权限不足、字段缺失或无命中时，不把 CRM 缺失写成客户事实。

## 1. 使用前提

- 必须先完成 `sharecrm auth login` 授权，并确认 `sharecrm auth status` 的 `tokenStatus=normal`。
- 每次查询 CRM 记录前必须先完成对象识别和对象描述。
- 只查询与内部接触、商机、合同、订单、回款、活动、失败原因有关的字段。
- 不展示对象 API 名、字段 API 名、SQL、内部记录 ID 或敏感字段原值。

## 2. 允许调用命令

| 数据域 | 调用场景 | CLI | 关键入参 | 写入位置 |
|:---|:---|:---|:---|:---|
| 对象识别 | 识别客户、联系人、商机、合同、订单、回款、活动对象 | `sharecrm data describe identify-with-describe` | `query`, `include_simple_describe`, `include_few_shots` | `crmContext` |
| 对象描述 | 获取字段 label、类型、选项和关联关系 | `sharecrm data describe get` | `object_api_name`, `simple_describe`, `include_few_shots` | `crmContext.account.fieldBasis` |
| 名称归一 | 用客户名称找 CRM 候选记录 | `sharecrm data record query-by-name` | `object_api_names`, `name` | `crmContext.account` |
| 明细查询 | 查询联系人、活动、商机、合同、订单、回款和失败原因摘要 | `sharecrm data record query-by-sql` | `sql`, `need_count` | `crmContext.*`、`cooperationContext.internalHistory` |
| 聚合查询 | 统计商机、合同、订单、回款、活动数量或状态分布 | `sharecrm data record query-aggregate-by-sql` | `sql`, `need_count` | `cooperationContext.internalHistory` |
| 详情查询 | 已有记录 ID 时补充业务摘要 | `sharecrm data record get-by-id` | `object_api_name`, `id` | `cooperationContext.internalHistory` |
| 关联对象 | 从客户对象探索联系人、商机、合同、订单、活动、回款等关联对象 | `sharecrm data describe list-related` | `objectApiName` | 内部查询规划 |
| 关系路径 | 起点对象和目标对象关系不清时使用 | `sharecrm data describe query-relation-paths` | `source_object_api_name`, `target_object_api_name`, `question` | 内部查询规划 |

## 3. 关键写入规则

- CRM 内部历史只写业务摘要，例如历史接触、商机阶段、合同/订单状态、回款背景、失败原因。
- 内部记录进入 `cooperationContext.internalHistory` 前必须解释其对当前合作判断的影响。
- 与发问方业务相关的客户侧合作信号写入 `sellerRelevantSignals`，不展示卖方画像原文。

## 4. 禁止默认调用

- `data record create/update` 和所有 CRM 写操作。
- 销售分配、转移、退回、公海、领取、收回等管理动作。
- 联系人手机号、邮箱、内部备注、审批意见、折扣、成本等敏感字段。

## 5. 降级规则

| 情况 | 处理 |
|:---|:---|
| CRM 无命中或权限不足 | 不输出内部历史接触结论；公开合作分析继续 |
| 对象识别失败 | 不猜对象；跳过该类 CRM 记录 |
| 对象描述失败 | 不查询该对象 |
| 字段不存在 | 寻找 label 语义相近字段；仍无则跳过 |
| 查询无记录 | 不输出该类内部记录 |

查询结果只默认消费首批摘要字段；当 `queryMeta.totalNumber` 大于返回数量或 `limitReached=true` 时，写入 `meta.retrievalCoverage`，不把首批记录当作全量内部历史。
