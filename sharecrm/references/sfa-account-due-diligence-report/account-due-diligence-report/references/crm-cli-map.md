# CRM 对象查询 Map

本文定义客户尽调报告中 CRM 内部记录的查询规则。CRM 字段允许租户自定义，因此本文件只固定实际 CLI、对象识别、对象描述、查询流程、返回结构和预设对象范围，不固定业务字段 API 名。

## Core Rules

1. CRM 数据用于补充内部客户阶段、负责人、联系人、商机、合同/订单、回款、销售记录和历史合作，不替代企业工商事实。
2. 先识别对象，再获取对象描述，再基于字段 label、类型、选项和关联关系选择字段；不得直接写死字段 API 名。
3. 预设对象是第一版默认范围；自定义对象不做全量扫描。
4. 只有用户明确提到某类内部数据，或预设对象不足以解释合作历史时，才探索自定义对象或其他关联对象。
5. 查询失败、权限不足或字段缺失不中止报告；不能把 CRM 缺失写成客户事实。
6. CRM 记录进入报告时只输出业务含义，不输出敏感字段原值和无关内部字段。
7. 生成报告不得自动创建、更新、删除 CRM 数据。
8. 默认调用范围只限于本文列出的 CRM 读操作 CLI；未列入本文的 CRM 写操作、表单操作或自动化操作不得调用。

## Allowed CRM Read CLI

| 场景 | CLI | 关键入参 |
|:---|:---|:---|
| 识别对象并获取简版描述 | `sharecrm data describe identify-with-describe` | `query`, `include_simple_describe`, `include_few_shots` |
| 已知对象 API 名时获取对象描述 | `sharecrm data describe get` | `object_api_name`, `simple_describe`, `include_few_shots` |
| 按名称归一到候选记录 | `sharecrm data record query-by-name` | `object_api_names`, `name` |
| 执行受控 SQL 明细查询 | `sharecrm data record query-by-sql` | `sql`, `need_count` |
| 执行受控 SQL 聚合查询 | `sharecrm data record query-aggregate-by-sql` | `sql`, `need_count` |
| 已有记录 ID 时获取单条详情 | `sharecrm data record get-by-id` | `object_api_name`, `id` |
| 获取对象直接关联对象 | `sharecrm data describe list-related` | `objectApiName` |
| 查询两个对象之间关系路径 | `sharecrm data describe query-relation-paths` | `source_object_api_name`, `target_object_api_name`, `question` |

## 查询流程

### 1. 识别对象

优先用对象中文名识别对象 API 名：

```text
sharecrm data describe identify-with-describe --data '{"query":"<对象中文名或业务短语>","include_simple_describe":true,"include_few_shots":false}'
```

识别结果处理：

| 结果 | 处理 |
|:---|:---|
| `resolution_status` 表示已唯一收敛 | 使用 `object_candidates[].object_api_name`，并消费 `simple_describe` 中的字段描述 |
| 多候选或未收敛 | 只在用户语义明确时选择；否则不要继续查 |
| 无候选 | 不猜测对象；可从已确认主对象出发查询关联对象 |

### 2. 获取对象描述

对每个要查询的对象，先获取当前租户下真实字段：

```text
sharecrm data describe get --data '{"object_api_name":"<ObjectApiName>","simple_describe":true,"include_few_shots":false}'
```

消费字段描述时关注：

- `api_name`：查询用字段名。
- `label`：业务含义主依据。
- `data_type`：字段类型，如文本、日期、金额、人员、关联对象、单选、多选。
- `options`：选项值及含义。
- `target_api_name`：关联对象。
- `target_object_label`：关联对象中文名。
- `parent_group_api_name`、`field_refs`：组合字段和子字段关系。
- `sortable`、`filterable`：用于判断是否可排序、过滤。

示例字段只能作为语义候选，不能作为硬编码契约。若字段不存在，应寻找 label 语义相近字段；仍找不到则跳过该判断。

### 3. 查询记录

优先使用已确认对象和字段构造受控查询：

```text
sharecrm data record query-by-sql --data '{"sql":"SELECT <已确认字段> FROM <ObjectApiName> WHERE ... LIMIT <n>","need_count":true}'
```

只查询对象描述中真实存在的字段。避免 `SELECT *`，避免把公司名、产品名、人名等自然语言值直接当作关联字段 ID。

字段选择必须先读对象描述，再按业务问题从 `field_list` 中挑选。除 `_id`、名称类字段等识别字段外，不预设固定字段清单；用户可能在预设对象上增加自定义字段，若自定义字段 label 能解释客户阶段、业务状态、合作历史、风险、产品、服务、回款、组织覆盖等报告问题，可以纳入查询。

默认优先选择摘要判断所需字段，避免拉取非必要字段：

