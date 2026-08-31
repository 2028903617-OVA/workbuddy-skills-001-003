---
name: fxiaoke-apl-function
version: 1.2.0
description: 纷享销客 APL 自定义函数（Groovy）编写参考与可复用模板。覆盖 5
  大命名空间（UI事件/按钮/计划任务/流程后动作/校验函数）、context、Fx.object、Fx.org、FQL、QueryOperator、构建器、聚合、日期处理、UIEvent
  数据更新事件 DSL，并结合本组织 8 份已上线生产函数（陈治彤/季必云/傅佳敏）提炼的真实写法、生产字段 code
  与「真实代码反模式与坑」，帮助快速写出可执行、不踩坑的 APL 函数。
---

# 纷享销客 APL 自定义函数编写技能

> 信息来源：纷享销客开发者手册 APL 参考文档（developer.fxiaoke.com/apl_v2）+ 本组织已上线生产函数（作者：陈治彤，函数「跟进任务积分人员更新完成值」）+ 本工作区实测（2026-07）。
> 适用语言：APL 支持 Jar / Groovy 两种；本技能示例均为 **Groovy**。

---

## 一、何时使用本技能

当用户的请求涉及「在纷享销客里写/改自定义函数」时，立即加载本技能。典型场景：

- **计划任务**：批量刷新/反写某对象字段（如刷新销售订单"首次回款日期"）。
- **流程后动作 / 前验证**：单据保存后或保存前做跨对象聚合、校验、回写。
- **范围规则**：查找关联字段可选范围（返回 QueryTemplate 或 List）。
- **积分 / 绩效 / 提成计算**：按人员、门店、月份聚合线索/订单/回款。

---

## 二、context 上下文对象（入口数据）

不同函数类型（命名空间）下 context 取数规则、返回值都不同，**写错取数入口是最高频的 bug**。纷享 APL 共有 **5 大命名空间**：

| 命名空间 | 触发时机 | context 入口 | 返回值类型 | 典型用途 | 真实样本 |
|---|---|---|---|---|---|
| **UI事件** | 字段 onChange / UI 交互 | `context.data`（当前主对象） | void / **数据更新事件** | 字段联动、自动带出 | #1 #3 #8 |
| **按钮** | 列表/详情按钮点击 | `context.data`（当前主对象） | void | 手动触发动作 | #2 |
| **计划任务** | 定时调度 | `context.objectIds`（List<String> id 列表） | void | 批量刷新/反写 | #4 |
| **流程（workflow post-action）** | 审批通过/状态变更后 | `context.data`（主单）+ `context.details[<子表api>]`（子表 List） | void | 跨对象回写、主从创建 | #5 #6 |
| **校验函数** | 审批节点校验 | `context.data`（当前主对象） | **`ValidateResult`** | 阻断式校验（read-only） | #7 |

> 边界：UI事件/按钮/校验函数/旧版流程函数用 `context.data`；**计划任务一律 `context.objectIds`**（除非单条触发）；**2024.2.24 后新建的流程函数不再支持 `context.details`**，但在此之前创建的老函数仍能跑（如样本 #5 创建于 2023-12，仍用 `context.details`）。

### 5 大命名空间取数详情

**UI事件 / 按钮 / 校验函数**（同入口，两种属性访问都行）：
```groovy
String id   = context.data["_id"] as String    // Map 访问（动态 key 用它）
String id2  = context.data._id as String       // 直接属性访问（字段名确定时更简洁）
String name = context.data["name"] as String
```

**计划任务**：
```groovy
List ids = context.objectIds as List
def (Boolean error, List dataList, String errorMessage) = Fx.object.findByIds("SalesOrderObj", ids,
    FQLAttribute.builder().columns(["_id","name","first_repayment_time__c"]).build())
dataList.each { item -> Map map = item as Map; String dataId = map._id as String; ... }
```

**流程（workflow post-action，主从结构）**：
```groovy
String priceList = context.data["field_0su78__c"] as String   // 主单字段
List details = context.details["object_Ye30r__c"] as List      // 子表明细 List
details.each { ij -> ... }
```

**关联业务模块（主单 context 里零成本取数）⭐**：
```groovy
// context.data.related_object = Map<业务对象API, List<业务数据ID>>
// 例：销售记录既关联线索又关联客户 → {"LeadsObj":["线6a01..."], "AccountObj":["客6a02..."]}
Map rel = context.data.related_object as Map
rel.each { def key, value ->
    if (key == "LeadsObj")   { String leadId = (value as List)[0] as String }
    if (key == "AccountObj") { String custId = (value as List)[0] as String }
}
```
> 与「查询时按需取关联」不同：计划任务里用 `FQLAttribute.builder().related_api_names([...]).related_object_data(true)` 拿到的是 `related_object_data` 字段（List<Map> 完整业务对象）；本处是主单 context 里已随主单载入、只有 id 的 Map。两者互补。

**校验函数返回 `ValidateResult`**：
```groovy
def result = ValidateResult.build {
    success = true             // 成功=通过校验（审批继续）
    errorMessage = "校验通过"   // 成功/失败都会显示给审批人
}
return result
```

**UI事件返回「数据更新事件」**（5 件套 DSL）：
```groovy
UIEvent event = UIEvent.build(context) {
    editMaster(["field_x__c": v])   // 改主单字段（也可 set(field:v)）
    removeDetail "SubObjApi"        // 清空子表所有行
    addDetail "SubObjApi" set(      // 增子表行（一次设多字段；字段名带 __c 必须加引号）
        "field_a__c": vA,
        "field_b__c": vB)
    doCalculate(true)               // 重算公式（addDetail 后必加，否则计算字段不刷新）
}
return event
```

⚠️ **apiName 前缀观察（非官方规则，待用户确认）**：样本里出现过 `F_`（流程/傅佳敏）、`Proc_`（流程/陈治彤）、`func_`（校验/傅佳敏）前缀，疑似"前缀=命名空间+作者"的习惯，但纷享官方未规定，命名时以平台自动生成为准。

⚠️ **空值坑**：前验证/UI 事件里，web 端字段空是 `''`（空串），移动端/server 端字段空是 `null`。判定时务必 `if (value != null && value != '')`，否则 web 上拿到 `''` 会让后续逻辑出错。

⚠️ **异步字段不可信**：`context.data` 里的统计字段、计算字段、引用字段可能不准确（尤其流程后动作），需要实时值请用 `Fx.object.findById` 重新查一次。

---

## 三、Fx.object 数据操作 API（核心）

> 通用返回解构：`def (Boolean error, 数据, String errorMessage) = ...`
> 查多条的返回体 `QueryResult` 含：`size`(本次返回条数) / `total`(总条数) / `dataList`(List)。

