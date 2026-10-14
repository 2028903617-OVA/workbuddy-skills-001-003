# -*- coding: utf-8 -*-
"""
集团联单周报生成器 (group-co-order-report)

根据每周的"上周集团内部联单"Excel，生成符合规范的多工作表主文件、
按门店拆分的品牌子文件，以及按部门带单费汇总表。

用法:
    python generate_report.py \
        --src "D:/Backup/Downloads/上周集团内部联单_2026-07-15 14_12.xlsx" \
        --out "F:/集团联单数据/2026/7月/2026.07.06-07.12" \
        --week "2026.07.06-07.12" \
        [--ref "F:/集团联单数据/2026/4月/2026.04.13-04.19/集团联单明细2026.04.13-04.19.xlsx"] \
        [--remove-dajin]   # 临时去除大金公司数据

依赖: pandas, openpyxl
"""
import argparse
import os
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# === 默认参考文件 (含人员卡号370人 + 付款公司映射表) ===
DEFAULT_REF = r'F:/集团联单数据/2026/4月/2026.04.13-04.19/集团联单明细2026.04.13-04.19.xlsx'

# === 23列顺序 (前16列基础数据 → 姓名/银行卡号/开户行/付款公司 → 毛利+待回款) ===
COLS_23 = [
    '销售订单编号', '公司', '负责人主属部门', '负责人', '客户名称', '客户电话',
    '安装地址（老）', '销售订单金额(元)', '实际金额新', '内部员工主属品牌',
    '内部员工姓名', '现场管理/带单费', '内部员工带单提成系数', '带单类型', '客户来源',
    '确认时间', '姓名', '银行卡号', '开户行', '内部带单费付款公司',
    '销售结算毛利合计', '毛利合计', '待回款金额新'
]
# 19列 (去掉 姓名/银行卡号/开户行/付款公司, 第17-20位)
COLS_19 = COLS_23[:16] + COLS_23[20:]

# 金额列 (1-indexed)
MONEY_23 = [8, 9, 12, 13, 21, 22, 23]
SUM_23 = [8, 9, 12, 21, 22, 23]       # 内部员工带单提成系数(13) 不汇总
MONEY_19 = [8, 9, 12, 13, 17, 18, 19]
SUM_19 = [8, 9, 12, 17, 18, 19]

# 向后兼容别名
COLS_22 = COLS_23
COLS_18 = COLS_19
MONEY_22 = MONEY_23
SUM_22 = SUM_23
MONEY_18 = MONEY_19
SUM_18 = SUM_19

# L列 = 现场管理/带单费 = 第12列，小计/合计行仅此列标黄
L_COL = 12

# 品牌 Sheet 列表 (按公司列归类, 非内部员工主属品牌)
ALL_BRANDS = ['大金', '方太', '乾鑫', '西门子', '欣暖家', '启欣']

# 付款公司兜底规则: 参考表无该部门时，按公司列分配
PAY_FALLBACK = {
    '启欣': '杭州启欣智家电器有限公司',
    '乾鑫': '杭州乾鑫暖通设备工程有限公司',
    '方太': '杭州欣锋控股集团有限公司',
    '欣暖家': '杭州欣暖家节能科技有限公司',
    '西门子': '杭州欣锋控股集团有限公司',
}

# 不统计带单费的品牌: 内部员工主属品牌 属于这些值的整行直接删除
BRAND_EXCLUDE = ['泽锋']

# 带单费为0时按此系数重算 (仅限下列公司)
ZERO_FEE_RECALC_RATE = 0.01
ZERO_FEE_RECALC_COMPANIES = ['欣暖家']

# === 规则12: 待回款未收齐 → 本期暂不计提带单费 (全部公司) ===
UNPAID_COL = '待回款金额新'          # 第23列
FEE_COL = '现场管理/带单费'           # 第12列 (L列)
GROSS_COL = '毛利合计'               # 第22列, 毛利封顶判定用
STATUS_UNPAID = '待回款未收齐'        # 带单费暂按0处理, 待款收齐后补算
STATUS_CAP = '毛利不足已裁剪'         # 按毛利封顶发放
STATUS_MARGIN_NEG = '毛利≤0不发带单费'  # 合计毛利 ≤0, 整组不发
DEFERRED_FILL = PatternFill('solid', fgColor='FFC000')   # 橙色底 = 本期调整过带单费的行

# === 规则13: 拆单合并看合计毛利 (同一客户窗口内多单合并判定) ===
SPLIT_MERGE_COMPANIES = ['西门子']   # 需按客户合并看合计毛利的公司
MERGE_WINDOW_DAYS = 7                # 同客户订单日期相差 ≤N 天视为同一笔成交(拆单)


def read_source(src, ref):
    df = pd.read_excel(src)
    df.columns = [str(c).strip().strip("'") for c in df.columns]

    ref_xls = pd.ExcelFile(ref)
    card_df = ref_xls.parse('集团公司人员卡号')
    card_map = {}
    for _, r in card_df.iterrows():
        name = str(r['姓名']).strip()
        card_map[name] = (str(r.get('银行卡号', '')), str(r.get('开户行', '')))

    pay_df = ref_xls.parse('内部带单费付款公司汇总表')
    pay_map = {}
    for _, r in pay_df.iterrows():
        dept = str(r['门店']).strip()
        pay_map[dept] = str(r.get('带单费付款公司选择', ''))

    return df, card_map, pay_map


