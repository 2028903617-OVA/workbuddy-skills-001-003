# ShareCRM CLI 最少 Loop 查询规则

本文件定义报告生成时的最短查询路径。目标是在保证数据准确的前提下减少无效 describe、重复查询和补查循环。

## 总原则

- 不猜对象 apiName，不猜字段 apiName，不猜枚举值。
- 先收敛对象和字段，再查询数据。
- 同一对象本轮只 describe 一次；已确认字段在本轮复用。
- 互不依赖的基础对象可以并行查；依赖 ID 的对象必须先完成名称归一。
- 查询失败、权限不足或字段不可用后，不在同一轮反复试同一对象。
- 基础事实足够支撑输出后停止补查，缺失项进入报告，不为了完整感继续 loop。

## 四步查询计划

### Step 1: metadata plan

确认本次报告需要哪些对象，只对这些对象做对象和字段确认。

优先使用：

```bash
sharecrm data describe identify-with-describe --query "<业务对象名>" --include_simple_describe true
```

已知对象 apiName 时使用：

```bash
sharecrm data describe get --object_api_name <objectApiName> --simple_describe true
```

只从返回的 `field_list` 中选择字段。字段不存在、禁用或无权限时，删除该字段并记录数据缺口。

### Step 2: identity plan

客户、商机、联系人、员工、部门等名称必须先归一为 `_id`。

```bash
sharecrm data record query-by-name --name "<名称>" --object_api_names AccountObj
sharecrm data record query-id-by-name --query "<名称>" --apiNames ContactObj
```

规则：

- 已有 `_id` 时，直接 `get-by-id` 或按 `_id` 查询，不再名称解析。
- `object_reference` 字段过滤必须使用关联记录 `_id`。
- `employee` / `department` 字段过滤必须先拿人员或部门 `_id`。
- 多候选或短词低置信候选必须让用户确认，不自动选择。

### Step 3: base fetch

客户简报基础对象通常为：

```text
AccountObj
NewOpportunityObj
ContactObj
ActiveRecordObj
```

字段查询使用：

```bash
sharecrm data record query-by-fields \
  --object_api_name <objectApiName> \
  --select_fields <confirmed_fields> \
  --account_id-eq <accountId> \
  --sort last_modified_time:desc \
  --limit 50
```

如对象没有 `last_modified_time` 或字段未确认，改用已确认的时间字段，如 `create_time`。

### Step 4: triggered fetch

只在触发条件成立时补查扩展对象：

```text
RequirementObj
ActivityQuestionObj
ActivityTodoObj
MethodologyTaskObj
ScheduleObj
CheckinsObj
AIMeetingObj
AIMeetingChunkObj
SalesOrderObj
PaymentObj
```

触发对象补查前先确认字段；不要为了数据覆盖而查询所有扩展对象。

## 明细与聚合选择

明细查询：

```bash
sharecrm data record query-by-fields ...
sharecrm data record query-by-sql --sql "SELECT field1, field2 FROM ObjectObj WHERE ..."
```

聚合查询：

```bash
sharecrm data record query-aggregate-by-sql \
  --sql "SELECT COUNT(*) as total, SUM(amount) as totalAmount FROM NewOpportunityObj WHERE ..."
```

约束：

- `query-by-sql` 只用于明细，不用于聚合。
- `query-aggregate-by-sql` 只用于 COUNT/SUM/MAX/MIN/AVG/GROUP BY。
- SQL 必须明确字段，不使用 `SELECT *`。
- 聚合结果用于周报、月报、团队汇总；客户简报只在需要金额/数量概览时使用聚合。

## 过滤操作符

| 字段类型 | 可用操作符 |
| --- | --- |
| text | `eq`, `ne`, `like`, `in` |
| number / date / date_time | `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `between`, `in` |
| boolean | `eq`, `ne` |
| array | `in` |

注意：

- `in` 值格式：`A,B`。
- `between` 值格式：`10,20`。
- 多个过滤条件默认 AND。
- `select_one` / `select_many` 必须使用 options 中的合法值。

## 字段和对象防误用

- 客户对象是 `AccountObj`，不是 `CustomerObj`。
- 商机对象是 `NewOpportunityObj`，不是 `OpportunityObj` 或 `SalesOpportunityObj`。
- 商机、销售记录、订单、回款中客户关联字段通常是 `account_id`，不要猜成 `accountId`、`_accountId`、`customer_id`。
- 销售记录中商机关联字段是 `new_opportunity_id`。
- 负责人字段通常是 `owner`，不是 `ownerId`。
- 回款对象是 `PaymentObj`，销售订单对象是 `SalesOrderObj`。

## 查询状态与停止条件

每个对象只保留一个最终状态：`已读取`、`无数据`、`权限不足`、`未触发查询`、`查询失败`。

停止补查条件：

- 已有基础对象和至少一个高价值证据源支撑核心结论。
- 扩展对象只会补充细节，不会改变结论。
- 同一对象已权限不足或不可恢复失败。
- 用户问题没有触发该扩展对象。

继续补查条件：

- 核心结论依赖该对象，例如见客前缺少会议参会人、交接缺少待兑现承诺、高层陪访缺少高层会纪要。
- CRM 基础对象与 Memory 冲突，需要额外证据核对。
- 用户明确要求某类数据，如回款、会议纪要、需求、待办。

## Query Plan 输出要求

在执行查询前形成内部 query plan：

```yaml
query_plan:
  target_report:
  object_plan:
    - object_api_name:
      reason:
      fields_to_describe:
      filters:
      status: planned|skipped
  identity_resolution:
    - entity:
      method:
      required: true|false
  stop_after:
    - condition
```

无需把完整 query plan 展示给用户，但最终报告必须输出数据覆盖摘要。
