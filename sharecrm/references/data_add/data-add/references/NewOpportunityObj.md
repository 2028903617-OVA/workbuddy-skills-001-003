# NewOpportunityObj（商机）

## 报价数据处理补充

在商机新建流程中，如果上游已构造并回填报价草稿或报价明细数据，必须先完成取价处理，再进入草稿重算。

## 取价处理

插件逻辑处理前，先判断哪些插件需要执行，通过执行以下CLI，根据返回值进行判断

```
sharecrm sales get-config-values --data '{"keys":["cpq","28","is_open_attribute","is_open_nonstandard_attribute"]}'
```
返回值说明：

| key                | value | 对应插件名称   | 执行条件        | 
|--------------------|-------|----------|-------------|
| cpq                |       | BOM插件    | 返回值仅为"1"时执行 |
| 28                 |       | 取价插件     | 返回值仅为"1"时执行 |
| is_open_attribute  |       | 属性插件     | 返回值仅为"1"时执行 |

根据返回值处理顺序如下：
第一步：如果 key = "cpq" 且值为"1"，判断文件 `references/BomService.md` 是否存在，存在则进入BOM处理逻辑，处理完后进入第二步判断

第二步：如果 key = "is_open_attribute" 且值为"1",判断文件 `references/AttributePlugin.md`是否存在，存在则进入属性处理逻辑，处理完后进入第三步判断

第三部：如果 key = "28" 且值为"1"，判断文件 `references/PriceService.md`是否存在，存在则进入取价处理逻辑

确保实现：以上插件处理后，确保`details`节点下的`product_id`不丢失

## 数据结构格式如下
```json
{
  "object_api_name": "NewOpportunityObj",//固定
  "object_data": { 
    //主对象数据的字段信息
  },
  "details": {//如果没有产品信息，可以没有details节点
     //这个key固定
    "NewOpportunityLinesObj": [
      {
        //从对象数据的字段信息
      }
    ],
    //如果有多个从对象，则继续添加
    "XXXObj": [
      {
        //从对象数据的字段信息
      }
    ]
  }
}
```
以上处理完，继续走主流程下的逻辑