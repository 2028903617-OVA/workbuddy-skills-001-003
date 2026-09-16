#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""价目表明细导入文件生成器。

把品牌价目表源表转成纷享销客「价目表明细」新建（12列）与更新（8列）导入文件，
并产出产品核对清单。只读写本地 xlsx，不联网、不调子进程。

用法:
  python build_import.py --source <源表.xlsx> [--brand 西门子]
      [--product-snapshot <产品快照.xlsx>] [--detail-snapshot <明细快照.xlsx>]
      [--outdir <输出目录>] [--downloads <Downloads目录>] [--keep-desc]

输出:
  <outdir>/{品牌}_新建价目表明细_{YYYYMMDD}.xlsx
  <outdir>/{品牌}_更新价目表明细_{YYYYMMDD}.xlsx   (有重复行才生成)
  <outdir>/{品牌}_产品核对清单_{YYYYMMDD}.xlsx      (有警示项才生成)
  stdout 摘要 JSON
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

NEW_COLS = ["成本价", "销售结算价", "品牌负责人审核价", "品牌", "产品大类", "产品品项",
            "产品等级", "价目表折扣（%）", "产品（必填）", "价目表售价", "价目表（必填）",
            "业务类型（必填）"]
NEW_DESC = ["金额字段类型,最大位数14,小数位数2\n123", "金额字段类型,最大位数14,小数位数2\n123",
            "金额字段类型,最大位数14,小数位数2\n123", "单行文本字段类型,最大字符数100\n示例文本",
            "空调", "冰箱", "A类", "百分数字段类型,小数位数2\n12.66",
            "此项必填,查找关联字段类型\n关联对象主属性", "金额字段类型,最大位数14,小数位数2\n123",
            "此项必填,主从关系字段类型\n主对象主属性", ""]
UPD_COLS = ["唯一性ID（必填）", "价目表明细编号", "成本价", "销售结算价", "品牌负责人审核价",
            "价目表售价", "价目表_唯一性ID（必填）", "价目表（必填）"]
UPD_DESC = ["此项必填\n请填入 唯一性ID", "自增编号字段类型\n示例文本",
            "金额字段类型,最大位数14,小数位数2\n123", "金额字段类型,最大位数14,小数位数2\n123",
            "金额字段类型,最大位数14,小数位数2\n123", "金额字段类型,最大位数14,小数位数2\n123",
            "此项必填\n示例文本", "此项必填,主从关系字段类型\n主对象主属性"]

# 组织(org) → 价目表。组织决定「价目表」列，与产品实际品牌无关。
# 例：欣暖家组织 → 美的价目表；乾鑫组织 → 乾鑫价目表（该表内可含大金/美的等品牌产品）。
ORG_PRICEBOOKS = {
    "乾鑫": "乾鑫价目表20260701", "西门子": "西门子价目表20260701",
    "怡口": "怡口价目表20250530", "方太": "方太价目表20260601",
    "鸿格": "鸿格价目表20250406", "工单结算": "工单结算表20260301",
    "启欣": "启欣价目表20260401", "大金": "大金价目表20260601",
    "能率": "能率价目表20250701", "云格": "云格20220801604864",
    "美的": "美的价目表20250901", "约克": "约克价目表20250301",
    "欣暖家": "美的价目表20250901",
}
PRICEBOOKS = ORG_PRICEBOOKS  # 向后兼容旧名

FIELD_VARIANTS = {
    "model": ["产品官方名称及型号", "产品（必填）", "产品", "型号规格"],
    "price": ["零售建议价", "零售价", "价目表售价"],
    "limit": ["零售限制价", "销售限制价", "（浮动下限价）品牌负责人审核价", "品牌负责人审核价"],
    "settle": ["销售结算价"],
    "cost": ["实际成本价", "成本价"],
    "note": ["备注"],
    "brand": ["品牌"],
    "pclass": ["产品大类"],
    "pitem": ["产品品项"],
}

