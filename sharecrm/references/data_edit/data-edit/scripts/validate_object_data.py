#!/usr/bin/env python3
"""CRM 对象数据校验脚本。

根据 object_api_name 和 data_id 调用 get-edit-form 获取布局和字段元数据，
对传入的 object_data 进行格式校验。

用法:
    python validate_object_data.py \\
        --object-api-name '<object_api_name>' \\
        --data-id '<data_id>' \\
        --object-data '<JSON或@文件路径>'
"""
from __future__ import annotations

import argparse
import os
import json
import shutil
import subprocess
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 13 位毫秒级 Unix 时间戳正则
MILLISECOND_TIMESTAMP_PATTERN = re.compile(r"^\d{13}$")

# ---- 字段类型分组 ----
# 文本类：需要校验字符串类型、最大长度、正则匹配
TEXT_TYPES = {"text", "long_text", "phone_number", "email", "url"}
# 日期类：需要校验是否为 13 位毫秒时间戳
DATE_TYPES = {"date", "date_time"}
# 数值类：需要校验是否为数值类型
NUMBER_TYPES = {"number", "currency", "percentile", "percent", "count", "summary"}
# 布尔类
BOOLEAN_TYPES = {"true_or_false"}
# 单选类：需要校验值是否在 options 列表中
SELECT_ONE_TYPES = {"select_one", "record_type"}
# 多选类：需要校验值为数组且每个元素都在 options 中
SELECT_MANY_TYPES = {"select_many"}
# 单引用类：需要校验值是否为非空记录 ID 字符串
REFERENCE_ONE_TYPES = {"object_reference", "master_detail"}
# 多引用类：需要校验值是否为非空 ID 数组
REFERENCE_MANY_TYPES = {"object_reference_many"}
# ID 数组类：需要校验值是否为 ID 数组
ID_ARRAY_TYPES = {"employee", "out_employee", "department", "dimension"}

# 销售记录 ActiveRecordObj 的 what_list 关联字段
ACTIVE_RECORD_OBJECT_API_NAME = "ActiveRecordObj"
ACTIVE_RECORD_RELATED_DATA_FIELD = "related_object_data"
ACTIVE_RECORD_RELATED_API_NAMES_FIELD = "related_api_names"
ACTIVE_RECORD_RELATED_GROUP_FIELD = "related_object"


@dataclass
class Issue:
    """校验问题：包含字段名、错误信息和可选的修复建议。"""
    field: str
    message: str
    suggestion: str | None = None


def load_json_argument(raw: str, label: str) -> Any:
    """解析 JSON 参数。支持直接传入 JSON 字符串或以 @ 开头的文件路径。"""
    value = raw.strip()
    if value.startswith("@"):
        value = Path(value[1:]).read_text(encoding="utf-8-sig")
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} 不是合法 JSON：{exc}") from exc


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


def run_sharecrm_describe(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    """调用 sharecrm describe CLI 并返回 data 字段。"""
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
        raise SystemExit("找不到 sharecrm 命令，请确认 CLI 已安装并在 PATH 中。") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        error_message = stderr or stdout or str(exc)
        raise SystemExit(f"调用 sharecrm data describe {command} 失败：{error_message}") from exc

    raw_output = (completed.stdout or "").strip()
    if not raw_output:
        raise SystemExit(f"sharecrm data describe {command} 没有返回内容。")

    try:
        response = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"sharecrm data describe {command} 返回不是合法 JSON：{exc}") from exc

    if not isinstance(response, dict):
        raise SystemExit(f"sharecrm data describe {command} 返回格式不正确。")

    if response.get("code") != 0:
        message = response.get("message") or "未知错误"
        raise SystemExit(f"sharecrm data describe {command} 失败：{message}")

    data = response.get("data")
    if not isinstance(data, dict):
        raise SystemExit(f"sharecrm data describe {command} 返回缺少 data 对象。")
    return data


