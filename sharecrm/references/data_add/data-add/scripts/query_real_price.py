#!/usr/bin/env python3
"""普通产品取价并回填明细。

把 PriceService 中确定性的两段逻辑收敛到脚本：
1. 从上下文已构造的 details map 中剔除 BOM 已回填行，组装取价入参
2. 调用 action-get-real-price，按 QuoteLinesObj / 非 QuoteLinesObj 规则回填

Agent 只负责传入上游已构造好的 accountId / object_api_name / object_data / details；
BOM 过滤、simpleResult、fullProductList 组装、接口调用和字段回填都由脚本完成。
禁止 Agent 手调 action-get-real-price，也禁止手写回填。

入参 --data：
{
  "accountId": "<客户ID>",                 // 可缺省，缺省时取 object_data.account_id
  "object_api_name": "QuoteObj",           // 可缺省，缺省时取 object_data.object_describe_api_name
  "object_data": { ... },                  // 当前主对象数据，原样传给取价接口
  "details": {                             // 上下文已构造的从对象 map，禁止改成数组
    "QuoteLinesObj": [
      {"product_id": "<产品ID>", "quantity": "1"}
    ]
  }
}

用法:
    python query_real_price.py --data '{"accountId":"...","object_api_name":"QuoteObj","object_data":{...},"details":{"QuoteLinesObj":[...]}}'

返回 status：
    READY          —— 已回填（含：剔除 BOM 后无待取价产品，跳过接口）
    EMPTY_PRICE    —— 接口返回为空，或存在待取价产品找不到可匹配 product_id
    CLI_ERROR      —— 取价接口调用失败
    INVALID_INPUT  —— 入参不合法
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Any


BOM_MARKERS = ("prod_pkg_key", "bom_core_id", "bom_id")
QUOTE_OBJ = "QuoteObj"
SALES_ORDER_OBJ = "SalesOrderObj"
SALE_CONTRACT_OBJ = "SaleContractObj"
QUOTE_LINES_OBJ = "QuoteLinesObj"
SALES_ORDER_PRODUCT_OBJ = "SalesOrderProductObj"
SALE_CONTRACT_LINE_OBJ = "SaleContractLineObj"
# 返回 details 前从所有明细行移除的字段，后续新增直接往对应名单加。
DETAIL_STRIP_FIELDS_QUOTE_LINES = (
    "amount",
    "order_field",
    "origin_selling_price",
    "price_book_price",
    "price_book_discount",
    "adjust_price",
    "temp_detail_id",
    "parent_bom_id",
    "price_book_subtotal",
)
DETAIL_STRIP_FIELDS_OTHER = (
    "selling_price",
    "amount",
    "order_field",
    "origin_selling_price",
    "adjust_price",
    "temp_detail_id",
    "parent_bom_id",
)


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


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def has_value(value: Any) -> bool:
    return value is not None and value != ""


def is_bom_row(row: dict) -> bool:
    """BOM 插件已回填的明细行：含 prod_pkg_key / bom_core_id / bom_id 任一即视为 BOM 行。"""
    return any(has_value(row.get(key)) for key in BOM_MARKERS)


def row_product_id(row: dict) -> str:
    value = row.get("product_id")
    if not has_value(value):
        value = row.get("productId")
    if not has_value(value):
        return ""
    return str(value).strip()


def row_amount(row: dict) -> str:
    """取价接口 amount 必须是字符串；数量取 quantity，缺省再取 amount，仍缺省则 \"1\"。"""
    value = row.get("quantity")
    if not has_value(value):
        value = row.get("amount")
    if not has_value(value):
        return "1"
    return str(value)


def rst_product_id(rst: dict) -> str:
    value = rst.get("product_id")
    if not has_value(value):
        value = rst.get("productId")
    if not has_value(value):
        return ""
    return str(value).strip()


def unwrap_response(resp: Any) -> Any:
    if isinstance(resp, dict) and "code" in resp:
        if resp.get("code") != 0:
            raise ValueError(resp.get("message") or "未知错误")
        return resp.get("data") if resp.get("data") is not None else {}
    if isinstance(resp, dict) and resp.get("errorCode"):
        raise ValueError(resp.get("errorMsg") or resp.get("message") or "取价接口执行失败")
    return resp


