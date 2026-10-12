# 属性插件处理逻辑说明

## Goal

在创建报价等业务单据时，统一执行属性插件逻辑并将字段准确回填到明细行。

## Trigger

- 用户进行销售合同、报价单、销售订单、商机创建时，明细行上的产品包含属性相关信息时，执行属性插件逻辑
- 如果用户输入信息中没有属性信息，则不处理以下的逻辑

## Inputs

- `product_id`：必须先明确 产品 ID
- 不管输入信息中，是否包含属性信息，都需要执行属性插件逻辑，获取属性信息进行匹配或提示用户要使用哪个属性的属性值

## Steps
- 第一步：根据产品ID获取该产品关联的属性信息，获取属性ID、属性值ID、是否必填、是否多选
```
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_attribute_relation_batch.py --data '{"product_ids":["<产品ID1>", "<产品ID2>"]}'
```
返回结果示例：
```json
{
  "groups": {
    "<产品ID1>": [
      {
        "_id": "<记录ID>",
        "product_id": "<产品ID>",
        "attribute_id": "<属性ID>",
        "attribute_value_ids": "<属性值ID1>|<属性值ID2>",
        "is_required": true,
        "is_multi_selected": true,
        "is_pricing": false,
        "order_number": 1
      }
    ]
  },
  "total": 10
}
```
如果查询回来的结果为空，则结束属性处理逻辑，输出：无需处理属性信息，否则输出：开始处理属性信息

- 第二步：从用户输入信息中，提取与产品关联的属性信息，产品关联的属性及属性值不能超出第一步获取的属性信息范围，如果超出范围，则询问用户属性信息是否准确

- 第三步：数据组装，组装原则如下：
  每一行明细行数据结构如下：
```json
  {
    "product_id": "<产品ID>",
     "attribute": "<属性名1>:<属性值名1>,<属性值名2>;<属性名2>:<属性值名1>", //属性值多选，用逗号分隔，属性之间用分号分隔，一定要注意格式
     "attribute_json": {"<属性1ID>":"<属性值1ID>|<属性值2ID>", "<属性2ID>":"<属性值2ID>"} //属性值多选，用 | 分隔，这个字段值是Map类型，禁止转成String类型
  }
```

`attribute`、和`attribute_json`字段，格式必须严格遵守，禁止随便拼接格式，`attribute_json` 存储的是 Map类型，禁止转成 String 类型


| 类型 | JSON表示 | 示例 |
| --- | --- | --- |
| Map/对象 | {} 直接对象 | {"key1":"value1", "key2":"value2"} |
| 字符串 | "" 包裹 | "{\"key1\":\"value1\"}" |

✅ 正确：attribute_json: {"属性ID1":"属性值ID1|属性值ID2"} → Map类型

❌ 错误：attribute_json: "{\"属性ID1\":\"属性值ID1|属性值ID2\"}" → 字符串类型


- 第四步：执行数据保存时，根据明细行的 `product_id`值相同，将对应的属性信息字段 `attribute`、`attribute_json`追加到明细行数据后，再进行提交保存

## Outputs


## Boundaries


## FailurePolicy