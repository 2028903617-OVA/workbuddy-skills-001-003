---
name: pyautogui-rpa-builder
description: |
  Build desktop GUI auto-click bots with pyautogui for web-based / B/S ERP systems
  (e.g. 金蝶云星空) driven by Excel data. Use this skill when a user wants to automate
  repetitive clicking in a browser or desktop app — searching, filling forms, clicking
  buttons in a loop. Encodes proven patterns that avoid common failures: head-tail list
  refresh to clear stale input, single-click-to-focus paste, long reaction waits so the
  "save confirmation" dialog never appears, template-match verification of open/close/
  popup state, paste pixel-diff verification, a GBK .bat launcher for double-click, and a
  dual basic/verified version split. Trigger phrases: "自动点击机器人", "桌面点击脚本",
  "按Excel循环点击", "金蝶/网页版 自动操作", "RPA 脚本".
agent_created: true
---

# pyautogui RPA Builder

## Purpose
Produce a maintainable pyautogui desktop-clicking bot that drives a web-based ERP / B/S
application through a loop of coordinate clicks, fed by an Excel column (e.g. material
names). The skill favors robustness over speed: each step waits for the slow web app to
react, and optional computer-vision checks confirm the UI actually changed.

## When to use
- A user asks for a bot that clicks through a desktop/browser app repeatedly.
- The target is a web page (e.g. 金蝶云星空) where inputs need focus before paste and
  reactions are slow.
- Pasted text sometimes fails to land, or a "是否保存" dialog appears mid-loop.
- Build two flavors: a lightweight "basic" version (pure clicks, no CV deps) and a
  "verified" version (template + paste checks).

## Workflow
1. Confirm inputs: which Excel file / sheet / column / row range drives the loop, and the
   exact click sequence in the target app (a screenshot per step helps).
2. Scaffold from `assets/bot_template.py` — copy it into the user's project and replace the
   TODO markers (excel_path, sheet, name_col, CALIB_POINTS, and the click sequence in run()).
3. Generate the launcher with `assets/make_bat.py` (writes a GBK `run_bot.bat` so
   double-clicking never shows garbled text).
4. Calibrate: run `python bot.py --calibrate` and click each reference point; coords persist
   to `kingdee_coords.json` (machine-specific — re-calibrate after moving the window or
   changing display scaling).
5. Dry-run: `python bot.py --dry-run` to confirm the Excel names are read correctly.
6. Trial: `python bot.py --start 5 --end 6` for a 2-row smoke test, then `--all` for full.

## Critical patterns (see `references/best_practices.md` for code)
- **Single-click to focus, then Ctrl+V.** Web inputs ignore Ctrl+A / triple-click / clear-×
  buttons; a plain `click()` then `hotkey('ctrl','v')` is the reliable path.
- **Head-tail refresh.** Reopen the list from the homepage at the start of every loop and
  close its tab at the end — the freshly opened search box is empty, so no stale value
  lingers and no clearing logic is needed.
- **Wait long enough after Save.** A ~2.0s `page_delay` after clicking 保存 lets the web app
  commit before the next click; this prevents the "是否保存" popup entirely, so no separate
  "是" confirmation step is required.
- **Verify, don't assume.** Use `pyautogui.locateOnScreen` (confidence ~0.85) to confirm a
  panel opened / closed; use a pixel diff (PIL ImageChops vs the empty-state screenshot
  captured at calibration) to confirm paste landed. Both skip gracefully when no reference
  image exists.
- **FAILSAFE + window activation.** Enable `pyautogui.FAILSAFE` (mouse-to-corner abort) and
  best-effort bring the target window front via pygetwindow before each item.
- **Two versions.** Ship `bot_template.py` as both a "basic" copy (drop the verify_* calls
  and CV imports) and a "verified" copy; keep coords.json per folder.

## Bundled resources
- `assets/bot_template.py` — full, commented, working template (verified flavor) to copy and adapt.
- `assets/make_bat.py` — writes a GBK `run_bot.bat` launcher (menu: calibrate / trial / full / dry-run).
- `references/best_practices.md` — environment setup, code snippets, and the pitfall list.
