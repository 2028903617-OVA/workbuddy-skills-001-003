# pyautogui RPA Builder — Best Practices & Pitfalls

Deep-dive companion to `SKILL.md`. Code patterns below are battle-tested on 金蝶云星空
(web-based ERP) and apply to any slow B/S app driven by coordinate clicks.

## 1. Environment

- **Python**: use the managed venv, not the system interpreter:
  `C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
- **Pinned deps (already installed in that venv)**:
  `pyautogui==0.9.54`, `pyperclip==1.11.0`, `openpyxl==3.1.5`, `numpy==2.4.4`, `Pillow==12.2.0`.
  The verified flavor needs `numpy` + `Pillow` (paste pixel-diff); the basic flavor needs only
  `pyautogui` + `openpyxl` + `pyperclip`.
- **bash caveats on this box**: no `mkdir`/`cp`/`rm`/`zip`/`ls`. Create dirs and copy/zip via
  the venv Python (`os`, `shutil`, `zipfile`). `rm` via `os.remove`.

## 2. Calibration design

- Store coords in `kingdee_coords.json` (`{key: [x, y]}`) next to the script. Re-calibrate
  whenever the window moves or display scaling changes (coords are absolute, screen-specific).
- During calibration, capture a small reference screenshot per `TEMPLATE_KEYS` entry
  (e.g. 140×44 region) into `templates/{key}.png`. The `search_box` capture doubles as the
  **empty-state** reference for paste verification — instruct the user to keep that box empty
  while calibrating it.
- Calibration points (8, after dropping the "是否保存→是" button — see §4):
  `material_list_tile, search_box, search_btn, result_code, sync_btn, save_btn, close_x,
  list_tab_close_x`.

## 3. Code patterns (copy from `assets/bot_template.py`)

**Single-click focus + paste** (web inputs need a click to enter edit mode):
```python
def focus_search(coords):
    pyautogui.click(coords["search_box"]); time.sleep(1.2)

def paste_text(text):
    pyperclip.copy(text); time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v"); time.sleep(1.5)
```

**Head-tail refresh** (reopen list each loop → search box is always empty):
```python
click_at(coords, "material_list_tile", CONFIG["page_delay"])   # open list
# ... focus / paste / search / click result / sync / save ...
click_at(coords, "close_x", 1.5)          # close modify tab
click_at(coords, "list_tab_close_x", 1.5) # close list tab
```

**Template-match verification** (open/close/popup state):
```python
def wait_for_template(tkey, mode, timeout=None):
    path = template_path(tkey)
    if not CONFIG["verify"] or not os.path.exists(path):
        return True
    conf = CONFIG["verify_conf"]  # ~0.85
    start = time.time()
    while time.time() - start < (timeout or CONFIG["verify_timeout"]):
        try:
            found = pyautogui.locateOnScreen(path, confidence=conf) is not None
        except Exception:
            found = False
        if (mode == "present" and found) or (mode == "absent" and not found):
            return True
        time.sleep(0.5)
    # final check
    ...
```
Wire it with a `VERIFY = {"open_action": ("template_key", "present"), ...}` map.

**Paste pixel-diff verification** (did the text actually land?):
```python
def verify_paste(coord):
    from PIL import ImageChops
    import numpy as np
    path = template_path("search_box")          # empty-state ref from calibration
    if not CONFIG["verify"] or not os.path.exists(path):
        return True
    x, y = coord; w, h = 140, 44
    cur = pyautogui.screenshot(region=(x-w//2, y-h//2, w, h)).convert("RGB")
    empty = Image.open(path).convert("RGB")
    diff = ImageChops.difference(empty, cur)
    n_diff = int((np.asarray(diff).sum(axis=2) > 30).sum())
    return n_diff > 50     # pasted text = thousands of differing px; cursor alone < 50
```

**Window activation + FAILSAFE**:
```python
pyautogui.FAILSAFE = True   # mouse to top-left corner aborts
import pygetwindow as gw
wins = gw.getWindowsWithTitle(CONFIG["win_title"])   # best-effort, system may block
```
Activate before each item; if it fails, just warn and continue (clicks still land if the user
manually focuses the app).

## 4. Why there is NO "是否保存 → 是" step

Clicking 保存 then immediately clicking close (before the web app commits) triggers the
"是否保存?" dialog. Fix is **timing, not another click**: keep `page_delay ≈ 2.0s` after
保存, then close. The modify-tab-close is still verified (`close_x` absent check) so a
genuinely-unsaved state stops the run with an error instead of mis-clicking. Hence the
"是" button is deliberately **not** calibrated — it removes a fragile manual step.

## 5. Launcher (run_bot.bat)

`make_bat.py` writes the `.bat` as **GBK** (`encoding="gbk"`) with `chcp 936 >nul` at the top.
This is mandatory: a UTF-8 `.bat` shows garbled Chinese on double-click. If a static `.bat`
ever looks garbled, regenerate it with `make_bat.py`.

## 6. Packaging

Bundle script + bat + coords.json + `templates/` + a work-log into a zip with
`zipfile` (no `zip` binary here). Keep the basic and verified copies in separate folders so
each has its own `kingdee_coords.json`.

## 7. Pitfall table

| Symptom | Root cause | Fix |
|---|---|---|
| Pasted text missing | Input not focused (no click before Ctrl+V) | `click()` then `hotkey('ctrl','v')` |
| Old value concatenated in search box | Stale text from previous loop | Head-tail refresh (reopen list each loop) |
| "是否保存" dialog appears | Closed page before save committed | Lengthen `page_delay` to ~2.0s after 保存 |
| Ctrl+A / triple-click selects only part | Web input ignores them | Single click + Ctrl+V (no pre-clear) |
| No "×" clear button on the field | Field simply doesn't have one | Don't rely on it; use head-tail refresh |
| .bat shows garbled text | Saved as UTF-8, not GBK | `make_bat.py` (writes GBK) + `chcp 936` |
| Verification false alarm | Reference image stale | Re-run `--calibrate` after moving window / scaling change |
| Clicks miss / paste fails | Window lost focus | `activate_kingdee()` before each item |
