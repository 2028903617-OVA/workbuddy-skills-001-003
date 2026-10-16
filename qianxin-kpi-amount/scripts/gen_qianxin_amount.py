# -*- coding: utf-8 -*-
"""
乾鑫 月度考核金额表 —— 通用版生成脚本  v2.0
================================================================
把「7月模板 / 8月基础表 / 8月人员表」三件套的旧写死逻辑，改为**按月份自动推导**。
换月时原则上**不改脚本**，只丢三个源文件进来。

用法
----
  python gen_qianxin_amount.py <F1> <F2> <F3> <月份> [V2] [补充人员表 ...]

  F1  上期「考核金额表」（四 sheet 骨架；提供 目标表基准 + 人员表补齐池）
  F2  本月基础表（「个人考核指标达成率」导出，14 列）
  F3  本月人员导出（「人员对象导出结果」）
  月份 8 | 9 | 10 | 11 | 12   —— 决定目标表取哪一列、输出文件名
  V2  （可选）样式模板；不传则自动找 乾鑫{月份}月考核金额表_美化版.xlsx，再退回 F1
  补充人员表（可选，可多个）——本月人员导出漏掉的人（如调岗还原）从这些表里按姓名补

自动推导（v2.0 相对 v1 的能力）
----------------------------
  1. 目标列：月份 → 列（8→D 9→E 10→F 11→G 12→H），可 --target-col 覆盖
  2. 表头容错：二级部门/主属部门-3/主属部门-2 等历史表头名都认
  3. 分组：按 F2 的部门列出现顺序自动分组，不再手写 GROUPS
  4. 角色：按 F2「考核角色」列查 ROLE_RULES，自动挂 基础奖金/阈值档/是否清零/是否引用小计
  5. 阈值表：按实际出现的角色自动生成 R36.. 并复制上行样式
  6. 人员表：F2 名册 - F3 名单 → 自动从「补充人员表 + F1」按本名补齐；部门列以 F2 为准
  7. 目标表：按新分组自动重排（保留 F1 内相对顺序、新进本店的追加到末尾）；门店短码自动映射
  8. 样式：扫描 V2 自动识别 普通行/普通小计行/停用行/高亮行；
         **门店小计行的底色 = 本店店长的底色**（8月红星=方大露绿 → 9月华东=方大露绿）
  9. 不写死的：清行范围、合计行来源行、阈值表行数

必须显式配置（脚本拒绝推算，缺就报错退出）
------------------------------------------
  · NEW_TARGET      —— 样式模板目标表里没有的**新人**（如新上岗店长）的职位与 5 个月目标
  · EXTRA_HIGHLIGHT —— 样式模板里没有的新人/新门店的高亮色
  · ROLE_RULES / THRESHOLD_TIERS —— 出现未登记角色时直接报错，不猜
"""
import os
import sys
import io
import copy

import openpyxl
from openpyxl.styles import PatternFill, Color
from openpyxl.worksheet.formula import ArrayFormula

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ==================================================================
#  一、业务配置区（换人 / 换角色 / 换阈值 才改；换月一般不用改）
# ==================================================================

# 角色规则：键 = F2「考核角色」列的值
#   base      本人行基础奖金（门店小计行固定 SUB_TOTAL_BASE）
#   tier      阈值档位 —— 决定 M/R/W 从 AB:AE 取哪一行
#   zero      个人考核金 D 是否清零（团队值仍计入门店小计）
#   ref_store 是否引用门店小计行（店长口径）
ROLE_RULES = {
    "销售顾问": dict(base=1000, tier="销售顾问", zero=False, ref_store=False),
    "客户经理": dict(base=1000, tier="客户经理", zero=False, ref_store=False),
    "店长":     dict(base=2000, tier="店长",     zero=False, ref_store=True),
    # 带教导师：阈值并销售顾问档；用户口径「不计个人考核金，但团队仍算进门店小计」
    # ★ 阈值表按「角色名」逐行生成（M/R/W 是按角色名 LOOKUP 的），所以每个角色都要有一行
    "带教导师": dict(base=1000, tier="销售顾问", zero=True,  ref_store=False),
}

# 阈值档位表（角色 → 新建线索数指标 / 第一成交率指标 / ABC转化率指标）
THRESHOLD_TIERS = {
    "销售顾问": (45, 0.30, 0.30),
    "客户经理": (35, 0.15, 0.15),
    "店长":     (15, 0.15, 0.15),
}

SUB_TOTAL_BASE = 2000          # 门店小计行基础奖金
SUB_FIRST_RATE = 0.15          # 门店小计行 第一成交率指标（模板惯例固定 0.15）
SUB_ABC_RATE = 0.15            # 门店小计行 ABC转化率指标（模板惯例固定 0.15）

STOPPED_SUFFIX = "(已停用)"
MONTH_COL = {8: "D", 9: "E", 10: "F", 11: "G", 12: "H"}

# ★ 样式模板目标表里没有的新人 —— 必须显式给，脚本不会替你猜目标
#   姓名: (职位, [8月, 9月, 10月, 11月, 12月])   单位：万元
NEW_TARGET = {
    # 示例（2026-09 汪凌杰新任恒大店店长，沿用店长档 15 万）：
    # "汪凌杰": ("店长", [15, 15, 15, 15, 15]),
}