### 查询
```groovy
// 1) FQL 查多条
FQLAttribute fql = FQLAttribute.builder()
  .columns(["_id","name","amount"])
  .queryTemplate(QueryTemplate.AND(["owner": QueryOperator.EQ(personId)],
                                   ["life_status": QueryOperator.EQ("normal")]))
  .limit(100).build()
def (Boolean error, QueryResult ret, String msg) = Fx.object.find("PaymentObj", fql, SelectAttribute.builder().needInvalid(false).build())

// 2) 查单条（优先用 findOne，不是 find+limit1）
def (Boolean error, Map d, String msg) = Fx.object.findOne("AccountObj",
    FQLAttribute.builder().columns(["_id","name"]).queryTemplate(QueryTemplate.AND(["_id": QueryOperator.EQ(id)])).build(),
    SelectAttribute.builder().build())

// 3) 按 id 查
def (Boolean error, Map d, String msg) = Fx.object.findById("AccountObj", id, FQLAttribute.builder().columns(["_id"]).build(), SelectAttribute.builder().build())

// 4) 按 id 集合批量查（计划任务主用）
def (Boolean error, List dataList, String msg) = Fx.object.findByIds("object_incentive_points__c", ids, FQLAttribute.builder().columns(["_id","name"]).build())

// 5) SQL 查询（明细/聚合都用它；聚合返回 List 而非 QueryResult）
def rst = Fx.object.select("select _id, name from AccountObj where create_time > 0 limit 10 offset 0").result() as QueryResult
// 大数据量流式（不支持 order by / limit，按闭包逐批处理）
Fx.object.select(sql, SelectAttribute.builder().build(), { list -> list.each { row -> log.info((row as Map)["name"]) } }).result()
```

#### 简化版签名（来自真实生产函数，适合简单等值查询）
```groovy
// 6) find 4 参简化版（where 直接传 List<Map> 等值，不构造 FQLAttribute）
def (Boolean error, QueryResult ret, String msg) = Fx.object.find(
    "OrderPaymentObj", [["payment_id": context.data["_id"]]], 100, 0)   // api, conditions, limit, offset
//   → ret.dataList / ret.total

// 7) findById 2 参简化版（只要一条记录，不传 FQL/Select）
def (Boolean error, Map d, String msg) = Fx.object.findById("SalesOrderObj", xsddbh)
//   → d 是单条 Map（可能为 null），没有 .total 属性！
```

#### ⭐ 同一查询的 3 种访问方式（本质等价，风格任选）
```groovy
// 方式 A：完整 3-arg + .result()（样本 #4）
def ret = Fx.object.find("SalesOrderProductObj",
    FQLAttribute.builder().columns([...]).queryTemplate(QueryTemplate.AND(["order_id": QueryOperator.EQ(ydd)])).limit(100).build(),
    SelectAttribute.builder().build()).result() as QueryResult
List list = ret.dataList

// 方式 B：完整 3-arg + APIResult 属性访问（样本 #8）
APIResult ret = Fx.object.find("SalesOrderProductObj",
    FQLAttribute.builder().columns([...]).queryTemplate(QueryTemplate.AND(["order_id": QueryOperator.EQ(ydd)])).limit(100).build(),
    SelectAttribute.builder().build())
if (ret.isError()) { log.info(ret.message()) }
QueryResult B = ret.data as QueryResult
List C = B.dataList as List

// 方式 C：4-arg 简化版 + 3-tuple 解构（样本 #7）
def (Boolean err, QueryResult data, String msg) = Fx.object.find("OrderPaymentObj", [["payment_id": id]], 100, 0)
if (!err && data.total > 0) { data.dataList.each { ... } }
```
> 关键：完整 3-arg 形式返回 **APIResult** 包装对象，可用 `.result()` / `.data` / `def (err,data,msg)=` 三种方式取出数据；4-arg 简化版直接返回 3-tuple。`.result()` 与 `.data` 等价。

#### findById 两种写法
```groovy
// 完整 4-arg（可指定返回字段）
def (Boolean e, Map d, String m) = Fx.object.findById("PriceBookProductObj", id,
    FQLAttribute.builder().columns(["_id","name","product_id","pricebook_sellingprice"]).build(),
    SelectAttribute.builder().build())
// 简化 2-arg（返回整条）
def (Boolean e, Map d, String m) = Fx.object.findById("SalesOrderObj", xsddbh)
// ⚠️ findById 返回 Map（单条）或 null，判存在性是 if (d != null)，绝对不能写 d.total（那是 QueryResult 的属性）
```

### 创建 / 更新 / 删除
```groovy
// 创建（主从同时）：details 传空 Map 表示不建从对象
def (Boolean error, Map data, String msg) = Fx.object.create("object_1yO4J__c", masterData, [:], CreateAttribute.builder().build())
// 创建（单条，无子表）：第三参 sub-detail 传 null（不是 [:]）
def (Boolean error, Map data, String msg) = Fx.object.create("follow_up_record__c", masterData, null, CreateAttribute.builder().build()).result() as Map
// 批量创建（单批最多 500）
def (Boolean error, List data, String msg) = Fx.object.batchCreate("AccountObj", objects, CreateAttribute.builder().build())

// 更新单条 —— 第二参是 dataId 字符串，不是把 _id 塞进 map！
def (Boolean error, Map data, String msg) = Fx.object.update("SalesOrderObj", dataId,
    ["first_repayment_time__c": minDate],
    UpdateAttribute.builder().triggerWorkflow(false).build())
// 按条件批量更新（默认最多 1000 条；设 isAllUpdate=true 突破；灰度能力）
Fx.object.update("object_x", QueryTemplate.AND(["name": QueryOperator.EQ("t")]), ["f":"v"], UpdateAttribute.builder().build())
// 底层批量字段更新（objects key=dataId；高风险）
Fx.object.batchUpdate("object_x", objectsMap, fields, BatchUpdateAttribute.builder().build())

// ⭐ 批量按主键更新（真实样本 #5，带字段白名单）——
//   datailsUpdateMap = Map<目标对象ID, 要更新的字段Map>；fields 是"允许更新的字段 API 列表"，未列入即使 put 了也不生效
List whiteList = ['field_d0da1__c','quantity','sales_price','subtotal']
def rst = Fx.object.batchUpdate('SalesOrderProductObj', datailsUpdateMap, whiteList).result() as List

// ⭐ 主从 update（给已有主单追加/重建子表，真实样本 #5）——
//   detailMap 结构 = Map<子表API, List<子表数据Map>>；第四个参是 ActionAttribute（不是 UpdateAttribute）
Map detailMap = ["SalesOrderProductObj": createList]
ActionAttribute attribute = ActionAttribute.build {
    triggerApprovalFlow = false   // 已审批通过，别再触发审批流
    triggerWorkflow = true
}
def result = Fx.object.update("SalesOrderObj", order_id, [:], detailMap, attribute).result() as Map
//   第三个参传 [:] 即可（masterId 已单独传；不要把 _id 再塞一遍）

// 删除
Fx.object.directDelete("object_x", id).result()                       // 直接删，不可恢复
Fx.object.delete("object_x", id).result()                             // 彻底删已作废数据
Fx.object.batchDelete("object_x", [id1,id2]).result()
```

### 其他
```groovy
// 关联/主从联查
def (Boolean e, QueryResult r, String m) = Fx.object.findWithRelated("object_child", "field_parent__c", [["_id": pid]], ["create_time":1], 10, 0, ActionAttribute.build{forceQueryFromDB=false})
// 团队成员
def rst = Fx.object.getTeamMember("AccountObj", dataId).result() as List
Fx.object.editTeamMember("AccountObj", dataId, teamMembers, false)
```

---

## 四、Fx.org 组织/人员 API

