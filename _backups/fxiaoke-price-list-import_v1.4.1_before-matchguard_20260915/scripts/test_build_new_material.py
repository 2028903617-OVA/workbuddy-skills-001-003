#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_new_material.py 的测试用例。运行: python test_build_new_material.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_new_material as M  # noqa

PASS = FAIL = 0


def chk(cond, name, got=None, want=None):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  OK   %s" % name)
    else:
        FAIL += 1
        print("  FAIL %s\n         got=%r want=%r" % (name, got, want))


def eq(got, want, name):
    chk(got == want, name, got, want)


print("== parse_name ==")
eq(M.parse_name("容声对开门冰箱BCD-606WKK1FPGZA"), ("容声", "对开门冰箱", "BCD-606WKK1FPGZA"), "冰箱三段")
eq(M.parse_name("卡萨帝多开门冰箱BCD-505W60CZBAS"), ("卡萨帝", "多开门冰箱", "BCD-505W60CZBAS"), "卡萨帝冰箱")
eq(M.parse_name("海信平板电视75E8S"), ("海信", "平板电视", "75E8S"), "电视型号码数字开头")
eq(M.parse_name("TCL平板电视98X11L"), ("TCL", "平板电视", "98X11L"), "TCL 无中文名")
eq(M.parse_name("东芝平板电视100L7QR"), ("东芝", "平板电视", "100L7QR"), "东芝电视")
r = M.parse_name("卡萨帝滚筒洗衣机CEC B12LWUS12YTGLBU1")
chk(r is not None and r[0] == "卡萨帝" and r[1] == "滚筒洗衣机", "品项尾部 CE/CZ 被剥掉", r)
eq(M.parse_name("不认识的产品XYZ123"), None, "无品牌返回 None")
eq(M.parse_name(""), None, "空串返回 None")

print("== 品牌前缀（有无空格 / 不误伤型号内斜杠）==")
eq(M.BRAND_PREFIX.sub("", "Casarte/卡萨帝 BCD-633WLCFDANZCU1 丝绒咖"), "BCD-633WLCFDANZCU1 丝绒咖", "有空格前缀")
eq(M.BRAND_PREFIX.sub("", "SIEMENS/西门子KF88HVA56C湖蕴蓝"), "KF88HVA56C湖蕴蓝", "无空格前缀")
eq(M.BRAND_PREFIX.sub("", "KFR-72LW/U61-1 白色"), "KFR-72LW/U61-1 白色", "型号内斜杠不误伤")
eq(M.BRAND_PREFIX.sub("", "H1210-MBLNE/QT98TU1"), "H1210-MBLNE/QT98TU1", "斜杠后非中文不误伤")

print("== clean_model ==")
eq(M.clean_model("BCD-515W60FZBAS琥珀钰"), "BCD-515W60FZBAS琥珀钰", "无前缀原样")
eq(M.clean_model("Ronshen/容声 BCD-509P60FZBBX"), "BCD-509P60FZBBX", "去前缀")
eq(M.clean_model("Casarte/卡萨帝 BCD-633WLCFDANZCU1 丝绒咖"), "BCD-633WLCFDANZCU1 丝绒咖", "保留颜色尾缀")
eq(M.clean_model("Midea/美的 MR- 449WUSJPGZ 月光米"), "MR-449WUSJPGZ 月光米", "型号码中间空格合并")
eq(M.clean_model("TINECO/添可 芙万 Artist 50S 芙万 Artist 50S"), "芙万 Artist 50S", "重复片段去重")
eq(M.clean_model("【新品】海信激光电视星光S2 纯享版 100吋 更护眼的家庭影院"),
   "海信激光电视星光S2 纯享版", "去新品/吋/营销词")
eq(M.clean_model("SIEMENS/西门子 WG74X2Y20W 黑色"), "WG74X2Y20W 黑色", "西门子洗衣机")

print("== tv_model ==")
eq(M.tv_model("海信RGB激光电视 星光S1纯享版 110英寸 110L7QR 大屏护眼 世界杯 流砂锖"),
   "110L7QR", "激光电视抽型号码")
eq(M.tv_model("Hisense/海信 85D50SD 85英寸 黑色 官方标配"), "85D50SD", "海信电视")
eq(M.tv_model("Skyworth/创维 75Q8H 75英寸 金色 官方标配"), "75Q8H", "创维电视")
eq(M.tv_model("海信激光电视星光S1 2026款 100英寸"), "星光S1", "无型号码退回中文系列名")
eq(M.tv_model("【新品】海信激光电视星光S2 纯享版 80吋 更护眼的家庭影院"),
   "星光S2 纯享版", "S2 系列名")

print("== ac_item（空调）==")
eq(M.ac_item("KFR-35GW/(35572)FNhAb-B1(WIFI)")[0], "1.5匹变频挂机", "35GW")
eq(M.ac_item("KFR-72LW/U61-1")[0], "3匹变频柜机", "72LW")
eq(M.ac_item("KFR-50GW/T3")[0], "2匹变频挂机", "50GW")
eq(M.ac_item("BCD-606WKK1FPGZA")[0], "", "非空调返回空")