# 分类关键词表: 关键词 -> (西门子: 大类列/品项列, 通用: 大类列/品项列)
KEYWORDS = [
    ("微蒸烤", ("微蒸烤【西门子品项】", "微蒸烤箱【西门子大类】"), ("", "蒸烤微一体机")),
    ("蒸烤一体", ("", ""), ("", "蒸烤一体机")),
    ("蒸烤微", ("微蒸烤【西门子品项】", "微蒸烤箱【西门子大类】"), ("", "蒸烤微一体机")),
    ("洗碗机", ("洗碗机【西门子品项】", ""), ("厨电", "洗碗机")),
    ("洗干一体", ("洗干一体机【西门子品项】", ""), ("厨电", "洗碗机")),
    ("洗衣機", ("", ""), ("", "")),
    ("洗衣机", ("洗衣机【西门子品项】", "洗衣机【西门子大类】"), ("", "")),
    ("干衣机", ("干衣机【西门子品项】", "干衣机【西门子大类】"), ("", "")),
    ("嵌入式冰箱", ("嵌入式冰箱【西门子品项】", ""), ("", "冰箱")),
    ("独立式冰箱", ("独立式冰箱【西门子品项】", ""), ("", "冰箱")),
    ("冰箱", ("独立式冰箱【西门子品项】", ""), ("", "冰箱")),
    ("酒柜", ("独立式酒柜【西门子品项】", "酒柜【西门子大类】"), ("", "")),
    ("咖啡机", ("独立式咖啡机【西门子品项】", "咖啡机【西门子大类】"), ("", "")),
    ("抽屉", ("嵌入式抽屉【西门子品项】", "抽屉【西门子大类】"), ("", "")),
    ("面板", ("", "面板【西门子大类】"), ("", "")),
    ("嵌饮机", ("嵌入式饮水机【西门子品项】", "嵌饮机【西门子大类】"), ("", "")),
    ("油烟机", ("油烟机【西门子品项】", ""), ("厨电", "油烟机")),
    ("烟机", ("", ""), ("厨电", "烟机")),
    ("灶具", ("灶具【西门子品项】", ""), ("厨电", "灶具")),
    ("蒸箱", ("蒸箱【西门子品项】", ""), ("", "蒸箱")),
    ("烤箱", ("烤箱【西门子品项】", ""), ("厨电", "烤箱")),
    ("微波炉", ("", ""), ("生活电器", "微波炉")),
    ("管线机", ("管线机【西门子品项】", ""), ("净水", "管线机")),
    ("中央净水", ("中央净水【西门子品项】", "净水【西门子大类】"), ("净水", "净水器")),
    ("净水", ("中央净水【西门子品项】", "净水【西门子大类】"), ("净水", "净水器")),
    ("前置", ("前置【西门子品项】", ""), ("净水", "前置过滤器")),
    ("软水", ("中央软水【西门子品项】", ""), ("净水", "")),
    ("热水器", ("", ""), ("热水", "热水器")),
    ("壁挂炉", ("", ""), ("地暖", "二联供锅炉地暖")),
    ("锅炉", ("", ""), ("地暖", "二联供锅炉地暖")),
    ("暖气片", ("", ""), ("地暖", "明装暖气片")),
    ("风管机", ("", ""), ("空调", "柜挂天井风管机家用多联")),
    ("多联", ("", ""), ("空调", "商用多联")),
    ("空调", ("", ""), ("空调", "空调")),
    ("新风", ("", ""), ("新风", "新风净水")),
    ("电饭煲", ("", ""), ("生活电器", "格力生活电器")),
    ("电压力锅", ("", ""), ("生活电器", "格力生活电器")),
    ("豆浆机", ("", ""), ("生活电器", "格力生活电器")),
    ("破壁机", ("", ""), ("生活电器", "格力生活电器")),
    ("电视", ("", ""), ("", "")),
    ("扫地机器人", ("", ""), ("生活电器", "")),
    ("洗地机", ("", ""), ("生活电器", "")),
]

QIXIN = "启欣"  # 启欣特殊规则

# 行级品牌关键词：品牌 = 产品实际品牌，从产品名/型号推断，与「组织」无关。
# 长词必须排在短词前面（如 "AO史密斯" 在 "史密斯" 之前），否则会被短词先截走。
BRAND_KEYWORDS = ["AO史密斯", "A.O.史密斯", "史密斯", "COLMO", "卡萨帝", "科沃斯",
                  "东芝", "索尼", "松下", "长虹", "容声", "博世",
                  "西门子", "小天鹅", "美的", "格力", "大金", "方太", "创维", "TCL",
                  "石头", "林内", "菲斯曼", "能率", "约克", "怡口", "海尔", "海信",
                  "老板", "华帝", "云格", "启欣"]


