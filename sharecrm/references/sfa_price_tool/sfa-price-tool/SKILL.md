---
name: "sfa-price-tool"
description: "当用户要询价或查询价格结果，包括价格、多少钱、可用价格、价目表、价目表明细、价格列表、最优价格、最高优先级价格、最终取价、成交价等价格业务时使用；可结合客户和产品确定可用价格。仅当用户目标是价格结果时才用本 skill；查询产品或客户对象字段、属性、详情时不使用本 skill。"
apiName: "sfa_price_tool"
---
# sfa-price-tool

## Trigger & Routing

先判定用户目标是否为获取价格或价目表结果。只有目标是价格、询价、可用价格、价目表、价目表明细、最优价格、优先级最高价格或最终价格时，才继续使用本 Skill；一旦命中价格意图，必须先依据本 Skill 判定业务类型，禁止先自由调用 `sharecrm` CLI，也禁止优先路由到通用查询类 skill。

如果用户目标是查询产品或客户对象的字段、属性、详情，且不是获取价格或价目表结果，不使用本 Skill，应走通用查询。

典型问法与分流：

| 用户问题 | 应走业务类型 |
|------|------|
| 帮我查一下产品X的价格 / 产品X有哪些价格 / 产品X的价格是多少 / 某个产品有哪些价格 / 某个产品的价目表明细是什么 / 某产品有哪些价目表明细 | 按产品查询价格 |
| 查一下客户A产品X的价格有哪些 / 某个客户购买某个产品时有哪些价格 / 查某客户的某产品价格列表 / 查询某个客户的某个产品有哪些可用价格列表 | 按客户及产品查询价格 |
| 某客户某产品最优价格是多少 / 某个用户某产品的最终价格是多少 / 某客户某产品哪个价格优先级最高 / 某客户某产品最终取价是多少 | 按客户及产品查询价格（直接进入最优价格 / 最终价格子分支） |

不适合：

- 查询产品或客户对象字段、属性、详情，且目标不是价格或价目表结果

## 最高优先级规则

- 产品字段解析闸门：除用户直接提供产品 ID 外，产品解析必须先执行 `GetObjectDescribe(ProductObj)`；用对象描述匹配字段并组装 `ResolveProductIdsBatch` 入参，匹配不到字段时才默认按 `name` 组装。

## Commands

- 对 `sharecrm` 的实际调用必须直接使用下方声明的唯一合法命令；不要根据工具名、动作名、中文语义或 kebab-case 自行拼接、改写、猜测 `sharecrm` 子命令。
- 如果正文其他位置与本节不一致，一律以本节为准。
- `QueryIdByName`（客户名称解析）：`sharecrm data record query-id-by-name --data '{"query":"<客户名称>","apiNames":["AccountObj"]}'`
- `QueryByFields`（客户名称 LIKE 兜底）：`sharecrm data record query-by-fields --object_api_name AccountObj --name-like <客户名称> --select_fields _id,name --limit 10`
- `GetObjectDescribe`：`sharecrm data describe get -d '{"object_api_name":"<object_api_name>"}'`
- 查询产品 ID 时，只能调用以下 Python 脚本，避免 Agent 多次调用 `sharecrm` 工具查询数据；脚本支持同时执行按产品名称查询和按产品字段查询：
  - `ResolveProductIdsBatch`：`cd "<{Current agent directory}/skill/{skillApiName}>" && python scripts/resolve_product_ids_batch.py --data '<JSON>'`
  - 入参格式：`{"items":[{"object_api_name":"ProductObj","method":"query-id-by-name","query":"<产品名称>"},{"object_api_name":"ProductObj","method":"query-by-fields","filters":[{"field_api":"<字段API>","operator":"eq","value":"<字段值>"}],"select_fields":["_id","name","<字段API>"],"limit":10}]}`
  - 每个产品解析单元对应一个 `items` 项；多个产品必须拆成多个项一次传入，禁止把多个产品值合并成同一个 `query-by-fields` 查询条件。
  - `method=query-id-by-name` 用于按产品名称解析，脚本会在未命中时自动按 `name LIKE` 兜底。
  - `method=query-by-fields` 用于按非 `name` 字段解析；唯一编码、枚举、布尔等精确字段优先使用 `operator=eq`。
  - 字段为单选、多选或布尔值时，`filters[].value` 必须使用 `GetObjectDescribe` 中该字段选项或布尔定义对应的 value，不要直接使用用户输入的展示文案。
  - `select_fields` 必须包含 `_id,name`，并补充用户用于定位的字段；没有额外定位字段时只保留 `_id,name`。
  - 返回按 `items` 顺序对应输入项，`status` 为 `UNIQUE` / `MULTIPLE` / `NOT_FOUND` / `ERROR`。
