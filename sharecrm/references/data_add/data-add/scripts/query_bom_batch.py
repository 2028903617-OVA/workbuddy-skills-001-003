#!/usr/bin/env python3
"""BOM 批量查询统一脚本，按 --mode 切换预设，避免 Agent 手拼 SQL 把 ID 裸写进 IN(...)。

合并自 query_bom_core_batch.py 与 query_bom_children_batch.py：两者只有
「对象 / IN 字段 / 分组字段 / 返回字段 / 过滤条件 / limit / --data 键」不同，
CLI 管道（resolve_sharecrm_command / call_query_by_sql / extract_records）完全一致，
故收敛为一份代码 + 预设表，后续新增 BOM 相关批量查询只需加一个 preset。

入参：
    --mode core      按 product_id 查询 BomCoreObj（BOM 头/母件）
    --mode children  按 core_id(bom_core_id) 查询 BOMObj 子产品节点
    --mode tree      调用 handleBomTree 并回填 BOM 明细字段（迁移自 handle_bom_tree.py）
    --mode expand    子产品递归展开：复用 BOM 沿 related_core_id 下钻、路径判环、深度上限、数量缩放
    --data           JSON 对象，键随 mode 变化（core/children 见各 preset 的 data_key；tree 为 handleBomTree 入参；expand 为 {"mothers":[{"bom_core_id":"...","quantity":"2"}]}）

core/children：脚本内部用转义后的值拼出 IN(...) SQL，调用 sharecrm data record query-by-sql，
再把返回记录按分组字段分组——每个 key 对应该 key 的记录数组（0 条=未命中/无子件、
≥1 条=命中列表），与 BomService 步骤 1 / 步骤 3 的逐 key 处理对齐。

tree：校验已组装的 dataList、补齐 temp_detail_id，调用 sharecrm sales product
handleBomTree，再按 temp_detail_id（降级 product_id）匹配返回行并回填 BOM /
价目表 / 价格字段。对应 BomService 步骤 4。

expand：对已确认 bom_core_id 的母件，批量查 BOMObj 子产品并沿 related_core_id
递归展开复用 BOM（以全部母件 bom_core_id 为种子按祖先链判环、深度上限 10 层、
同一 related_core_id 被不同分支复用时各自独立展开），按 amount_any / 数量缩放
规则算出每行最终数量，输出按深度优先排好的新增子产品行。对应 BomService 步骤 3。
返回 status：READY / CLI_ERROR / INVALID_INPUT / CYCLE_DETECTED / DEPTH_EXCEEDED。

tree 返回 status：
    READY          —— 已回填
    EMPTY_RESULT   —— 接口返回为空，或找不到可回填明细
    MATCH_ERROR    —— temp_detail_id / product_id 匹配歧义
    CLI_ERROR      —— handleBomTree 调用失败
    INVALID_INPUT  —— 入参不合法

用法:
    python query_bom_batch.py --mode core --data '{"product_ids":["69e9...","69e8..."]}'
    python query_bom_batch.py --mode children --data '{"core_ids":["69e9...","69e8..."]}'
    python query_bom_batch.py --mode tree --data '{"accountId":"...","objectApiName":"QuoteObj","detailObjectApiName":"QuoteLinesObj","objectData":{...},"dataList":[...]}'
    python query_bom_batch.py --mode expand --data '{"mothers":[{"bom_core_id":"69e9...","quantity":"2"}]}'
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from typing import Any


# 预设表：每个 mode 固定一份查询规格，Agent 不接触 SQL 细节。
#   object        —— 查询对象 API 名称
#   in_field      —— IN(...) 字段
#   group_field   —— 返回记录的分组字段
#   data_key      —— --data JSON 中承载 ID 列表的键
#   select_fields —— SELECT 字段
#   extra_filter  —— is_deleted 之外的附加过滤（含前导 AND）
#   limit         —— 返回条数上限
#   label         —— preset 用途说明
PRESETS: dict[str, dict] = {
    "core": {
        "object": "BomCoreObj",
        "in_field": "product_id",
        "group_field": "product_id",
        "data_key": "product_ids",
        # _id 作为 bom_core_id，name 作为 bom_core_id__r。
        "select_fields": "_id, name, product_id,category",
        "extra_filter": "",
        "limit": 500,
        "label": "按产品 ID 查询 BomCoreObj",
    },
    "children": {
        "object": "BOMObj",
        "in_field": "core_id",
        "group_field": "core_id",
        "data_key": "core_ids",
        # 子产品展开所需字段：product_id/name 回填明细，amount 作数量，core_id 分组，related_core_id 回填，
        # parent_bom_id/order_field 用于组内层级排序（父在前、子在后，同级按序号升序）。
        "select_fields": "_id, name, product_id, product_id__r, related_core_id, core_id, parent_bom_id, order_field, amount, amount_any",
        # 仅取启用子产品，保留母件下完整启用结构。
        "extra_filter": "AND enabled_status = true AND parent_bom_id is not null ",
        "limit": 2000,
        "label": "按 bom_core_id 查询 BOMObj 子产品节点",
        # 组内排序：先按父子层级（父级在前、子级在后，深度优先），同级再按序号升序。
        "hierarchy_sort": {"parent_field": "parent_bom_id", "order_field": "order_field"},
    },
}


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
    """SQL 字符串字面量：单引号包裹，内部单引号翻倍转义，避免 Agent 裸拼 IN(...) 时的注入/语法错误。"""
    return "'" + str(value).replace("'", "''") + "'"


def build_sql(preset: dict, ids: list[str]) -> str:
    in_list = ", ".join(sql_quote(i) for i in ids)
    return (
        f"SELECT {preset['select_fields']} FROM {preset['object']} "
        f"WHERE {preset['in_field']} IN ({in_list}) "
        f"{preset['extra_filter']} "
        f"ORDER BY {preset['group_field']}, create_time LIMIT {preset['limit']}"
    )


def call_query_by_sql(sql: str) -> dict:
    """调用 sharecrm data record query-by-sql，返回解析后的 dict 或 {"error": ...}。

    服务端单页上限 50 条（LIMIT_CAPPED，与 SQL LIMIT 无关），翻页只能用 SQL 原生
    OFFSET（LIMIT n OFFSET m）；--search_after 会被服务端命令解析静默忽略，不可用。
    raw 模式分页元信息：queryMeta.page.{requestedLimit,offset,returnedCount,appliedLimit}
    + recordResult.totalNumber。
    """
    cmd = resolve_sharecrm_command() + ["data", "record", "query-by-sql", "--need_count", "true", "--raw"]
    cmd += ["--sql", sql]
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

    raw = (completed.stdout or "").strip()
    if not raw:
        return {"error": "CLI 无返回内容"}

    try:
        resp = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"error": f"返回非法 JSON：{exc}"}

    # 兼容 {"code":0,"data":{...}} 包装
    if isinstance(resp, dict) and "code" in resp:
        if resp.get("code") != 0:
            return {"error": resp.get("message") or "未知错误"}
        resp = resp.get("data") or {}
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


def get_page_info(resp: dict) -> tuple[int, int]:
    """raw 模式分页元信息：返回 (本页条数, 总条数)。字段缺失时按 (0, 0) 处理。"""
    if not isinstance(resp, dict):
        return 0, 0
    meta = resp.get("queryMeta")
    page = meta.get("page") if isinstance(meta, dict) else None
    record_result = resp.get("recordResult")
    returned = page.get("returnedCount", 0) if isinstance(page, dict) else 0
    total = record_result.get("totalNumber", 0) if isinstance(record_result, dict) else 0
    return returned, total


def query_all_records(sql: str) -> tuple[list[dict], str | None]:
    """SQL OFFSET 分页拉取全部记录（服务端单页上限 50），失败返回 ([], 错误信息)。

    终止条件：本页 0 条，或累计条数达到 totalNumber。offset 按实际已消费条数推进，
    兼容权限过滤导致单页少返回的场景（ORG_PAGE_FILTERED）。
    """
    all_records: list[dict] = []
    for _ in range(100):  # 防无限循环
        paged_sql = sql if not all_records else f"{sql} OFFSET {len(all_records)}"
        resp = call_query_by_sql(paged_sql)
        if isinstance(resp, dict) and "error" in resp:
            return [], resp["error"]
        records = extract_records(resp)
        all_records.extend(records)
        _returned, total = get_page_info(resp)
        if not records or (total > 0 and len(all_records) >= total):
            break
    return all_records, None


def group_by(ids: list[str], records: list[dict], group_field: str) -> dict[str, list[dict]]:
    """按 group_field 分组命中记录。未命中的 key 对应空数组，便于上游做 0/≥1 判定。"""
    groups: dict[str, list[dict]] = {i: [] for i in ids}
    for record in records:
        key = record.get(group_field)
        if isinstance(key, str) and key in groups:
            groups[key].append(record)
    return groups


def _order_sort_key(value) -> tuple:
    """序号升序排序键：数值优先（按 float 升序），非数值按字符串升序，缺失/空沉底。

    order_field 在 BOMObj 中以字符串存储（如 "1"、"2"），需先尝试数值解析再做字符串兜底，
    避免 "10" < "2" 的字符串字典序错误。
    """
    if value is None or value == "":
        return (2, 0.0, "")
    s = str(value).strip()
    if not s:
        return (2, 0.0, "")
    try:
        return (0, float(s), "")
    except ValueError:
        return (1, 0.0, s)


def sort_hierarchy(records: list[dict], parent_field: str, order_field: str) -> list[dict]:
    """组内树形排序：父级节点在前、子级节点在后（深度优先），同级按 order_field 升序。

    - 以 _id 建索引；每条记录的 parent_field 若指向返回集内的某 _id，则归为其子节点，否则视为根。
      （现有 SQL 过滤 parent_bom_id is not null，故顶层子产品的 parent_bom_id 指向不在返回集中的
      组装件根，自然落入根集合。）
    - 用显式栈做前序遍历，避免深树递归栈溢出；visited 集合防环引用导致的死循环。
    - 保留所有记录（含 _id 缺失或父缺失的异常行），不丢数据。
    """
    by_id: dict[str, dict] = {}
    for record in records:
        rid = record.get("_id")
        if isinstance(rid, str):
            by_id[rid] = record

    children_map: dict[str, list[dict]] = {rid: [] for rid in by_id}
    roots: list[dict] = []
    for record in records:
        pid = record.get(parent_field)
        if isinstance(pid, str) and pid in by_id:
            children_map[pid].append(record)
        else:
            roots.append(record)

    for siblings in children_map.values():
        siblings.sort(key=lambda r: _order_sort_key(r.get(order_field)))
    roots.sort(key=lambda r: _order_sort_key(r.get(order_field)))

    result: list[dict] = []
    visited: set[str] = set()
    # 根按序号排好后入栈，逆序压栈保证出栈顺序即序号升序；子节点同理。
    stack: list[dict] = list(reversed(roots))
    while stack:
        node = stack.pop()
        nid = node.get("_id")
        if isinstance(nid, str):
            if nid in visited:
                continue
            visited.add(nid)
        result.append(node)
        for child in reversed(children_map.get(nid, [])):
            stack.append(child)
    return result


# ---------------------------------------------------------------------------
# expand 模式：子产品递归展开（BomService 步骤 3）
# ---------------------------------------------------------------------------

# 递归深度硬上限：已确认母件为第 1 层，每下钻一层复用 BOM 加 1。
MAX_EXPAND_DEPTH = 10


class ExpandError(ValueError):
    """expand 模式终止错误，携带输出 status。"""

    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


def _has_value(value: Any) -> bool:
    return value is not None and value != ""


def parse_qty(value: Any) -> Decimal:
    """数量解析：缺失或非法按 1 处理（对齐 BomService 输入约束与 amount 缺失规则）。"""
    if not _has_value(value):
        return Decimal(1)
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return Decimal(1)


def qty_to_str(value: Decimal) -> str:
    """数量输出：整数去小数位，小数去尾零，避免 8.0 / 1E+2 这类写法。"""
    if value == value.to_integral_value():
        return str(value.quantize(Decimal(1)))
    return format(value.normalize(), "f")


def is_true_flag(value: Any) -> bool:
    """amount_any 判定：布尔 true 或字符串 "true"（大小写不敏感），缺失按 false。"""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() == "true"


def fetch_children_groups(core_ids: list[str]) -> dict[str, list[dict]]:
    """按 children preset 批量查询 BOMObj 子产品并做组内树形排序，失败抛 ExpandError。"""
    preset = PRESETS["children"]
    records, error = query_all_records(build_sql(preset, core_ids))
    if error:
        raise ExpandError("CLI_ERROR", error)
    groups = group_by(core_ids, records, preset["group_field"])
    hierarchy = preset.get("hierarchy_sort")
    if hierarchy:
        for key, recs in groups.items():
            groups[key] = sort_hierarchy(recs, hierarchy["parent_field"], hierarchy["order_field"])
    return groups


def expand_core(
    core_id: str,
    parent_qty: Decimal,
    path: set,
    depth: int,
    cache: dict,
    rows_out: list,
) -> None:
    """递归展开一个 core_id 的子产品，按深度优先顺序向 rows_out 追加新增明细行。

    - children preset 返回组内已按树形排好序，顺序迭代即保持父在前、子在后。
    - 复用 BOM 节点（related_core_id 有值）：先追加节点行（携带 bom_core_id），
      再紧随其后续递归追加其子产品行；沿祖先链判环，深度超限即停。
    - 数量缩放：amount_any 为 true 时取 amount；否则 amount × 上一层行最终数量。
    """
    if depth > MAX_EXPAND_DEPTH:
        raise ExpandError(
            "DEPTH_EXCEEDED",
            f"复用 BOM 递归展开超过 {MAX_EXPAND_DEPTH} 层上限（core_id={core_id}）",
        )
    if core_id not in cache:
        cache.update(fetch_children_groups([core_id]))
    for child in cache[core_id]:
        amount = parse_qty(child.get("amount"))
        qty = amount if is_true_flag(child.get("amount_any")) else amount * parent_qty
        row: dict[str, Any] = {}
        if _has_value(child.get("product_id")):
            row["product_id"] = child.get("product_id")
        if _has_value(child.get("product_id__r")):
            row["product_id__r"] = child.get("product_id__r")
        row["quantity"] = qty_to_str(qty)
        rows_out.append(row)

        related = child.get("related_core_id")
        if _has_value(related):
            related = str(related).strip()
            if related in path:
                raise ExpandError("CYCLE_DETECTED", f"复用 BOM 环引用：{related}")
            row["bom_core_id"] = related
            expand_core(related, qty, path | {related}, depth + 1, cache, rows_out)


def run_expand(raw_data: str) -> None:
    """expand 模式入口：校验 mothers → 批量预取首层子产品 → 逐母件递归展开。"""
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        sys.exit(f"--data 不是合法 JSON：{exc}")
    if not isinstance(data, dict):
        sys.exit("--data 必须是 JSON 对象")

    mothers = data.get("mothers")
    if not isinstance(mothers, list) or not mothers:
        emit({"status": "INVALID_INPUT", "error": "mothers 必须是非空数组"})
        return

    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for index, mother in enumerate(mothers):
        if not isinstance(mother, dict) or not _has_value(mother.get("bom_core_id")):
            emit({"status": "INVALID_INPUT", "error": f"mothers[{index}] 缺少 bom_core_id"})
            return
        core_id = str(mother["bom_core_id"]).strip()
        if core_id in seen:
            emit({"status": "INVALID_INPUT", "error": f"mothers 中 bom_core_id 重复：{core_id}"})
            return
        seen.add(core_id)
        normalized.append((core_id, parse_qty(mother.get("quantity"))))

    cache: dict[str, list[dict]] = {}
    try:
        # 首层一次性批量查询，与 children 模式的批量约定一致；递归层按需单查并缓存。
        cache.update(fetch_children_groups([cid for cid, _qty in normalized]))
        seed = {cid for cid, _qty in normalized}
        groups: dict[str, list[dict]] = {}
        for core_id, qty in normalized:
            rows: list[dict] = []
            expand_core(core_id, qty, set(seed), 1, cache, rows)
            groups[core_id] = rows
    except ExpandError as exc:
        emit({"status": exc.status, "error": str(exc)})
        return

    emit({"status": "READY", "groups": groups})


def normalize_ids(value, data_key: str) -> list[str]:
    """把 value 归一化为去空白、去重保序的 ID 列表。value 可为字符串或字符串数组。"""
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        raise ValueError(f"{data_key} 必须是字符串或字符串数组")
    ids: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str):
            raise ValueError("ID 必须是字符串")
        item = item.strip()
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            ids.append(item)
    return ids


QUOTE_LINES_OBJ = "QuoteLinesObj"

# tree 模式：返回行 → 明细行，有值才写。discount / price_per_set / 可选金额字段单独处理。
DIRECT_FIELDS = (
    ("price_book_product_id", "price_book_product_id"),
    ("price_book_product_id__r", "price_book_product_id__r"),
    ("price_book_id", "price_book_id"),
    ("price_book_id__r", "price_book_id__r"),
    ("attribute_price_book_id", "attribute_price_book_id"),
    ("attribute_price_book_id__r", "attribute_price_book_id__r"),
    ("prod_pkg_key", "prod_pkg_key"),
    ("parent_prod_pkg_key", "parent_prod_pkg_key"),
    ("root_prod_pkg_key", "root_prod_pkg_key"),
    ("related_core_id", "related_core_id"),
    ("new_bom_path", "new_bom_path"),
)


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def has_value(value: Any) -> bool:
    return value is not None and value != ""


def row_product_id(row: dict) -> str:
    value = row.get("product_id")
    if not has_value(value):
        value = row.get("productId")
    if not has_value(value):
        return ""
    return str(value).strip()


def row_temp_id(row: dict) -> str:
    value = row.get("temp_detail_id")
    if not has_value(value):
        return ""
    return str(value).strip()


def unwrap_response(resp: Any) -> Any:
    if isinstance(resp, dict) and "code" in resp:
        if resp.get("code") != 0:
            raise ValueError(resp.get("message") or "未知错误")
        return resp.get("data") if resp.get("data") is not None else {}
    if isinstance(resp, dict) and resp.get("errorCode"):
        raise ValueError(resp.get("errorMsg") or resp.get("message") or "handleBomTree 执行失败")
    return resp


def extract_return_rows(resp: Any) -> list[dict]:
    """从 handleBomTree 返回中抽取明细行，兼容多种包装形态。"""
    if isinstance(resp, list):
        return [item for item in resp if isinstance(item, dict)]
    if not isinstance(resp, dict):
        return []
    for key in ("dataList", "data_list", "newRst", "new_rst", "records"):
        value = resp.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]
    nested = resp.get("data")
    if nested is not None and nested is not resp:
        return extract_return_rows(nested)
    return []


def ensure_temp_detail_ids(data_list: list[dict]) -> None:
    """上游已有 temp_detail_id 则沿用；缺失的按明细顺序补齐，保证本次 dataList 内唯一。"""
    used: set[str] = set()
    for index, row in enumerate(data_list):
        tid = row_temp_id(row)
        if not tid:
            continue
        if tid in used:
            raise ValueError(f"dataList[{index}].temp_detail_id 重复：{tid}")
        used.add(tid)

    next_i = 0
    for row in data_list:
        if row_temp_id(row):
            continue
        while f"detail_{next_i}" in used:
            next_i += 1
        tid = f"detail_{next_i}"
        row["temp_detail_id"] = tid
        used.add(tid)
        next_i += 1


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    if not has_value(payload.get("accountId")):
        errors.append("缺少 accountId")
    if not has_value(payload.get("objectApiName")):
        errors.append("缺少 objectApiName")
    if not has_value(payload.get("detailObjectApiName")):
        errors.append("缺少 detailObjectApiName")

    data_list = payload.get("dataList")
    if not isinstance(data_list, list):
        errors.append("dataList 必须是数组")
        return errors
    if not data_list:
        errors.append("dataList 不能为空，必须传入当前从对象的完整明细数组")
        return errors

    for index, row in enumerate(data_list):
        if not isinstance(row, dict):
            errors.append(f"dataList[{index}] 必须是对象")

    if any(not isinstance(row, dict) for row in data_list):
        return errors

    if not any(has_value(row.get("bom_core_id")) for row in data_list):
        errors.append("dataList 必须至少有一行带 bom_core_id，否则不得调用 handleBomTree")
    return errors


def build_api_payload(payload: dict, data_list: list[dict]) -> dict:
    api_payload = {
        "accountId": str(payload["accountId"]),
        "objectApiName": str(payload["objectApiName"]),
        "detailObjectApiName": str(payload["detailObjectApiName"]),
        "dataList": data_list,
    }
    if has_value(payload.get("partnerId")):
        api_payload["partnerId"] = payload.get("partnerId")
    object_data = payload.get("objectData")
    api_payload["objectData"] = object_data if isinstance(object_data, dict) else {}
    return api_payload


def call_handle_bom_tree(payload: dict) -> dict:
    """调用 sharecrm sales product handleBomTree，返回解析后的 dict 或 {"error": ...}。"""
    try:
        completed = subprocess.run(
            resolve_sharecrm_command()
            + [
                "sales",
                "product",
                "handleBomTree",
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


def is_fillable_rst(rst: dict) -> bool:
    """仅回填带 BOM 树字段的返回行，避免把普通产品回显行的折扣等字段误覆盖。"""
    return has_value(rst.get("prod_pkg_key")) or has_value(rst.get("_id"))


def apply_row(row: dict, rst: dict, detail_object_api_name: str) -> None:
    """按 BomService 字段映射回填一行；不覆盖未返回的 bom_core_id__r。"""
    for dest, src in DIRECT_FIELDS:
        if has_value(rst.get(src)):
            row[dest] = rst.get(src)

    discount = rst.get("price_book_discount")
    row["discount"] = 100 if not has_value(discount) else discount

    if has_value(rst.get("price_per_set")):
        row["price_per_set"] = rst.get("price_per_set")
    if has_value(rst.get("price_book_subtotal")):
        row["price_book_subtotal"] = rst.get("price_book_subtotal")
    if has_value(rst.get("price_tiered_record")):
        row["price_tiered_record"] = rst.get("price_tiered_record")

    if has_value(rst.get("_id")):
        row["bom_id"] = rst.get("_id")
    if has_value(rst.get("name")):
        row["bom_id__r"] = rst.get("name")

    pkg = rst.get("prod_pkg_key")
    root = rst.get("root_prod_pkg_key")
    # 原行可能已带 bom_core_id（步骤 3 子件/复用节点）；先清再按母件条件回填。
    row.pop("bom_core_id", None)
    if has_value(pkg) and pkg == root and has_value(rst.get("bom_core_id")):
        row["bom_core_id"] = rst.get("bom_core_id")

    if has_value(rst.get("bom_core_id__r")):
        row["bom_core_id__r"] = rst.get("bom_core_id__r")

    if has_value(rst.get("adjust_price")):
        if detail_object_api_name == QUOTE_LINES_OBJ:
            row["price"] = rst.get("adjust_price")
        else:
            row["product_price"] = rst.get("adjust_price")


class MatchError(ValueError):
    """temp_detail_id / product_id 匹配歧义。"""


def match_return_rows(original: list[dict], returned: list[dict]) -> list[tuple[int, dict]]:
    """返回 (原始行下标, 返回行)。优先 temp_detail_id，否则按 product_id 唯一匹配。"""
    orig_by_tid: dict[str, int] = {}
    for index, row in enumerate(original):
        tid = row_temp_id(row)
        if not tid:
            continue
        if tid in orig_by_tid:
            raise MatchError(f"原始明细 temp_detail_id 重复：{tid}")
        orig_by_tid[tid] = index

    pairs: list[tuple[int, dict]] = []
    matched_orig: set[int] = set()
    unmatched_ret: list[dict] = []
    used_ret_tids: set[str] = set()

    for rst in returned:
        tid = row_temp_id(rst)
        if tid and tid in orig_by_tid:
            if tid in used_ret_tids:
                raise MatchError(f"返回明细 temp_detail_id 重复：{tid}")
            used_ret_tids.add(tid)
            orig_index = orig_by_tid[tid]
            pairs.append((orig_index, rst))
            matched_orig.add(orig_index)
        else:
            unmatched_ret.append(rst)

    if not unmatched_ret:
        return pairs

    remaining = [index for index in range(len(original)) if index not in matched_orig]
    pid_to_indices: dict[str, list[int]] = {}
    for index in remaining:
        pid = row_product_id(original[index])
        if not pid:
            continue
        pid_to_indices.setdefault(pid, []).append(index)

    ret_pid_count: dict[str, int] = {}
    for rst in unmatched_ret:
        pid = row_product_id(rst)
        if pid:
            ret_pid_count[pid] = ret_pid_count.get(pid, 0) + 1

    for rst in unmatched_ret:
        pid = row_product_id(rst)
        if not pid:
            raise MatchError("无法使用 temp_detail_id 匹配，且返回行 product_id 为空")
        candidates = pid_to_indices.get(pid, [])
        if len(candidates) != 1 or ret_pid_count.get(pid, 0) != 1:
            raise MatchError(f"降级按 product_id 匹配出现歧义或无法唯一匹配：{pid}")
        orig_index = candidates[0]
        pairs.append((orig_index, rst))
        matched_orig.add(orig_index)
        pid_to_indices[pid] = []

    return pairs


def fail(status: str, error: str, data_list: list | None = None) -> None:
    payload: dict[str, Any] = {"status": status, "error": error}
    if data_list is not None:
        payload["dataList"] = data_list
    emit(payload)


def strip_temp_detail_ids(data_list: list[dict]) -> None:
    """匹配完成后移除内部匹配字段，禁止落库。"""
    for row in data_list:
        if isinstance(row, dict):
            row.pop("temp_detail_id", None)


def ready_payload(data_list: list[dict], detail_object_api_name: str) -> dict:
    strip_temp_detail_ids(data_list)
    return {
        "status": "READY",
        "detailObjectApiName": detail_object_api_name,
        "details": {detail_object_api_name: data_list},
    }


def run_bom_tree(raw_data: str) -> None:
    """tree 模式入口：校验入参 → 补 temp_detail_id → 调 handleBomTree → 匹配回填。"""
    try:
        payload = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        sys.exit(f"--data 不是合法 JSON：{exc}")

    if not isinstance(payload, dict):
        sys.exit("--data 必须是 JSON 对象")

    errors = validate_payload(payload)
    if errors:
        emit({"status": "INVALID_INPUT", "error": "；".join(errors)})
        return

    data_list = [dict(row) for row in payload["dataList"]]
    try:
        ensure_temp_detail_ids(data_list)
    except ValueError as exc:
        emit({"status": "INVALID_INPUT", "error": str(exc), "dataList": data_list})
        return

    detail_object_api_name = str(payload["detailObjectApiName"])
    resp = call_handle_bom_tree(build_api_payload(payload, data_list))
    if isinstance(resp, dict) and "error" in resp:
        fail("CLI_ERROR", resp["error"], data_list)
        return

    returned = extract_return_rows(resp)
    if not returned:
        fail("EMPTY_RESULT", "handleBomTree 返回为空，无法回填明细", data_list)
        return

    try:
        pairs = match_return_rows(data_list, returned)
    except MatchError as exc:
        fail("MATCH_ERROR", str(exc), data_list)
        return

    fill_pairs = [(index, rst) for index, rst in pairs if is_fillable_rst(rst)]
    if not fill_pairs:
        fail("EMPTY_RESULT", "找不到可安全回填的明细行", data_list)
        return

    matched_orig = {index for index, _rst in fill_pairs}
    missing_bom = [
        index
        for index, row in enumerate(data_list)
        if has_value(row.get("bom_core_id")) and index not in matched_orig
    ]
    if missing_bom:
        fail("EMPTY_RESULT", "已进入 BOM 流程的明细找不到可回填返回行", data_list)
        return

    filled = [dict(row) for row in data_list]
    for index, rst in fill_pairs:
        apply_row(filled[index], rst, detail_object_api_name)

    emit(ready_payload(filled, detail_object_api_name))


def main() -> None:
    parser = argparse.ArgumentParser(description="BOM 批处理统一脚本（按 --mode 切换）")
    parser.add_argument(
        "--mode",
        required=True,
        choices=sorted(PRESETS.keys()) + ["tree", "expand"],
        help="core=按 product_id 查 BomCoreObj；children=按 core_id 查 BOMObj 子产品；tree=调用 handleBomTree 并回填；expand=子产品递归展开",
    )
    parser.add_argument(
        "--data",
        required=True,
        help="JSON 对象，键随 mode 变化：core 用 product_ids，children 用 core_ids，tree 用 handleBomTree 入参，expand 用 mothers",
    )
    args = parser.parse_args()

    if args.mode == "tree":
        run_bom_tree(args.data)
        return

    if args.mode == "expand":
        run_expand(args.data)
        return

    preset = PRESETS[args.mode]
    data_key = preset["data_key"]

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as exc:
        sys.exit(f"--data 不是合法 JSON：{exc}")

    if not isinstance(data, dict):
        sys.exit("--data 必须是 JSON 对象")
    if data_key not in data:
        sys.exit(f"--data 必须包含 {data_key}")

    try:
        ids = normalize_ids(data[data_key], data_key)
    except ValueError as exc:
        sys.exit(f"--data 取值非法：{exc}")

    if not ids:
        # 空输入不发起 SQL 调用（IN() 为非法 SQL），直接返回空分组。
        print(json.dumps({"groups": {}, "total": 0}, ensure_ascii=False))
        return

    sql = build_sql(preset, ids)
    records, error = query_all_records(sql)
    if error:
        print(json.dumps({"error": error}, ensure_ascii=False))
        return

    groups = group_by(ids, records, preset["group_field"])
    hierarchy = preset.get("hierarchy_sort")
    if hierarchy:
        # children 模式：组内按父子层级 + 同级序号升序排序，父级在前、子级在后。
        for key, recs in groups.items():
            groups[key] = sort_hierarchy(recs, hierarchy["parent_field"], hierarchy["order_field"])
    print(json.dumps({"groups": groups, "total": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()