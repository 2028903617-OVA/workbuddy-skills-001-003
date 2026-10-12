# BomCoreObj（产品组合｜组合 | CPQ）

新建产品组合时，**查产品 ID 与补齐明细字段**必须走脚本，禁止 Agent 手查 ProductObj 或手算序号/层级字段。

## 严格执行步骤

1. 从用户输入识别父项产品、子件清单、分组、层级（`level_key`）；分组不用查产品。
2. 调用 `prepare_bom_create.py` 完成产品解析与字段补齐（见下文）。
3. 不用校验组合/明细是否已存在（支持多版本）。
4. 若步骤 1 拿不到 `BomCoreObj` / `BOMObj` 对象描述，终止新建。
5. 脚本返回 `READY` 后，必须先把 `preview` 给用户确认，**未明确确认前禁止创建**。

## 必收集输入

缺失时先问用户，再调脚本：

- 父项产品：名称或已确认 ID
- 子件列表：至少 1 条（含分组）
- 分组：通过名称/备注识别，入参标 `isGroup: true`
- 层级：有序号列时写入 `level_key`（如 `1`、`1.2`、`1.2.3`）；没有则整表按一级处理

## 调用脚本（必须）

```bash
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/prepare_bom_create.py --data '<JSON>'
```

也可用文件：`--data @payload.json`。

### 入参

```json
{
  "parent": { "name": "wsh组合" },
  "children": [
    { "name": "华为手机", "level_key": "1.1" },
    { "name": "配件分组", "level_key": "1.2", "isGroup": true },
    { "name": "Iphone16", "level_key": "1.2.1", "amount": 1, "price_mode": "2" },
    { "name": "耐克跑鞋", "level_key": "1.2.2", "price_mode": "1", "adjust_price": 12 }
  ]
}
```

说明：

- 已确认产品 ID 时可写 `"product_id": "<id>"`，脚本跳过该条名称查询。
- 分组只传 `name` + `isGroup: true`（及 `level_key`），不要传 `product_id`。
- `price_mode`：`1`=配置价格，`2`=价目表价格；未指定则产品 `adjust_price` 默认 `0`。

### 返回 status 与处理

| status | 含义 | Agent 动作 |
|---|---|---|
| `READY` | 产品已唯一命中，字段已补齐 | 展示 `preview`，确认后用 `object_data` + `details.BOMObj` 继续创建 |
| `PRODUCT_NOT_RESOLVED` | 父项/子件未命中或多命中 | 按 `unresolved` 请用户确认，禁止猜测 |
| `LEVEL_BROKEN` | `level_key` 父子断裂 | 按 `level_issues` 请用户补全/修正，禁止降级猜测 |
| `EMPTY_CHILDREN` | 子件为空 | 要求补充子件 |
| `INVALID_INPUT` / 含 `error` | 入参或 CLI 异常 | 如实告知，修正后重跑 |

`READY` 时脚本已完成：

- 解析父子产品 ID（分组不查）
- `amount` / `adjust_price`（分组均为 `null`；价目表模式 `price_mode=2` 时 `adjust_price` 强制 `null`）
- 分组标记：`isGroup` / `isFake` / `label`
- `order_field`（产品与分组都写，同级从 1 递增）
- `rowId` / `parent_rowId`（由 `level_key` 映射；提交前已去掉 `level_key`）
- `preview` 树形预览文本
- `defaults_used`：标明哪些行用了默认 `amount=1` / `adjust_price=0`

## 必要校验（脚本外仍须遵守）

- 父项未命中/多命中：停止，不得继续创建。
- 子件产品未命中/多命中：逐条挂起确认，不得猜测。
- 子件 0 条：停止并要求补充。
- 层级断裂：用户补全前禁止创建。
- 数据顺序：按来源数据顺序传入 `children`，脚本保持该顺序。

## 创建前确认（必须）

用脚本返回的 `preview` 向用户确认：

1. 父项产品是否正确（名称 + ID）
2. 子件清单与层级是否正确
3. 默认值是否接受（见 `defaults_used`）

用户未明确确认前，禁止执行创建。

## 组装新建数据结构格式如下
```json
{
  "object_api_name": "BomCoreObj",//固定
  "object_data": { 
    //主对象数据的字段信息
  },
  "details": {
     //这个key固定
    "BOMObj": [
      {
        //从对象数据的字段信息

      },
      {
        //从对象数据的字段信息
      }
    ]
  }
}
```

## 提交注意

- `details.BOMObj` 直接使用脚本 `READY` 返回值；不要再手改 `order_field` / `rowId` / `parent_rowId`。
- `isGroup` / `rowId` / `parent_rowId` / `label` / `isFake` 即使不在明细描述中，也直接带入新建数据。
- 主对象 `object_data.product_id` 使用脚本返回的父项 ID，再合并表单其它可写字段后保存。