- `priceToolAction`：`sharecrm sales product action-price-tool --data '<JSON>'`
  - 按客户及产品查询价格：`{"accountId":"<客户ID>","productInfos":[{"productId":"<产品ID>"}]}`
  - 按产品查询价格：`{"productInfos":[{"productId":"<产品ID>"}]}`
  - `productInfos` 必须是数组，可以传多个产品。
  - 当且仅当用户明确描述具体数量时，才允许在 `productInfos` 中传 `amount`，例如：`{"accountId":"<客户ID>","productInfos":[{"productId":"<产品ID>","amount":1}]}`。注意：`priceToolAction` 的 `amount` 必须是数字类型（如 `1`），不能是字符串（如 `"1"`）。
  - 返回结果会标识是否开启价目表；该标识只用于选择字段组，不作为用户可见内容。
- `getRealPriceAction`：`sharecrm sales product action-get-real-price --data '{"accountId":"<客户ID>","fullProductList":[{"productId":"<产品ID1>","amount":"1"},{"productId":"<产品ID2>","amount":"1"}]}'`
  - 只允许 `accountId + fullProductList[{productId, amount}]`

## Core Rules

- 这是“询价工具”，核心目的是查可用的价格列表、价目表、价目表明细和最优价格。
- 本 Skill 中所有 `sharecrm` 调用都必须严格使用 `Commands` 章节中的唯一合法命令；不得自行改写参数名、参数层级、参数类型、数组结构，也不要自行探索 `sharecrm --help`、`sharecrm data --help` 或其他命令路径。
- `getRealPriceAction` 用于按客户及产品场景下查询某客户某些产品的最高优先级价格 / 最终取价。
- 只要问题已经明显命中本 Skill，就必须先依据本 Skill 的业务分流规则行动；不要跳过 Skill 直接靠 CLI 试探查询。
- 未判定业务类型前，禁止直接执行 `priceToolAction`，也不要直接查询价目表相关对象当作最终答案。
- 查询客户或产品时，必须先解析为唯一记录；无法唯一命中时，不得继续调用询价工具，必须要求用户补充或选择。
- 无论是按客户及产品查询价格，还是按产品查询价格，严禁直接复用上下文中的历史结果、历史表格、历史字段值或历史结论；每次都必须重新执行 `priceToolAction` 查询。
- 只有 `getRealPriceAction` 返回的结果，才能表述为“最优价格”“优先级最高价格”“最终取价”；不要把普通询价列表排序后冒充最终答案。
- 结果展示必须严格按照本 Skill 规定的结果表格式生成；严禁补值、猜值、改写字段，或脱离字段规则自由发挥。
- 本 Skill 采用静默执行：除非必须向用户追问或直接输出最终结果，其他阶段一律不向用户输出任何说明。
- 额外操作识别：完成价格查询后，主动识别用户原始消息中的其他操作意图（提到具体数量时通常隐含计算总价）。如有额外操作意图：
  - 不输出常规追问，改为向用户发出确认询问，例如"您提到了华为手机10个、苹果手机10个，是否需要计算总价？"。
  - 必须等待用户明确确认后才可执行该操作；禁止在用户确认前直接执行。
  - 计算总价时以价目表售价为单价 × 数量，多行累加（字段关系：价目表售价 × 折扣 = 价目表价格）。
- 如无额外操作意图，按"追问决策"章节规则执行。

## Shared Resolution Flow

- 客户对象固定为 `AccountObj`，产品对象固定为 `ProductObj`。
- 用户未提供客户 / 产品信息或 ID 时，必须提示用户先输入。
- 用户直接提供 ID 时可直接继续后续询价。
- 客户解析保持名称优先：用户提供客户名称时，先执行 `QueryIdByName`；未命中时，再执行 `QueryByFields`。
- 产品解析固定先执行 `GetObjectDescribe(ProductObj)`，再根据对象描述把一个或多个产品输入转换为 `ResolveProductIdsBatch` 的 `items`，并一次调用脚本：
  - 能匹配到字段时，只能使用本次对象描述映射字段 API 并按字段类型规范化过滤值；字段映射为 `name` 时，生成 `method=query-id-by-name` 的 item。
  - 匹配不到字段时，才默认把产品信息作为 `name` 值处理，生成 `method=query-id-by-name` 的 item；脚本内部负责未命中后的 `name LIKE` 兜底。
  - 字段映射为非 `name` 字段时，生成 `method=query-by-fields` 的 item，只传该产品自己的字段过滤条件。
  - 禁止凭历史记忆、常见字段名、上次查询结果或字段展示文案直接推断产品字段 API；如果用户明确要按某字段查询但对象描述中无法确认该字段，对用户说明无法准确映射并要求补充字段或产品 ID。
