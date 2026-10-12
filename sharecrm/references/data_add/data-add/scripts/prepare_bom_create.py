#!/usr/bin/env python3
"""BomCoreObj 新建前置：批量解析产品 ID，并补齐明细字段。

把 skill 里确定性的两段逻辑收敛到脚本：
1. 查 ProductObj：父项 + 非分组子件（分组不查产品）
2. 补字段：amount / adjust_price / price_mode / order_field / rowId / parent_rowId /
   分组标记（isGroup/isFake/label），并做 level_key 完整性校验、生成树形预览

Agent 只负责从用户输入里拆出父项与子件清单（含分组识别、level_key），再调本脚本；
未唯一命中产品、层级断裂时按 status 停下来问用户，不要猜。

入参 --data：
{
  "parent": {"name": "父项产品名"} | {"product_id": "<已确认ID>"},
  "children": [
    {
      "name": "子件或分组名",          // 展示名；分组必填（作 label）
      "product_id": "<可选，已确认ID>", // 有则不再按 name 查
      "level_key": "1.1",             // 可选；有则校验父子完整性
      "amount": 1,                    // 可选；产品缺省 1，分组强制 null
      "adjust_price": 0,              // 可选；受 price_mode 约束
      "price_mode": "1"|"2",          // 可选；1=配置价格，2=价目表价格
      "isGroup": false                // true 时为分组，不查产品
    }
  ]
}

用法:
    python prepare_bom_create.py --data '{"parent":{"name":"wsh组合"},"children":[...]}'
    python prepare_bom_create.py --data @payload.json

返回 status：
    READY                    —— 可进入创建前确认（含 object_data / details / preview）
    PRODUCT_NOT_RESOLVED     —— 父项或子件产品未命中/多命中，需用户确认
    LEVEL_BROKEN             —— level_key 父子断裂
    EMPTY_CHILDREN           —— 子件为空
    INVALID_INPUT / ERROR    —— 入参或 CLI 异常
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


PRICE_MODE_CONFIG = "1"  # 配置价格：回填源文件价格
PRICE_MODE_LIST = "2"  # 价目表价格：adjust_price 强制 null


def resolve_sharecrm_command() -> list[str]:
    executable = shutil.which("sharecrm")
    if executable:
        if os.name == "nt" and executable.lower().endswith((".cmd", ".bat")):
            return ["cmd", "/c", executable]
        return [executable]
    if os.name == "nt":
        for candidate in ("sharecrm.exe", "sharecrm.cmd", "sharecrm.bat"):
            executable = shutil.which(candidate)
            if executable:
                if executable.lower().endswith((".cmd", ".bat")):
                    return ["cmd", "/c", executable]
                return [executable]
        return ["cmd", "/c", "sharecrm"]
    return ["sharecrm"]


def load_json_argument(raw: str, label: str) -> Any:
    value = raw.strip()
    if value.startswith("@"):
        value = Path(value[1:]).read_text(encoding="utf-8-sig")
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} 不是合法 JSON：{exc}") from exc


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def is_group_item(item: dict) -> bool:
    return bool(item.get("isGroup") or item.get("is_group"))


def item_display_name(item: dict) -> str:
    for key in ("name", "label", "product_name", "product_id__r"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def query_product_by_name(query: str) -> dict:
    """调用 sharecrm data record query-id-by-name 查 ProductObj。"""
    payload = json.dumps({"query": query, "apiNames": ["ProductObj"]}, ensure_ascii=False)
    try:
        completed = subprocess.run(
            resolve_sharecrm_command() + ["data", "record", "query-id-by-name", "--data", payload],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return {"error": "找不到 sharecrm 命令，请确认 CLI 已安装并在 PATH 中。"}
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or str(exc)).strip()
        return {"error": f"CLI 调用失败：{details}"}

    raw = (completed.stdout or "").strip()
    if not raw:
        return {"error": "CLI 无返回内容"}

    try:
        resp = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"error": f"返回非法 JSON：{exc}"}

    if isinstance(resp, dict) and "code" in resp:
        if resp.get("code") != 0:
            return {"error": resp.get("message") or "未知错误"}
        return resp.get("data") or {}
    return resp if isinstance(resp, dict) else {}


def resolve_product_hits(query: str, resp: dict) -> dict:
    """把 query-id-by-name 结果归一成统一命中结构。"""
    if resp.get("error"):
        return {"query": query, "status": "ERROR", "error": resp["error"], "candidates": []}

    positions = resp.get("name2IdPos") or []
    candidates = []
    for pos in positions:
        if not isinstance(pos, dict):
            continue
        pid = pos.get("id")
        if not pid:
            continue
        candidates.append({"id": str(pid), "name": pos.get("name") or query})

    if len(candidates) == 0:
        return {"query": query, "status": "NOT_FOUND", "candidates": []}
    if len(candidates) == 1:
        return {
            "query": query,
            "status": "RESOLVED",
            "product_id": candidates[0]["id"],
            "product_name": candidates[0]["name"],
            "candidates": candidates,
        }
    return {"query": query, "status": "MULTI", "candidates": candidates}


def batch_resolve_products(queries: list[str]) -> dict[str, dict]:
    """并发按名称解析产品；同名只查一次。"""
    unique: list[str] = []
    seen: set[str] = set()
    for q in queries:
        q = (q or "").strip()
        if not q or q in seen:
            continue
        seen.add(q)
        unique.append(q)

    results: dict[str, dict] = {}
    if not unique:
        return results

    with ThreadPoolExecutor(max_workers=min(len(unique), 8)) as executor:
        futures = {executor.submit(query_product_by_name, q): q for q in unique}
        for future in as_completed(futures):
            q = futures[future]
            results[q] = resolve_product_hits(q, future.result())
    return results


def parent_level_key(level_key: str) -> str | None:
    """取直接父层级；一级返回 None。"""
    text = str(level_key).strip()
    if not text or "." not in text:
        return None
    return text.rsplit(".", 1)[0]


def validate_level_keys(children: list[dict]) -> list[dict]:
    """校验 level_key 父子完整性，返回断裂问题列表。

    约定：`1` / `1.1` / `1.2` 这类深度 ≤1（点号个数 ≤1）可作为一级节点，
    不要求存在父层级；深度 ≥2（如 `1.2.1`、`1.4.1`）必须在同批存在直接父层级。
    """
    keys = {
        str(item["level_key"]).strip()
        for item in children
        if item.get("level_key") not in (None, "")
    }
    issues: list[dict] = []
    for idx, item in enumerate(children):
        lk = item.get("level_key")
        if lk in (None, ""):
            continue
        lk = str(lk).strip()
        # 一级（无点）或伪一级（仅一段点号，如 1.1）不强制父节点
        if lk.count(".") <= 1:
            continue
        parent = parent_level_key(lk)
        if parent is None or parent in keys:
            continue
        name = item_display_name(item) or f"第{idx + 1}行"
        issues.append(
            {
                "index": idx,
                "name": name,
                "level_key": lk,
                "missing_parent": parent,
                "message": (
                    f"层级校验未通过：子件「{name}」的 level_key 为 {lk}，"
                    f"但缺少父层级 {parent} 对应节点。请补全父节点或修正层级后重试。"
                ),
            }
        )
    return issues


def apply_price_fields(item: dict, is_group: bool) -> tuple[Any, Any]:
    """按分组与 price_mode 规则回填 amount / adjust_price。"""
    if is_group:
        return None, None

    amount = item.get("amount")
    if amount is None or amount == "":
        amount = 1

    price_mode = item.get("price_mode")
    if price_mode is not None:
        price_mode = str(price_mode).strip()

    if price_mode == PRICE_MODE_LIST:
        return amount, None

    adjust_price = item.get("adjust_price")
    if price_mode == PRICE_MODE_CONFIG:
        # 配置价格：以源文件价格回填；未给则保持 None（不默认 0）
        if adjust_price is None or adjust_price == "":
            return amount, None
        return amount, adjust_price

    # 未指定定价模式：缺省 adjust_price=0
    if adjust_price is None or adjust_price == "":
        adjust_price = 0
    return amount, adjust_price


def assign_order_fields(children: list[dict]) -> None:
    """同级兄弟（含分组）按来源顺序从 1 编号。"""
    has_level = any(item.get("level_key") not in (None, "") for item in children)
    if not has_level:
        for i, item in enumerate(children, start=1):
            item["order_field"] = str(i)
        return

    buckets: dict[str | None, list[dict]] = {}
    for item in children:
        lk = item.get("level_key")
        parent = parent_level_key(str(lk).strip()) if lk not in (None, "") else None
        buckets.setdefault(parent, []).append(item)

    for siblings in buckets.values():
        for seq, item in enumerate(siblings, start=1):
            item["order_field"] = str(seq)


def assign_row_ids_and_parents(children: list[dict]) -> None:
    """生成 rowId；有 level_key 时为非一级节点写 parent_rowId。"""
    base = int(time.time() * 1000)
    level_to_row: dict[str, str] = {}

    for idx, item in enumerate(children):
        row_id = item.get("rowId") or f"{base}{idx + 1:03d}"
        item["rowId"] = str(row_id)
        lk = item.get("level_key")
        if lk not in (None, ""):
            level_to_row[str(lk).strip()] = item["rowId"]

    for item in children:
        lk = item.get("level_key")
        if lk in (None, ""):
            item.pop("parent_rowId", None)
            continue
        parent = parent_level_key(str(lk).strip())
        if parent is None:
            item.pop("parent_rowId", None)
            continue
        parent_row = level_to_row.get(parent)
        if parent_row:
            item["parent_rowId"] = parent_row
        else:
            item.pop("parent_rowId", None)


def build_preview(parent_name: str, children: list[dict]) -> str:
    lines = [f"父项：{parent_name}", "子件树："]
    for item in children:
        lk = item.get("level_key")
        # 与层级约定一致：点号个数 ≤1 视为一级（缩进 0）；更深按点号-1 缩进
        if lk in (None, ""):
            depth = 0
        else:
            dots = str(lk).count(".")
            depth = 0 if dots <= 1 else dots - 1
        indent = "  " * depth
        name = item_display_name(item) or "(未命名)"
        order_field = item.get("order_field", "")
        amount = item.get("amount")
        adjust_price = item.get("adjust_price")
        amount_text = "" if amount is None else amount
        price_text = "" if adjust_price is None else adjust_price
        lk_text = lk if lk not in (None, "") else "-"
        lines.append(
            f"{indent}- [{lk_text}] {name} 序号={order_field} | 数量={amount_text} | 选配价格={price_text}"
        )
    return "\n".join(lines)


def collect_defaults_used(raw_children: list[dict], enriched: list[dict]) -> list[dict]:
    defaults: list[dict] = []
    for idx, (raw, out) in enumerate(zip(raw_children, enriched)):
        if is_group_item(raw):
            continue
        if raw.get("amount") in (None, "") and out.get("amount") == 1:
            defaults.append({"index": idx, "field": "amount", "value": 1})
        price_mode = str(raw.get("price_mode") or "").strip()
        if price_mode not in (PRICE_MODE_LIST, PRICE_MODE_CONFIG):
            if raw.get("adjust_price") in (None, "") and out.get("adjust_price") == 0:
                defaults.append({"index": idx, "field": "adjust_price", "value": 0})
    return defaults


def enrich_pipeline(
    children: list[dict],
    product_map: dict[str, dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """补齐字段；返回 (enriched_for_submit, working_with_level_for_preview, unresolved)。"""
    working: list[dict] = []
    unresolved: list[dict] = []

    for idx, raw in enumerate(children):
        item = dict(raw)
        group = is_group_item(item)
        name = item_display_name(item)

        amount, adjust_price = apply_price_fields(item, group)
        item["amount"] = amount
        item["adjust_price"] = adjust_price

        if item.get("price_mode") is not None:
            item["price_mode"] = str(item["price_mode"]).strip()

        if group:
            item["isGroup"] = True
            item["isFake"] = True
            item["label"] = name or item.get("label") or f"分组{idx + 1}"
            item.pop("product_id", None)
        else:
            item.pop("isGroup", None)
            item.pop("isFake", None)
            existing_id = item.get("product_id")
            if isinstance(existing_id, str) and existing_id.strip():
                item["product_id"] = existing_id.strip()
                if name:
                    item["product_id__r"] = name
                    item["label"] = name
            elif not name:
                unresolved.append(
                    {
                        "index": idx,
                        "role": "child",
                        "query": "",
                        "status": "NOT_FOUND",
                        "candidates": [],
                        "message": f"第{idx + 1}条子件缺少产品名称或 product_id",
                    }
                )
            else:
                hit = product_map.get(name) or {
                    "query": name,
                    "status": "NOT_FOUND",
                    "candidates": [],
                }
                if hit.get("status") == "RESOLVED":
                    item["product_id"] = hit["product_id"]
                    item["product_id__r"] = hit.get("product_name") or name
                    item["label"] = hit.get("product_name") or name
                else:
                    unresolved.append(
                        {
                            "index": idx,
                            "role": "child",
                            "query": name,
                            "status": hit.get("status"),
                            "error": hit.get("error"),
                            "candidates": hit.get("candidates") or [],
                            "message": (
                                f"子件「{name}」产品未唯一命中（{hit.get('status')}），请确认后重试。"
                            ),
                        }
                    )

        working.append(item)

    assign_order_fields(working)
    assign_row_ids_and_parents(working)

    # 提交副本：删除中间字段 level_key / name
    submit: list[dict] = []
    for item in working:
        out = dict(item)
        out.pop("level_key", None)
        out.pop("name", None)
        out.pop("is_group", None)
        submit.append(out)

    return submit, working, unresolved


def normalize_input(data: dict) -> tuple[dict, list[dict]]:
    parent = data.get("parent")
    children = data.get("children")
    if not isinstance(parent, dict):
        raise ValueError('parent 必须是对象，如 {"name":"..."} 或 {"product_id":"..."}')
    if not isinstance(children, list):
        raise ValueError("children 必须是数组")
    normalized_children: list[dict] = []
    for idx, child in enumerate(children):
        if not isinstance(child, dict):
            raise ValueError(f"children[{idx}] 必须是对象")
        normalized_children.append(dict(child))
    return dict(parent), normalized_children


def main() -> None:
    parser = argparse.ArgumentParser(description="BomCoreObj 新建前置：查产品并补齐明细字段")
    parser.add_argument(
        "--data",
        required=True,
        help='JSON 或 @文件路径：{"parent":{...},"children":[...]}',
    )
    args = parser.parse_args()

    data = load_json_argument(args.data, "--data")
    if not isinstance(data, dict):
        emit({"status": "INVALID_INPUT", "error": "--data 必须是 JSON 对象"})
        return

    try:
        parent, children = normalize_input(data)
    except ValueError as exc:
        emit({"status": "INVALID_INPUT", "error": str(exc)})
        return

    if not children:
        emit({"status": "EMPTY_CHILDREN", "error": "子件为 0 条，请补充子件后再试。"})
        return

    level_issues = validate_level_keys(children)
    if level_issues:
        emit(
            {
                "status": "LEVEL_BROKEN",
                "error": level_issues[0]["message"],
                "level_issues": level_issues,
            }
        )
        return

    queries: list[str] = []
    parent_id = parent.get("product_id")
    parent_name = item_display_name(parent)
    if not (isinstance(parent_id, str) and parent_id.strip()):
        if not parent_name:
            emit(
                {
                    "status": "PRODUCT_NOT_RESOLVED",
                    "error": "父项产品缺少名称或 product_id",
                    "unresolved": [
                        {
                            "role": "parent",
                            "query": "",
                            "status": "NOT_FOUND",
                            "candidates": [],
                            "message": "父项产品缺少名称或 product_id",
                        }
                    ],
                }
            )
            return
        queries.append(parent_name)

    for child in children:
        if is_group_item(child):
            continue
        if isinstance(child.get("product_id"), str) and child["product_id"].strip():
            continue
        name = item_display_name(child)
        if name:
            queries.append(name)

    product_map = batch_resolve_products(queries)

    unresolved: list[dict] = []
    resolved_parent_id: str | None = None
    resolved_parent_name = parent_name or ""

    if isinstance(parent_id, str) and parent_id.strip():
        resolved_parent_id = parent_id.strip()
    else:
        hit = product_map.get(parent_name) or {
            "query": parent_name,
            "status": "NOT_FOUND",
            "candidates": [],
        }
        if hit.get("status") == "RESOLVED":
            resolved_parent_id = hit["product_id"]
            resolved_parent_name = hit.get("product_name") or parent_name
        else:
            unresolved.append(
                {
                    "role": "parent",
                    "query": parent_name,
                    "status": hit.get("status"),
                    "error": hit.get("error"),
                    "candidates": hit.get("candidates") or [],
                    "message": (
                        f"父项产品「{parent_name}」未唯一命中（{hit.get('status')}），请确认后重试。"
                    ),
                }
            )

    details, working, child_unresolved = enrich_pipeline(children, product_map)
    unresolved.extend(child_unresolved)
    preview = build_preview(resolved_parent_name or parent_name or "(父项)", working)

    if unresolved:
        emit(
            {
                "status": "PRODUCT_NOT_RESOLVED",
                "error": unresolved[0].get("message") or "存在未唯一命中的产品",
                "unresolved": unresolved,
                "preview": preview,
            }
        )
        return

    emit(
        {
            "status": "READY",
            "object_data": {
                "product_id": resolved_parent_id,
                "product_id__r": resolved_parent_name,
            },
            "details": {"BOMObj": details},
            "preview": preview,
            "defaults_used": collect_defaults_used(children, details),
            "trace_id": str(uuid.uuid4()),
        }
    )


if __name__ == "__main__":
    main()