- 客户对象：优先选择名称、负责人、分配/公海状态、客户阶段/级别、成交状态、最后跟进、最后成交、行业、区域等 label 相关字段。
- 联系人对象：优先判断是否有覆盖、部门、职务、角色等，不查询或输出手机号、邮箱等联系方式原值。
- 商机对象：优先选择阶段、金额、预计成交时间、输赢状态、关联客户、负责人等 label 相关字段。
- 合同、订单、回款对象：优先选择状态、金额、时间、产品/服务摘要、关联客户等 label 相关字段。
- 销售记录/活动对象：优先选择互动时间、互动类型、摘要、负责人等 label 相关字段。

label 不清楚、字段含义无法支撑报告判断、字段明显敏感或仅为系统技术字段时，默认不查询；确需查询详情时，先用明细 SQL 拉取少量摘要字段，再按记录 ID 获取单条详情。

如果需要总数、求和、平均、分组等聚合口径，使用聚合查询：

```text
sharecrm data record query-aggregate-by-sql --data '{"sql":"SELECT COUNT(_id) FROM <ObjectApiName>","need_count":false}'
```

如果已取得记录 ID，可查询详情：

```text
sharecrm data record get-by-id --data '{"object_api_name":"<ObjectApiName>","id":"<recordId>"}'
```

名称归一工具可作为辅助通道，但不能作为唯一通道；失败时应回到对象描述驱动的 SQL 或明确的关联关系查询：

```text
sharecrm data record query-by-name --data '{"object_api_names":["<ObjectApiName>"],"name":"<名称>"}'
```

### 4. 解释业务含义

根据字段 label、字段类型、选项值和对象关系解释业务含义，例如：

- label 表示负责人、所属公海、客户阶段、成交状态、最后跟进时间时，用于判断内部覆盖状态。
- 商机对象中的阶段、金额、预计成交时间、输赢状态等字段，用于判断是否已有业务推进。
- 联系人对象中的职务、角色、部门、联系方式等字段，用于判断联系人覆盖情况，但不输出隐私细节。
- 销售合同/销售订单中的金额、产品、周期、状态等字段，用于判断历史合作。
- 回款和回款计划用于判断履约、回款和账期相关背景。
- 销售记录用于判断近期互动活跃度。

## CRM 取数覆盖策略

CRM 记录首次获取也采用时间窗优先策略。先根据对象语义和用户场景确定默认时间窗、状态筛选和排序，再获取首批记录。`LIMIT` 和分页参数只是执行控制，不代表业务覆盖范围。

默认策略：

| 数据域 | 默认时间窗 | 首次获取优先级 |
|:---|:---|:---|
| 商机/跟进 | 当前未关闭商机 + 近 12-24 个月历史商机/互动 | 当前推进、最近互动、金额较大、输赢状态明确 |
| 合同/订单/回款 | 近 24-36 个月 | 最近成交、金额较大、未回款/逾期、产品/服务摘要 |
| 联系人覆盖 | 当前有效记录优先 | 部门、职务、角色、覆盖数量；不输出联系方式原值 |
| 销售记录/活动 | 近 6-12 个月 | 最近互动、互动类型、摘要、负责人 |

如果首批不足以判断历史合作、当前推进、回款或联系人覆盖，应优先使用聚合、状态筛选、时间筛选或关键记录查询补充，不机械翻页。

补充查询示例方向：

- 当前推进：未关闭商机、关键阶段、预计成交时间、负责人。
- 历史输赢：近 12-24 个月已关闭商机的输赢状态、金额区间、原因摘要。
- 历史成交：近 24-36 个月合同/订单的状态、产品或服务摘要、时间和金额区间。
- 回款风险：未回款、逾期、回款计划异常等摘要。

当 `queryMeta.totalNumber` 大于返回数量或 `limitReached=true` 时，把覆盖范围写入 `meta.retrievalCoverage`，不要把首批记录当作全量结论。

## 卖方画像降级查询

当 `seller-context-rules.md` 中的 `service_models` 配置为空、不可用或不足以判断发问方服务形态时，可把 CRM 产品/服务对象和已成交合同/订单作为卖方画像降级来源。

执行要求：

- 先用 `sharecrm data describe identify-with-describe` 识别"产品"、"商品"、"服务"、"产品线"等对象语义；不假设固定对象 API 名。
- 识别成功后必须获取对象描述，再按字段 label 选择产品线、产品分类、服务类型、有效状态等摘要字段。
- 已成交合同/订单只消费近 12-24 个月成交产品/服务类型、服务形态、客户行业分布等聚合或摘要。
- 只进入 `sellerContext.summaryForInternalReasoning`，不进入客户报告正文。

禁止：