# ★ 样式模板里没有的新人 / 新门店的高亮色 —— (theme索引, tint) 或 "#RRGGBB"
EXTRA_HIGHLIGHT = {
    # 示例（2026-09 汪凌杰 = 恒大店店长，accent4 浅色）：
    # "汪凌杰": (7, 0.6),
}

SUB_INHERIT_CAPTAIN_COLOR = True   # 门店小计行是否继承本店店长的整行底色

# ---- 表头容错：按优先级给出候选关键字 ----
HDR_DEPT  = ["二级部门(主属部门)", "二级部门（主属部门）", "主属部门-3", "主属部门-2", "主属部门", "部门"]
HDR_NAME  = ["员工姓名", "姓名"]
HDR_ROLE  = ["考核角色", "角色"]
HDR_TGT   = ["月度销售指标"]
HDR_AMT   = ["月度整体销售金额"]
HDR_LEADT = ["月度新建线索数指标"]
HDR_LEAD  = ["新建线索数（创建人）", "新建线索数(创建人)", "新建线索数"]
HDR_FIRST = ["第一成交顾客数"]
HDR_ABC   = ["ABC成交顾客数"]
SKIP_NAMES = ("", "总计", "小计", "合计")

# ==================================================================
#  二、工具
# ==================================================================
def L(c):
    return openpyxl.utils.get_column_letter(c)


def ci(names, *keys):
    """按优先级找列（0-based 下标）；找不到抛 KeyError"""
    for k in keys:
        for i, h in enumerate(names):
            if h and k in str(h):
                return i
        for i, h in enumerate(names):          # 第二遍：忽略全/半角括号差异
            if h and k.replace("(", "（").replace(")", "）") in str(h).replace("(", "（").replace(")", "）"):
                return i
    raise KeyError(f"表头找不到 {keys}（现有表头：{names}）")


def tval(c):
    v = c.value
    return v.text if isinstance(v, ArrayFormula) else v


def fill_key(f):
    """把 fill 归一成可比较的 key；（无填充 → None）"""
    try:
        if f is None or f.fill_type is None:
            return None
        fg = f.fgColor
        if fg is None:
            return None
        if fg.type == "theme":
            return ("theme", fg.theme, fg.tint)
        if fg.type == "rgb":
            return ("rgb", str(fg.rgb))
        if fg.type == "indexed":
            return ("indexed", fg.indexed)
        return (fg.type,)
    except Exception:
        return None


def is_red(f):
    k = fill_key(f)
    return bool(k and k[0] == "rgb" and str(k[1]).upper().endswith("FF0000"))


def pick_out(base):
    """若目标文件被 WPS/Excel 占用无法覆盖，则返回带递增后缀的可用名"""
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


def snapshot_row(ws, r, ncol):
    return [copy.copy(ws.cell(r, c)._style) for c in range(1, ncol + 1)]


def apply_snapshot(ws, r, snap, ncol=None):
    for i, st in enumerate(snap, start=1):
        if ncol and i > ncol:
            break
        ws.cell(r, i)._style = copy.copy(st)


def paint_row(ws, r, snap, key, ncol=31):
    """套用整行底色：以 snap 为底，把 A..Y(前25列) 统一刷成 key 颜色，其余列沿用 snap"""
    apply_snapshot(ws, r, snap, ncol=ncol)
    if not key:
        return
    if key[0] == "RGB":
        fg = bg = Color(rgb=key[1])
    else:
        fg = bg = Color(theme=key[1], tint=key[2])
    for c in range(1, 26):                      # A..Y
        f = PatternFill(fill_type="solid", fgColor=fg, bgColor=bg)
        ws.cell(r, c).fill = f


def strip_fill(ws, r, ncol=31):
    for c in range(1, ncol + 1):
        ws.cell(r, c).fill = PatternFill(fill_type=None)


# ==================================================================
#  三、命令行 / 源文件
# ==================================================================
args = [a for a in sys.argv[1:] if not a.startswith("--")]
OPTS = {}
for a in sys.argv[1:]:
    if a.startswith("--") and "=" in a:
        k, v = a[2:].split("=", 1)
        OPTS[k] = v

if len(args) < 4:
    print(__doc__)
    raise SystemExit("用法：python gen_qianxin_amount.py <F1> <F2> <F3> <月份> [V2] [补充人员表 ...]")

F1 = args[0]
F2 = args[1]
F3 = args[2]
REPORT_MONTH = str(args[3]).strip()
EXTRA_SHEETS = args[5:] if len(args) > 5 else []

if REPORT_MONTH not in [str(m) for m in MONTH_COL]:
    raise SystemExit(f"[X] 月份 {REPORT_MONTH} 无对应目标列，请用 8/9/10/11/12 或 --target-col=D 显式指定")
TARGET_COL = OPTS.get("target-col", MONTH_COL[int(REPORT_MONTH)])

