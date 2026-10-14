# 价目表明细 OpenAPI 直写

> ⚠️ 本文件含内部标识符（appId / ea / userId / 出口 IP / 记录 ID / 字段 API 名），**属内部资料，勿外发、勿用于脱敏产出**。
> 结论依据：2026-10-13 实测（建 1 条 + 删 1 条，回读闭环）。**旧结论「价目表明细禁止 Agent 写入（`DISABLED_OBJECT`）」已作废。**
> ★ **v1.9.0（2026-10-13）起，直写已是能力 1 的默认落地方式**（配合 `query_pricebook.py` 阶段 2 `--apply`）；
> 「生成导入文件 → 人工导入」降级为可选备用（用户明确要文件时才用）。

## 0. 何时用 / 什么不能做

| | 说明 |
|---|---|
| ✅ 适用 | 能力 1 已算好的行（产品已匹配、价格已核、大类/品项已定），要**直接落库**、免掉人工导入 |
| ⛔ 前置 | **必须用户两次动作**：① 先跑阶段 1 只读查询；② 拿到「新建 X 行 / 更新 Y 行」结果**明确确认后**再加 `--apply`；凭证文件在位；目标价目表启用状态已确认 |
| ⛔ 不适用 | **销售订单及任何含业务插件的对象** —— 见 §7；产品主数据**不得新建**（见 §2 注） |

「先查后确认」是硬流程：`query_pricebook.py` 不加 `--apply` 只打印报文与「[只读] 未写入」，**永远不会偷偷写**。

## 1. 凭证与鉴权

- **凭证文件（落盘、不手抄）**：`C:\Users\Administrator\.workbuddy\fxiaoke-app-003.json`
  ```
  {appId: FSAID_1326cf8, appSecret: <…>, permanentCode: <…>,
   domain: https://open.fxiaoke.com, ea: hzxfdq, userId: 1775}
  ```
- **★ 必须走新版 header 鉴权**：`authorization: Bearer <token>` + `x-fs-ea: hzxfdq` + `x-fs-userid: 1775`。
  旧版 body 通道（`corpAccessToken` / `corpId` / `currentOpenUserId`）对本应用返回 `10006` —— **两套鉴权不可混用**。
- 取 token（只读）：`openapi_client.py token --cred-file <上面那个文件>` → `errorCode=0` 即有效。
- 公网出口 IP 须在自建应用白名单内（当前 `122.224.175.110`，**动态 IP**，变了要重配白名单，否则报 `20014`）。

> **现成客户端（已内置通道 B 命令，默认 dry-run）**：后台开发空间 `工具/sharecrm-tools/openapi_client.py`
> ```
> # 1) 取 token（只读，验证凭证）
> python openapi_client.py token --cred-file C:/Users/Administrator/.workbuddy/fxiaoke-app-003.json
>
> # 2) 预演（不联网、不落库）——先看报文对不对
> python openapi_client.py create-pricebook-product --cred-file <凭证> \
>   --pricebook-id <价目表_id> --product-id <产品_id> --selling-price 523 \
>   --product-category 7 --product-item option_gree_living_appliances__c --brand 格力
>
> # 3) 用户二次确认后，才加 --execute 真提交
> python openapi_client.py create-pricebook-product ... --execute
>
> # 4) 撤回
> python openapi_client.py delete --cred-file <凭证> --object PriceBookProductObj --id <明细_id> --execute
> ```
> 其他子命令：`token` / `describe` / `upload` / `create-payment` / `create-order`。
> ⚠️ `get`（`/cgi/crm/v2/data/get`）**暂不可用**（报 `50009 parameter is null`，见 §6）→ **回读改用 CLI `sharecrm data record get-by-id`**。
> ⚠️ `--execute` 默认**不带**（铁律 1）；不带时命令只打印将发送的报文。

## 2. 最小必填字段（实测只需 4 个）

| 字段 | 必填 | 说明 |
|---|---|---|
| `pricebook_id` | ✅ | 价目表（master_detail） |
| `product_id` | ✅ | 产品（object_reference）—— **只沿用金蝶已同步的产品，绝不新建 `ProductObj`** |
| `record_type` | ✅ | 恒 `default__c`（该对象仅此一个选项） |
| `pricebook_sellingprice` | ✅ | 价目表售价 —— ★ **默认值表达式 `$product_id__r.price$`，API 通道不自动算，必须显式传** |
| `field_yy0j1__c` 产品大类 | 视组织 | select_one，传**码值** |
| `product_item__c` 产品品项 | 视组织 | select_one，传**码值** |
| `field_xv1Bw__c` 品牌 | 视组织 | text，直接填文本 |
| `discount` 折扣 | ❌ | percentile，普通默认值 `"100"` → **API 会自动带出 100.00%**，可省略 |
| `pricebook_price` | — | **formula**（`sellingprice × discount`），服务端自动算 |
| `name` | — | auto_number，自动生成 |
| 其余（产品名称/编码/单位/条码/规格/上下架/标准价） | — | **quote 引用字段**，只读自动带出，别传 |

> ★★ **铁律：「普通默认值」走 API 生效；`default_is_expression: true` 的「默认值表达式」不生效。**
> 典型受害者：`pricebook_sellingprice`（本对象）、`OrderPaymentObj.field_xt8A2__c`、`PaymentObj.field_081hm__c`、`ProductObj.price`。
> 排查：`sharedev_api.py field PriceBookProductObj <字段>`，会把这类字段标上 `★默认值表达式`。

