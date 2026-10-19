# -*- coding: utf-8 -*-
"""
欣暖家月度考核金额表生成器 v2
改进点：
  1. 输出工作簿含 3 个 sheet：金额表、人员表、目标表（从用户原表完整保留）。
  2. 美的特渠部下 8 人按最新结构拆到 特定渠道1部 / 特定渠道2部。
  3. 试用期人员按报表月份从目标表选择对应目标行（默认 8 月）。
  4. 门店/渠道小计的目标值直接引用目标表中的合计行，不再简单相加。
  5. 视觉、公式、数字格式与用户 2026-08-19 原表保持一致。

输入：
  base_path      基础数据表（23 列，performance 数据）
  template_path  用户原表模板（含 人员表/目标表/金额表样式）
  report_month   报表月份，用于试用期目标行选择（默认 8）
输出：
  out_path       新版考核金额表 xlsx
"""
import sys, re, openpyxl
from copy import copy

BONUS = 300

OUT_HEADERS = [
    "主属部门-3", "员工姓名", "达成奖金",
    "月度销售指标", "月度整体销售金额（含变更）", "月度整体达成率", "月度整体达成奖金",
    "第一成交率金额指标", "第一成交率金额（含变更）", "第一成交率金额达成率", "第一成交达成奖金",
    "ABC成交金额指标", "ABC成交金额（含变更）", "ABC成交金额达成率", "ABC成交达成奖金",
    "ABC成交客户数（订单对象统计）", "ABC客单价",
    "ABC成交顾客数指标", "ABC成交顾客数", "ABC成交顾客数达成率", "ABC成交顾客数达成奖金",
    "录入ABC线索数指标", "录入ABC线索数", "ABC线索新建达成率", "ABC录入线索达成奖金",
]

# 用户确认的最新部门拆分：特定渠道 1 部 / 2 部
DEPT_OVERRIDES = {
    "吴建": "特定渠道1部",
    "车邦建": "特定渠道1部",
    "韩芬": "特定渠道1部",
    "周晨烨": "特定渠道1部",
    "王浩萍": "特定渠道2部",
    "郁轹文": "特定渠道2部",
    "钟俊楠": "特定渠道2部",
    "陈学健": "特定渠道2部",
}

# 金额表中的分组顺序（按用户原表 + 新拆分）
GROUP_ORDER = [
    "美的滨江店",
    "东芝华东店",
    "东芝宝龙店",
    "特定渠道1部",
    "特定渠道2部",
    "美的特渠部",
]

# 组内人员显示顺序（未指定的组保留基础表原序）
NAME_ORDER = {
    "特定渠道1部": ["吴建", "车邦建", "韩芬", "周晨烨"],
    "特定渠道2部": ["王浩萍", "郁轹文", "钟俊楠", "陈学健"],
}

# 目标表中 门店/渠道合计行 的显示名 -> 金额表主属部门名 映射
TARGET_SUBTOTAL_MAP = {
    "美的滨江店合计": "美的滨江店",
    "东芝华东店合计": "东芝华东店",
    "东芝宝龙店合计": "东芝宝龙店",
    "渠道1部小计": "特定渠道1部",
    "渠道2部小计": "特定渠道2部",
    "渠道部合计": "美的特渠部",
}


def num(v):
    return v if isinstance(v, (int, float)) else 0.0


def parse_period(period_text):
    """
    从试用期说明文字解析适用月份范围。
    例：
      '（7月试用期）'     -> {7}
      '（8-12月）'        -> {8,9,10,11,12}
      '（7.8月试用期）'   -> {7,8}
      '（9-12月）'        -> {9,10,11,12}
      None / 设计师       -> 全月 {1..12}
    """
    if not period_text:
        return set(range(1, 13))
    t = str(period_text).strip("（）()")
    # 7月试用期 / 7.8月试用期
    m = re.search(r"(\d+)(?:\.(\d+))?月试用期", t)
    if m:
        if m.group(2):
            return {int(m.group(1)), int(m.group(2))}
        return {int(m.group(1))}
    # 8-12月 / 9-12月
    m = re.search(r"(\d+)-(\d+)月", t)
    if m:
        return set(range(int(m.group(1)), int(m.group(2)) + 1))
    # 默认全年
    return set(range(1, 13))


