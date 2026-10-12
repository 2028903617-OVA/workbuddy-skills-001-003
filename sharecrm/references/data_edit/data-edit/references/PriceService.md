# 取价插件处理逻辑说明

## Goal

在创建报价等业务单据时，统一执行产品取价并将返回字段准确回填到明细行。

## Trigger

- 用户明确要求取价，或业务流程中进入“明细行价格计算/回填”阶段。
- 上游流程已经拿到客户信息、产品列表和数量，准备进行价格计算。

## Inputs

- `accountId`：客户 ID。
- `object_api_name`：对象 API 名称（例如 `QuoteObj`）。
- `fullProductList`：产品与数量列表，最少包含 `productId`、`amount`。
- `object_data`：当前主对象数据，最少包含对象标识与客户信息。

参数示例：

```json
{
  "accountId": "67bfdf757fae3c0001a12a8c",
  "object_api_name": "QuoteObj",
  "fullProductList": [
    {
      "productId": "69e9dc5062d1bd0007ade492",
      "amount": "1"
    }
  ],
  "object_data": {
    "object_describe_api_name": "QuoteObj",
    "account_id": "67bfdf757fae3c0001a12a8c"
  }
}
```

## Steps

### 1) 调用取价接口

执行：

```bash
sharecrm sales product action-get-real-price -d '<按 Inputs 组装后的 JSON 参数>'
```

### 2) 处理取价返回并回填明细
前提条件：如果取价接口返回为空或找不到可匹配 `product_id` 的产品，不做以下赋值处理
1. 场景A：仅适用于`QuoteLinesObj`对象赋值处理逻辑
- 产品匹配原则：`quote_create_data.details`节点下明细行的 `product_id` 必须与返回结果 `newRst` 节点的 `product_id` 一致
- 将接口返回的 `selling_price` 赋给明细行 `price`字段
- 将接口返回的 `_id` 赋给明细行 `price_book_product_id` 字段
- 将接口返回的 `display_name` 或 `name` 赋给明细行 `price_book_product_id__r` 字段
- 将接口返回的 `pricebook_id` 赋给明细行 `price_book_id` 字段
- 将接口返回的 `pricebook_id__r` 赋给明细行 `price_book_id__r` 字段
- 将接口返回的 `discount` 赋给明细行 `discount` 字段
- 将接口返回的 `price_book_subtotal` 赋给明细行 `price_book_subtotal` 字段， 如果对象描述里没有此字段，忽略赋值
- 将接口返回的 `price_tiered_record` 赋给明细行 `price_tiered_record` 字段  如果对象描述里没有此字段，忽略赋值
- 若明细中不存在对应字段，直接补充该字段后再写值。
2. 场景B：仅适用于非`QuoteLinesObj`对象赋值处理逻辑
- 产品匹配原则：`quote_create_data.details`节点下明细行的 `product_id` 必须与返回结果 `newRst` 节点的 `product_id` 一致
- 将接口返回的 `selling_price` 赋给明细行 `product_price` 字段
- 将接口返回的 `_id` 赋给明细行 `price_book_product_id` 字段
- 将接口返回的 `display_name` 或 `name` 赋给明细行 `price_book_product_id__r` 字段
- 将接口返回的 `pricebook_id` 赋给明细行 `price_book_id` 字段
- 将接口返回的 `pricebook_id__r` 赋给明细行 `price_book_id__r` 字段
- 将接口返回的 `discount` 赋给明细行 `discount` 字段
- 将接口返回的 `pricebook_price` 赋给明细行 `price_book_price` 字段
- 将接口返回的 `price_book_subtotal` 赋给明细行 `price_book_subtotal` 字段， 如果对象描述里没有此字段，忽略赋值
- 将接口返回的 `price_tiered_record` 赋给明细行 `price_tiered_record` 字段  如果对象描述里没有此字段，忽略赋值
- 若明细中不存在对应字段，直接补充该字段后再写值。

## Outputs

- 已完成价格回填的单据数据（主对象与明细保持可继续后续流程的结构）。
- 每条明细行至少补齐价格、价目表产品、折扣及小计相关字段。
- 输出显示取价匹配到的价目表名称，pricebook_id__r


## Boundaries

- 本 skill 只负责“取价 + 回填”，不负责创建写入、不负责草稿重算、不负责提交确认。
- 上游必须保证产品列表、客户信息和对象标识已准备完成。

## FailurePolicy

- 取价接口失败：停止流程并返回失败原因。
- 返回为空或找不到可匹配 `product_id`：停止流程并提示补充或校正产品信息。
- 回填字段结构异常：停止流程并提示检查明细节点结构。