print("== fix_item ==")
eq(M.fix_item("国产嵌入式洗碗机", "厨房大电", "CXW-350-LSAT2F1BNW", "西门子"),
   "国产欧式油烟机", "CXW → 油烟机")
eq(M.fix_item("倍世中央软水机IOT智能物联", "水健康", "CKC1000-RMF29HU1", "卡萨帝"),
   "净水机", "IOT 脏值被过滤并兜底")
eq(M.fix_item("热水器空机", "热水器", "JSLQ27-16CXE5UltraU1", "卡萨帝"),
   "燃气热水器", "空机脏值过滤后兜底燃气热水器")
eq(M.fix_item("国产滚筒洗衣机", "洗护", "WG74X2Y20W", "西门子"),
   "国产滚筒洗衣机", "正常品项不动")

print("== compose_g ==")
eq(M.compose_g("容声", "多开门冰箱", "BCD-515W60FZBAS琥珀钰"),
   "容声多开门冰箱BCD-515W60FZBAS琥珀钰", "常规拼接")
eq(M.compose_g("海信", "激光电视", "海信激光电视星光S1"),
   "海信激光电视星光S1", "spec 已含品牌时不重复")
eq(M.compose_g("容声", "", "BCD-606"), "", "无品项返回空")
eq(M.compose_g("容声", "多开门冰箱", ""), "", "无型号返回空")

print("== guess_item（最相近型号）==")
lib = M.build_lib(
    [{"name": "容声多开门冰箱BCD-505W60CZBAS", "mat": "", "spec": "BCD-505W60CZBAS"},
     {"name": "容声对开门冰箱BCD-606WKK1FPGZA", "mat": "", "spec": "BCD-606WKK1FPGZA"},
     {"name": "卡萨帝多开门冰箱BCD-633WDCHU1", "mat": "", "spec": "BCD-633WDCHU1"},
     {"name": "格力1.5匹变频挂机KFR-35GW/(35558)FNhAa-B1", "mat": "", "spec": "KFR-35GW/(35558)FNhAa-B1"}],
    None)
it, cf, src = M.guess_item("容声", "BCD-515W60FZBAS", "冰箱", lib)
eq(it, "多开门冰箱", "借同系列品项")
chk(src == "最相近型号" and cf >= 0.7, "来源=最相近型号且高置信", (src, cf))
it2, cf2, src2 = M.guess_item("卡萨帝", "BCD-633WLCFDANZCU1", "冰箱", lib)
eq(it2, "多开门冰箱", "卡萨帝借同系列品项")
# 行业不符降级：拿洗护的型号去问冰箱
it3, cf3, src3 = M.guess_item("容声", "BCD-505W60CZBAS", "洗护", lib)
chk("行业众数" in src3 or src3 == "无可用样本" or cf3 < 0.7,
    "行业不符时降级不返回高置信冰箱品项", (it3, src3, cf3))

print("== 端到端 process_rows ==")
rows = [
    {"row": 2, "brand": "容声", "industry": "冰箱", "E": "BCD-515W60FZBAS琥珀钰"},
    {"row": 3, "brand": "容声", "industry": "冰箱", "E": "Ronshen/容声 BCD-509P60FZBBX"},
    {"row": 4, "brand": "海信", "industry": "电视机",
     "E": "海信RGB激光电视 星光S1纯享版 110英寸 110L7QR 大屏护眼 世界杯 流砂锖"},
    {"row": 5, "brand": "TCL", "industry": "电视机", "E": "98X11L"},
    {"row": 6, "brand": "卡萨帝", "industry": "热水器",
     "E": "Casarte/卡萨帝 JSLQ27-16CXE5UltraU1 博卡灰 天然气"},
]
res = M.process_rows(rows, lib)
eq(res[0]["F"], "BCD-515W60FZBAS琥珀钰", "端到端 F1")
eq(res[0]["G"], "容声多开门冰箱BCD-515W60FZBAS琥珀钰", "端到端 G1")
eq(res[1]["F"], "BCD-509P60FZBBX", "端到端 F2")
eq(res[1]["G"], "容声多开门冰箱BCD-509P60FZBBX", "端到端 G2")
eq(res[2]["F"], "110L7QR", "端到端 电视 F")
eq(res[2]["G"], "海信激光电视110L7QR", "端到端 电视 G（品牌不重复）")
eq(res[3]["G"], "TCL平板电视98X11L", "端到端 TCL G")
eq(res[4]["G"], "卡萨帝燃气热水器JSLQ27-16CXE5UltraU1 博卡灰 天然气", "端到端 热水器兜底")
chk(all(r["F"] and r["G"] for r in res), "端到端 F/G 零空值",
    [r for r in res if not (r["F"] and r["G"])])

print("")
print("=" * 60)
print("通过 %d / 失败 %d" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
