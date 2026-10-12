#!/usr/bin/env python3
"""Create a governed CSV for a large ShareCRM RECORD query.

Read one JSON envelope from stdin and write exactly one result JSON object to
stdout. The query plan stays in memory; only the final CSV is published under
the current ShareAgent run's releasefile directory.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional


# 本环境 sharecrm 单页实际最多返回 50 条（appliedLimit 上限为 50），
# 因此分页大小须设为 50，否则 validate_page 会因 appliedLimit 不符而失败。
PAGE_SIZE = 50
DEFAULT_ROW_LIMIT = 20_000
MAX_ROW_LIMIT = 20_000
# 571 条 / 50 ≈ 12 页，预留余量设为 20。
MAX_PAGES = 20
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024
MAX_DIRECTORY_SIZE_BYTES = 400 * 1024 * 1024
SINGLE_PAGE_TIMEOUT_SECONDS = 90
TOTAL_TIMEOUT_SECONDS = 30 * 60
MAX_RETRIES_PER_PAGE = 2

RESERVED_QUERY_KEYS = {"execution_mode", "executionMode", "limit", "offset"}
NON_RECORD_QUERY_KEYS = {"aggregates", "aggregation", "aggregations", "groupings", "group_by", "having"}
ALLOWED_QUERY_KEYS = {
    "object_api_name",
    "object_display_name",
    "relations",
    "groupings",
    "select_fields",
    "aggregates",
    "having",
    "filters",
    "order_by",
    "distinct",
    "question",
    "frame_id",
    "search_source",
}
DENIAL_CODES = {
    "VIEW_LIST_PERMISSION_DENIED",
    "EXPORT_PERMISSION_DENIED",
    "OBJECT_NOT_FOUND",
    "FIELD_NOT_FOUND",
    "FIELD_NOT_FILTERABLE",
}
AGGREGATE_EXPRESSION = re.compile(r"^\s*(COUNT|SUM|AVG|MIN|MAX)\s*\(", re.IGNORECASE)
FORMULA_PREFIX = ("=", "+", "-", "@")
SAFE_FILE_COMPONENT = re.compile(r"[^\w\-\.]+", re.UNICODE)
MULTIPLE_UNDERSCORES = re.compile(r"_+")


class FileAnalysisError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False, stage: str = "input"):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.stage = stage


@dataclass(frozen=True)
class Workspace:
    root: Path
    temp_dir: Path
    release_dir: Path
    temp_fd: int
    release_fd: int


@dataclass(frozen=True)
class PageWindow:
    requested_limit: int
    applied_limit: int
    returned_count: int


@dataclass(frozen=True)
class PageResult:
    query_mode: str
    display_rows: list[dict[str, Any]]
    matched_total: Optional[int]
    page: PageWindow
    notice_codes: list[str]
    data_security: dict[str, Any]


@dataclass
class FileAnalysisResult:
    status: str
    file_path: Optional[str]
    file_name: Optional[str]
    file_label: Optional[str]
    file_format: Optional[str]
    object_api_name: str
    object_display_name: Optional[str]
    is_cross_object: bool
    rows_written: int
    matched_total: Optional[int]
    pages_queried: int
    page_size: int
    truncated: bool
    stop_reason: str
    consistency: str
    notice_codes: list[str]
    schema_drift: bool
    schema_drift_columns: list[str]
    data_security: dict[str, Any]
    elapsed_ms: int
    error: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.error is None:
            payload.pop("error")
        payload["schema_version"] = "1"
        return payload


PageRunner = Callable[[dict[str, Any]], str]


def validate_envelope(value: Any) -> tuple[str, dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {"workspace_dir", "object_data_query"}:
        raise FileAnalysisError(
            "INVALID_INPUT",
            "Input must contain only workspace_dir and object_data_query.",
        )
    workspace_dir = value["workspace_dir"]
    query = value["object_data_query"]
    if not isinstance(workspace_dir, str) or not workspace_dir.strip():
        raise FileAnalysisError("INVALID_WORKSPACE", "workspace_dir must be a non-empty path.")
    if not isinstance(query, dict):
        raise FileAnalysisError("INVALID_INPUT", "object_data_query must be a JSON object.")
    return workspace_dir, query


def resolve_workspace(workspace_dir: str) -> Workspace:
    requested = Path(workspace_dir).expanduser()
    if not requested.exists() or not requested.is_dir() or requested.is_symlink():
        raise FileAnalysisError("INVALID_WORKSPACE", "workspace_dir must be an existing non-symlink directory.")
    root = requested.resolve(strict=True)

    root_fd = _open_directory(root)
    temp_fd: Optional[int] = None
    release_fd: Optional[int] = None
    try:
        temp_fd = _open_child_directory(root_fd, "tempfile")
        release_fd = _open_child_directory(root_fd, "releasefile")
        return Workspace(
            root=root,
            temp_dir=root / "tempfile",
            release_dir=root / "releasefile",
            temp_fd=temp_fd,
            release_fd=release_fd,
        )
    except OSError as exc:
        raise FileAnalysisError("INVALID_WORKSPACE", "Required run directory is unavailable.") from exc
    finally:
        os.close(root_fd)
        if temp_fd is not None and release_fd is None:
            os.close(temp_fd)


def _directory_open_flags() -> int:
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise FileAnalysisError("INVALID_WORKSPACE", "Runtime does not support secure run directory access.")
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def _open_directory(path: Path) -> int:
    try:
        directory_fd = os.open(str(path), _directory_open_flags())
    except OSError as exc:
        raise FileAnalysisError("INVALID_WORKSPACE", "workspace_dir is unavailable.") from exc
    try:
        if not stat.S_ISDIR(os.fstat(directory_fd).st_mode):
            raise FileAnalysisError("INVALID_WORKSPACE", "workspace_dir is unavailable.")
        return directory_fd
    except Exception:
        os.close(directory_fd)
        raise


def _open_child_directory(parent_fd: int, name: str) -> int:
    directory_fd = os.open(name, _directory_open_flags(), dir_fd=parent_fd)
    try:
        if not stat.S_ISDIR(os.fstat(directory_fd).st_mode):
            raise OSError("Required run directory is unavailable.")
        return directory_fd
    except Exception:
        os.close(directory_fd)
        raise


def close_workspace(workspace: Workspace) -> None:
    for directory_fd in (workspace.temp_fd, workspace.release_fd):
        try:
            os.close(directory_fd)
        except OSError:
            pass


def normalize_query(query: Mapping[str, Any], offset: int) -> tuple[dict[str, Any], str]:
    if not isinstance(query, Mapping):
        raise FileAnalysisError("INVALID_INPUT", "object_data_query must be a JSON object.")
    conflicting_keys = sorted(RESERVED_QUERY_KEYS.intersection(query))
    if conflicting_keys:
        raise FileAnalysisError("INVALID_INPUT", "Paging and execution mode are controlled by this script.")
    unknown_keys = sorted(set(query).difference(ALLOWED_QUERY_KEYS))
    if unknown_keys:
        raise FileAnalysisError("INVALID_INPUT", "object_data_query contains an unsupported field.")
    if NON_RECORD_QUERY_KEYS.intersection(query):
        raise FileAnalysisError("INVALID_INPUT", "File analysis only supports RECORD queries.")
    if query.get("relations"):
        raise FileAnalysisError("INVALID_INPUT", "File analysis only supports single-object queries.")
    if query.get("distinct") is True:
        raise FileAnalysisError("INVALID_INPUT", "File analysis does not support distinct queries.")
    if "distinct" in query and not isinstance(query["distinct"], bool):
        raise FileAnalysisError("INVALID_INPUT", "distinct must be a boolean when provided.")

    object_api_name = query.get("object_api_name")
    select_fields = query.get("select_fields")
    order_by = query.get("order_by")
    if not isinstance(object_api_name, str) or not object_api_name.strip():
        raise FileAnalysisError("INVALID_INPUT", "object_api_name is required.")
    if not isinstance(select_fields, list) or not select_fields or not all(isinstance(item, str) and item.strip() for item in select_fields):
        raise FileAnalysisError("INVALID_INPUT", "select_fields must be a non-empty string array.")
    if any(AGGREGATE_EXPRESSION.match(item) for item in select_fields):
        raise FileAnalysisError("INVALID_INPUT", "File analysis only supports RECORD fields.")
    if not isinstance(order_by, list) or not order_by:
        raise FileAnalysisError("MISSING_DETERMINISTIC_ORDER", "order_by is required for file analysis.")
    validate_deterministic_order(order_by)

    normalized = dict(query)
    raw_display_name = normalized.pop("object_display_name", None)
    if raw_display_name is not None and not isinstance(raw_display_name, str):
        raise FileAnalysisError("INVALID_INPUT", "object_display_name must be a string when provided.")
    display_name = raw_display_name.strip() if isinstance(raw_display_name, str) else ""
    display_name = display_name or object_api_name.strip()
    normalized["object_api_name"] = object_api_name.strip()
    normalized["execution_mode"] = "SCRIPT"
    normalized["limit"] = PAGE_SIZE
    normalized["offset"] = offset
    return normalized, display_name


def validate_deterministic_order(order_by: list[Any]) -> None:
    for item in order_by:
        if not isinstance(item, Mapping):
            raise FileAnalysisError("MISSING_DETERMINISTIC_ORDER", "order_by must contain valid sort fields.")
        unsupported = set(item).difference({"field", "function", "direction", "is_asc"})
        field = item.get("field")
        direction = item.get("direction")
        is_asc = item.get("is_asc")
        function = item.get("function")
        if (unsupported or not isinstance(field, str) or not field.strip()
                or AGGREGATE_EXPRESSION.match(field) or function is not None):
            raise FileAnalysisError("MISSING_DETERMINISTIC_ORDER", "order_by must use RECORD fields without functions.")
        if direction is not None:
            if not isinstance(direction, str) or direction.strip().upper() not in {"ASC", "DESC"}:
                raise FileAnalysisError("MISSING_DETERMINISTIC_ORDER", "order_by direction must be ASC or DESC.")
        if is_asc is not None and not isinstance(is_asc, bool):
            raise FileAnalysisError("MISSING_DETERMINISTIC_ORDER", "order_by is_asc must be a boolean.")
        if direction is None and is_asc is None:
            raise FileAnalysisError("MISSING_DETERMINISTIC_ORDER", "order_by direction is required.")
        if direction is not None and is_asc is not None and (direction.strip().upper() == "ASC") != is_asc:
            raise FileAnalysisError("MISSING_DETERMINISTIC_ORDER", "order_by direction is inconsistent.")


def build_file_name(display_name: str, now: datetime, suffix: str) -> str:
    timestamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%f")[:-3] + "Z"
    return "data-analysis-%s-%s-%s.csv" % (sanitize_file_component(display_name), timestamp, suffix)


def sanitize_file_component(value: str) -> str:
    cleaned = SAFE_FILE_COMPONENT.sub("_", str(value).strip())
    cleaned = MULTIPLE_UNDERSCORES.sub("_", cleaned).strip("_.")
    return cleaned[:48] or "object"


def parse_page_response(raw: str) -> PageResult:
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned an invalid response.", stage="sharecrm_query") from exc
    if not isinstance(data, dict) or "code" in data or "data" in data:
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned an invalid response.", stage="sharecrm_query")
    query_meta = data.get("queryMeta")
    if not isinstance(query_meta, dict):
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned an invalid query meta.", stage="sharecrm_query")
    notice_codes = extract_notice_codes(query_meta)
    denial_code = next((code for code in notice_codes if code in DENIAL_CODES), None)
    if denial_code:
        raise FileAnalysisError(denial_code, "The requested query is not permitted.", stage="sharecrm_query")

    page_data = query_meta.get("page")
    if not isinstance(page_data, dict):
        page_data = query_meta
    page = PageWindow(
        requested_limit=require_int(page_data.get("requestedLimit"), "queryMeta.requestedLimit"),
        applied_limit=require_int(page_data.get("appliedLimit"), "queryMeta.appliedLimit"),
        returned_count=require_int(page_data.get("returnedCount"), "queryMeta.returnedCount"),
    )

    record_result = data.get("recordResult")
    if data.get("queryMode") != "RECORD":
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "File analysis requires a RECORD response.", stage="sharecrm_query")
    # 非 --raw 模式：recordResult 直接为记录数组（键名为中文显示名，值为展示值），无 totalNumber。
    if not isinstance(record_result, list):
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned invalid record rows.", stage="sharecrm_query")
    records = record_result
    # 非 --raw 模式不返回 totalNumber，matched_total 置为 None，由主循环用
    # "返回数 < PAGE_SIZE" 作为末页兜底判断。
    matched_total = None
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned invalid record rows.", stage="sharecrm_query")
    if page.returned_count != len(records):
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned inconsistent page metadata.", stage="sharecrm_query")
    data_security = query_meta.get("data_security")
    if data_security is None:
        data_security = {}
    if not isinstance(data_security, dict):
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned invalid data security metadata.", stage="sharecrm_query")
    return PageResult(
        query_mode="RECORD",
        display_rows=[dict(row) for row in records],
        matched_total=matched_total,
        page=page,
        notice_codes=notice_codes,
        data_security=data_security,
    )


def extract_notice_codes(query_meta: Any) -> list[str]:
    if not isinstance(query_meta, dict):
        return []
    notices = query_meta.get("notices", [])
    if not isinstance(notices, list):
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned invalid notices.", stage="sharecrm_query")
    codes = []
    for notice in notices:
        if not isinstance(notice, dict):
            raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned invalid notices.", stage="sharecrm_query")
        code = notice.get("code")
        if isinstance(code, str) and code:
            codes.append(code)
    return codes


def require_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned invalid %s." % label, stage="sharecrm_query")
    return value


def resolve_sharecrm_command() -> list[str]:
    executable = shutil.which("sharecrm")
    if executable:
        if os.name == "nt" and executable.lower().endswith((".cmd", ".bat")):
            return ["cmd", "/c", executable]
        return [executable]
    if os.name == "nt":
        return ["cmd", "/c", "sharecrm"]
    return ["sharecrm"]


def run_sharecrm_page(query: dict[str, Any]) -> str:
    # 注意：不使用 --raw。非 --raw 模式返回结构为
    # {"queryMode","queryMeta":{"page":{...}},"recordResult":[...]}，
    # 记录键为字段中文显示名，值直接是展示值（如 来源=招商资源）。
    command = resolve_sharecrm_command() + [
        "semantic",
        "object-data-query",
        "--data",
        json.dumps(query, ensure_ascii=False, separators=(",", ":")),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=SINGLE_PAGE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise FileAnalysisError("SHARECRM_UNAVAILABLE", "ShareCRM command is unavailable.", retryable=False, stage="sharecrm_query") from exc
    except subprocess.TimeoutExpired as exc:
        raise FileAnalysisError("SHARECRM_TIMEOUT", "ShareCRM request timed out.", retryable=True, stage="sharecrm_query") from exc
    if completed.returncode != 0:
        raise FileAnalysisError("SHARECRM_QUERY_FAILED", "ShareCRM query failed.", retryable=False, stage="sharecrm_query")
    raw = (completed.stdout or "").strip()
    if not raw:
        raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned no response.", stage="sharecrm_query")
    return raw


def execute_page(query: dict[str, Any], runner: PageRunner) -> PageResult:
    last_error: Optional[FileAnalysisError] = None
    for attempt in range(MAX_RETRIES_PER_PAGE + 1):
        try:
            return parse_page_response(runner(query))
        except FileAnalysisError as error:
            last_error = error
            if not error.retryable or attempt == MAX_RETRIES_PER_PAGE:
                raise
            time.sleep(min(2 ** attempt, 2))
    raise last_error or FileAnalysisError("SHARECRM_QUERY_FAILED", "ShareCRM query failed.", stage="sharecrm_query")


def run_file_analysis(
    workspace_dir: str,
    object_data_query: dict[str, Any],
    runner: PageRunner = run_sharecrm_page,
    row_limit: int = DEFAULT_ROW_LIMIT,
    now_provider: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    suffix_provider: Callable[[], str] = lambda: secrets.token_hex(3),
) -> FileAnalysisResult:
    started = time.monotonic()
    object_api_name = str(object_data_query.get("object_api_name", "")) if isinstance(object_data_query, dict) else ""
    display_name = None
    rows_written = 0
    pages_queried = 0
    matched_total: Optional[int] = None
    notice_codes: list[str] = []
    data_security = {"masked": False, "mask_policy_degraded": False}
    workspace: Optional[Workspace] = None
    part_name: Optional[str] = None
    final_path: Optional[Path] = None
    file_name: Optional[str] = None
    publish_status: Optional[str] = None
    stop_reason: Optional[str] = None
    schema_drift = False
    schema_drift_columns: list[str] = []
    try:
        workspace = resolve_workspace(workspace_dir)
        normalized_first_query, display_name = normalize_query(object_data_query, offset=0)
        object_api_name = normalized_first_query["object_api_name"]
        effective_row_limit = resolve_row_limit(row_limit)
        page = execute_page(normalized_first_query, runner)
        pages_queried = 1
        notice_codes.extend(page.notice_codes)
        merge_data_security(data_security, page.data_security)
        validate_page(page)
        matched_total = page.matched_total
        if matched_total == 0:
            return completed_result(
                object_api_name, display_name, object_data_query, rows_written, matched_total, pages_queried,
                "EMPTY_RESULT", notice_codes, data_security, started,
            )

        file_name, part_name, final_path, part_fd = allocate_output_file(
            workspace, display_name, now_provider, suffix_provider
        )
        headers = collect_headers(page.display_rows)
        if not headers:
            raise FileAnalysisError("PLATFORM_RESPONSE_INVALID", "ShareCRM returned no rows for a non-empty result.", stage="sharecrm_query")
        with os.fdopen(part_fd, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            handle.flush()
            while publish_status is None:
                handle.flush()
                limit_reason = would_exceed_limits(workspace, part_fd, headers, page.display_rows)
                if limit_reason:
                    if rows_written == 0:
                        raise FileAnalysisError(
                            limit_reason, "The CSV cannot include a complete result page.", stage="file_publish"
                        )
                    publish_status = "PARTIAL"
                    stop_reason = limit_reason
                    break
                new_columns = find_new_columns(headers, page.display_rows)
                if new_columns:
                    publish_status = "PARTIAL"
                    stop_reason = "SCHEMA_DRIFT"
                    schema_drift = True
                    schema_drift_columns = new_columns
                    break
                # 仅当 matched_total 已知时做超额写入检查；非 --raw 模式 matched_total 为 None，跳过。
                if matched_total is not None and rows_written + page.page.returned_count > matched_total:
                    if rows_written == 0:
                        raise FileAnalysisError(
                            "PAGINATION_INCONSISTENT",
                            "ShareCRM returned more rows than its matched total.",
                            stage="sharecrm_query",
                        )
                    publish_status = "PARTIAL"
                    stop_reason = "PAGINATION_INCONSISTENT"
                    break
                write_rows(writer, headers, page.display_rows)
                rows_written += len(page.display_rows)
                # 末页兜底：非 --raw 模式不返回 totalNumber，当本页返回数 < PAGE_SIZE
                # 即视为已到末页，写完即结束（ALL_ROWS_READ）。
                is_last_page = page.page.returned_count < PAGE_SIZE
                if matched_total is not None:
                    # matched_total 已知时仍做精确一致性校验
                    if rows_written > matched_total:
                        if rows_written - len(page.display_rows) == 0:
                            raise FileAnalysisError(
                                "PAGINATION_INCONSISTENT",
                                "ShareCRM returned more rows than its matched total.",
                                stage="sharecrm_query",
                            )
                        publish_status = "PARTIAL"
                        stop_reason = "PAGINATION_INCONSISTENT"
                        break
                    if rows_written >= matched_total:
                        publish_status = "COMPLETED"
                        stop_reason = "ALL_ROWS_READ"
                        break
                if is_last_page:
                    publish_status = "COMPLETED"
                    stop_reason = "ALL_ROWS_READ"
                    break
                if rows_written >= effective_row_limit:
                    publish_status = "PARTIAL"
                    stop_reason = "MAX_ROWS_REACHED"
                    break
                if pages_queried >= MAX_PAGES or time.monotonic() - started > TOTAL_TIMEOUT_SECONDS:
                    publish_status = "PARTIAL"
                    stop_reason = "MAX_PAGES_REACHED" if pages_queried >= MAX_PAGES else "TIME_LIMIT_REACHED"
                    break
                next_offset = pages_queried * PAGE_SIZE
                next_query, _ = normalize_query(object_data_query, offset=next_offset)
                try:
                    page = execute_page(next_query, runner)
                except FileAnalysisError as error:
                    if rows_written > 0 and error.retryable:
                        publish_status = "PARTIAL"
                        stop_reason = "QUERY_ERROR_AFTER_PARTIAL"
                        break
                    raise
                pages_queried += 1
                notice_codes.extend(page.notice_codes)
                merge_data_security(data_security, page.data_security)
                try:
                    validate_page(
                        page,
                        expected_total=matched_total,
                    )
                except FileAnalysisError:
                    if rows_written > 0:
                        publish_status = "PARTIAL"
                        stop_reason = "PAGINATION_INCONSISTENT"
                        break
                    raise
                if not page.display_rows:
                    publish_status = "PARTIAL"
                    stop_reason = "PAGINATION_INCONSISTENT"
                    break
            close_and_sync(handle)
        if publish_status is None or stop_reason is None:
            raise FileAnalysisError("FILE_PUBLISH_FAILED", "CSV writing ended without a result.", stage="file_publish")
        file_name, final_path = publish_output(
            workspace, part_name, file_name, final_path, display_name, now_provider, suffix_provider
        )
        part_name = None
        if publish_status == "PARTIAL":
            return partial_result(
                file_name, final_path, object_api_name, display_name, object_data_query, rows_written,
                matched_total, pages_queried, stop_reason, notice_codes, data_security, started,
                schema_drift=schema_drift, schema_drift_columns=schema_drift_columns,
            )
        return completed_result(
            object_api_name, display_name, object_data_query, rows_written, matched_total, pages_queried,
            stop_reason, notice_codes, data_security, started, file_name=file_name, final_path=final_path,
        )
    except FileAnalysisError as error:
        if workspace is not None:
            delete_if_exists(workspace.temp_fd, part_name)
        return failed_result(object_api_name, display_name, object_data_query, pages_queried, started, error)
    except OSError:
        if workspace is not None:
            delete_if_exists(workspace.temp_fd, part_name)
        return failed_result(
            object_api_name,
            display_name,
            object_data_query,
            pages_queried,
            started,
            FileAnalysisError("FILE_PUBLISH_FAILED", "Could not safely publish the CSV.", stage="file_publish"),
        )
    finally:
        if workspace is not None:
            close_workspace(workspace)


def resolve_row_limit(row_limit: int) -> int:
    if isinstance(row_limit, bool) or not isinstance(row_limit, int):
        raise FileAnalysisError("INVALID_RUNTIME_CONFIG", "Row limit must be an integer.", stage="runtime_config")
    effective = min(row_limit, MAX_ROW_LIMIT)
    effective = effective // PAGE_SIZE * PAGE_SIZE
    if effective < PAGE_SIZE:
        raise FileAnalysisError("INVALID_RUNTIME_CONFIG", "Row limit must allow at least one full page.", stage="runtime_config")
    return effective


def close_and_sync(handle: Any) -> None:
    handle.flush()
    os.fsync(handle.fileno())


def validate_page(
    page: PageResult,
    expected_total: Optional[int] = None,
) -> None:
    if page.page.requested_limit != PAGE_SIZE or page.page.applied_limit != PAGE_SIZE:
        raise FileAnalysisError("PAGINATION_INCONSISTENT", "ShareCRM did not apply the fixed page size.", stage="sharecrm_query")
    if page.page.returned_count > PAGE_SIZE:
        raise FileAnalysisError(
            "PAGINATION_INCONSISTENT",
            "ShareCRM returned more rows than the fixed page size.",
            stage="sharecrm_query",
        )
    if expected_total is not None and page.matched_total != expected_total:
        raise FileAnalysisError("PAGINATION_INCONSISTENT", "ShareCRM total changed during file analysis.", stage="sharecrm_query")


def merge_data_security(summary: dict[str, Any], page_data_security: dict[str, Any]) -> None:
    masked_infos = page_data_security.get("masked_field_infos")
    if isinstance(masked_infos, list) and masked_infos:
        summary["masked"] = True
    if page_data_security.get("mask_policy_degraded") is True:
        summary["mask_policy_degraded"] = True


def allocate_output_file(
    workspace: Workspace,
    display_name: str,
    now_provider: Callable[[], datetime],
    suffix_provider: Callable[[], str],
) -> tuple[str, str, Path, int]:
    for _ in range(16):
        file_name = build_file_name(display_name, now_provider(), suffix_provider())
        part_name = file_name + ".part"
        final_path = workspace.release_dir / file_name
        if directory_entry_exists(workspace.release_fd, file_name):
            continue
        try:
            part_fd = os.open(
                part_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=workspace.temp_fd,
            )
        except FileExistsError:
            continue
        except OSError as exc:
            raise FileAnalysisError("FILE_PUBLISH_FAILED", "Could not allocate the output file.", stage="file_publish") from exc
        return file_name, part_name, final_path, part_fd
    raise FileAnalysisError("FILE_PUBLISH_FAILED", "Could not allocate a unique output file.", stage="file_publish")


def write_rows(writer: csv.writer, headers: list[str], rows: list[dict[str, Any]]) -> None:
    for row in rows:
        writer.writerow([csv_value(row.get(header)) for header in headers])


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, str):
        stripped = value.lstrip()
        if stripped.startswith(FORMULA_PREFIX):
            return "'" + stripped
    return value


def find_new_columns(headers: list[str], rows: list[dict[str, Any]]) -> list[str]:
    header_set = set(headers)
    new_columns = []
    for row in rows:
        for key in row:
            if key not in header_set and key not in new_columns:
                new_columns.append(key)
                if len(new_columns) == 20:
                    return new_columns
    return new_columns


def collect_headers(rows: list[dict[str, Any]]) -> list[str]:
    headers = []
    for row in rows:
        for field in row:
            if field not in headers:
                headers.append(field)
    return headers


def directory_entry_exists(directory_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise FileAnalysisError("FILE_PUBLISH_FAILED", "Could not inspect the output directory.", stage="file_publish") from exc
    return True


def directory_size_bytes(directory_fd: int) -> int:
    total = 0
    try:
        names = os.listdir(directory_fd)
    except OSError as exc:
        raise FileAnalysisError("FILE_PUBLISH_FAILED", "Could not inspect the output directory.", stage="file_publish") from exc
    for name in names:
        try:
            entry = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise FileAnalysisError("FILE_PUBLISH_FAILED", "Could not inspect the output directory.", stage="file_publish") from exc
        if stat.S_ISREG(entry.st_mode):
            total += entry.st_size
    return total


def would_exceed_limits(
    workspace: Workspace, part_fd: int, headers: list[str], rows: list[dict[str, Any]]
) -> Optional[str]:
    estimated = encoded_csv_rows_size(headers, rows)
    current_file_size = os.fstat(part_fd).st_size
    directory_size = directory_size_bytes(workspace.temp_fd) + directory_size_bytes(workspace.release_fd)
    if current_file_size + estimated > MAX_FILE_SIZE_BYTES:
        return "FILE_SIZE_LIMIT_REACHED"
    if directory_size + estimated > MAX_DIRECTORY_SIZE_BYTES:
        return "DIRECTORY_SIZE_LIMIT_REACHED"
    return None


def encoded_csv_rows_size(headers: list[str], rows: list[dict[str, Any]]) -> int:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    write_rows(writer, headers, rows)
    return len(output.getvalue().encode("utf-8"))


def publish_output(
    workspace: Workspace,
    part_name: str,
    file_name: str,
    final_path: Path,
    display_name: str,
    now_provider: Callable[[], datetime],
    suffix_provider: Callable[[], str],
) -> tuple[str, Path]:
    for attempt in range(16):
        try:
            os.link(
                part_name,
                file_name,
                src_dir_fd=workspace.temp_fd,
                dst_dir_fd=workspace.release_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            if attempt == 15:
                raise FileAnalysisError(
                    "FILE_PUBLISH_FAILED", "Could not allocate a unique output file.", stage="file_publish"
                )
            file_name = build_file_name(display_name, now_provider(), suffix_provider())
            final_path = workspace.release_dir / file_name
            continue
        except OSError as exc:
            raise FileAnalysisError("FILE_PUBLISH_FAILED", "Could not safely publish the CSV.", stage="file_publish") from exc
        delete_if_exists(workspace.temp_fd, part_name)
        return file_name, final_path
    raise FileAnalysisError("FILE_PUBLISH_FAILED", "Could not allocate a unique output file.", stage="file_publish")


def partial_result(
    file_name: str,
    final_path: Path,
    object_api_name: str,
    display_name: str,
    query: dict[str, Any],
    rows_written: int,
    matched_total: Optional[int],
    pages_queried: int,
    reason: str,
    notice_codes: list[str],
    data_security: dict[str, Any],
    started: float,
    schema_drift: bool = False,
    schema_drift_columns: Optional[list[str]] = None,
) -> FileAnalysisResult:
    return result(
        status="PARTIAL",
        file_name=file_name,
        final_path=final_path,
        object_api_name=object_api_name,
        display_name=display_name,
        query=query,
        rows_written=rows_written,
        matched_total=matched_total,
        pages_queried=pages_queried,
        truncated=True,
        stop_reason=reason,
        notice_codes=notice_codes,
        data_security=data_security,
        started=started,
        schema_drift=schema_drift,
        schema_drift_columns=schema_drift_columns,
    )


def completed_result(
    object_api_name: str,
    display_name: Optional[str],
    query: dict[str, Any],
    rows_written: int,
    matched_total: Optional[int],
    pages_queried: int,
    stop_reason: str,
    notice_codes: list[str],
    data_security: dict[str, Any],
    started: float,
    file_name: Optional[str] = None,
    final_path: Optional[Path] = None,
) -> FileAnalysisResult:
    return result(
        status="COMPLETED",
        file_name=file_name,
        final_path=final_path,
        object_api_name=object_api_name,
        display_name=display_name,
        query=query,
        rows_written=rows_written,
        matched_total=matched_total,
        pages_queried=pages_queried,
        truncated=False,
        stop_reason=stop_reason,
        notice_codes=notice_codes,
        data_security=data_security,
        started=started,
    )


def result(
    status: str,
    file_name: Optional[str],
    final_path: Optional[Path],
    object_api_name: str,
    display_name: Optional[str],
    query: dict[str, Any],
    rows_written: int,
    matched_total: Optional[int],
    pages_queried: int,
    truncated: bool,
    stop_reason: str,
    notice_codes: list[str],
    data_security: dict[str, Any],
    started: float,
    schema_drift: bool = False,
    schema_drift_columns: Optional[list[str]] = None,
) -> FileAnalysisResult:
    return FileAnalysisResult(
        status=status,
        file_path=str(final_path) if final_path else None,
        file_name=file_name,
        file_label=(display_name + " data analysis") if final_path and display_name else None,
        file_format="csv" if final_path else None,
        object_api_name=object_api_name,
        object_display_name=display_name,
        is_cross_object=bool(query.get("relations")),
        rows_written=rows_written,
        matched_total=matched_total,
        pages_queried=pages_queried,
        page_size=PAGE_SIZE,
        truncated=truncated,
        stop_reason=stop_reason,
        consistency="BEST_EFFORT_OFFSET",
        notice_codes=deduplicate(notice_codes),
        schema_drift=schema_drift,
        schema_drift_columns=list(schema_drift_columns or []),
        data_security=data_security,
        elapsed_ms=int((time.monotonic() - started) * 1000),
    )


def failed_result(
    object_api_name: str,
    display_name: Optional[str],
    query: Any,
    pages_queried: int,
    started: float,
    error: FileAnalysisError,
) -> FileAnalysisResult:
    return FileAnalysisResult(
        status="FAILED",
        file_path=None,
        file_name=None,
        file_label=None,
        file_format=None,
        object_api_name=object_api_name,
        object_display_name=display_name,
        is_cross_object=bool(query.get("relations")) if isinstance(query, dict) else False,
        rows_written=0,
        matched_total=None,
        pages_queried=pages_queried,
        page_size=PAGE_SIZE,
        truncated=False,
        stop_reason="FAILED",
        consistency="BEST_EFFORT_OFFSET",
        notice_codes=[],
        schema_drift=False,
        schema_drift_columns=[],
        data_security={"masked": False, "mask_policy_degraded": False},
        elapsed_ms=int((time.monotonic() - started) * 1000),
        error={"code": error.code, "message": error.message, "retryable": error.retryable, "stage": error.stage},
    )


def deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def delete_if_exists(directory_fd: int, name: Optional[str]) -> None:
    if name is not None:
        try:
            os.unlink(name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        except OSError:
            pass


def main() -> None:
    started = time.monotonic()
    try:
        envelope = json.load(sys.stdin)
        workspace_dir, query = validate_envelope(envelope)
        result_payload = run_file_analysis(workspace_dir, query)
    except FileAnalysisError as error:
        result_payload = failed_result("", None, {}, 0, started, error)
    except (OSError, json.JSONDecodeError):
        result_payload = failed_result(
            "",
            None,
            {},
            0,
            started,
            FileAnalysisError("INVALID_INPUT", "Input must be a valid JSON envelope."),
        )
    print(json.dumps(result_payload.to_dict(), ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
