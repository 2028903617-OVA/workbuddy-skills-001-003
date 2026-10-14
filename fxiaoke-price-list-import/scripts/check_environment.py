#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""环境只读检查。

检查项分两组：
  · **通用**（python / openpyxl）—— 三个能力都要
  · **能力 1 专用**（node / sharecrm CLI / OpenAPI 凭证文件）—— 实时查 + 直写
  · **能力 2 / 3 专用**（产品快照 / 明细快照，标 optional=True）—— 底表匹配

★ v1.9.0：能力 1 已不用快照，快照缺失**不影响能力 1**。

输出 JSON: {"status": "ready|partial|needs_setup", "checks": [...]}
只读取状态，不安装、不联网、不修改任何配置。
"""
import glob
import json
import os
import sys

DOWNLOADS = r"D:\Backup\Downloads"

# 能力 1 依赖路径（与 query_pricebook.py 保持一致）
NODE_CANDIDATES = [
    r"C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-6/node.exe",
    r"C:/Users/Administrator/.workbuddy/binaries/node/versions/22.12.0/node.exe",
]
CLI_JS = (r"C:/Users/Administrator/.workbuddy/binaries/node/workspace/"
          r"node_modules/@share-crm/sharecrm-cli/dist/index.js")
CRED_FILE = r"C:/Users/Administrator/.workbuddy/fxiaoke-app-003.json"


def _header_and_row2(path):
    """读表头与第 2 行。read_only 下 dimension 损坏的导出文件会只读到 1 列
    （实测 09-21 产品快照 max_column=1），列数 < 3 时回退非只读模式。"""
    import openpyxl
    for read_only in (True, False):
        try:
            wb = openpyxl.load_workbook(path, read_only=read_only, data_only=True)
            ws = wb[wb.sheetnames[0]]
            hdr = row2 = None
            for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
                hdr = [str(h) if h is not None else "" for h in row]
            for row in ws.iter_rows(min_row=2, max_row=2, values_only=True):
                row2 = list(row)
            wb.close()
            if hdr and len(hdr) >= 3:
                return hdr, row2
        except Exception:
            continue
    return None, None


def find_snapshot(pattern, required_cols):
    files = sorted(glob.glob(os.path.join(DOWNLOADS, pattern)), reverse=True)
    for f in files:
        if os.path.basename(f).startswith("~$"):
            continue
        hdr, row2 = _header_and_row2(f)
        if hdr is None:
            continue
        ok = all(c in hdr for c in required_cols)
        if ok and (not row2 or row2[0] is None or str(row2[0]).strip() == ""):
            ok = False
        if ok:
            return f
    return None


def main():
    checks = []

    ver = sys.version_info
    py_ok = ver >= (3, 10)
    checks.append({"id": "python", "ok": py_ok, "affects": "全部",
                   "detail": "Python %d.%d.%d" % (ver.major, ver.minor, ver.micro)})

    openpyxl_ok, openpyxl_detail = False, "未安装"
    try:
        import openpyxl
        openpyxl_ok = True
        openpyxl_detail = "openpyxl %s" % openpyxl.__version__
    except ImportError:
        pass
    checks.append({"id": "openpyxl", "ok": openpyxl_ok, "affects": "全部",
                   "detail": openpyxl_detail})

    # ---- 能力 1 专用：实时查 + 直写 ----
    node = next((p for p in NODE_CANDIDATES if os.path.isfile(p)), None)
    checks.append({"id": "node", "ok": node is not None, "affects": "能力 1",
                   "detail": node or "找不到 node.exe（候选：%s）" % "; ".join(NODE_CANDIDATES)})

    cli_ok = node is not None and os.path.isfile(CLI_JS)
    checks.append({"id": "sharecrm-cli", "ok": cli_ok, "affects": "能力 1（实时查）",
                   "detail": CLI_JS if cli_ok else "找不到 sharecrm CLI：%s" % CLI_JS})

    cred_ok = os.path.isfile(CRED_FILE)
    checks.append({"id": "openapi-cred", "ok": cred_ok, "affects": "能力 1（直写）",
                   "detail": CRED_FILE if cred_ok else "找不到凭证文件：%s" % CRED_FILE})

    # ---- 能力 2 / 3 专用：快照（★ optional，不影响能力 1）----
    prod = find_snapshot("产品对象导出结果_*.xlsx", ["产品名称（必填）", "物料名称"])
    checks.append({"id": "product-snapshot", "ok": prod is not None, "optional": True,
                   "affects": "能力 2/3（能力 1 不需要）",
                   "detail": prod or "Downloads 下找不到含必需列且有数据的产品对象导出"})

    det = find_snapshot("价目表明细对象导出结果_*.xlsx", ["产品（必填）", "价目表（必填）"])
    checks.append({"id": "detail-snapshot", "ok": det is not None, "optional": True,
                   "affects": "能力 2/3（能力 1 不需要）",
                   "detail": det or "Downloads 下找不到含必需列且有数据的价目表明细导出"})

    ability1_ready = node is not None and cli_ok and cred_ok
    snapshots_ready = prod is not None and det is not None

    if not py_ok or not openpyxl_ok:
        status = "needs_setup"
    elif ability1_ready and snapshots_ready:
        status = "ready"
    else:
        status = "partial"

    print(json.dumps({"status": status, "checks": checks,
                      "summary": {
                          "能力1": "ready" if ability1_ready else "缺少依赖",
                          "能力2/3": "ready" if snapshots_ready else "快照缺失（降级）",
                      }}, ensure_ascii=False, indent=2))
    sys.exit(0 if status in ("ready", "partial") else 1)


if __name__ == "__main__":
    main()
