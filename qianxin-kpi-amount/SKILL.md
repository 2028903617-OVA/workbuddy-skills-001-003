---
name: qianxin-kpi-amount
description: Generate the monthly KPI assessment amount workbook for 乾鑫格力事业部 (乾鑫8月考核金额表) from three source files (7月模板 / 8月基础表 / 8月人员表), using the user's manually-tuned V2 template as the style authority, then apply only minimal post-processing (rate columns as 0.00%, total row without fill). Use when the user asks for "乾鑫考核金额表", "乾鑫考核表", "格力考核金额", or similar — especially the multi-sheet workbook with 新绩效/基数表/人员/目标 and the F/K/P/U 店长-vs-个人 口径 fix.
agent_created: true
---

# 乾鑫 月度考核金额表 生成 + 美化

## Overview

This skill generates the styled monthly KPI assessment amount workbook for 乾鑫格力事业部 from three input files, then applies the standardized beautification that was iterated and confirmed with the user:

1. **F1** — 7月模板（四 sheet 骨架：新绩效/基数表/人员/目标）
2. **F2** — 8月基础表（新格式，嵌套进 基数表）
3. **F3** — 8月人员导出（嵌套进 人员表，停用人员从 F1 补齐）

The output workbook contains four sheets. The script also fixes the **F/K/P/U four-item achievement bonus 口径** (店长 references the store subtotal row; 销售顾问/客户经理 compute per-person), unifies fonts/alignment/borders, unifies percentage vs decimal number formats, and marks `已停用` cells red.

## Triggers

Use this skill when the user requests:

- "生成乾鑫考核金额表" / "做乾鑫格力考核表"
- "乾鑫8月考核金额表" / "乾鑫{月}月考核金额表"
- Any task involving the 乾鑫 bonus/commission amount workbook with sheets 新绩效/基数表/人员/目标.
- Re-running the beautification (font/align/border/percent/red) on an existing 乾鑫 workbook.

## Required Inputs

Ask the user for (or infer from the working directory's `乾鑫8月源文件/`):

1. **F1_path**: 7月模板 workbook (`F1_乾鑫7月考核金额.xlsx`).
2. **F2_path**: 8月基础表 (`F2_8月基础表.xlsx`).
3. **F3_path**: 8月人员导出 (`F3_8月人员表.xlsx`).
4. **report_month**: 报表月份数字（默认 `8`），仅用于输出文件名。

> 月月必改（换月时更新 `scripts/gen_qianxin_amount.py` 内）：`GROUPS`（5店21人归属与名单）、`STOPPED`（停用人员原名→带后缀名映射）。详见 `references/business_rules.md` 第三节。

## Workflow

1. 打开 F1 模板，清空并重建「新绩效」人员行 / 门店小计行 / 合计行。
2. 嵌套 F2 到「基数表」（值复制，绩效表经 `LOOKUP(基数表!C:C, 基数表!F:F)` 取金额）。
3. 嵌套 F3 到「人员表」，并从 F1 补齐停用 3 人；A 列=`=U{行}`、B 列=数组公式。
4. 目标表对停用人员姓名加 `(已停用)` 后缀。
5. **F/K/P/U 口径**：店长引用本店小计行，销售顾问/客户经理按个人达成率自算。
6. **样式继承 V2 模板**：清空值但保留 font/fill/border/alignment/number_format，不硬编码底色/加粗/字体/number_format/已停用标红。
7. **合计行样式**：V2 模板无合计行，新增合计行继承 R27 样式，但去除底色；随后统一 J/O/T/Y 达成率列为 `0.00%`，防止 V2 模板中个别小计行 `General` 导致百分比/小数混排。
8. 保存（若规范名被 WPS 占用，自动改用 `_v{n}.xlsx`）。

## Script

Run the bundled single-pass script (generation + 口径 + 美化 + 格式统一 + 标红):

```bash
python scripts/gen_qianxin_amount.py <F1_path> <F2_path> <F3_path> <report_month>
```

Example (using the working-directory source layout):

```bash
python scripts/gen_qianxin_amount.py \
  "乾鑫8月源文件/F1_乾鑫7月考核金额.xlsx" \
  "乾鑫8月源文件/F2_8月基础表.xlsx" \
  "乾鑫8月源文件/F3_8月人员表.xlsx" \
  8
```

If arguments are omitted, the script defaults to the `乾鑫8月源文件/` relative paths and `report_month=8`.

## Verification Checklist

After generating, verify against the produced workbook:

- **四 sheet 齐全**：新绩效 / 基数表 / 人员 / 目标。
- **行结构**：人员 21 人（5 店），小计行 5 个（R6/8/13/19/27 示例，随 GROUPS 变），合计行 1 个。
- **F/K/P/U 口径**：
  - 店长个人行 F/K/P/U = `=F{sub}`/`=K{sub}`/`=P{sub}`/`=U{sub}`（引用门店小计）。
  - 销售顾问/客户经理个人行 F = `=IF(J>=0.7,IF(J>=1,G,J*G),0)`，K=`=IF(O>=1,L,0)`，P=`=IF(T>=R,Q,0)`，U=`=IF(Y>=W,V,0)`。
- **数组公式首字母**：所有 `ArrayFormula` 的 `text` 必须以 `=` 开头（无 `OOKUP` 失效），数量与预期一致。
- **数字格式**：新绩效 J/O/T/Y 在 R2~合计行统一为 `0.00%`，无 General/小数混排。
- **已停用标红**：由 V2 模板决定，脚本不再主动标红；若 V2 未标红则不再追加。
- **样式继承**：R1-R27 与 V2 模板逐格零差异；合计行 R28 无底色、其余样式继承 R27。
- **边框/对齐/冻结**：继承 V2 模板，脚本不再主动设置。
- **三表数据自洽**：基数表嵌套 F2 全量；人员表 = F3 人员 + 停用补齐；目标表停用已加后缀。

## 业务规则参考

See `references/business_rules.md` for the full sheet structure, the F/K/P/U 口径 table, the AB:AE threshold table, the ArrayFormula `=` pitfall, the beautification checklist, and the percentage/decimal unification rules.

## 文件命名规范

输出文件统一命名为 `乾鑫{月}月考核金额表_美化版.xlsx`（如 `乾鑫8月考核金额表_美化版.xlsx`）。生成前提醒用户关闭旧文件，避免 WPS 占用导致无法覆盖；若占用脚本自动改用 `_v{n}.xlsx` 临时名。

## 做表前检查清单（必做）

每次生成前逐项确认，缺项主动提醒用户：

- [ ] **本次报表月份？**（决定输出文件名与 GROUPS/STOPPED 是否需更新）
- [ ] **三件套是否齐全？**（F1 7月模板 / F2 8月基础表 / F3 8月人员导出）
- [ ] **GROUPS 门店归属与名单是否仍是本月口径？**（换月必查，禁用写死）
- [ ] **STOPPED 停用人员映射是否准确？**（影响人员表补齐与目标表改名）
- [ ] **F/K/P/U 口径是否与确认一致？**（店长→门店小计，个人→自算）
- [ ] **四 sheet 是否都保留？**（新绩效 + 基数表 + 人员 + 目标）
- [ ] **数字格式是否统一（达成率全百分比、金额全 2 位）？**
- [ ] **已停用是否标红？**
- [ ] **生成后自检**：数组公式首字母、格式、标红、行结构，再交付。
