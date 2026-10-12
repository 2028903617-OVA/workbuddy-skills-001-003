# 商机（NewOpportunityObj）评分数据查询

用于商机质量、赢单概率、推进价值等 knowhow 评分。对象定位后，评分所需 CRM 数据优先复用当前上下文中同一商机的脚本返回数据包；没有可复用数据包时，统一调用一次本 skill 内置脚本查询。不得在脚本已覆盖的数据包上重复手工拼接 `sharecrm` 命令。

## 0. 卖方行业配置

卖方主营行业由 `scripts/query-diagnosis-data.py` 统一查询并写入脚本返回：

```json
{
  "queried_at": "2026-07-03T00:00:00Z",
  "seller_context": {
    "seller_industry": "<SELLER_INDUSTRY>"
  }
}
```

调用方只读取 `seller_context.seller_industry` 作为 `SELLER_INDUSTRY`，不得额外手工调用 `sharecrm sales get-config-by-key`。`seller_context.seller_industry` 为空时，评分依据中不得编造卖方行业上下文。

## 1. 对象定位

sharecrm data record query-id-by-name --data '{"query":"<商机名称>","apiNames":["NewOpportunityObj"]}'

未命中时模糊兜底（候选 >=2 时展示 `_id` / `name` / `account_id` 供选择）：

sharecrm data record query-by-fields --object_api_name NewOpportunityObj --select_fields "_id,name,account_id" --name-like "<关键词>" --limit 10 --sort last_modified_time:desc --raw

对象定位阶段只负责得到唯一 `<opportunity_id>`；不得在此阶段生成评分结论。

## 2. 查询范围

确认商机 ID 后，先检查当前上下文是否已有 `Opportunity_Data_Package`：

- 可复用条件：`opportunity_id` 与当前商机一致、`status=READY`、包含 `data`、`seller_context`、`buyer_industry`、`errors`、`notes`。
- 时效条件：包含 `queried_at`，且 `queried_at` 距当前时间不超过 30 分钟。
- 满足可复用条件时，直接消费该 JSON 数据包，不再调用脚本。
- 用户明确要求“最新 / 重新查询 / 重新评分”，或已知商机阶段、报价、销售记录、联系人、竞争对手、客户信息刚发生变更时，不复用旧数据包，必须重新调用脚本。
- 不满足可复用条件或时效条件时，只调用一次脚本查询评分所需全部数据，包括报价单与报价明细：

python scripts/query-diagnosis-data.py --opportunity-id "<opportunity_id>" --pretty

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `opportunity_id` | 是 | 已确认的 `NewOpportunityObj` 记录 ID。 |

脚本输出后，调用方消费脚本返回 JSON，并可把该 JSON 作为后续 `sfa-opportunity-diagnosis` 的 `Opportunity_Data_Package` 继续复用；不得拆分执行其他查询。

| JSON 路径 | 数据包 | 查询对象 | 评分用途 |
| --- | --- | --- | --- |
| `queried_at` | 数据包查询时间 | 脚本返回 | 判断当前上下文数据包是否仍可复用。 |
| `seller_context.seller_industry` | 卖方行业配置 | 脚本返回 | 评分依据中的卖方业务上下文。 |
| `buyer_industry` | 买方行业 | 来自关联客户行业字段 | 行业匹配度、业务价值和需求场景判断。 |
| `data.opportunity_full` | 商机全量记录 | `NewOpportunityObj` | 核对金额、阶段、预计成交日期、负责人、客户等核心事实。 |
| `data.account_full` / `data.account_fields` | 关联客户 | `AccountObj` | 补足客户画像、行业、状态、历史价值背景。 |
| `data.opportunity_contacts` | 商机联系人 | `NewOpportunityContactsObj` | 判断决策链覆盖、关键人识别、角色完整度。 |
| `data.contacts` | 联系人详情 | `ContactObj` | 补足联系人姓名、职位、部门等评分证据。 |
| `data.contact_relationships` | 联系人关系 | `NewOpportunityContactRelationshipObj` | 判断 Coach、影响链、支持度与隐性权力中心。 |
| `data.quotes` | 报价单 | `QuoteObj` | 判断商务成熟度、预算确认度与推进阶段。 |
| `data.quote_lines_by_quote_id` | 报价明细 | `QuoteLinesObj` | 判断产品结构、折扣、报价完整度；仅做内部定性判断。 |
| `data.active_records` | 销售记录 | `ActiveRecordObj` | 判断项目真实性、需求清晰度、客户关注点和推进动作。 |
| `data.competitive_lines` | 竞争对手明细 | `CompetitiveLinesObj` | 判断竞争态势，不得只靠商机主数据 `competitor` 字段给分。 |

## 3. 消费规则

- 必须消费脚本返回的 `data`、`seller_context`、`buyer_industry`、`errors`、`notes`。
- 当前上下文已有同一商机且未过期的 `Opportunity_Data_Package` 时，必须优先复用；不得为了评分重复查询同一批商机相关信息。
- `errors` 非空时不得忽略；若主商机可用但关联数据失败，允许降级评分，但必须在对应维度说明缺失的数据包及可信度影响。
- 报价金额、单价、折扣、竞对报价金额等敏感商务信息只用于内部判断商务成熟度、预算风险和竞争风险；评分依据只做定性描述，不逐条列示具体数值。
- 联系人、联系人关系、销售记录、竞争对手明细或报价明细为空时，只能标注证据不足或暂未发现明确记录，不得自动推断为不存在。
- 字段不存在或记录未体现时，不猜测，按评分标准保守给分。

## 4. 脚本返回状态

| `status` | 含义 | 处理 |
| --- | --- | --- |
| `READY` | 数据包已完成查询 | 消费完整 JSON 生成评分。 |
| `OPPORTUNITY_NOT_FOUND` | 已给 ID 但查不到主商机 | 阻断评分，说明商机主数据不可用。 |
| `ERROR` | sharecrm 调用或 JSON 解析失败 | 阻断或按错误范围降级，必须向用户说明。 |

`OPPORTUNITY_NOT_RESOLVED` 属于名称定位场景；本数据查询规范只接受确认后的商机 ID，正常不应出现该状态。
