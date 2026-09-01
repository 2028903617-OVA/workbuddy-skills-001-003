# -*- coding: utf-8 -*-
"""
乾鑫 月度考核金额表 —— 生成 + 格式美化 一体化脚本
=================================================
输入三件套（相对脚本运行目录，或用参数覆盖）:
  F1 = 7月模板（含 新绩效/基数表/人员/目标 四 sheet，作为样式与公式骨架）
  F2 = 8月基础表（新格式，嵌套进 基数表）
  F3 = 8月人员导出（嵌套进 人员表）

产出: 乾鑫{月}月考核金额表_美化版.xlsx

流程:
  1. 打开 F1 模板，清空并重建「新绩效」人员/小计/合计行
  2. 嵌套 F2 到「基数表」、F3(+停用补齐) 到「人员」
  3. 目标表同步加「(已停用)」后缀
  4. F/K/P/U 四项达成金口径:
       店长       -> 引用本店小计行
       销售顾问/客户经理 -> 按个人达成率自算
  5. 统一美化（字体/对齐/边框/清理/冻结）
  6. 数值格式统一 + 已停用标红
  7. 保存

注意（月月必查，非 8月 需改）:
  - GROUPS: 5 店 21 人的门店归属与成员名单
  - STOPPED: 停用人员原名 -> 带后缀名 的映射
  - report_month: 决定输出文件名中的月份字
  - 阈值表 AB:AE (R36-38) 的 指标值（新建线索数/第一成交率/ABC转化率）
"""
import openpyxl, sys, io, os, copy
from openpyxl.worksheet.formula import ArrayFormula
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, Color

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============ 参数 ============
# argv: F1 F2 F3 out_month [V2]
# F1=7月模板(人员停用补齐来源)  F2=基础表  F3=人员表  V2=样式模板(权威美化版)
args = sys.argv[1:]
F1 = args[0] if len(args) > 0 else "乾鑫8月源文件/F1_乾鑫7月考核金额.xlsx"
F2 = args[1] if len(args) > 1 else "乾鑫8月源文件/F2_8月基础表.xlsx"
F3 = args[2] if len(args) > 2 else "乾鑫8月源文件/F3_8月人员表.xlsx"
REPORT_MONTH = args[3] if len(args) > 3 else "8"
V2 = args[4] if len(args) > 4 else "乾鑫8月考核金额表_美化版_v2.xlsx"

# ============ 月月必改 业务数据（非 8月 要更新） ============
# (门店, [成员名单]) —— 停用人员带 "(已停用)" 后缀
GROUPS = [
    ("格力红星店",   ["方大露", "张杰（格力）(已停用)", "李先兰", "齐壮壮(已停用)"]),
    ("格力滨江六空店", ["孙冬连"]),
    ("格力恒大店",   ["谭朝军(已停用)", "高凤莺", "杨岳仙", "尚娜"]),
    ("格力华东店",   ["汤三九", "金梅", "沈正亮", "陶明明", "张嘉一"]),
    ("格力特渠部",   ["刘勇", "张勤", "徐豪", "颜永福", "伊鑫", "陈婷婷", "马英兰"]),
]
# 停用人员：F2/F3 中不含，需从 7月模板人员表补齐，并加后缀
STOPPED = {
    "齐壮壮": "齐壮壮(已停用)",
    "张杰（格力）": "张杰（格力）(已停用)",
    "谭朝军": "谭朝军(已停用)",
}

def pick_out(base):
    """处理文件占用：若 base 被 WPS 占用无法覆盖，则返回带递增后缀的可用名"""
    if not os.path.exists(base):
        return base
    try:
        with open(base, "a"):
            pass
        return base
    except PermissionError:
        i = 2
        while True:
            cand = base[:-5] + f"_v{i}.xlsx" if base.endswith(".xlsx") else f"{base}_v{i}"
            if not os.path.exists(cand):
                return cand
            i += 1

OUT = pick_out(f"乾鑫{REPORT_MONTH}月考核金额表_美化版.xlsx")

