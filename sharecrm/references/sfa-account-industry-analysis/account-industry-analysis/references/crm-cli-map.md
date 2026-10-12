# 客户行业分析 CRM CLI Map

本文定义 `account-industry-analysis` 可使用的 CRM 读命令。CRM 字段允许租户自定义，因此本文件只固定对象识别、对象描述、记录查询流程和禁止边界，不固定业务字段 API 名。

## Core Rules

1. CRM 数据只用于补充内部行业锚定、同类样本、成交/输单样本和客户阶段，不替代企业公开行业事实。
2. 先识别对象，再获取对象描述，再基于字段 `label`、类型、选项和关联关系选择字段；不得直接写死字段 API 名。
3. 默认调用范围只限于本文列出的 CRM 读操作；不得调用写操作、表单操作、自动化操作或管理动作。
4. CRM 查询结果可能使用中文 label 作为 key；报告消费时保留业务可读字段名，不展示 SQL、对象 API 名、字段 API 名或内部记录 ID。
5. 查询失败、权限不足、字段缺失或无命中时，不把 CRM 缺失写成客户事实。

## 1. 使用前提

- 必须先完成 `sharecrm auth login` 授权，并确认 `sharecrm auth status` 的 `tokenStatus=normal`。
- 每次查询 CRM 记录前必须先完成对象识别和对象描述。
- 只查询与行业锚定、行业字段归一、同类样本、成交/输单样本有关的字段。
- 不展示对象 API 名、字段 API 名、SQL、内部记录 ID 或敏感字段原值。

## 2. 允许调用命令

| 数据域 | 调用场景 | CLI | 关键入参 | 写入位置 |
|:---|:---|:---|:---|:---|
| 对象识别 | 识别客户、线索、商机、产品、合同、订单等对象 | `sharecrm data describe identify-with-describe` | `query`, `include_simple_describe`, `include_few_shots` | `crmContext` 内部锚定 |
| 对象描述 | 已知对象 API 名时获取字段 label、类型、选项 | `sharecrm data describe get` | `object_api_name`, `simple_describe`, `include_few_shots` | `crmContext.account.fieldBasis`、`crmContext.industryAnchor.fieldBasis` |
| 记录归一 | 用名称找到 CRM 候选客户记录 | `sharecrm data record query-by-name` | `object_api_names`, `name` | `crmContext.account` |
| 明细查询 | 基于对象描述后的受控 SQL 查询 | `sharecrm data record query-by-sql` | `sql`, `need_count` | `crmContext.internalSamples` |
| 聚合查询 | 统计同类客户、商机、合同、订单等内部样本分布 | `sharecrm data record query-aggregate-by-sql` | `sql`, `need_count` | `crmContext.internalSamples` |
| 详情查询 | 已有记录 ID 时补充单条记录上下文 | `sharecrm data record get-by-id` | `object_api_name`, `id` | `crmContext.account`、`crmContext.internalSamples` |
| 关联对象 | 从客户对象探索同类样本、商机、合同、订单等关联对象 | `sharecrm data describe list-related` | `objectApiName` | `crmContext.internalSamples` |
| 关系路径 | 起点对象和目标对象明确但关系链路不清时使用 | `sharecrm data describe query-relation-paths` | `source_object_api_name`, `target_object_api_name`, `question` | 内部查询规划，不直接进入正文 |

## 3. 禁止默认调用

- `create`、`update`、`AllocateAction`、`MoveAction`、`RemoveAction`、`ReturnAction`、`TakeBack` 等写操作或管理动作。
- CRM 产品、订单、合同的全量明细。
- 手机号、邮箱、审批意见、成本、折扣、底价等敏感字段。
- 卖方画像配置读取不属于 CRM map；按 `business-context.md` 使用顶层配置命令。

## 4. 降级规则

| 情况 | 处理 |
|:---|:---|
| CRM 对象识别失败 | 不猜字段；行业锚定降级为公开主营业务和用户上下文 |
| 对象描述失败 | 不查询该对象 |
| 字段不存在 | 寻找 label 语义相近字段；仍无则跳过 |
| 查询无记录 | 不输出该类内部记录 |
| 查询报错或权限不足 | 继续外部行业分析，不编造 CRM 样本 |

查询结果只默认消费首批摘要字段；当 `queryMeta.totalNumber` 大于返回数量或 `limitReached=true` 时，写入 `meta.retrievalCoverage`，不把首批记录当作全量内部样本。