- `ResolveProductIdsBatch` 返回 `NOT_FOUND` 则明确说明未找到，返回 `MULTIPLE` 则展示候选项并要求用户选择，返回 `ERROR` 则说明解析失败；不能自行猜测。
- 只有拿到唯一客户或产品 `_id` 后，才能进入依赖该对象的询价步骤。
- 如果当前条件仍不足以唯一命中，可以提示用户补充更精确的客户名、产品信息或直接提供 ID。
- 不要在客户或产品未唯一确定时直接调用询价工具。

## Route A: 按客户及产品查询价格

- 必须先确认客户名称或客户 ID，以及至少一个产品信息或产品 ID；任一缺失时先提示用户补充，不得继续。
- 先按 `Shared Resolution Flow` 解析客户和一个或多个产品。
- 只允许调用 `priceToolAction`。
- `accountId` 必须传；`productInfos` 必须传，且其中每个产品项都必须有 `productId`。
- 当用户有描述具体的数量时，需要传 `amount`；否则不要传 `amount`。
- 只允许使用 `accountId + productInfos[]` 结构。
- 如果出现参数错误，先检查是否误把该接口传成了其他接口的参数格式，不要擅自改成 `account_id + product_id` 或 `fullProductList`。
- 如果结果为空，明确说明该客户对这些产品当前没有查到可用数据。
- 查询结果必须按 `Output Contract` 输出。

## Route B: 最优价格 / 最终价格子分支

- 用户一开始就问某客户某产品的最优价格、最高优先级价格、哪个价格优先级最高或最终价格。
- 用户在按客户及产品查询价格的列表结果基础上继续追问“哪个价格最优”“哪个价格优先级最高”“哪个价目表优先级最高”“最终取价是多少”。
- 如果用户一次给了多个产品的最优价格 / 最终价格诉求，允许在同一次 `getRealPriceAction` 中传多个产品。
- 先确认客户和产品都已经唯一命中。
- 严禁直接复用上下文中的历史询价结果；必须先重新执行一次 `priceToolAction`。
- 只允许调用 `getRealPriceAction`。
- `getRealPriceAction` 只允许 `accountId + fullProductList[{productId, amount}]`。
- 如果 `getRealPriceAction` 返回为空或失败，要明确说明最高优先级价格未成功取回，不要用普通询价列表兜底冒充最终答案。
- 查询结果必须按 `Output Contract` 输出。
- 返回最优价格/最终价格结果后，追问决策见"追问决策"章节。

## Route C: 按产品查询价格

- 必须先要求用户输入至少一个产品信息或产品 ID；如果缺少产品信息，不得继续。
- 先按 `Shared Resolution Flow` 解析一个或多个产品。
- 只允许调用 `priceToolAction`。
- 如果用户的问题是“产品X的价格是多少”，默认仍按本业务类型处理，不要直接用 `GetRecordById(ProductObj)` 返回标准价格代替价格列表。
- `productInfos` 必须传，且其中每个产品项都必须有 `productId`。
- 当用户有描述具体的数量时，需要传 `amount`；否则不要传 `amount`。
- 按产品查询价格时，不得传 `accountId`。
- 如果结果为空，明确说明这些产品当前没有查到可用数据。
- 查询结果必须按 `Output Contract` 输出。


## 追问决策

**本规则优先级高于 Output Contract，输出最终回复前必须先完成本节检查。**

### Route A

- 拿到 `priceToolAction` 返回的所有产品结果后，必须先逐产品计数：每个产品在结果中出现了几行记录。
- **只要存在任意一个产品的记录行数 > 1，Route A 的追问即被强制禁止：不追问任何内容，不输出任何下游操作引导语。**
- 仅当所有产品记录行数都 = 1 时，Route A 才允许追问，例如"是否需要基于这些价格生成报价单、销售订单或销售合同等"。

### Route B

- 返回最优价格/最终价格结果后，直接追问下游操作，例如"是否需要基于这些价格生成报价单、销售订单或销售合同等"。

### Route C

- 返回按产品查询价格结果后，必须追加一句简短追问，引导用户继续查询具体客户可用价格，例如"如果需要查询某个客户的可用价格，请继续输入客户名称"。

### 禁止行为