# ---- 命令行一次性覆盖（免改脚本）----
#   --new-target="汪凌杰:店长:15,15,15,15,15;某人:客户经理:10,10,10,10,10"
for _spec in OPTS.get("new-target", "").split(";"):
    _spec = _spec.strip()
    if not _spec:
        continue
    _nm, _pos, _vals = _spec.split(":")
    NEW_TARGET[_nm.strip()] = (_pos.strip(), [float(x) for x in _vals.split(",")])
#   --highlight="汪凌杰:7:0.6"  或  --highlight="某人:#FFC000"
for _spec in OPTS.get("highlight", "").split(";"):
    _spec = _spec.strip()
    if not _spec:
        continue
    _p = _spec.split(":")
    if len(_p) == 3:
        EXTRA_HIGHLIGHT[_p[0].strip()] = (int(_p[1]), float(_p[2]))
    else:
        EXTRA_HIGHLIGHT[_p[0].strip()] = _p[1].strip()

WD = os.path.dirname(os.path.abspath(F2))
# 样式模板：显式 > 同月「_美化版」> F1
if len(args) > 4:
    V2 = args[4]
else:
    cand = [os.path.join(WD, f"乾鑫{REPORT_MONTH}月考核金额表_美化版.xlsx"),
            os.path.join(os.getcwd(), f"乾鑫{REPORT_MONTH}月考核金额表_美化版.xlsx")]
    V2 = next((p for p in cand if os.path.exists(p)), F1)
OUT = pick_out(os.path.join(os.getcwd(), f"乾鑫{REPORT_MONTH}月考核金额表_美化版.xlsx"))

print("=" * 78)
print(f"乾鑫 {REPORT_MONTH} 月考核金额表   |   目标列 = {TARGET_COL}   |   输出 = {os.path.basename(OUT)}")
print("=" * 78)
print(f"  F1 上期模板   : {F1}")
print(f"  F2 本月基础表 : {F2}")
print(f"  F3 本月人员表 : {F3}")
print(f"  V2 样式模板   : {V2}")
for e in EXTRA_SHEETS:
    print(f"  补充人员表    : {e}")

# ==================================================================
#  四、读 F2（本月基础表）→ 自动分组
# ==================================================================
wb2 = openpyxl.load_workbook(F2, data_only=True)
ws2 = wb2[wb2.sheetnames[0]]
F2_HDR = [ws2.cell(1, c).value for c in range(1, ws2.max_column + 1)]
I_DEPT  = ci(F2_HDR, *HDR_DEPT)
I_NAME  = ci(F2_HDR, *HDR_NAME)
I_ROLE  = ci(F2_HDR, *HDR_ROLE)
I_TGT   = ci(F2_HDR, *HDR_TGT)
I_AMT   = ci(F2_HDR, *HDR_AMT)
I_LEADT = ci(F2_HDR, *HDR_LEADT)
I_LEAD  = ci(F2_HDR, *HDR_LEAD)
I_FIRST = ci(F2_HDR, *HDR_FIRST)
I_ABC   = ci(F2_HDR, *HDR_ABC)

F2DATA = {}
GROUPS = []          # [(门店全名, [成员名, ...]), ...]  按 F2 出现顺序
for r in range(2, ws2.max_row + 1):
    raw = ws2.cell(r, I_NAME + 1).value
    if raw is None or str(raw).strip() in SKIP_NAMES:
        continue
    nm = str(raw).strip()
    dept = ws2.cell(r, I_DEPT + 1).value
    dept = str(dept).strip() if dept is not None else ""
    F2DATA[nm] = {
        "dept": dept,
        "role": (str(ws2.cell(r, I_ROLE + 1).value).strip()
                 if ws2.cell(r, I_ROLE + 1).value is not None else None),
        "amt": ws2.cell(r, I_AMT + 1).value,
        "lead": ws2.cell(r, I_LEAD + 1).value,
        "first": ws2.cell(r, I_FIRST + 1).value,
        "abc": ws2.cell(r, I_ABC + 1).value,
    }
    if not GROUPS or GROUPS[-1][0] != dept:
        GROUPS.append([dept, []])
    GROUPS[-1][1].append(nm)
GROUPS = [(g, m) for g, m in GROUPS if g]

roles_used = {v["role"] for v in F2DATA.values()}
print(f"\n[1] F2 读取 {len(F2DATA)} 人 / {len(GROUPS)} 个门店")
print("    门店顺序: " + " → ".join(f"{g}({len(m)})" for g, m in GROUPS))
print("    角色分布: " + ", ".join(f"{r}={sum(1 for v in F2DATA.values() if v['role'] == r)}"
                                    for r in sorted(x for x in roles_used if x)))

# ---- 角色必须全部登记，否则报错（禁止猜） ----
unknown = sorted(r for r in roles_used if r not in ROLE_RULES)
if unknown:
    raise SystemExit(f"[X] F2 出现未登记角色 {unknown}，请在 ROLE_RULES 中登记后再跑（禁止推算）")
missing_tier = sorted({ROLE_RULES[r]["tier"] for r in roles_used} - set(THRESHOLD_TIERS))
if missing_tier:
    raise SystemExit(f"[X] 阈值档位 {missing_tier} 未在 THRESHOLD_TIERS 中定义")
# 阈值表按「角色名」逐行生成 —— 顺序取 ROLE_RULES 的声明顺序（见文件顶部）
used_roles = [r for r in ROLE_RULES if r in roles_used]

