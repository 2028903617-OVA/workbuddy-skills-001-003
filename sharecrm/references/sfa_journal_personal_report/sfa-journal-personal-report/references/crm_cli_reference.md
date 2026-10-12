# CRM CLI 查询参考

本文件用于个人销售日报、周报、月报的数据查询。只有在当前环境提供 `sharecrm` CLI，且用户请求需要查询 CRM 数据时才读取本文件。

## 基本原则

- 先解析销售人员和周期，再查 CRM 事实；人员范围见 `rules/R08_person_scope_and_coverage.md`，日期边界见 `references/report_periods.md`。
- 只使用：`describe get`、`query-by-fields`、`query-by-name`、`query-id-by-name`。不要尝试 `sharecrm sales ...`、`--data` 查询或未记录快捷命令。
- 首次查询对象前必须 describe；字段未确认时不要猜负责人、阶段、金额、时间字段。
- 能并行的查询不要串行：先一次性定对象清单并行 describe，再并行查询互不依赖的核心事实。
- 查询前写 query plan：对象清单、时间窗口、人员过滤方式、时间字段、选择字段、limit、是否需要历史日期。
- 查询集最小化：不要为了填写数据覆盖说明而查询对象；未触发的对象标注“未触发查询”。已从日志、销售记录或商机拿到足够支撑结论的金额、阶段、客户名或承诺信息时，不再补查订单、回款、客户、线索或联系人。
- 已知标准对象 ApiName 不需要 `identify-with-describe`；未知自定义对象才先识别。
- 没有原始查询返回或明确查询状态，不得写成 CRM 事实；模型判断只能写“推断/待确认”。
- 权限不足、查询失败、查询成功 0 条必须分开表达；权限不足不得写成无数据。
- 同一对象本轮权限不足、describe 失败或不可恢复错误后，不要重复试同一对象。

## 查询批次

1. Batch A 字段确认：只 describe 本轮计划查询的对象，并行执行。
2. Batch B 核心事实：优先并行查询日志、销售记录、商机。
3. Batch C 指标补查：仅当成交/回款指标无法从核心事实判断，或用户明确要求成交/回款明细时，并行查询订单、回款。
4. Batch D 可选事实：仅在承诺、会议、拜访或待办无法判断时查询日程/外勤。
5. Batch E 扩展上下文：仅在缺客户名称、线索状态、来源或联系人时查询客户/线索/联系人。
6. 自定义对象：用户指定后先 describe，再按已确认字段查；不要当作标准对象处理。

简洁版默认对象：

| 周期 | P0 默认查 | P1/P2 按需查 |
| --- | --- | --- |
| 日报 | 日志、销售记录、商机 | 订单/回款：当日成交或回款无法从核心事实判断；日程/外勤：会议、拜访、待办或承诺闭环无法判断；前 1-2 日核心对象：仅判断连续缺失时 |
| 周报 | 日志、销售记录、商机；订单/回款仅在关键经营信号需要且核心事实不足时补查 | 日程/外勤：会议、拜访、待办兑现；客户/线索/联系人：名称、状态、来源、关键人缺失 |
| 月报 | 日志、销售记录、商机；订单/回款仅在目标完成、成交或回款结构需要且核心事实不足时补查 | 客户/线索/联系人：月度新增、成交状态、联系人上下文缺失 |

基础事实对象（日志、销售记录、商机、订单、回款）权限不足时，不继续查询依赖这些事实解释的扩展对象。

## 字段确认

每个对象在本轮请求中首次查询前，先执行：

```bash
sharecrm data describe get --object_api_name <ObjectApiName> --simple_describe true
```

执行后只使用返回中确认存在的字段：

- 时间字段：如 `create_time`、`payment_time`、`new_stat_date`、`journal_time`。
- 人员字段：不要默认存在 `owner`、`owner_id`、`created_by` 或销售姓名字段。
- 关联和选择字段：`--select_fields` 只能放已确认字段；不确定就删掉或标待确认。
- 人员字段无法确认时，先按时间窗口查，再用返回中的可识别人员字段谨慎筛选，并在数据说明写“人员过滤置信度有限”。
- 时间字段无法确认时，不构造时间过滤；记录为“查询失败：时间字段未确认”。

