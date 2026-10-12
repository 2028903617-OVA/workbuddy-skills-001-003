#!/usr/bin/env python3
"""批量解析产品 ID。

脚本只执行已经由 Skill 判定好的查询任务，不负责理解用户语义或字段映射。
每个 item 表示一个产品解析单元，可使用 query-id-by-name 或 query-by-fields。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


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


def unwrap_response(resp: Any) -> Any:
    if isinstance(resp, dict) and "code" in resp:
        if resp.get("code") != 0:
            raise ValueError(resp.get("message") or "未知错误")
        return resp.get("data") or {}
    return resp


def run_sharecrm(args: list[str]) -> Any:
    try:
        completed = subprocess.run(
            resolve_sharecrm_command() + args,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise RuntimeError("找不到 sharecrm 命令，请确认 CLI 已安装并在 PATH 中。") from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or str(exc)).strip()
        raise RuntimeError(f"CLI 调用失败：{details}") from exc

    raw = (completed.stdout or "").strip()
    if not raw:
        raise RuntimeError("CLI 无返回内容")

    try:
        return unwrap_response(json.loads(raw))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"返回非法 JSON：{exc}") from exc


def normalize_select_fields(value: Any) -> str:
    if value is None:
        return "_id,name"
    if isinstance(value, str):
        fields = [field.strip() for field in value.split(",") if field.strip()]
    elif isinstance(value, list):
        fields = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("select_fields 必须是字符串或字符串数组")
            item = item.strip()
            if item:
                fields.append(item)
    else:
        raise ValueError("select_fields 必须是字符串或字符串数组")

    required_fields = ["_id", "name"]
    merged_fields = required_fields + [field for field in fields if field not in required_fields]
    return ",".join(dict.fromkeys(merged_fields))


def extract_id(record: dict[str, Any]) -> Any:
    return record.get("id") or record.get("_id") or record.get("dataId")


def extract_records_from_query_id_by_name(resp: Any) -> list[dict[str, Any]]:
    if not isinstance(resp, dict):
        return []
    records = resp.get("name2IdPos") or []
    if not isinstance(records, list):
        return []
    normalized: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        item = dict(record)
        item_id = extract_id(item)
        if item_id is not None:
            item["id"] = item_id
        normalized.append(item)
    return normalized


def find_record_list(resp: Any) -> list[dict[str, Any]]:
    if isinstance(resp, list):
        return [item for item in resp if isinstance(item, dict)]
    if not isinstance(resp, dict):
        return []

    for key in ("recordResult", "record_result"):
        value = resp.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    data = resp.get("data")
    if data is not resp:
        return find_record_list(data)
    return []


def extract_records_from_query_by_fields(resp: Any) -> list[dict[str, Any]]:
    records = find_record_list(resp)
    normalized: list[dict[str, Any]] = []
    for record in records:
        item = dict(record)
        item_id = extract_id(item)
        if item_id is not None:
            item["id"] = item_id
        normalized.append(item)
    return normalized


def status_for(records: list[dict[str, Any]]) -> str:
    if not records:
        return "NOT_FOUND"
    if len(records) == 1:
        return "UNIQUE"
    return "MULTIPLE"


def query_id_by_name(item: dict[str, Any]) -> dict[str, Any]:
    object_api_name = item.get("object_api_name") or "ProductObj"
    query = item.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query-id-by-name item 必须提供 query")
    query = query.strip()
    payload = json.dumps({"query": query, "apiNames": [object_api_name]}, ensure_ascii=False)
    resp = run_sharecrm(["data", "record", "query-id-by-name", "--data", payload])
    records = extract_records_from_query_id_by_name(resp)
    if records:
        return {"records": records, "totalSize": len(records), "resolved_by": "query-id-by-name"}

    fallback_result = query_by_fields(
        {
            "object_api_name": object_api_name,
            "filters": [{"field_api": "name", "operator": "like", "value": query}],
            "select_fields": ["_id", "name"],
            "limit": item.get("limit") or 10,
        }
    )
    fallback_result["resolved_by"] = "query-by-fields:name-like"
    return fallback_result


def query_by_fields(item: dict[str, Any]) -> dict[str, Any]:
    object_api_name = item.get("object_api_name") or "ProductObj"
    args = ["data", "record", "query-by-fields", "--object_api_name", object_api_name]
    filters = item.get("filters")
    if not isinstance(filters, list) or not filters:
        raise ValueError("query-by-fields item 必须提供 filters")

    for filter_item in filters:
        if not isinstance(filter_item, dict):
            raise ValueError("filters 每项必须是对象")
        field_api = filter_item.get("field_api") or filter_item.get("field")
        operator = (filter_item.get("operator") or "eq").lower()
        value = filter_item.get("value")
        if not isinstance(field_api, str) or not field_api.strip():
            raise ValueError("filter 必须提供 field_api")
        if operator not in {"eq", "like"}:
            raise ValueError("operator 只支持 eq 或 like")
        if value is None:
            raise ValueError("filter 必须提供 value")
        args.extend([f"--{field_api.strip()}-{operator}", str(value)])

    args.extend(["--select_fields", normalize_select_fields(item.get("select_fields"))])
    args.extend(["--limit", str(item.get("limit") or 10)])
    resp = run_sharecrm(args)
    records = extract_records_from_query_by_fields(resp)
    return {"records": records, "totalSize": len(records)}


def resolve_one(item: dict[str, Any], index: int) -> dict[str, Any]:
    key = item.get("key") or f"item_{index + 1}"
    method = item.get("method")
    result: dict[str, Any] = {
        "key": key,
        "method": method,
        "object_api_name": item.get("object_api_name") or "ProductObj",
    }
    if "query" in item:
        result["query"] = item.get("query")
    if "filters" in item:
        result["filters"] = item.get("filters")

    try:
        if method == "query-id-by-name":
            query_result = query_id_by_name(item)
        elif method == "query-by-fields":
            query_result = query_by_fields(item)
        else:
            raise ValueError("method 只支持 query-id-by-name 或 query-by-fields")
        records = query_result["records"]
        result.update(query_result)
        result["status"] = status_for(records)
    except Exception as exc:  # noqa: BLE001 - 脚本需把单项错误回传给 Skill 处理
        result.update({"status": "ERROR", "totalSize": 0, "records": [], "error": str(exc)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="批量解析产品 ID")
    parser.add_argument("--data", required=True, help='JSON，格式为 {"items":[...]}')
    args = parser.parse_args()

    try:
        payload = json.loads(args.data)
    except json.JSONDecodeError as exc:
        sys.exit(f"--data 不是合法 JSON：{exc}")
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        sys.exit('--data 必须是 JSON 对象，且包含数组字段 "items"')

    items = payload["items"]
    indexed_items: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            sys.exit("items 每项必须是对象")
        indexed_items.append((index, item))

    results: list[dict[str, Any]] = [None] * len(indexed_items)  # type: ignore[list-item]
    if indexed_items:
        with ThreadPoolExecutor(max_workers=min(len(indexed_items), 8)) as executor:
            futures = {
                executor.submit(resolve_one, item, index): index
                for index, item in indexed_items
            }
            for future in as_completed(futures):
                results[futures[future]] = future.result()

    print(json.dumps({"items": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
