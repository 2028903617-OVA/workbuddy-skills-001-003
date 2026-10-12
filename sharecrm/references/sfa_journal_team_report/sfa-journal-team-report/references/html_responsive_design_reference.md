# HTML 自适应设计参考

本文件用于团队日报、团队周报、团队月报的 HTML 输出。目标是让同一份 HTML 在手机端和 Web 端都易读、专业、稳定。

当输入包含 Excel / xlsx / 多页签表格时，HTML 必须把多个 sheet 转成横向导航页签。页面应像销售主管的经营工作台：先看总览和管理判断，再进入成交、Pipeline、AE、客户、风险与数据说明。

## 页面原则

- 单页 HTML，默认不依赖外部资源。
- Mobile-first：先保证手机端单列阅读，再增强桌面端布局。
- 页面像团队经营看板，不像营销落地页。
- 横向导航页签是多 sheet 转 HTML 的核心交互；不要把多个 sheet 上下堆成长页面。
- 每个页签都要包含“洞察 + 表格/明细 + 管理动作或判断”，不能只搬表格。
- 不展示对象 ApiName、记录 ID、系统字段。

## 横向页签结构

推荐页签顺序：

1. 总览
2. 成交明细
3. Pipeline
4. AE 表现
5. 客户复盘
6. 风险行动
7. 数据说明

页签命名可根据附件 sheet 名调整，但必须保持业务语义清晰。典型映射：

- `月度汇总` / `周度汇总` -> `总览`
- `成交明细` / `订单` / `回款` -> `成交明细`
- `Pipeline明细` / `商机` -> `Pipeline`
- `AE表现分层` -> `AE 表现`
- `重点客户复盘` / `重点客户/行业复盘` -> `客户复盘`
- `风险与行动计划` -> `风险行动`
- `数据说明` -> `数据说明`

分周期页签可在同一模板上调整命名和权重：

- 团队日报：总览、AE 今日异常、重点商机异动、风险行动、数据说明；不展示成交明细和 Pipeline 空页签。
- 团队周报：总览、成交与回款、Pipeline、AE 表现、客户复盘、风险行动、数据说明；总览或风险行动必须包含上周 P0/P1 管理动作闭环。
- 团队月报：总览、成交结构、Pipeline 结构、AE 分层趋势、客户/行业复盘、管理问题与下月策略、数据说明；必须体现团队活跃度、Pipeline 集中度、数据质量风险、下月资源配置和管理节奏。

## 布局规则

- 主容器：`max-width: 1360px; margin: 0 auto; padding: 24px;`
- 顶部：轻量 topbar + 报告标题 + 团队范围 + 周期 + 数据口径 + 团队健康度。
- 横向页签：桌面端 sticky tabs，移动端横向滚动；当前页签高亮。
- 手机端：所有模块单列排列，宽表横向滚动。
- 桌面端：总览可用左右分栏；指标卡、摘要卡、行动块可多列。
- 表格：必须有横向滚动容器 `.table-wrap { overflow-x: auto; }`。
- 长文本：允许换行，不使用固定高度截断关键内容。
- P0/P1/P2：使用标签、顶部细线或浅色背景区分；不要使用高饱和大色块。
- 数据说明：作为备注页签弱化展示，使用小字号、灰色文字、浅色背景或左边线。
- 打印：`@media print` 中隐藏 tabs，并展开所有 tab panel。

## 推荐 CSS/JS 结构

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
  background: linear-gradient(180deg, #ffffff 0, var(--bg) 360px), var(--bg);
}

.report-shell {
  max-width: 1360px;
  margin: 0 auto;
  padding: 26px 24px 56px;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 22px;
  padding: 30px 0 24px;
}

.tabs-wrap {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: 10px 0;
  background: rgba(247, 248, 251, .92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

.tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.tab-button {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: #ffffff;
  color: var(--muted);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 720;
  padding: 8px 12px;
  white-space: nowrap;
}

.tab-button[aria-selected="true"] {
  color: var(--text);
  background: var(--accent-soft);
  border-color: #ffe08a;
}

.tab-panel {
  display: none;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 18px;
}

.tab-panel.active {
  display: block;
}

.metric-grid,
.summary-grid,
.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(188px, 1fr));
  gap: 12px;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}