- 查询或展示产品、订单、合同的全量明细。
- 展示客户名称、成交金额、折扣、成本、合同条款、审批意见等敏感信息。
- 将历史成交记录写成当前战略、当前主推产品或确定销售动作。

## 预设对象范围

| 业务域 | 优先对象 | 已知对象 API 名 | 关联字段口径 | 报告消费位置 |
|:---|:---|:---|:---|:---|
| 客户档案 | 客户 | `AccountObj` | 主体对象 | CRM 内部记录、客户阶段 |
| 联系人 | 联系人 | `ContactObj` | 通常通过 `account_id` 关联客户 | 联系人覆盖、内部接触 |
| 商机 | 商机 | `NewOpportunityObj` | 通常通过 `account_id` 关联客户 | 当前推进、历史输赢 |
| 销售合同 | 销售合同 | `SaleContractObj` | 通常通过 `account_id` 关联客户 | 历史成交、合作周期 |
| 销售订单 | 销售订单 | `SalesOrderObj` | 通常通过 `account_id` 关联客户 | 历史订单、产品和金额 |
| 回款 | 回款 | `PaymentObj` | 通常通过 `account_id` 关联客户 | 回款、账期、履约背景 |
| 回款计划 | 回款计划 | `PaymentPlanObj` | 通常通过 `account_id` 关联客户 | 未来回款安排 |
| 销售记录 | 销售记录/拜访 | `ActiveRecordObj` | 通常通过 `account_id` 关联客户 | 近期互动、跟进活跃度 |

可选关联对象：销售线索 `LeadsObj`、报价单 `QuoteObj`、开票申请 `InvoiceApplicationObj`、需求 `RequirementObj`、客户画像 `ProfileObj`。只有用户明确关注或报告需要解释对应事实时才查询。

## 关联对象探索

当预设对象不足以覆盖用户问题时，从客户对象出发查询关联对象：

```text
sharecrm data describe list-related --data '{"objectApiName":"AccountObj"}'
```

只选择与报告问题相关的关联对象。不要扫描所有关联对象。选择前应看：

- `objectLabel` 和 `relatedListLabel` 是否与用户问题直接相关。
- `relationFieldApiName` 是否能从客户记录关联过去。
- 该对象是否包含可解释客户阶段、合作历史、风险或内部覆盖的字段。

如果已经确定起点对象和目标对象，但不确定关系链路，可查询关系路径：

```text
sharecrm data describe query-relation-paths --data '{"source_object_api_name":"<SourceObjectApiName>","target_object_api_name":"<TargetObjectApiName>","question":"<查询目的>"}'
```

只选择能解释当前报告问题的最短、最清晰链路；不要因为存在关系路径就扩展查询无关对象。

## Return Structure Notes

### 对象识别与描述

`sharecrm data describe identify-with-describe` 通常返回：

- `object_candidates`：候选对象数组，每项包含 `object_api_name`、`object_name`。
- `resolution_status`：对象识别状态。
- `message`：识别说明。
- `simple_describe`：当请求简版描述且对象收敛时返回，结构同对象描述。

`sharecrm data describe get` 通常返回：

- `api_name`、`display_name`、`object_alias_name`、`base_description`、`extended_description`。
- `field_list`：字段数组，每项通常包含 `api_name`、`data_type`、`label`、`type`、`options`、`target_api_name`、`target_object_label`、`parent_group_api_name`、`field_refs`、`sortable`、`filterable` 等。

字段清单来自当前租户配置，不能把某次返回字段当成所有租户固定字段。

### 记录查询

`sharecrm data record query-by-sql` 明细查询通常返回：

- `queryMode`。
- `queryMeta`：包含 `totalNumber`、`requestedLimit`、`returnedCount`、`limitReached`、`appliedLimit` 等。
- `recordResult`：记录数组。

注意：`recordResult` 中返回字段可能使用中文 label 作为 key，即使 SQL 中使用的是 API 字段名。报告消费时应按中文 label 和对象描述解释业务含义，不向用户暴露原始 SQL 或无关 API 字段。

`sharecrm data record query-aggregate-by-sql` 聚合查询通常返回：

- `queryMode`。
- `aggregateResult.rows`：聚合结果数组。
- `queryMeta`：返回数量、limit 等元信息。

`sharecrm data record query-by-name` 通常返回：

- `records`。
- `resolution_status`。
- `record_candidates`。
- `message`。

无命中时通常返回空数组；只能说明该名称归一接口未命中，不能推断 CRM 中一定不存在相关记录。

`sharecrm data record get-by-id` 通常返回：

- `record`：单条记录详情。

详情记录也可能使用中文 label 作为 key，且可能包含当前权限下可见的较多字段。报告只消费与客户判断有关的字段，避免输出内部备注、敏感个人信息、折扣、成本、审批意见等。

