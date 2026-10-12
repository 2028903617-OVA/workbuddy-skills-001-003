# BomService

## Goal

在创建报价、销售订单、销售合同等业务单据时，识别并处理 BOM 产品，调用 BOM 树构建接口，并将接口返回字段安全回填到从对象明细行。

## Trigger

- 本插件由入口对象（QuoteObj / SalesOrderObj / SaleContractObj 等）在特性 key `cpq` 或 `simple_cpq` 返回值为 `"1"` 时才触发进入；进入本插件即视为门控已通过，无需重复查询特性开关。

## Inputs

- `accountId`：客户 ID。
- `partnerId`：合作伙伴 ID，可选。
- `objectApiName`：主对象 API 名称，如 `QuoteObj`、`SalesOrderObj`。
- `detailObjectApiName`：从对象 API 名称，如 `QuoteLinesObj`、`SalesOrderProductObj`。
- `dataList`：当前从对象的完整明细数组，包含 BOM 产品和普通产品；如果属性插件已返回 `attribute_json`，对应明细行必须携带该字段，且值保持 Map/对象类型。
- `objectData`：当前主对象数据。
- `productId` / `productIds`：待识别产品 ID；批量值优先。未显式提供时，从 `dataList[].product_id` 去空、去重、保序提取。

输入约束：

- `quantity` 缺失时按上游明细已有值处理；仍缺失时默认使用 `"1"`，参与乘法运算时按数值 1 计算。
- 当用户要求"母件及所有子产品下单"(如"用海尔空调及所有子产品下单"、"连同子产品一起下单"、"及全部明细")，或步骤 1 查询到 `BomCoreObj.category == standard` 时，上游传入的 `dataList` 可能只含母件明细行、缺少子产品行；此时必须先执行步骤 3 子产品展开，再调用 `handleBomTree`。

## Steps

### 1. 查询并确认 BomCoreObj

按产品 ID 一次性批量查询 `BomCoreObj`，避免逐个产品多轮查询。查询时只能调用以下 python 脚本，禁止 Agent 手拼 SQL：

```bash
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_bom_batch.py --mode core --data '{"product_ids":["<产品ID1>","<产品ID2>"]}'
```

脚本返回按输入 key 分组的命中记录（`groups` + `total`）：每个 key 对应该 key 的记录数组，0 条=未命中、1 条=唯一命中、多条=多候选。每条记录含 `_id`、`name`、`category`。

对每个输入 key 独立处理：

- 命中 0 条：该明细不进入 BOM 流程，保留原始明细继续走普通产品处理。
- 命中 1 条：使用该记录 `_id` 作为 `bom_core_id`，使用 `name` 作为 `bom_core_id__r`。
- 命中多条：
  - 如果用户已指定 BOM 版本、状态或其他可唯一定位的信息，直接选中对应记录。
  - 否则必须让用户选择；未选定前不得继续调用 `handleBomTree`。
- 查询失败：停止 BOM 流程并返回失败原因。

### 2. 执行二次校验

进入 BOM 流程前必须完成以下校验：

1. 剔除所有 0 命中的明细。
2. 如果剔除后没有任何 `bom_core_id`，直接结束 BomService，不调用 `handleBomTree`。
3. 不同输入 key 不允许映射到同一个 `bom_core_id`；重复时停止流程并提示。
4. 每条进入 BOM 流程的明细都必须有唯一的 `bom_core_id` 和 `bom_core_id__r`；缺失时停止流程并提示。

### 3. 子产品展开(母件及所有子产品下单)

触发决策（自上而下取首个命中行）：

| 条件 | 处理 |
| --- | --- |
| 上游 `dataList` 已包含完整子产品行 | 跳过本步骤 |
| 用户明确要求"母件及所有子产品"类表达（"及所有子产品"、"连同子产品一起"、"及全部明细"、"及所有明细"） | 展开 |
| 任一已确认母件 `category == standard`（标准 BOM） | 自动展开，无需用户额外指令 |
| 以上均不满足 | 跳过本步骤，不得擅自展开 |

`category` 缺失或取值非 `standard` 时，不作为自动展开依据。

执行要求：

- **调用脚本展开**：对每条已确认 `bom_core_id` 的母件明细，统一调用以下 python 脚本完成子产品查询、复用 BOM 递归展开（含防环与深度上限）和数量缩放；禁止 Agent 手拼 SQL 或手写展开逻辑：

```bash
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_bom_batch.py --mode expand --data '{"mothers":[{"bom_core_id":"<已确认母件1的bom_core_id>","quantity":"<母件行数量>"},{"bom_core_id":"<已确认母件2的bom_core_id>","quantity":"1"}]}'
```