# ==================================================================
#  五、打开样式模板，扫描样式库
# ==================================================================
wb = openpyxl.load_workbook(V2, data_only=False)
ws = wb["新绩效"]
NCOL = max(ws.max_column, 31)
ws_max_row = ws.max_row          # 供清行范围用（不再写死 39）

TPL_COLOR = {}       # 名称(人/门店) → 整行底色 key
TPL_ROW_SNAP = {}    # 名称 → 整行样式快照
normal_snap = sub_snap = stopped_snap = None

for r in range(2, ws_max_row + 1):
    c3 = ws.cell(r, 3).value
    if not isinstance(c3, str) or not c3.strip():
        continue
    nm = c3.strip()
    a = ws.cell(r, 1).value
    is_sub = (a is not None and str(a).strip() == nm) and not ws.cell(r, 2).value
    snap = snapshot_row(ws, r, NCOL)
    col = fill_key(ws.cell(r, 2).fill)          # B 列有底色 = 整行高亮
    if col:
        TPL_COLOR[nm] = ("THEME", col[1], col[2]) if col[0] == "theme" else ("RGB", col[1])
        TPL_ROW_SNAP[nm] = snap
    elif is_red(ws.cell(r, 3).fill) and stopped_snap is None:
        stopped_snap = snap
    elif is_sub and sub_snap is None:
        sub_snap = snap
    elif (not is_sub) and normal_snap is None:
        normal_snap = snap

if normal_snap is None:
    raise SystemExit("[X] 样式模板里找不到「普通人员行」，无法建立样式库")
if sub_snap is None:
    sub_snap = normal_snap
if stopped_snap is None:
    stopped_snap = normal_snap
for nm, c in EXTRA_HIGHLIGHT.items():
    TPL_COLOR[nm] = (("THEME", c[0], c[1]) if isinstance(c, tuple) and len(c) == 2 else ("RGB", c))
print(f"[2] 样式库: 高亮行 {len(TPL_COLOR)} 个 → {list(TPL_COLOR)}"
      f" | 停用行 {'有' if stopped_snap is not normal_snap else '无'}")

# ---- 门店 → 店长（用于小计行继承底色） ----
CAPTAIN = {}
for g, members in GROUPS:
    for nm in members:
        if F2DATA.get(nm, {}).get("role") == "店长" and g not in CAPTAIN:
            CAPTAIN[g] = nm
print(f"    门店店长: {CAPTAIN if CAPTAIN else '（无）'}")

# ==================================================================
#  六、重建「新绩效」
# ==================================================================
for mc in list(ws.merged_cells.ranges):
    ws.unmerge_cells(str(mc))
for r in range(2, ws_max_row + 1):          # 动态清行（含阈值表区）
    for c in range(1, NCOL + 1):
        ws.cell(r, c).value = None


def set_arr(r, c, formula):
    ws.cell(r, c).value = ArrayFormula(f"{L(c)}{r}", formula)


def set_f(r, c, formula):
    ws.cell(r, c).value = formula


# ---- 行布局 ----
row = 2
layout = []                                  # [r, kind, nm, shop, sub, r1, r2]
for shop, members in GROUPS:
    r1 = row
    for nm in members:
        layout.append([row, "P", nm, shop, None, None, None])
        row += 1
    r2 = row - 1
    sub = row
    layout.append([sub, "S", shop, shop, None, r1, r2])
    row += 1
    for it in layout:
        if it[1] == "P" and it[3] == shop and it[4] is None:
            it[4] = sub
TOTAL_ROW = row
SUB_ROWS = [it[0] for it in layout if it[1] == "S"]
N_PERSON = sum(1 for it in layout if it[1] == "P")
print(f"[3] 行布局: 人员 {N_PERSON} 人, 小计行 {SUB_ROWS}, 合计行 R{TOTAL_ROW}")

