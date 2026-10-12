# R10 - HTML 自适应报告输出

## 目标

生成个人日报、个人周报或个人月报时，默认将已生成的 Markdown 正文同步转换成可在手机端和 Web 端阅读的单页 HTML。Markdown 正文必须先在对话中完整展开输出；`.md` 文件只是归档物，不能替代对话内正文。同一份报告只执行一次 HTML 生成。

HTML 是展示形态，不改变个人报表的分析逻辑、数据来源优先级和 CRM 日志保存确认规则。

个人日报、周报、月报的 HTML 必须保持统一品牌风格，但信息架构必须随周期变化：

- 日报：今日执行闭环，突出今日结果、待办闭环、今日风险和明日行动。
- 周报：销售战报，突出经营信号、承诺对账、重点商机、风险和下周打法。
- 月报：月度经营复盘，突出目标完成、Pipeline 结构、重点客户复盘、损失原因和下月策略。

## 执行条件

本规则默认执行；“生成 HTML、导出 HTML、网页版、手机查看、自适应页面、H5、用浏览器打开、做成页面”只是加强 HTML 交付意图。只有用户明确说“只要 Markdown、不要 HTML、不用网页、不生成 HTML”时，才跳过本规则。

如果本轮已经基于同一份 Markdown 写出 `.html`，不要再次输出完整 HTML 或生成第二个 HTML 文件；只返回已生成路径。

## 执行顺序

本规则只负责把已完成的 Markdown 报表渲染为 HTML，不重新路由、不重新读取周期规则、不重新查询 CRM、不触发 R09 保存确认。输入必须复用总流程已确定的周期、销售人员、时间范围、数据说明和同一份 Markdown 正文。

1. 确认 Markdown 正文已经完整生成并已在对话中展示。
2. 直接使用 `assets/personal_report_template.html` 作为 HTML 模板。
3. 将个人报表正文映射到模板占位符；日报、周报、月报必须填入不同的周期标签、模块标题和主体内容，不得只替换标题。
4. 如果运行环境允许写文件，写出同前缀 `.md` 归档和一个完整单文件 HTML；不能写文件时，在 Markdown 正文后输出一次完整 HTML 内容。
5. 在回复末尾提供可直接打开的 `.html` 路径，并附上 `.md` 归档路径。

正常生成不得读取 `references/html_responsive_design_reference.md`；只有模板缺失、用户要求修改响应式样式、或生成后出现明显布局问题需要排查时才读取。

## 内容映射

将 Markdown 模块映射到模板区域：标题/人员/时间范围 -> 顶部信息区；摘要 -> 周期摘要区；关键指标 -> 周期信号区；成果 -> 结果区；客户与商机 -> 客户/商机区；复盘 -> 复盘区；承诺与风险 -> 风险区；下一步行动 -> 行动区；数据说明 -> 页面底部弱化说明。CRM 日志保存确认可以留在 HTML 之后的对话确认，不必写入 HTML 主体。

优先使用 `assets/personal_report_template.html` 并填满模板占位符。缺失数据时用“待确认 / 信息不足 / CRM数据覆盖待确认”，不要留裸占位符。关键占位符包括：`{{health_score}}`、`{{health_grade}}`、`{{report_type}}`、`{{period_class}}`、`{{data_scope}}`、`{{brand_text}}`、`{{period_brief_label}}`、`{{subtitle}}`、`{{health_aria_label}}`、`{{health_label}}`、`{{toc_title}}`、`{{summary_label}}`、`{{metrics_label}}`、`{{results_label}}`、`{{opportunities_label}}`、`{{risks_label}}`、`{{actions_label}}`、`{{review_label}}`、`{{cover_tags}}`、`{{executive_summary}}`。旧生成链路至少要填满 `summary_cards`、`metrics`、`customer_opportunity`、`commitments_risks` 和 `p0/p1/p2_actions`。

模板固定文案必须适配中文环境：不要保留英文品牌、英文报告类型、英文健康度或英文目录。日报、周报、月报的顶部、目录、健康度标签和模块标题必须随周期变化。

## 分周期 HTML 结构

| 周期 | 顶部/健康标签 | 模块顺序 |
| --- | --- | --- |
| 日报 | “个人日报速览 / 今日执行闭环”；“今日闭环度/今日健康度” | 今日摘要、今日执行信号、今日结果、重点跟进、今日风险、明日行动、待办与数据说明 |
| 周报 | “个人周报速览 / 销售战报”；“周度健康度” | 本周摘要、关键经营信号、承诺对账/本周结果、重点客户与商机、承诺与风险、下周动作、复盘与数据说明 |
| 月报 | “个人月报速览 / 月度经营复盘”；“月度完成度/月度健康度” | 月度摘要、目标完成、成交与 Pipeline 结构、重点客户复盘、主要风险与损失、下月策略与行动、月度趋势与数据说明 |

没有足够数据时仍保留关键区块并标注“待确认”，不能空白或只写“无数据”。日报数据缺失时，必须突出“数据缺失诊断 + 待确认 + 补录 P0”。月报必须突出结构判断，不展示按周流水清单。

## HTML 输出要求

- 输出必须是完整 HTML 文档，包含 `<!doctype html>`、`html`、`head`、`body`。
- 必须包含 `<meta name="viewport" content="width=device-width, initial-scale=1.0">`。
- CSS 优先内联在 `<style>` 中，避免依赖外部 CSS、字体或 CDN。
- 页面默认 mobile-first，桌面端通过 media query 增强布局。桌面端可以使用左侧目录 + 右侧正文布局；移动端目录必须隐藏。
- 不使用固定大宽度容器；主体容器使用 `max-width` 和响应式 padding。参考商机诊断输出物时，`max-width` 可放宽到约 1200-1320px。
- 指标区域使用 responsive grid。
- 表格必须包在横向滚动容器中；非关键指标模块优先用短段落或列表。
- 颜色克制，适合专业销售个人日志；使用白色/浅灰工作台背景，logo 色 `#ffb400` 只作为小面积强调，如状态点、标签、细线、重点数字，不要使用深橙、棕色或大面积橙黄色渐变。
- 支持浏览器打印，至少提供 `@media print` 基础样式。

## 用户可见数据限制

- 不展示 `JournalObj`、`ActiveRecordObj` 等对象 ApiName。
- 不展示 `_id`、记录 ID、数据 ID 或长串主键。
- 不展示 `work_summary`、`journal_time` 等字段 ApiName。
- CRM 数据说明使用中文对象名，例如“日志、销售记录、日程、商机、订单、回款”。
- 系统字段、锁定状态、生命周期字段不进入 HTML。

## 文件交付

如果运行环境允许写文件，成对交付同前缀文件：`personal-report-[period]-[date-or-range].md` 和 `personal-report-[period]-[date-or-range].html`，例如 `personal-report-weekly-<YYYY-WXX>.md/html`。对话中仍要直接完整展示 Markdown 正文；不要只交付路径、只交付 `.md` 或 `.html`，也不要同时生成“简洁版 HTML”和“完整版 HTML”。不能写文件时，先输出 Markdown 正文，再输出一次完整 HTML 内容。

## 禁止行为

- 不把 HTML 输出当成已保存 CRM。
- 不在用户未确认前写入 CRM 日志。
- 不为了美观删减关键风险、承诺对账、下一步行动或数据说明。
- 不输出依赖外网才能正常显示的 HTML。
- 不在 HTML 中暴露系统字段、对象 ApiName 或记录 ID。