def guess_brand_from_model(model):
    for b in BRAND_KEYWORDS:
        if b in model:
            return b
    return None


def open_wb(path, data_only=True):
    """读 Excel；优先 read_only 提速，遇 dimension 元数据损坏的文件（max_row=1）
    自动回退到非 read_only 模式。"""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=data_only)
    for s in wb.sheetnames:
        if s.startswith("hidden"):
            continue
        try:
            first = next(wb[s].iter_rows(min_row=1, max_row=1, values_only=True), None)
        except Exception:
            first = None
        if first and len(first) >= 3:
            return wb
        break
    wb.close()
    return openpyxl.load_workbook(path, data_only=data_only)


def parse_yymmdd(name):
    """6 位数字日期名（YYMMDD）解析为 (year, month, day)；其他返回 None。
    4 位日期名无年份信息，不做解析（跨年文件会排错）。"""
    digits = re.sub(r"[\s\.\-（）()]+", "", str(name))
    if re.fullmatch(r"\d{6}", digits):
        yy, mm, dd = int(digits[:2]), int(digits[2:4]), int(digits[4:6])
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return (2000 + yy, mm, dd)
    return None


def find_data_sheet(wb):
    """定位数据 sheet：跳过 hidden 开头与 Sheet1 的表及空表后，
    若存在 6 位日期名（YYMMDD）的表则取日期最大的，否则取最右的。
    返回 (sheet, 名字) 或 (None, None)。"""
    cands = []
    for sn in wb.sheetnames:
        if sn.lower().startswith("hidden") or sn == "Sheet1":
            continue
        ws = wb[sn]
        first = None
        for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
            first = row[0] if row else None
        if first is not None and str(first).strip() != "":
            cands.append((sn, ws))
    if not cands:
        return None, None
    dated = [(parse_yymmdd(sn), sn, ws) for sn, ws in cands]
    dated = [x for x in dated if x[0] is not None]
    if dated:
        dated.sort(key=lambda x: x[0])
        _, sn, ws = dated[-1]
        return ws, sn
    sn, ws = cands[-1]
    return ws, sn


def detect_format_and_rows(ws):
    """返回 (格式, 表头行号, 数据起始行号, 表头list)。格式: apply/template。"""
    rows = []
    for row in ws.iter_rows(min_row=1, max_row=5, values_only=True):
        rows.append(list(row))
    first_cell = str(rows[0][0]) if rows and rows[0] else ""
    if "申请表" in first_cell:
        hdr = None
        for i, r in enumerate(rows, start=1):
            if r and any("产品官方名称及型号" == str(c) for c in r if c):
                hdr = r
                return ("apply", i, i + 1, hdr)
        raise ValueError("申请表格式但找不到表头行（应含『产品官方名称及型号』）")
    if "唯一性ID" in first_cell:
        return ("template", 1, 2, rows[0])
    raise ValueError("无法识别源表格式：R1 首格=『%s』" % first_cell[:30])


def detect_brand(ws, fmt):
    """返回申请表 R2 的部门文本（去前缀），模板格式或空返回 None。"""
    if fmt == "apply":
        for row in ws.iter_rows(min_row=2, max_row=2, values_only=True):
            text = str(row[0]) if row and row[0] else ""
            text = text.replace("申请部门：", "").replace("申请部门:", "").strip()
            return text or None
    return None


def col_index(hdr, concept):
    for name in FIELD_VARIANTS.get(concept, []):
        for i, h in enumerate(hdr):
            if h is not None and str(h).strip() == name:
                return i
    return None