# ============ 工具 ============
def L(c):
    return openpyxl.utils.get_column_letter(c)

def ci(names, key):
    for i, h in enumerate(names):
        if h and key in str(h):
            return i
    raise KeyError(key)

# ============ 1. 读 F2 (8月基础表 新格式) ============
wb2 = openpyxl.load_workbook(F2, data_only=True)
ws2 = wb2[wb2.sheetnames[0]]
F2_HDR = [ws2.cell(1, c).value for c in range(1, ws2.max_column + 1)]
I_DEPT3 = ci(F2_HDR, "主属部门-3")
I_NAME  = ci(F2_HDR, "员工姓名")
I_ROLE  = ci(F2_HDR, "考核角色")
I_TGT   = ci(F2_HDR, "月度销售指标")
I_AMT   = ci(F2_HDR, "月度整体销售金额")
I_LEADT = ci(F2_HDR, "月度新建线索数指标")
I_LEAD  = ci(F2_HDR, "新建线索数（创建人）")
I_FIRST = ci(F2_HDR, "第一成交顾客数")
I_ABC   = ci(F2_HDR, "ABC成交顾客数")

F2DATA = {}
F2ORDER = []
for r in range(2, ws2.max_row + 1):
    nm = ws2.cell(r, I_NAME + 1).value
    if nm is None or str(nm).strip() in ("", "总计"):
        continue
    nm = str(nm).strip()
    F2DATA[nm] = {
        "dept3": ws2.cell(r, I_DEPT3 + 1).value,
        "role": ws2.cell(r, I_ROLE + 1).value,
        "target": ws2.cell(r, I_TGT + 1).value,
        "amt": ws2.cell(r, I_AMT + 1).value,
        "leadt": ws2.cell(r, I_LEADT + 1).value,
        "lead": ws2.cell(r, I_LEAD + 1).value,
        "first": ws2.cell(r, I_FIRST + 1).value,
        "abc": ws2.cell(r, I_ABC + 1).value,
    }
    F2ORDER.append(nm)
print(f"F2 读取: {len(F2DATA)} 人")

# ============ 3. 打开样式模板(V2)，重建 新绩效 ============
wb = openpyxl.load_workbook(V2, data_only=False)
ws = wb["新绩效"]
for mc in list(ws.merged_cells.ranges):
    ws.unmerge_cells(str(mc))
for r in range(2, 39):
    for c in range(1, ws.max_column + 1):
        ws.cell(r, c).value = None

def set_arr(r, c, formula):
    ws.cell(r, c).value = ArrayFormula(f"{L(c)}{r}", formula)

def set_f(r, c, formula):
    ws.cell(r, c).value = formula

# ---- 行布局 ----
row = 2
layout = []
for shop, members in GROUPS:
    r1 = row
    for nm in members:
        layout.append((row, "P", nm, shop, None, None, None))
        row += 1
    r2 = row - 1
    sub = row
    layout.append((sub, "S", shop, shop, None, r1, r2))
    row += 1
    for i, t in enumerate(layout):
        if t[1] == "P" and t[3] == shop and t[4] is None:
            layout[i] = (t[0], t[1], t[2], t[3], sub, None, None)

TOTAL_ROW = row
SUB_ROWS = [t[0] for t in layout if t[1] == "S"]
print(f"行布局: 人员{len([t for t in layout if t[1]=='P'])}人, 小计行{SUB_ROWS}, 合计行R{TOTAL_ROW}")