th,
td {
  border-bottom: 1px solid var(--border);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}

@media (max-width: 1080px) {
  .hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .report-shell {
    padding: 18px 12px 38px;
  }

  h1 {
    font-size: 26px;
  }

  .tab-panel {
    padding: 16px;
  }

  .metric-grid,
  .summary-grid,
  .action-grid {
    grid-template-columns: 1fr;
  }
}

@media print {
  body {
    background: #ffffff;
  }

  .tabs-wrap {
    display: none;
  }

  .tab-panel {
    display: block !important;
    break-inside: avoid;
  }
}
```

```html
<script>
  (function () {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.tab-button'));
    var panels = Array.prototype.slice.call(document.querySelectorAll('.tab-panel'));
    function activate(id) {
      buttons.forEach(function (button) {
        var selected = button.getAttribute('data-tab') === id;
        button.setAttribute('aria-selected', selected ? 'true' : 'false');
      });
      panels.forEach(function (panel) {
        panel.classList.toggle('active', panel.id === id);
      });
    }
    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        activate(button.getAttribute('data-tab'));
      });
    });
  }());
</script>
```

## 表格与手机端

团队报表中 AE 表现、成交明细和 Pipeline 明细可以保留表格，但必须处理手机端：

- 简单表格：使用 `.table-wrap` 横向滚动。
- 行数多、列数多：保留关键字段，必要时分组；不要删掉金额、负责人、阶段、风险、优先级和管理判断。
- 每个表格前应有 1-3 条洞察，说明表格背后的管理含义。
- 同一客户或商机的多条记录先合并，再进入客户复盘页签，避免重复刷屏。

## 页签内容标准

- 总览：必须有管理摘要、关键指标卡、最大风险和下期主管动作。
- 成交明细：必须说明成交贡献来自哪些 AE、客户或行业，是否存在单点依赖。
- Pipeline：必须说明 Pipeline 金额、阶段质量、逾期、空金额、阶段缺失、负责人/客户/行业集中度和下期转化判断。
- AE 表现：必须说明 AE 分层、活跃度、沉默/待激活成员、数据异常、数据缺失和对应管理动作。
- 客户复盘：必须说明 P0/P1 客户或商机的本期进展、卡点和下一步；周报客户复盘必须补充金额、阶段变化、赢率变化、负责 AE、关键人/决策链、本期进展、当前判断和下期动作。
- 风险行动：必须说明风险等级、影响、建议动作，并输出 P0/P1/P2；周报必须区分跨 AE 风险和客户级风险，月报必须将活跃度系统性缺失、Pipeline 集中度、逾期商机、数据污染等问题转成动作。
- 数据说明：必须说明数据来源、周期、人员范围、清洗口径、test 记录/空金额/阶段缺失处理和生成时间；弱化展示。

## HTML 内容限制

- HTML 中的 CRM 数据说明只能使用中文对象名。
- 不输出 `_id`、记录 ID、数据 ID 或长串主键。
- 不输出 `JournalObj`、`NewOpportunityObj` 等对象 ApiName；如果附件原文含有对象 ApiName，应转成中文对象名。
- 不输出 `work_summary`、`work_experience`、`journal_time` 等字段 ApiName。
- 不把“生成 HTML”描述为“已保存到 CRM”。

## 验收标准

生成 HTML 前检查：

1. 有 viewport。
2. 有横向导航页签，且当前页签可切换。
3. 手机端单列可读，页签可横向滚动。
4. 桌面端宽度不超过主容器。
5. 表格不会撑破屏幕。
6. 每个页签不只是表格，至少包含洞察、判断或动作。
7. P0/P1/P2 行动在手机端仍清晰。
8. 没有对象 ApiName、记录 ID 或系统字段。
9. 打印时所有页签内容展开。
10. HTML 之后仍有 CRM 日志保存确认。