同一对象本轮已 describe 过，复用字段，不重复 describe。

## 用户可见对象名称

查询和内部处理可以使用 ApiName；对用户输出 CRM 数据汇总、数据说明和保存结果时必须改成中文对象名，且隐藏 `_id`、记录 ID 和长串主键。

| 内部对象 ApiName | 用户可见名称 |
|------------------|--------------|
| `JournalObj` | 日志 |
| `ActiveRecordObj` | 销售记录 |
| `ScheduleObj` | 日程 |
| `CheckinsObj` | 外勤 |
| `NewOpportunityObj` | 商机 |
| `SalesOrderObj` | 订单 |
| `PaymentObj` | 回款 |
| `AccountObj` | 客户 |
| `LeadsObj` | 线索 |
| `ContactObj` | 联系人 |
| `PersonnelObj` | 人员 |

## 查询结果状态

生成报表前，必须维护每类 CRM 数据状态：

| 状态 | 含义 | 输出处理 |
| --- | --- | --- |
| 已读取 | 查询成功且有可用记录 | 可用于事实和指标统计 |
| 无数据 | 查询成功但返回 0 条记录 | 只能说明本期 CRM 未记录该类数据 |
| 权限不足 | CLI 返回无对象、列表、字段或数据权限 | 标注“权限不足未读取”，不要写成无数据 |
| 未触发查询 | 周期或报表逻辑未要求查询该对象 | 标注“未触发查询”，不要写成无订单/无回款 |
| 查询失败 | 非权限类错误、字段不支持或命令失败 | 标注失败原因并降低相关结论置信度 |

报表末尾的数据说明必须弱化展示数据覆盖，例如：

```text
> 数据覆盖：日志 已读取；销售记录 权限不足未读取；商机 已读取；订单 无数据；回款 未触发查询；联系人 未触发查询。
```

事实表达：`已读取` 且有记录才写“CRM 显示/查询到”；`无数据` 只能写“本次查询未返回记录”；`权限不足/查询失败/字段不支持` 不得当作 0；`未触发查询` 不得暗示该对象没有记录；连续缺失必须列出实际查询过的日期范围和对象状态。

## 常用命令

### 查询对象字段

```bash
sharecrm data describe get --object_api_name <ObjectApiName> --simple_describe true
```

### 按名称查询记录

用于查询客户、人员、线索等主记录；没有查到时向用户确认名称或要求补充数据。

```bash
sharecrm data record query-by-name --name <名称> --object_api_names <ObjectApiName>
```

### 按名称查询记录 ID

只需要记录 ID 用于后续过滤时，优先使用更轻量的 ID 查询。

```bash
sharecrm data record query-id-by-name --query <名称> --apiNames <ObjectApiName>
```

### 按字段查询记录

用于按已确认字段查询明细数据。固定使用扁平参数，不使用 `--data` JSON，也不要混用 JSON 和扁平参数。

```bash
sharecrm data record query-by-fields \
  --object_api_name <ObjectApiName> \
  --select_fields <confirmed_fields> \
  --<confirmed_field>-eq <value> \
  --<confirmed_time_field>-gte "<startTime>" \
  --<confirmed_time_field>-lte "<endTime>" \
  --sort <confirmed_time_field>:desc \
  --limit 50
```

要求：`ObjectApiName`、`select_fields`、过滤字段、时间字段和排序字段都必须来自 describe；时间格式用 `yyyy-MM-dd HH:mm:ss`；`limit` 默认 50，需要更多时分批或说明覆盖限制。

## 人员过滤

个人报表尽量限定到当前销售人员，但不要猜负责人字段。先用 `currentEmployeeName` 或用户指定姓名确认销售姓名；需要人员记录时先 describe `PersonnelObj`，再 `query-by-name` 或 `query-id-by-name`。只有业务对象 describe 返回可用人员字段后，才使用人员过滤；否则先按时间窗口查，再基于返回中的人员/创建人/负责人文本谨慎筛选，并在数据说明写明限制。不要默认所有对象都支持 `owner`、`owner_id` 或人员 ID 过滤。

## 目标、任务与口径缺失处理