# ---- 写人员行（含 F/K/P/U 口径） ----
for (r, kind, nm, shop, sub, _, _) in layout:
    if kind != "P":
        continue
    d = F2DATA[nm]
    role = d["role"]
    E = 2000 if role == "店长" else 1000
    set_arr(r, 1,  f"=LOOKUP(1,0/(人员!D:D=C{r}),人员!A:A)")     # A 部门
    ws.cell(r, 2).value = role                                   # B 角色
    ws.cell(r, 3).value = nm                                     # C 姓名
    set_f(r, 4,  f"=F{r}+K{r}+P{r}+U{r}")                        # D 考核金额
    ws.cell(r, 5).value = E                                      # E 基础奖金
    # F/K/P/U：店长引用门店小计，其余按个人
    if role == "店长":
        set_f(r, 6,  f"=F{sub}")
        set_f(r, 11, f"=K{sub}")
        set_f(r, 16, f"=P{sub}")
        set_f(r, 21, f"=U{sub}")
    else:
        set_f(r, 6,  f"=IF(J{r}>=0.7,IF(J{r}>=1,G{r},J{r}*G{r}),0)")
        set_f(r, 11, f"=IF(O{r}>=1,L{r},0)")
        set_f(r, 16, f"=IF(T{r}>=R{r},Q{r},0)")
        set_f(r, 21, f"=IF(Y{r}>=W{r},V{r},0)")
    set_f(r, 7,  f"=E{r}*0.4")                                   # G 权重
    set_arr(r, 8, f"=LOOKUP(1,0/(目标!B:B=C{r}),目标!D:D)*10000")  # H 月度销售指标
    set_arr(r, 9, f"=LOOKUP(1,0/(基数表!C:C=C{r}),基数表!F:F)")     # I 含变更(键改C列)
    set_f(r, 10, f"=I{r}/H{r}")                                  # J 达成率
    set_f(r, 12, f"=E{r}*0.2")                                   # L 权重
    set_arr(r, 13, f"=LOOKUP(1,0/(AB:AB=B{r}),AC:AC)")             # M 新建线索数指标
    ws.cell(r, 14).value = d["lead"]                              # N 新建线索数
    set_f(r, 15, f"=IFERROR(N{r}/M{r},0)")                       # O 达成率
    set_f(r, 17, f"=E{r}*0.2")                                   # Q 权重
    set_arr(r, 18, f"=LOOKUP(1,0/(AB:AB=B{r}),AD:AD)")             # R 第一成交率指标
    ws.cell(r, 19).value = d["first"]                             # S 第一成交顾客数
    set_f(r, 20, f"=IFERROR(S{r}/N{r},0)")                       # T 第一成交率
    set_f(r, 22, f"=E{r}*0.2")                                   # V 权重
    set_arr(r, 23, f"=LOOKUP(1,0/(AB:AB=B{r}),AE:AE)")             # W ABC线索转化率指标
    ws.cell(r, 24).value = d["abc"]                               # X ABC成交顾客数
    set_f(r, 25, f"=IFERROR(X{r}/N{r},0)")                       # Y ABC线索转化率

# ---- 写小计行 ----
for (r, kind, shop, _, _, r1, r2) in layout:
    if kind != "S":
        continue
    ws.cell(r, 1).value = shop
    ws.cell(r, 3).value = shop
    set_f(r, 4,  f"=F{r}+K{r}+P{r}+U{r}")
    ws.cell(r, 5).value = 2000
    set_f(r, 6,  f"=IF(J{r}>=0.7,IF(J{r}>=1,G{r},J{r}*G{r}),0)")
    set_f(r, 7,  f"=E{r}*0.4")
    set_arr(r, 8, f"=LOOKUP(1,0/(目标!B:B=C{r}),目标!D:D)*10000")
    set_f(r, 9,  f"=SUM(I{r1}:I{r2})")
    set_f(r, 10, f"=I{r}/H{r}")
    set_f(r, 11, f"=IF(O{r}>=1,L{r},0)")
    set_f(r, 12, f"=E{r}*0.2")
    set_f(r, 13, f"=SUM(M{r1}:M{r2})")
    set_f(r, 14, f"=SUM(N{r1}:N{r2})")
    set_f(r, 15, f"=IFERROR(N{r}/M{r},0)")
    set_f(r, 16, f"=IF(T{r}>=R{r},Q{r},0)")
    set_f(r, 17, f"=E{r}*0.2")
    ws.cell(r, 18).value = 0.15                                   # R 阈值(字面)
    set_f(r, 19, f"=SUM(S{r1}:S{r2})")
    set_f(r, 20, f"=IFERROR(S{r}/N{r},0)")
    set_f(r, 21, f"=IF(Y{r}>=W{r},V{r},0)")
    set_f(r, 22, f"=E{r}*0.2")
    ws.cell(r, 23).value = 0.15                                   # W 阈值(字面)
    set_f(r, 24, f"=SUM(X{r1}:X{r2})")
    set_f(r, 25, f"=IFERROR(X{r}/N{r},0)")