## 3. 码值获取（select_one 填 label 会被拒）

`sharedev_api.py field PriceBookProductObj <字段>` → 读 `options[].value`。实测例：

| 字段 | label | **提交值** |
|---|---|---|
| `field_yy0j1__c` 产品大类 | 生活电器 | `7`（文本"生活电器"会被拒） |
| `product_item__c` 产品品项 | 格力生活电器 | `option_gree_living_appliances__c` |
| `field_xv1Bw__c` 品牌 | 格力 | `格力`（text 字段，直接填文本） |

**例外**：`ProductObj.category` 传的是**路径文本**（如 `K_大松/K_大松小家电/K-大松电风扇`），不是码值。

## 4. 写入调用

`POST {domain}/cgi/crm/v2/data/create`（新版 header 鉴权）

```json
{
  "data": {
    "dataObjectApiName": "PriceBookProductObj",
    "data": {
      "pricebook_id": "<价目表 _id>",
      "product_id": "<产品 _id>",
      "record_type": "default__c",
      "pricebook_sellingprice": 523,
      "field_yy0j1__c": "7",
      "product_item__c": "option_gree_living_appliances__c",
      "field_xv1Bw__c": "格力"
    }
  }
}
```

成功 → `errorCode=0` + 返回 `dataId`；服务端自动带出 quote 字段与 `pricebook_price`。

## 5. ★ 写前必做：查重

用「`product_id` + `pricebook_id`」**双条件**查已有明细；**已存在就不得再建**（同一产品在同一价目表只应有一行）。

> ⚠️ **查重结果禁止用 `tail` / `head` 截断**——必须看 `returnedCount` / `totalNumber` 并完整读取命中行。
> 截断会造成「系统里没有这个产品/明细」的**误判**，进而在错误的判断上继续行动。2026-10-13 已踩过这次坑。

## 6. 撤回：删除

`POST {domain}/cgi/crm/v2/data/delete`

```json
{ "data": { "dataObjectApiName": "PriceBookProductObj", "idList": ["<明细 _id>"] } }
```

- ⚠️ 只认 **`data.idList`（数组）**；写 `data.dataId` / `data.dataIds` / `data.ids` 会报 **`50009 删除数据不能为空`**；`/cgi/crm/v2/data/deleteById` 路径**不存在**（报 `10006 ... is not exists`）。
- 价目表明细**可以直接删除**（多数对象须先作废再删）。
- 删后**回读确认为空** → **回退闭环成立**。

> ⚠️ **回读请用 CLI，不要用 `openapi_client.py get`**：
> ```
> sharecrm data record get-by-id --object_api_name PriceBookProductObj --id <明细_id>
> ```
> 返回 `{}` 即已删除成功（实测：删除后回读 `{}`，且双条件查重回 `totalNumber=0`）。
>
> **`openapi_client.py get`（`/cgi/crm/v2/data/get`）当前不可用**：`dataId` / `dataIds` / `id` / `idList` / `ids` / `dataIdList` / 数组形态 / 附加 `fieldList`·`fields`·`fieldApiNames` 等共 11 种写法**一律** `50009 parameter is null`；同族路径 `/data/getById`、`/data/detail`、`/data/queryById` 均 `10006 … is not exist`。（2026-10-13 实测；`dataObjectApiName` 传对时不再报 10006，说明对象名识别 OK、缺的是另一个未知名参数。）→ 待查官方文档后再修，先用 CLI 回读。

## 7. ★★ 边界：不延伸到销售订单

`SalesOrderObj` 的拒绝码含 `DOMAIN_PLUGIN_EXISTS`（price-service / multi-unit / bom / attribute / change_price）+ `UI_EVENT_EXISTS` —— 属**业务插件 / 页面事件依赖**：取价与多单位插件只在 CRM 页面执行，OpenAPI 绕过会**静默产生错价**（写成功但是错的）。

**判据一句话：拒绝码里有没有 `DOMAIN_PLUGIN_EXISTS` / `UI_EVENT_EXISTS`。有 = 不能绕；没有 = 换通道可解。**

（回款 `PaymentObj` / 价目表明细 = 仅 `DISABLED_OBJECT` = 纯通道级 → 可换通道；销售订单 = 有插件码 → 仍须页面手工录单。）

## 8. 变更台账（写完必补）

`工具/sharecrm-tools/change_ledger.py add ...` —— 7 列：时间(系统) / 动作 / 对象·记录ID / 改了什么 / 依据(用户原话) / 结果 / 回退方式；`verify` 应输出 0 问题。
规则：①先确认 → 再写 → 写完**立即**补记 ②时间取系统真实值 ③**被拦未写入的尝试也要记**（`write_db=false`）④每条必含回退方式 ⑤只追加不改写。

## 9. 自检清单

- [ ] 已取得用户**二次确认**（明确说了改什么、影响哪条记录）
- [ ] 查重通过：`product_id + pricebook_id` 无既有行（且查重未经截断）
- [ ] `pricebook_sellingprice` **显式传值**、非空
- [ ] `record_type = default__c`
- [ ] 所有 select_one 字段传的是**码值**，不是 label
- [ ] 产品是**已同步**的主数据（未新建）
- [ ] 写完已**回读**核对（价格 / 产品 / 价目表 / 分类）
- [ ] 变更台账已补、`verify` 通过
- [ ] 已告知用户**撤回方式**（`data/delete` + `data.idList`）