- **脚本行为**（脚本已实现，Agent 不重复执行）：
  - 按 `core_id` 批量查询 `BOMObj` 子产品节点（组内已按树形排序：父级在前、子级在后，同级按 `order_field` 升序）；沿 `related_core_id` 递归展开复用 BOM，以本次全部已确认母件的 `bom_core_id` 为种子按祖先链判环，深度硬上限 10 层（母件为第 1 层，每下钻一层复用 BOM 加 1）；同一 `related_core_id` 被不同母件或不同分支合法复用时不视为环，按各自父行数量独立展开。
  - 数量规则：若 `BOMObj.amount_any` 为 `true`，`子产品数量 = BOMObj.amount`（不随母件缩放）；否则 `子产品数量 = BOMObj.amount × 上一层行最终数量`（递归时以引用行的最终数量作为母件数量）；`amount` / 母件数量缺失按 `"1"`，`amount_any` 缺失按 `false`。
  - 展开结果为一次性快照：若其后母件（或任一层引用行）数量发生变更，必须用新数量重新调用脚本展开，禁止直接沿用旧子产品行数量。

- **脚本返回**：`status == READY` 时含 `groups`（键为母件 `bom_core_id`，值为按深度优先排好的新增子产品行数组）：普通子产品行含 `product_id`、`product_id__r`、`quantity`；复用 BOM 节点行额外含 `bom_core_id`（取值 ← 节点的 `related_core_id`，不带 `bom_core_id__r`），且其子产品行紧随该节点行之后。某母件无子产品时对应空数组，保留母件明细原样继续后续流程。其它 `status`（`CLI_ERROR` / `INVALID_INPUT` / `CYCLE_DETECTED` / `DEPTH_EXCEEDED`）停止 BOM 流程并说明原因。

- **合并回 dataList**：保留母件行在 `dataList` 中的原始位置，把 `groups[bom_core_id]` 的子产品行按返回顺序追加在该母件行之后；普通产品行与其他母件行位置保持不变。复用 BOM 节点行携带的 `bom_core_id` 必须原样保留至步骤 4 传入 `handleBomTree`，用于接口识别该子产品引用了另一个 BOM；该行按非母件处理（脚本回填时不回填 `bom_core_id`，已设置的值不被接口返回覆盖）。普通子产品行不设置 `bom_core_id` / `bom_core_id__r`。`temp_detail_id` 不在步骤 3 生成，统一推迟到步骤 4 调用脚本前一次性分配。

- **执行属性插件**（受特性开关 `is_open_attribute` 门控）：门控值取上游 `get-config-values` 查询结果。仅当返回值为 `"1"` 时，步骤 3 新增的每条子产品明细行都必须使用其 `product_id` 执行 `references/AttributePlugin.md`，无论用户输入中是否包含属性信息；开关非 `"1"` 或缺失时跳过属性处理，子产品行不携带 `attribute`/`attribute_json`，直接进入展开后校验。属性插件返回 `attribute`、`attribute_json` 时，必须合并到对应的新增子产品行；其中 `attribute_json` 保持 Map/对象类型，禁止转成字符串。属性关系查询为空时，按属性插件规则结束该行的属性处理并继续；存在待确认或必填属性未完成时，不得调用 `handleBomTree`。

- **展开后校验**：展开后的 `dataList` 必须仍包含所有普通产品行，且至少一条母件行带 `bom_core_id`；同时所有新增子产品行均已完成属性处理（含按门控跳过的情形），才允许进入步骤 4 调用脚本。

### 4. 调用 handleBomTree 并回填

只有至少存在一条已确认的 `bom_core_id` 时，才允许调用。`handleBomTree` 接口调用与返回值回填只能走以下 python 脚本，禁止 Agent 手调 `handleBomTree`，禁止手写回填。

```bash
cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/query_bom_batch.py --mode tree --data '<按规则组装后的 JSON 参数>'
```

入参结构：

```json
{
  "accountId": "<客户ID>",
  "partnerId": "<合作伙伴ID，可选，无值时省略>",
  "objectApiName": "QuoteObj",
  "detailObjectApiName": "QuoteLinesObj",
  "objectData": { "<主对象字段>": "<值>" },
  "dataList": [
    { "temp_detail_id": "detail_0", "product_id": "<普通产品ID>", "product_id__r": "<普通产品名称>", "quantity": "1" },
    { "temp_detail_id": "detail_1", "product_id": "<BOM母件产品ID>", "product_id__r": "<BOM母件产品名称>", "quantity": "2", "bom_core_id": "<步骤1确认的BomCoreObj._id>", "bom_core_id__r": "<BomCoreObj.name>", "attribute_json": { "<属性ID>": "<属性值ID>" } },
    { "temp_detail_id": "detail_2", "product_id": "<子产品ID>", "product_id__r": "<子产品名称>", "quantity": "4", "attribute_json": { "<属性ID>": "<属性值ID>" } },
    { "temp_detail_id": "detail_3", "product_id": "<复用BOM产品ID>", "product_id__r": "<复用BOM产品名称>", "quantity": "2", "bom_core_id": "<该节点的related_core_id>" }
  ]
}
```