# ---- 合计行 ----
tr = TOTAL_ROW
set_f(tr, 4, f"=SUM(D2:D{tr-1})" + "".join(f"-D{r}" for r in SUB_ROWS))
set_f(tr, 9, f"=SUM(I2:I{tr-1})" + "".join(f"-I{r}" for r in SUB_ROWS))
# V2 模板无合计行，R28 样式继承 R27（特渠小计行）以保持协调
for c in range(1, ws.max_column + 1):
    src = ws.cell(27, c)
    dst = ws.cell(tr, c)
    dst.font = copy.copy(src.font)
    dst.fill = copy.copy(src.fill)
    dst.border = copy.copy(src.border)
    dst.alignment = copy.copy(src.alignment)
    dst.number_format = src.number_format

# V2 模板在 J13/J19 等小计行可能是 General，导致达成率列同时出现百分比和小数
# 脚本兜底：强制数据区（R2~TOTAL_ROW）达成率列统一为 0.00%
RATE_COLS = [10, 15, 20, 25]  # J/O/T/Y
for c in RATE_COLS:
    for r in range(2, TOTAL_ROW + 1):
        ws.cell(r, c).number_format = '0.00%'

# 去除合计行底色（保留字体/边框/对齐/数值格式）
for c in range(1, ws.max_column + 1):
    ws.cell(TOTAL_ROW, c).fill = PatternFill(fill_type=None)

# ---- 阈值表 AB35:AE38 ----
thr = [(36, "销售顾问", 45, 0.3, 0.3), (37, "客户经理", 35, 0.15, 0.15), (38, "店长", 15, 0.15, 0.15)]
for (r, role, m, fr, abc) in thr:
    ws.cell(r, 28).value = role
    ws.cell(r, 29).value = m
    ws.cell(r, 30).value = fr
    ws.cell(r, 31).value = abc
print("新绩效 写入完成")

# ============ 4. 重建 基数表（嵌套 F2 新格式） ============
wsb = wb["基数表"]
for mc in list(wsb.merged_cells.ranges):
    wsb.unmerge_cells(str(mc))
for r in range(1, wsb.max_row + 1):
    for c in range(1, wsb.max_column + 1):
        wsb.cell(r, c).value = None
for r in range(1, ws2.max_row + 1):
    for c in range(1, ws2.max_column + 1):
        wsb.cell(r, c).value = ws2.cell(r, c).value   # 仅复制值
print(f"基数表 嵌套完成: {ws2.max_row}r x {ws2.max_column}c")

# ============ 5. 重建 人员表 ============
wsp = wb["人员"]
for mc in list(wsp.merged_cells.ranges):
    wsp.unmerge_cells(str(mc))
for r in range(1, wsp.max_row + 1):
    for c in range(1, wsp.max_column + 1):
        wsp.cell(r, c).value = None

wb3 = openpyxl.load_workbook(F3, data_only=True)
ws3 = wb3[wb3.sheetnames[0]]
F3_HDR = [ws3.cell(1, c).value for c in range(1, ws3.max_column + 1)]
N3 = ws3.max_column

wsp.cell(1, 1).value = "负责人所在部门"
wsp.cell(1, 2).value = "查看绩效表是否为空"
for i, h in enumerate(F3_HDR):
    wsp.cell(1, 3 + i).value = h