```groovy
def (Boolean e, Map u, String m) = Fx.org.findUserById(userId)            // 查人员信息
def (Boolean e, Map u, String m) = Fx.org.findByUserIds([id1,id2])
def (Boolean e, Map d, String m) = Fx.org.findSuperordinateDepartments(deptId, true)  // 上级部门（递归）
def (Boolean e, Map d, String m) = Fx.org.findSubordinateDepartments(deptId, true)   // 下级部门（递归）
def (Boolean e, Map c, String m) = Fx.org.getCompanyInfo()               // 企业信息（时区等）
// 注意：人员字段（如转正日期 probation_end_date__c）在返回的 Map 里按 key 取
if (u[1]["probation_end_date__c"]) { long t = u[1]["probation_end_date__c"] as long; Date d = Date.of(t) }
```

---

## 五、FQL / 查询构建器

### FQLAttribute.builder()
- `.columns(["_id","name",...])` —— 指定返回字段（不支持 `select *`）
- `.queryTemplate(QueryTemplate.AND([...]))` —— 条件（见下）
- `.limit(n)` / `.build()`

### QueryTemplate
- `QueryTemplate.AND([[字段: QueryOperator.EQ(v)], ...])`
- `QueryTemplate.OR(t1, t2)` —— **OR 需要单独向销售开通"对象列表筛选支持或者"产品**

### SelectAttribute.builder()
- `.needInvalid(false)` —— 排除作废数据（推荐查有效数据都加）
- `.needCount(true)` —— 返回 total
- `.build()`

### UpdateAttribute.builder() / CreateAttribute.builder() / ActionAttribute
- `UpdateAttribute.builder().triggerWorkflow(true|false).build()` —— 是否触发工作流（**刷新历史数据建议 false，避免连锁触发**）
- `ActionAttribute` 含：`triggerWorkflow`、`triggerApprovalFlow`、`skipFunctionAction`、`skipAfterFunction`、`specifyCreatedBy` 等

### QueryOperator 操作符全集
`EQ` `NEQ` `GT` `GTE` `LT` `LTE` `IN(List)` `NOTIN(List)` `LIKE('%x%')` `ISNULL` `ISNOTNULL`；
SQL 文本模式下还支持 `= != > < >= <=` `IN/NOT IN` `BETWEEN AND` `is null/is not null` `like/not like` `@>`(数组包含，单选/多选 List 字段) `&&`(数组交集，多选用户/部门，需括号包裹)。

### FQL / SQL 模式（Fx.object.select）
- 默认 limit 10，最大 100；默认 offset 0。
- 聚合：`count/sum/min/max/avg` + `group by`（**不支持 having**）；聚合结果返回 `List` 不是 `QueryResult`。
- 字段间比较支持（`where last_modified_time > create_time`），但 `in/between/@>` 不支持字段间比较。
- OR 需开通。

---

## 六、日志、日期

```groovy
log.info("当前执行: " + dataId)
log.error("异常: " + msg)
// 日期
Date now = Date.now()
Date d1  = Date.of("2000-01-01")          // 字符串
Date d2  = Date.of(1602325440000)         // 毫秒时间戳（long）
Date firstDay = someDate.withDay(1)       // 本月1日
Date lastDay  = firstDay + 1.months - 1.days  // 本月最后一天
Date next     = someDate + 1.months
```

---

## 七、本组织已验证的生产字段（实测 code，勿用中文过滤）

> 这些是「引用字段 / 选项字段」真实存储值，**必须用 code 不是显示值**，否则过滤失效。
> ⚠️ **金额类字段（回款金额 / 订单金额）不止一种，不要当固定事实写死**：下表 `amount`、`field_7QA6l__c` 仅是已上线生产函数里用到的**示例**，实际用哪个以用户后续明确指定为准（可能还有 `payment_amount`、`order_amount` 等其他金额字段）。

| 对象 | 字段 API | code / 取值 | 说明 |
|---|---|---|---|
| 回款 `PaymentObj` | `field_274Al__c` | `8b4we3s9C` = 销售收款；`定金` = 定金 | **回款类型权威字段**（回款明细上的是引用字段，读不到，直接读 PaymentObj 这个） |
| 回款 `PaymentObj` | `order_id` | 存**订单 `_id`**（非编号文本） | 按订单聚合回款用此字段 |
| 回款 `PaymentObj` | `amount` | 回款金额（**示例**；金额字段有多种，以用户指定为准） | 生产函数用过此字段；注意不是 `payment_amount` |
| 回款 `PaymentObj` | `payment_time` | datetime | 回款日期（首回款=MIN(payment_time)，仅取"销售收款+已回款 normal"） |
| 销售订单 `SalesOrderObj` | `field_7QA6l__c` | 订单金额（**示例**；金额字段有多种，以用户指定为准） | 生产积分函数用过此字段（也可能用 `order_amount`，以用户指定为准） |
| 销售订单 `SalesOrderObj` | `order_time` | datetime | 订单日期 |
| 销售订单 `SalesOrderObj` | `first_repayment_time__c` | date | 首次回款日期（普通字段，无自动反写，需计划任务刷） |
| 人员对象 `PersonnelObj` | `amount__c` | currency | 月度销售指标 |
| 人员对象 `PersonnelObj` | `name` | 系统名(昵称) | 人员识别主键 |
| 人员对象 `PersonnelObj` | `main_department` | 主属部门 | 门店/部门归属 |
| 人员对象 `PersonnelObj` | `field_v2M9H__c` | `6p1Rxc395`=欣暖家 | 事业部/品牌 |
| 销售记录 `ActiveRecordObj` | `related_sales_lead__c` | 关联线索 | 同线索聚合对比用 |
| 销售记录 `ActiveRecordObj` | `active_record_type` | 跟进类型 | |
| 线索 `LeadsObj` | `created_by` | 人员 id（数组） | 按创建人统计线索用 |
| 线索 `LeadsObj` | `creation_date__c` | datetime | 线索创建日期 |

### 新增对象（来自 8 份生产函数，已验证真实 code）

