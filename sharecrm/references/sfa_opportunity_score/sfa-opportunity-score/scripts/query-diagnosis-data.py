#!/usr/bin/env python3
"""Query CRM facts for sfa-opportunity-diagnosis.

The script wraps the repeatable sharecrm read path used by the diagnosis skill:

1. resolve a NewOpportunityObj by id or name
2. query the full opportunity record
3. query account, contacts, contact relationships, sales records, competitors
4. optionally query quotes and quote lines

Output is always JSON. Required data failures are reported in `errors`; absent
optional data is represented as an empty list instead of being invented.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Any


ACCOUNT_FIELDS = [
    "_id",
    "name",
    "account_level",
    "industry",
    "industry_level1",
    "industry_level2",
    "owner",
    "customer_status",
    "region",
    "total_amount",
    "last_followed_time",
    "last_modified_time",
    "create_time",
]

OPPORTUNITY_CONTACT_FIELDS = [
    "_id",
    "new_opportunity_id",
    "contact_id",
    "role",
    "is_key_person",
    "decision_role",
    "influence_direction",
    "report_to",
    "support_degree",
    "last_modified_time",
]

CONTACT_RELATIONSHIP_FIELDS = [
    "_id",
    "name",
    "opportunity_id",
    "contact_id",
    "related_contact_id",
    "relationship_type",
    "influence_direction",
    "support_degree",
    "report_to",
    "decision_role",
    "remark",
    "last_modified_time",
]

QUOTE_FIELDS = [
    "_id",
    "name",
    "new_opportunity_id",
    "account_id",
    "owner",
    "quote_time",
    "quote_amount",
    "record_type",
    "last_modified_time",
]

QUOTE_LINE_FIELDS = [
    "_id",
    "quote_id",
    "product_id",
    "quantity",
    "price",
    "selling_price",
    "sales_price",
    "discount",
    "total_discount",
    "sales_amount",
    "total_amount",
    "last_modified_time",
]

ACTIVE_RECORD_FIELDS = [
    "_id",
    "active_record_content",
    "active_record_type",
    "new_opportunity_id",
    "create_time",
]

COMPETITIVE_LINE_FIELDS = [
    "_id",
    "name",
    "new_opportunity_id",
    "competitor",
    "our_advantage",
    "our_disadvantage",
    "competitor_quote_amount",
    "competitive_product",
    "remark",
    "last_modified_time",
]


class SharecrmError(Exception):
    """Raised when a sharecrm command cannot be completed."""


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def resolve_sharecrm_command() -> list[str]:
    if os.name == "nt":
        cmd_path = shutil.which("sharecrm.cmd") or shutil.which("sharecrm.bat")
        if cmd_path:
            base_dir = os.path.dirname(cmd_path)
            node_path = os.path.join(base_dir, "node.exe")
            script_path = os.path.join(
                base_dir, "node_modules", "@share-crm", "sharecrm-cli", "dist", "index.js"
            )
            if os.path.exists(node_path) and os.path.exists(script_path):
                return [node_path, script_path]
        for candidate in ("sharecrm.exe", "sharecrm"):
            executable = shutil.which(candidate)
            if executable and not executable.lower().endswith((".cmd", ".bat")):
                return [executable]
        for candidate in ("sharecrm.cmd", "sharecrm.bat"):
            executable = shutil.which(candidate)
            if executable:
                return ["cmd", "/c", executable]
        return ["cmd", "/c", "sharecrm"]

    executable = shutil.which("sharecrm")
    if executable:
        return [executable]

    return ["sharecrm"]


def run_sharecrm(args: list[str]) -> Any:
    command_desc = "sharecrm " + " ".join(args)
    command = resolve_sharecrm_command() + args
    max_attempts = 4

    for attempt in range(max_attempts):
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError as exc:
            raise SharecrmError("找不到 sharecrm 命令，请确认 CLI 已安装并在 PATH 中。") from exc
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or exc.stdout or str(exc)).strip()
            if "Failed to read session file" in details and attempt < max_attempts - 1:
                time.sleep(0.35 * (attempt + 1))
                continue
            raise SharecrmError(f"{command_desc} 调用失败：{details}") from exc

        raw = (completed.stdout or "").strip()
        if not raw:
            raise SharecrmError(f"{command_desc} 没有返回内容。")

        try:
            response = json.loads(raw)
        except json.JSONDecodeError as exc:
            if "Failed to read session file" in raw and attempt < max_attempts - 1:
                time.sleep(0.35 * (attempt + 1))
                continue
            if "errorCode：" in raw or "errorCode:" in raw:
                raise SharecrmError(f"{command_desc} 返回失败：{raw}") from exc
            raise SharecrmError(f"{command_desc} 返回不是合法 JSON：{exc}") from exc

        if isinstance(response, dict) and "code" in response:
            if response.get("code") != 0:
                message = response.get("message") or response.get("msg") or "未知错误"
                if (
                    "Failed to read session file" in str(message)
                    and attempt < max_attempts - 1
                ):
                    time.sleep(0.35 * (attempt + 1))
                    continue
                raise SharecrmError(f"{command_desc} 返回失败：{message}")
            return response.get("data")

        return response

    raise SharecrmError(f"{command_desc} 多次重试后仍失败。")


def describe_object(object_api_name: str) -> Any:
    payload = compact_json(
        {
            "query": object_api_name,
            "object_api_names": [object_api_name],
            "include_simple_describe": True,
        }
    )
    return run_sharecrm(
        ["data", "describe", "identify-with-describe", "--data", payload]
    )


def parse_described_fields(description: Any) -> set[str]:
    if not isinstance(description, dict):
        return set()

    for wrapper_key in (
        "object_describe",
        "objectDescribe",
        "simple_describe",
        "simpleDescribe",
        "describe",
        "data",
    ):
        wrapped = description.get(wrapper_key)
        if isinstance(wrapped, dict):
            names = parse_described_fields(wrapped)
            if names:
                return names

    for list_key in ("objects", "object_list", "objectList", "results", "list"):
        wrapped_list = description.get(list_key)
        if isinstance(wrapped_list, list):
            for item in wrapped_list:
                if isinstance(item, dict):
                    names = parse_described_fields(item)
                    if names:
                        return names

    for key in (
        "field_metadata",
        "fields",
        "fieldMetas",
        "field_metas",
        "field_list",
        "fieldList",
    ):
        raw = description.get(key)
        if isinstance(raw, dict):
            return {str(name) for name in raw if name}
        if isinstance(raw, list):
            names: set[str] = set()
            for item in raw:
                if not isinstance(item, dict):
                    continue
                for name_key in (
                    "field_api_name",
                    "fieldName",
                    "field_name",
                    "api_name",
                    "apiName",
                    "name",
                ):
                    value = item.get(name_key)
                    if isinstance(value, str) and value:
                        names.add(value)
                        break
            if names:
                return names

    return set()


def filter_fields(
    object_api_name: str,
    requested_fields: list[str],
    descriptions: dict[str, Any],
    errors: list[dict[str, str]],
) -> list[str]:
    if object_api_name not in descriptions:
        try:
            descriptions[object_api_name] = describe_object(object_api_name)
        except SharecrmError as exc:
            errors.append(
                {
                    "scope": f"describe:{object_api_name}",
                    "message": str(exc),
                }
            )
            return requested_fields

    described = parse_described_fields(descriptions[object_api_name])
    if not described:
        return requested_fields

    fields = [field for field in requested_fields if field in described]
    return fields or requested_fields


def query_by_fields(
    object_api_name: str,
    select_fields: list[str],
    eq_filters: dict[str, str],
    limit: int,
    sort: str | None,
    descriptions: dict[str, Any],
    errors: list[dict[str, str]],
) -> list[dict[str, Any]]:
    fields = filter_fields(object_api_name, select_fields, descriptions, errors)
    raw_args = [
        "data",
        "record",
        "query-by-fields",
        "--object_api_name",
        object_api_name,
        "--select_fields",
        ",".join(fields),
        "--limit",
        str(limit),
    ]
    for field, value in eq_filters.items():
        raw_args.extend([f"--{field}-eq", value])
    if sort:
        raw_args.extend(["--sort", sort])
    raw_args.append("--raw")

    return extract_records(run_sharecrm(raw_args))


def get_by_id(object_api_name: str, record_id: str) -> dict[str, Any] | None:
    payload = compact_json({"object_api_name": object_api_name, "id": record_id})
    data = run_sharecrm(
        [
            "data",
            "record",
            "get-by-id",
            "--raw",
            "--data",
            payload,
        ]
    )
    if isinstance(data, dict):
        record = data.get("record")
        if isinstance(record, dict):
            return record
        return data
    records = extract_records(data)
    return records[0] if records else None


def extract_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if not isinstance(value, dict):
        return []

    if any(key in value for key in ("_id", "id", "name")) and not any(
        isinstance(value.get(key), list)
        for key in ("records", "rows", "items", "list", "dataList")
    ):
        return [value]

    for key in (
        "recordResult",
        "record_result",
        "records",
        "rows",
        "items",
        "list",
        "dataList",
        "object_data",
        "objects",
        "result",
        "data",
    ):
        child = value.get(key)
        if isinstance(child, list):
            return [item for item in child if isinstance(item, dict)]
        if isinstance(child, dict):
            nested = extract_records(child)
            if nested:
                return nested

    return []


def first_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    return records[0] if records else None


def extract_id(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("_id", "id", "data_id", "dataId", "value"):
            nested = value.get(key)
            if nested:
                return str(nested).strip()
    return ""


def get_field_id(record: dict[str, Any] | None, *field_names: str) -> str:
    if not isinstance(record, dict):
        return ""
    for field_name in field_names:
        value = record.get(field_name)
        value_id = extract_id(value)
        if value_id:
            return value_id
    return ""


def get_text(record: dict[str, Any] | None, *field_names: str) -> str:
    if not isinstance(record, dict):
        return ""
    for field_name in field_names:
        value = record.get(field_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value is not None and not isinstance(value, (dict, list)):
            return str(value).strip()
    return ""


def parse_query_id_result(value: Any) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    raw_items: Any
    if isinstance(value, dict):
        raw_items = value.get("name2IdPos") or value.get("records") or value.get("data") or []
    elif isinstance(value, list):
        raw_items = value
    else:
        raw_items = []

    if not isinstance(raw_items, list):
        return []

    for item in raw_items:
        if not isinstance(item, dict):
            continue
        record_id = get_field_id(item, "id", "_id", "data_id", "dataId")
        if not record_id:
            continue
        records.append(
            {
                "id": record_id,
                "name": str(item.get("name") or ""),
                "apiName": str(item.get("apiName") or item.get("object_api_name") or ""),
            }
        )
    return records


def resolve_opportunity_id(args: argparse.Namespace) -> tuple[str, list[dict[str, str]]]:
    if args.opportunity_id:
        return args.opportunity_id.strip(), []

    payload = compact_json(
        {"query": args.opportunity_name, "apiNames": ["NewOpportunityObj"]},
    )
    matches = parse_query_id_result(
        run_sharecrm(["data", "record", "query-id-by-name", "--data", payload])
    )
    if len(matches) == 1:
        return matches[0]["id"], matches
    return "", matches


def query_seller_industry(errors: list[dict[str, str]]) -> dict[str, Any]:
    payload = compact_json({"key": "service_models"})
    try:
        raw = run_sharecrm(["sales", "get-config-by-key", "--data", payload])
    except SharecrmError as exc:
        errors.append({"scope": "seller_industry", "message": str(exc)})
        return {"seller_industry": "", "raw": None}

    value = ""
    if isinstance(raw, dict):
        value = str(raw.get("value") or "").strip()
    elif isinstance(raw, str):
        value = raw.strip()

    parts = [part.strip() for part in re.split(r"[,，;；]", value) if part.strip()]
    return {"seller_industry": parts[0] if parts else "", "raw": raw}


def extract_buyer_industry(account: dict[str, Any] | None) -> str:
    return get_text(
        account,
        "industry_level1",
        "industry_level2",
        "industry",
    )


def collect_contact_ids(contact_links: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    contact_ids: list[str] = []
    for link in contact_links:
        contact_id = get_field_id(link, "contact_id")
        if contact_id and contact_id not in seen:
            seen.add(contact_id)
            contact_ids.append(contact_id)
    return contact_ids


def safe_query(
    scope: str,
    errors: list[dict[str, str]],
    func,
    default: Any,
) -> Any:
    try:
        return func()
    except SharecrmError as exc:
        errors.append({"scope": scope, "message": str(exc)})
        return default


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    descriptions: dict[str, Any] = {}
    queried_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def merge_task_result(result: dict[str, Any]) -> Any:
        errors.extend(result.get("errors", []))
        if args.include_describes:
            descriptions.update(result.get("describes", {}))
        return result.get("value")

    def run_task(scope: str, func, default: Any) -> dict[str, Any]:
        task_errors: list[dict[str, str]] = []
        task_descriptions: dict[str, Any] = {}
        value = safe_query(scope, task_errors, func(task_descriptions, task_errors), default)
        return {
            "value": value,
            "errors": task_errors,
            "describes": task_descriptions,
        }

    def run_plain_task(scope: str, func, default: Any) -> dict[str, Any]:
        task_errors: list[dict[str, str]] = []
        value = safe_query(scope, task_errors, func, default)
        return {"value": value, "errors": task_errors, "describes": {}}

    def run_seller_task(scope: str, func, default: Any) -> dict[str, Any]:
        task_errors: list[dict[str, str]] = []
        value = func(task_errors)
        if value is None:
            value = default
        return {"value": value, "errors": task_errors, "describes": {}}

    try:
        opportunity_id, candidates = resolve_opportunity_id(args)
    except SharecrmError as exc:
        return {
            "status": "ERROR",
            "queried_at": queried_at,
            "message": str(exc),
            "errors": [{"scope": "resolve_opportunity", "message": str(exc)}],
        }

    if not opportunity_id:
        return {
            "status": "OPPORTUNITY_NOT_RESOLVED",
            "queried_at": queried_at,
            "message": "商机未唯一命中，请根据 candidates 选择唯一商机后用 --opportunity-id 重试。",
            "candidates": candidates,
        }

    opportunity_full = safe_query(
        "opportunity_full",
        errors,
        lambda: get_by_id("NewOpportunityObj", opportunity_id),
        None,
    )
    if not opportunity_full:
        return {
            "status": "OPPORTUNITY_NOT_FOUND",
            "queried_at": queried_at,
            "opportunity_id": opportunity_id,
            "errors": errors,
        }

    account_id = get_field_id(opportunity_full, "account_id")
    account_full = None
    account_fields = None
    seller_context = {"seller_industry": "", "raw": None}
    contact_links: list[dict[str, Any]] = []
    contact_relationships: list[dict[str, Any]] = []
    quotes: list[dict[str, Any]] = []
    active_records: list[dict[str, Any]] = []
    competitive_lines: list[dict[str, Any]] = []

    first_wave: dict[str, Any] = {
        "seller_context": (
            "seller",
            lambda task_errors: query_seller_industry(task_errors),
            {"seller_industry": "", "raw": None},
        ),
        "opportunity_contacts": (
            "query",
            lambda task_descriptions, task_errors: lambda: query_by_fields(
                "NewOpportunityContactsObj",
                OPPORTUNITY_CONTACT_FIELDS,
                {"new_opportunity_id": opportunity_id},
                args.limit_contacts,
                "last_modified_time:desc",
                task_descriptions,
                task_errors,
            ),
            [],
        ),
        "contact_relationships": (
            "query",
            lambda task_descriptions, task_errors: lambda: query_by_fields(
                "NewOpportunityContactRelationshipObj",
                CONTACT_RELATIONSHIP_FIELDS,
                {"opportunity_id": opportunity_id},
                args.limit_contact_relationships,
                "last_modified_time:desc",
                task_descriptions,
                task_errors,
            ),
            [],
        ),
        "quotes": (
            "query",
            lambda task_descriptions, task_errors: lambda: query_by_fields(
                "QuoteObj",
                QUOTE_FIELDS,
                {"new_opportunity_id": opportunity_id},
                args.limit_quotes,
                "last_modified_time:desc",
                task_descriptions,
                task_errors,
            ),
            [],
        ),
        "active_records": (
            "query",
            lambda task_descriptions, task_errors: lambda: query_by_fields(
                "ActiveRecordObj",
                ACTIVE_RECORD_FIELDS,
                {"new_opportunity_id": opportunity_id},
                args.limit_active_records,
                "create_time:desc",
                task_descriptions,
                task_errors,
            ),
            [],
        ),
        "competitive_lines": (
            "query",
            lambda task_descriptions, task_errors: lambda: query_by_fields(
                "CompetitiveLinesObj",
                COMPETITIVE_LINE_FIELDS,
                {"new_opportunity_id": opportunity_id},
                args.limit_competitive_lines,
                "last_modified_time:desc",
                task_descriptions,
                task_errors,
            ),
            [],
        ),
    }

    if account_id:
        first_wave["account_full"] = (
            "plain",
            lambda: get_by_id("AccountObj", account_id),
            None,
        )
        first_wave["account_fields"] = (
            "query",
            lambda task_descriptions, task_errors: lambda: query_by_fields(
                "AccountObj",
                ACCOUNT_FIELDS,
                {"_id": account_id},
                1,
                None,
                task_descriptions,
                task_errors,
            ),
            [],
        )
    else:
        errors.append(
            {
                "scope": "account",
                "message": "商机记录中未读取到 account_id，无法查询关联客户与买方行业。",
            }
        )

    with ThreadPoolExecutor(max_workers=min(4, len(first_wave) or 1)) as executor:
        futures = {}
        for key, (task_type, task_func, default) in first_wave.items():
            if task_type == "plain":
                futures[executor.submit(run_plain_task, key, task_func, default)] = key
            elif task_type == "seller":
                futures[executor.submit(run_seller_task, key, task_func, default)] = key
            else:
                futures[executor.submit(run_task, key, task_func, default)] = key

        for future in as_completed(futures):
            key = futures[future]
            value = merge_task_result(future.result())
            if key == "seller_context":
                seller_context = value
            elif key == "account_full":
                account_full = value
            elif key == "account_fields":
                account_fields = first_record(value)
            elif key == "opportunity_contacts":
                contact_links = value
            elif key == "contact_relationships":
                contact_relationships = value
            elif key == "quotes":
                quotes = value
            elif key == "active_records":
                active_records = value
            elif key == "competitive_lines":
                competitive_lines = value

    contacts: list[dict[str, Any]] = []
    quote_lines_by_quote_id: dict[str, list[dict[str, Any]]] = {}

    second_wave: dict[str, tuple[str, Any, Any]] = {}
    for contact_id in collect_contact_ids(contact_links):
        second_wave[f"contact:{contact_id}"] = (
            "plain",
            lambda contact_id=contact_id: get_by_id("ContactObj", contact_id),
            None,
        )

    for quote in quotes:
        quote_id = get_field_id(quote, "_id", "id")
        if not quote_id:
            continue
        second_wave[f"quote_lines:{quote_id}"] = (
            "query",
            lambda task_descriptions, task_errors, quote_id=quote_id: lambda: query_by_fields(
                "QuoteLinesObj",
                QUOTE_LINE_FIELDS,
                {"quote_id": quote_id},
                args.limit_quote_lines,
                "last_modified_time:desc",
                task_descriptions,
                task_errors,
            ),
            [],
        )

    with ThreadPoolExecutor(max_workers=min(4, len(second_wave) or 1)) as executor:
        futures = {}
        for key, (task_type, task_func, default) in second_wave.items():
            if task_type == "plain":
                futures[executor.submit(run_plain_task, key, task_func, default)] = key
            else:
                futures[executor.submit(run_task, key, task_func, default)] = key

        for future in as_completed(futures):
            key = futures[future]
            value = merge_task_result(future.result())
            if key.startswith("contact:"):
                if value:
                    contacts.append(value)
            elif key.startswith("quote_lines:"):
                quote_lines_by_quote_id[key.removeprefix("quote_lines:")] = value

    account_for_industry = account_fields or account_full
    return {
        "status": "READY",
        "queried_at": queried_at,
        "opportunity_id": opportunity_id,
        "seller_context": seller_context,
        "buyer_industry": extract_buyer_industry(account_for_industry),
        "data": {
            "opportunity_full": opportunity_full,
            "account_full": account_full,
            "account_fields": account_fields,
            "opportunity_contacts": contact_links,
            "contacts": contacts,
            "contact_relationships": contact_relationships,
            "quotes": quotes,
            "quote_lines_by_quote_id": quote_lines_by_quote_id,
            "active_records": active_records,
            "competitive_lines": competitive_lines,
        },
        "describes": descriptions if args.include_describes else {},
        "errors": errors,
        "notes": [
            "报价、单价、折扣、竞对报价金额等敏感商务信息仅用于内部判断，不应在诊断正文逐条列示具体数值。",
            "联系人、竞争对手明细或销售记录为空时只能标注证据不足，不得自动推断为不存在。",
        ],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="查询商机诊断所需 CRM 数据并输出 JSON 数据包。"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--opportunity-id", help="已确认的 NewOpportunityObj 记录 ID。")
    source.add_argument("--opportunity-name", help="商机名称；必须唯一命中，否则返回候选。")
    parser.add_argument("--limit-contacts", type=int, default=20)
    parser.add_argument("--limit-contact-relationships", type=int, default=50)
    parser.add_argument("--limit-quotes", type=int, default=3)
    parser.add_argument("--limit-quote-lines", type=int, default=20)
    parser.add_argument("--limit-active-records", type=int, default=10)
    parser.add_argument("--limit-competitive-lines", type=int, default=20)
    parser.add_argument(
        "--include-describes",
        action="store_true",
        help="在输出中附带 describe 结果，便于排查字段口径。",
    )
    parser.add_argument("--pretty", action="store_true", help="兼容旧参数；输出仍为单行 JSON。")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