# ---- 人员行 ----
n_zero = 0
for (r, kind, nm, shop, sub, _, _) in layout:
    if kind != "P":
        continue
    d = F2DATA[nm]
    rule = ROLE_RULES[d["role"]]
    set_arr(r, 1, f"=LOOKUP(1,0/(人员!D:D=C{r}),人员!A:A)")               # A 部门
    ws.cell(r, 2).value = d["role"]                                        # B 考核角色
    ws.cell(r, 3).value = nm                                               # C 员工姓名
    if rule["zero"]:
        ws.cell(r, 4).value = 0                                            # D 个人考核金清零
        n_zero += 1
    else:
        set_f(r, 4, f"=F{r}+K{r}+P{r}+U{r}")                               # D 考核金额
    ws.cell(r, 5).value = rule["base"]                                     # E 基础奖金
    if rule["ref_store"]:                                                  # F/K/P/U 店长引用门店小计
        set_f(r, 6,  f"=F{sub}")
        set_f(r, 11, f"=K{sub}")
        set_f(r, 16, f"=P{sub}")
        set_f(r, 21, f"=U{sub}")
    else:                                                                  # 其余按个人达成率自算
        set_f(r, 6,  f"=IF(J{r}>=0.7,IF(J{r}>=1,G{r},J{r}*G{r}),0)")
        set_f(r, 11, f"=IF(O{r}>=1,L{r},0)")
        set_f(r, 16, f"=IF(T{r}>=R{r},Q{r},0)")
        set_f(r, 21, f"=IF(Y{r}>=W{r},V{r},0)")
    set_f(r, 7,  f"=E{r}*0.4")                                             # G 权重
    set_arr(r, 8, f"=LOOKUP(1,0/(目标!B:B=C{r}),目标!{TARGET_COL}:{TARGET_COL})*10000")   # H 月度销售指标
    set_arr(r, 9, f"=LOOKUP(1,0/(基数表!C:C=C{r}),基数表!F:F)")             # I 月度整体销售金额(含变更)
    set_f(r, 10, f"=I{r}/H{r}")                                            # J 达成率
    set_f(r, 12, f"=E{r}*0.2")                                             # L 权重
    set_arr(r, 13, f"=LOOKUP(1,0/(AB:AB=B{r}),AC:AC)")                      # M 新建线索数指标
    ws.cell(r, 14).value = d["lead"]                                       # N 新建线索数
    set_f(r, 15, f"=IFERROR(N{r}/M{r},0)")                                 # O 达成率
    set_f(r, 17, f"=E{r}*0.2")                                             # Q 权重
    set_arr(r, 18, f"=LOOKUP(1,0/(AB:AB=B{r}),AD:AD)")                      # R 第一成交率指标
    ws.cell(r, 19).value = d["first"]                                      # S 第一成交顾客数
    set_f(r, 20, f"=IFERROR(S{r}/N{r},0)")                                 # T 第一成交率
    set_f(r, 22, f"=E{r}*0.2")                                             # V 权重
    set_arr(r, 23, f"=LOOKUP(1,0/(AB:AB=B{r}),AE:AE)")                      # W ABC转化率指标
    ws.cell(r, 24).value = d["abc"]                                        # X ABC成交顾客数
    set_f(r, 25, f"=IFERROR(X{r}/N{r},0)")                                 # Y ABC线索转化率

# ---- 小计行 ----
for (r, kind, shop, _, _, r1, r2) in layout:
    if kind != "S":
        continue
    ws.cell(r, 1).value = shop
    ws.cell(r, 3).value = shop
    set_f(r, 4,  f"=F{r}+K{r}+P{r}+U{r}")
    ws.cell(r, 5).value = SUB_TOTAL_BASE
    set_f(r, 6,  f"=IF(J{r}>=0.7,IF(J{r}>=1,G{r},J{r}*G{r}),0)")
    set_f(r, 7,  f"=E{r}*0.4")
    set_arr(r, 8, f"=LOOKUP(1,0/(目标!B:B=C{r}),目标!{TARGET_COL}:{TARGET_COL})*10000")
    set_f(r, 9,  f"=SUM(I{r1}:I{r2})")
    set_f(r, 10, f"=I{r}/H{r}")
    set_f(r, 11, f"=IF(O{r}>=1,L{r},0)")
    set_f(r, 12, f"=E{r}*0.2")
    set_f(r, 13, f"=SUM(M{r1}:M{r2})")
    set_f(r, 14, f"=SUM(N{r1}:N{r2})")
    set_f(r, 15, f"=IFERROR(N{r}/M{r},0)")
    set_f(r, 16, f"=IF(T{r}>=R{r},Q{r},0)")
    set_f(r, 17, f"=E{r}*0.2")
    ws.cell(r, 18).value = SUB_FIRST_RATE
    set_f(r, 19, f"=SUM(S{r1}:S{r2})")
    set_f(r, 20, f"=IFERROR(S{r}/N{r},0)")
    set_f(r, 21, f"=IF(Y{r}>=W{r},V{r},0)")
    set_f(r, 22, f"=E{r}*0.2")
    ws.cell(r, 23).value = SUB_ABC_RATE
    set_f(r, 24, f"=SUM(X{r1}:X{r2})")
    set_f(r, 25, f"=IFERROR(X{r}/N{r},0)")

# ---- 合计行 ----
tr = TOTAL_ROW
set_f(tr, 4, f"=SUM(D2:D{tr-1})" + "".join(f"-D{r}" for r in SUB_ROWS))
set_f(tr, 9, f"=SUM(I2:I{tr-1})" + "".join(f"-I{r}" for r in SUB_ROWS))
# 合计行样式 = 最后一个门店小计行（动态，不再写死 R27）；随后去底色
last_sub_snap = snapshot_row(ws, SUB_ROWS[-1], NCOL) if ws.cell(SUB_ROWS[-1], 3).value else sub_snap
apply_snapshot(ws, tr, last_sub_snap, ncol=NCOL)
strip_fill(ws, tr, ncol=NCOL)

# ---- 按名称/角色复刻行样式 ----
for (r, kind, nm, shop, _, _, _) in layout:
    if kind == "S":
        key = None
        if SUB_INHERIT_CAPTAIN_COLOR and shop in CAPTAIN:
            key = TPL_COLOR.get(CAPTAIN[shop])
        paint_row(ws, r, sub_snap, key, ncol=NCOL)
    elif nm in TPL_COLOR:
        paint_row(ws, r, normal_snap, TPL_COLOR[nm], ncol=NCOL)
    elif nm.endswith(STOPPED_SUFFIX):
        apply_snapshot(ws, r, stopped_snap, ncol=NCOL)
    else:
        apply_snapshot(ws, r, normal_snap, ncol=NCOL)