查询结果只默认消费首批明细；当 `queryMeta.totalNumber` 大于 `recordResult.length` 或 `limitReached=true` 时，不推断为全量记录。报告中如需说明，应使用业务语言表达"本次基于首批记录判断，非全部明细"。

### 关联关系

`sharecrm data describe list-related` 通常返回：

- `relatedObjects`：关联对象数组，每项包含 `objectApiName`、`objectLabel`、`relatedListName`、`relatedListLabel`、`relationFieldApiName`、`relationFieldLabel`、`relationFieldType` 等。

`sharecrm data describe query-relation-paths` 通常返回：

- `meta`：包含起点对象、目标对象、返回路径数量、是否截断等。
- `paths`：候选路径数组。
- `issues`：问题或提示数组。

## Raw Output Examples

以下示例只用于帮助后续维护者理解真实返回结构。CRM 字段受租户配置影响很大，示例只能作为“结构参考”和“字段语义候选”，不能写死到查询契约里。

### 示例 1：对象描述 `data describe get`

实测：

```text
sharecrm data describe get --data '{"object_api_name":"AccountObj","simple_describe":true,"include_few_shots":false}'
```

可返回如下结构：

```json
{
  "api_name": "AccountObj",
  "display_name": "客户",
  "field_list": [
    {
      "api_name": "account_type",
      "label": "客户类型",
      "data_type": "select_one"
    },
    {
      "api_name": "account_no",
      "label": "客户编号",
      "data_type": "auto_number"
    },
    {
      "api_name": "province",
      "label": "省",
      "data_type": "province"
    },
    {
      "api_name": "tel",
      "label": "电话",
      "data_type": "phone_number"
    }
  ]
}
```

消费建议：

- 先用 `display_name` 和 `field_list[*].label` 理解业务语义，再决定查什么。
- 类似 `tel` 这种敏感字段即使存在，也不默认进入报告正文。
- 同一租户下 `AccountObj` 可能有几十到上百个字段，实际查询只选与问题相关的少量字段。

### 示例 2：明细查询 `query-by-sql`

常见返回结构通常为：

```json
{
  "queryMode": "sql",
  "queryMeta": {
    "totalNumber": 38,
    "requestedLimit": 10,
    "returnedCount": 10,
    "limitReached": true,
    "appliedLimit": 10
  },
  "recordResult": [
    {
      "客户名称": "某客户",
      "负责人": "某负责人",
      "客户阶段": "已成交"
    }
  ]
}
```

消费建议：

- `recordResult` 的 key 可能是中文 label，不要强行按 SQL 里的 API 字段名消费。
- `queryMeta.totalNumber > returnedCount` 或 `limitReached=true` 时，必须写入 `meta.retrievalCoverage`。
- 只消费与客户判断相关的业务字段，不输出内部技术字段和敏感字段原值。

### 示例 3：名称归一 `query-by-name`

常见返回结构通常为：

```json
{
  "resolution_status": "resolved | ambiguous | no_match",
  "records": [],
  "record_candidates": [],
  "message": "..."
}
```

消费建议：

- `no_match` 或空数组只能说明名称归一未命中，不能直接推断 CRM 一定没有该公司记录。
- 这类 miss 后，仍要回到 `identify-with-describe -> get -> query-by-sql` 的对象描述驱动链路。

## 第一版不默认查询自定义对象

自定义对象后置处理：

- 用户明确提到对象语义时，先调用 `sharecrm data describe identify-with-describe`。
- 识别成功后必须调用 `sharecrm data describe get`，再按字段 label 解读。
- 若对象含义不明确、结果为多对象或字段无法支撑报告判断，不查询或不消费。
- 不做全量自定义对象发现、全量扫描或模糊碰撞。

## 输出到报告的边界

允许输出：

- 是否已建档、是否已有负责人或公海状态。
- 是否存在当前商机、历史商机、历史成交、订单/合同、回款和近期互动。
- 内部覆盖状态对客户理解、合作历史、风险或经营判断的影响。

禁止输出：

- 联系人手机号、邮箱、身份证等敏感个人信息。
- 内部备注、审批意见、成本、折扣、底价等敏感商业字段。
- 未经解释的字段 API 名和原始 JSON。
- 自动创建或更新 CRM 数据的动作建议。

## 失败处理

| 情况 | 处理 |
|:---|:---|
| 对象识别失败 | 不猜对象；跳过该类 CRM 记录 |
| 对象多候选 | 用户语义不明确时不查询 |
| 对象描述失败 | 不查询该对象 |
| 字段不存在 | 寻找 label 语义相近字段；仍无则跳过 |
| 查询无记录 | 不输出该类内部记录 |
| 查询报错或权限不足 | 继续外部报告，不编造 CRM 记录 |
| CRM 与外部事实冲突 | 分开表达来源和时间口径，不强行合并 |
