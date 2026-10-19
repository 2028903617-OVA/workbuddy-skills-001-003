---
name: xinnuanjia-kpi-amount
description: Generate the monthly KPI bonus amount table for 杭州欣暖家节能科技有限公司 from a base performance sheet plus a previous-month finished workbook (used as template for style / 人员表 / 目标表). Use when the user asks for "欣暖家考核金额表", "月度考核金额", "KPI金额表", "欣暖家绩效奖金", or similar — including when the workbook must preserve 人员表 and 目标表 sheets, switch probationary vs formal targets by month, and merge/split channel departments.
agent_created: true
---

# 欣暖家月度 KPI 考核金额表生成（v2.0 通用版）

## 核心变化（v1 → v2）

| 项 | v1（8 月硬编码） | v2（通用） |
|---|---|---|
| 部门块顺序 | 写死 6 块 | **按基础表「二级部门」首次出现顺序自动推导**，父块（美的特渠部）展开为 1部/2部并排到最后 |
| 部门名 | 无别名 | `天猫彩电店 → 天猫彩电部` 等**别名自动映射** |
| 不做统计的部门 | 无 | `--skip-dept` **整块剔除人员**（不再落入"未登记部门"误报） |
| 新部门 | 直接算 | **白名单闸门**：基础表出现 `known_depts` 外的部门 → 报错，禁止静默纳入 |
| 目标取值 | 部分写死 | 目标表按 `--month` 过滤（试用期/正式自动切换），查不到回落报表「指标」列 |
| 小计目标 | 写死合计值 | **成员目标相加**（8 月定案口径）；可切 `--subtotal-from sheet` |
| 小计行标签 | 写死 | 门店「XX合计」/ 渠道「渠道N部小计」/ 父块「渠道部合计」 |
| 样式 | 写死行号 | **自动扫描模板**里的人员行 / 小计行样式 |
| 人员表 | 单份 | **可合并多份导出**（按唯一性ID去重） |
| 月份校验 | 无 | `--month` 必须 1–12，越界直接报错 |

## Triggers

- 「生成欣暖家考核金额表」「做欣暖家月度 KPI 金额表」「欣暖家绩效奖金表」
- 任何基于「欣暖家员工考核绩效（全量总计）数值版」产出的月度奖金表任务

## Required Inputs

1. **base_path** — 本月基础表 `欣暖家员工考核绩效（全量总计）数值版_YYYY-MM-DD HH_mm.xlsx`（23 列，含实际达成值 + 报表指标值）
2. **template_path** — **上期成品**（含金额表样式 + `人员表` + `目标表`），例：`欣暖家8月考核金额表_新.xlsx`
3. **month** — 报表月份（1–12）
4. **out_path** — 输出路径
5. **roster**（可选，可多个）— 最新人员对象导出，合并进 `人员表`

## 脚本用法

```bash
python scripts/gen_xinnuanjia_amount.py \
  --base   "D:/Backup/Downloads/欣暖家员工考核绩效（全量总计）数值版_2026-10-16 16_20.xlsx" \
  --template "C:/Users/Administrator/WorkBuddy/2026-08-07-09-18-03/欣暖家8月考核金额表_新.xlsx" \
  --month 9 \
  --out    "C:/Users/Administrator/WorkBuddy/20260427135223/欣暖家9月考核金额表.xlsx" \
  --roster "D:/Backup/Downloads/人员对象导出结果_xxx.xlsx" \
  --skip-dept 天猫零售部
```

### 全部参数

| 参数 | 说明 |
|---|---|
| `--base` `--template` `--month` `--out` | 必填 |
| `--roster FILE` | 人员导出，可重复；按「唯一性ID」去重合并 |
| `--config cfg.json` | 覆盖 `DEFAULT_CONFIG`（alias / known_depts / skip_depts / person_dept / parent_blocks / sub_label / name_order / 奖金基数） |
| `--skip-dept NAME ...` | 本月不做的部门，**整块剔除人员** |
| `--skip-person NAME ...` | 只剔人，部门保留 |
| `--person-dept "姓名:部门"` | 人员归部覆盖（父部门拆 1部/2部，或跨部门还原） |
| `--dept NAME ...` | 确认纳入 `known_depts` 外的新部门 |
| `--allow-new-dept` | 一次性放行所有新部门（不推荐） |
| `--target-source sheet\|report` | 目标来源，默认 `sheet`（目标表优先，缺失回落报表指标） |
| `--subtotal-from members\|sheet` | 小计目标口径，默认 `members`（成员相加，8 月定案） |
| `--keep-target` | 不重建目标表（原样保留模板的） |
| `--allow-unknown-dept` | 允许未登记部门（默认报错） |