def extract_new_rst(resp: Any) -> list[dict]:
    """从取价返回中抽取 newRst，兼容多种包装形态。"""
    if isinstance(resp, list):
        return [item for item in resp if isinstance(item, dict)]
    if not isinstance(resp, dict):
        return []
    for key in ("newRst", "new_rst"):
        value = resp.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]
    nested = resp.get("data")
    if nested is not None and nested is not resp:
        return extract_new_rst(nested)
    return []


def index_new_rst(records: list[dict]) -> dict[str, dict]:
    """按 product_id 建索引；同一产品多次出现时保留首条。"""
    indexed: dict[str, dict] = {}
    for record in records:
        pid = rst_product_id(record)
        if pid and pid not in indexed:
            indexed[pid] = record
    return indexed


def display_name_of(rst: dict) -> Any:
    if has_value(rst.get("display_name")):
        return rst.get("display_name")
    return rst.get("name")


def apply_discount(row: dict, rst: dict) -> None:
    discount = rst.get("discount")
    row["discount"] = 100 if not has_value(discount) else discount


def apply_optional_fields(row: dict, rst: dict) -> None:
    if has_value(rst.get("price_book_subtotal")):
        row["price_book_subtotal"] = rst.get("price_book_subtotal")
    if has_value(rst.get("price_tiered_record")):
        row["price_tiered_record"] = rst.get("price_tiered_record")


def apply_common_fields(row: dict, rst: dict) -> None:
    """场景 A/B 公共回填：价目表产品、价目表及其 __r、折扣、价目表价格、可选字段。"""
    row["price_book_product_id"] = rst.get("_id")
    row["price_book_product_id__r"] = display_name_of(rst)
    row["price_book_id"] = rst.get("pricebook_id")
    row["price_book_id__r"] = rst.get("pricebook_id__r")
    apply_discount(row, rst)
    row["price_book_price"] = rst.get("pricebook_price")
    apply_optional_fields(row, rst)


def apply_quote_lines(row: dict, rst: dict) -> None:
    """场景 A：仅 QuoteLinesObj。售价写入 price，其余与场景 B 一致。"""
    row["price"] = rst.get("selling_price")
    apply_common_fields(row, rst)


def apply_other_lines(row: dict, rst: dict) -> None:
    """场景 B：非 QuoteLinesObj。售价写入 product_price，其余与场景 A 一致。"""
    row["product_price"] = rst.get("selling_price")
    apply_common_fields(row, rst)


def apply_price(row: dict, rst: dict, detail_object_api_name: str) -> None:
    if detail_object_api_name == QUOTE_LINES_OBJ:
        apply_quote_lines(row, rst)
    else:
        apply_other_lines(row, rst)


def apply_bom_adjust_price(row: dict, object_api_name: str) -> None:
    """BOM 过滤时：凡带 BOM 标记的行，用 adjust_price 回写价格字段，不参与取价。"""
    if not is_bom_row(row) or not has_value(row.get("adjust_price")):
        return
    if object_api_name == QUOTE_LINES_OBJ:
        row["price"] = row.get("adjust_price")
    else:
        row["product_price"] = row.get("adjust_price")


def apply_bom_prices(details: dict) -> None:
    for object_api_name, items in details.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                apply_bom_adjust_price(item, object_api_name)