i_dept_f3 = ci(F3_HDR, "负责人所在部门")
U_COL = 3 + i_dept_f3
print(f"人员表: F3负责人所在部门=col{i_dept_f3+1} -> 新表 col{U_COL}({L(U_COL)})")

# 停用3人从 7月模板人员表补齐
wb1old = openpyxl.load_workbook(F1, data_only=True)
wsold = wb1old["人员"]
OLD_HDR = {}
for c in range(3, wsold.max_column + 1):
    h = wsold.cell(1, c).value
    if h:
        OLD_HDR[str(h)] = c
old_rows = {}
for r in range(2, wsold.max_row + 1):
    nm = wsold.cell(r, 4).value
    if nm and str(nm).strip() in STOPPED:
        old_rows[str(nm).strip()] = r
print(f"7月人员表找到停用行: {old_rows}")

NAME_FIX = {"主属部门": "主属部门（必填）"}
F3_IDX = {str(h): i for i, h in enumerate(F3_HDR) if h}

def build_row_from_old(orr):
    vals = [None] * N3
    for h, c in OLD_HDR.items():
        key = NAME_FIX.get(h, h)
        if key in F3_IDX:
            vals[F3_IDX[key]] = wsold.cell(orr, c).value
    return vals

r = 2
for r3 in range(2, ws3.max_row + 1):
    if ws3.cell(r3, 2).value is None or str(ws3.cell(r3, 2).value).strip() == "":
        continue
    for i in range(N3):
        wsp.cell(r, 3 + i).value = ws3.cell(r3, i + 1).value
    r += 1
n_f3 = r - 2
for oldname, newname in STOPPED.items():
    if oldname not in old_rows:
        print(f"  [!] 7月表无 {oldname}")
        continue
    vals = build_row_from_old(old_rows[oldname])
    vals[1] = newname
    for i in range(N3):
        wsp.cell(r, 3 + i).value = vals[i]
    r += 1
n_all = r - 2
print(f"人员表: F3 {n_f3}人 + 停用补齐 {n_all - n_f3}人 = {n_all}人")

for rr in range(2, r):
    wsp.cell(rr, 1).value = f"=U{rr}"
    wsp.cell(rr, 2).value = ArrayFormula(f"B{rr}", f"=LOOKUP(1,0/(新绩效!C:C=D{rr}),新绩效!C:C)")

# ============ 6. 目标表 停用加后缀 ============
wst = wb["目标"]
changed = []
for rr in range(1, wst.max_row + 1):
    nm = wst.cell(rr, 2).value
    if nm and str(nm).strip() in STOPPED:
        wst.cell(rr, 2).value = STOPPED[str(nm).strip()]
        changed.append((rr, STOPPED[str(nm).strip()]))
print(f"目标表改名: {changed}")

# 样式完全继承 V2 模板，脚本不再重新设置（避免与人工调整冲突）
# 后续如需要脚本级样式，可恢复之前的美化/底色/加粗/数值格式段

# 清理：人员表末尾空行、目标表末尾空列
wp = wb["人员"]
del_rows = []
for r in range(wp.max_row, 1, -1):
    if all(wp.cell(r, c).value is None for c in range(1, wp.max_column + 1)):
        del_rows.append(r)
    else:
        break
if del_rows:
    wp.delete_rows(min(del_rows), len(del_rows))
    print(f"人员表: 删除 {len(del_rows)} 个空行")
wt = wb["目标"]
del_cols = []
for c in range(wt.max_column, 1, -1):
    if all(wt.cell(r, c).value is None for r in range(1, wt.max_row + 1)):
        del_cols.append(c)
    else:
        break
if del_cols:
    wt.delete_cols(min(del_cols), len(del_cols))
    print(f"目标表: 删除 {len(del_cols)} 个空列")

# 样式完全继承 V2 模板，不统一 number_format、不强制已停用标红

# ============ 8. 保存 ============
wb.calculation.fullCalcOnLoad = True
try:
    wb.save(OUT)
except PermissionError:
    OUT = pick_out(OUT)
    wb.save(OUT)
print(f"\n已保存: {OUT}")
