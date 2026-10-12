# 取价插件处理逻辑说明

## Goal

在创建报价等业务单据时，统一执行产品取价并将返回字段准确回填到明细行。

## Trigger

- 用户明确要求取价，或业务流程中进入“明细行价格计算/回填”阶段。
- 上游流程已经拿到客户信息、产品列表和数量，准备进行价格计算。
- 已由 BOM 插件回填的明细行不进入本插件流程，仅未进入 BOM 流程的普通产品行触发取价。

## Inputs

- `accountId`：客户 ID。可缺省，缺省时取 `object_data.account_id`。
- `object_api_name`：主对象 API 名称（例如 `QuoteObj`）。可缺省，缺省时取 `object_data.object_describe_api_name`。
- `object_data`：当前主对象数据，最少包含对象标识与客户信息。
- `details`：上下文已构造的从对象明细，必须是 Map。Map 的 Key 是从对象 apiName（如 `QuoteLinesObj`、`SalesOrderProductObj`、`SaleContractLineObj`、`NewOpportunityLinesObj`），Value 是该从对象的明细数组。禁止改成数组。

输入约束：

- 必须把上下文已构造的完整 `details` Map 原样传入脚本，禁止只传普通产品行、禁止拆成数组。
- BOM 行过滤、`simpleResult`、`fullProductList` 组装均由脚本完成，禁止 Agent 手拼取价入参。
- `simpleResult` 固定 `true`，禁止修改，由脚本内部写入，禁止调用方传入或改写。

参数示例：

```json
{
  "accountId": "67bfdf757fae3c0001a12a8c",
  "object_api_name": "QuoteObj",
  "object_data": <上游已构造的 object_data>,
  "details": <上游已构造的 details>
}
```

## Steps

取价与回填只能调用以下 python 脚本，禁止 Agent 手调 `action-get-real-price`，禁止手写回填。

### 1) 调用取价脚本

```bash
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_real_price.py --data '{"accountId":"<客户ID>","object_api_name":"<主对象apiName>","object_data":{...},"details":{"<从对象apiName>":[...]}}'
```

脚本内部处理：

- 剔除 BOM 插件已回填的明细行（行内已存在 `prod_pkg_key` / `bom_core_id` / `bom_id` 任一即剔除），不参与取价。凡带 BOM 标记的行，在过滤时用 `adjust_price` 回写价格：`QuoteLinesObj` 写 `price`，其它从对象写 `product_price`。
- 剔除后若无任何待取价产品，不调用取价接口，仍会处理 BOM 行价格后返回 `details`。
- 请求取价接口的参数格式维持现状：`accountId` + `object_api_name` + `simpleResult: true` + `fullProductList[{productId, amount}]` + `object_data`。`amount` 取明细 `quantity`（缺省再取 `amount`，仍缺省则 `"1"`），类型为字符串。
- 字段回填由脚本完成：`QuoteLinesObj` 与其它从对象规则不同；BOM 行跳过取价回填，即使接口返回中存在可匹配数据也不得赋值。Agent 禁止再手写赋值。
- 取价/BOM 价格回写后，脚本再补销售价与小计：订单/合同 `sales_price = product_price * discount / 100`、`subtotal = sales_price * quantity`；报价先 `sales_price = price * discount / 100`，再 `selling_price = sales_price * extra_discount / 100`、`sales_amount = selling_price * quantity`、`total_amount = sales_price * quantity`。`discount` / `extra_discount` 无值按 100，`quantity` 无值按 1。
- 随后仅对三个主对象写金额，其它主对象不处理：`QuoteObj.quote_product_sum = sum(QuoteLinesObj.sales_amount)`，`quote_amount = quote_product_sum * quote_discount / 100`；`SaleContractObj.amount = sum(SaleContractLineObj.subtotal)`；`SalesOrderObj.product_amount = sum(SalesOrderProductObj.subtotal)`，`order_amount = product_amount * discount / 100`。`quote_discount` / `discount` 无值按 100。
- 返回前脚本按对象名单剥离多余字段（含 `temp_detail_id`、`adjust_price`、`amount`、`order_field` 等），普通行与 BOM 行都剥离。Agent 禁止再手删这些字段，禁止提示用户“移除 temp_detail_id”。