import re

# 组号后缀模式：匹配末尾的 "N组" / "第N组"（如 1组、2组、第1组、第2组）
_GROUP_SUFFIX_RE = re.compile(r'[第]?\d+组\s*$')


def _resolve_pay_company(dept, company, pay_map):
    """解析付款公司（严格两级 + 兜底），返回 (付款公司, 是否命中参考表)：

    1. 精确匹配参考表 pay_map（权威依据）
    2. 剥离 "N组"/"第N组" 后缀后再精确匹配
    3. 仍未命中 → 公司级兜底，hit=False，供汇总"待人工确认"清单
    """
    # 1) 精确匹配
    if dept in pay_map and pay_map[dept]:
        return pay_map[dept], True
    # 2) 剥离 "1组"/"2组"/"第1组" 等后缀，用基础部门名再查
    base = _GROUP_SUFFIX_RE.sub('', dept).strip()
    if base and base in pay_map and pay_map[base]:
        return pay_map[base], True
    # 3) 公司级兜底（未在参考表命中）
    return PAY_FALLBACK.get(company, ''), False


def fill_info(df, card_map, pay_map):
    """填充姓名/银行卡号/开户行/付款公司，打印匹配情况。"""
    df['姓名'] = ''
    df['银行卡号'] = ''
    df['开户行'] = ''
    df['内部带单费付款公司'] = ''
    df['_pay_hit'] = False   # 是否命中参考表（供过滤后汇总"待确认"清单）

    unmatched_card = []

    for i, r in df.iterrows():
        emp = str(r['内部员工姓名']).strip()
        dept = str(r['负责人主属部门']).strip()
        company = str(r['公司']).strip()
        if emp in card_map:
            df.at[i, '姓名'] = emp
            df.at[i, '银行卡号'] = card_map[emp][0]
            df.at[i, '开户行'] = card_map[emp][1]
        pay_company, hit = _resolve_pay_company(dept, company, pay_map)
        df.at[i, '内部带单费付款公司'] = pay_company
        df.at[i, '_pay_hit'] = bool(hit)

        status = 'OK' if (df.at[i, '银行卡号'] and df.at[i, '银行卡号'] != 'nan') else '未匹配'
        pay = df.at[i, '内部带单费付款公司']
        print(f"  {emp} | 卡号: {df.at[i, '银行卡号']} | 付款公司: {pay} | {status}")
        if status == '未匹配':
            unmatched_card.append(emp)

    if unmatched_card:
        print(f"\n⚠️ 未匹配银行卡号: {unmatched_card}")
    return df, unmatched_card


def recalc_zero_fee(df, companies=None, rate=None):
    """把指定公司里「现场管理/带单费」为 0 的行，按订单金额 × 系数重算带单费。

    同步把「内部员工带单提成系数」写成该系数，保持两列一致。
    只动命中行，其余行原值不变。返回 (df, 重算明细列表)。
    """
    if companies is None:
        companies = ZERO_FEE_RECALC_COMPANIES
    if rate is None:
        rate = ZERO_FEE_RECALC_RATE
    changed = []
    for i, r in df.iterrows():
        if str(r['公司']).strip() not in companies:
            continue
        try:
            fee = float(r['现场管理/带单费'])
        except (TypeError, ValueError):
            continue
        if fee != 0:
            continue
        try:
            amount = float(r['销售订单金额(元)'])
        except (TypeError, ValueError):
            print(f"  ⚠️ {r['销售订单编号']} 订单金额无法解析，跳过重算")
            continue
        df.at[i, '现场管理/带单费'] = round(amount * rate, 2)
        df.at[i, '内部员工带单提成系数'] = rate
        changed.append((r['销售订单编号'], str(r['公司']).strip(), amount, round(amount * rate, 2)))
    return df, changed


# === 规则12/13 工具 ===

# 订单编号形如 2026-09-29-147825，前 10 位即下单日期
_ORDER_DATE_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})')


def _order_date(order_no, confirm_time=None):
    """取订单日期: 优先用订单编号前缀(YYYY-MM-DD)，回退到确认时间。"""
    m = _ORDER_DATE_RE.match(str(order_no).strip())
    if m:
        try:
            return pd.Timestamp(f'{m.group(1)}-{m.group(2)}-{m.group(3)}')
        except Exception:
            pass
    try:
        ts = pd.Timestamp(confirm_time)
        return pd.NaT if pd.isna(ts) else ts.normalize()
    except Exception:
        return pd.NaT


def _num(v):
    """安全转 float，空值/异常一律返回 0.0。"""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if pd.isna(f) else f


def defer_unpaid_fee(df, unpaid_col=UNPAID_COL, fee_col=FEE_COL):
    """规则12: 待回款金额 ≠ 0 → 本期不计算带单费，置 0 并打标记。

    带单费原值另存到 _fee_orig，供"暂缓带单费清单"与后续补算使用。
    返回 (df, 暂缓明细列表)；明细元素为 dict。
    """
    df['_fee_status'] = ''
    df['_fee_orig'] = df[fee_col].apply(_num)
    rows = []
    for i, r in df.iterrows():
        unpaid = _num(r.get(unpaid_col))
        if round(unpaid, 2) == 0:
            continue
        orig = _num(r.get(fee_col))
        df.at[i, fee_col] = 0.0
        df.at[i, '_fee_status'] = STATUS_UNPAID
        rows.append({
            '销售订单编号': r.get('销售订单编号', ''),
            '公司': str(r.get('公司', '')).strip(),
            '负责人主属部门': r.get('负责人主属部门', ''),
            '负责人': r.get('负责人', ''),
            '客户名称': r.get('客户名称', ''),
            '待回款金额新': round(unpaid, 2),
            '原带单费': round(orig, 2),
            '调整后带单费': 0.0,
            '带单费状态': STATUS_UNPAID,
        })
    return df, rows


