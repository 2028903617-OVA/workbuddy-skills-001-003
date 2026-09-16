#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 GBK 编码的 run_bot.bat 启动器（双击不乱码）。

用法：
  python make_bat.py                 # 在脚本同目录生成 run_bot.bat
  python make_bat.py D:/mybot/bot.py # 指定 bot 路径，在同目录生成 run_bot.bat

要点：
  - 必须 GBK 编码 + 首行 `chcp 936 >nul`，否则中文菜单双击乱码。
  - 调用受管 venv 的 python 解释器，避免依赖系统环境。
  - 菜单：1 校准 / 2 试跑(5-6行) / 3 全量 / 4 预览名称 / 5 退出。
"""

import os
import sys

# 受管 venv 解释器（金蝶机器人依赖装在里面）
PYTHON = r"C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

BAT_CONTENT = """@echo off
chcp 936 >nul
title 金蝶同步销客物料机器人
set "PY={python}"
set "BOT={bot}"

:menu
cls
echo ==============================
echo   金蝶同步销客物料机器人
echo ==============================
echo  [1] 校准参考点（首次/移动窗口后）
echo  [2] 试跑 第5-6行
echo  [3] 全量执行
echo  [4] 预览 Excel 名称（dry-run）
echo  [5] 退出
echo ==============================
set /p choice=请选择 [1-5]：
if "%choice%"=="1" goto calib
if "%choice%"=="2" goto trial
if "%choice%"=="3" goto full
if "%choice%"=="4" goto dry
if "%choice%"=="5" goto end
echo 输入无效，请重新选择。
pause
goto menu

:calib
"%PY%" "%BOT%" --calibrate
pause
goto menu

:trial
"%PY%" "%BOT%" --start 5 --end 6
pause
goto menu

:full
"%PY%" "%BOT%" --all
pause
goto menu

:dry
"%PY%" "%BOT%" --dry-run
pause
goto menu

:end
exit /b
"""


def main():
    # bot 路径：命令行参数，或本脚本同目录下的 bot.py
    if len(sys.argv) > 1:
        bot_path = sys.argv[1]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        bot_path = os.path.join(here, "bot.py")
    if not os.path.exists(bot_path):
        print(f"[错误] 找不到 bot 脚本：{bot_path}")
        sys.exit(1)

    out_dir = os.path.dirname(os.path.abspath(bot_path))
    out_path = os.path.join(out_dir, "run_bot.bat")
    content = BAT_CONTENT.format(python=PYTHON, bot=bot_path)
    # 关键：GBK 编码，否则双击中文乱码
    with open(out_path, "w", encoding="gbk") as f:
        f.write(content)
    print(f"已生成 GBK 启动器 -> {out_path}")


if __name__ == "__main__":
    main()