| 对象 | 字段 API | code / 取值 | 说明 |
|---|---|---|---|
| 合同变更明细 `object_Ye30r__c` | `field_3pbyw__c` | 订单产品明细 id | 指向原订单产品 |
| 合同变更明细 `object_Ye30r__c` | `field_a1d87__c` | `option1`=否 / `kY661dOQl`=是 | 是否赠品（不可修改） |
| 合同变更明细 `object_Ye30r__c` | `field_9bMs1__c` | 数量 | 变更后商品数量 |
| 合同变更明细 `object_Ye30r__c` | `field_x81z5__c` | `K80IzX2T0`=全换货 / `option1`=全退货 / `hnmnJYhkM`=部分退货 / `5kTtu2c34`=单价变更 | 变更类型（4 值选项） |
| 合同变更明细 `object_Ye30r__c` | `field_hKn2u__c` | 数量 | 新增商品数量 |
| 合同变更明细 `object_Ye30r__c` | `field_41L8X__c` | 单价 | 新增商品单价 |
| 合同变更明细 `object_Ye30r__c` | `field_f1Byc__c` | 单价 | 变更后原商品单价 |
| 合同变更明细 `object_Ye30r__c` | `field_1m2f4__c` | 产品 id | 新增产品 |
| 合同变更明细 `object_Ye30r__c` | `field_pT3xx__c` | 金额 | 价目表售价 |
| 合同变更明细 `object_Ye30r__c` | `field_2IKPf__c` / `field_5sKmP__c` / `field_68O7A__c` / `field_J15ok__c` / `field_z1I9u__c` / `field_F1hO0__c` | 数量/单价/成本/结算价/毛利/折扣% | 变更前原商品 6 项 + 折扣 |
| 合同变更申请单（父） | `field_0su78__c` | 价目表 id | 主单上的价目表 |
| 合同变更申请单（父） | `field_k2db9__c` | 销售订单 id | 主单上的原销售订单 |
| 订单产品 `SalesOrderProductObj` | `quantity` / `sales_price` / `product_price` / `subtotal` / `discount` | 数量/单价/价目表售价/小计/折扣 | 标准字段 |
| 订单产品 `SalesOrderProductObj` | `field_d0da1__c` | 布尔 | 是否赠品 |
| 订单产品 `SalesOrderProductObj` | `field_BqU1u__c` | `option1`=常规机 | 库存状态（默认常规机） |
| 订单产品 `SalesOrderProductObj` | `field_y924A__c` | `台` | 计价单位（默认台） |
| 订单产品 `SalesOrderProductObj` | `field_FFkCJ__c`/`field_1XqnJ__c`/`field_QUjoa__c`/`field_9LIge__c`/`field_u2297__c`/`field_oP6Kp__c` | 数量/单价/成本/结算价/毛利/价目表售价 | "变更前影子字段 6 件套" |
| 订单产品 `SalesOrderProductObj` | `product_category__c` / `product_item__c` / `price_book_product_id` / `price_book_id` / `order_id` | — | 产品大类/品项/价目表明细/价目表/订单 |
| 价目表明细 `PriceBookProductObj` | `pricebook_sellingprice` | 金额 | 价目表售价 |
| 价目表明细 `PriceBookProductObj` | `field_yy0j1__c` | — | 产品大类 |
| 价目表明细 `PriceBookProductObj` | `product_item__c` | — | 产品品项 |
| 高级外勤 `follow_up_record__c` | `follow_up_type__c` | — | 跟进类型 |
| 高级外勤 `follow_up_record__c` | `record_content__c` | — | 记录内容 |
| 高级外勤 `follow_up_record__c` | `related_customer__c` / `related_lead__c` / `related_sales_record__c` | 客户/线索/销售记录 id | 3 个关联查找字段 |
| 高级外勤 `follow_up_record__c` | `owner` / `created_by` / `owner_department`(String) / `data_own_department`(List) / `create_time` | — | 人员/部门/时间（create_time 常保留主单时间） |
| 销售记录 `ActiveRecordObj` | `active_record_type` / `active_record_content` | — | 跟进类型 / 记录内容 |
| 销售记录 `ActiveRecordObj` | `related_object` | Map<api, List<id>> | 关联业务模块（见第二节） |
| 回款明细 `OrderPaymentObj` | `payment_id` | 回款 id | 关联父回款 |
| 回款明细 `OrderPaymentObj` | `order_id` | 销售订单 id | 关联销售订单 |

---

## 八、可复用模板

### 模板 A：计划任务批量刷新某对象字段（写法已对照真实生产函数校准）
场景：刷新 7 月销售订单的 `first_repayment_time__c` = 该订单名下"销售收款+已回款"回款的最早 `payment_time`。
⚠️ `payment_time` 是 `com.fxiaoke.functions.time.Date`，**无 getTime() 也无 compareTo**：比较必须用 `.toString()`（ISO 字典序=时间序），见 D18。

```groovy
List ids = context.objectIds as List
def (Boolean e0, List orders, String m0) = Fx.object.findByIds("SalesOrderObj", ids,
    FQLAttribute.builder().columns(["_id"]).build())
orders.each { o ->
    String oid = (o as Map)._id as String
    // 查该订单名下、销售收款、已回款的回款，取最早 payment_time
    def (Boolean e1, QueryResult pr, String m1) = Fx.object.find("PaymentObj",
        FQLAttribute.builder()
            .columns(["_id","payment_time"])
            .queryTemplate(QueryTemplate.AND(
                ["order_id": QueryOperator.EQ(oid)],
                ["life_status": QueryOperator.EQ("normal")],
                ["field_274Al__c": QueryOperator.EQ("8b4we3s9C")]   // 销售收款 code
            ))
            .build(),
        SelectAttribute.builder().needInvalid(false).build())
    if (!e1 && pr && pr.dataList && pr.dataList.size() > 0) {
        Date minDate = null
        pr.dataList.each { p ->
            Date t = (p as Map)["payment_time"] as Date
            // 用 toString() 比较早晚（ISO 字典序），不要 t < minDate（会触发 compareTo 静态检查失败）
            if (t != null && (minDate == null || t.toString() < minDate.toString())) minDate = t
        }
        if (minDate != null) {
            Fx.object.update("SalesOrderObj", oid,
                ["first_repayment_time__c": minDate],
                UpdateAttribute.builder().triggerWorkflow(false).build())
        }
    }
}
```

### 模板 B：按人员+日期聚合（积分/完成值，来自已上线函数）
要点：① `owner` 是数组，用 `QueryOperator.EQ("人员id字符串")` 可匹配；② 线索用 `created_by`、订单/回款用 `owner`；③ 当月范围=本月1日..月末最后一天；④ 个人销售收款用 `field_DapeV__c > 0`，团队用 `field_274Al__c = '8b4we3s9C'`；⑤ 更新用 `Fx.object.update(api, id, map, UpdateAttribute.builder().triggerWorkflow(true).build())`。

### 模板 C：校验函数（审批节点阻断校验，ValidateResult）
场景：回款审批前，校验其回款明细关联的销售订单都已审核通过（life_status=normal）。

```groovy
def result = ValidateResult.build {
    def (Boolean err, QueryResult data, String msg) = Fx.object.find(
        "OrderPaymentObj", [["payment_id": context.data["_id"]]], 100, 0)
    if (err || data.total == 0) {
        success = false
        errorMessage = "没有回款明细"
    } else {
        boolean allPass = data.dataList.every { detail ->
            def (Boolean e2, Map order, String m2) = Fx.object.findById("SalesOrderObj", detail["order_id"] as String)
            !e2 && order != null && order["life_status"] == "normal"   // ⚠️ 用 order != null 判存在，绝不用 order.total
        }
        success = allPass
        errorMessage = allPass ? "全部关联订单已审核通过" : "有关联订单未审核通过"
    }
}
return result
```

### 模板 D：UI事件「数据更新事件」（自动带出子表明细）
场景：选中原销售订单后，把该订单下所有订单产品自动带出到变更单明细。

