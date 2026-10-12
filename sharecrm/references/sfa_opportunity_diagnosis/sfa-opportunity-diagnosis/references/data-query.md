# 商机（NewOpportunityObj）数据查询配置 — Data_Query_Config

商机诊断先定位唯一商机；确认商机 ID 后，诊断所需 CRM 数据优先复用当前上下文中同一商机的脚本返回数据包；没有可复用数据包时，统一调用一次本 skill 内置脚本查询。不得在脚本已覆盖的数据包上重复手工拼接 `sharecrm` 命令。

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

调用方只读取 `seller_context.seller_industry` 作为 `SELLER_INDUSTRY`，不得额外手工调用 `sharecrm sales get-config-by-key`。`seller_context.seller_industry` 为空时，所有远端 knowhow 检索的 `coreTopics` 不拼接行业，并在输出标注“缺少卖方行业信息”。

## 1. 对象定位

sharecrm data record query-id-by-name --data '{"query":"<商机名称>","apiNames":["NewOpportunityObj"]}'

未命中时模糊兜底（候选 ≥2 时展示 `_id` / `name` / `account_id__r` 供选择）：

sharecrm data record query-by-fields --object_api_name NewOpportunityObj --select_fields "_id,name,account_id" --name-like "<关键词>" --limit 10 --sort last_modified_time:desc --raw

对象定位阶段只负责得到唯一 `<opportunity_id>`；不得在此阶段生成诊断结论。

## 2. 查询范围

确认商机 ID 后，先检查当前上下文是否已有 `Opportunity_Data_Package`：

- 可复用条件：`opportunity_id` 与当前商机一致、`status=READY`、包含 `data.opportunity_full`、`seller_context`、`buyer_industry`、`errors`、`notes`。
- 时效条件：包含 `queried_at`，且 `queried_at` 距当前时间不超过 30 分钟。
- 满足可复用条件时，直接消费该 JSON 数据包，不再调用脚本。
- 用户明确要求“最新 / 重新查询 / 重新诊断”，或已知商机阶段、报价、销售记录、联系人、竞争对手、客户信息刚发生变更时，不复用旧数据包，必须重新调用脚本。
- 不满足可复用条件或时效条件时，只调用一次脚本查询诊断所需全部数据，包括报价单与报价明细：

python scripts/query-diagnosis-data.py --opportunity-id "<opportunity_id>" --pretty

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `opportunity_id` | 是 | 已确认的 `NewOpportunityObj` 记录 ID。 |

脚本输出后，调用方消费脚本返回 JSON，并可把该 JSON 作为后续诊断的 `Opportunity_Data_Package` 继续复用；不得拆分执行其他查询。

| JSON 路径 | 数据包 | 查询对象 | 诊断用途 |
| --- | --- | --- | --- |
| `queried_at` | 数据包查询时间 | 脚本返回 | 判断当前上下文数据包是否仍可复用。 |
| `seller_context.seller_industry` | 卖方行业配置 | 脚本返回 | 远端 knowhow 检索主题与输出缺口标注。 |
| `buyer_industry` | 买方行业 | 来自关联客户行业字段 | 行业上下文判断，不替代商机主数据。 |
| `data.opportunity_full` | 商机全量记录 | `NewOpportunityObj` | 唯一的商机主数据来源；核对金额、联系人、时间、预算、系统阶段与状态等核心事实。 |
| `data.account_full` / `data.account_fields` | 关联客户 | `AccountObj` | 补足客户画像、状态、行业、价值背景。 |
| `data.opportunity_contacts` | 商机联系人 | `NewOpportunityContactsObj` | 识别角色、关键人、支持度与触达层级。 |
| `data.contacts` | 联系人详情 | `ContactObj` | 补足联系人姓名、职位、部门等详情。 |
| `data.contact_relationships` | 联系人关系 | `NewOpportunityContactRelationshipObj` | 判断真假决策者、Coach、反对者与隐性权力中心。 |
| `data.quotes` | 报价单 | `QuoteObj` | 判断商务成熟度、报价阶段、预算/竞争风险。 |
| `data.quote_lines_by_quote_id` | 报价明细 | `QuoteLinesObj` | 判断产品、单价、折扣、报价结构；仅做内部定性判断。 |
| `data.active_records` | 销售记录 | `ActiveRecordObj` | 识别客户关注点、推进卡点、竞品动作和下一步动作。 |
| `data.competitive_lines` | 竞争对手明细 | `CompetitiveLinesObj` | 校验竞争态势，不得只靠商机主数据 `competitor` 字段下结论。 |

## 3. 消费规则

- 必须消费脚本返回的 `data`、`seller_context`、`buyer_industry`、`errors`、`notes`。
- 当前上下文已有同一商机且未过期的 `Opportunity_Data_Package` 时，必须优先复用；不得为了诊断重复查询同一批商机相关信息。
- `errors` 非空时不得忽略；若主商机可用但关联数据失败，允许降级诊断，但必须标注缺失的数据包及可信度影响。
- 报价金额、单价、折扣、竞对报价金额等敏感商务信息只用于内部判断商务成熟度、预算风险和竞争风险；输出正文只做定性描述，不逐条列示具体数值。
- 联系人、联系人关系、销售记录、竞争对手明细或报价明细为空时，只能标注证据不足或暂未发现明确记录，不得自动推断为不存在。
- `AI_Stage` 不由脚本返回或由其他 skill 提供；调用方必须根据数据包内的系统阶段、系统状态、销售记录、报价和联系人事实，按 `SKILL.md` Workflow 第 5 步直接判断。评分（`Scoring_Result`）优先通过 `sharecrm sales profile get_profile_score --objectApiName NewOpportunityObj --objectId <opportunity_id>` 获取并校验对象一致；CLI 失败、空结果、无评分信息或对象不一致时，调用 `sfa-opportunity-score` 获取同一商机评分，详见 `SKILL.md`。

## 4. 脚本返回状态

| `status` | 含义 | 处理 |
| --- | --- | --- |
| `READY` | 数据包已完成查询 | 消费完整 JSON 生成诊断。 |
| `OPPORTUNITY_NOT_FOUND` | 已给 ID 但查不到主商机 | 阻断诊断，说明商机主数据不可用。 |
| `ERROR` | sharecrm 调用或 JSON 解析失败 | 阻断或按错误范围降级，必须向用户说明。 |

`OPPORTUNITY_NOT_RESOLVED` 属于名称定位场景；本数据查询规范只接受商机 ID，正常不应出现该状态。