def load_base_data(base_path):
    """读取基础数据表，仅保留人员行，返回字典列表。"""
    wb = openpyxl.load_workbook(base_path, data_only=True, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    headers = rows[0]
    persons = []
    for r in rows[1:]:
        name = r[2]
        if name is None:
            continue
        ns = str(name).strip()
        if ns == "" or "小计" in ns or ns == "公司小计" or ns == "总计":
            continue
        rec = {
            "name": ns,
            "dept": r[1],
            # 基础绩效数据（仅读取实际完成值，目标值和达成率全部以目标表为准）
            "monthly_sales_amount": num(r[5]),  # 月度整体销售金额（含变更）
            "first_deal_amount": num(r[9]),     # 第一成交率金额（含变更）
            "abc_amount": num(r[13]),           # ABC成交金额（含变更）
            "abc_customers": num(r[15]),        # ABC成交客户数
            "abc_customer_count": num(r[18]),   # ABC成交顾客数
            "abc_leads": num(r[21]),            # 录入ABC线索数
            "disabled": "停用" in ns,
        }
        persons.append(rec)
    return persons


def load_target_table(template_path, report_month):
    """
    从模板工作簿的目标表读取目标，按 report_month 选择试用期人员的对应行。
    返回：
      person_targets: {name: {monthly, first_deal, abc_amount, customers, leads}}
      subtotal_targets: {dept_name: {monthly, first_deal, abc_amount, customers, leads}}
    """
    wb = openpyxl.load_workbook(template_path, data_only=True, read_only=False)
    if "目标表" not in wb.sheetnames:
        raise ValueError(f"模板文件缺少【目标表】sheet: {template_path}")
    ws = wb["目标表"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    # 目标表列：A=序号/门店, B=人员, C=试用期说明, D=月度销售指标, E=第一成交率金额,
    #           G=ABC成交金额, I=成交顾客数, K=录入ABC线索数量
    raw_rows = []
    for r in rows:
        store_or_dept = str(r[0]).strip() if r[0] else ""
        person = str(r[1]).strip() if r[1] else ""
        # 人员为空但门店/合计列含小计/合计关键词的，仍保留作为小计行
        if r[1] is None and not any(k in store_or_dept for k in TARGET_SUBTOTAL_MAP):
            continue
        period = str(r[2]).strip() if r[2] else None
        monthly = num(r[3])
        first_deal = num(r[4])
        abc_amount = num(r[6])
        customers = num(r[8])
        leads = num(r[10])
        raw_rows.append({
            "store": store_or_dept,
            "person": person,
            "period": period,
            "monthly": monthly,
            "first_deal": first_deal,
            "abc_amount": abc_amount,
            "customers": customers,
            "leads": leads,
        })

    person_targets = {}
    for row in raw_rows:
        person = row["person"]
        if not person or any(k in row["store"] for k in TARGET_SUBTOTAL_MAP) or "合计" in person or "小计" in person:
            continue
        months = parse_period(row["period"])
        if report_month not in months:
            continue
        # 若同一人员在 8 月命中多行，后覆盖前；正常应只命中一行
        person_targets[person] = {
            "monthly": row["monthly"],
            "first_deal": row["first_deal"],
            "abc_amount": row["abc_amount"],
            "customers": row["customers"],
            "leads": row["leads"],
        }

    subtotal_targets = {}
    for row in raw_rows:
        store = row["store"]
        mapped = TARGET_SUBTOTAL_MAP.get(store)
        if mapped is None:
            continue
        subtotal_targets[mapped] = {
            "monthly": row["monthly"],
            "first_deal": row["first_deal"],
            "abc_amount": row["abc_amount"],
            "customers": row["customers"],
            "leads": row["leads"],
        }

    return person_targets, subtotal_targets


def apply_targets_and_depts(persons, person_targets, report_month):
    """把目标与最新部门合并进人员记录，并返回缺目标人员清单。"""
    missing = []
    for p in persons:
        name = p["name"]
        # 去掉 "(已停用)" 等后缀用于目标匹配
        clean_name = re.sub(r"[（(].*?[)）]", "", name).strip()
        tgt = person_targets.get(clean_name)
        if tgt is None:
            if p["disabled"]:
                tgt = {"monthly": 0, "first_deal": 0, "abc_amount": 0, "customers": 0, "leads": 0}
            else:
                missing.append(name)
                tgt = {"monthly": 0, "first_deal": 0, "abc_amount": 0, "customers": 0, "leads": 0}
        p["target"] = tgt
        # 部门覆盖
        if clean_name in DEPT_OVERRIDES:
            p["dept"] = DEPT_OVERRIDES[clean_name]
    return missing


def safe_rate(actual, target):
    """按目标值计算达成率，目标为空/0 时返回 0。"""
    return actual / target if target else 0.0


def compute_person_bonus(p):
    """按目标表目标值重新计算达成率并判断奖金。"""
    if p["disabled"]:
        return 0, 0, 0, 0, 0, 0
    t = p["target"]
    monthly_rate = safe_rate(p["monthly_sales_amount"], t["monthly"])
    first_rate = safe_rate(p["first_deal_amount"], t["first_deal"])
    abc_rate = safe_rate(p["abc_amount"], t["abc_amount"])
    customer_rate = safe_rate(p["abc_customer_count"], t["customers"])
    lead_rate = safe_rate(p["abc_leads"], t["leads"])
    b4 = BONUS if monthly_rate >= 1 else 0
    b1 = BONUS if first_rate >= 1 else 0
    b3a = BONUS if abc_rate >= 1 else 0
    b3c = BONUS if customer_rate >= 1 else 0
    b2 = BONUS if lead_rate >= 1 else 0
    total = b4 + b1 + max(b3a, b3c) + b2
    return b4, b1, b3a, b3c, b2, total


def build_person_row(p):
    """构建人员输出列（达成率列由 build_workbook 统一写公式）。"""
    t = p["target"]
    b4, b1, b3a, b3c, b2, total = compute_person_bonus(p)
    cust = p["abc_customers"]
    kehu_price = (p["abc_amount"] / cust) if cust else 0.0
    return [
        p["dept"], p["name"], total,
        t["monthly"], p["monthly_sales_amount"], None, b4,          # F 达成率公式 =E/D
        t["first_deal"], p["first_deal_amount"], None, b1,          # J 达成率公式 =I/H
        t["abc_amount"], p["abc_amount"], None, b3a,                # N 达成率公式 =M/L
        p["abc_customers"], kehu_price,
        t["customers"], p["abc_customer_count"], None, b3c,         # T 达成率公式 =S/R
        t["leads"], p["abc_leads"], None, b2,                       # X 达成率公式 =W/V
    ]


def sum_records(recs):
    """对一组人员记录做数值汇总，返回汇总后的列字典。"""
    s = {
        "monthly_sales_amount": 0.0,
        "first_deal_amount": 0.0,
        "abc_amount": 0.0,
        "abc_customers": 0.0,
        "abc_customer_count": 0.0,
        "abc_leads": 0.0,
    }
    for r in recs:
        for k in s:
            s[k] += r[k]
    return s


def build_subtotal_row(dept, recs, tgt, bonus_sums):
    """构建小计/合计输出列（达成率列由 build_workbook 统一写公式）。"""
    s = sum_records(recs)
    b4, b1, b3a, b3c, b2, total = bonus_sums
    cust = s["abc_customers"]
    kehu_price = (s["abc_amount"] / cust) if cust else 0.0
    return [
        dept, "小计", total,
        tgt["monthly"], s["monthly_sales_amount"], None, b4,          # F 公式 =E/D
        tgt["first_deal"], s["first_deal_amount"], None, b1,          # J 公式 =I/H
        tgt["abc_amount"], s["abc_amount"], None, b3a,                # N 公式 =M/L
        s["abc_customers"], kehu_price,
        tgt["customers"], s["abc_customer_count"], None, b3c,         # T 公式 =S/R
        tgt["leads"], s["abc_leads"], None, b2,                       # X 公式 =W/V
    ]


def build_amount_rows(persons, subtotal_targets):
    """按分组顺序构建完整金额表数据行（不含表头）。"""
    # 按部门分组
    groups = {dept: [] for dept in GROUP_ORDER if dept != "美的特渠部"}
    for p in persons:
        d = p["dept"]
        if d in groups:
            groups[d].append(p)
        else:
            # 兜底：未命中分组的人员放到其原部门（理论上不应发生）
            groups.setdefault(d, []).append(p)

    rows = []
    all_persons = []
    subtotal_rows = {}  # dept -> row_data
    subtotal_bonus = {}  # dept -> (b4,b1,b3a,b3c,b2,total)

    # 门店/渠道小组
    for dept in GROUP_ORDER:
        if dept == "美的特渠部":
            continue
        recs = groups.get(dept, [])
        # 若该组有指定顺序，按顺序排列；否则保留基础表原序
        if dept in NAME_ORDER:
            order = {n: i for i, n in enumerate(NAME_ORDER[dept])}
            recs = sorted(recs, key=lambda p: order.get(re.sub(r"[（(].*?[)）]", "", p["name"]).strip(), 999))
        for p in recs:
            rows.append(build_person_row(p))
            all_persons.append(p)
        # 小组小计
        bsum = [0, 0, 0, 0, 0, 0]
        for p in recs:
            bb = compute_person_bonus(p)
            for k in range(6):
                bsum[k] += bb[k]
        tgt = subtotal_targets.get(dept, {"monthly": 0, "first_deal": 0, "abc_amount": 0, "customers": 0, "leads": 0})
        sub_row = build_subtotal_row(dept, recs, tgt, tuple(bsum))
        rows.append(sub_row)
        subtotal_rows[dept] = sub_row
        subtotal_bonus[dept] = tuple(bsum)

    # 美的特渠部 = 特定渠道1部 + 特定渠道2部
    parent_dept = "美的特渠部"
    parent_recs = groups.get("特定渠道1部", []) + groups.get("特定渠道2部", [])
    parent_bsum = [0, 0, 0, 0, 0, 0]
    for p in parent_recs:
        bb = compute_person_bonus(p)
        for k in range(6):
            parent_bsum[k] += bb[k]
    parent_tgt = subtotal_targets.get(parent_dept, {"monthly": 0, "first_deal": 0, "abc_amount": 0, "customers": 0, "leads": 0})
    parent_row = build_subtotal_row(parent_dept, parent_recs, parent_tgt, tuple(parent_bsum))
    rows.append(parent_row)
    subtotal_rows[parent_dept] = parent_row
    subtotal_bonus[parent_dept] = tuple(parent_bsum)

    return rows, all_persons


def copy_style(src_cell, dst_cell):
    dst_cell.font = copy(src_cell.font)
    dst_cell.border = copy(src_cell.border)
    dst_cell.fill = copy(src_cell.fill)
    dst_cell.alignment = copy(src_cell.alignment)
    dst_cell.number_format = src_cell.number_format
    dst_cell.protection = copy(src_cell.protection)


def replace_personnel_sheet(wb, personnel_path):
    """用最新人员对象导出结果替换输出工作簿里的【人员表】sheet。

    - personnel_path 指向纷享销客「人员对象导出结果」xlsx，数据在 '人员数据'（缺省取首个 sheet）。
    - 保留原 sheet 位置，仅替换内容；不破坏金额表/目标表。
    """
    src_wb = openpyxl.load_workbook(personnel_path, data_only=True, read_only=False)
    src_name = "人员数据" if "人员数据" in src_wb.sheetnames else src_wb.sheetnames[0]
    src = src_wb[src_name]
    old_idx = wb.sheetnames.index("人员表") if "人员表" in wb.sheetnames else 1
    if "人员表" in wb.sheetnames:
        del wb["人员表"]
    ws = wb.create_sheet("人员表", old_idx)
    for row in src.iter_rows():
        for c in row:
            if c.value is not None:
                cell = ws.cell(row=c.row, column=c.column, value=c.value)
                cell.number_format = c.number_format
    for col, dim in src.column_dimensions.items():
        if dim.width:
            ws.column_dimensions[col].width = dim.width
    src_wb.close()
    return wb


def build_workbook(template_path, amount_rows, out_path, personnel_path=None):
    """以用户原表为模板，替换金额表，保留人员表/目标表。

    personnel_path 非空时，用最新人员表覆盖输出里的【人员表】sheet（解决“人员有调整、
    模板旧人员表过期”的坑）。
    """
    swb = openpyxl.load_workbook(template_path)
    if personnel_path:
        replace_personnel_sheet(swb, personnel_path)
    main_title = swb.sheetnames[0]
    # 删除旧金额表，重建同名 sheet 并置于首位
    del swb[main_title]
    ows = swb.create_sheet(main_title, 0)

    sws = openpyxl.load_workbook(template_path).active  # 仅用于取样式样本

    # 找样式样本行
    header_rep = 1
    data_rep = 2
    subtotal_rep = None
    for r in range(1, sws.max_row + 1):
        if sws.cell(row=r, column=2).value and "小计" in str(sws.cell(row=r, column=2).value):
            subtotal_rep = r
            break
    if subtotal_rep is None:
        subtotal_rep = 2

    # 写表头
    ows.append(OUT_HEADERS)
    for c in range(1, 26):
        copy_style(sws.cell(row=header_rep, column=c), ows.cell(row=1, column=c))

    BONUS_COLS = [(7, "G"), (11, "K"), (15, "O"), (21, "U"), (25, "Y")]
    person_rows = []
    blocks = []
    cur = None
    parent_sub = None
    row = 2

    for orow in amount_rows:
        nm = orow[1]
        is_person = (nm is not None and nm != "小计")
        is_store = (nm == "小计")

        for c in range(1, 26):
            ows.cell(row=row, column=c, value=orow[c - 1])

        rep = data_rep if is_person else subtotal_rep
        for c in range(1, 26):
            copy_style(sws.cell(row=rep, column=c), ows.cell(row=row, column=c))

        dept_name = orow[0]
        if is_person:
            person_rows.append(row)
            if cur is None:
                cur = {"persons": [], "sub_row": None}
            cur["persons"].append(row)
        elif is_store:
            if dept_name == "美的特渠部":
                parent_sub = row
            else:
                cur["sub_row"] = row
                blocks.append(cur)
                cur = None
        row += 1

    # 公式：数据行（个人奖金基数 300）
    for r in person_rows:
        ows.cell(row=r, column=6, value=f"=IF(D{r}=0,0,E{r}/D{r})")   # 月度整体达成率
        ows.cell(row=r, column=10, value=f"=IF(H{r}=0,0,I{r}/H{r})")  # 第一成交率金额达成率
        ows.cell(row=r, column=14, value=f"=IF(L{r}=0,0,M{r}/L{r})")  # ABC成交金额达成率
        ows.cell(row=r, column=20, value=f"=IF(R{r}=0,0,S{r}/R{r})")  # ABC成交顾客数达成率
        ows.cell(row=r, column=24, value=f"=IF(V{r}=0,0,W{r}/V{r})")  # ABC线索新建达成率
        ows.cell(row=r, column=7, value=f"=IF(F{r}>=1,300,0)")
        ows.cell(row=r, column=11, value=f"=IF(J{r}>=1,300,0)")
        ows.cell(row=r, column=15, value=f"=IF(N{r}>=1,300,0)")
        ows.cell(row=r, column=21, value=f"=IF(T{r}>=1,300,0)")
        ows.cell(row=r, column=25, value=f"=IF(X{r}>=1,300,0)")
        ows.cell(row=r, column=3, value=f"=G{r}+K{r}+Y{r}+IF((O{r}+U{r})>=300,300,0)")

    # 公式：门店/渠道小计（月度整体基数 2000，其余 1000，ABC 合并阈值 1000）
    for b in blocks:
        sr = b["sub_row"]
        ows.cell(row=sr, column=6, value=f"=IF(D{sr}=0,0,E{sr}/D{sr})")
        ows.cell(row=sr, column=10, value=f"=IF(H{sr}=0,0,I{sr}/H{sr})")
        ows.cell(row=sr, column=14, value=f"=IF(L{sr}=0,0,M{sr}/L{sr})")
        ows.cell(row=sr, column=20, value=f"=IF(R{sr}=0,0,S{sr}/R{sr})")
        ows.cell(row=sr, column=24, value=f"=IF(V{sr}=0,0,W{sr}/V{sr})")
        ows.cell(row=sr, column=7, value=f"=IF(F{sr}>=1,2000,0)")
        ows.cell(row=sr, column=11, value=f"=IF(J{sr}>=1,1000,0)")
        ows.cell(row=sr, column=15, value=f"=IF(N{sr}>=1,1000,0)")
        ows.cell(row=sr, column=21, value=f"=IF(T{sr}>=1,1000,0)")
        ows.cell(row=sr, column=25, value=f"=IF(X{sr}>=1,1000,0)")
        ows.cell(row=sr, column=3, value=f"=G{sr}+K{sr}+Y{sr}+IF((O{sr}+U{sr})>=1000,1000,0)")

    # 公式：美的特渠部小计 同样使用小计口径
    if parent_sub:
        ows.cell(row=parent_sub, column=6, value=f"=IF(D{parent_sub}=0,0,E{parent_sub}/D{parent_sub})")
        ows.cell(row=parent_sub, column=10, value=f"=IF(H{parent_sub}=0,0,I{parent_sub}/H{parent_sub})")
        ows.cell(row=parent_sub, column=14, value=f"=IF(L{parent_sub}=0,0,M{parent_sub}/L{parent_sub})")
        ows.cell(row=parent_sub, column=20, value=f"=IF(R{parent_sub}=0,0,S{parent_sub}/R{parent_sub})")
        ows.cell(row=parent_sub, column=24, value=f"=IF(V{parent_sub}=0,0,W{parent_sub}/V{parent_sub})")
        ows.cell(row=parent_sub, column=7, value=f"=IF(F{parent_sub}>=1,2000,0)")
        ows.cell(row=parent_sub, column=11, value=f"=IF(J{parent_sub}>=1,1000,0)")
        ows.cell(row=parent_sub, column=15, value=f"=IF(N{parent_sub}>=1,1000,0)")
        ows.cell(row=parent_sub, column=21, value=f"=IF(T{parent_sub}>=1,1000,0)")
        ows.cell(row=parent_sub, column=25, value=f"=IF(X{parent_sub}>=1,1000,0)")
        ows.cell(row=parent_sub, column=3, value=f"=G{parent_sub}+K{parent_sub}+Y{parent_sub}+IF((O{parent_sub}+U{parent_sub})>=1000,1000,0)")

    # 数字格式统一（金额类 2 位小数，计数类整数，达成率保持百分比）
    AMOUNT_FMT = "#,##0.00"
    INT_FMT = "0"
    # C=3, D=4, E=5, G=7, H=8, I=9, K=11, L=12, M=13, O=15, Q=17, U=21, Y=25
    amount_cols = [3, 4, 5, 7, 8, 9, 11, 12, 13, 15, 17, 21, 25]
    # P=16, R=18, S=19, V=22, W=23
    int_cols = [16, 18, 19, 22, 23]
    for r in range(2, ows.max_row + 1):
        for c in amount_cols:
            ows.cell(row=r, column=c).number_format = AMOUNT_FMT
        for c in int_cols:
            ows.cell(row=r, column=c).number_format = INT_FMT

    # 列宽 / 冻结
    for col, dim in sws.column_dimensions.items():
        if dim.width:
            ows.column_dimensions[col].width = dim.width
    ows.freeze_panes = sws.freeze_panes
    sws.parent.close()

    swb.save(out_path)
    return out_path, person_rows, blocks, parent_sub


def main(base_path, template_path, out_path, report_month=8, personnel_path=None):
    persons = load_base_data(base_path)
    person_targets, subtotal_targets = load_target_table(template_path, report_month)
    missing = apply_targets_and_depts(persons, person_targets, report_month)

    amount_rows, all_persons = build_amount_rows(persons, subtotal_targets)
    out_path, person_rows, blocks, parent_sub = build_workbook(
        template_path, amount_rows, out_path, personnel_path
    )

    # ---- 自检 ----
    print(f"输入基础表: {base_path}")
    print(f"模板原表: {template_path}")
    print(f"输出: {out_path}")
    print(f"报表月份: {report_month}")
    print(f"人员数: {len(all_persons)} | 金额表数据行(含小计): {len(amount_rows)}")
    if missing:
        print(f"⚠️ 未匹配到目标表的人员: {missing}")
    else:
        print("✅ 所有人员均匹配到目标表")

    bad = 0
    for r in person_rows:
        nm = ows_value(out_path, r, 2)
        # 由于公式列 data_only 未被 Excel 计算过，直接读取指标列/完成列重新验算
        d = ows_value(out_path, r, 4)
        e = ows_value(out_path, r, 5)
        h = ows_value(out_path, r, 8)
        i = ows_value(out_path, r, 9)
        l = ows_value(out_path, r, 12)
        m = ows_value(out_path, r, 13)
        rr = ows_value(out_path, r, 18)
        s = ows_value(out_path, r, 19)
        v = ows_value(out_path, r, 22)
        w = ows_value(out_path, r, 23)

        def q(val):
            return val if isinstance(val, (int, float)) else 0

        f = q(e) / q(d) if q(d) else 0
        j = q(i) / q(h) if q(h) else 0
        n = q(m) / q(l) if q(l) else 0
        t = q(s) / q(rr) if q(rr) else 0
        x = q(w) / q(v) if q(v) else 0
        g = 300 if f >= 1 else 0
        k = 300 if j >= 1 else 0
        o = 300 if n >= 1 else 0
        u = 300 if t >= 1 else 0
        y = 300 if x >= 1 else 0
        c = g + k + y + (300 if (o + u) >= 300 else 0)
        # 找到对应人员口径奖金
        for p in all_persons:
            if p["name"] == nm:
                bb = compute_person_bonus(p)
                if c != bb[5]:
                    bad += 1
                    print(f"  ** 公式模拟与口径不符: {nm} 公式={c} 口径={bb[5]}")
                break
    print(f"公式模拟 vs 口径自检: {'全部一致' if bad == 0 else str(bad) + ' 行不符'}")
    return out_path


def ows_value(path, row, col):
    """读取已保存文件指定单元格的 data_only 值（用于自检）。"""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb.active
    v = ws.cell(row=row, column=col).value
    wb.close()
    return v


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else r"D:/Backup/Downloads/欣暖家员工考核绩效（全量总计）数值版_2026-08-24 13_11.xlsx"
    tmpl = sys.argv[2] if len(sys.argv) > 2 else r"D:/Backup/xwechat_files/wxid_xf22fbly6tho12_7f07/msg/file/2026-08/欣暖家员工考核绩效（全量总计）数值版_2026-08-19 13_00(1)(1).xlsx"
    out = sys.argv[3] if len(sys.argv) > 3 else r"C:/Users/Administrator/WorkBuddy/2026-08-07-09-18-03/欣暖家8月考核金额表_美化版_2026-08-28.xlsx"
    month = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    personnel = sys.argv[5] if len(sys.argv) > 5 else None
    main(base, tmpl, out, month, personnel)