def apply_gross_margin_cap(df, companies=None, window_days=None,
                           gross_col=GROSS_COL, fee_col=FEE_COL):
    """规则13: 拆单合并看合计毛利，对带单费做封顶。

    同一公司 + 同一客户(名称+电话) + 订单日期相差 ≤ window_days 的多张订单，
    视为"一次成交被拆成多单"，按组合计毛利判定：
      · 合计毛利 ≤ 0            → 组内带单费全部置 0（不发）
      · 0 < 合计毛利 < 合计带单费 → 组内带单费按原比例分摊，总额封顶为合计毛利
      · 合计毛利 ≥ 合计带单费     → 正常发放，不改动
    返回 (df, 裁剪明细列表)。
    """
    if companies is None:
        companies = SPLIT_MERGE_COMPANIES
    if window_days is None:
        window_days = MERGE_WINDOW_DAYS
    changes = []
    for comp in companies:
        idx = df.index[df['公司'].astype(str).str.strip() == comp]
        if len(idx) == 0:
            continue
        sub = df.loc[idx].copy()
        sub['_od'] = [
            _order_date(r.get('销售订单编号'), r.get('确认时间'))
            for _, r in sub.iterrows()
        ]
        for key, g in sub.groupby(['客户名称', '客户电话'], sort=False, dropna=False):
            g = g.sort_values('_od', kind='mergesort')
            # 按日期聚类：相邻订单日期差 > window_days 即切开
            clusters, cur = [], []
            for _, r in g.iterrows():
                if cur and pd.notna(r['_od']) and pd.notna(cur[-1][1]) \
                        and (r['_od'] - cur[-1][1]).days > window_days:
                    clusters.append(cur)
                    cur = []
                cur.append((r.name, r['_od']))
            if cur:
                clusters.append(cur)

            for cl in clusters:
                ids = [c[0] for c in cl]
                gross = sum(_num(df.at[i, gross_col]) for i in ids)
                payable = [i for i in ids if _num(df.at[i, fee_col]) > 0]
                fee_total = sum(_num(df.at[i, fee_col]) for i in payable)
                if fee_total <= 0:
                    continue                       # 无可计提（已暂缓/原值即0）
                tag = f"{g['客户名称'].iloc[0]}"
                if gross <= 0:
                    for i in ids:
                        old = _num(df.at[i, fee_col])
                        if old == 0:
                            continue
                        df.at[i, fee_col] = 0.0
                        if df.at[i, '_fee_status'] == '':
                            df.at[i, '_fee_status'] = STATUS_MARGIN_NEG
                        changes.append({
                            '销售订单编号': df.at[i, '销售订单编号'],
                            '公司': comp, '客户名称': tag, '组单数': len(ids),
                            '合计毛利': round(gross, 2), '合计带单费': round(fee_total, 2),
                            '原带单费': round(old, 2), '调整后带单费': 0.0,
                            '带单费状态': STATUS_MARGIN_NEG,
                        })
                elif gross < fee_total:
                    done = 0.0
                    for n, i in enumerate(payable):
                        old = _num(df.at[i, fee_col])
                        if n == len(payable) - 1:
                            new = round(gross - done, 2)       # 末行兜差，保证总额=合计毛利
                        else:
                            new = round(gross * old / fee_total, 2)
                            done += new
                        df.at[i, fee_col] = new
                        if df.at[i, '_fee_status'] == '':
                            df.at[i, '_fee_status'] = STATUS_CAP
                        changes.append({
                            '销售订单编号': df.at[i, '销售订单编号'],
                            '公司': comp, '客户名称': tag, '组单数': len(ids),
                            '合计毛利': round(gross, 2), '合计带单费': round(fee_total, 2),
                            '原带单费': round(old, 2), '调整后带单费': new,
                            '带单费状态': STATUS_CAP,
                        })
    return df, changes


# === 格式工具 ===
HEADER_FONT = Font(name='Arial', bold=True, color='FFFFFF', size=10)
HEADER_FILL = PatternFill('solid', fgColor='4472C4')
SUMMARY_FILL = PatternFill('solid', fgColor='FFFF00')
SUMMARY_FONT = Font(name='Arial', bold=True, size=10)
NORMAL_FONT = Font(name='Arial', size=10)
THIN_BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
CENTER_ALIGN = Alignment(horizontal='center', vertical='center', wrap_text=True)


