#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyautogui RPA Bot — verified flavor template (金蝶云星空 "同步销客物料" 风格)

复制此文件到你的项目目录，替换所有 【TODO】 标记，然后：
  1) python bot.py --calibrate     # 逐一点击 8 个参考点，坐标存入 kingdee_coords.json
  2) python bot.py --dry-run        # 确认 Excel 名称读取正确
  3) python bot.py --start 5 --end 6   # 试跑 2 行
  4) python bot.py --all            # 全量执行

依赖（已装在受管 venv）：
  基础版：pyautogui, openpyxl, pyperclip
  校验版：上面 + numpy, Pillow
运行：C:\\Users\\Administrator\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe bot.py ...

安全：FAILSAFE=True —— 鼠标甩到屏幕左上角即中止。
"""

import os
import sys
import time
import json
import argparse

import pyautogui
import pyperclip

# ---- Excel 读取（基础版也需要）----
from openpyxl import load_workbook

# ---- 校验版专用（无 numpy/Pillow 时自动降级为“跳过校验”）----
try:
    import numpy as np
    from PIL import Image, ImageChops
    _HAS_CV = True
except Exception:
    _HAS_CV = False

# 安全开关：鼠标移到屏幕左上角 (0,0) 中止脚本
pyautogui.FAILSAFE = True

# =====================================================================
# 【TODO】配置区
# =====================================================================
CONFIG = {
    # ---- Excel 数据源 ----
    "excel_path": r"C:\Users\Administrator\WorkBuddy\2026-09-12-13-15-14\kingdee_bot_v2_verified\物料清单.xlsx",  # 【TODO】改成你的 Excel
    "sheet": "Sheet1",          # 【TODO】工作表名
    "name_col": "B",            # 【TODO】名称所在列（如 "B"）
    "header_row": 1,            # 表头行（数据从第 header_row+1 行开始）

    # ---- 目标窗口 ----
    "win_title": "金蝶云星空",   # 【TODO】pygetwindow 按标题激活窗口（best-effort，失败仅告警）

    # ---- 节奏（金蝶反应慢，宁长勿短）----
    "click_delay": 1.2,         # 普通点击后等待
    "search_delay": 2.0,        # 点搜索后等待结果
    "page_delay": 2.0,          # 点“保存”后等待提交，关键：足够长则“是否保存”不弹
    "verify": True if _HAS_CV else False,   # 是否做模板/粘贴校验
    "verify_conf": 0.85,        # 模板匹配置信度
    "verify_timeout": 12,       # 单次校验最长等待（秒）

    # ---- 执行模式 ----
    "confirm_each": False,      # False=自动连续执行；True=每行回车前确认
}

# 校准点（8 个；已去掉“是否保存→是”按钮，靠 page_delay 规避）
CALIB_POINTS = [
    ("material_list_tile", "【物料列表】入口磁贴（首页点它打开列表）"),
    ("search_box",        "列表搜索框【中心】（校准时保持为空，作为粘贴校验的空态基准）"),
    ("search_btn",        "【搜索】按钮"),
    ("result_code",       "搜索结果首行【物料编码/可点击进入】位置"),
    ("sync_btn",          "进入后【同步销客物料】按钮"),
    ("save_btn",          "【保存】按钮"),
    ("close_x",           "修改页右上角【关闭×】"),
    ("list_tab_close_x",  "列表页签【关闭×】"),
]

# 模板截图键（校准时截取小图存入 templates/{key}.png）
TEMPLATE_KEYS = ("search_box", "close_x")

# 校验映射：动作键 -> (模板键, "present"/"absent")
# present = 该模板应出现在屏幕上；absent = 应已消失（关闭成功）
VERIFY = {
    "material_list_tile": ("search_box", "present"),  # 打开列表后搜索框在
    "close_x":            ("close_x",   "absent"),     # 关闭修改页后×应消失
}

COORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kingdee_coords.json")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


# =====================================================================
# 坐标与模板工具
# =====================================================================
def load_coords():
    if os.path.exists(COORDS_FILE):
        with open(COORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_coords(coords):
    os.makedirs(os.path.dirname(COORDS_FILE), exist_ok=True)
    with open(COORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)
    print(f"  坐标已保存 -> {COORDS_FILE}")


def template_path(key):
    return os.path.join(TEMPLATES_DIR, f"{key}.png")


def calibrate():
    """逐一点击参考点，坐标写入 kingdee_coords.json，并截取模板小图。"""
    coords = {}
    print("\n=== 校准模式 ===")
    print("依次移动鼠标到各点中心，就位后按回车。鼠标甩到左上角可中止。\n")
    for key, hint in CALIB_POINTS:
        input(f"→ 请移动鼠标到【{hint}】，就位后按回车：")
        x, y = pyautogui.position()
        coords[key] = [x, y]
        print(f"  ✓ {key} = ({x}, {y})")
        # 截取模板小图（搜索框/关闭×）
        if key in TEMPLATE_KEYS and _HAS_CV:
            os.makedirs(TEMPLATES_DIR, exist_ok=True)
            w, h = (140, 44) if key == "search_box" else (24, 24)
            shot = pyautogui.screenshot(region=(x - w // 2, y - h // 2, w, h))
            shot.save(template_path(key))
            print(f"  ✓ 模板已存 templates/{key}.png")
    save_coords(coords)
    print("校准完成。\n")


# =====================================================================
# 窗口激活（best-effort）
# =====================================================================
def activate_window():
    try:
        import pygetwindow as gw
        wins = gw.getWindowsWithTitle(CONFIG["win_title"])
        if wins:
            wins[0].activate()
            time.sleep(0.3)
    except Exception as e:
        print(f"  [warn] 窗口激活失败，请手动保持目标窗口在前台：{e}")


# =====================================================================
# 校验：模板匹配（开/关/弹窗状态）
# =====================================================================
def wait_for_template(action_key, timeout=None):
    """根据 VERIFY 映射确认 UI 状态；无模板或无 CV 则直接放行。"""
    if action_key not in VERIFY:
        return True
    tkey, mode = VERIFY[action_key]
    path = template_path(tkey)
    if not CONFIG["verify"] or not _HAS_CV or not os.path.exists(path):
        return True
    conf = CONFIG["verify_conf"]
    start = time.time()
    limit = timeout or CONFIG["verify_timeout"]
    while time.time() - start < limit:
        try:
            found = pyautogui.locateOnScreen(path, confidence=conf) is not None
        except Exception:
            found = False
        if (mode == "present" and found) or (mode == "absent" and not found):
            return True
        time.sleep(0.5)
    # 超时：再判一次
    try:
        found = pyautogui.locateOnScreen(path, confidence=conf) is not None
    except Exception:
        found = False
    ok = (mode == "present" and found) or (mode == "absent" and not found)
    if not ok:
        raise RuntimeError(f"校验超时：模板 {tkey} 期望 {mode} 但未满足（动作 {action_key}）")
    return True


# =====================================================================
# 校验：粘贴像素差分（文字是否真的落进输入框）
# =====================================================================
def verify_paste(coord):
    """把当前搜索框截图与校准时的空态对比，差异像素>50 视为已粘贴。返回 bool。"""
    path = template_path("search_box")
    if not CONFIG["verify"] or not _HAS_CV or not os.path.exists(path):
        return True
    x, y = coord
    w, h = 140, 44
    cur = pyautogui.screenshot(region=(x - w // 2, y - h // 2, w, h)).convert("RGB")
    empty = Image.open(path).convert("RGB")
    diff = ImageChops.difference(empty, cur)
    n_diff = int((np.asarray(diff).sum(axis=2) > 30).sum())
    if n_diff > 50:
        return True
    print(f"  [warn] 粘贴校验未通过（差异像素={n_diff}），可能文字未落入")
    return False


# =====================================================================
# 基础动作
# =====================================================================
def click_at(coords, key, delay=None):
    x, y = coords[key]
    pyautogui.click(x, y)
    time.sleep(delay if delay is not None else CONFIG["click_delay"])


def focus_search(coords):
    """网页输入框：先单击进入编辑态，再粘贴。"""
    pyautogui.click(coords["search_box"])
    time.sleep(CONFIG["click_delay"])


def paste_text(text):
    pyperclip.copy(text)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1.5)


# =====================================================================
# Excel 读取
# =====================================================================
def read_names(start=None, end=None):
    wb = load_workbook(CONFIG["excel_path"], data_only=True)
    ws = wb[CONFIG["sheet"]]
    col = CONFIG["name_col"].upper()
    rows = ws[col]
    names = []
    for cell in rows:
        if cell.row <= CONFIG["header_row"]:
            continue
        if start and cell.row < start:
            continue
        if end and cell.row > end:
            continue
        val = cell.value
        if val is None or str(val).strip() == "":
            continue
        names.append((cell.row, str(val).strip()))
    return names


# =====================================================================
# 主循环（头尾刷新：每次重开列表 -> 搜索框恒为空）
# =====================================================================
def run(start=None, end=None, all_rows=False):
    coords = load_coords()
    missing = [k for k, _ in CALIB_POINTS if k not in coords]
    if missing:
        print(f"[错误] 缺少校准点：{missing}，请先 --calibrate")
        sys.exit(1)

    names = read_names(start, end) if not all_rows else read_names()
    print(f"\n=== 执行 {len(names)} 行 ===")
    activate_window()

    for idx, (row, name) in enumerate(names, 1):
        print(f"\n[{idx}/{len(names)}] 第 {row} 行：{name}")
        if CONFIG["confirm_each"]:
            choice = input("  回车继续（输入 q 退出）: ")
            if choice.strip().lower() == "q":
                break

        # —— 头：从首页重开列表 ——
        click_at(coords, "material_list_tile", CONFIG["page_delay"])
        wait_for_template("material_list_tile")  # 搜索框出现

        # —— 粘贴名称（单击聚焦 + Ctrl+V），失败重试一次 ——
        focus_search(coords)
        paste_text(name)
        if not verify_paste(coords["search_box"]):
            focus_search(coords)
            paste_text(name)
            if not verify_paste(coords["search_box"]):
                raise RuntimeError(f"第 {row} 行粘贴校验两次失败，已中止")

        # —— 搜索 ——
        click_at(coords, "search_btn", CONFIG["search_delay"])

        # —— 点结果进入 ——
        click_at(coords, "result_code", CONFIG["click_delay"])

        # —— 同步销客物料 ——
        click_at(coords, "sync_btn", 1.5)

        # —— 保存（关键：留足 page_delay，避免“是否保存”弹窗）——
        click_at(coords, "save_btn", CONFIG["page_delay"])

        # —— 尾：关闭修改页 + 列表页签（头尾刷新）——
        click_at(coords, "close_x", 1.5)
        wait_for_template("close_x")  # close_x 应消失
        click_at(coords, "list_tab_close_x", 1.5)

    print("\n=== 全部完成 ===")


# =====================================================================
# 入口
# =====================================================================
def main():
    ap = argparse.ArgumentParser(description="pyautogui RPA 机器人（校验版模板）")
    ap.add_argument("--calibrate", action="store_true", help="校准 8 个参考点")
    ap.add_argument("--dry-run", action="store_true", help="仅打印读取到的名称")
    ap.add_argument("--start", type=int, help="起始行（含）")
    ap.add_argument("--end", type=int, help="结束行（含）")
    ap.add_argument("--all", dest="all_rows", action="store_true", help="全量执行")
    args = ap.parse_args()

    if args.calibrate:
        calibrate()
        return
    if args.dry_run:
        names = read_names(args.start, args.end)
        print(f"读取到 {len(names)} 个名称：")
        for r, n in names:
            print(f"  行{r}: {n}")
        return
    if args.all_rows or args.start or args.end:
        run(args.start, args.end, all_rows=args.all_rows)
        return
    # 无参数：交互菜单
    print("用法：")
    print("  python bot.py --calibrate      校准参考点")
    print("  python bot.py --dry-run        预览名称")
    print("  python bot.py --start 5 --end 6  试跑")
    print("  python bot.py --all            全量")


if __name__ == "__main__":
    main()
