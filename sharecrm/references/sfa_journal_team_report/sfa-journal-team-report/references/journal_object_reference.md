# CRM 日志对象 JournalObj 参考

本文件用于团队日报、团队周报、团队月报生成后的 CRM 日志保存确认。

对象 ApiName：`JournalObj`

## 默认写入字段

团队日报、周报、月报保存到 CRM 日志时，确认区展示 6 个中文字段：业务类型、时间、本期工作总结、下期工作计划、心得体会、点评人。内部 payload 默认写入 `journal_time`、`period_type`、`record_type`、`owner`、`comment_by`、`work_summary`、`work_plan`、`work_experience`。

无论用户选择简洁版还是详细版，写入 CRM 日志的内容都必须是纯文本，不包含 HTML 标签、Markdown 表格、完整报表全文或保存确认模块。本期工作总结和下期工作计划不要做提炼，必须从对应报表模块原文详细回填；心得体会可以适当提炼。

| 字段名称 | Api Name | 写入规则 |
|----------|----------|----------|
| 业务类型 | `record_type` | 面向用户展示为“日计划 / 周计划 / 月计划”；内部 payload 必须写 CRM 接受的枚举值，具体值需以 `JournalObj` 字段定义或已确认租户枚举为准 |
| 时间 | `journal_time` | payload 使用 `yyyyMMdd`；日报用日报对应日期，周报/月报使用已解析周期结束日，必须与报表标题和 CRM 查询周期一致 |
| 本期工作总结 | `work_summary` | 从团队报表中能代表本期工作的模块原文详细回填，不做提炼；周报优先回填“本周关键结果、AE 表现与异常、重点客户与商机、跨 AE 风险”，日报/月报使用对应关键结果、异常/风险和重点客户/商机模块 |
| 下期工作计划 | `work_plan` | 从团队行动计划 P0/P1/P2 原文详细回填，不做提炼，保留优先级、负责人、动作、截止时间和验证标准 |
| 心得体会 | `work_experience` | 从管理判断、风险复盘、团队经验和关键反思中适当提炼为纯文本 |
| 负责人 | `owner` | employee 字段；团队日志默认写入当前管理者或当前用户，payload 必须传员工 ID 数组，例如 `["1000"]` |
| 点评人 | `comment_by` | employee 字段；团队日志默认写入当前管理者或当前用户，保存预览展示姓名或“姓名（员工ID）”，payload 必须传员工 ID 数组，例如 `["1000"]` |

## 默认不主动写入字段

以下字段可能存在于 CRM 日志对象中，但本 skill 保存团队日报、周报、月报时不主动映射。

| 字段名称 | Api Name | 用途 |
|----------|----------|------|
| 日志编号 | `name` | 系统自动生成，由系统处理 |
| 关联业务模块 | `related_object` | 不主动填写 |
| 负责人主属部门 | `owner_department` | 不主动填写 |
| 归属部门 | `data_own_department` | 不主动填写 |
| 锁定状态 | `lock_status` | 不主动填写 |
| 生命状态 | `life_status` | 不主动填写 |
| 点评状态 | `comment_status` | 不主动填写 |
| 是否补交 | `is_delayed` | 不主动填写 |
| 日志日期范围 | `journal_time_range` | 不主动填写 |
| 外部负责人 | `out_owner` | 不主动填写 |
| 最后修改时间 | `last_modified_time` | 系统字段，不主动填写 |
| 创建时间 | `create_time` | 系统字段，不主动填写 |
| 最后修改人 | `last_modified_by` | 系统字段，不主动填写 |
| 创建人 | `created_by` | 系统字段，不主动填写 |

## 报表字段映射

| JournalObj 字段 | 来源 |
|-----------------|------|
| `record_type` | 面向用户展示为日计划/周计划/月计划；内部 payload 使用 CRM 枚举值，具体值需以 `JournalObj` 字段定义或已确认租户枚举为准 |
| `journal_time` | `yyyyMMdd` 格式；日报用日报对应日期，周报/月报使用已解析周期结束日，必须与报表标题和 CRM 查询周期一致 |
| `work_summary` | 团队报表关键业务模块的原文详细回填，不做提炼 |
| `work_plan` | 团队行动计划 P0/P1/P2 的原文详细回填，不做提炼 |
| `work_experience` | 管理判断、风险复盘、团队经验和关键反思的适当提炼 |
| `owner` | employee 字段，必须传当前管理者或当前用户员工 ID 数组，例如 `["1000"]` |
| `comment_by` | employee 字段，必须传当前管理者或当前用户员工 ID 数组，例如 `["1000"]`；保存预览展示姓名或“姓名（员工ID）” |
| `period_type` | 周期辅助字段；仅在 CRM 创建日志需要时写入，具体值需以 `JournalObj` 字段定义或已确认租户枚举为准 |

## Payload 模板

内部写入 payload 默认只包含：

- 命令参数 `--object_api_name JournalObj`
- `data.journal_time`
- `data.period_type`
- `data.record_type`
- `data.owner`，值为当前管理者或当前用户员工 ID 数组，例如 `["1000"]`
- `data.comment_by`，值为当前管理者或当前用户员工 ID 数组，例如 `["1000"]`
- `data.work_summary`
- `data.work_plan`
- `data.work_experience`
- `details`，默认 `{}`

不要在 `data` 中主动加入 `name`、`journal_time_range`、`related_object` 或其他非默认字段。不要把 `object_api_name` 或 `object_data` 放进 `--data` JSON 内。

如果当前 CRM 创建接口返回非默认字段必填错误，不要自动补填；说明缺少的必填字段，并等待用户或系统明确要求。

## 写入约束

- 写入前必须先让用户确认待写入内容。
- 面向用户的确认区只展示中文字段名，不展示 ApiName。
- 确认区只展示业务类型、时间、本期工作总结、下期工作计划、心得体会、点评人。
- 确认区展示的时间必须与报表标题和 CRM 查询范围一致；内部 `journal_time` 必须是单个 `yyyyMMdd` 日期，日报用日报对应日期，周报用 ISO 自然周周日，月报用自然月最后一天。
- 本期工作总结、下期工作计划、心得体会必须是纯文本，不包含 HTML 标签、Markdown 表格、完整报表正文、详细版全文或保存确认模块。
- 本期工作总结和下期工作计划必须原文详细回填，不做提炼；心得体会可以适当提炼。
- 负责人和点评人默认都是当前管理者或当前用户；确认区展示点评人姓名，payload 写员工 ID 数组；无法确认员工 ID 时不要写入，先向用户确认或查询。
- 未确认前不调用 CRM 创建能力。
- 非默认字段、系统字段、除 `comment_by` 以外的评论字段、锁定状态和生命周期字段不主动填写。
- 写入失败时返回失败原因和 payload，不声称已保存。