def to_number(value: Any, default: float = 0.0) -> float:
    if not has_value(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def rate_of(value: Any, default: float = 100.0) -> float:
    """折扣/额外折扣按百分数：100 → 1.0。"""
    return to_number(value, default) / 100.0


def apply_order_or_contract_amounts(row: dict) -> None:
    sales_price = to_number(row.get("product_price")) * rate_of(row.get("discount"))
    row["sales_price"] = sales_price
    row["subtotal"] = sales_price * to_number(row.get("quantity"), 1.0)


def apply_quote_amounts(row: dict) -> None:
    sales_price = to_number(row.get("price")) * rate_of(row.get("discount"))
    selling_price = sales_price * rate_of(row.get("extra_discount"))
    quantity = to_number(row.get("quantity"), 1.0)
    row["sales_price"] = sales_price
    row["selling_price"] = selling_price
    row["sales_amount"] = selling_price * quantity
    row["total_amount"] = sales_price * quantity


def apply_derived_amounts(row: dict, object_api_name: str) -> None:
    if object_api_name == QUOTE_LINES_OBJ:
        apply_quote_amounts(row)
    elif object_api_name in (SALES_ORDER_PRODUCT_OBJ, SALE_CONTRACT_LINE_OBJ):
        apply_order_or_contract_amounts(row)


def apply_derived_amounts_to_details(details: dict) -> None:
    """取价/BOM 价格回写后，补齐销售价与小计相关字段。"""
    for object_api_name, items in details.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                apply_derived_amounts(item, object_api_name)


def sum_detail_field(details: dict, detail_object_api_name: str, field: str) -> float:
    items = details.get(detail_object_api_name)
    if not isinstance(items, list):
        return 0.0
    total = 0.0
    for item in items:
        if isinstance(item, dict):
            total += to_number(item.get(field))
    return total


def apply_master_object_amounts(object_data: dict, details: dict, object_api_name: str) -> dict:
    """仅 QuoteObj / SalesOrderObj / SaleContractObj 写主对象金额；其它对象原样返回。"""
    payload = dict(object_data)
    if object_api_name == QUOTE_OBJ:
        quote_product_sum = sum_detail_field(details, QUOTE_LINES_OBJ, "sales_amount")
        payload["quote_product_sum"] = quote_product_sum
        payload["quote_amount"] = quote_product_sum * rate_of(payload.get("quote_discount"))
    elif object_api_name == SALE_CONTRACT_OBJ:
        payload["amount"] = sum_detail_field(details, SALE_CONTRACT_LINE_OBJ, "subtotal")
    elif object_api_name == SALES_ORDER_OBJ:
        product_amount = sum_detail_field(details, SALES_ORDER_PRODUCT_OBJ, "subtotal")
        payload["product_amount"] = product_amount
        payload["order_amount"] = product_amount * rate_of(payload.get("discount"))
    return payload


def finish_ready(details: dict, object_data: dict, object_api_name: str) -> None:
    apply_bom_prices(details)
    apply_derived_amounts_to_details(details)
    filled_object_data = apply_master_object_amounts(object_data, details, object_api_name)
    strip_details_fields(details)
    emit({"status": "READY", "details": details, "object_data": filled_object_data})


def strip_fields_for(object_api_name: str) -> tuple[str, ...]:
    if object_api_name == QUOTE_LINES_OBJ:
        return DETAIL_STRIP_FIELDS_QUOTE_LINES
    return DETAIL_STRIP_FIELDS_OTHER


def strip_unwanted_fields(row: dict, object_api_name: str) -> None:
    for key in strip_fields_for(object_api_name):
        row.pop(key, None)


def strip_details_fields(details: dict) -> None:
    """返回前按对象名单清理多余字段，普通行与 BOM 行都剥离。"""
    for object_api_name, items in details.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                strip_unwanted_fields(item, object_api_name)


def iter_detail_rows(details: dict) -> list[tuple[str, int, dict]]:
    """按 details map 的插入顺序展开 (对象 apiName, 行下标, 行)。"""
    rows: list[tuple[str, int, dict]] = []
    for object_api_name, items in details.items():
        if not isinstance(items, list):
            raise ValueError(f"details.{object_api_name} 必须是数组")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"details.{object_api_name}[{index}] 必须是对象")
            rows.append((object_api_name, index, item))
    return rows


def collect_priceable(details: dict) -> list[tuple[str, int, dict]]:
    priceable: list[tuple[str, int, dict]] = []
    for object_api_name, index, row in iter_detail_rows(details):
        if is_bom_row(row):
            continue
        if not row_product_id(row):
            continue
        priceable.append((object_api_name, index, row))
    return priceable


def build_full_product_list(priceable: list[tuple[str, int, dict]]) -> list[dict]:
    return [
        {"productId": row_product_id(row), "amount": row_amount(row)}
        for _, _, row in priceable
    ]