- 仅 BOM 母件行携带 `bom_core_id` / `bom_core_id__r`；复用 BOM 节点行（步骤 3 递归展开产生）仅携带 `bom_core_id`；普通产品行和普通子产品行均不带。
- `attribute_json` 仅在属性插件已返回时携带，保持 Map/对象类型，禁止序列化为字符串。

调用要求：

- 调用前必须为 `dataList` 中每条明细行统一生成仅本次内部使用的 `temp_detail_id`，一次性覆盖所有行（含步骤 3 新增的全部子产品行及复用 BOM 节点行），不再在步骤 2、步骤 3 分批生成或补发。上游已有该字段则沿用；必须在本次 `dataList` 内唯一，按最终明细顺序生成，如 `detail_0`、`detail_1`、`detail_2`。缺失时脚本会按同一规则补齐，Agent 不得在脚本返回后再改。
- `dataList` 必须传入当前从对象的完整明细数组（含普通产品行），不能只传带 `bom_core_id` 的 BOM 母件行，避免接口返回后普通明细丢失或顺序错乱。
- 对已确认的 BOM 母件行补充 `bom_core_id` 和 `bom_core_id__r` 后再调用。

脚本内部处理：

- 校验 `dataList` 非空且至少一行带 `bom_core_id`，补齐缺失的 `temp_detail_id`，再调用 `sharecrm sales product handleBomTree`。
- 按 `temp_detail_id` 精确匹配返回行；无法使用时才降级按 `product_id` 唯一匹配。匹配歧义、返回为空、已进入 BOM 流程的行找不到返回行，均停止回填。
- 字段回填由脚本完成，规则以脚本内部实现为准；Agent 禁止再手写赋值。

脚本返回（`status == READY` 时）含 `dataList`（完整明细数组，普通行与 BOM 行都在，顺序不变）及 `details`（键为 `detailObjectApiName`，值与 `dataList` 同一数组）；其它 `status` 仅含 `error`，不得覆盖上下文。

`status` 说明：

- `READY`：已回填，整节点覆盖上下文对应从对象明细。
- `EMPTY_RESULT`：接口返回为空，或找不到可安全回填的明细行。
- `MATCH_ERROR`：`temp_detail_id` 或降级 `product_id` 匹配出现歧义。
- `CLI_ERROR`：`handleBomTree` 调用失败。
- `INVALID_INPUT`：入参不合法。

### 5. 覆盖上下文明细

仅当 `status == READY` 时：

1. 用脚本返回的 `details` **整节点覆盖**上下文对应从对象明细；若上下文按数组持有该从对象，则用返回的 `dataList` 整数组覆盖。禁止只改部分行、禁止丢字段、禁止再手写一遍回填。
2. 覆盖完成后进入后续取价/保存流程；禁止再整理提交数据。

`status` 非 `READY` 时：不得覆盖上下文明细，按 FailurePolicy 停止流程。

## Outputs

- 输出已完成 BOM 字段回填的明细数据，供主流程继续执行创建确认、保存或后续插件处理。
- 不输出 `handleBomTree` 入参。
- 不输出接口原始返回值。
- 不输出匹配中间过程、临时标识或调试数据。

## Boundaries

- 本 skill 只负责 BOM 头查询、BOM 树接口调用和明细字段回填。
- 不负责普通产品取价；普通产品取价交由取价插件处理。
- 不负责属性解析或属性字段组装；属性处理交由属性插件处理。
- 不负责记录创建、草稿重算、提交确认或审批触发。
- BomService 已回填的明细行归本插件所有，其他插件不得覆盖；普通产品取价、属性解析等只允许作用于未进入 BOM 流程的明细行。
- 禁止 Agent 手调 `handleBomTree` 或手写回填；只能调用 `scripts/query_bom_batch.py --mode tree`。
- 禁止 Agent 手拼 SQL 或手写子产品展开/数量缩放逻辑；只能调用 `scripts/query_bom_batch.py --mode core/children/expand`。

## FailurePolicy

以下情况必须停止 BOM 流程并说明原因，且不得覆盖上下文明细：

- `BomCoreObj` 查询接口失败。
- `BOMObj` 子产品查询接口失败(母件及所有子产品下单场景)。
- 复用 BOM 递归展开出现环引用或超出深度上限。
- 步骤 3 新增子产品的属性插件执行失败，或存在待确认、必填但未完成的属性信息。
- 多候选无法根据用户输入唯一确定，且用户未完成选择。
- 不同输入 key 映射到同一个 `bom_core_id`。
- 已进入 BOM 流程的明细缺少唯一 `bom_core_id` 或 `bom_core_id__r`。
- 脚本返回非 `READY`（`CLI_ERROR` / `EMPTY_RESULT` / `MATCH_ERROR` / `INVALID_INPUT`），或明细结构异常无法安全回填。

0 命中 BOM 不视为失败；对应明细退出 BomService，继续按普通产品流程处理。
