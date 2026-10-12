# CRM 行业锚定手册

本文定义如何从 CRM 中锚定目标客户的行业、赛道和区域。

## 1. 先识别对象，再读字段

执行要求：

1. 先识别客户对象。
2. 再读取对象描述。
3. 再根据字段 label、类型、选项和关联关系理解行业字段。
4. 再查询客户记录。

不得跳过对象描述直接假设行业字段 API 名。

## 2. CRM 读取顺序

本规则复用原始 `sfa-industry-analysis` 中的有效 CRM 锚定思路：先对象识别，再对象描述，再记录查询，再行业归一。运行时命令以当前平台实际 CLI 帮助为准，不硬编码租户字段。

### 2.1 对象识别

目标是确认用户输入对应哪个 CRM 对象和记录。

候选对象优先级：

1. 客户对象，例如 `AccountObj`。
2. 线索对象，例如 `LeadsObj`，仅在用户输入明显是线索或客户对象无命中时使用。
3. 商机对象，例如 `NewOpportunityObj`，仅用于辅助识别关联客户，不作为行业锚定主对象。

参考命令形态：

```bash
sharecrm data describe identify-with-describe --data '{"query":"<客户名或业务短语>","object_api_names":["AccountObj","LeadsObj","NewOpportunityObj"],"include_few_shots":false}'
```

处理规则：

- 唯一命中客户对象时，继续读取对象描述和记录。
- 多候选时，返回候选主体要求用户确认，不猜。
- 只命中商机或线索时，必须回到关联客户主体做行业锚定。
- 无命中时，允许使用公开资料降级，但 `crmContext.industryAnchor.anchorStatus` 标为 `user_provided` 或 `inferred`。

### 2.2 对象描述

目标是确认当前租户真实字段 label、类型、选项和关联关系。

参考命令形态：

```bash
sharecrm data describe get --data '{"object_api_name":"AccountObj","simple_describe":true}'
```

使用规则：

- 只在内部使用对象 API 名和字段 API 名。
- 输出正文只展示字段业务含义，不展示对象 API 名、字段 API 名或内部记录 ID。
- 字段不可见时，记录为字段权限不足，不绕过权限。

### 2.3 名称转 CRM 记录

目标是用客户名称找到唯一 CRM 记录。

参考命令形态：

```bash
sharecrm data record query-by-name --data '{"object_api_name":"AccountObj","name":"<客户名>"}'
```

处理规则：

- 唯一命中：取该客户记录。
- 多个候选：要求用户确认，不做完整行业结论。
- 无命中：标注“客户未在 CRM 命中，行业未经 CRM 确认”，进入降级。

### 2.4 读取客户完整记录

目标是取得行业、赛道、区域、分层、集团关系等锚定字段。

参考命令形态：

```bash
sharecrm data record get-by-id --data '{"object_api_name":"AccountObj","id":"<account_id>"}'
```

读取后写入：

- 独立模式：`standalone-report-data-model.md` 的 `crmContext.industryAnchor`。
- 编排模式：`insight-data-model.md` 的 `targetCustomer` 和行业相关字段。

## 3. 行业字段候选方向

运行时优先寻找：

- 所属行业
- 行业分类
- 行业一级/二级
- 赛道
- 区域
- 客户分层

字段名和字段 API 以当前租户真实对象描述为准。

## 4. 锚定规则

- 客户唯一命中时，以 CRM 行业字段为主依据。
- 行业字段为空或不清晰时，可结合公开主营业务和区域做推断，并标注 `inferred`。
- 用户给出的行业名与 CRM 冲突时，以 CRM 为准，并在待核实说明差异。
- 客户无法在 CRM 唯一确认时，不得伪装为已完成 CRM 锚定。

## 5. 行业名归一

CRM 行业字段可能是枚举码、层级值、标签或多选字段。归一规则：

1. 先根据对象描述中的 label、选项和层级关系转成可读行业名。
2. 再结合客户主营业务、经营模式、区域、规模和上下游位置做多维识别。
3. 命中行业模板时，写入 `industryContext.templateContext.templateName`。
4. 未命中模板时，走通用口径，并在 `gaps` 中标注该行业未建个性化模板。

不得只凭一个行业字段值直接输出完整行业判断。

## 6. 内部样本查询

在权限允许时，可查询：

- 同行业客户。
- 同行业历史成交或输单样本。
- 与该客户相关的商机、订单、合同和销售记录。

用途：

- 解释客户行业位置。
- 补充行业影响的内部样本。
- 判断哪些行业变化与客户经营有关。

参考查询方向：

```bash
sharecrm data record query-by-fields --data '{"object_api_name":"AccountObj","select_fields":["_id","name","<行业字段>"],"search_template_query":{"filters":[{"field_api_name":"<行业字段>","operator":"EQ","value":"<行业值>"}],"limit":20},"need_count":true}'
```

商机、合同、订单、活动等对象必须先 `describe get`，再依据真实 label 判断业务含义。不得假设 `sales_status`、`sales_stage`、`lost_reason`、`amount`、`close_date` 等字段一定存在。

内部样本写入规则：

- 同行业客户样本写入 `crmContext.internalSamples`。
- 该客户相关商机、订单、合同和活动仅写业务摘要，不输出敏感字段原值。
- 客户原话、会议纪要、客户声音等可作为高价值证据，但正文必须脱敏。
- 样本不足时，不输出强归因判断，只进入 `gaps`。

## 7. 能力降级

| 情况 | 处理 |
|:---|:---|
| `describe` 不可用 | 标 `crmContext.industryAnchor.anchorStatus=inferred`，行业锚定降级为公开资料或用户输入 |
| 客户名称无命中 | 标“客户未在 CRM 命中”，不伪装为 CRM 已确认 |
| 多候选 | 要求用户确认主体，不输出完整行业结论 |
| 行业字段为空 | 结合公开主营业务推断，标 `inferred` |
| 字段权限不足 | 记录权限缺口，不绕过权限 |
| 内部样本不足 | 不输出强样本判断，只说明样本不足 |

快速检索未命中不等于 CRM 未覆盖；必须完成对象识别、对象描述和记录查询后，才能说明当前 CRM 证据不足。

## 8. 边界

- 不输出对象 API 名。
- 不输出内部记录 ID。
- 不输出敏感字段原值。
- 快速检索未命中不等于 CRM 未覆盖。
