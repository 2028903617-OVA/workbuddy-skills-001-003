#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_sync.py —— 001/003 两台机器 skills 目录 Git 中转同步一键脚本。

设计要点（详见 workbuddy-dual-machine-memory-sync SKILL.md）：
- 整目录镜像（非行并集），复用 Git 天然冲突合并。
- 超大项（fxiaoke-apl-testground 7.5MB 等）已在仓库 .gitignore 排除，本脚本仅提示。
- 冲突保护：检测到 both modified 即中止 push 并告警，绝不无脑覆盖（对应记忆同步 E1 竞态教训）。

用法：
  python skill_sync.py --machine 003 --status      # 查看仓库状态/待同步/超大项
  python skill_sync.py --machine 003 --pull        # 拉取远端（冲突则中止）
  python skill_sync.py --machine 003 --push        # 本机改动提交并推远端（冲突则中止）
  python skill_sync.py --machine 003 --sync        # pull + push 一体化
"""
import argparse
import datetime as _dt
import subprocess
import sys
from pathlib import Path

SKILLS_DIR = Path.home() / ".workbuddy" / "skills"
OTHER = {"001": "003", "003": "001"}
# 超大项黑名单（与 .gitignore 对应，仅用于提示，不参与 git 同步）
LARGE_DIRS = ["fxiaoke-apl-testground", "talking-video-auto-edit", "wps-office-automation-skill"]


def _run(args: list, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(args, cwd=str(SKILLS_DIR), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"命令失败 {' '.join(args)}: {r.stderr.strip()}")
    return r


def _has_conflict() -> bool:
    """git status --porcelain 含 UU/AA/DD 或 both modified 即冲突。"""
    r = _run(["git", "status", "--porcelain"], check=False)
    for line in r.stdout.splitlines():
        code = line[:2]
        if code in ("UU", "AA", "DD") or "both" in line:
            return True
    return False


def cmd_status(args) -> int:
    print(f"[status] skills 仓库: {SKILLS_DIR}")
    print(f"[status] 本机: {args.machine}  对端: {OTHER[args.machine]}")
    try:
        br = _run(["git", "branch", "--show-current"], check=False).stdout.strip()
        print(f"[status] 分支: {br or '(detached)'}")
    except Exception as e:  # noqa: BLE001
        print(f"[status] 取分支失败: {e}")
    rem = _run(["git", "remote", "-v"], check=False).stdout.strip()
    if rem:
        print(f"[status] 远端:\n{rem}")
    else:
        print("[status] ⚠️ 未配置远端（git remote add origin <URL>），无法跨机，仅本机仓库。")
    st = _run(["git", "status", "--short"], check=False).stdout.strip()
    print(f"[status] 工作区改动:\n{st if st else '(clean)'}")
    print("[status] 超大项（.gitignore 已排除，需手动/网盘同步）:")
    for d in LARGE_DIRS:
        p = SKILLS_DIR / d
        print(f"  - {d}/  {'存在' if p.exists() else '不存在'}")
    if _has_conflict():
        print("[status] ⚠️ 检测到合并冲突，请先 git mergetool 解决！")
    else:
        print("[status] 无合并冲突。")
    return 0


def cmd_pull(args) -> int:
    if _has_conflict():
        print("[pull] ❌ 存在未解决冲突，中止。请先 git mergetool。")
        return 1
    r = _run(["git", "fetch", "origin"], check=False)
    if r.returncode != 0:
        print(f"[pull] ⚠️ fetch 失败（可能未配远端）: {r.stderr.strip()}")
        return 1
    r = _run(["git", "pull", "--ff-only", "origin"], check=False)
    if r.returncode != 0:
        print(f"[pull] ❌ pull 失败（可能需先配 upstream 或存在冲突）: {r.stderr.strip()}")
        return 1
    print("[pull] ✅ 已拉取远端最新。")
    return 0


def cmd_push(args) -> int:
    _run(["git", "add", "-A"], check=False)
    if _has_conflict():
        print("[push] ❌ 检测到合并冲突，中止 push！请先 git mergetool 解决，切勿无脑覆盖。")
        return 1
    st = _run(["git", "status", "--porcelain"], check=False).stdout.strip()
    if st:
        msg = f"sync: machine {args.machine} {_dt.datetime.now():%Y-%m-%d %H:%M}"
        _run(["git", "commit", "-q", "-m", msg], check=False)
        print(f"[push] 已提交: {msg}")
    else:
        print("[push] 本机无改动，无需提交。")
    r = _run(["git", "push", "origin", "HEAD"], check=False)
    if r.returncode != 0:
        print(f"[push] ❌ push 失败（可能未配远端/upstream，或远端有更新需先 pull）: {r.stderr.strip()}")
        return 1
    print("[push] ✅ 已推送到远端。")
    return 0


def cmd_sync(args) -> int:
    if cmd_pull(args) != 0:
        return 1
    return cmd_push(args)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--machine", required=True, choices=["001", "003"])
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--pull", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--sync", action="store_true", help="pull + push")
    args = ap.parse_args()
    if args.pull:
        return cmd_pull(args)
    if args.push:
        return cmd_push(args)
    if args.sync:
        return cmd_sync(args)
    return cmd_status(args)  # 默认 status


if __name__ == "__main__":
    sys.exit(main() or 0)