def load_edit_layout(object_api_name: str, data_id: str) -> tuple[Any, Any]:
    """拉取编辑表单布局数据。"""
    data = run_sharecrm_describe(
        "get-edit-form",
        {
            "object_api_name": object_api_name,
            "data_id": data_id,
        },
    )
    return data.get("form_fields"), data.get("field_metadata")


def first_present(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """从 mapping 中按顺序查找第一个存在的 key，返回其值。"""
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def comparable(value: Any) -> str:
    """将值转为字符串，用于类型宽松的比较。"""
    return str(value)


def value_equals(left: Any, right: Any) -> bool:
    """比较两个值是否相等，先直接比较，再转为字符串比较。"""
    return left == right or comparable(left) == comparable(right)


def normalize_type(value: Any) -> str:
    """标准化字段类型名：转小写、替换连字符和空格为下划线。"""
    if value is None:
        return ""
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def is_truthy(value: Any) -> bool:
    """判断值是否为"真"，支持 bool、数值、字符串形式的布尔值。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def is_missing(value: Any) -> bool:
    """判断值是否为空（None、空字符串、空列表、空字典）。"""
    return value is None or value == "" or value == [] or value == {}


def is_required(field: dict[str, Any]) -> bool:
    """判断字段是否为必填。支持多种必填标记字段名。"""
    return any(
        is_truthy(field.get(key))
        for key in ("is_required",)
    )


def field_name(field: dict[str, Any]) -> str:
    """从字段配置中提取字段 API 名称。支持多种可能的 key。"""
    name = first_present(field, ("field_name", "api_name"))
    return str(name or "").strip()


def field_type(form_field: dict[str, Any] | None, metadata: dict[str, Any] | None) -> str:
    """获取字段的标准化类型。优先使用 metadata.type，其次使用 form_field 的 render_type。"""
    if metadata:
        meta_type = normalize_type(metadata.get("type"))
        if meta_type:
            return meta_type
    if form_field:
        return normalize_type(form_field.get("render_type"))
    return ""


def field_label(form_field: dict[str, Any] | None, metadata: dict[str, Any] | None) -> str:
    """获取字段的中文标签，优先从 metadata 获取。"""
    label = None
    if metadata:
        label = metadata.get("label")
    if label is None and form_field:
        label = form_field.get("label")
    return str(label or "").strip()


def build_form_field_map(form_fields: Any, errors: list[Issue]) -> dict[str, dict[str, Any]]:
    """将 form_fields 数组转为以字段名为 key 的字典。"""
    if not isinstance(form_fields, list):
        errors.append(Issue("form_fields", "必须是 get-edit-form 返回的 form_fields JSON 数组。"))
        return {}

    fields: dict[str, dict[str, Any]] = {}
    for index, raw_field in enumerate(form_fields):
        if not isinstance(raw_field, dict):
            errors.append(Issue(f"form_fields[{index}]", "必须是对象。"))
            continue
        name = field_name(raw_field)
        if not name:
            errors.append(Issue(f"form_fields[{index}]", "必须包含 field_name 或 api_name。"))
            continue
        fields[name] = raw_field
    return fields


def build_metadata_map(field_metadata: Any, errors: list[Issue]) -> dict[str, dict[str, Any]]:
    """将 field_metadata 对象转为以字段名为 key 的字典。field_metadata 的 key 是默认字段名，value 中的 api_name 优先。"""
    if not isinstance(field_metadata, dict):
        errors.append(Issue("field_metadata", "必须是 get-edit-form 返回的 field_metadata JSON 对象。"))
        return {}

    metadata: dict[str, dict[str, Any]] = {}
    for fallback_name, raw_field in field_metadata.items():
        if not isinstance(raw_field, dict):
            continue
        field = dict(raw_field)
        name = field_name(field) or str(fallback_name).strip()
        if name:
            metadata[name] = field
    return metadata


def extract_options(field: dict[str, Any] | None) -> list[dict[str, Any]]:
    """从字段配置中提取选项列表，统一为 [{"value": ..., "label": ...}] 格式。"""
    if not field:
        return []
    raw_options = field.get("options")
    if not isinstance(raw_options, list):
        return []

    options: list[dict[str, Any]] = []
    for item in raw_options:
        if isinstance(item, dict):
            value = first_present(item, ("value", "api_name", "apiname"))
            if value is None:
                continue
            options.append({"value": value, "label": item.get("label", value)})
        else:
            options.append({"value": item, "label": item})
    return options


def option_value_set(options: list[dict[str, Any]]) -> list[Any]:
    """提取所有选项的 value 列表。"""
    return [option["value"] for option in options]


def find_label_match(value: Any, options: list[dict[str, Any]]) -> dict[str, Any] | None:
    """在选项中查找 label 匹配但 value 不匹配的选项（用户可能误传了 label 而非 value）。"""
    for option in options:
        label = option.get("label")
        option_value = option.get("value")
        if label is not None and not value_equals(label, option_value) and value_equals(value, label):
            return option
    return None


def is_valid_option_value(value: Any, options: list[dict[str, Any]]) -> bool:
    """判断值是否为合法的选项值（与任一 option value 匹配）。"""
    return any(value_equals(value, option.get("value")) for option in options)


def format_json(value: Any) -> str:
    """将值格式化为 JSON 字符串，用于错误信息展示。"""
    return json.dumps(value, ensure_ascii=False)


def add_type_error(errors: list[Issue], name: str, expected: str, value: Any, suggestion: str | None = None) -> None:
    """添加一条类型不匹配的错误。"""
    errors.append(Issue(name, f"必须为{expected}；当前值为 {format_json(value)}。", suggestion))


def validate_option_value(field_name_: str, value: Any, options: list[dict[str, Any]], issues: list[Issue]) -> None:
    """校验选项值：先检查是否为合法值，再检查是否为 label（给出修正建议）。"""
    if is_valid_option_value(value, options):
        return

    # 检查用户是否误传了选项的 label 而非 value
    label_match = find_label_match(value, options)
    if label_match is not None:
        issues.append(
            Issue(
                field_name_,
                f"当前传入的是展示值 {format_json(value)}；请改为提交值 {format_json(label_match['value'])}。",
                f"将 {format_json(value)} 替换为 {format_json(label_match['value'])}。",
            )
        )
        return

    issues.append(
        Issue(
            field_name_,
            f"必须是以下选项提交值之一：{format_json(option_value_set(options))}；当前值为 {format_json(value)}。",
            "请使用 field_metadata.options 中的 value，不要使用 label。",
        )
    )


def validate_string(name: str, value: Any, errors: list[Issue], *, type_label: str = "字符串") -> bool:
    """校验值是否为非空字符串。"""
    if not isinstance(value, str) or value.strip() == "":
        add_type_error(errors, name, type_label, value)
        return False
    return True


def validate_text_constraints(name: str, value: Any, metadata: dict[str, Any] | None, errors: list[Issue]) -> None:
    """校验文本类字段的额外约束：最大长度和正则模式匹配。"""
    if not validate_string(name, value, errors):
        return

    if not metadata:
        return

    # 校验最大长度
    max_length = first_present(metadata, ("max_length", "maxlength"))
    if max_length is not None:
        try:
            max_length_int = int(max_length)
        except (TypeError, ValueError):
            max_length_int = None
        if max_length_int is not None and len(value) > max_length_int:
            errors.append(Issue(name, f"长度不能超过 {max_length_int} 个字符。"))

    # 校验正则模式
    pattern = metadata.get("pattern")
    if isinstance(pattern, str) and pattern:
        try:
            compiled = re.compile(pattern)
        except re.error:
            return
        if not compiled.search(value):
            errors.append(Issue(name, f"必须匹配正则表达式 {format_json(pattern)}。"))


def validate_number(name: str, value: Any, errors: list[Issue]) -> None:
    """校验值是否为数值类型（排除 bool）。支持字符串形式的数值。"""
    if isinstance(value, bool):
        add_type_error(errors, name, "数值", value)
        return
    if isinstance(value, (int, float)):
        return
    if isinstance(value, str):
        try:
            float(value)
            return
        except ValueError:
            pass
    add_type_error(errors, name, "数值", value)


def validate_boolean(name: str, value: Any, errors: list[Issue]) -> None:
    """校验值是否为布尔类型。"""
    if not isinstance(value, bool):
        add_type_error(errors, name, "布尔值", value)


def validate_millisecond_timestamp(name: str, value: Any, errors: list[Issue]) -> None:
    """校验值是否为 13 位毫秒级 Unix 时间戳（支持 int 和数字字符串）。"""
    if isinstance(value, bool):
        valid = False
    elif isinstance(value, int):
        valid = bool(MILLISECOND_TIMESTAMP_PATTERN.fullmatch(str(value)))
    elif isinstance(value, str):
        valid = bool(MILLISECOND_TIMESTAMP_PATTERN.fullmatch(value.strip()))
    else:
        valid = False

    if not valid:
        add_type_error(
            errors,
            name,
            "13 位毫秒级 Unix 时间戳",
            value,
            '示例：1790352000000。不要使用秒级时间戳、"YYYYMMDD" 或 ISO/日期字符串。',
        )


def validate_string_array(name: str, value: Any, errors: list[Issue], suggestion: str) -> bool:
    """校验值是否为非空 ID/字符串数组。"""
    if not isinstance(value, list):
        add_type_error(errors, name, "数组", value, suggestion)
        return False
    invalid = [item for item in value if not isinstance(item, (str, int)) or str(item).strip() == ""]
    if invalid:
        errors.append(Issue(name, "数组元素必须是非空 ID 或字符串。", suggestion))
        return False
    return True


def validate_reference_many(name: str, value: Any, errors: list[Issue]) -> None:
    """校验多引用字段：值必须为记录 ID 数组。"""
    validate_string_array(name, value, errors, '请使用 ["<record_id>"]。')


def validate_related_object(name: str, value: Any, errors: list[Issue]) -> None:
    """校验 related_object 字段：值必须为 {ObjectApiName: ["id1", "id2", ...]} 格式。"""
    if not isinstance(value, dict):
        add_type_error(errors, name, '形如 {"ObjectApiName": ["id1", "id2"]} 的对象', value)
        return
    for obj_name, ids in value.items():
        if not isinstance(obj_name, str) or not obj_name.strip():
            errors.append(Issue(f"{name}.key", "对象 apiName 必须是非空字符串。"))
            continue
        if not isinstance(ids, list):
            errors.append(
                Issue(
                    f"{name}.{obj_name}",
                    f"必须是记录 ID 数组；当前值为 {format_json(ids)}。",
                    f'请使用 ["<record_id>"]，不要使用 {format_json(ids)}。',
                )
            )
            continue
        for idx, item in enumerate(ids):
            if not isinstance(item, (str, int)) or str(item).strip() == "":
                errors.append(
                    Issue(
                        f"{name}.{obj_name}[{idx}]",
                        f"必须是非空记录 ID；当前值为 {format_json(item)}。",
                    )
                )


def is_active_record_object(object_api_name: str) -> bool:
    """判断当前对象是否为销售记录对象。"""
    return object_api_name.strip() == ACTIVE_RECORD_OBJECT_API_NAME


def is_active_record_related_field(name: str) -> bool:
    """判断字段是否为 ActiveRecordObj 专属 what_list 关联字段。"""
    return name in {
        ACTIVE_RECORD_RELATED_DATA_FIELD,
        ACTIVE_RECORD_RELATED_API_NAMES_FIELD,
        ACTIVE_RECORD_RELATED_GROUP_FIELD,
    }


def unique_preserve_order(values: list[str]) -> list[str]:
    """按首次出现顺序去重。"""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def validate_active_record_related_fields(object_api_name: str, object_data: dict[str, Any], errors: list[Issue]) -> None:
    """校验销售记录 ActiveRecordObj 的 related_object_data / related_api_names 组合格式。"""
    if not is_active_record_object(object_api_name):
        return

    if ACTIVE_RECORD_RELATED_GROUP_FIELD in object_data and not is_missing(object_data.get(ACTIVE_RECORD_RELATED_GROUP_FIELD)):
        errors.append(
            Issue(
                ACTIVE_RECORD_RELATED_GROUP_FIELD,
                "ActiveRecordObj 不允许提交 related_object；请改用 related_object_data 和 related_api_names。",
                "移除 related_object，按 references/ActiveRecordObj.md 的格式提交。",
            )
        )

    has_related_data = ACTIVE_RECORD_RELATED_DATA_FIELD in object_data
    has_related_api_names = ACTIVE_RECORD_RELATED_API_NAMES_FIELD in object_data
    if not has_related_data and not has_related_api_names:
        return

    if not has_related_data:
        errors.append(
            Issue(
                ACTIVE_RECORD_RELATED_DATA_FIELD,
                "ActiveRecordObj 提交关联业务模块时必须同时提供 related_object_data。",
            )
        )
        return
    if not has_related_api_names:
        errors.append(
            Issue(
                ACTIVE_RECORD_RELATED_API_NAMES_FIELD,
                "ActiveRecordObj 提交关联业务模块时必须同时提供 related_api_names。",
            )
        )
        return

    related_data = object_data.get(ACTIVE_RECORD_RELATED_DATA_FIELD)
    related_api_names = object_data.get(ACTIVE_RECORD_RELATED_API_NAMES_FIELD)

    if not isinstance(related_data, list):
        add_type_error(
            errors,
            ACTIVE_RECORD_RELATED_DATA_FIELD,
            "数组，元素形如 {\"describe_api_name\":\"AccountObj\",\"id\":\"...\",\"name\":\"...\"}",
            related_data,
        )
        return

    if not isinstance(related_api_names, list):
        add_type_error(
            errors,
            ACTIVE_RECORD_RELATED_API_NAMES_FIELD,
            "对象 apiName 数组",
            related_api_names,
            '示例：["AccountObj"]。',
        )
        return

    described_api_names: list[str] = []
    for index, item in enumerate(related_data):
        item_field = f"{ACTIVE_RECORD_RELATED_DATA_FIELD}[{index}]"
        if not isinstance(item, dict):
            errors.append(
                Issue(
                    item_field,
                    "必须是包含 describe_api_name、id、name 的对象。",
                )
            )
            continue

        describe_api_name = item.get("describe_api_name")
        record_id = item.get("id")
        record_name = item.get("name")

        if not isinstance(describe_api_name, str) or not describe_api_name.strip():
            errors.append(Issue(f"{item_field}.describe_api_name", "必须是非空对象 apiName 字符串。"))
        else:
            described_api_names.append(describe_api_name.strip())

        if not isinstance(record_id, str) or not record_id.strip():
            errors.append(Issue(f"{item_field}.id", "必须是非空记录 ID 字符串。"))

        if not isinstance(record_name, str) or not record_name.strip():
            errors.append(Issue(f"{item_field}.name", "必须是非空记录名称字符串。"))

    actual_api_names: list[str] = []
    for index, item in enumerate(related_api_names):
        if not isinstance(item, str) or not item.strip():
            errors.append(Issue(f"{ACTIVE_RECORD_RELATED_API_NAMES_FIELD}[{index}]", "必须是非空对象 apiName 字符串。"))
            continue
        actual_api_names.append(item.strip())

    expected_api_names = unique_preserve_order(described_api_names)
    if actual_api_names != expected_api_names:
        errors.append(
            Issue(
                ACTIVE_RECORD_RELATED_API_NAMES_FIELD,
                f"必须等于 related_object_data[].describe_api_name 去重后的结果 {format_json(expected_api_names)}；当前值为 {format_json(actual_api_names)}。",
                "按 related_object_data 中的 describe_api_name 重算 related_api_names。",
            )
        )


def validate_known_field(
    name: str,
    value: Any,
    form_field: dict[str, Any] | None,
    metadata: dict[str, Any] | None,
    object_data: dict[str, Any],  # noqa: ARG001 保留以保持接口一致，后续可能用于跨字段校验
    errors: list[Issue],
    warnings: list[Issue],
) -> None:
    """根据字段类型对已知字段的值进行格式校验。按优先级匹配：select_many > select_one/有options > date > number > boolean > text > id_array > reference_one > reference_many > 未知类型。"""
    ftype = field_type(form_field, metadata)
    options = extract_options(metadata) or extract_options(form_field)

    # 多选字段：值必须是数组，每个元素必须为合法选项值
    if ftype in SELECT_MANY_TYPES:
        if not isinstance(value, list):
            add_type_error(errors, name, "select_many 字段的数组", value)
            return
        if options:
            for index, item in enumerate(value):
                validate_option_value(f"{name}[{index}]", item, options, errors)
        return

    # 单选字段或有选项的字段：值必须是单选值（不能是数组），若存在 options 则校验合法性
    if ftype in SELECT_ONE_TYPES or options:
        if isinstance(value, list):
            add_type_error(errors, name, "单个选项提交值", value)
            return
        if options:
            validate_option_value(name, value, options, errors)
        elif not isinstance(value, (str, int, float)):
            add_type_error(errors, name, "单个选项提交值", value)
        return

    # 日期字段：校验 13 位毫秒时间戳
    if ftype in DATE_TYPES:
        validate_millisecond_timestamp(name, value, errors)
        return

    # 数值字段
    if ftype in NUMBER_TYPES:
        validate_number(name, value, errors)
        return

    # 布尔字段
    if ftype in BOOLEAN_TYPES:
        validate_boolean(name, value, errors)
        return

    # 文本字段：校验字符串 + 长度和正则约束
    if ftype in TEXT_TYPES:
        validate_text_constraints(name, value, metadata, errors)
        return

    # ID 数组字段
    if ftype in ID_ARRAY_TYPES:
        validate_string_array(name, value, errors, '请使用 ["<id>"]。')
        return

    # 单引用字段：校验为非空记录 ID 字符串
    if ftype in REFERENCE_ONE_TYPES:
        validate_string(name, value, errors, type_label="非空记录 ID 字符串")
        return

    # 多引用字段：校验为记录 ID 数组
    if ftype in REFERENCE_MANY_TYPES:
        validate_reference_many(name, value, errors)
        return

    # 字段类型不在任何已知分组中：仅发出警告，不做格式校验
    if not ftype:
        warnings.append(Issue(name, "字段类型缺失，未执行格式校验。"))
    else:
        warnings.append(Issue(name, f"字段类型 {format_json(ftype)} 无法识别，未执行格式校验。"))


def validate_object_data(
    object_api_name: str,
    form_fields: Any,
    field_metadata: Any,
    object_data: Any,
) -> tuple[list[Issue], list[Issue]]:
    """主校验函数。

    对 object_data 执行两类校验：
    1. 必填字段检查：遍历 form_fields + field_metadata 中标记为必填的字段，检查 object_data 中是否存在。
    2. 字段值格式校验：遍历 object_data 中的每个字段，根据其类型进行格式校验。
        - 在 form_field_map / metadata_map 中找不到的字段给出警告但不报错

    Returns:
        (errors, warnings): 错误列表和警告列表。errors 为空时校验通过。
    """
    errors: list[Issue] = []
    warnings: list[Issue] = []

    form_field_map = build_form_field_map(form_fields, errors)
    metadata_map = build_metadata_map(field_metadata, errors)

    if not isinstance(object_data, dict):
        errors.append(Issue("object_data", "必须是 JSON 对象。"))
        return errors, warnings

    validate_active_record_related_fields(object_api_name, object_data, errors)

    # ---- 必填字段检查 ----
    all_known_fields = set(form_field_map) | set(metadata_map)
    for name in sorted(all_known_fields):
        form_field = form_field_map.get(name)
        metadata = metadata_map.get(name)
        required_source = form_field or metadata
        if required_source and is_required(required_source) and is_missing(object_data.get(name)):
            label = field_label(form_field, metadata)
            message = "是必填字段，但 object_data 中缺少该字段。"
            if label:
                message = f"{message} 字段标签：{label}。"
            errors.append(
                Issue(
                    name,
                    message,
                    "请告知用户必须输入",
                )
            )

    # ---- 字段值格式校验 ----
    for name, value in object_data.items():
        # 跳过空值字段（必填缺失已在上面检查）
        if is_missing(value):
            continue

        if is_active_record_object(object_api_name) and is_active_record_related_field(name):
            continue

        form_field = form_field_map.get(name)
        metadata = metadata_map.get(name)

        # related_object 特殊字段：校验 {ObjectApiName: ["id1", ...]} 格式
        if name == "related_object":
            validate_related_object(name, value, errors)
            continue

        # 字段在 form_fields 和 field_metadata 中都找不到，仅警告
        if metadata is None and form_field is None:
            warnings.append(
                Issue(
                    name,
                    "字段未出现在 form_fields 或 field_metadata 中，未执行格式校验。",
                    "请核对该字段 apiName 是否来自 get-edit-form。",
                )
            )
            continue

        # 字段在 field_metadata 中找不到，回退使用 form_fields 的 render_type（精度较低）
        if metadata is None:
            warnings.append(
                Issue(
                    name,
                    "字段未出现在 field_metadata 中，已回退使用 form_fields.render_type 进行校验。",
                )
            )

        validate_known_field(name, value, form_field, metadata, object_data, errors, warnings)

    return errors, warnings


def print_issues(title: str, issues: list[Issue]) -> None:
    """打印校验问题列表，包含字段名、错误信息和修复建议。"""
    if not issues:
        return
    print(title)
    for issue in issues:
        line = f"- [{issue.field}] {issue.message}"
        if issue.suggestion:
            line += f" 建议：{issue.suggestion}"
        print(line)


def issues_to_json(issues: list[Issue]) -> list[dict[str, str]]:
    """将校验问题转换为可机读 JSON。"""
    result: list[dict[str, str]] = []
    for issue in issues:
        item = {"field": issue.field, "message": issue.message}
        if issue.suggestion:
            item["suggestion"] = issue.suggestion
        result.append(item)
    return result


def print_success_payload(
    object_data: dict[str, Any],
    warnings: list[Issue],
) -> None:
    """成功时只输出可机读 JSON，供调用方替换当前快照。"""
    payload: dict[str, Any] = {
        "validation_passed": True,
        "object_data": object_data,
        "warnings": issues_to_json(warnings),
    }
    print(json.dumps(payload, ensure_ascii=False))


def parse_args(argv: list[str]) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="在提交编辑数据前校验 CRM object_data。")
    parser.add_argument(
        "--object-api-name",
        "--object_api_name",
        dest="object_api_name",
        required=True,
        help="对象 apiName。",
    )
    parser.add_argument(
        "--data-id",
        "--data_id",
        dest="data_id",
        required=True,
        help="记录 ID。",
    )
    parser.add_argument(
        "--object-data",
        "--object_data",
        dest="object_data",
        required=True,
        help="object_data JSON。以 @ 开头可从文件读取 JSON。",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    """入口函数。加载参数、执行校验、输出结果。返回 0 表示校验通过，1 表示有错误。"""
    args = parse_args(argv)
    form_fields, field_metadata = load_edit_layout(args.object_api_name, args.data_id)
    object_data = load_json_argument(args.object_data, "object_data")

    errors, warnings = validate_object_data(args.object_api_name, form_fields, field_metadata, object_data)
    if errors:
        print_issues("警告：", warnings)
        print_issues("校验失败：", errors)
        return 1

    print_success_payload(object_data, warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