# ---- 阈值表 AB:AE（按实际出现的「角色名」自动生成，从 R36 起） ----
THR_START = 36
prev_thr_row = None
for i, role in enumerate(used_roles):
    r = THR_START + i
    m, fr, abc = THRESHOLD_TIERS[ROLE_RULES[role]["tier"]]
    ws.cell(r, 28).value = role
    ws.cell(r, 29).value = m
    ws.cell(r, 30).value = fr
    ws.cell(r, 31).value = abc
    if prev_thr_row is not None:
        sn = snapshot_row(ws, prev_thr_row, NCOL)
        apply_snapshot(ws, r, sn, ncol=NCOL)
    prev_thr_row = r

# ---- 列级数字格式统一 ----
# 模板里各行的金额/比率列格式并不齐（例：滨江小计行的 K 列是 General，会显示成 400 而不是 400.00），
# 这里按列统一，覆盖模板的逐行差异，保证整列显示一致。
COL_NUMBER_FORMAT = {
    4:  "0.00_ ",   # D  考核金额
    6:  "0.00_ ",   # F  任务达成金
    8:  "0.00",     # H  月度销售指标
    9:  "0.00_ ",   # I  月度整体销售金额（含变更）
    10: "0.00%",    # J  月度整体销售达成率
    11: "0.00_ ",   # K  线索达成金额
    15: "0.00%",    # O  新建线索数达成率
    16: "0.00_ ",   # P  第一成交达成金额
    18: "0.00%",    # R  第一成交率指标
    20: "0.00%",    # T  第一成交率
    21: "0.00_ ",   # U  ABC成交达成金额
    23: "0.00%",    # W  ABC线索转化率指标
    25: "0.00%",    # Y  ABC线索转化率
}
_fmt_last = TOTAL_ROW                    # 只统一表格区（第 2 行 ~ 合计行），表外空行不动
for _c, _fmt in COL_NUMBER_FORMAT.items():
    for _r in range(2, _fmt_last + 1):
        ws.cell(_r, _c).number_format = _fmt
print(f"[3] 新绩效写入完成 | 阈值表 R{THR_START}-R{THR_START + len(used_roles) - 1}"
      f" = {used_roles} | D 列清零 {n_zero} 人")

# ==================================================================
#  七、重建「基数表」（嵌套 F2）
# ==================================================================
wsb = wb["基数表"]
for mc in list(wsb.merged_cells.ranges):
    wsb.unmerge_cells(str(mc))
for r in range(1, wsb.max_row + 1):
    for c in range(1, wsb.max_column + 1):
        wsb.cell(r, c).value = None
base_row_snap = snapshot_row(wsb, 2, wsb.max_column)
for r in range(1, ws2.max_row + 1):
    for c in range(1, ws2.max_column + 1):
        wsb.cell(r, c).value = ws2.cell(r, c).value
for r in range(2, ws2.max_row + 1):
    apply_snapshot(wsb, r, base_row_snap, ncol=wsb.max_column)
print(f"[4] 基数表 嵌套完成: {ws2.max_row} 行 x {ws2.max_column} 列")

# ==================================================================
#  八、重建「人员表」
# ==================================================================
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
# 部门相关列（用于「以 F2 为准」覆写）
DEPT_COLS = [i for i, h in enumerate(F3_HDR)
             if h and str(h).strip() in ("负责人所在部门", "归属部门", "主属部门（必填）")]
print(f"[5] 人员表: 负责人所在部门 = F3 第 {i_dept_f3 + 1} 列 → 新表 {L(U_COL)} 列；部门列 {[L(3 + i) for i in DEPT_COLS]}")

# ---- ① F3 本月导出 ----
r = 2
have = set()
for r3 in range(2, ws3.max_row + 1):
    if ws3.cell(r3, 2).value is None or str(ws3.cell(r3, 2).value).strip() == "":
        continue
    for i in range(N3):
        wsp.cell(r, 3 + i).value = ws3.cell(r3, i + 1).value
    have.add(str(ws3.cell(r3, 2).value).strip())
    r += 1
n_f3 = r - 2

# ---- ② 补齐池：补充人员表（优先）+ F1 人员表 ----
# ★ 各版本人员表列数/列序可能不同（F1 比 F3 少 2 列，且「主属部门」没有「（必填）」后缀），
#   所以一律**按列名映射**读取，绝不能按位置读。
import re as _re


def _norm_hdr(h):
    return _re.sub(r"[（(].*?[）)]", "", str(h)).strip()


