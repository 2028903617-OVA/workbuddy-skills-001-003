# HTML 自适应设计参考

本文件用于个人日报、个人周报、个人月报的 HTML 输出。目标是让同一份 HTML 在手机端和 Web 端都易读、专业、稳定。

个人周报 HTML 需要对标商机赢单教练/商机诊断输出物的“结论先行、风险可见、行动明确”，但视觉上采用 AI-native 产品周报风格：干净浅色工作台、紧凑摘要、经营信号卡片、风险承诺与下周动作。它不是营销页，也不是流水日志页。

## 页面原则

- 单页 HTML，默认不依赖外部资源。
- Mobile-first：先保证手机端单列阅读，再增强桌面端布局。
- 页面像 AI-native 销售工作台里的 Weekly Brief，不像传统深色封面报告。
- 内容顺序与个人报表一致；日报 HTML 应突出今日执行闭环和数据覆盖，周报 HTML 应使用轻量周报呈现：顶部信息、周度健康状态、本周 AI 摘要、关键经营信号、本周结果、重点客户与商机、风险与承诺、下周动作、复盘与数据说明。
- 不展示对象 ApiName、记录 ID、系统字段。

## 布局规则

- 主容器：移动端单列；桌面端使用 `max-width: 1320px; margin: 0 auto;` 的工作台布局。
- 手机端：所有模块单列排列，目录隐藏，操作卡片纵向堆叠。
- 桌面端：允许左侧目录 + 右侧正文；指标卡、摘要卡、行动块可多列；正文模块仍保持清晰纵向阅读。
- 顶部：使用轻量 topbar + hero，不使用大面积深色封面；展示报告标题、销售人员、周期、核心健康状态和关键标签。
- 色彩：背景使用白色/浅灰；logo 色 `#ffb400` 只作为状态点、细线、标签和重点数字强调。不要使用深橙、棕色或大面积橙黄色渐变。
- 表格：必须有横向滚动容器 `.table-wrap { overflow-x: auto; }`。
- 长文本：允许换行，不使用固定高度截断关键内容。
- P0/P1/P2：使用标签、顶部细线或浅色背景区分，参考商机诊断的风险优先级表达；不要使用高饱和大色块。
- 数据说明：作为备注区弱化展示，建议使用小字号、灰色文字、浅色背景或左边线；不要做成醒目业务卡片。
- 日报数据缺失场景：仍保留摘要、执行信号、今日结果、重点跟进、风险、明日行动、待办与数据说明；用“待确认/需补录/需排查”明确缺口，不用空卡片撑版面。

## 推荐 CSS 片段

```css
* {
  box-sizing: border-box;
}

:root {
  --accent: #ffb400;
  --accent-soft: #fff8db;
  --text: #111827;
  --muted: #6b7280;
  --bg: #f7f8fb;
  --card: #ffffff;
  --border: #e5e7eb;
  --radius: 8px;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.6;
  color: #374151;
  background: linear-gradient(180deg, #ffffff 0, var(--bg) 320px), var(--bg);
}

.app-shell {
  max-width: 1320px;
  margin: 0 auto;
  padding: 28px 24px 56px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 0 22px;
  border-bottom: 1px solid var(--border);
}

.brand-mark {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background: var(--accent);
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 22px;
  padding: 30px 0 26px;
}

.health-panel,
.section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 10px 24px rgba(17, 24, 39, .035);
}

.health-panel {
  padding: 18px;
}

.layout {
  display: grid;
  grid-template-columns: 236px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.toc {
  position: sticky;
  top: 16px;
  max-height: calc(100vh - 32px);
  overflow-y: auto;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, .82);
}

.section {
  padding: 20px;
  margin-bottom: 18px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 16px;
  color: var(--text);
  font-size: 19px;
}

.section-title::after {
  content: "";
  height: 2px;
  flex: 1;
  background: linear-gradient(90deg, var(--accent), rgba(255, 180, 0, 0));
}

.brief-box {
  background: #fbfcfe;
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius);
  padding: 16px 18px;
}

.metric-grid,
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.metric-card,
.summary-card,
.action-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  background: #fbfcfe;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 640px;
}

th,
td {
  border-bottom: 1px solid var(--border);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 1080px) {
  .hero,
  .layout {
    display: block;
  }

  .toc {
    display: none;
  }

  .health-panel {
    margin-top: 18px;
  }
}

@media (max-width: 760px) {
  .app-shell {
    padding: 18px 12px 38px;
  }

  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  h1 {
    font-size: 26px;
  }

  .section {
    padding: 16px;
  }

  .summary-grid,
  .metric-grid,
  .action-grid {
    grid-template-columns: 1fr;
  }
}

@media print {
  body {
    background: #ffffff;
  }

  .toc {
    display: none;
  }

  .section {
    break-inside: avoid;
    box-shadow: none;
    border-color: #d1d5db;
  }
}
```

## 表格与手机端

个人报表中关键指标可以保留表格，但必须处理手机端：

- 简单表格：使用 `.table-wrap` 横向滚动。
- 非指标模块：优先使用短段落、项目符号或卡片，不要把客户跟进写成宽表。
- 同一客户或商机的多条记录先合并，再进入 HTML，避免手机端重复刷屏。

## 周报 AI Brief 模块

个人周报 HTML 必须尽量使用以下模块名或等价结构：

- 本周 AI 摘要：一句话总评、关键数字、最大风险、下周打法。
- 关键经营信号：成交/回款、Pipeline、新增客户/商机、待办兑现率、重点跟进数。
- 本周结果：成果、证据、价值。
- 重点客户与商机：金额、阶段、关键人、动作、承诺、卡点、下周动作。
- 风险与承诺：P0/P1/P2、承诺状态、风险依据、深层判断、应对动作。
- 下周动作：P0/P1/P2，包含对象、动作、截止时间、完成标志。
- 复盘与数据说明：有效打法、无效动作、下周调整、CRM 数据覆盖。

## HTML 内容限制

- HTML 中的 CRM 数据说明只能使用中文对象名。
- 不输出 `_id`、记录 ID、数据 ID 或长串主键。
- 不输出 `JournalObj`、`NewOpportunityObj` 等对象 ApiName。
- 不输出 `work_summary`、`work_experience`、`journal_time` 等字段 ApiName。
- 不把“生成 HTML”描述为“已保存到 CRM”。

## 验收标准

生成 HTML 前检查：

1. 有 viewport。
2. 手机端单列可读。
3. 桌面端宽度不超过主容器。
4. 目录在桌面端可用，移动端隐藏。
5. 指标卡、行动卡和表格不会撑破屏幕。
6. 没有深橙、棕色或大面积橙黄色渐变。
7. P0/P1/P2 优先级清晰。
8. 数据说明弱化展示。
