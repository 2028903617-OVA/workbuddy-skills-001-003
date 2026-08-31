---
name: xinnuanjia-kpi-amount
description: Generate the monthly KPI bonus amount table for 杭州欣暖家节能科技有限公司 from a base performance sheet and a target/personnel template workbook. Use when the user asks for "欣暖家考核金额表", "月度考核金额", "KPI金额表", or similar, especially when the workbook must preserve 人员表 and 目标表 sheets and apply probationary target selection by report month.
agent_created: true
---

# 欣暖家月度 KPI 考核金额表生成

## Overview

This skill generates the styled monthly KPI bonus amount table for 欣暖家 from:

1. A **base performance workbook** (23 columns) containing actual sales/ABC/first-deal/lead data.
2. A **template workbook** containing:
   - The previous month's styled amount table (used only for visual style/number formats).
   - A `人员表` sheet (copied as-is).
   - A `目标表` sheet (copied as-is; also used to pick the correct target row for each employee).

The output workbook contains three sheets: the amount table, `人员表`, and `目标表`.

## Triggers

Use this skill when the user requests:

- "生成欣暖家考核金额表"
- "做欣暖家月度 KPI 金额表"
- "欣暖家考核金额美化版"
- Any task involving the 欣暖家 bonus/commission amount table.

## Required Inputs

Ask the user for (or infer from context):

1. **base_path**: Path to the base performance workbook (`欣暖家员工考核绩效（全量总计）数值版_YYYY-MM-DD HH_mm.xlsx`).
2. **template_path**: Path to the styled template workbook that contains `人员表` and `目标表`.
3. **report_month**: The month the report is for (default `8`). This selects the correct probationary target row from `目标表`:
   - `李虹`, `徐越`: choose the `（8-12月）` row for month 8.
   - `方宇`, `陈学健`, `钟俊楠`: choose the `（7.8月试用期）` row for month 8.
4. **out_path**: Where to save the generated file.

## Workflow

1. Read the base performance workbook and extract person rows. **Only use actual achievement values from the base sheet** (sales amount, first-deal amount, ABC amount, customer count, lead count); ignore any target/achievement-rate columns in the base sheet.
2. Read the `目标表` from the template and select targets for `report_month`. **All target values and achievement rates must come from this target sheet.**
3. Apply department overrides:
   - `特定渠道1部`: 吴建, 车邦建, 韩芬, 周晨烨
   - `特定渠道2部`: 王浩萍, 郁轹文, 钟俊楠, 陈学健
   - `美的特渠部` becomes the parent subtotal of the two channel departments.
4. Group people in the order: 美的滨江店 → 东芝华东店 → 东芝宝龙店 → 特定渠道1部 → 特定渠道2部 → 美的特渠部. No 公司小计 or 总计 rows are generated.
5. Recompute every achievement rate as `actual / target` using the target values from `目标表`, then compute per-person bonuses:
   - `月度整体达成奖金` = 300 if 月度整体达成率 ≥ 1, else 0
   - `第一成交达成奖金` = 300 if 第一成交率金额达成率 ≥ 1, else 0
   - `ABC成交达成奖金` = 300 if ABC成交金额达成率 ≥ 1, else 0
   - `ABC成交顾客数达成奖金` = 300 if ABC成交顾客数达成率 ≥ 1, else 0
   - `ABC录入线索达成奖金` = 300 if ABC线索新建达成率 ≥ 1, else 0
   - `达成奖金` = 月度整体 + 第一成交 + max(ABC成交, ABC成交顾客数) + 录入线索
   - Disabled employees (e.g., `吴思琴(已停用)`) get 0 for all bonuses.
6. For subtotal rows (门店 / 渠道 / 美的特渠部), use the target values directly from `目标表`, recompute subtotal achievement rates as `sum(actual) / target`, and apply the subtotal bonus formula:
   - `月度整体达成奖金` = 2000 if subtotal 月度整体达成率 ≥ 1, else 0
   - `第一成交达成奖金`, `ABC成交达成奖金`, `ABC成交顾客数达成奖金`, `ABC录入线索达成奖金` = 1000 if their subtotal rate ≥ 1, else 0
   - `达成奖金` = 月度整体 + 第一成交 + 录入线索 + IF((ABC成交 + ABC成交顾客数) ≥ 1000, 1000, 0)
   - Target mappings: 美的滨江店合计, 东芝华东店合计, 东芝宝龙店合计, 渠道1部小计, 渠道2部小计, 渠道部合计 → 美的特渠部.