def to_number(v):
    if v is None or str(v).strip() == "":
        return None
    s = str(v).replace(",", "").replace("¥", "").replace("￥", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def round_price(v):
    """4 个价字段（成本价/销售结算价/品牌负责人审核价/价目表售价）共用：
    四舍五入取整到 0 位小数（half-up），None 原样返回。"""
    if v is None:
        return None
    from decimal import Decimal, ROUND_HALF_UP
    return int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def extract_grade(note):
    if note is None:
        return ""
    m = re.fullmatch(r"\s*([A-Fa-f])\s*(类)?\s*", str(note))
    if m:
        return m.group(1).upper() + "类"
    return ""


def load_source_rows(path, brand_hint=None):
    """解析源表。返回 (rows, brand, fmt, sheet_name, errors)。"""
    wb = open_wb(path)
    ws, sheet_name = find_data_sheet(wb)
    if ws is None:
        raise ValueError("源表里找不到数据 sheet（全是 hidden/空表）")
    fmt, hdr_row, data_row, hdr = detect_format_and_rows(ws)
    brand = brand_hint or detect_brand(ws, fmt)
    idx = {k: col_index(hdr, k) for k in FIELD_VARIANTS}
    rows = []
    for r in ws.iter_rows(min_row=data_row, max_row=ws.max_row, values_only=True):
        def g(k):
            i = idx[k]
            return r[i] if i is not None and i < len(r) else None
        model = g("model")
        if model is None or str(model).strip() == "":
            continue
        rows.append({
            "model": str(model).strip(),
            "price": to_number(g("price")),
            "limit": to_number(g("limit")),
            "settle": to_number(g("settle")),
            "cost": to_number(g("cost")),
            "note": g("note"),
            "src_brand": (str(g("brand")).strip() if g("brand") else ""),
            "src_pclass": (str(g("pclass")).strip() if g("pclass") else ""),
            "src_pitem": (str(g("pitem")).strip() if g("pitem") else ""),
        })
    wb.close()
    return rows, brand, fmt, sheet_name, idx


def classify(model, brand, src_pclass, src_pitem):
    """返回 (产品大类, 产品品项, matched)。乾鑫读源表；大金固定；欣暖家留空。"""
    if brand == "乾鑫":
        return src_pclass, src_pitem, True
    if brand == "大金":
        return "空调", "空调", True
    if brand == "欣暖家":
        return "", "", True
    group = 0 if brand == "西门子" else 1
    for kw, si, gen in KEYWORDS:
        if kw in model:
            picked = si if group == 0 else gen
            return picked[0], picked[1], True
    return "", "", False


def find_snapshot(pattern, downloads, required_cols):
    """按文件名日期降序找最新可用快照（含必需列且有数据行）。
    返回 (path, date_str) 或 (None, None)。"""
    files = sorted(glob.glob(os.path.join(downloads, pattern)), reverse=True)
    for f in files:
        if os.path.basename(f).startswith("~$"):
            continue
        try:
            wb = open_wb(f)
        except Exception:
            continue
        ws = wb[wb.sheetnames[0]]
        hdr = None
        for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
            hdr = [str(h) if h is not None else "" for h in row]
        ok = bool(hdr) and all(c in hdr for c in required_cols)
        if ok:
            for row in ws.iter_rows(min_row=2, max_row=2, values_only=True):
                if not row or row[0] is None or str(row[0]).strip() == "":
                    ok = False
        wb.close()
        if ok:
            m = re.search(r"(\d{8})", os.path.basename(f))
            d = ("%s-%s-%s" % (m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:8])) if m else ""
            return f, d
    return None, None


def load_products(path):
    """产品快照 -> list of dict。"""
    wb = open_wb(path)
    ws = wb[wb.sheetnames[0]]
    hdr = None
    for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
        hdr = list(row)
    want = {"name": "产品名称（必填）", "mat": "物料名称", "spec": "型号规格",
            "code": "物料编号", "pclass": "产品大类", "pitem": "产品品相"}
    ix = {k: (hdr.index(v) if v in [str(h) for h in hdr] else None) for k, v in want.items()}
    out = []
    for r in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        def g(k):
            i = ix[k]
            return (str(r[i]).strip() if i is not None and i < len(r) and r[i] is not None else "")
        if ix["name"] is None or not g("name"):
            continue
        out.append({"name": g("name"), "mat": g("mat"), "spec": g("spec"),
                    "code": g("code"), "pclass": g("pclass"), "pitem": g("pitem")})
    wb.close()
    return out


def match_product(model, products):
    """返回 (系统产品名称, 匹配方式) 或 (None, None)。"""
    for p in products:
        if p["name"] == model or p["mat"] == model:
            return p["name"], "精确"
    for p in products:
        if p["spec"] and len(p["spec"]) >= 4 and p["spec"] in model:
            return p["name"], "型号包含"
    for p in products:
        if p["mat"] and len(p["mat"]) >= 6 and (p["mat"] in model or model in p["mat"]):
            return p["name"], "子串"
    return None, None