POOL = []            # [(路径, ws, {列名:列号}, {规范化列名:列号}, 系统名列号)]
for p in list(EXTRA_SHEETS) + [F1]:
    try:
        wbx = openpyxl.load_workbook(p, data_only=True)
        wsx = wbx["人员"] if "人员" in wbx.sheetnames else wbx[wbx.sheetnames[0]]
        byname, bynorm, nk = {}, {}, None
        for c in range(1, wsx.max_column + 1):
            h = wsx.cell(1, c).value
            if not h:
                continue
            hs = str(h).strip()
            byname[hs] = c                       # 同名取最后一列（跳过旧版前置的重复列）
            bynorm[_norm_hdr(hs)] = c
            if "系统名（昵称）（必填）" in hs or _norm_hdr(hs) == "系统名":
                nk = c
        if nk is None:
            print(f"    [!] {p} 找不到「系统名」列，跳过该补齐池")
            continue
        POOL.append((p, wsx, byname, bynorm, nk))
    except Exception as e:
        print(f"    [!] 补齐池读取失败 {p}: {e}")


def take_from_pool(base_name):
    """按本名到补齐池取一整行；返回 (来源路径, 按 F3 列序对齐的值列表)"""
    for p, wsx, byname, bynorm, nk in POOL:
        rr = None
        for r2 in range(2, wsx.max_row + 1):
            v = wsx.cell(r2, nk).value
            if v and str(v).strip() == base_name:
                rr = r2
                break
        if rr is None:
            continue
        vals = [None] * N3
        for i, h in enumerate(F3_HDR):
            if not h:
                continue
            hs = str(h).strip()
            sc = byname.get(hs) or bynorm.get(_norm_hdr(hs))
            if sc:
                vals[i] = wsx.cell(rr, sc).value
        return p, vals
    return None, None


# 目标名册 = F2 全部人名（含停用）；缺席者补齐
need = [nm for _, members in GROUPS for nm in members]
n_pool = 0
for nm in need:
    if nm in have:
        continue
    base = nm[:-len(STOPPED_SUFFIX)] if nm.endswith(STOPPED_SUFFIX) else nm
    src, vals = take_from_pool(base)
    if vals is None:
        src, vals = take_from_pool(nm)
    if vals is None:
        print(f"    [!] 补齐失败：{nm} 在 F3 与所有补齐池中都找不到 → 新绩效 A 列会 #N/A")
        continue
    if len(vals) < N3:
        vals = vals + [None] * (N3 - len(vals))
    # 部门列以 F2 为准（本月权威）
    dept = F2DATA.get(nm, {}).get("dept")
    if dept:
        for i in DEPT_COLS:
            old = vals[i]
            if isinstance(old, str) and "/" in old:
                vals[i] = old.rsplit("/", 1)[0] + "/" + dept
            else:
                vals[i] = dept
    vals[1] = nm                       # 第 2 列 = 系统名（含 (已停用) 后缀）
    for i in range(N3):
        wsp.cell(r, 3 + i).value = vals[i]
    have.add(nm)
    r += 1
    n_pool += 1
n_all = r - 2
print(f"    人员表 = F3 {n_f3} 人 + 补齐 {n_pool} 人 = {n_all} 人")

# ---- A/B 列公式 + 样式 ----
wsp_row_snap = snapshot_row(wsp, 2, wsp.max_column)
for rr in range(2, r):
    wsp.cell(rr, 1).value = f"={L(U_COL)}{rr}"                 # 修复 v1 写死 U 列的 bug
    wsp.cell(rr, 2).value = ArrayFormula(f"B{rr}", f"=LOOKUP(1,0/(新绩效!C:C=D{rr}),新绩效!C:C)")
for rr in range(2, r):
    apply_snapshot(wsp, rr, wsp_row_snap, ncol=wsp.max_column)

# ==================================================================
#  九、重建「目标」表
# ==================================================================
# 数据源：上期模板的「目标」sheet
# ★ 必须 data_only=False —— 门店小计行的判据是「D..H 是 =SUM() 公式」，
#   用 data_only=True 会读到缓存值/None，导致小计行被误判成人员行、短码映射失效
wst0 = openpyxl.load_workbook(F1, data_only=False)["目标"]
TGT = {}           # 本名 → (职位, [D..H])
SHORT = {}         # 门店全名 → 短码
DIST = None        # 分销行 [D..H]


def bare(nm):
    """去掉 (已停用) 后缀，用于跨月按本名匹配（上期模板里的名字没有后缀）"""
    return nm[:-len(STOPPED_SUFFIX)] if nm.endswith(STOPPED_SUFFIX) else nm


for rr in range(1, wst0.max_row + 1):
    a = str(wst0.cell(rr, 1).value or "").strip()
    who = wst0.cell(rr, 2).value
    vals = [wst0.cell(rr, c).value for c in range(4, 9)]
    if a == "分销":
        DIST = vals
        continue
    if a == "合计":
        continue
    # 门店小计行判据：D..H 全是公式（=SUM(...)）；人员行是数字
    if vals and all(isinstance(v, str) and v.startswith("=") for v in vals):
        if who:
            SHORT[str(who).strip()] = a
        continue
    if who:
        TGT[str(who).strip()] = (wst0.cell(rr, 3).value, vals)
if DIST is None:
    raise SystemExit("[X] 上期模板「目标」表里找不到『分销』行，无法重建目标表")

