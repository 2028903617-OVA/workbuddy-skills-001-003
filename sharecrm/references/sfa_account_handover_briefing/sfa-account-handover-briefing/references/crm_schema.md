# CRM 字段映射参考

仅在需要解释原始 CRM 字段、用户粘贴数据或 CLI 查询结果时读取本文件。团队交接简报应优先使用 Memory 中的历史和关系信息，再用 CRM 校准事实。

## Handover 主要对象

| 对象 | 中文名称 | 交接用途 |
| --- | --- | --- |
| `AccountObj` | 客户 | 客户画像、客户状态、归属背景 |
| `NewOpportunityObj` | 商机 | 当前/历史商机、阶段、金额、预算、输赢状态 |
| `ContactObj` | 联系人 | 关键人地图、接手联络顺序、角色候选 |
| `ActiveRecordObj` | 销售记录/跟进动态 | 博弈编年、客户原话、承诺、情绪、敏感点 |
| `CompetitiveLinesObj` | 竞品明细 | 竞品历史、报价、优劣势、输赢结果 |
| `ContractObj` | 合同 | 历史合作、续约窗口、合同状态 |
| `SalesOrderObj` | 销售订单 | 订单、回款、应收、历史合作金额 |
| `PaymentObj` | 回款 | 回款流水，若环境中存在独立回款对象 |
| `PersonnelObj` | 人员 | 原 AE、接手 AE、CSM、售前、实施负责人 |
| `ScheduleObj` | 日程 | 已约会议、未来交接或客户沟通安排 |
| `CheckinsObj` | 外勤签到 | 现场拜访历史和拜访频率 |

客户健康、CSM 预警、流失原因等可能由不同企业通过自定义对象或自定义字段承载。通用交接规则不得硬编码任何企业租户自定义 API 名；只有在用户提供字段说明、当前租户 schema 可确认，或企业标准 reference 已明确时，才可读取并解释。

## AccountObj 客户字段

| 字段 | 含义 | 映射到 |
| --- | --- | --- |
| `_id` | 客户 ID | 交接记录溯源 |
| `name` | 客户名称 | 简报标题和客户画像 |
| `industry` | 行业/细分赛道 | 行业背景、风险假设 |
| `employee_count` | 员工规模 | 客户规模 |
| `annual_revenue` | 营收量级 | 客户价值和财务背景 |
| `deal_status` | 成交状态 | 新客户/已成交/多次成交/沉默客户 |
| `account_source` | 客户来源 | 项目起源 |
| `last_followed_time` | 最后跟进时间 | 接手紧急度和信息时效 |
| `create_time` | 客户入库时间 | 客户历史长度 |
| `address` | 所在地 | 区域与拜访背景 |
| `website` | 官网 | 可选公开信息检索 |

用户提供 CRM 截图、链接或记录 ID 时，`_id` 是客户主记录的优先精确定位键。名称检索未命中但 `_id` 能查到记录时，以 `_id` 查询结果为准，并把名称检索状态写成“名称检索未命中”，不要写成“CRM 无客户”。

## NewOpportunityObj 商机字段

| 字段 | 含义 | 交接关注点 |
| --- | --- | --- |
| `_id` | 商机 ID | 溯源 |
| `name` | 商机名称 | 当前/历史商机 |
| `sales_stage` | 销售阶段 | 接手人判断项目所处位置 |
| `sales_status` | 商机状态 | 进行中、赢单、输单、无效 |
| `amount` | 商机金额 | 客户价值与优先级 |
| `probability` | AE 录入赢率 | 原 AE 主观信心，不等于预测 |
| `close_date` | 预计结单日期 | 时间压力 |
| `budget_status` | 预算状态 | 预算是否需要接手人核对 |
| `approval_flow` | 审批链路 | 决策链和内部政治 |
| `competitors` | 已知竞品 | 竞品历史 |
| `notes` | 商机备注 | 项目起源、特殊背景、敏感点 |

多个商机并存时，交接简报应区分：进行中商机、历史赢单、历史输单、搁置商机。

## ContactObj 联系人字段

| 字段 | 含义 | 交接关注点 |
| --- | --- | --- |
| `_id` | 联系人 ID | 溯源 |
| `name` | 姓名 | 关键人地图 |
| `job_title` | 职务 | EB/TB/UX/Coach/Gatekeeper 候选判断 |
| `primary_contact` / `is_primary` | CRM 主联系人标记 | 主联系人，不等同于最终决策人 |
| `mobile` / `email` | 联系方式 | 交接场景可展示给接手人，但应避免对外暴露 |

角色判断必须结合 Memory 和互动证据。不能只因为职位高就确认 EB，也不能只因为频繁沟通就确认 Coach。

## ActiveRecordObj 跟进记录字段

| 字段 | 含义 | 交接关注点 |
| --- | --- | --- |
| `interactive_scenario` | 互动场景 | 需求调研、POC、商务谈判、客户经营会等 |
| `interactive_types` | 互动方式 | 电话、在线会议、现场拜访、邮件 |
| `active_record_content` | 跟进正文 | 客户原话、承诺、反对意见、参会人、情绪、下一步 |
| `create_time` | 记录时间 | 博弈编年排序 |

互动场景只能作为弱信号，必须阅读正文。正文中的承诺、未兑现、客户原话、参会人变化和情绪变化优先级最高。

## CompetitiveLinesObj 竞品明细字段

| 字段 | 含义 | 交接关注点 |
| --- | --- | --- |
| `_id` | 竞品明细 ID | 溯源 |
| `name` | 明细名称 | 竞品记录 |
| `competitor_id` | 竞品 | 竞品名称或竞品对象 ID |
| `advantage` | 竞品优势 | 客户认可竞品的原因 |
| `weaknesses` | 竞品弱点 | 我方可用的差异化空间 |
| `quotation_amount` | 竞品报价 | 商务压力 |
| `is_win` | 竞品是否赢单 | 历史结果或当前结果 |

## full 模式对象

### ContractObj

| 字段 | 含义 | 交接关注点 |
| --- | --- | --- |
| `_id` | 合同 ID | 溯源 |
| `name` | 合同名称 | 历史合作项目 |
| `contract_amount` | 合同金额 | 历史客户价值 |
| `started_time` | 合同开始时间 | 合作周期 |
| `expired_time` | 合同到期时间 | 续约窗口 |
| `status` | 合同状态 | 生效、到期、终止等 |

### SalesOrderObj

| 字段 | 含义 | 交接关注点 |
| --- | --- | --- |
| `_id` | 订单 ID | 溯源 |
| `name` | 订单名称 | 历史订单 |
| `order_amount` | 订单金额 | 历史成交金额 |
| `order_status` | 订单状态 | 执行中、已完成、终止等 |
| `payment_amount` | 已回款金额 | 回款健康 |
| `receivable_amount` | 应收金额 | 回款风险 |

## 最小可用输入

没有 CLI 或 CRM 工具输出时，最小输入为：

```text
客户名称：
交接原因：
原负责人：
接手人：
当前商机/合作状态：
最近一次互动：
关键联系人：
待兑现承诺：
已知风险或敏感点：
竞品情况：
```

缺失项进入“交接缺口”，不要静默补齐。
