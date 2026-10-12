---
name: "sfa-product-attribute-tool"
description: "仅用于产品关联属性查询、产品关联属性、产品解除属性关联这三个场景。当用户询问某产品关联了哪些属性、产品属性关联关系、查看产品关联属性，或要求产品关联属性、或要求产品解除属性关联时使用；不要用于普通产品详情、产品价格、产品多单位、库存、分类或其他产品操作。"
apiName: "sfa_product_attribute_tool"
---
# 产品与属性关联关系处理工具

## Scope

本 Skill 只处理以下三个场景：

| 场景         | 典型问法                                 |
|------------|--------------------------------------|
| 查询产品关联哪些属性 | 产品 A 关联了哪些属性 / 查看产品 A 的属性关联          |
| 产品进行属性关联   | 产品 A 要关联颜色这个属性 / 产品 A 关联颜色、尺寸、体积这些属性 |
| 产品解除属性关联  | 产品 A 解除与颜色 的关联关系 / 把产品 A 的某个属性关联删掉   |

不处理：

- 普通产品详情查询
- 产品价格、价目表、询价
- 产品多单位转换
- 产品分类、库存、上下架或其他产品管理操作
- 属性本身的新增、编辑、删除


常见对象apiName说明：

| 对象中文名称        | apiName                   |
| ----------------  | ------------------------- |
| 产品               | ProductObj                |
| 属性               | AttributeObj              |
| 属性值             | AttributeValueObj         |
| 产品属性关联关系     | ProductAttributeRelationObj |


## Required Discovery

先区分场景，然后按场景的Workflow严格执行，并且需要严格遵守Boundaries里的规则。

查询产品、属性、属性值的ID时，只能调用以下python脚本，避免Agent多次调用sharecrm工具查询数据，该工具支持同时查询多个对象的数据
```
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_id_by_name_batch.py --data '{"ProductObj":["产品A","产品B"], "AttributeObj":["属性A","属性B"], "AttributeValueObj":["属性值A","属性值B"]}'
```
当没有找对应数据时，禁止随意寻找工具，务必提示用户，输入正确的名称，然后再查询ID


## 场景A：查询产品关联哪些属性

### Workflow
- 步骤1：明确产品ID
    从输入信息中，提取所有产品名称，再获取产品ID，如果上下文已经获取过产品ID，则直接进入步骤2

- 步骤2：根据产品ID查询产品关联属性
```
sharecrm data record query-by-sql --need_count true --raw --sql "SELECT _id, product_id, attribute_id, attribute_value_ids, is_required, is_multi_selected, is_pricing, order_number FROM ProductAttributeRelationObj WHERE product_id IN (<产品ID>, <产品ID>) AND life_status = 'normal' ORDER BY product_id, create_time LIMIT 20"
```

- 步骤3：返回结果展示处理
1.以表格的形式进行展示
2.以产品分组的方式进行展示
3.没有关联属性的产品独立一个表格展示，分组内容：未关联属性的产品，表头：产品名称，表体：具体的产品名称，有多个产品就展示多行，禁止一个产品一个表格展示



## 场景B：产品进行属性关联
### Workflow
- 步骤1：明确产品ID
    从输入信息中，提取所有产品名称，再获取产品ID

- 步骤2：明确属性 ID 和属性值ID
  从输入信息中，提取所有属性名称，再获取属性ID，
  情况一：如果输入信息中没有指定属性值信息，询问用户是否关联所有属性值还是指定属性值，以弹窗选择的形式进行询问，用户指定属性值时，属性值需要支持多选；
  情况二：如果用户指定属性值，需要检查该属性值是否属于要关联的属性。如果属性值不存在，提示用户是否选择该属性下的其它属性值

  禁止操作说明：场景B属于产品增量关联属性，严禁删除产品已关联的属性

- 步骤3：如果有指定属性对应的属性值，则需要获取属性值ID

- 步骤4：组装产品关联属性的参数，请求参数格式如下：
```json
{
  "product_ids": [<产品ID>, <产品ID>],//产品ID，至少有一个产品ID
  "attribute_infos": [
    {
      "attribute_Id": <属性ID>, // 属性ID，不允许为空
      "value_Ids": [<属性值ID>, <属性值ID>],//不允许为空
      "is_pricing":  true, // 是否参与定价，默认为true,除非用户要求不参与定价
      "default_value_id": <属性值ID>, //指定属性值ID
      "is_required": false, // 是否必选，默认为false，除非用户要求必填
      "is_multi_selected": false // 是否多选，默认为false，除非用户要求多选
    }
  ]
}
```

- 步骤5：调用产品关联属性接口

```
sharecrm sales product inc-assoc-attribute --data <步骤4组装的参数>
```

- 步骤6：展示产品关联属性结果
    必须以表格形式展示，参考场景A

## 场景C：产品解除属性关联
### Workflow

- 步骤1：明确产品ID
    从输入信息中，提取所有产品名称，再获取产品ID

- 步骤2：查看产品是否关联了要解除的属性，如果没有要解除的属性，提示用户，没有要解除的属性，停止后续的操作，如果存在要解除的属性，则进入下一步

- 步骤3：明确属性 ID 和属性值ID
  从输入信息中，提取所有属性名称，再获取属性ID

- 步骤4：组装产品关联属性的参数，请求参数格式如下：

```json
{
  "product_ids": [<产品ID>, <产品ID>],//产品ID，不允许为空
  "attribute_ids": [<属性ID>, <属性ID>] // 属性ID，不允许为空
}
```

- 步骤5：调用产品解除属性关联接口

```
sharecrm sales product dis-assoc-attribute --data <步骤3组装的参数>
```

- 步骤6：展示产品关联属性结果
  必须以表格形式展示，参考场景A

## Boundaries
- 该SKILL只处理场景A 、场景B 、场景C，不处理其它场景

## FailurePolicy
- 通过指定的命令关联属性失败时，禁止使用其它命令进行操作
- 通过指定的命令解除属性关联失败时，禁止使用其它命令进行操作