def load_details(path):
    """明细快照 -> {(产品,价目表): (唯一性ID, 编号, 价目表ID)}。"""
    wb = open_wb(path)
    ws = wb[wb.sheetnames[0]]
    hdr = None
    for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
        hdr = [str(h) if h else "" for h in row]

    def ix(name):
        return hdr.index(name) if name in hdr else None
    i_id, i_no = ix("唯一性ID（必填）"), ix("价目表明细编号")
    i_prod, i_pb = ix("产品（必填）"), ix("价目表（必填）")
    i_pbid = ix("价目表_唯一性ID（必填）")
    out = {}
    if i_prod is None or i_pb is None:
        wb.close()
        raise ValueError("明细快照缺少 产品/价目表 列")
    for r in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        def g(i):
            return (str(r[i]).strip() if i is not None and i < len(r) and r[i] is not None else "")
        if g(i_prod) and g(i_pb):
            out[(g(i_prod), g(i_pb))] = (g(i_id), g(i_no), g(i_pbid))
    wb.close()
    return out


def write_sheet(path, cols, desc, data_rows, keep_desc):
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "价目表明细导入模版"
    ws.append(cols)
    for i, c in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=i)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2F5597")
    if keep_desc and desc:
        ws.append(desc)
    for row in data_rows:
        ws.append([row.get(c, "") for c in cols])
    for i, c in enumerate(cols, start=1):
        ws.column_dimensions[get_column_letter(i)].width = max(10, min(30, len(c) * 2 + 4))
    wb.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--brand", default=None,
                    help="组织名（决定价目表）；与 --org 等价，二者取优先级高者")
    ap.add_argument("--org", default=None,
                    help="组织名（决定价目表），优先级高于 --brand")
    ap.add_argument("--product-snapshot", default=None)
    ap.add_argument("--detail-snapshot", default=None)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--downloads", default=r"D:\Backup\Downloads")
    ap.add_argument("--keep-desc", action="store_true",
                    help="导入文件保留模板的字段说明行（默认不保留）")
    args = ap.parse_args()

    if not os.path.exists(args.source):
        print(json.dumps({"error": "源表不存在: %s" % args.source}, ensure_ascii=False))
        sys.exit(2)

    # org = 组织，决定「价目表」列；brand(产品实际品牌) 由每行型号独立推断
    org = args.org or args.brand
    rows, auto_dept, fmt, sheet_name, _ = load_source_rows(args.source, org)
    if org is None:
        org = auto_dept
    if org is None:
        # 乾鑫模板源表可从行内品牌列推断
        if rows and rows[0]["src_brand"]:
            org = "乾鑫"
        else:
            print(json.dumps({"error": "无法识别组织，请用 --org 指定（如 欣暖家/乾鑫/西门子）"},
                             ensure_ascii=False))
            sys.exit(2)
    prod_path, prod_date = (args.product_snapshot, "") if args.product_snapshot else \
        find_snapshot("产品对象导出结果_*.xlsx", args.downloads,
                      required_cols=["产品名称（必填）", "物料名称"])
    det_path, det_date = (args.detail_snapshot, "") if args.detail_snapshot else \
        find_snapshot("价目表明细对象导出结果_*.xlsx", args.downloads,
                      required_cols=["产品（必填）", "价目表（必填）"])
    if args.product_snapshot:
        m = re.search(r"(\d{8})", os.path.basename(args.product_snapshot))
        prod_date = ("%s-%s-%s" % (m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:8])) if m else ""
    if args.detail_snapshot:
        m = re.search(r"(\d{8})", os.path.basename(args.detail_snapshot))
        det_date = ("%s-%s-%s" % (m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:8])) if m else ""

    products = load_products(prod_path) if prod_path else []
    details = load_details(det_path) if det_path else {}

    pricebook = ORG_PRICEBOOKS.get(org, "")
    today = datetime.date.today().strftime("%Y%m%d")
    outdir = args.outdir or os.path.dirname(os.path.abspath(args.source))
    os.makedirs(outdir, exist_ok=True)

    new_rows, upd_rows, warns = [], [], []
    n_pending = n_dup = 0
    for src in rows:
        # 品牌 = 产品实际品牌，与组织无关：
        #   源表品牌列优先（乾鑫源表带此列）→ 其次从型号名推断 → 最后回退到组织名
        row_brand = src["src_brand"] or guess_brand_from_model(src["model"]) or org
        # 价目表严格按组织(org)走：同一张价目表内可含多个品牌（如乾鑫价目表里有大金/美的）
        pb = ORG_PRICEBOOKS.get(org, "")
        sysname, how = (match_product(src["model"], products) if products else (src["model"], "无快照直填"))
        w = {"源表型号": src["model"], "品牌": row_brand}
        if not products:
            w["状态"] = "无产品快照·未校验"
            w["建议"] = "导入前人工核对产品名称"
            warns.append(w)
        elif sysname is None:
            w["状态"] = "金蝶未同步"
            w["建议"] = "先在金蝶建好并同步到纷享销客，再重跑本表"
            warns.append(w)
            n_pending += 1
            continue
        # 分类特例按「组织」判断（乾鑫读源表列、西门子交叉、大金固定、欣暖家留空）
        pclass, pitem, matched = classify(src["model"], org, src["src_pclass"], src["src_pitem"])
        if not matched and org not in ("欣暖家", "大金", "乾鑫"):
            w2 = {"源表型号": src["model"], "品牌": row_brand, "状态": "分类未匹配",
                  "建议": "请人工确认产品大类/产品品项后补填"}
            warns.append(w2)
        grade = extract_grade(src["note"])
        if row_brand == QIXIN:
            price = limit = settle = cost = None
            pitem = ""
        else:
            price, limit, settle, cost = src["price"], src["limit"], src["settle"], src["cost"]
        base = {
            "成本价": round_price(cost), "销售结算价": round_price(settle),
            "品牌负责人审核价": round_price(limit), "品牌": row_brand,
            "产品大类": pclass, "产品品项": pitem, "产品等级": grade, "价目表折扣（%）": 100,
            "产品（必填）": sysname, "价目表售价": round_price(price), "价目表（必填）": pb,
            "业务类型（必填）": "预设业务类型",
        }
        if pb == "":
            warns.append({"源表型号": src["model"], "品牌": row_brand,
                          "状态": "价目表未配置", "建议": "该品牌不在启用价目表清单，请确认品牌或补充价目表"})
        key = (sysname, pb)
        if pb and key in details:
            uid, no, pbid = details[key]
            upd_rows.append({
                "唯一性ID（必填）": uid, "价目表明细编号": no,
                "成本价": round_price(cost), "销售结算价": round_price(settle),
                "品牌负责人审核价": round_price(limit),
                "价目表售价": round_price(price), "价目表_唯一性ID（必填）": pbid, "价目表（必填）": pb,
            })
            n_dup += 1
        else:
            new_rows.append(base)

    if not new_rows and not upd_rows and not warns:
        print(json.dumps({"error": "没有可生成的数据行"}, ensure_ascii=False))
        sys.exit(2)

    out = {"组织": org, "format": fmt, "sheet": sheet_name, "新建": len(new_rows),
           "更新": len(upd_rows), "待同步": n_pending, "警示": len(warns),
           "产品快照": prod_date or "无", "明细快照": det_date or "无", "files": []}
    suffix = "未校验" if not products else ""
    if new_rows:
        p1 = os.path.join(outdir, "%s_新建价目表明细_%s%s.xlsx" % (org, today, ("_" + suffix) if suffix else ""))
        write_sheet(p1, NEW_COLS, NEW_DESC, new_rows, args.keep_desc)
        out["files"].append(p1)
    if upd_rows:
        p2 = os.path.join(outdir, "%s_更新价目表明细_%s.xlsx" % (org, today))
        write_sheet(p2, UPD_COLS, UPD_DESC, upd_rows, args.keep_desc)
        out["files"].append(p2)
    if warns:
        p3 = os.path.join(outdir, "%s_产品核对清单_%s.xlsx" % (org, today))
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "核对清单"
        ws.append(["说明", "产品快照日期: %s | 明细快照日期: %s | 快照之后的新增与变更未覆盖" %
                   (prod_date or "无", det_date or "无")])
        ws.append(["源表型号", "品牌", "状态", "建议"])
        for w in warns:
            ws.append([w.get("源表型号", ""), w.get("品牌", ""), w.get("状态", ""), w.get("建议", "")])
        for i, c in enumerate(["源表型号", "品牌", "状态", "建议"], start=1):
            ws.cell(row=2, column=i).font = openpyxl.styles.Font(bold=True)
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = 30
        wb.save(p3)
        out["files"].append(p3)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