def format_sheet(ws, ncols, money_indices, has_summary=True, sum_indices=None):
    if sum_indices is None:
        sum_indices = money_indices
    for col_idx in range(1, ncols + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
        col_letter = get_column_letter(col_idx)
        max_w = len(str(cell.value or '')) * 2 + 4
        for row in range(2, ws.max_row + 1):
            c = ws.cell(row=row, column=col_idx)
            c.font = NORMAL_FONT
            c.border = THIN_BORDER
            c.alignment = Alignment(vertical='center', wrap_text=True)
            val_len = len(str(c.value or '')) * 1.2 + 4
            max_w = max(max_w, val_len)
        ws.column_dimensions[col_letter].width = min(max_w, 40)
        if col_idx in money_indices:
            for row in range(2, ws.max_row + 1):
                c = ws.cell(row=row, column=col_idx)
                if c.value is not None and c.value != '':
                    try:
                        float(c.value)
                        c.number_format = '#,##0.00'
                    except Exception:
                        pass

    if has_summary:
        sr = ws.max_row
        for col_idx in range(1, ncols + 1):
            c = ws.cell(row=sr, column=col_idx)
            c.font = SUMMARY_FONT
            if col_idx == L_COL:                       # 仅L列标黄
                c.fill = SUMMARY_FILL
            if col_idx in sum_indices:
                col_l = get_column_letter(col_idx)
                c.value = f'=SUM({col_l}2:{col_l}{sr-1})'
                c.number_format = '#,##0.00'
        ws.cell(row=sr, column=1).value = '合计'


def paint_fee_flags(ws, pairs, status_map):
    """把本期调整过带单费的行，在 L列(现场管理/带单费) 涂橙色底。

    pairs: [(工作表行号, 销售订单编号), ...]
    """
    if not status_map:
        return
    for row_no, order_no in pairs:
        if status_map.get(str(order_no).strip()):
            ws.cell(row=row_no, column=L_COL).fill = DEFERRED_FILL


def write_df_to_sheet(ws, df_data, cols, money_indices, has_summary=True, sum_indices=None,
                      status_map=None):
    for ci, col_name in enumerate(cols, 1):
        ws.cell(row=1, column=ci, value=col_name)
    pairs = []
    for ri, (_, row) in enumerate(df_data.iterrows()):
        for ci, col_name in enumerate(cols, 1):
            val = row.get(col_name, '')
            if pd.isna(val):
                val = ''
            ws.cell(row=ri + 2, column=ci, value=val)
        pairs.append((ri + 2, row.get('销售订单编号', '')))
    if has_summary and len(df_data) > 0:
        if sum_indices is None:
            sum_indices = money_indices
        sr = len(df_data) + 2
        for ci in range(1, len(cols) + 1):
            if ci in sum_indices:
                cl = get_column_letter(ci)
                ws.cell(row=sr, column=ci, value=f'=SUM({cl}2:{cl}{sr-1})')
        ws.cell(row=sr, column=1, value='合计')
    format_sheet(ws, len(cols), money_indices, has_summary and len(df_data) > 0, sum_indices)
    paint_fee_flags(ws, pairs, status_map)


def write_subfile_with_subtotals(ws, df_data, cols, money_indices, sum_indices,
                                 group_col='负责人主属部门', status_map=None):
    """品牌子文件: 多部门时按部门加'小计'行 + 末尾'合计'行；单部门仅'合计'行。
    小计/合计行仅 L列(现场管理/带单费) 标黄，其余列只加粗不加底色。
    本期调整过带单费的数据行，L列涂橙色底（status_map 非空时）。"""
    ncols = len(cols)
    for ci, col_name in enumerate(cols, 1):
        ws.cell(row=1, column=ci, value=col_name)

    current_row = 2
    subtotal_rows = []
    pairs = []
    n_depts = df_data[group_col].nunique() if len(df_data) > 0 else 0

    if n_depts <= 1:
        for ri, (_, row) in enumerate(df_data.iterrows()):
            for ci, col_name in enumerate(cols, 1):
                val = row.get(col_name, '')
                if pd.isna(val):
                    val = ''
                ws.cell(row=ri + 2, column=ci, value=val)
            pairs.append((ri + 2, row.get('销售订单编号', '')))
        if len(df_data) > 0:
            sr = len(df_data) + 2
            for ci in sum_indices:
                cl = get_column_letter(ci)
                ws.cell(row=sr, column=ci, value=f'=SUM({cl}2:{cl}{sr-1})')
            ws.cell(row=sr, column=1, value='合计')
        format_sheet(ws, ncols, money_indices, len(df_data) > 0, sum_indices)
        paint_fee_flags(ws, pairs, status_map)
        return

    for dept, group_df in df_data.groupby(group_col, sort=False):
        group_start = current_row
        for _, row in group_df.iterrows():
            for ci, col_name in enumerate(cols, 1):
                val = row.get(col_name, '')
                if pd.isna(val):
                    val = ''
                ws.cell(row=current_row, column=ci, value=val)
            pairs.append((current_row, row.get('销售订单编号', '')))
            current_row += 1
        group_end = current_row - 1
        ws.cell(row=current_row, column=1, value=f'{dept} 小计')
        for ci in sum_indices:
            cl = get_column_letter(ci)
            ws.cell(row=current_row, column=ci,
                    value=f'=SUM({cl}{group_start}:{cl}{group_end})')
            ws.cell(row=current_row, column=ci).number_format = '#,##0.00'
        subtotal_rows.append(current_row)
        current_row += 1

    grand_total_row = current_row
    ws.cell(row=grand_total_row, column=1, value='合计')
    for ci in sum_indices:
        cl = get_column_letter(ci)
        formula = '=' + '+'.join([f'{cl}{r}' for r in subtotal_rows])
        ws.cell(row=grand_total_row, column=ci, value=formula)
        ws.cell(row=grand_total_row, column=ci).number_format = '#,##0.00'

    # 统一格式 (表头蓝底白字, 框线, 金额千分位)
    for col_idx in range(1, ncols + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
        col_letter = get_column_letter(col_idx)
        max_w = len(str(cell.value or '')) * 2 + 4
        for row in range(2, grand_total_row + 1):
            c = ws.cell(row=row, column=col_idx)
            c.font = NORMAL_FONT
            c.border = THIN_BORDER
            c.alignment = Alignment(vertical='center', wrap_text=True)
            val_len = len(str(c.value or '')) * 1.2 + 4
            max_w = max(max_w, val_len)
        ws.column_dimensions[col_letter].width = min(max_w, 40)
        if col_idx in money_indices:
            for row in range(2, grand_total_row + 1):
                c = ws.cell(row=row, column=col_idx)
                if c.value is not None and c.value != '' and not str(c.value).startswith('='):
                    try:
                        float(c.value)
                        c.number_format = '#,##0.00'
                    except Exception:
                        pass

    # 仅 L列(现场管理/带单费) 标黄 + 加粗
    for sr in subtotal_rows + [grand_total_row]:
        for col_idx in range(1, ncols + 1):
            c = ws.cell(row=sr, column=col_idx)
            c.font = SUMMARY_FONT
            if col_idx == L_COL:
                c.fill = SUMMARY_FILL
    # 本期调整过带单费的数据行 → L列橙色底
    paint_fee_flags(ws, pairs, status_map)


def get_subfile_name(company, dept, pay_map):
    pmt = pay_map.get(dept, '')
    if '乾鑫' in pmt:
        suffix = '乾鑫'
    elif '智好' in pmt:
        suffix = '智好'
    elif '智德' in pmt:
        suffix = '智德'
    elif '欣锋' in pmt or '欣锋控股' in pmt:
        suffix = '欣锋'
    elif '启欣' in pmt:
        suffix = '启欣'
    else:
        suffix = company
    if company in suffix or suffix in company:
        label = company
    else:
        label = f'{company}（{suffix}）'
    return f'集团联单明细{WEEK_LABEL} - {label}.xlsx'


# 清单表列定义（不改主表列结构，调整明细单独成表）
ADJUST_COLS_DEFER = ['销售订单编号', '公司', '负责人主属部门', '负责人', '客户名称',
                     '待回款金额新', '原带单费', '调整后带单费', '带单费状态']
ADJUST_COLS_CAP = ['销售订单编号', '公司', '客户名称', '组单数',
                   '合计毛利', '合计带单费', '原带单费', '调整后带单费', '带单费状态']


def write_adjust_sheet(wb, title, cols, rows):
    """写带单费调整清单（暂缓/毛利封顶），状态列涂橙色底。"""
    ws = wb.create_sheet(title)
    for ci, h in enumerate(cols, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.font = HEADER_FONT
        c.fill = HEADER_FILL
        c.border = THIN_BORDER
        c.alignment = CENTER_ALIGN
    money_cols = {'待回款金额新', '合计毛利', '合计带单费', '原带单费', '调整后带单费'}
    for ri, r in enumerate(rows):
        for ci, h in enumerate(cols, 1):
            v = r.get(h, '')
            cell = ws.cell(row=ri + 2, column=ci, value=v)
            cell.font = NORMAL_FONT
            cell.border = THIN_BORDER
            if h in money_cols and isinstance(v, (int, float)):
                cell.number_format = '#,##0.00'
    if '带单费状态' in cols:
        st_ci = cols.index('带单费状态') + 1
        for ri in range(len(rows)):
            ws.cell(row=ri + 2, column=st_ci).fill = DEFERRED_FILL
    widths = {'销售订单编号': 22, '公司': 10, '负责人主属部门': 26, '负责人': 10,
              '客户名称': 28, '组单数': 8, '待回款金额新': 14, '合计毛利': 12,
              '合计带单费': 12, '原带单费': 12, '调整后带单费': 14, '带单费状态': 18}
    for ci, h in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(ci)].width = widths.get(h, 14)
    return ws


# === 待回款跟踪清单（跨周提醒：待回款≠0 暂缓的订单，款收齐后再补算带单费）===
TRACKING_LIST = r'F:/集团联单数据/带单费待回款跟踪清单.xlsx'
TRACKING_COLS = ['销售订单编号', '公司', '负责人主属部门', '负责人', '客户名称',
                 '待回款金额', '原带单费', '首次标记周', '状态', '备注']


def _load_tracking():
    """读跟踪清单；不存在或异常则返回空表。"""
    if not os.path.exists(TRACKING_LIST):
        return pd.DataFrame(columns=TRACKING_COLS)
    try:
        t = pd.read_excel(TRACKING_LIST, dtype={'销售订单编号': str})
        t.columns = [str(c).strip() for c in t.columns]
        for c in TRACKING_COLS:
            if c not in t.columns:
                t[c] = ''
        return t[TRACKING_COLS]
    except Exception:
        return pd.DataFrame(columns=TRACKING_COLS)


def manage_tracking(df, deferred_rows, week_label):
    """维护《带单费待回款跟踪清单》并在运行时提醒：

    1) 已有跟踪项：本期待回款已归 0 → 标 '已全款-待补算'（提醒补算带单费）；否则提醒仍待回款；
    2) 本周新暂缓订单 → upsert 进清单（状态 '待核查全款'）；
    3) 打印提醒清单，供用户核查后补算带单费。
    """
    t = _load_tracking()

    unpaid_now = {}
    for _, r in df.iterrows():
        oid = str(r['销售订单编号']).strip()
        v = pd.to_numeric(r.get('待回款金额新'), errors='coerce')
        unpaid_now[oid] = 0.0 if pd.isna(v) else float(v)

    reminders = []
    for i in t.index:
        if str(t.at[i, '状态']).startswith('已完成'):
            continue
        oid = str(t.at[i, '销售订单编号']).strip()
        if oid in unpaid_now and unpaid_now[oid] == 0:
            if not str(t.at[i, '状态']).startswith('已全款'):
                t.at[i, '状态'] = '已全款-待补算'
                t.at[i, '备注'] = f'{week_label} 已全款，可补算带单费'
            reminders.append((oid, '已全款'))
        else:
            reminders.append((oid, '仍待回款'))

    exist = set(t['销售订单编号'].astype(str).str.strip()) if len(t) else set()
    for r in deferred_rows:
        oid = str(r['销售订单编号']).strip()
        if oid in exist:
            continue
        t = pd.concat([t, pd.DataFrame([{
            '销售订单编号': oid, '公司': r['公司'],
            '负责人主属部门': r['负责人主属部门'], '负责人': r.get('负责人', ''),
            '客户名称': r['客户名称'],
            '待回款金额': r['待回款金额新'], '原带单费': r['原带单费'],
            '首次标记周': week_label, '状态': '待核查全款', '备注': '',
        }])], ignore_index=True)
        exist.add(oid)

    os.makedirs(os.path.dirname(TRACKING_LIST), exist_ok=True)
    t.to_excel(TRACKING_LIST, index=False)

    if reminders:
        print(f"\n{'='*64}")
        print(f"⏰ 待回款跟踪提醒（《带单费待回款跟踪清单》共 {len(reminders)} 单）：")
        for oid, st in reminders:
            row = t[t['销售订单编号'].astype(str).str.strip() == oid]
            r = row.iloc[0] if len(row) else None
            tail = '✅ 已全款 → 请补算带单费' if st == '已全款' else '⏳ 仍有待回款，继续暂缓'
            if r is not None:
                print(f"   - {oid} | {r['公司']} | {r['客户名称']} | "
                      f"待回款 {r['待回款金额']} | {tail}")
        print(f"{'='*64}")
    return t


def build(src, out_dir, week_label, ref=DEFAULT_REF, remove_dajin=False):
    global WEEK_LABEL
    WEEK_LABEL = week_label
    os.makedirs(out_dir, exist_ok=True)

    df, card_map, pay_map = read_source(src, ref)
    print(f'原始数据: {len(df)} 条')
    print('公司分布:', df['公司'].value_counts().to_dict())
    print('负责人主属部门:', df['负责人主属部门'].value_counts().to_dict())
    print('\n=== 银行信息匹配情况 ===')
    df, unmatched = fill_info(df, card_map, pay_map)

    if remove_dajin:
        removed = df[df['公司'] == '大金']
        df = df[df['公司'] != '大金'].copy()
        print(f'\n已过滤大金数据 {len(removed)} 条，剩余 {len(df)} 条')

    # 剔除不统计带单费的品牌 (内部员工主属品牌 命中 BRAND_EXCLUDE)
    if BRAND_EXCLUDE:
        mask = df['内部员工主属品牌'].astype(str).str.strip().isin(BRAND_EXCLUDE)
        removed_brand = df[mask]
        if len(removed_brand) > 0:
            print(f'\n已剔除不统计带单费品牌({BRAND_EXCLUDE}) {len(removed_brand)} 条:')
            for _, r in removed_brand.iterrows():
                print(f"  - {r['内部员工姓名']} | {r['公司']} | {r['负责人主属部门']} | 品牌={r['内部员工主属品牌']}")
        df = df[~mask].copy()
        print(f'剔除后剩余 {len(df)} 条')

    # 剔除实际金额为0的行（不统计）
    _amt = pd.to_numeric(df['实际金额新'], errors='coerce').fillna(0)
    mask_zero_amt = _amt == 0
    removed_zero_amt = df[mask_zero_amt]
    if len(removed_zero_amt) > 0:
        print(f'\n已剔除实际金额为0 {len(removed_zero_amt)} 条（不统计）:')
        for _, r in removed_zero_amt.iterrows():
            print(f"  - {r['内部员工姓名']} | {r['公司']} | {r['负责人主属部门']} | 实际金额={r['实际金额新']}")
    df = df[~mask_zero_amt].copy()
    print(f'剔除后剩余 {len(df)} 条')

    # 指定公司里带单费为0的行，按订单金额 × 系数重算
    df, recalc_rows = recalc_zero_fee(df)
    if recalc_rows:
        print(f'\n已按 {ZERO_FEE_RECALC_RATE:.0%} 重算带单费({ZERO_FEE_RECALC_COMPANIES}) {len(recalc_rows)} 条:')
        for oid, comp, amt, new_fee in recalc_rows:
            print(f"  - {oid} | {comp} | 订单金额 {amt:,.2f} × {ZERO_FEE_RECALC_RATE:.0%} = {new_fee:,.2f}")

    # 规则12: 待回款金额 ≠ 0 → 本期不计算带单费（暂缓，待款收齐后补算）
    df, deferred_rows = defer_unpaid_fee(df)
    if deferred_rows:
        print(f'\n{"="*64}')
        print(f'⏸️ 待回款金额≠0，本期暂不计提带单费 {len(deferred_rows)} 条（款收齐后补算）:')
        for r in deferred_rows:
            print(f"   - {r['销售订单编号']} | {r['公司']} | {r['负责人主属部门']} | "
                  f"{r['客户名称']} | 待回款 {r['待回款金额新']:,.2f} | 原带单费 {r['原带单费']:,.2f} → 0")
        print(f'{"="*64}')

    # 规则13: 拆单合并，看合计毛利对带单费封顶
    df, cap_rows = apply_gross_margin_cap(df)
    if cap_rows:
        print(f'\n{"="*64}')
        print(f'✂️ 合计毛利不足，带单费已按毛利封顶 {len(cap_rows)} 条:')
        for r in cap_rows:
            print(f"   - {r['销售订单编号']} | {r['公司']} | {r['客户名称']} | {r['组单数']}单 | "
                  f"合计毛利 {r['合计毛利']:,.2f} vs 合计带单费 {r['合计带单费']:,.2f} | "
                  f"带单费 {r['原带单费']:,.2f} → {r['调整后带单费']:,.2f} | {r['带单费状态']}")
        print(f'{"="*64}')

    # 本期调整过带单费的行（橙色底标记用）
    status_map = {str(r['销售订单编号']).strip(): str(r['_fee_status'])
                  for _, r in df.iterrows() if str(r['_fee_status']).strip()}

    # 排序: 公司 → 负责人主属部门
    df_sorted = df.sort_values(['公司', '负责人主属部门']).reset_index(drop=True)

    # 未命中参考表的部门（仅统计最终保留的行，供人工确认）
    miss_df = df_sorted[~df_sorted['_pay_hit'].astype(bool)]
    if len(miss_df) > 0:
        print(f"\n{'='*64}")
        print(f"⚠️ 以下部门在参考表(内部带单费付款公司汇总表)未命中，已按公司兜底 —— 请确认：")
        for d in miss_df['负责人主属部门'].unique():
            row = miss_df[miss_df['负责人主属部门'] == d].iloc[0]
            print(f"   - 部门: {d} | 公司: {row['公司']} | 已填付款公司: {row['内部带单费付款公司']}")
        print(f"{'='*64}")

    # 待回款跟踪清单（跨周提醒：核查是否全款，全款后补算带单费）
    manage_tracking(df_sorted, deferred_rows, week_label)

    # === 主文件 ===
    wb = Workbook()
    wb.remove(wb.active)

    ws1 = wb.create_sheet('销售订单数据')
    write_df_to_sheet(ws1, df_sorted, COLS_18, MONEY_18, sum_indices=SUM_18,
                      status_map=status_map)

    ws2 = wb.create_sheet('集团互联销售明细')
    write_df_to_sheet(ws2, df_sorted, COLS_22, MONEY_22, sum_indices=SUM_22,
                      status_map=status_map)

    brands = [b for b in ALL_BRANDS if not (remove_dajin and b == '大金')]
    for brand in brands:
        ws_brand = wb.create_sheet(brand)
        brand_df = df_sorted[df_sorted['公司'] == brand].copy()
        write_df_to_sheet(ws_brand, brand_df, COLS_22, MONEY_22, sum_indices=SUM_22,
                          status_map=status_map)

    # 人员卡号 sheet
    card_df = pd.read_excel(ref, sheet_name='集团公司人员卡号')
    ws9 = wb.create_sheet('集团公司人员卡号')
    for ci, h in enumerate(['序号', '姓名', '银行卡号', '开户行'], 1):
        ws9.cell(row=1, column=ci, value=h)
        ws9.cell(row=1, column=ci).font = HEADER_FONT
        ws9.cell(row=1, column=ci).fill = HEADER_FILL
        ws9.cell(row=1, column=ci).border = THIN_BORDER
        ws9.cell(row=1, column=ci).alignment = CENTER_ALIGN
    for ri, (_, r) in enumerate(card_df.iterrows()):
        ws9.cell(row=ri + 2, column=1, value=ri + 1)
        ws9.cell(row=ri + 2, column=2, value=r['姓名'])
        ws9.cell(row=ri + 2, column=3, value=r.get('银行卡号', ''))
        ws9.cell(row=ri + 2, column=4, value=r.get('开户行', ''))
        for c in range(1, 5):
            ws9.cell(row=ri + 2, column=c).font = NORMAL_FONT
            ws9.cell(row=ri + 2, column=c).border = THIN_BORDER
    for ci, w in zip(range(1, 5), [6, 12, 24, 10]):
        ws9.column_dimensions[get_column_letter(ci)].width = w

    # 付款公司汇总表 sheet
    pay_df = pd.read_excel(ref, sheet_name='内部带单费付款公司汇总表')
    ws10 = wb.create_sheet('内部带单费付款公司汇总表')
    for ci, h in enumerate(['门店', '带单费付款公司选择'], 1):
        ws10.cell(row=1, column=ci, value=h)
        ws10.cell(row=1, column=ci).font = HEADER_FONT
        ws10.cell(row=1, column=ci).fill = HEADER_FILL
        ws10.cell(row=1, column=ci).border = THIN_BORDER
        ws10.cell(row=1, column=ci).alignment = CENTER_ALIGN
    for ri, (_, r) in enumerate(pay_df.iterrows()):
        ws10.cell(row=ri + 2, column=1, value=r['门店'])
        ws10.cell(row=ri + 2, column=2, value=r.get('带单费付款公司选择', ''))
        for ci in range(1, 3):
            ws10.cell(row=ri + 2, column=ci).font = NORMAL_FONT
            ws10.cell(row=ri + 2, column=ci).border = THIN_BORDER
    ws10.column_dimensions['A'].width = 28
    ws10.column_dimensions['B'].width = 32

    # 带单费调整清单（不改主表列结构，调整明细单独成表）
    if deferred_rows:
        write_adjust_sheet(wb, '暂缓带单费清单', ADJUST_COLS_DEFER, deferred_rows)
    if cap_rows:
        write_adjust_sheet(wb, '毛利封顶调整清单', ADJUST_COLS_CAP, cap_rows)

    main_path = f'{out_dir}/集团联单明细{week_label}.xlsx'
    wb.save(main_path)
    print(f'\nSaved main: {main_path}')

    # === 品牌子文件 (按 公司+部门 拆分, 含部门小计) ===
    sub_groups = {}
    for _, r in df_sorted.iterrows():
        key = (str(r['公司']).strip(), str(r['负责人主属部门']).strip())
        sub_groups.setdefault(key, []).append(r)

    sub_by_name = {}
    for (company, dept), records in sub_groups.items():
        sub_name = get_subfile_name(company, dept, pay_map)
        sub_by_name.setdefault(sub_name, []).extend(records)

    for sub_name, records in sub_by_name.items():
        sub_df = pd.DataFrame(records).reset_index(drop=True)
        sub_path = f'{out_dir}/{sub_name}'
        sub_wb = Workbook()
        sub_ws = sub_wb.active
        sub_ws.title = 'Sheet1'
        write_subfile_with_subtotals(sub_ws, sub_df, COLS_22, MONEY_22, sum_indices=SUM_22,
                                     status_map=status_map)
        sub_wb.save(sub_path)
        print(f'Sub-file: {sub_name} ({len(sub_df)} 条)')

    # === 按部门带单费汇总 ===
    print('\n=== 带单费按部门汇总 ===')
    dept_sum = df_sorted.groupby('负责人主属部门').agg(
        记录数=('销售订单编号', 'count'),
        带单费合计=('现场管理/带单费', 'sum'),
        实际金额合计=('实际金额新', 'sum'),
        毛利合计=('毛利合计', 'sum')
    ).reset_index()
    print(dept_sum.to_string())

    dept_wb = Workbook()
    dept_ws = dept_wb.active
    dept_ws.title = '带单费按部门汇总'
    dept_cols = ['负责人主属部门', '记录数', '实际金额合计', '带单费合计', '毛利合计']
    dept_money = [3, 4, 5]
    for ci, h in enumerate(dept_cols, 1):
        dept_ws.cell(row=1, column=ci, value=h)
        dept_ws.cell(row=1, column=ci).font = HEADER_FONT
        dept_ws.cell(row=1, column=ci).fill = HEADER_FILL
        dept_ws.cell(row=1, column=ci).border = THIN_BORDER
        dept_ws.cell(row=1, column=ci).alignment = CENTER_ALIGN
    dept_sorted = dept_sum.sort_values('带单费合计', ascending=False).reset_index(drop=True)
    for ri, (_, r) in enumerate(dept_sorted.iterrows()):
        for ci, c in enumerate(dept_cols, 1):
            dept_ws.cell(row=ri + 2, column=ci, value=r[c])
    tr = len(dept_sorted) + 2
    dept_ws.cell(row=tr, column=1, value='合计')
    for ci in dept_money:
        cl = get_column_letter(ci)
        dept_ws.cell(row=tr, column=ci, value=f'=SUM({cl}2:{cl}{tr-1})')
    format_sheet(dept_ws, len(dept_cols), dept_money, has_summary=True)
    for ci, w in zip(range(1, 6), [30, 8, 16, 14, 12]):
        dept_ws.column_dimensions[get_column_letter(ci)].width = w
    dept_path = f'{out_dir}/带单费汇总_按部门_{week_label}.xlsx'
    dept_wb.save(dept_path)
    print(f'\nSaved dept summary: {dept_path}')
    if deferred_rows:
        tot = sum(r['原带单费'] for r in deferred_rows)
        print(f'\n⏸️ 暂缓计提带单费 {len(deferred_rows)} 条，涉及金额 {tot:,.2f} 元 —— '
              f'待回款收齐后再补算（已列入主文件《暂缓带单费清单》）')
    if cap_rows:
        cut = sum(r['原带单费'] - r['调整后带单费'] for r in cap_rows)
        print(f'✂️ 毛利封顶裁剪 {len(cap_rows)} 条，减少带单费 {cut:,.2f} 元 '
              f'（已列入主文件《毛利封顶调整清单》）')
    print(f'\n⚠️ 需手动补填银行卡号: {unmatched}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='集团联单周报生成器')
    parser.add_argument('--src', required=True, help='源Excel路径')
    parser.add_argument('--out', required=True, help='输出目录')
    parser.add_argument('--week', required=True, help='周标签, 如 2026.07.06-07.12')
    parser.add_argument('--ref', default=DEFAULT_REF, help='参考文件(含卡号/付款公司映射)')
    parser.add_argument('--remove-dajin', action='store_true', help='临时去除大金公司数据')
    args = parser.parse_args()
    build(args.src, args.out, args.week, args.ref, args.remove_dajin)