```groovy
String ydd = context.data.field_k2db9__c as String          // 原销售订单
if (!ydd) { return UIEvent.build(context) { } }
def (Boolean err, QueryResult ret, String msg) = Fx.object.find("SalesOrderProductObj",
    FQLAttribute.builder()
        .columns(["_id","product_id","quantity","sales_price","field_d0da1__c","field_8NgO5__c"])
        .queryTemplate(QueryTemplate.AND(["order_id": QueryOperator.EQ(ydd)])).limit(100).build(),
    SelectAttribute.builder().build())
UIEvent event = UIEvent.build(context) {
    removeDetail "object_Ye30r__c"                            // 先清空旧明细
    if (!err && ret.dataList) {
        ret.dataList.each { item ->
            Boolean zp = item["field_d0da1__c"] as Boolean
            addDetail "object_Ye30r__c" set(
                "field_3pbyw__c": item["_id"],
                "field_Gwi1i__c": item["product_id"],
                "field_2IKPf__c": item["quantity"],
                "field_5sKmP__c": item["sales_price"],
                "field_a1d87__c": (zp ? "kY661dOQl" : "option1")   // 用三元，别手撸 if-elseif
            )
        }
    }
    doCalculate(true)                                        // 重算公式
}
return event
```

### 模板 E：流程后动作（合同变更审核通过后回写订单产品）
场景：变更单明细 → 按"变更后数量/变更类型"回写/新建订单产品。

```groovy
Map datailsUpdateMap = [:]
List createList = []
context.details["object_Ye30r__c"].each { ij ->
    Map updateMap = [:]
    // ... 按 ij["field_x81z5__c"]（变更类型）+ ij["field_9bMs1__c"]（变更后数量）分支计算 updateMap ...
    datailsUpdateMap.put(ij["field_3pbyw__c"], updateMap)    // key = 订单产品 ID
}
if (datailsUpdateMap) {                                      // Groovy truthy：非空 Map
    List fields = ['quantity','sales_price','subtotal','field_d0da1__c']
    Fx.object.batchUpdate('SalesOrderProductObj', datailsUpdateMap, fields).result() as List
}
if (createList) {
    Map detailMap = ["SalesOrderProductObj": createList]
    ActionAttribute attr = ActionAttribute.build { triggerApprovalFlow = false; triggerWorkflow = true }
    Fx.object.update("SalesOrderObj", context.data["field_k2db9__c"], [:], detailMap, attr).result() as Map
}

---

## 九、高频坑清单（必读）

1. **计划任务入口是 `context.objectIds`，不是 `context.data`**；单条触发才用 `context.data`。
2. **更新 API 第二参是 dataId 字符串**，不要把 `_id` 塞进 updateFields map（老手也容易错）。
3. **引用字段读不到值**：回款明细上的回款类型是引用字段（fs-server/APL 取不到真实值），要读 `PaymentObj.field_274Al__c` 本身；且其值是 **code**（`8b4we3s9C`），**不是中文"销售收款"**。
4. **select 默认 limit 10、max 100**；要全量用 `.select(sql, attr, closure)` 流式或分页。
5. **聚合结果类型是 List**（不是 QueryResult），解构时注意。
6. **日期 datetime→date**：写 date 字段直接传 Date 对象即可，平台自动截断；不要手拼字符串。
7. **刷新历史数据把 triggerWorkflow 设 false**，避免连锁触发其他工作流/积分重算。
8. **web 空值 `''` vs 移动端 `null`**：前验证/UI 事件判定要 `!= null && != ''`。
9. **OR 条件需开通**：产品未开通时 QueryTemplate.OR 不可用。
10. **`context.details` 在 2024.2.24 后新建流程函数中已移除**，别再用。
11. **销售订单对象经 fs-server 的更新接口被禁用**（报"当前对象不支持执行该操作:编辑"）——如需外部改订单字段，走计划任务 APL 或后台 CSV 导入，不能靠 MCP 增量更新。

---

## 十、真实代码反模式与坑（来自 8 份已上线生产函数）

> 以下全部是**真实生产代码里出现过的 bug / 坏味道**，写新函数时主动规避。样本作者：陈治彤 / 季必云 / 傅佳敏。

### D1. Boolean → option code 手撸映射（重灾区，出现 3 次）
```groovy
// ❌ 真实代码：
if (zp == "option1") zpCode = false
else if (zp == "kY661dOQl") zpCode = true
// ✅ 改用 getOptionInfo，避免硬编码 option code（改字段选项值就失准）
def info = Fx.object.getOptionInfo("object_Ye30r__c", "field_a1d87__c").result()  // Map<中文, code>
def zpCode = (info["是"] == zp)   // 或按业务取对应 code
```

### D2. findById 返回 Map 却当 QueryResult 用（生产事故级）
```groovy
def (Boolean e, Map d, String m) = Fx.object.findById("SalesOrderObj", id)
if (d.total != 0) { ... }   // ❌ d 是 Map，d.total 永远是 null，null != 0 永远 true → 校验形同虚设
// ✅ 判存在性是：
if (d != null) { String smzt = d["life_status"] as String; ... }
```

### D3. 循环内只 set 不累加（"全部通过"被单条通过覆盖）
```groovy
// ❌ 真实代码：循环里 success = true，只要任意一条通过整体就通过
dataList.each { if (it["life_status"] == "normal") success = true }
// ✅ 必须每条都通过：
boolean allPass = dataList.every { it["life_status"] == "normal" }
success = allPass
```

### D4. createMap 在分支外 add（脏数据）
```groovy
// ❌ 真实代码：每轮迭代末尾的 createList.add(createMap) 写在 if/else if 之外
//    → type 不匹配时也塞了一个空/只含 _id 的 Map 进去，createList != [] 判空失效
// ✅ 在分支内部显式 add，且仅当确要创建时才 add
if (type == "K80IzX2T0") { Map m = [...]; createList.add(m) }
```

### D5. 同 key 多次 put 覆盖
```groovy
// ❌ 真实代码：discount 被 put 两次，第二次覆盖第一次
createMap.put("discount", ij["field_52Qj6__c"])
createMap.put("discount", ij["field_F1hO0__c"])
// ✅ 想清楚只 put 一次，或用变量算好再 put 一次
```

### D6. 整数字面量赋值数字字段
```groovy
// ❌ field_1b9t7__c:0   （0 是 int，数字字段通常要 BigDecimal）
// ✅ field_1b9t7__c: 0 as BigDecimal  或  BigDecimal.ZERO
```

### D7. if/else if 分支体完全相同（复制粘贴漏改）
```groovy
// ❌ 真实代码：两个分支的 addDetail 调用 12 个字段完全一样，仅差一行 log
if (zpCode == "option1")        { addDetail "object_Ye30r__c" set(...) }
else if (zpCode == "kY661dOQl") { addDetail "object_Ye30r__c" set(...) }  // 一模一样
// ✅ 合并：if (zpCode == "option1" || zpCode == "kY661dOQl") { addDetail ... }
```

### D8. 变量误赋值（复制粘贴漏改字段）
```groovy
// ❌ 真实代码：afterQuantity 和 yGoodsQuantity 都从 field_9bMs1__c 取
BigDecimal afterQuantity = ij["field_9bMs1__c"] == null ? 0 : ij["field_9bMs1__c"] as BigDecimal
BigDecimal yGoodsQuantity = ij["field_9bMs1__c"] == null ? 0 : ij["field_9bMs1__c"] as BigDecimal  // 应是 field_hKn2u__c
// ✅ 每个变量单独核对源字段，命名也别用 yGoodsQuantity / yGodsPrice 这种易混的
```

### D9. 变量命名差（可读性）
避免 `Map B`、`List C`、`String ddcpid`(声明未用)、`owner1`(与字段 owner 混用)。用 `queryResult`、`productList`、`ownerList` 之类。

### D10. 空值没判（NPE 风险）
- `valuelist[0] as String` 前先判 `valuelist?.size() > 0`
- `context.data.related_object` 遍历前先判 `!= null`
- `findById` 结果先判 `!= null` 再取字段

### D11. 注释当变更日志
`// 1.数量=... // 2.销售单价=...` 这类把字段序号当版本号，业务调整时极易漏改。注释写"为什么"不写"第几步"。

