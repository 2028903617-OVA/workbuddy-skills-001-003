#!/usr/bin/env python3
"""批量按名称查询多个关联对象的记录 ID。

入参是 Map，key 为 object_api_name（关联对象的 apiName），value 为查询关键词。value 既
可以是单个关键词字符串，也可以是关键词数组——用数组来表达「同一个关联对象需要查多个名称」
（例如表单里有两个人员字段都指向 PersonnelObj），避免 JSON 重复 key 互相覆盖。

对每个 (apiName, 关键词) 并发调用 sharecrm data record query-id-by-name；结果按对象
apiName 汇总，同一对象下多个关键词的命中合并进同一个 name2IdPos（形如
{"totalSize":N,"name2IdPos":[{"apiName":...,"name":...,"id":...}]}），由调用方据此判断
唯一命中/多命中/未命中——多命中时务必交用户确认，不要默认选第一条。单个关键词查询失败时
记入该对象结果的 errors 字段。单关键词写法的输出与旧版完全一致。

用法:
    # 单关键词（向后兼容）
    python query_id_by_name_batch.py --data '{"AccountObj":"王小二","PersonnelObj":"张三"}'
    # 同一对象多个关键词
    python query_id_by_name_batch.py --data '{"PersonnelObj":["高光荣","金典"],"AccountObj":"王小二"}'
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


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


def normalize_queries(value) -> list[str]:
    """把 value 归一化为关键词列表，去掉空白项。value 可为字符串或字符串数组。"""
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        raise ValueError("value 必须是字符串或字符串数组")
    queries: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise ValueError("关键词必须是字符串")
        item = item.strip()
        if item:
            queries.append(item)
    return queries


def merge_results(api_name: str, pairs: list[tuple[str, dict]]) -> dict:
    """合并同一对象下多个关键词的查询结果。

    pairs: [(关键词, query_one 返回的 resp), ...]
    成功命中合并进 name2IdPos（按 id 去重）；失败的关键词记入 errors。
    单关键词且成功时，输出与旧版完全一致（无 errors 字段）。
    """
    merged: dict = {"totalSize": 0, "name2IdPos": []}
    seen_ids: set[str] = set()
    errors: list[dict] = []
    for query, resp in pairs:
        if isinstance(resp, dict) and resp.get("error"):
            errors.append({"query": query, "error": resp["error"]})
            continue
        merged["totalSize"] += (resp or {}).get("totalSize", 0) or 0
        for pos in (resp or {}).get("name2IdPos", []) or []:
            pos_id = pos.get("id") if isinstance(pos, dict) else None
            if pos_id is not None and pos_id in seen_ids:
                continue
            if pos_id is not None:
                seen_ids.add(pos_id)
            merged["name2IdPos"].append(pos)
    if errors:
        merged["errors"] = errors
    return merged


def query_one(api_name: str, query: str) -> tuple[str, dict]:
    payload = json.dumps({"query": query, "apiNames": [api_name]}, ensure_ascii=False)
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
        return api_name, {"error": "找不到 sharecrm 命令，请确认 CLI 已安装并在 PATH 中。"}
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or str(exc)).strip()
        return api_name, {"error": f"CLI 调用失败：{details}"}

    raw = (completed.stdout or "").strip()
    if not raw:
        return api_name, {"error": "CLI 无返回内容"}

    try:
        resp = json.loads(raw)
    except json.JSONDecodeError as exc:
        return api_name, {"error": f"返回非法 JSON：{exc}"}

    # 兼容 {"code":0,"data":{...}} 包装
    if isinstance(resp, dict) and "code" in resp:
        if resp.get("code") != 0:
            return api_name, {"error": resp.get("message") or "未知错误"}
        return api_name, resp.get("data") or {}

    return api_name, resp


def main() -> None:
    parser = argparse.ArgumentParser(description="批量查询多个关联对象的记录 ID")
    parser.add_argument("--data", required=True, help='JSON Map，key=object_api_name，value=查询关键词（字符串或字符串数组）')
    args = parser.parse_args()

    try:
        query_map = json.loads(args.data)
    except json.JSONDecodeError as exc:
        sys.exit(f"--data 不是合法 JSON：{exc}")

    if not isinstance(query_map, dict):
        sys.exit("--data 必须是 JSON 对象（Map）")

    # 归一化：每个对象 apiName → 关键词列表
    tasks: list[tuple[str, str]] = []
    try:
        for api_name, value in query_map.items():
            for query in normalize_queries(value):
                tasks.append((api_name, query))
    except ValueError as exc:
        sys.exit(f"--data 取值非法：{exc}")

    # 按对象 apiName 聚合各关键词的结果，保持入参出现顺序
    pairs_by_api: dict[str, list[tuple[str, dict]]] = {api_name: [] for api_name, _ in tasks}

    if tasks:
        with ThreadPoolExecutor(max_workers=min(len(tasks), 8)) as executor:
            futures = {
                executor.submit(query_one, api_name, query): (api_name, query)
                for api_name, query in tasks
            }
            for future in as_completed(futures):
                api_name, query = futures[future]
                _, resp = future.result()
                pairs_by_api[api_name].append((query, resp))

    results = {api_name: merge_results(api_name, pairs) for api_name, pairs in pairs_by_api.items()}

    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
