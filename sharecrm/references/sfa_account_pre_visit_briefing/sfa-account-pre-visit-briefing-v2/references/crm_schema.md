# CRM 字段映射参考

仅在需要把原始 CRM 记录或用户粘贴的 CRM 文本映射到 R01-R05 字段时读取本文件。若字段含义已经清楚，正常简报不要加载。

## 见客简报需要的对象

| 对象 | 用途 | 对应规则 |
| --- | --- | --- |
| `AccountObj` | 客户身份与基础画像 | R01 |
| `NewOpportunityObj` | 当前商机、阶段、金额、赢率、预计结单日期 | R01、R05 |
| `ActiveRecordObj` | 最近互动、情绪、承诺、痛点证据 | R01-R03 |
| `ContactObj` | 联系人、职务、关键人标记、决策链线索 | R02 |
| Order object | 历史合作订单 | R09 full 模式 |
| Payment object | 回款与应收风险 | R09 full 模式 |

## 客户字段

| 字段 | 含义 | 映射到 |
| --- | --- | --- |
| `_id` | 客户 ID | `customer.account_id` |
| `name` | 客户名称 | `customer.name` |
| `industry` | 行业/细分赛道 | `customer.industry` |
| `employee_count` | 员工规模 | `customer.employee_count` |
| `annual_revenue` | 营收量级 | `customer.revenue_band` |
| `deal_status` | 未成交/已成交/多次成交 | `customer.deal_status` |
| `account_source` | 客户来源 | `customer.account_source` |
| `last_followed_time` | 最后跟进时间 | `customer.last_followed_time` |
| `create_time` | 客户入库时间 | 时效性/上下文 |
| `address` | 所在地 | `customer.location` |
| `website` | 官网，可用于公开信息检索 | 可选 |

客户 ID、客户名称、行业或细分赛道、规模均可用时，`basic_info=true`。

## 商机字段

| 字段 | 含义 | 映射到 |
| --- | --- | --- |
| `_id` | 商机 ID | `active_opportunity.opportunity_id` |
| `name` | 商机名称 | `active_opportunity.name` |
| `sales_stage` | 销售阶段 | `active_opportunity.stage` |
| `sales_status` | 进行中/赢单/输单/无效 | `active_opportunity.status` |
| `amount` | 商机金额 | `active_opportunity.amount` |
| `probability` | AE 录入的赢率 | `crm_probability` |
| `close_date` | 预计结单日期 | 风险和紧迫度 |
| `last_activity_time` | 最近商机动态时间 | 时效性 |
| `competitors` | 已知竞品 | R04 `competitors` |
| `budget_status` | 已批复/申请中/未知 | 会议目标 |
| `approval_flow` | 审批链路 | 决策链线索 |
| `notes` | 来源、触发事件、特殊背景 | R01-R03 |

如果有多个商机，优先选择与今天会议相关或最近活跃的进行中商机。

## 跟进记录字段

| 字段 | 含义 | 映射到 |
| --- | --- | --- |
| `_id` | 跟进记录 ID | 溯源 |
| `interactive_scenario` | 互动场景，如 POC、需求调研 | 会议上下文 |
| `interactive_types` | 电话、会议、拜访、邮件等 | 互动形式 |
| `create_time` | 跟进时间 | 时效性 |
| `active_record_content` | AE 跟进正文 | 痛点、决策链、承诺 |
| `sentiment` | 积极/中性/冷淡/负面 | 身份标签中的情绪温度 |
| `participants` | 参与人 | R02 决策链 |

最近 90 天内至少有一条有效互动时，`recent_interactions=true`。优先使用最近 3-5 条。

## 联系人字段

| 字段 | 含义 | 映射到 |
| --- | --- | --- |
| `_id` | 联系人 ID | 溯源 |
| `name` | 姓名 | R02 人员列表 |
| `job_title` | 职务 | 角色推断 |
| `primary_contact` 或 `is_primary` | CRM 关键联系人标记 | EB 候选 |
| `mobile`、`email` | 联系方式 | 最终简报通常不展示 |

除非用户明确需要，不要在简报中暴露私人联系方式。

## 互动场景枚举

场景值只能作为弱信号：

| 值 | 含义 | 可能用途 |
| --- | --- | --- |
| `product_introduction` | 产品介绍或初次见面 | 早期探需 |
| `requirements_research` | 需求调研 | 痛点提取 |
| `POC` | 方案讲解、演示或 POC | 阶段和必选条件提取 |
| `bidding` | 招投标或商务谈判 | 价格/采购风险 |
| `high_level_reporting` | 高层汇报 | EB 参与线索 |
| `project_launch` | 项目启动 | 售后上下文 |
| `customer_management` | 客户经营会 | 续约/增购上下文 |
| `closing_meeting` | 结项会 | memory/历史合作 |
| `default` | 其他 | 需要看正文 |

## 用户最小输入格式

没有 CRM 工具输出时，最小可用输入为：

```text
客户名称：
今天见谁：
会议目的：
当前阶段：
商机金额/赢率：
最近一次互动：
已知痛点：
已知竞品：
预算状态：
```

缺失字段应在 R01/R05 中列出，不要静默推断。
