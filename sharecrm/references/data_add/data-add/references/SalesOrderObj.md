# SalesOrderObj（销售订单）
必须先从上下文收集的数据项，如果缺失以下数据项，必须让用户确认
- 客户 account_id    查询数据时用 AccountObj 对象
- 产品 product_id    查询数据时用 ProductObj 对象
- 数量 quantity

查询客户和产品ID时，只能调用以下python脚本，避免Agent多次调用sharecrm工具查询数据
```
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_id_by_name_batch.py --data '{"ProductObj":["产品A","产品B"], "AccountObj":"客户名称A"}'
```
当客户没有找到时，禁止随意寻找工具，务必提示用户，输入正确的客户名称，然后再查询客户ID

当部分产品名称没有找到时，禁止随意寻找工具，务必提示用户，输入正确的产品名称，然后再查询产品ID


## 必填字段忽略处理
- 除以上三个字段外，后面有必填字段校验，禁止询问，直接跳过`form_fields` 中 is_required=true的校验，禁止收集必填字段信息，禁止自动随意赋值，必填字段会在创建页面进行赋值


## 插件处理逻辑

插件逻辑处理前，先判断哪些插件需要执行，通过执行以下CLI，根据返回值进行判断

```
sharecrm sales get-config-values --data '{"keys":["cpq","simple_cpq","28","is_open_attribute","is_open_nonstandard_attribute"]}'
```
返回值说明：

| key                | value | 对应插件名称   | 执行条件        | 
|--------------------|-------|----------|-------------|
| cpq                |       | BOM插件    | 返回值仅为"1"时执行 |
| simple_cpq         |       | BOM插件    | 返回值仅为"1"时执行 |
| 28                 |       | 取价插件     | 返回值仅为"1"时执行 |
| is_open_attribute  |       | 属性插件     | 返回值仅为"1"时执行 |

根据返回值处理顺序如下：

第一步：如果 key = "is_open_attribute" 且值为"1",判断文件 `references/AttributePlugin.md`是否存在，存在则进入属性处理逻辑，处理完后进入第二步判断，

第二步：如果 key = "cpq" 或 key = "simple_cpq" 且值为"1"，判断文件 `references/BomService.md` 是否存在，存在则进入BOM处理逻辑，处理完后进入第三步判断

第三步：分两个场景
- 场景A：如果 key = "28" 且值为"1"，判断文件 `references/PriceService.md` 是否存在，存在则进入取价处理逻辑，处理完后进入第三步判断。
- 场景B：如果 key = "28" 且值为"0"，分支1: 并且用户没有指定价格，直接进入第三步判断。 分支2：用户指定了产品价格，赋值给`SalesOrderProductObj`.`product_price`,如果用户没有指定产品折扣，则`SalesOrderProductObj`.`discount`:"100"

**插件回填字段必须原样保留**。确保实现：以上插件处理后，提交用的`details`必须就是插件处理后的最终明细数组——`product_id`与各插件回填字段（BOM 插件映射的`bom_id`/`bom_core_id`/`bom_core_id__r`/`prod_pkg_key`/`parent_prod_pkg_key`/`root_prod_pkg_key`/`related_core_id`/`new_bom_path`/`price_per_set`/`price_book_product_id`/`price_book_id`/`discount`/`price_book_subtotal`/`price_tiered_record`，取价插件回填的`product_price`/`price_book_product_id`/`price_book_id`/`discount`/`price_book_price`/`price_book_subtotal`/`price_tiered_record`，属性插件返回的`attribute`/`attribute_json`）全部保留，不得丢失、不得改写，即使不在 `form_fields`、即使只读，也必须原样保留进 `details` 提交，不得丢弃、不得改写。

注意：属性插件必须先于BOM插件执行，因为属性处理结果会影响BOM取价与子件展开。

## 数据结构格式如下
```json
{
  "object_api_name": "SalesOrderObj",//固定
  "object_data": { 
    //主对象数据的字段信息
  },
  "details": {
     //这个key固定
    "SalesOrderProductObj": [
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