7. Build the amount table using the template's visual style (colors, borders, number formats, freeze panes, formulas). Write achievement-rate columns as formulas (`=E/D`, `=I/H`, `=M/L`, `=S/R`, `=W/V`) so they stay in sync with the target sheet. Force all amount/currency columns to 2 decimal places; count columns to integers.
8. Preserve the `人员表` and `目标表` sheets from the template.
9. Save the output workbook.

## Script

Run the bundled script for deterministic generation:

```bash
python scripts/gen_xinnuanjia_amount.py <base_path> <template_path> <out_path> [report_month]
```

Example:

```bash
python scripts/gen_xinnuanjia_amount.py \
  "D:/Backup/Downloads/欣暖家员工考核绩效（全量总计）数值版_2026-08-24 13_11.xlsx" \
  "D:/Backup/xwechat_files/wxid_xf22fbly6tho12_7f07/msg/file/2026-08/欣暖家员工考核绩效（全量总计）数值版_2026-08-19 13_00(1)(1).xlsx" \
  "C:/Users/Administrator/WorkBuddy/2026-08-07-09-18-03/欣暖家8月考核金额表_美化版_2026-08-28.xlsx" \
  8
```

## Verification Checklist

After generating, verify:

- Output has exactly three sheets: amount table, `人员表`, `目标表`.
- Departments are split into `特定渠道1部` and `特定渠道2部` under `美的特渠部`.
- Probationary employees use the target row matching `report_month`.
- Achievement rates are computed from the `目标表` target values, not copied from the base sheet.
- Store/channel subtotal targets match `目标表` totals (e.g., 美的滨江店 = 920000, 美的特渠部 = 1360000).
- Achievement-rate columns contain formulas (`=E/D`, `=I/H`, `=M/L`, `=S/R`, `=W/V`).
- Bonus columns follow the pattern `=IF(F2>=1,300,0)` for persons and `=IF(F7>=1,2000,0)` / `=IF(J7>=1,1000,0)` etc. for subtotals.
- Visual style (blue bonus columns, yellow subtotal rows, thin borders, frozen panes) matches the template.

## Business Rules Reference

See `references/business_rules.md` for the full bonus calculation rules and target mappings.

## 文件命名规范

输出文件统一命名为 `欣暖家{月}月考核金额表.xlsx`（示例：`欣暖家8月考核金额表.xlsx`、`欣暖家9月考核金额表.xlsx`）。每月仅替换月份，不再带日期 / "美化版" / "_改"等后缀。生成前提醒用户关闭旧文件，避免 WPS 占用导致无法覆盖；若占用则先用临时名生成，最后一次性重命名为规范名。

## 做表前检查清单（必做）

每次生成前逐项确认，缺项主动提醒用户：

- [ ] **本次报表月份？**（决定试用期目标行：8月→李虹/徐越取8-12月行、方宇/陈学健/钟俊楠取7.8月试用期行）
- [ ] **是否提供了最新人员表？**（没提供 → 主动提醒；部门结构以人员表为准，不要写死）
- [ ] **是否提供了目标表？**（小计目标、试用期取值必须取自它；基础表的目标/达成率列不可信，一律不读）
- [ ] **用户原表有无「公司小计 / 总计」行？**（没有就不自加）
- [ ] **小计奖金基数是否与员工不同？**（先看原表公式：门店小计月度整体 2000、其余 1000）
- [ ] **三表是否都保留？**（金额表 + 人员表 + 目标表）
- [ ] **金额列是否统一 2 位小数、计数类整数？**
- [ ] **生成后自检**：公式模拟 vs 口径一致、全部人员匹配目标、行结构与原表一致，再交付。