- 目标来源优先级：CRM 目标/配额字段或对象 -> 用户提供 -> CRM 日志明确目标 -> memory 兜底。没有目标数据时不计算完成率，只输出成交、回款、Pipeline 等事实。
- 任务/P0 来源优先级：CRM 任务字段或对象 -> 日程 -> 销售记录承诺 -> 上期日志下期计划 -> 用户输入 -> memory 兜底。
- 没有明确任务对象时，不说“已查询 CRM 任务”；写“任务数据来自日程、销售记录、日志或用户输入推断”。

## 日志历史查询建议

生成个人报表前，优先查询目标周期日志：日报查上一日和当天，周报精确查上周和本周，月报查上月和月内。只有用户要历史参考时才查最近历史日志。

查询日志时也必须先 describe。只有字段确认存在时，才使用 `record_type`、`journal_time`、人员字段或名称字段过滤。

日志查询必须精确到目标周期：

- 个人周报上周承诺：优先使用 `journal_time = previous_period_end_yyyyMMdd`；字段存在时同时使用 `period_type`、`record_type` 和人员字段过滤。
- 个人周报本周重复生成检查：优先使用 `journal_time = current_period_end_yyyyMMdd`。
- 个人月报上月复盘：优先使用 `journal_time = previous_month_end_yyyyMMdd`。
- 如果精确周期查询成功但返回 0 条，状态写“无数据/待确认”；不要再宽泛查询最近周报、最近月报或更早日志来替代该周期证据。
- 只有用户明确要求历史参考时，才另查最近历史日志，并明确标注为“历史参考，不是上一周期记录”。

如果日志不可用，说明无法读取历史日志；不要自动退回为已读取本地 memory，除非本地 memory 明确存在且用户允许参考。

判断连续缺失时，必须明确追加前 1-2 日同一核心对象查询；否则只能说明“今日未查询到核心记录”，不能写“连续 3 日数据缺失”。

## 查询失败处理

遇到以下情况，不要继续换命令乱试：CLI 不存在、无权限、describe 失败、字段不确定、一次按已确认字段构造的 query 失败、人员/时间范围不明确、CRM 与用户输入冲突。

处理方式：

```text
当前无法完整查询 CRM 数据，原因是：[原因]。
请补充：[需要用户补充的数据]。
以下内容将基于已获得数据生成；受影响的判断会在对应模块内简短说明。
```

如果是字段或命令问题，说明“已按对象字段查询，但当前 CLI/字段不支持该条件”，然后追问或基于已获得数据继续生成；查询数据时不要继续尝试 `sharecrm sales ...`、`--data`、`owner_id` 等未确认写法。保存日志的 `--data` 创建命令见 `rules/R09_journal_storage_confirmation.md`。

如果是权限不足，记录该对象状态为“权限不足”，本轮不要更换字段或命令重复尝试同一对象；后续报表只基于已读取对象、用户输入和允许的兜底数据生成。

## 日志写入处理

- 本文件不维护写入 payload 细节，避免双份规则冲突。
- 保存前必须先执行 `rules/R09_journal_storage_confirmation.md`，展示中文预览并等待用户明确确认。
- 用户确认后按 `rules/R09_journal_storage_confirmation.md` 和 `references/journal_object_reference.md` 的唯一写入范式执行。
- 无写入能力、无权限或写入失败时，不编造成功状态、命令结果或记录 ID。

## 禁止行为

- 不在 describe 之前查询业务对象。
- 不使用企业规范未记录的 `sharecrm sales ...` 快捷命令。
- 查询记录时不使用 `--data` JSON 或混合 JSON/扁平参数写法；保存日志由 R09 处理。
- 不猜 `owner`、`owner_id`、`stage`、`payment_amount`、`account_name` 等字段。
- 不输出与 CRM 记录矛盾的推断。
- 不在信息不足时假装知道。
- 不声称已经自动同步、自动写入或自动提醒，除非环境确实提供相应能力。
- 不把没有查询到的数据写成事实。
- 推断必须标注来源和置信度：确认 / 推断 / 待确认。
- 不在用户确认前写入日志。
- 不编造 CRM 创建命令、记录 ID 或保存成功状态。