def build_object_data(data: dict, object_api_name: str, account_id: str) -> dict:
    object_data = data.get("object_data")
    if object_data is None:
        object_data = {}
    if not isinstance(object_data, dict):
        raise ValueError("object_data 必须是 JSON 对象")
    payload = dict(object_data)
    if not has_value(payload.get("object_describe_api_name")):
        payload["object_describe_api_name"] = object_api_name
    if not has_value(payload.get("account_id")):
        payload["account_id"] = account_id
    return payload


def call_get_real_price(payload: dict) -> dict:
    """调用 sharecrm sales product action-get-real-price，参数格式保持 PriceService 现状。"""
    try:
        completed = subprocess.run(
            resolve_sharecrm_command()
            + [
                "sales",
                "product",
                "action-get-real-price",
                "-d",
                json.dumps(payload, ensure_ascii=False),
            ],
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

    try:
        return unwrap_response(resp)
    except ValueError as exc:
        return {"error": str(exc)}


def fail(status: str, error: str, details: dict) -> None:
    emit({"status": status, "error": error, "details": details})


def main() -> None:
    parser = argparse.ArgumentParser(description="普通产品取价并回填明细")
    parser.add_argument(
        "--data",
        required=True,
        help='JSON：{"accountId":"...","object_api_name":"QuoteObj","object_data":{...},"details":{"QuoteLinesObj":[...]}}',
    )
    args = parser.parse_args()

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as exc:
        sys.exit(f"--data 不是合法 JSON：{exc}")

    if not isinstance(data, dict):
        sys.exit("--data 必须是 JSON 对象")

    details = data.get("details")
    if not isinstance(details, dict):
        emit({"status": "INVALID_INPUT", "error": "details 必须是 JSON 对象（从对象 apiName → 明细数组）"})
        return

    object_data = data.get("object_data") if isinstance(data.get("object_data"), dict) else {}
    object_api_name = data.get("object_api_name") or object_data.get("object_describe_api_name")
    account_id = data.get("accountId") or object_data.get("account_id")
    if not has_value(object_api_name):
        emit({"status": "INVALID_INPUT", "error": "缺少 object_api_name"})
        return
    if not has_value(account_id):
        emit({"status": "INVALID_INPUT", "error": "缺少 accountId"})
        return
    object_api_name = str(object_api_name)
    account_id = str(account_id)

    try:
        priceable = collect_priceable(details)
        object_data_payload = build_object_data(data, object_api_name, account_id)
    except ValueError as exc:
        emit({"status": "INVALID_INPUT", "error": str(exc), "details": details})
        return

    if not priceable:
        finish_ready(details, object_data, object_api_name)
        return

    api_payload = {
        "accountId": account_id,
        "object_api_name": object_api_name,
        "simpleResult": True,
        "fullProductList": build_full_product_list(priceable),
        "object_data": object_data_payload,
    }
    resp = call_get_real_price(api_payload)
    if isinstance(resp, dict) and "error" in resp:
        fail("CLI_ERROR", resp["error"], details)
        return

    new_rst = extract_new_rst(resp)
    if not new_rst:
        fail("EMPTY_PRICE", "取价接口返回为空，请补充或校正产品信息", details)
        return

    rst_by_product = index_new_rst(new_rst)
    unmatched = []
    for _, _, row in priceable:
        pid = row_product_id(row)
        if pid not in rst_by_product:
            unmatched.append(pid)
    if unmatched:
        fail(
            "EMPTY_PRICE",
            "找不到可匹配 product_id 的取价结果，请补充或校正产品信息：" + ", ".join(unmatched),
            details,
        )
        return

    filled: dict[str, list] = {}
    for object_api_name_key, items in details.items():
        filled[object_api_name_key] = [dict(item) if isinstance(item, dict) else item for item in items]

    for object_api_name_key, index, _row in priceable:
        target = filled[object_api_name_key][index]
        rst = rst_by_product[row_product_id(target)]
        apply_price(target, rst, object_api_name_key)

    finish_ready(filled, object_data, object_api_name)


if __name__ == "__main__":
    main()