### D12. record_type 硬编码
`record_type:"default__c"` 手动设业务类型，一般应由系统按业务类型自动派发，手动设可能不符合本单类型。

### D13. `/** */` 块注释导致编译失败（编辑器坑）
纷享 APL 编辑器/计划任务验证入口对 JavaDoc 风格 `/** ... */` 块注释解析不稳定，会报 `unexpected token: * @ line N`。**统一改用 `//` 行注释**（真实生产函数里 `//` 注释到处都是，稳定）。
另：Java 泛型写法 `Map<String, Long>` 也尽量别写，改成 `Map` / `List`（更贴近纷享 Groovy 实际，且避免个别入口泛型解析问题）。

### D14. `for`/`while` 语句被沙箱禁用（编辑器坑）
纷享 APL 沙箱明确禁止传统命令式循环，会抛 `SecurityException: ForStatements are not allowed`（同时 `while(true)` 也不推荐，稳妥起见一并避开）。

**❌ 禁写**：
```groovy
for (int i = 0; i < list.size(); i += 100) { ... }     // 外层分批
while (true) { ... if (done) break; offset += N }       // 内层翻页
```

**✅ 替换方案**（按场景挑）：

1. **固定步长分页**（外层 for 场景）：用 `List.collate(step).eachWithIndex` —— Groovy `collate(n)` 把 List 切成 n 一组的 `List<List<E>>`，再用 `eachWithIndex` 拿批次号：
```groovy
orderIds.collate(ORDER_CHUNK).eachWithIndex { List subIds, int i ->
    // i 就是批次号；subIds.size() 自动 ≤ ORDER_CHUNK
    fetchPage(0, subIds, i)
}
```

2. **不确定页数翻页**（while 场景）：用**闭包递归** —— 沙箱允许闭包内部递归调用自身：
```groovy
def fetchPage
fetchPage = { int offset, List subIds, int chunkIdx ->
    def (Boolean err, QueryResult data, String msg) = Fx.object.find(...)
    if (err || data.dataList == null || data.dataList.isEmpty()) return
    // ... 聚合逻辑 ...
    if (data.dataList.size() >= PAY_LIMIT) {
        fetchPage(offset + PAY_LIMIT, subIds, chunkIdx)   // 递归翻下一页
    }
}
fetchPage(0, initialSubIds, 0)
```

3. **有限次数循环**：用 `int.times { i -> ... }` 或 `0.upto(n-1) { i -> ... }` 或 `(0..<n).each { i -> ... }`。

4. **Map 按 key 分批回写**：先 `new ArrayList(map.keySet())` 再 `.collate(n).eachWithIndex`。

**记忆口诀**：看到要写 `for / while`，立刻反射——分页用 `collate + eachWithIndex`，翻页用闭包递归，遍历用 `each`。

**⚠️ 优先最简，别过度设计**：多数业务场景数据量在 `find` 单次的 `limit` 覆盖范围内，**先尝试「一次 find（limit 拉大如 2000） + 一次 batchUpdate」**，不要一上来就写翻页/递归/分块。翻页递归只在「确定会超单次 limit 上限」时才用。用户原话教训：写 APL 先用最简单的逻辑跑通，再按需优化。

### D15. `Fx.object.find` 两种返回形式，闭包递归解构会触发 `Object#call` 静态检查报错
`find` 有两种合法接收方式，**混用或解构方式不对会报 `Cannot find matching method java.lang.Object#call(...)` / `find(String, Object, SelectAttribute) not found`**：

- **方式 A（APIResult 包装，推荐用于多条件 FQL）**：
  ```groovy
  APIResult ret = Fx.object.find("Obj", FQLAttribute.builder().queryTemplate(...).limit(2000).build(), SelectAttribute.builder().build())
  if (ret.isError()) { log.info(ret.message()); return }
  QueryResult data = ret.data as QueryResult
  // data.dataList / data.total
  ```
- **方式 B（3-tuple 解构，仅适用于简化版 `find(api, [["field":v]], limit, offset)`）**：
  ```groovy
  def (Boolean err, QueryResult data, String msg) = Fx.object.find("Obj", [["field_a": v]], 100, 0)
  ```
  **两种不可混用**：不能在 `FQLAttribute` 版上写 `def (Boolean, QueryResult, String) = Fx.object.find(FQLAttr, SelectAttr)`（静态检查会认为 find 没有「返回 3 元组」的签名，进而在后续闭包递归 `fetchPage(offset,...)` 调用处报 `Object#call` 找不到方法）。

**避坑**：多条件查询一律用方式 A（`APIResult` 接收）；只在「单等值简化查询」且确需 3-tuple 时用方式 B。

### D16. 嵌套 Map 字面量赋值时父 Map 触发 `No such property` 静态检查
**现象**：`No such property: first_repayment_time__c for class: java.lang.Object @ line N`
**根因**：当外层 Map 声明为 `Map updateMap = [:]`（无泛型）时，value 类型被静态检查器推断为 `Object`；之后 `updateMap[oid] = ["first_repayment_time__c": ptime]` 时，静态检查器把内部 Map 字面量的字符串 key 当作"Object 的属性访问"在找 → 报"无此属性"。
**修复（双保险，任一即可）**：
1. 外层 Map 显式声明 value 类型：`Map<String, Map> updateMap = [:]`
2. put 时给内部 Map 字面量加 `as Map` 强转：`updateMap[oid] = (["first_repayment_time__c": ptime] as Map)`

**记忆口诀**：写到"Map 套 Map"（如 batchUpdate 的 `Map<id, fieldsMap>`）时，**先声明泛型**（`Map<String, Map>`）**再赋值**；别只写 `Map x = [:]` 让静态检查器瞎猜 value 类型。

**子坑（key 类型不匹配）**：声明 `Map<String, Map>` 后，若 key 来自 `each { oid, v -> ... }` 闭包参数（静态类型为 `Object`），put 时会报 `LinkedHashMap#putAt(String, Map) with arguments [Object, Map]`（Object 不能当 String key）。**修复**：put 时把 key 转成 String：`updateMap[oid as String] = (["field": v] as Map)`。oid 实际存的就是 String 订单 ID，转一下无副作用。

### D17. `QueryTemplate.AND/OR` 接收**可变参数 Map**，不是 List；且每个 Map 只能 1 个 key
**现象 A（编译）**：`Cannot find matching method QueryTemplate#AND(java.util.List)` —— 写 `QueryTemplate.AND([map1, map2])`（外层包一层 List）时触发。
**现象 B（运行）**：`The number of keys in the map cannot exceed 1` —— 把多个条件塞进**同一个 Map**（如 `AND([["a":op_a, "b":op_b]])` 或 `AND([a:op_a, b:op_b])`）时触发。

