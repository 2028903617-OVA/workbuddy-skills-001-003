# R09 - 团队 CRM 日志存储确认

## 目标

团队日报、团队周报、团队月报生成完成后，询问用户是否将本次报表保存到 CRM 日志对象 `JournalObj`。

本规则只负责“生成后确认”和“待写入内容整理”。面向用户只展示中文字段，不展示字段 ApiName。未获得用户明确确认前，不允许调用任何 CRM 写入能力。

生成报告时只展示中文保存预览，不构造 payload、不读取 `references/journal_object_reference.md`、不调用写入能力。只有用户明确确认保存后，才进入字段映射和 payload 构造。

团队日志的负责人和点评人默认回填当前管理者或当前用户本人。`owner` 和 `comment_by` 都是 employee 字段，内部 payload 必须传员工 ID 数组，例如 `["1000"]`；不要传人员姓名字符串。

日志保存日期必须复用 `R01_period_router.md` 和 `references/report_periods.md` 已解析出的时间窗口，不要重新按当前日期猜测：

- 日报：`journal_time` 使用日报对应日期。
- 周报：`journal_time` 使用 ISO 自然周周日，即 `period_end`。
- 月报：`journal_time` 使用自然月最后一天，即 `period_end`。

保存预览的“时间”可以展示日期范围；payload 的 `journal_time` 只能写单个 `yyyyMMdd` 日期。

## 触发时机

在团队日报、团队周报或团队月报正文和 HTML 交付完成后执行本规则。

## 确认话术

输出报表后，追加以下确认：

是否将本次团队[日报/周报/月报]保存到 CRM 日志？
确认后我会按下方内容写入；未确认前不会保存。

同时展示正文形式的中文写入预览，不要放进代码块：

- `## 📝 日志保存预览`
- 业务类型：日计划/周计划/月计划
- 时间：
- 本期工作总结：
- 下期工作计划：
- 心得体会：
- 点评人：

确认区只展示上述 6 个中文字段。不要展示日志编号、负责人、日志日期范围、关联业务模块、对象 ApiName 或字段 ApiName。

写入内容必须是纯文本，不包含 HTML 标签、Markdown 表格、CRM 日志保存确认模块或数据说明模块。本期工作总结和下期工作计划不要提炼，必须从对应报表模块原文详细回填；心得体会可从管理判断、风险复盘、团队经验和关键反思中适当提炼。

## 明确确认标准

只有用户明确表达以下意图，才可以进入写入步骤：

- 确认保存
- 确认写入
- 保存到 CRM
- 写入日志对象
- 保存到日志
- 是，保存

以下情况都不能写入：

- 用户没有回复
- 用户只说“看看、先这样、稍后”
- 用户要求修改报表
- 用户对字段内容有疑问
- 团队范围完全无法确认

## 确认后字段映射

只有用户明确确认保存后，才读取 `references/journal_object_reference.md` 并构造 payload。payload 必须包含：`journal_time`、`period_type`、`record_type`、`owner`、`comment_by`、`work_summary`、`work_plan`、`work_experience`。不要主动包含 `name`、`journal_time_range`、`related_object`、系统字段、除 `comment_by` 以外的评论字段、锁定状态和生命周期字段；如当前 CRM 强制要求其他字段，说明缺少必填字段并等待明确指令。

## 写入前检查

调用 CRM 写入能力前必须确认：用户已明确确认保存；已读取 `references/journal_object_reference.md`；团队范围或 AE 覆盖已在报表中说明；`journal_time` 已按周期规则转换为单个 `yyyyMMdd`（日报日期、周报 ISO 周日、月报自然月最后一天），且与报表标题和 CRM 查询周期一致；`period_type` 和 `record_type` 已按 `JournalObj` 字段定义或租户枚举确认；`owner` 与 `comment_by` 均为当前管理者或当前用户员工 ID 数组，例如 `["1000"]`。

字段来源必须保持：`work_summary` 从团队报表中能代表本期工作的模块原文详细回填，周报优先“本周关键结果、AE 表现与异常、重点客户与商机、跨 AE 风险”；`work_plan` 从团队行动计划 P0/P1/P2 原文详细回填，并保留优先级、负责人、动作、截止时间和验证标准；`work_experience` 由管理判断、风险复盘、团队经验和关键反思适当提炼。

## 写入能力处理

确认保存并完成字段映射后，只使用以下命令路径：

```bash
sharecrm data record create --object_api_name JournalObj --data '<JSON>'
```

不要把对象名、中文字段名或人员姓名字符串写入 `--data`；不要把 `journal_time` 写成带横线、时间或日期范围的格式；不要省略 `--object_api_name JournalObj`。

团队周报 payload 结构为 `{"data":{"journal_time":"<period_end_yyyyMMdd>","period_type":"<confirmed_period_type>","record_type":"<confirmed_record_type>","owner":["1000"],"comment_by":["1000"],"work_summary":"从团队关键结果、AE表现、重点客户与商机、跨AE风险原文详细回填的纯文本","work_plan":"从团队行动计划P0/P1/P2原文详细回填的纯文本","work_experience":"从管理复盘适当提炼的纯文本"},"details":{}}`。

命令示例：

```bash
sharecrm data record create --object_api_name JournalObj --data '{"data":{"journal_time":"<period_end_yyyyMMdd>","period_type":"<confirmed_period_type>","record_type":"<confirmed_record_type>","owner":["1000"],"comment_by":["1000"],"work_summary":"从团队关键结果、AE表现、重点客户与商机、跨AE风险原文详细回填的纯文本","work_plan":"从团队行动计划P0/P1/P2原文详细回填的纯文本","work_experience":"从管理复盘适当提炼的纯文本"},"details":{}}'
```

如果当前管理者或当前用户员工 ID 无法确认，不能试错写入，必须先查询或向用户确认。当前环境没有可用写入能力、CLI 不支持创建记录、无权限或写入失败时，不声称已经保存；说明失败原因，并输出仅包含上述字段的待写入 payload，便于人工处理或稍后重试。

## 成功输出

写入成功后返回：已保存到 CRM 日志；展示业务类型、时间、保存结果：成功。默认不展示记录 ID、`_id` 或长串主键，只有用户明确要求排查底层数据或定位记录时才补充。

## 禁止行为

不在用户确认前自动写入；不把 memory 等同于 CRM；不编造创建命令、记录 ID 或成功状态；不默认展示记录 ID、`_id` 或长串主键；不主动写入日志编号、日志日期范围、关联业务模块、非默认人员/评论字段、系统字段、锁定状态或生命周期字段；不把 HTML 标签、Markdown 表格、完整报表正文、详细版全文或保存确认模块写入 CRM 日志；不在面向用户的确认区展示字段 ApiName。