# 新人必须显式配置
for g, members in GROUPS:
    for nm in members:
        if bare(nm) not in TGT and bare(nm) not in NEW_TARGET:
            raise SystemExit(f"[X] 目标表模板里没有 {bare(nm)}，请在脚本顶部 NEW_TARGET 显式配置其职位与 5 个月目标（禁止推算）")
_all_bare = {bare(m) for _, ms in GROUPS for m in ms}
for nm in NEW_TARGET:
    if nm not in _all_bare:
        print(f"    [!] NEW_TARGET 里的 {nm} 本月不在名册，已忽略")

wst = wb["目标"]
for mc in list(wst.merged_cells.ranges):
    wst.unmerge_cells(str(mc))
goal_last = wst.max_row
for rr in range(1, goal_last + 1):
    for c in range(1, wst.max_column + 1):
        wst.cell(rr, c).value = None
# 样式快照（源行可能与输出行重叠，必须先抓）
goal_style_person = snapshot_row(wst, 3, 12)
goal_style_sub    = snapshot_row(wst, 7, 12)
goal_style_dist   = snapshot_row(wst, 29, 12)
goal_style_total  = snapshot_row(wst, 30, 12)

wst.cell(1, 1).value = "2026年乾鑫保底指标"
for i, h in enumerate(["门店", "人员", "职位", "8月", "9月", "10月", "11月", "12月", "合计", "总计"], start=1):
    wst.cell(2, i).value = h

# 每个门店：先按上期顺序排（保留相对次序），本店新进的追加到末尾
row = 3
sub_rows_goal = []
for shop, members in GROUPS:
    bare2real = {bare(m): m for m in members}
    short = SHORT.get(shop)
    order_bare = []
    for rr in range(3, wst0.max_row + 1):
        n0 = wst0.cell(rr, 2).value
        if not n0:
            continue
        a0 = str(wst0.cell(rr, 1).value or "").strip()
        if short is not None and a0 != short:
            continue                                   # ★ 只取「上期同门店块」内的人，避免调店者被提前捞出
        n0b = str(n0).strip()
        if n0b in TGT and n0b in bare2real and n0b not in order_bare:
            order_bare.append(n0b)
    ordered = [bare2real[b] for b in order_bare]
    ordered += [m for m in members if m not in ordered]        # 本店新进 → 追加到末尾
    r1 = row
    for nm in ordered:
        base = bare(nm)
        pos, vals = NEW_TARGET[base] if base in NEW_TARGET else TGT[base]
        wst.cell(row, 1).value = SHORT.get(shop, shop)
        wst.cell(row, 2).value = nm
        wst.cell(row, 3).value = pos
        for k, v in enumerate(vals):
            wst.cell(row, 4 + k).value = v
        wst.cell(row, 9).value = f"=SUM(D{row}:H{row})"
        wst.cell(row, 12).value = ArrayFormula(f"L{row}", f"=LOOKUP(1,0/(新绩效!C:C=B{row}),新绩效!C:C)")
        apply_snapshot(wst, row, goal_style_person, ncol=12)
        row += 1
    r2 = row - 1
    wst.cell(row, 1).value = SHORT.get(shop, shop)
    wst.cell(row, 2).value = shop
    for col in "DEFGHI":
        wst.cell(row, openpyxl.utils.column_index_from_string(col)).value = f"=SUM({col}{r1}:{col}{r2})"
    wst.cell(row, 10).value = f"=I{row}"
    apply_snapshot(wst, row, goal_style_sub, ncol=12)
    sub_rows_goal.append(row)
    row += 1

# 分销行
wst.cell(row, 1).value = "分销"
for k, v in enumerate(DIST):
    wst.cell(row, 4 + k).value = v
wst.cell(row, 9).value = f"=SUM(D{row}:H{row})"
wst.cell(row, 10).value = f"=I{row}"
wst.cell(row, 12).value = ArrayFormula(f"L{row}", f"=LOOKUP(1,0/(新绩效!C:C=B{row}),新绩效!C:C)")
apply_snapshot(wst, row, goal_style_dist, ncol=12)
dist_row = row
row += 1

# 合计行
wst.cell(row, 1).value = "合计"
for col in "DEFGH":
    wst.cell(row, openpyxl.utils.column_index_from_string(col)).value = \
        "=" + "+".join(f"{col}{rr}" for rr in sub_rows_goal + [dist_row])
wst.cell(row, 9).value = f"=SUM(D{row}:H{row})"
wst.cell(row, 10).value = f"=I{row}"
wst.cell(row, 12).value = ArrayFormula(f"L{row}", f"=LOOKUP(1,0/(新绩效!C:C=B{row}),新绩效!C:C)")
apply_snapshot(wst, row, goal_style_total, ncol=12)
print(f"[6] 目标表 重建完成: {row} 行（门店小计 {sub_rows_goal} / 分销 R{dist_row} / 合计 R{row}）")

# ==================================================================
#  十、保存
# ==================================================================
wb.calculation.fullCalcOnLoad = True
OUT = pick_out(OUT)
try:
    wb.save(OUT)
except PermissionError:
    OUT = pick_out(OUT)
    wb.save(OUT)
print(f"\n[DONE] 已保存: {OUT}")
print(f"       （打开后由 Excel/WPS 重算；J/O/T/Y 达成率已统一 0.00%）")