**根因**：`QueryTemplate.AND/OR` 的签名是**可变参数 `AND(Map... conditions)`**，每个 Map 必须是**只含 1 个 key** 的字段条件。两种错误写法：① 外层多包了一层 `[...]` 变成传 List；② 多个条件写进同一个 Map。

**❌ 错误写法 1（外层多包 List）**：
```groovy
QueryTemplate.AND([                 // ← 这个外层 [ ] 会让它变成 AND(List)，编译报错
    ["order_id": QueryOperator.IN(ids)],
    ["life_status": QueryOperator.EQ("normal")]
])
```
**❌ 错误写法 2（多条件同 Map）**：
```groovy
QueryTemplate.AND([                // ← 一个 Map 含 2 个 key，运行报 keys exceed 1
    "order_id": QueryOperator.IN(ids),
    "life_status": QueryOperator.EQ("normal")
])
```
**✅ 正确写法（可变参数，每个条件一个独立 Map，无外层 List）**：
```groovy
QueryTemplate.AND(
    ["order_id": QueryOperator.IN(ids)],
    ["life_status": QueryOperator.EQ("normal")],
    ["field_274Al__c": QueryOperator.EQ("8b4we3s9C")]
)
```
**记忆口诀**：`AND(map1, map2, map3)` —— **每个条件一个 `[key: op]` Map 直接当参数，不加外层 `[ ]`**，且**每个 Map 只放 1 个 key**。

### D18. FQL 返回的日期字段是 `com.fxiaoke.functions.time.Date`：读取用 `as Date`、比较用 `.toString()`、回填传 Date 对象
**现象（运行）**：`ClassCast error: Cannot cast object '2026-07-04' with class 'com.fxiaoke.functions.time.Date' to class 'java.lang.Long'`
**根因**：`Fx.object.find` 拉回的日期字段（`payment_time`/`confirm_time`/`create_time` 等）运行时是**纷享自定义的 `com.fxiaoke.functions.time.Date`**（环境内 `Date` 简写即指向它），既不是 `Long`（epoch 毫秒）也不是 `java.util.Date`。该类**没有 `getTime()`，也没实现 `Comparable`**——所以"`as Long`"、`getTime()`、以及代码内直接 `a < b`（静态检查翻译成 `compareTo`）**三条路全失败**（报 `Date#getTime() not found` / `Object#compareTo not found`）。
**✅ 真实生产函数验证过的正确写法**（来自「跟进任务积分人员更新完成值（线索+订单+回款）」陈治彤）：
1. **读取**：`Date ptime = m["payment_time"] as Date`（环境默认 `Date` = 该类，直接 `as Date` 即可，无需全限定名；该真实函数里 `Date x = item["payment_time"] as Date` 可编译可跑）。
2. **比较早晚**：不能用 `getTime()`/`<`。该类的 `toString()` 返回 **ISO 格式**（如 `2026-07-04`），**字典序即时间序**，故用字符串比：
   `if (cur == null || ptime.toString() < cur.toString()) { ... }`（两个 String 比较走 `String#compareTo`，静态检查放行）。
3. **回填 date 字段直接传 Date 对象**：`["first_repayment_time__c": ptime]`——datetime 的 Date 写 date 字段平台自动截断到日（真实函数 `masterDataAB.put("field_date__c", order_timeA)` 用 datetime Date 写 date 字段成功）；**不要**手拼字符串或转 Long。
4. 该类还支持 `withDay(1)`（本月1日）、`+ 1.months - 1.days`（月份加减）等运算；查询时用 `QueryOperator.GTE/LTE(dateObj)` 做日期范围过滤（真实函数大量使用）。
5. 聚合 Map 的 value 类型声明为 `Map<String, Date>` 以通过静态检查。
**典型场景**：计算"首次回款日期"——对每订单取 `PaymentObj`（筛选 `field_274Al__c='8b4we3s9C'` 销售收款 + `life_status='normal'`）的 `MIN(payment_time)`，用 `toString()` 比较取最早，再 batchUpdate 到订单 `first_repayment_time__c`。
**取最早的可靠写法（推荐）**：同一订单有多笔回款时，**必须比日期取最早**——用 `toString()` 字符串比较：`if (cur == null || ptime.toString() < cur.toString()) firstPayMap[oid] = ptime`（用户明确要求跨回款比对早晚，例：一笔 29 号、一笔 30 号要取 29 号）。若确定筛选范围内每订单只有一笔回款，也可直接取第一笔简化（`if (!firstPayMap.containsKey(oid)) firstPayMap[oid] = ptime`），但**不能以此替代"取最早"语义**。

---

## 十一、官方文档入口（排错时查阅）

- APL 总览：https://developer.fxiaoke.com/apl_v2/func-introduce/apl-introduce.html
- context：https://developer.fxiaoke.com/apl_v2/func-apl/api/1.context.html
- Fx.object：https://www.fxiaoke.com/mob/guide/apl_v2/dist/func-apl/api/2.ObjectDataAPI.html
- Fx.org：https://developer.fxiaoke.com/apl_v2/en/func-apl/api/3.OrganizationAPI.html
- FQL 指南：https://developer.fxiaoke.com/apl_v2/en/func-apl/start/fql.html

---

## 十二、本组织提成/计提函数图谱（2026-08 实测）

> 来源：用户逐段贴出的本组织「提成计算基数表」相关 APL 函数（作者陈治彤等）+ 对象字段导出 `D:/Backup/Downloads/对象及字段API (1).xlsx`（17 sheet，覆盖完整提成体系）。
> ⚠️ **这些函数只是提成链路的一部分，不是全貌**（用户明确）。已覆盖：基数表创建 → 跨月结转 → 个人有效回款 → 计提状态 → 团队汇总 → 团队有效回款。尚未覆盖（待补充）：实际计提金额计算、个人提成明细生成、品类/品项级提成落地、提成发放/审批、与薪酬/金蝶对接。分析新函数前不要假设链路已完整。

### 12.1 对象关系图

```
SalesOrderObj(订单) ──审核通过──┐
PaymentObj(回款) ───审核通过───┼─→ commission_base_table__c (计提基数表_主)
变更单 ──────────审批通过────┤      │
退款 ─────────────审核通过────┘      ├─ provision_base_details__c (计提基数明细, 4类 record_type)
                                    ├─ product_item_base__c (品类/项计提基数)
                                    └─ product_provision_base__c (产品计提基数)
                                         │
commission_base_table__c ──触发──→ commission_summary_table__c (提成汇总表_团队)
target_achieved__c (计提目标达成) ─→ 反算 commission_summary_table__c 团队有效回款
valid_collection_amount__c (有效回款业绩设置) ─ 提供 可计提比例 RecordableRatio + 折扣区间
provisioning_conditions_se__c (计提条件设置) ─ 提供 计提规则(金额区间+回款比例)
```

### 12.2 已分析 9 段函数定位（绑定对象 / 作用 / 关键字段）