- Route A 且存在多行记录产品时，禁止输出任何追问语。
- 禁止在 Route A 下使用 Route B 或 Route C 的追问模板。
- 禁止只检查部分产品的记录行数就做出追问决策。


## Output Contract

### Reply Scope

- 允许的回复内容仅限：Markdown 结果表、按产品分表时的产品名称标题、本 Skill 明确要求的追问语、以及 Core Rules 中额外操作识别要求的操作确认语；不输出其他正文。
- 追问内容必须严格使用当前业务类型允许的追问；严禁套用其他业务类型的追问模板。
- 有价格记录时，直接输出最终 Markdown 表格；无价格记录时，按当前 Route 的空结果规则回复。不要输出价格摘要、客户/产品解析表格、工具调用说明、字段取舍说明、空值判断说明、表格修正说明或中间整理草稿。

### 结果表字段规则

- 字段来源只能是当前场景的 `Field Maps`，以及按"默认字段之外字段追加规则"加入的字段。
- `固定展示` 字段必须展示；`有值展示` 字段仅在当前结果表记录中至少一条记录有展示值时展示，整列无展示值时不展示。
- 按产品分表时，每个产品表独立判断 `有值展示` 字段；合并表时，对合并后的全部记录判断。
- 有展示值：值不是 `null`、`undefined`、空字符串、空白字符串、空数组或空对象；数字 `0` 是有展示值。
- 空值字段取舍仅作为内部成表处理；最终 Markdown 表格不得包含整列无展示值的 `有值展示` 字段，不得在正文中说明字段取舍、空值判断或表格修正过程。
- 空单元格留空；禁止使用占位符，禁止用其他记录的值填充。

### 结果表格式

- 默认使用 Markdown 表格展示结果。
- 普通询价结果表格形态：产品数 `<= 5` 时按产品分表；产品数 `> 5` 时合并为一个表。
- 按产品分表时，分组标题只能是产品名称；标题不能代替结果表中的"产品名称"列。
- 结果表字段必须遵守"结果表字段规则"。
- 表头展示名必须逐字使用 `Field Maps` 中的名称；列顺序保持 `Field Maps` 顺序。
- 多条记录保持列表完整，不只展示第一条。
- 一行是一条价格记录，不能转置成竖表。

## Field Maps

### 普通询价公共字段规则

#### 当未开启价目表时

| 字段 API | 展示名 | 显示策略 |
|------|------|------|
| `name` | 产品名称 | 固定展示 |
| `product_code` | 产品编码 | 有值展示 |
| `price` | 标准价格 | 固定展示 |

#### 当开启价目表时

| 字段 API | 展示名 | 显示策略 |
|------|------|------|
| `product_id__r` | 产品名称 | 固定展示 |
| `product_code` | 产品编码 | 有值展示 |
| `pricebook_id__r` | 价目表 | 固定展示 |
| `pricebook_price` | 价目表价格 | 固定展示 |
| `discount` | 价目表折扣 | 固定展示 |
| `pricebook_sellingprice` | 价目表售价 | 固定展示 |
| `ceiling_price` | 浮动上限价格 | 有值展示 |
| `floor_price` | 浮动下限价格 | 有值展示 |
| `start_count` | 起始数量(不含) | 有值展示 |
| `end_count` | 结束数量(含) | 有值展示 |
| `unit__r` | 单位 | 有值展示 |
| `mc_currency` | 币种 | 有值展示 |
| `start_date` | 有效开始时间 | 有值展示 |
| `end_date` | 有效结束时间 | 有值展示 |

### 最优价格 / 最终价格字段规则

| 字段 API | 展示名 | 显示策略 |
|------|------|------|
| `product_id__r` | 产品名称 | 固定展示 |
| `product_code` | 产品编码 | 有值展示 |
| `pricebook_id__r` | 价目表 | 固定展示 |
| `pricebook_price` | 价目表价格 | 固定展示 |
| `discount` | 价目表折扣 | 固定展示 |
| `selling_price` | 最优价格 | 固定展示 |
| `unit__r` | 单位 | 有值展示 |

## 默认字段之外字段追加规则

- 如果用户要求追加展示默认字段之外的其他字段，先执行 `GetObjectDescribe` 确认对象字段 API，再补充展示。未开启价目表时对象为 `ProductObj`，开启价目表时对象为 `PriceBookProductObj`。
- 追加字段加入当前场景的 `Field Maps` 末尾，显示策略为 `有值展示`，并遵守"结果表字段规则"。
- 额外字段的表头优先使用对象描述返回的字段名称、标签名或显示名；如果无法准确定位字段，先说明无法准确映射，不要猜测。