## Workflow

1. **读基础表**：取实际达成值列（月度整体销售 / 第一成交金额 / ABC 成交金额 / ABC 成交客户数 / ABC 成交顾客数 / 录入线索数）+ 报表指标列兜底。**基础表的「目标值」列不作为最终目标**。
2. **白名单闸门**：`known_depts` 之外出现部门 → 报错，要求 `--dept` 纳入或 `--skip-dept` 跳过。
3. **部门块推导**：按基础表二级部门首次出现序 → 别名映射 → 跳过 skip_depts → 父块展开为子块并排最后。
4. **归部**：`person_dept` 覆盖优先（父部门拆 1部/2部）→ 否则用基础表部门。仍在父块内 → 报错禁止猜。
5. **目标解析**：目标表按月份过滤（`parse_period` 解析「（7月试用期）」「（8-12月）」「（7.8月试用期）」「（9-12月）」）→ 停用人员置 0 → 都查不到则回落报表指标并打印提示；月度销售指标仍为 0 → 报错。
6. **人员奖金**：`b4+b1+max(b3a,b3c)+b2`，每项 300，达成率 `实际/目标 ≥ 1` 才发。
7. **小计奖金**：月度整体 2000，其余 1000；`tot = b4+b1+b2+ (1000 if b3a+b3c>=1000 else 0)`。
8. **写表**：按模板样式写金额表 + 达成率公式（`=E/D` `=I/H` `=M/L` `=S/R` `=W/V`）+ 数字格式（金额 2 位、计数整数）+ 列宽 + 冻结。
9. **重建目标表**（默认）：按月保留生效区间标签 + 合计行 = 成员相加 + 奖金列 = `n*300`。
10. **合并人员表**（有 `--roster` 时）。

## Verification Checklist（交付前必做）

- [ ] 三张表齐全：金额表 + `人员表` + `目标表`
- [ ] 部门块顺序与人数对得上；跳过部门的人**既不在明细也不在小计**
- [ ] 达成率列是**公式**（`=E/D` `=I/H` `=M/L` `=S/R` `=W/V`）
- [ ] 奖金列是 `=IF(F{r}>=1,300,0)`；小计行 `=IF(F{r}>=1,2000,0)` / `=IF(J{r}>=1,1000,0)`
- [ ] 小计目标 = 成员目标相加，且与目标表合计行一致
- [ ] 停用人员（`(已停用)`）五项奖金全 0
- [ ] 金额列 2 位小数、计数列整数
- [ ] 样式（蓝底奖金列、黄底小计行、细边框、冻结窗格）与模板一致
- [ ] **独立复算**：读产物静态列重算一遍奖金，与引擎输出 0 差异
- [ ] **逐格比对**：与上期成品比对值 / 公式 / 格式 / 列宽 / 冻结，0 差异

## 换月 SOP

1. 让用户给：本月基础表 + 最新人员导出（+ 是否有部门变动 / 人员调岗 / 停用）
2. 用上期成品当 `--template`
3. 先跑一遍 → 看报错：新部门？父块未拆？指标为 0？
4. 按报错补 `--dept` / `--person-dept` / `--skip-dept`
5. 跑通后核对输出打印的「员工个人合计 / 小计合计 / 总奖金」与业务预期
6. 独立复算 + 与上期比对 → 交付

## 文件命名规范

`欣暖家{月}月考核金额表.xlsx`，不带日期 / 「美化版」/「_改」。生成前提醒用户关闭旧文件（WPS 占用会导致无法覆盖）。

## 做表前检查清单

- [ ] **本月报表月份？**（决定试用期/正式目标行）
- [ ] **上期成品拿来当模板了吗？**（样式 + 目标表 + 人员表都从它来）
- [ ] **最新人员表提供了吗？**（部门结构以人员表 / 基础表为准，不写死）
- [ ] **哪些部门本月不做？**（`--skip-dept`）
- [ ] **有无人员调岗 / 部门还原？**（`--person-dept`）
- [ ] **用户原表有无「公司小计 / 总计」行？**（没有就不自加）
- [ ] **生成后自检**：公式 vs 口径、全部人员匹配目标、行结构与上期一致

## Business Rules Reference

见 `references/business_rules.md`（列布局 / 奖金规则 / 口径两版本说明 / v1→v2 对照）。
