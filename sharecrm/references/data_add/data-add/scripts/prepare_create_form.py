#!/usr/bin/env python3
"""一步式准备 CRM 新建表单。

输入对象名称，脚本内部按顺序执行三个 CLI，把"识别对象 → 确定业务类型 → 拉新建表单"
压缩成一次调用：

1. identify-with-describe → 解析唯一目标对象 apiName
2. record-list           → 确定业务类型 record_type
3. get-create-form       → 拉取新建表单并裁剪（form_fields / field_metadata / initial_object_data）

脚本不替用户做任何"猜"的决定。遇到对象没唯一命中、或业务类型有多个候选时，
不会硬选一个，而是输出候选项并把 status 设为需要进一步确认，交回给调用方处理。

正常流程输出一行 JSON；上游 CLI 返回非法 JSON 或 `code != 0` 时，原样输出 CLI 内容。
调用方按 status 分支：
- OBJECT_NOT_FOUND               未匹配到任何可用对象（零命中或多命中全部查不到业务类型）；附提示
- OBJECT_NOT_RESOLVED            对象多命中需用户确认；附 object_candidates（每个候选含 record_types）
- RECORD_TYPE_SELECTION_REQUIRED 业务类型有多个，需用户选择；附 object_api_name 和 record_types
- READY                          已就绪；附 object_api_name、record_type 和裁剪后的 form

用法:
    # 首次调用：用口语对象名
    python prepare_create_form.py --object-name '客户'
    # 对象多命中、用户确认后：用确认的 apiName 直接跳过识别
    python prepare_create_form.py --object-api-name 'AccountObj'
    # 业务类型多选、用户选定后：带上 record-type（object-name 或 object-api-name 二选一）
    python prepare_create_form.py --object-api-name 'AccountObj' --record-type 'default__c'
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


class _DescribeError(Exception):
    """内部异常：承载一次 describe 调用失败的可读原因。

    由 `_run_describe` 抛出，再由外层包装函数决定如何处理：
    严格模式转成 `SystemExit`，容错模式吞掉返回 `None`。
    """


class _RawCliOutput(str):
    """需要由主流程原样输出的 CLI 返回内容。"""


def _run_describe(command: str, payload: dict[str, Any]) -> Any:
    """执行 + 解析的主体逻辑，严格模式与容错模式共用。

    成功时返回解析后的业务结果（兼容 {"code":0,"data":{...}} 包装与直接返回业务对象两种）；
    非法 JSON 或 `code != 0` 时返回 `_RawCliOutput`，由主流程原样输出；
    命令缺失、CLI 报错、空输出则抛出 `_DescribeError`。
    """
    try:
        completed = subprocess.run(
            resolve_sharecrm_command()
            + [
                "data",
                "describe",
                command,
                "-d",
                json.dumps(payload, ensure_ascii=False),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise _DescribeError("找不到 sharecrm 命令，请确认 CLI 已安装并在 PATH 中。") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        details = stderr or stdout or str(exc)
        raise _DescribeError(f"调用 sharecrm data describe {command} 失败：{details}") from exc

    raw_output = (completed.stdout or "").strip()
    if not raw_output:
        raise _DescribeError(f"sharecrm data describe {command} 没有返回内容。")

    try:
        response = json.loads(raw_output)
    except json.JSONDecodeError:
        return _RawCliOutput(raw_output)

    # 带 code/data 包装时，校验 code 并拆出 data
    if isinstance(response, dict) and "code" in response:
        if response.get("code") != 0:
            return _RawCliOutput(raw_output)
        return response.get("data")

    return response


def run_describe(command: str, payload: dict[str, Any]) -> Any:
    """调用 sharecrm data describe <command>，返回解析后的业务结果（严格模式）。

    兼容两种返回：带 {"code":0,"data":{...}} 包装的，和直接返回业务对象的。
    带包装时校验 code 并拆出 data；不带包装时原样返回。
    非法 JSON 或 `code != 0` 时返回 `_RawCliOutput`；其余失败 `raise SystemExit`。
    """
    try:
        return _run_describe(command, payload)
    except _DescribeError as exc:
        raise SystemExit(str(exc)) from exc


def run_describe_safe(command: str, payload: dict[str, Any]) -> Any | None:
    """`run_describe` 的容错版：相同的失败条件下返回 `None`，不抛异常。

    用于「逐对象批量查业务类型」等单点失败不应中断整体流程的场景。
    成功时返回值与 `run_describe` 完全一致。
    """
    try:
        result = _run_describe(command, payload)
        return None if isinstance(result, _RawCliOutput) else result
    except _DescribeError:
        return None


def emit(payload: dict[str, Any]) -> None:
    """输出一行 JSON 结果。"""
    print(json.dumps(payload, ensure_ascii=False))


def identify_object(
    object_name: str,
) -> _RawCliOutput | tuple[str | None, list[dict[str, Any]], str]:
    """识别目标对象。返回 (唯一命中的 apiName 或 None, 候选列表, resolution_status)。"""
    result = run_describe(
        "identify-with-describe",
        {"query": object_name, "include_simple_describe": False},
    )
    if isinstance(result, _RawCliOutput):
        return result
    if not isinstance(result, dict):
        raise SystemExit("identify-with-describe 返回格式不正确。")

    candidates = result.get("object_candidates") or []
    status = str(result.get("resolution_status") or "")

    if status == "RESOLVED" and len(candidates) == 1:
        api_name = str(candidates[0].get("object_api_name") or "").strip()
        if api_name:
            return api_name, candidates, status

    return None, candidates, status



def resolve_record_type(
    object_api_name: str,
) -> _RawCliOutput | tuple[str | None, list[dict[str, Any]]]:
    """自动判断业务类型。返回 (选定的 record_type 或 None, 业务类型候选列表)。

    仅在调用方未指定 --record-type 时使用：
    - 候选只有 1 个：自动采用。
    - 候选有多个：返回 None，交回调用方让用户选。
    - 候选为 0 个：无法继续，退出。

    调用方已确认业务类型时，直接采用其传入值，不会走这里（省一次 record-list 查询）。
    """
    result = run_describe("record-list", {"object_api_name": object_api_name})
    if isinstance(result, _RawCliOutput):
        return result
    if isinstance(result, dict):
        record_types = result.get("result") or []
    elif isinstance(result, list):
        record_types = result
    else:
        record_types = []

    if len(record_types) == 1 and isinstance(record_types[0], dict):
        return str(record_types[0].get("value")), record_types

    if len(record_types) == 0:
        raise SystemExit(f"对象 {object_api_name} 没有返回任何业务类型，无法继续。")

    return None, record_types


def fetch_record_types(object_api_name: str) -> list[dict[str, Any]]:
    """容错查询单个对象的业务类型列表，用于多命中分支批量列出。

    内部用 `run_describe_safe("record-list", ...)`，单点失败不会中断整体流程。
    返回规整后的 `record_types` 列表，每项至少含 `label` / `value`。
    查询失败（返回 `None`）或结果为空时，返回空列表 `[]`，由调用方据此剔除该对象。
    """
    result = run_describe_safe("record-list", {"object_api_name": object_api_name})
    if result is None:
        return []

    if isinstance(result, dict):
        raw_record_types = result.get("result") or []
    elif isinstance(result, list):
        raw_record_types = result
    else:
        return []

    record_types: list[dict[str, Any]] = []
    for item in raw_record_types:
        if not isinstance(item, dict):
            continue
        value = item.get("value")
        if value is None:
            continue
        record_types.append(
            {
                "label": item.get("label"),
                "value": str(value),
            }
        )

    return record_types


def build_multi_object_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """多命中分支：为每个候选对象查询业务类型，并过滤掉查不到的候选。

    遍历输入候选，对每个对象调用 `fetch_record_types`：
    - `record_types` 非空 → 保留该候选，输出 `{ object_api_name, label(透传展示信息), record_types }`；
      展示信息从原候选项透传（保留原候选的 `object_api_name` 与展示字段，如对象显示名）。
    - `record_types` 为空（查询失败或确实没有） → 直接剔除，不加入结果、不带任何错误标记。

    返回过滤后的候选列表（输入候选集合的子集）。列表为空时由调用方走 OBJECT_NOT_FOUND。
    """
    enriched: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        object_api_name = str(candidate.get("object_api_name") or "").strip()
        if not object_api_name:
            continue

        record_types = fetch_record_types(object_api_name)
        if not record_types:
            # 查询失败或为空 → 直接剔除，不带错误标记
            continue

        # 透传原候选的展示信息，并附上 record_types
        entry = dict(candidate)
        entry["object_api_name"] = object_api_name
        entry["record_types"] = record_types
        enriched.append(entry)

    return enriched


def load_create_form(object_api_name: str, record_type: str) -> Any:
    """拉取新建表单。"""
    return run_describe(
        "get-create-form",
        {"object_api_name": object_api_name, "record_type_apiName": record_type},
    )


def trim_form(form: dict[str, Any]) -> dict[str, Any]:
    """裁剪 `get-create-form` 返回的表单，保留 `form_fields` 与 `field_metadata` 两部分。

    步骤：
    1. 裁剪 `form_fields`：保留非只读字段（`is_readonly != true`）；但只读字段若为必填
       （`is_required == true`）也保留。其余只读且非必填的字段剔除。
    2. 裁剪 `field_metadata`：剪裁完 `form_fields` 后，只保留其中仍存在字段对应的描述数据
       （即 `field_metadata` 仅保留键名出现在裁剪后 `form_fields` 的 `field_name` 集合中的项）。
    3. `form_fields` 与 `field_metadata` 均原样保留各自的字段结构，不重组、不扁平化。
    4. `initial_object_data` 原样保留，但剔除 `data_own_department` 与 `created_by`
       两个字段——它们由系统按当前用户/负责人联动维护，不应作为初始可提交字段带入快照。

    返回 `{ "form_fields": [...], "field_metadata": {...}, "initial_object_data": {...} }`.
    """
    form = form if isinstance(form, dict) else {}

    raw_form_fields = form.get("form_fields") or []
    field_metadata = form.get("field_metadata")
    if not isinstance(field_metadata, dict):
        field_metadata = {}

    # 步骤 1：裁剪 form_fields —— 非只读保留；只读但必填也保留
    trimmed_form_fields: list[dict[str, Any]] = []
    kept_field_names: set[Any] = set()
    for layout_field in raw_form_fields:
        if not isinstance(layout_field, dict):
            continue

        is_readonly = layout_field.get("is_readonly") is True
        is_required = layout_field.get("is_required") is True
        if is_readonly and not is_required:
            continue

        trimmed_form_fields.append(layout_field)
        kept_field_names.add(layout_field.get("field_name"))

    # 步骤 2：field_metadata 只保留裁剪后 form_fields 中仍存在的字段
    trimmed_field_metadata = {
        name: meta
        for name, meta in field_metadata.items()
        if name in kept_field_names
    }

    # 步骤 3 & 4：两部分各自原样保留；initial_object_data 剔除系统联动字段
    initial_object_data = form.get("initial_object_data")
    if isinstance(initial_object_data, dict):
        initial_object_data = {
            key: value
            for key, value in initial_object_data.items()
            if key not in ("data_own_department", "created_by")
        }

    return {
        "form_fields": trimmed_form_fields,
        "field_metadata": trimmed_field_metadata,
        "initial_object_data": initial_object_data,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="一步完成识别对象、确定业务类型、拉取新建表单。"
    )
    parser.add_argument(
        "--object-name",
        "--object_name",
        dest="object_name",
        help="对象口语名称，例如 '客户' / '线索' / '销售合同'。首次调用用它，脚本内部识别成 apiName。",
    )
    parser.add_argument(
        "--object-api-name",
        "--object_api_name",
        dest="object_api_name",
        help=(
            "已确认的对象 apiName（如 'AccountObj'）。"
            "对象多命中（OBJECT_NOT_RESOLVED）经用户确认后，第二次调用传它直接跳过识别，避免再次多命中死循环。"
        ),
    )
    parser.add_argument(
        "--record-type",
        "--record_type",
        dest="record_type",
        help="业务类型提交值。已知或用户已选定时传入；不传则脚本自行判断或交回选择。",
    )
    args = parser.parse_args(argv)

    if not args.object_name and not args.object_api_name:
        parser.error("必须提供 --object-name（口语名）或 --object-api-name（已确认的 apiName）之一。")

    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    # 步骤 1：确定目标对象 apiName
    if args.object_api_name:
        # 调用方已传入确认过的 apiName（如多命中确认后），直接采用，跳过识别。
        object_api_name = args.object_api_name.strip()
        if not object_api_name:
            raise SystemExit("--object-api-name 不能为空。")
    else:
        # 仅有口语名：走识别。
        identification = identify_object(args.object_name)
        if isinstance(identification, _RawCliOutput):
            print(identification)
            return 0
        object_api_name, candidates, status = identification
        if object_api_name is None:
            # 零命中：一个对象都没匹配到
            if not candidates:
                emit(
                    {
                        "status": "OBJECT_NOT_FOUND",
                        "message": "未匹配到任何可用对象，请更换对象名称或确认该对象是否存在后重试。",
                    }
                )
                return 0

            # 多命中：为每个候选对象查询业务类型，查不到的剔除
            object_candidates = build_multi_object_candidates(candidates)
            if not object_candidates:
                # 所有候选都查不到业务类型 → 无任何可用候选
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
                    "object_candidates": object_candidates,
                    "message": "对象未唯一命中，请根据 object_candidates 列表判断最合适的对象，确认后用 --object-api-name '<确认的 apiName>' --record-type '<确认的 recordType>'  重试；若无法判断，再询问用户。",
                }
            )
            return 0

    # 步骤 2：确定业务类型
    if args.record_type:
        # 调用方已传入确认过的业务类型，直接采用，跳过 record-list 查询。
        record_type = args.record_type.strip()
        if not record_type:
            raise SystemExit("--record-type 不能为空。")
    else:
        record_type_result = resolve_record_type(object_api_name)
        if isinstance(record_type_result, _RawCliOutput):
            print(record_type_result)
            return 0
        record_type, record_types = record_type_result
        if record_type is None:
            emit(
                {
                    "status": "RECORD_TYPE_SELECTION_REQUIRED",
                    "object_api_name": object_api_name,
                    "record_types": record_types,
                    "message": "业务类型有多个候选，，请根据 record_types 列表判断最合适的业务类型 确认后用 --object-api-name '<确认的 apiName>' --record-type '<确认的 recordType>' 重试；若无法判断，再询问用户。",
                }
            )
            return 0

    # 步骤 3：拉取新建表单并裁剪
    form = load_create_form(object_api_name, record_type)
    if isinstance(form, _RawCliOutput):
        print(form)
        return 0
    emit(
        {
            "status": "READY",
            "object_api_name": object_api_name,
            "record_type": record_type,
            "form": trim_form(form),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
