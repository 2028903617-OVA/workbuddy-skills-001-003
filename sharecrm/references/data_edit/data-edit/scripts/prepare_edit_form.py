#!/usr/bin/env python3
"""一步式准备 CRM 编辑表单。

输入对象名称 + 记录关键词，脚本内部按顺序执行三个 CLI，把"识别对象 → 定位唯一记录 →
拉编辑表单"压缩成一次调用：

1. identify-with-describe → 解析唯一目标对象 apiName
2. query-id-by-name       → 按关键词定位唯一记录 data_id
3. get-edit-form          → 拉取编辑表单并裁剪（form_fields / field_metadata / object_data）

脚本不替用户做任何"猜"的决定。遇到对象没唯一命中、或记录有多个候选时，不会硬选一个，
而是输出候选项并把 status 设为需要进一步确认，交回给调用方处理。

与新建不同：编辑沿用记录已有的业务类型，不做业务类型选择；表单返回的 details/从对象
一律剔除，本脚本只服务主对象字段编辑。

输出始终是一行 JSON，调用方按 status 分支：
- OBJECT_NOT_FOUND     未匹配到任何可用对象；附提示
- OBJECT_NOT_RESOLVED  对象多命中需用户确认；附 object_candidates
- RECORD_NOT_FOUND     按关键词没查到记录；附提示，请用户换更准确的关键词
- RECORD_NOT_RESOLVED  记录多命中需用户确认；附 record_candidates（每项含 name / data_id）
- READY                已就绪；附 object_api_name、data_id 和裁剪后的 form

用法:
    # 首次调用：口语对象名 + 记录关键词
    python prepare_edit_form.py --object-name '客户' --record-query '北京华为'
    # 对象多命中、用户确认后：用确认的 apiName 跳过识别
    python prepare_edit_form.py --object-api-name 'AccountObj' --record-query '北京华为'
    # 记录多命中、用户选定后：直接带上确认的 data_id 跳过查询，直接就绪
    python prepare_edit_form.py --object-api-name 'AccountObj' --data-id '69e9a174...'
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Any


def resolve_sharecrm_command() -> list[str]:
    """解析 sharecrm 可执行入口，兼容 Windows batch 包装器。"""
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


class _CliError(Exception):
    """内部异常：承载一次 CLI 调用失败的可读原因。

    由 `_run_cli` 抛出，再由外层包装函数决定如何处理：严格模式转成 `SystemExit`。
    """


def _run_cli(args: list[str], payload: dict[str, Any], payload_flag: str) -> Any:
    """执行 + 解析的主体逻辑。

    `args` 是 sharecrm 之后的子命令片段（如 ['data','describe','get-edit-form']），
    `payload_flag` 是承载 JSON 的参数名（describe 用 '-d'，record 用 '--data'）。

    成功时返回解析后的业务结果（兼容 {"code":0,"data":{...}} 包装与直接返回业务对象两种）；
    任何失败（命令缺失、CLI 报错、空输出、非法 JSON、`code != 0`）都抛出 `_CliError`。
    """
    command_desc = " ".join(args)
    try:
        completed = subprocess.run(
            resolve_sharecrm_command()
            + args
            + [payload_flag, json.dumps(payload, ensure_ascii=False)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise _CliError("找不到 sharecrm 命令，请确认 CLI 已安装并在 PATH 中。") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        details = stderr or stdout or str(exc)
        raise _CliError(f"调用 sharecrm {command_desc} 失败：{details}") from exc

    raw_output = (completed.stdout or "").strip()
    if not raw_output:
        raise _CliError(f"sharecrm {command_desc} 没有返回内容。")

    try:
        response = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise _CliError(f"sharecrm {command_desc} 返回不是合法 JSON：{exc}") from exc

    if isinstance(response, dict) and "code" in response:
        if response.get("code") != 0:
            message = response.get("message") or "未知错误"
            raise _CliError(f"sharecrm {command_desc} 失败：{message}")
        return response.get("data")

    return response


def run_describe(command: str, payload: dict[str, Any]) -> Any:
    """调用 sharecrm data describe <command>（严格模式，失败即 SystemExit）。"""
    try:
        return _run_cli(["data", "describe", command], payload, "-d")
    except _CliError as exc:
        raise SystemExit(str(exc)) from exc


def run_record(command: str, payload: dict[str, Any]) -> Any:
    """调用 sharecrm data record <command>（严格模式，失败即 SystemExit）。"""
    try:
        return _run_cli(["data", "record", command], payload, "--data")
    except _CliError as exc:
        raise SystemExit(str(exc)) from exc


def emit(payload: dict[str, Any]) -> None:
    """输出一行 JSON 结果。"""
    print(json.dumps(payload, ensure_ascii=False))


def identify_object(object_name: str) -> tuple[str | None, list[dict[str, Any]]]:
    """识别目标对象。返回 (唯一命中的 apiName 或 None, 候选列表)。"""
    result = run_describe(
        "identify-with-describe",
        {"query": object_name, "include_simple_describe": False},
    )
    if not isinstance(result, dict):
        raise SystemExit("identify-with-describe 返回格式不正确。")

    candidates = result.get("object_candidates") or []
    status = str(result.get("resolution_status") or "")

    if status == "RESOLVED" and len(candidates) == 1:
        api_name = str(candidates[0].get("object_api_name") or "").strip()
        if api_name:
            return api_name, candidates

    return None, candidates


def _extract_record_list(result: Any) -> list[dict[str, Any]]:
    """从 query-id-by-name 的返回中规整出记录列表。

    真实返回形如：
        {"totalSize":1,"name2IdPos":[{"apiName":"AccountObj","name":"王小二",
                                       "rerankerScore":0.98,"id":"6a29..."}]}
    命中记录在 `name2IdPos` 数组里，每项含 `name` 和 `id`。这里以 `name2IdPos`
    为主，并对个别环境返回 list 的情况做兜底。返回一个 dict 列表（非 dict 项剔除）。
    """
    if isinstance(result, dict):
        raw = result.get("name2IdPos")
        if not isinstance(raw, list):
            # 极个别环境直接返回列表容器时的兜底
            raw = result.get("data") if isinstance(result.get("data"), list) else []
    elif isinstance(result, list):
        raw = result
    else:
        raw = []

    return [item for item in raw if isinstance(item, dict)]


def _record_id(record: dict[str, Any]) -> str:
    """从一条记录里取出主键 ID。query-id-by-name 用的是 `id`。"""
    for key in ("id", "_id", "data_id", "dataId"):
        value = record.get(key)
        if value:
            return str(value)
    return ""


def _record_name(record: dict[str, Any]) -> str:
    """从一条记录里取出展示名称。"""
    for key in ("name", "title", "label"):
        value = record.get(key)
        if value:
            return str(value)
    return ""


def locate_record(
    object_api_name: str, record_query: str
) -> tuple[str | None, list[dict[str, Any]]]:
    """按关键词定位唯一记录。返回 (唯一 data_id 或 None, 规整后的候选列表)。

    - 命中 1 条：返回该 data_id。
    - 命中多条：返回 None + 候选列表（每项含 name / data_id），交回让用户选。
    - 命中 0 条：返回 (None, [])，由调用方走 RECORD_NOT_FOUND。
    """
    result = run_record(
        "query-id-by-name",
        {"query": record_query, "apiNames": [object_api_name]},
    )
    records = _extract_record_list(result)

    normalized: list[dict[str, Any]] = []
    for record in records:
        data_id = _record_id(record)
        if not data_id:
            continue
        normalized.append({"name": _record_name(record), "data_id": data_id})

    if len(normalized) == 1:
        return normalized[0]["data_id"], normalized

    return None, normalized


def load_edit_form(object_api_name: str, data_id: str) -> Any:
    """拉取编辑表单。"""
    return run_describe(
        "get-edit-form",
        {"object_api_name": object_api_name, "data_id": data_id},
    )


def trim_form(form: dict[str, Any]) -> dict[str, Any]:
    """整理 `get-edit-form` 返回的表单，保留 `form_fields` / `field_metadata` / `object_data`。

    与新建不同，编辑**不裁剪只读字段**：agent 需要 `form_fields` 里完整的
    `is_readonly` 标记才能判断哪些字段不能改、要原样保留。裁掉只读字段会让 agent
    丢失这一信息，反而可能误写只读字段。所以这里三部分全部原样保留：

    1. `form_fields`：全部字段原样保留（含只读字段及其 `is_readonly` 标记）。
    2. `field_metadata`：原样保留。
    3. `object_data`：作为构造修改快照的基础底座，但只保留出现在 `field_metadata`
       中的字段——未在 `field_metadata` 里描述的属性不是可编辑字段，剔除可避免把它们
       误带进更新快照；同时额外剔除 `owner_department_id`——它是负责人所属部门，由系统
       按负责人联动维护，不应作为可提交字段带进更新快照。
    4. `details`/从对象数据一律不返回——本脚本只服务主对象字段编辑。

    返回 `{ "form_fields": [...], "field_metadata": {...}, "object_data": {...} }`。
    """
    form = form if isinstance(form, dict) else {}

    form_fields = form.get("form_fields") or []
    field_metadata = form.get("field_metadata")
    if not isinstance(field_metadata, dict):
        field_metadata = {}

    object_data = form.get("object_data")
    if isinstance(object_data, dict):
        object_data = {
            key: value
            for key, value in object_data.items()
            if key != "owner_department_id" and key in field_metadata
        }

    return {
        "form_fields": form_fields,
        "field_metadata": field_metadata,
        "object_data": object_data,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="一步完成识别对象、定位唯一记录、拉取编辑表单。"
    )
    parser.add_argument(
        "--object-name",
        "--object_name",
        dest="object_name",
        help="对象口语名称，例如 '客户' / '联系人' / '商机'。首次调用用它，脚本内部识别成 apiName。",
    )
    parser.add_argument(
        "--object-api-name",
        "--object_api_name",
        dest="object_api_name",
        help=(
            "已确认的对象 apiName（如 'AccountObj'）。对象多命中（OBJECT_NOT_RESOLVED）"
            "经用户确认后，第二次调用传它直接跳过识别，避免再次多命中死循环。"
        ),
    )
    parser.add_argument(
        "--record-query",
        "--record_query",
        dest="record_query",
        help="记录关键词：名称、编号、标题等，用于按名定位记录。未确定 data_id 时必传。",
    )
    parser.add_argument(
        "--data-id",
        "--data_id",
        dest="data_id",
        help=(
            "已确认的记录主键。记录多命中（RECORD_NOT_RESOLVED）经用户选定后，传它直接"
            "跳过查询进入就绪；传它时可不传 --record-query。"
        ),
    )
    args = parser.parse_args(argv)

    if not args.object_name and not args.object_api_name:
        parser.error("必须提供 --object-name（口语名）或 --object-api-name（已确认的 apiName）之一。")

    if not args.record_query and not args.data_id:
        parser.error("必须提供 --record-query（记录关键词）或 --data-id（已确认的记录主键）之一。")

    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    # 步骤 1：确定目标对象 apiName
    if args.object_api_name:
        object_api_name = args.object_api_name.strip()
        if not object_api_name:
            raise SystemExit("--object-api-name 不能为空。")
    else:
        object_api_name, candidates = identify_object(args.object_name)
        if object_api_name is None:
            if not candidates:
                emit(
                    {
                        "status": "OBJECT_NOT_FOUND",
                        "message": "未匹配到任何可用对象，请更换对象名称或确认该对象是否存在后重试。",
                    }
                )
                return 0

            emit(
                {
                    "status": "OBJECT_NOT_RESOLVED",
                    "object_candidates": candidates,
                    "message": (
                        "对象未唯一命中，请根据 object_candidates 判断最合适的对象，确认后用 "
                        "--object-api-name '<确认的 apiName>' --record-query '<记录关键词>' 重试；"
                        "若无法判断，再询问用户。"
                    ),
                }
            )
            return 0

    # 步骤 2：定位唯一记录 data_id
    if args.data_id:
        data_id = args.data_id.strip()
        if not data_id:
            raise SystemExit("--data-id 不能为空。")
    else:
        data_id, record_candidates = locate_record(object_api_name, args.record_query)
        if data_id is None:
            if not record_candidates:
                emit(
                    {
                        "status": "RECORD_NOT_FOUND",
                        "object_api_name": object_api_name,
                        "message": "按该关键词没有查到记录，请用更准确的名称/编号后重试。",
                    }
                )
                return 0

            emit(
                {
                    "status": "RECORD_NOT_RESOLVED",
                    "object_api_name": object_api_name,
                    "record_candidates": record_candidates,
                    "message": (
                        "记录未唯一命中，请把 record_candidates（含 name / data_id）交用户选择，"
                        "选定后用 --object-api-name '<apiName>' --data-id '<选定的 data_id>' 重试；"
                        "选定前不要写入任何候选 ID。"
                    ),
                }
            )
            return 0

    # 步骤 3：拉取编辑表单并裁剪
    form = load_edit_form(object_api_name, data_id)
    emit(
        {
            "status": "READY",
            "object_api_name": object_api_name,
            "data_id": data_id,
            "form": trim_form(form),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