脚本返回：

```json
{
  "status": "READY",
  "object_data": {
    "object_describe_api_name": "QuoteObj",
    "account_id": "67bfdf757fae3c0001a12a8c",
    "quote_product_sum": 100,
    "quote_amount": 100
  },
  "details": {
    "QuoteLinesObj": [
      {
        "product_id": "69e9dc5062d1bd0007ade492",
        "quantity": "1",
        "price": 100,
        "price_book_product_id": "<价目表产品ID>",
        "price_book_product_id__r": "<价目表产品名称>",
        "price_book_id": "<价目表ID>",
        "price_book_id__r": "<价目表名称>",
        "price_book_price": 100,
        "discount": 100
      }
    ]
  }
}
```

`status` 说明：

- `READY`：已回填（含剔除 BOM 后无待取价产品、跳过接口）。
- `EMPTY_PRICE`：接口返回为空，或存在待取价产品找不到可匹配 `product_id`。
- `CLI_ERROR`：取价接口调用失败。
- `INVALID_INPUT`：入参不合法。

### 2) 覆盖上下文 details 与 object_data

仅当 `status == READY` 时：

1. 用脚本返回的 `details` **整节点覆盖**上下文的 `details`，禁止只改部分行、禁止丢字段、禁止再手写一遍回填。
2. 用脚本返回的 `object_data` **整节点覆盖**上下文的 `object_data`，禁止只改部分字段、禁止再手写主对象金额。
3. 覆盖完成后直接进入保存/后续主流程；禁止再整理提交数据、禁止提示移除 `temp_detail_id`。

`status` 非 `READY` 时：不得覆盖上下文 `details` 或 `object_data`，按 FailurePolicy 停止流程。

### 3) 用户特殊要求处理，此时禁止重新执行取价逻辑

1、必须以取价结果为准的字段，禁止修改
- `QuoteLinesObj`的`price`
- `SalesOrderProductObj`的`product_price`
- `SaleContractLineObj`的`product_price`
- `NewOpportunityLinesObj`的`price`

2、用户说修改价格时处理逻辑
特别强调：改价指的都是修改`销售价格`字段
- 比如`NewOpportunityLinesObj`的`sales_price`
- 比如`QuoteLinesObj`的`selling_price`
- 比如`SaleContractLineObj`的`sales_price`
- 比如`SalesOrderProductObj`的`sales_price`

3、需要反算场景
- 改销售价格，需要反算折扣
- 改折扣，需要反算销售价格
- 改小计，需要反算销售价格、折扣

## Outputs

- 已完成价格回填的单据数据（主对象与明细保持可继续后续流程的结构）。
- 上下文 `details` 与 `object_data` 必须被脚本返回值整节点覆盖。
- 每条普通产品明细行至少补齐价格、价目表产品、价目表、折扣及小计相关字段（含 `price_book_id__r`、`price_book_product_id__r`）。
- 必须输出调用前的 `details` JSON，以及覆盖上下文后的新 `details` JSON。

## Boundaries

- 本 skill 只负责“取价 + 回填”，不负责创建写入、不负责草稿重算、不负责提交确认。
- 上游必须保证产品列表、客户信息和对象标识已准备完成。
- BOM 插件已回填的明细行（含 BOM 母件行与子产品行）不再调用取价接口；本插件不得读取、改写或覆盖这些行的任何字段（含价格、折扣、价目表相关字段），这些行的价格以 BOM 插件回填结果为准。
- 禁止将从对象的折扣，用于计算主对象的整单折扣。
- 禁止 Agent 手调取价接口或手写回填；只能调用 `scripts/query_real_price.py`。

## FailurePolicy

- 取价接口失败（`CLI_ERROR`）：停止流程并返回失败原因，不得覆盖上下文 `details` 或 `object_data`。
- 返回为空或找不到可匹配 `product_id`（`EMPTY_PRICE`）：停止流程并提示补充或校正产品信息，不得覆盖上下文 `details` 或 `object_data`。
- 入参不合法（`INVALID_INPUT`）或回填字段结构异常：停止流程并提示检查明细节点结构，不得覆盖上下文 `details` 或 `object_data`。