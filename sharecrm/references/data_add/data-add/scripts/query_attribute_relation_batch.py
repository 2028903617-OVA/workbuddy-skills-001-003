#!/usr/bin/env python3
"""批量按产品 ID 查询 ProductAttributeRelationObj，获取属性关联信息。

入参是 JSON 对象：
    {"product_ids": ["<产品ID1>", "<产品ID2>"]}

脚本内部用转义后的值拼出 IN(...) SQL，调用 sharecrm data record query-by-sql，
支持分页查询，自动循环获取所有数据后再按 product_id 分组返回。

该脚本提供可导入的通用方法 call_query_by_sql，供其他模块复用。

用法:
    python query_attribute_relation_batch.py --data '{"product_ids":["69e9...","69e8..."]}'

返回格式:
{
  "groups": {
    "<产品ID1>": [
      {
        "_id": "<记录ID>",
        "product_id": "<产品ID>",
        "attribute_id": "<属性ID>",
        "attribute_value_ids": "<属性值ID1>|<属性值ID2>",
        "is_required": true,
        "is_multi_selected": true,
        "is_pricing": false,
        "order_number": 1
      }
    ]
  },
  "total": 10
}
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys


# 查询字段
SELECT_FIELDS = "_id, product_id, attribute_id, attribute_value_ids, is_required, is_multi_selected, is_pricing, order_number"
RESULT_LIMIT = 2000


def resolve_sharecrm_command() -> list[str]:
    """定位 sharecrm 可执行文件，Windows 下兼容 .cmd/.bat 包装。"""
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


def sql_quote(value: str) -> str:
    """SQL 字符串字面量：单引号包裹，内部单引号翻倍转义，避免注入/语法错误。"""
    return "'" + str(value).replace("'", "''") + "'"


def normalize_product_ids(value) -> list[str]:
    """把 value 归一化为去空白、去重保序的产品 ID 列表。value 可为字符串或字符串数组。"""
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        raise ValueError("product_ids 必须是字符串或字符串数组")
    ids: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str):
            raise ValueError("产品 ID 必须是字符串")
        item = item.strip()
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            ids.append(item)
    return ids


def call_query_by_sql(sql: str, need_count: bool = True, raw: bool = True, search_after: list = None) -> dict:
    """通用方法：调用 sharecrm data record query-by-sql，返回解析后的 dict 或 {"error": ...}。

    该方法是通用的 SQL 查询方法，可被其他 Python 模块导入并复用。

    入参:
        sql: 完整的 SQL 查询语句
        need_count: 是否返回总数，默认为 True
        raw: 是否使用 raw 格式返回，默认为 True
        search_after: 分页游标，用于获取下一批数据，格式为 [product_id, create_time, _id]

    返回:
        成功时返回解析后的 dict（可能包含 records 字段和 queryMeta 信息）
        失败时返回 {"error": "错误描述"}
    """
    cmd = resolve_sharecrm_command() + ["data", "record", "query-by-sql"]
    if need_count:
        cmd.append("--need_count")
        cmd.append("true")
    if raw:
        cmd.append("--raw")
    if search_after:
        cmd.append("--search_after")
        cmd.append(json.dumps(search_after))
    cmd.append("--sql")
    cmd.append(sql)

    try:
        completed = subprocess.run(
            cmd,
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

    stdout = (completed.stdout or "").strip()
    if not stdout:
        return {"error": "CLI 无返回内容"}

    try:
        resp = json.loads(stdout)
    except json.JSONDecodeError:
        # JSON 解析失败，检查是否包含错误信息
        if "errorCode" in stdout or "errorMsg" in stdout:
            # 提取错误信息
            import re
            error_msg = ""
            match = re.search(r'errorMsg[：:]\s*([^\n]+)', stdout)
            if match:
                error_msg = match.group(1).strip()
            else:
                match = re.search(r'"errorMsg"\s*:\s*"([^"]+)"', stdout)
                if match:
                    error_msg = match.group(1).strip()
            return {"error": error_msg or "SQL 执行失败"}
        return {"error": "返回非 JSON 响应"}

    # 兼容 {"code":0,"data":{...}} 包装
    if isinstance(resp, dict) and "code" in resp:
        if resp.get("code") != 0:
            return {"error": resp.get("message") or "未知错误"}
        resp = resp.get("data") or {}

    # 检查是否有 errorCode
    if isinstance(resp, dict) and resp.get("errorCode"):
        return {"error": resp.get("errorMsg") or "SQL 执行失败"}

    return resp if isinstance(resp, dict) else {}


def extract_records(resp: dict) -> list[dict]:
    """从 query-by-sql 返回中抽取 records 列表，兼容多种包装形态。"""
    if not isinstance(resp, dict):
        return []
    for key in ("recordResult", "record_result"):
        result = resp.get(key)
        if isinstance(result, list):
            return [r for r in result if isinstance(r, dict)]
        if isinstance(result, dict) and isinstance(result.get("records"), list):
            return [r for r in result["records"] if isinstance(r, dict)]
    if isinstance(resp.get("records"), list):
        return [r for r in resp["records"] if isinstance(r, dict)]
    return []


def get_query_meta(resp: dict) -> dict:
    """从返回中抽取 queryMeta 信息。"""
    if not isinstance(resp, dict):
        return {}
    return resp.get("queryMeta", {})


def get_search_after_id(resp: dict) -> list:
    """从返回中抽取分页游标 searchAfterId。"""
    if not isinstance(resp, dict):
        return None
    record_result = resp.get("recordResult", {})
    if isinstance(record_result, dict):
        return record_result.get("searchAfterId")
    return None


def should_continue_paging(resp: dict) -> bool:
    """判断是否需要继续分页。"""
    meta = get_query_meta(resp)
    if not meta:
        return False
    # 如果 returnedCount < totalNumber，说明还有更多数据
    returned = meta.get("returnedCount", 0)
    total = meta.get("totalNumber", 0)
    limit_reached = meta.get("limitReached", False)
    return returned < total and not limit_reached


def group_by_product_id(product_ids: list[str], records: list[dict]) -> dict[str, list[dict]]:
    """按 product_id 分组命中记录。未命中的 key 对应空数组，便于上游做 0/1/多候选判定。"""
    groups: dict[str, list[dict]] = {pid: [] for pid in product_ids}
    for record in records:
        pid = record.get("product_id")
        if isinstance(pid, str) and pid in groups:
            groups[pid].append(record)
    return groups


def build_sql(product_ids: list[str]) -> str:
    """构建查询 ProductAttributeRelationObj 的 SQL。"""
    in_list = ", ".join(sql_quote(pid) for pid in product_ids)
    return (
        f"SELECT {SELECT_FIELDS} FROM ProductAttributeRelationObj "
        f"WHERE product_id IN ({in_list}) "
        f"ORDER BY product_id, create_time LIMIT {RESULT_LIMIT}"
    )


def query_all_records(product_ids: list[str]) -> tuple[list[dict], str]:
    """分页查询所有产品关联的属性记录。

    返回:
        (records, error_msg): 成功时返回 (所有记录列表, None)，失败时返回 ([], 错误信息)
    """
    sql = build_sql(product_ids)
    all_records: list[dict] = []
    search_after = None
    max_iterations = 100  # 防止无限循环
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        resp = call_query_by_sql(sql, search_after=search_after)

        if isinstance(resp, dict) and "error" in resp:
            return [], resp["error"]

        records = extract_records(resp)
        all_records.extend(records)

        # 检查是否需要继续分页
        if not should_continue_paging(resp):
            break

        # 获取下一页游标
        search_after = get_search_after_id(resp)
        if not search_after:
            break

    return all_records, None


def main() -> None:
    parser = argparse.ArgumentParser(description="批量按产品 ID 查询 ProductAttributeRelationObj")
    parser.add_argument(
        "--data",
        required=True,
        help='JSON：{"product_ids":[...]}',
    )
    args = parser.parse_args()

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as exc:
        sys.exit(f"--data 不是合法 JSON：{exc}")

    if not isinstance(data, dict):
        sys.exit("--data 必须是 JSON 对象")
    if "product_ids" not in data:
        sys.exit("--data 必须包含 product_ids")

    try:
        product_ids = normalize_product_ids(data["product_ids"])
    except ValueError as exc:
        sys.exit(f"--data 取值非法：{exc}")

    if not product_ids:
        # 空输入不发起 SQL 调用（IN() 为非法 SQL），直接返回空分组。
        print(json.dumps({"groups": {}, "total": 0}, ensure_ascii=False))
        return

    records, error_msg = query_all_records(product_ids)
    if error_msg:
        print(json.dumps({"error": error_msg}, ensure_ascii=False))
        return

    groups = group_by_product_id(product_ids, records)
    print(json.dumps({"groups": groups, "total": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