| # | 函数（用户命名） | 绑定对象 | namespace | 作用 | 关键写/读字段 |
|---|---|---|---|---|---|
| 1 | 订单审核通过创建基数明细 | commission_base_table__c | 流程后动作 | 订单审核通过→建主记录+订单明细 | sales_orderId__c, customer__c, owner, field_6WkL4__c, field_fi91b__c |
| 2 | 回款审核通过创建基数明细 | commission_base_table__c | 流程后动作 | 回款审核通过→建回款明细 | record_type=record_53Jr3__c |
| 3 | 变更单审批通过创建基数明细 | commission_base_table__c | 流程后动作 | 变更审批通过→建变更明细 | record_type=record_lON4W__c |
| 4 | 退款审核通过创建基数明细 | commission_base_table__c | 流程后动作 | 退款审核通过→建退款明细 | record_type=record_917k1__c |
| 5 | 计算个人有效回款额/限价折扣系数 | commission_base_table__c | 流程后动作 | 算个人有效指标 | personal_valid_collection__c, limit_discount_coefficient__c, valid_performance__c |
| 6 | 生成团队提成汇总 | commission_base_table__c | 流程后动作 | 部门聚合写团队字段 | → commission_summary_table__c: team_order_amount__c, team_collection_amount__c, team_monthly_gross_profit__c |
| 7 | 按计提规则计算计提状态 | commission_base_table__c | 流程后动作 | 翻转 provision_status__c | 读 provisioning_conditions_se__c; 写 provision_status__c(option_unprovided__c↔option_provisioned_amount__c) |
| 8 | 计算团队有效回款金额 | target_achieved__c | 流程后动作 | 反算团队有效回款 | 读 valid_collection_amount__c; 写 commission_summary_table__c: team_effective_collection__c, team_effective_collection_exe__c |
| 9 | 更新上月未计提明细到本月 | commission_base_table__c | 流程后动作 | 跨月结转上月未计提明细 | 克隆 provision_base_details__c/product_item_base__c/product_provision_base__c, calc_type__c=option_cross_month_calculation__c |

> 第 6/7/8 段与基数表是「同一主记录上的多个流程后动作」，并行触发；第 9 段在本月新基数创建时把上月未计提明细克隆过来（标记跨月计算）。

### 12.3 计提体系字段 code 表（实测，勿用中文过滤）

**commission_base_table__c（计提基数表）**
| 字段 API | 含义 / 取值 | 说明 |
|---|---|---|
| field_6WkL4__c | 开始日期(本月) | 月份锚点之一 |
| field_fi91b__c | 结束日期(本月) | 月份锚点之一；跨月查找用 `field_fi91b__c < 本月开始` |
| sales_orderId__c | 销售订单 _id | 跨月结转/去重用 |
| customer__c | 客户 _id | |
| owner | 负责人(List) | 取 owner[0] |
| data_own_department | 归属部门(List, 冻结) | 团队汇总按此聚合 |
| assigned_month_date__c | 计提周期月 | 基计8 按此归月 |
| provision_status__c | option_unprovided__c(未计提) / option_provisioned_amount__c(已计提) / 实习试用 | 统计只计已计提+实习试用 |
| provision_commission__c | '1'=方太厨电顾问(接待人) | 团队汇总剔除 provision_commission__c='1' |
| actual_sales_amount__c | 实际销售金额 = order_amount + changed_amount | 分母 |
| actual_collection_amount__c | 实际回款金额 = recovery − refund | 分子/回款净额 |
| personal_valid_collection__c / limit_discount_coefficient__c / valid_performance__c | 个人有效指标 | 基计5 写 |
| recoveryRatio | 实际回款比例 = actual_collection/actual_sales×100 | 基计7 比较用 |

**provision_base_details__c（计提基数明细）**
| 字段 API | 含义 / 取值 | 说明 |
|---|---|---|
| provision_base__c | 父基数表 _id | |
| record_type | default__c(订单) / record_53Jr3__c(回款) / record_lON4W__c(变更) / record_917k1__c(退款) | 4 类明细 |
| calc_type__c | option_cross_month_calculation__c(跨月) / option_individual__c(个人) / option_team__c(团队) | 跨月结转标记 |
| order_amount__c / changed_amount__c / recovery_amount__c / refund_amount__c | 四类金额 | |
| order_date__c / change_date__c / recovery_date__c / refund_date__c | 四类日期 | |
| settlement_gross_profit__c / gross_profitDifference__c / site_management__c / settlement_price__c / complement_rate__c / settlement_differenc__c | 毛利/结算价等 | |
| sales_order__c / change_order__c / recovery_details__c / refund_details__c | 关联原单 | |

**commission_summary_table__c（提成汇总表_团队）**
| 字段 API | 含义 | 由谁写 |
|---|---|---|
| team_order_amount__c | 团队订单金额 | 基计6 |
| team_collection_amount__c | 团队回款金额(回款−退款净额，未乘比例) | 基计6 |
| team_monthly_gross_profit__c | 团队月度毛利 | 基计6 |
| team_effective_collection__c | 团队有效回款(乘可计提比例+折扣区间) | 基计8 |
| team_effective_collection_exe__c | 团队有效回款除个人 | 基计8 |

**valid_collection_amount__c（有效回款业绩设置）**
| 字段 API | 含义 | 说明 |
|---|---|---|
| calc_type__c | option_team__c(团队) / option_individual__c(个人) | 基计8 取 option_team__c |
| performance_coefficient__c | 可计提比例 RecordableRatio | 基计8 乘此/100 |
| disStart / disEnd | 限价折扣区间(开始/结束) | 实际整单折扣需落在区间内 |

**provisioning_conditions_se__c（计提条件设置）**
| 字段 API | 含义 |
|---|---|
| field_j11M8__c | 订单金额开始 |
| field_0x0o4__c | 订单金额结束 |
| payment_terms__c | 合同条款 |
| payment_ratio__c | 回款比例条件 |

**product_item_base__c / product_provision_base__c（品类项/产品计提基数）**
- product_item_base__c：provision_base_table__c, product_category__c, product_item__c, product_order_amount__c, product_quantity__c, order_detail_id__c
- product_provision_base__c：provision_base_table__c, productId__c, quantity__c, sales_unit_price__c, type__c, is_below_price__c, sales_settlement_gross__c, sales_settlement_price__c, original_quantity__c

### 12.4 统计口径 6 条铁律（前台对账必看）

1. **函数读中间表不读原始表**：所有提成统计基于 `commission_base_table__c`（事件拆分后的基数表），不是从 `SalesOrderObj`/`PaymentObj` 重算。前台要一致必须用同表、同过滤。
2. **一单拆四类明细**：订单/回款/变更/退款各自生成 `provision_base_details__c` 一行（record_type 不同），金额分别落在 order/changed/recovery/refund_amount__c。
3. **四套时间锚点**：订单月 / 回款月 / 变更月 / 退款月 各自归月（field_6WkL4__c / field_fi91b__c 等），不统一按订单创建时间。统计月份以基数表月份字段为准。
4. **只算已计提+实习试用**：`provision_status__c ∈ option_provisioned_amount__c(已计提) / 实习试用`；`option_unprovided__c`(未计提) 被排除；且剔除 `provision_commission__c='1'`（方太厨电顾问接待人）。
5. **跨月结转会重复**：上月未计提的同一订单，本月被克隆一份明细（`calc_type__c=option_cross_month_calculation__c`）。前台按订单去重会漏算这部分。
6. **两个"团队回款"不一样**：`team_collection_amount__c`（基计6，回款−退款净额，不乘比例）≥ `team_effective_collection__c`（基计8，再乘 RecordableRatio + 折扣区间校验）。前台若读前者、函数入账用后者，数字必然偏大。
