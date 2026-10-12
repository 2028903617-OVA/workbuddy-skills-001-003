#!/usr/bin/env python3
"""
build-html-report.py

将 sfa-decision-chain-diagnosis 的 Markdown 诊断正文渲染为 HTML 报告。

样式契约：
- 唯一样式来源是 ``assets/output.html`` 中的 <style> 块（运行时读取）。
- 脚本 **不得** 复用样式文件里的示例数据；所有可见数据必须来自输入 Markdown。

输入：Markdown（优先来自 ``--markdown <text>``；也兼容 ``--input <path>``；缺省从 stdin 读取）
输出：HTML（写入 ``--output <path>``，缺省 stdout）
失败：Markdown 结构校验失败、样式文件缺失或输入为空时以退出码 1 终止；不输出半成品 HTML。
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ASSETS_HTML = SKILL_DIR / "assets" / "output.html"

REQUIRED_SECTIONS = [
    "## 概要",
    "## 一、核心诊断结论",
    "## 二、决策链诊断结果",
    "## 三、根因分析",
    "## 四、关键风险与应对策略",
    "## 五、建议动作",
    "## 收口要求",
]

EXPECTED_BOTTOM_LINES = ["决策者覆盖", "Coach经营深度", "反对者识别"]
EXPECTED_ROLE_ROWS = ["Sponsor", "最高决策者", "业务方KP", "IT方KP", "采购方", "项目接口人"]
EXPECTED_ROOT_CAUSE_HEADINGS = [
    "### 决策者覆盖问题",
    "### Coach经营深度问题",
    "### 反对者识别问题",
]
EXPECTED_TRUE_DM_ROWS = [
    "当前识别的最高决策者是否可靠",
    "是否存在把流程角色误判为拍板角色的风险",
]
EXPECTED_POWER_ROWS = ["是否存在隐性权力中心", "识别线索", "应对思路"]
HEALTH_BANDS = [
    (25, 30, "优秀"),
    (18, 24, "及格"),
    (12, 17, "危险"),
    (0, 11, "极危"),
]
LEVEL_ENUM = {"高", "中", "低", "无法判断"}
COVERAGE_ENUM = {"已覆盖", "部分覆盖", "未覆盖", "无法判断"}
IMPACT_ENUM = {"高", "中", "低"}
YES_NO_UNKNOWN_ENUM = {"是", "否", "待补充", "无法判断"}


class ValidationError(Exception):
    """校验失败时抛出，调用方负责打印并退出 1。"""


def _esc(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _read_style() -> str:
    if not ASSETS_HTML.is_file():
        raise ValidationError(f"[校验失败] 缺少样式文件：{ASSETS_HTML}")
    text = ASSETS_HTML.read_text(encoding="utf-8")
    match = re.search(r"<style>([\s\S]*?)</style>", text)
    if not match:
        raise ValidationError("[校验失败] assets/output.html 中未找到 <style> 块")
    return match.group(1)


def _clean_inline(text: str) -> str:
    value = text.strip()
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    value = re.sub(r"`(.*?)`", r"\1", value)
    value = value.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    return value.strip()


def _split_rows(section: str) -> list[str]:
    return [line.rstrip() for line in section.splitlines()]


def _extract_section(text: str, heading: str, next_heading: str | None) -> str:
    pattern = rf"(?ms)^{re.escape(heading)}\s*\n(.*?)(?=^{re.escape(next_heading)}\s*$|\Z)" if next_heading else rf"(?ms)^{re.escape(heading)}\s*\n(.*)\Z"
    match = re.search(pattern, text)
    if not match:
        raise ValidationError(f"[校验失败] 缺少章节：{heading}")
    return match.group(1).strip()


def _split_table_row(line: str, expected_columns: int, path: str) -> list[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        raise ValidationError(f"[校验失败] {path} 不是合法 Markdown 表格行")
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if len(cells) != expected_columns:
        raise ValidationError(f"[校验失败] {path} 列数应为 {expected_columns}，实际为 {len(cells)}")
    return cells


def _extract_table(section: str, heading: str, expected_columns: int) -> list[list[str]]:
    lines = _split_rows(section)
    header_index = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) == expected_columns:
                header_index = idx
                break
    if header_index is None or header_index + 2 >= len(lines):
        raise ValidationError(f"[校验失败] {heading} 缺少完整表格")

    table_lines = [lines[header_index].strip()]
    for line in lines[header_index + 2 :]:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines.append(stripped)
        elif table_lines:
            break

    if len(table_lines) < 2:
        raise ValidationError(f"[校验失败] {heading} 缺少完整表格")

    rows = [_split_table_row(table_lines[0], expected_columns, f"{heading} 表头")]
    for idx, line in enumerate(table_lines[1:], start=1):
        rows.append(_split_table_row(line, expected_columns, f"{heading} 第 {idx} 行"))
    return rows


def _extract_subsection(section: str, heading: str, next_heading: str | None = None) -> str:
    pattern = rf"(?ms)^{re.escape(heading)}\s*\n(.*?)(?=^{re.escape(next_heading)}\s*$|\Z)" if next_heading else rf"(?ms)^{re.escape(heading)}\s*\n(.*)\Z"
    match = re.search(pattern, section)
    if not match:
        raise ValidationError(f"[校验失败] 缺少子章节：{heading}")
    return match.group(1).strip()


def _extract_bullet_value(section: str, label: str, *, required: bool = True) -> str:
    pattern = rf"(?m)^-\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?[:：]\s*(.+?)\s*$"
    match = re.search(pattern, section)
    if match:
        return _clean_inline(match.group(1))
    if required:
        raise ValidationError(f"[校验失败] 缺少字段：{label}")
    return ""


def _extract_bullet_values(section: str, label: str, *, required: bool = True) -> list[str]:
    pattern = rf"(?m)^-\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?[:：]\s*(.*?)\s*$"
    match = re.search(pattern, section)
    if not match:
        if required:
            raise ValidationError(f"[校验失败] 缺少字段：{label}")
        return []

    inline_value = _clean_inline(match.group(1))
    following = section[match.end() :]
    items: list[str] = []

    if inline_value:
        normalized = re.sub(r"\s*[|｜]\s*", "\n", inline_value)
        normalized = re.sub(r"(?<!^)\s*(?=(?:[①②③④⑤⑥⑦⑧⑨⑩]|\d+[.．、)]))", "\n", normalized)
        parts = [part.strip() for part in re.split(r"[；;\n]+", normalized) if part.strip()]
        if len(parts) > 1:
            items.extend(parts)
        else:
            items.append(inline_value)

    for line in following.splitlines():
        if not line.strip():
            continue
        if re.match(r"^(?:-\s*\S|\|\s*\S|##\s*\S|###\s*\S)", line):
            break
        bullet_match = re.match(r"^\s+-\s*(.+?)\s*$", line)
        numbered_match = re.match(r"^\s*(?:\d+[.．、)]|[①②③④⑤⑥⑦⑧⑨⑩])\s*(.+?)\s*$", line)
        if bullet_match:
            items.append(_clean_inline(bullet_match.group(1)))
            continue
        if numbered_match:
            items.append(_clean_inline(numbered_match.group(1)))
            continue
        if items and re.match(r"^\s{2,}\S", line):
            items[-1] = f"{items[-1]} {_clean_inline(line)}".strip()
            continue
        break

    if required and not items:
        raise ValidationError(f"[校验失败] 字段为空：{label}")
    return items


def _collect_section_bullets(section: str) -> list[str]:
    items = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        items.append(_clean_inline(line[2:]))
    return items


def _require_enum(value: str, allowed: set[str], path: str) -> None:
    if value not in allowed:
        raise ValidationError(f"[校验失败] {path} 必须为 {' / '.join(sorted(allowed))}")


def _parse_score_30(value: str) -> int:
    match = re.match(r"^(\d{1,2})\s*(?:/\s*30)?$", value)
    if not match:
        raise ValidationError("[校验失败] 综合评分必须为 0-30 或 x/30 格式")
    score = int(match.group(1))
    if not 0 <= score <= 30:
        raise ValidationError("[校验失败] 综合评分必须在 0-30 之间")
    return score


def _parse_score_10(value: str, path: str) -> int:
    match = re.match(r"^(\d{1,2})\s*(?:/\s*10)?$", value)
    if not match:
        raise ValidationError(f"[校验失败] {path} 必须为 0-10 或 x/10 格式")
    score = int(match.group(1))
    if not 0 <= score <= 10:
        raise ValidationError(f"[校验失败] {path} 必须在 0-10 之间")
    return score


def _derive_health(score: int) -> str:
    for low, high, label in HEALTH_BANDS:
        if low <= score <= high:
            return label
    raise ValidationError("[校验失败] 综合评分超出健康等级区间")


def _parse_meta(section: str) -> dict[str, Any]:
    opportunity_name = _extract_bullet_value(section, "商机名称")
    diagnosis_date = _extract_bullet_value(section, "诊断日期")
    total_score_raw = _extract_bullet_value(section, "综合评分")
    health_level = _extract_bullet_value(section, "健康等级")
    judgement_basis = _extract_bullet_value(section, "判定依据")

    total_score = _parse_score_30(total_score_raw)
    _require_enum(health_level, {"优秀", "及格", "危险", "极危"}, "健康等级")
    expected_health = _derive_health(total_score)
    if health_level != expected_health:
        raise ValidationError(f"[校验失败] 健康等级与综合评分不匹配：{total_score} 分应为 {expected_health}")

    return {
        "opportunity_name": opportunity_name,
        "diagnosis_date": diagnosis_date,
        "total_score": total_score,
        "total_score_display": f"{total_score}/30",
        "health_level": health_level,
        "judgement_basis": judgement_basis,
    }


def _parse_core_conclusion(section: str) -> dict[str, Any]:
    one_liner = _extract_bullet_value(section, "一句话结论")
    three_elements = _extract_bullet_values(section, "决策链三要素")
    key_actions = _extract_bullet_values(section, "关键行动项")
    if len(three_elements) != 3:
        raise ValidationError("[校验失败] 决策链三要素必须恰好为 3 项")
    if len(key_actions) != 3:
        raise ValidationError("[校验失败] 关键行动项必须恰好为 3 项")
    return {
        "one_liner": one_liner,
        "three_elements": three_elements,
        "key_actions": key_actions,
    }


def _parse_bottom_scores(section: str, total_score: int) -> list[dict[str, Any]]:
    rows = _extract_table(section, "三底线量化评分", 3)
    data_rows = rows[1:]
    if len(data_rows) != 3:
        raise ValidationError("[校验失败] 三底线量化评分必须为 3 行")
    parsed = []
    total = 0
    for idx, row in enumerate(data_rows):
        line_name, score_raw, reason = row
        expected = EXPECTED_BOTTOM_LINES[idx]
        if line_name != expected:
            raise ValidationError(f"[校验失败] 三底线量化评分第 {idx + 1} 行必须为 {expected}")
        score = _parse_score_10(score_raw, f"三底线量化评分第 {idx + 1} 行得分")
        total += score
        parsed.append(
            {
                "line": line_name,
                "score": score,
                "score_display": f"{score}/10",
                "reason": _clean_inline(reason),
            }
        )
    if total != total_score:
        raise ValidationError(f"[校验失败] 三底线量化评分总和 {total} 与综合评分 {total_score} 不一致")
    return parsed


def _parse_coverage_map(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "决策链覆盖地图", 6)
    data_rows = rows[1:]
    if len(data_rows) != 6:
        raise ValidationError("[校验失败] 决策链覆盖地图必须为 6 行")
    parsed = []
    for idx, row in enumerate(data_rows):
        role, name, title, support, influence, coverage = [_clean_inline(cell) for cell in row]
        expected_role = EXPECTED_ROLE_ROWS[idx]
        if role != expected_role:
            raise ValidationError(f"[校验失败] 决策链覆盖地图第 {idx + 1} 行角色必须为 {expected_role}")
        _require_enum(support, LEVEL_ENUM, f"决策链覆盖地图第 {idx + 1} 行支持度")
        _require_enum(influence, LEVEL_ENUM, f"决策链覆盖地图第 {idx + 1} 行影响度")
        _require_enum(coverage, COVERAGE_ENUM, f"决策链覆盖地图第 {idx + 1} 行覆盖状态")
        if not name:
            raise ValidationError(f"[校验失败] 决策链覆盖地图第 {idx + 1} 行姓名不能为空，请使用 待补充 或 无法判断")
        if not title:
            raise ValidationError(f"[校验失败] 决策链覆盖地图第 {idx + 1} 行职位不能为空，请使用 待补充 或 无法判断")
        parsed.append(
            {
                "role": role,
                "name": name,
                "title": title,
                "support": support,
                "influence": influence,
                "coverage": coverage,
            }
        )
    return parsed


def _parse_aux_checks(section: str) -> dict[str, Any]:
    true_dm = _extract_subsection(section, "### 真假决策者校验", "### 隐性权力中心观察")
    power_center = _extract_subsection(section, "### 隐性权力中心观察")

    true_dm_rows = _extract_table(true_dm, "真假决策者校验", 3)[1:]
    if len(true_dm_rows) != 2:
        raise ValidationError("[校验失败] 真假决策者校验必须为 2 行")
    parsed_true_dm = []
    for idx, row in enumerate(true_dm_rows):
        item, conclusion, explanation = [_clean_inline(cell) for cell in row]
        expected_item = EXPECTED_TRUE_DM_ROWS[idx]
        if item != expected_item:
            raise ValidationError(f"[校验失败] 真假决策者校验第 {idx + 1} 行项目必须为 {expected_item}")
        if idx == 0:
            _require_enum(conclusion, YES_NO_UNKNOWN_ENUM, f"真假决策者校验第 {idx + 1} 行结论")
        else:
            _require_enum(conclusion, LEVEL_ENUM, f"真假决策者校验第 {idx + 1} 行结论")
        parsed_true_dm.append({"item": item, "conclusion": conclusion, "explanation": explanation})

    power_rows = _extract_table(power_center, "隐性权力中心观察", 3)[1:]
    if len(power_rows) != 3:
        raise ValidationError("[校验失败] 隐性权力中心观察必须为 3 行")
    parsed_power_rows = []
    for idx, row in enumerate(power_rows):
        item, conclusion, explanation = [_clean_inline(cell) for cell in row]
        expected_item = EXPECTED_POWER_ROWS[idx]
        if item != expected_item:
            raise ValidationError(f"[校验失败] 隐性权力中心观察第 {idx + 1} 行项目必须为 {expected_item}")
        if idx == 0:
            _require_enum(conclusion, YES_NO_UNKNOWN_ENUM, f"隐性权力中心观察第 {idx + 1} 行结论")
        elif not conclusion:
            raise ValidationError(f"[校验失败] 隐性权力中心观察第 {idx + 1} 行结论不能为空")
        parsed_power_rows.append({"item": item, "conclusion": conclusion, "explanation": explanation})

    return {"true_dm": parsed_true_dm, "power_center": parsed_power_rows}


def _parse_root_causes(section: str) -> list[dict[str, Any]]:
    parsed = []
    for idx, heading in enumerate(EXPECTED_ROOT_CAUSE_HEADINGS):
        next_heading = EXPECTED_ROOT_CAUSE_HEADINGS[idx + 1] if idx + 1 < len(EXPECTED_ROOT_CAUSE_HEADINGS) else None
        sub = _extract_subsection(section, heading, next_heading)
        rows = _extract_table(sub, heading, 3)
        data_rows = rows[1:]
        if not data_rows:
            raise ValidationError(f"[校验失败] {heading} 至少需要 1 行数据")
        items = []
        for row_idx, row in enumerate(data_rows, start=1):
            problem, cause, solution = [_clean_inline(cell) for cell in row]
            if not any([problem, cause, solution]):
                raise ValidationError(f"[校验失败] {heading} 第 {row_idx} 行不能为空")
            items.append({"problem": problem, "cause": cause, "solution": solution})
        parsed.append({"heading": heading.replace("### ", ""), "rows": items})
    return parsed


def _parse_risks(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "关键风险与应对策略", 4)
    data_rows = rows[1:]
    if not data_rows:
        raise ValidationError("[校验失败] 关键风险与应对策略不能为空")
    parsed = []
    for idx, row in enumerate(data_rows, start=1):
        risk, impact, strategy, talk_track = [_clean_inline(cell) for cell in row]
        if not risk:
            raise ValidationError(f"[校验失败] 关键风险与应对策略第 {idx} 行风险不能为空")
        _require_enum(impact, IMPACT_ENUM, f"关键风险与应对策略第 {idx} 行影响程度")
        parsed.append(
            {
                "risk": risk,
                "impact": impact,
                "strategy": strategy,
                "talk_track": talk_track,
            }
        )
    return parsed


def _parse_actions_table(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "建议动作", 6)
    data_rows = rows[1:]
    if len(data_rows) != 3:
        raise ValidationError("[校验失败] 建议动作必须为 3 行")
    expected_priority = ["P0", "P1", "P2"]
    parsed = []
    for idx, row in enumerate(data_rows):
        priority, action, purpose, time, owner, done_when = [_clean_inline(cell) for cell in row]
        if priority != expected_priority[idx]:
            raise ValidationError(f"[校验失败] 建议动作第 {idx + 1} 行优先级必须为 {expected_priority[idx]}")
        parsed.append(
            {
                "priority": priority,
                "action": action,
                "purpose": purpose,
                "time": time,
                "owner": owner,
                "done_when": done_when,
            }
        )
    return parsed


def _parse_closure_requirements(section: str) -> list[str]:
    items = _collect_section_bullets(section)
    if not items:
        raise ValidationError("[校验失败] 收口要求不能为空")
    return items


def _parse_markdown(text: str) -> dict[str, Any]:
    normalized = _normalize(text).strip()
    if not normalized:
        raise ValidationError("[校验失败] 输入为空")

    sections = {}
    for index, heading in enumerate(REQUIRED_SECTIONS):
        next_heading = REQUIRED_SECTIONS[index + 1] if index + 1 < len(REQUIRED_SECTIONS) else None
        sections[heading] = _extract_section(normalized, heading, next_heading)

    meta = _parse_meta(sections["## 概要"])
    return {
        "meta": meta,
        "core_conclusion": _parse_core_conclusion(sections["## 一、核心诊断结论"]),
        "bottom_scores": _parse_bottom_scores(sections["## 二、决策链诊断结果"], meta["total_score"]),
        "coverage_map": _parse_coverage_map(sections["## 二、决策链诊断结果"]),
        "aux_checks": _parse_aux_checks(sections["## 二、决策链诊断结果"]),
        "root_causes": _parse_root_causes(sections["## 三、根因分析"]),
        "risks": _parse_risks(sections["## 四、关键风险与应对策略"]),
        "actions": _parse_actions_table(sections["## 五、建议动作"]),
        "closure_requirements": _parse_closure_requirements(sections["## 收口要求"]),
    }


def _impact_tag_class(value: str) -> str:
    return {"高": "tag-p0", "中": "tag-p1", "低": "tag-p2"}.get(value, "tag-p2")


def _status_tag_class(value: str) -> str:
    if value in {"是", "已覆盖", "高"}:
        return "tag-confirmed"
    if value in {"部分覆盖", "中", "待补充"}:
        return "tag-inferred"
    return "tag-unknown"


def _render_list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{_esc(item)}</li>" for item in items) + "</ul>"


def _bottom_score_rows(rows: list[dict[str, Any]]) -> str:
    out = []
    for row in rows:
        out.append(
            "<tr>"
            f"<td>{_esc(row['line'])}</td>"
            f"<td style=\"text-align:center;font-weight:700\">{_esc(row['score_display'])}</td>"
            f"<td>{_esc(row['reason'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _coverage_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        out.append(
            "<tr>"
            f"<td>{_esc(row['role'])}</td>"
            f"<td>{_esc(row['name'])}</td>"
            f"<td>{_esc(row['title'])}</td>"
            f"<td><span class=\"tag {_status_tag_class(row['support'])}\">{_esc(row['support'])}</span></td>"
            f"<td><span class=\"tag {_status_tag_class(row['influence'])}\">{_esc(row['influence'])}</span></td>"
            f"<td><span class=\"tag {_status_tag_class(row['coverage'])}\">{_esc(row['coverage'])}</span></td>"
            "</tr>"
        )
    return "\n".join(out)


def _root_cause_blocks(items: list[dict[str, Any]]) -> str:
    blocks = []
    for item in items:
        rows = []
        for row in item["rows"]:
            rows.append(
                "<tr>"
                f"<td>{_esc(row['problem'])}</td>"
                f"<td>{_esc(row['cause'])}</td>"
                f"<td>{_esc(row['solution'])}</td>"
                "</tr>"
            )
        blocks.append(
            "<div class=\"section\" style=\"margin-bottom:20px\">"
            f"<div class=\"key-insight\">{_esc(item['heading'])}</div>"
            "<div class=\"table-wrap\">"
            "<table>"
            "<thead><tr><th>问题</th><th>根因</th><th>解决方法</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
            "</div>"
            "</div>"
        )
    return "\n".join(blocks)


def _simple_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        out.append(
            "<tr>"
            f"<td>{_esc(row['item'])}</td>"
            f"<td>{_esc(row['conclusion'])}</td>"
            f"<td>{_esc(row['explanation'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _risk_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        out.append(
            "<tr>"
            f"<td>{_esc(row['risk'])}</td>"
            f"<td><span class=\"tag {_impact_tag_class(row['impact'])}\">{_esc(row['impact'])}</span></td>"
            f"<td>{_esc(row['strategy'])}</td>"
            f"<td>{_esc(row['talk_track'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _action_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        tag_class = {"P0": "tag-p0", "P1": "tag-p1", "P2": "tag-p2"}.get(row["priority"], "tag-p2")
        out.append(
            "<tr>"
            f"<td><span class=\"tag {tag_class}\">{_esc(row['priority'])}</span></td>"
            f"<td>{_esc(row['action'])}</td>"
            f"<td>{_esc(row['purpose'])}</td>"
            f"<td>{_esc(row['time'])}</td>"
            f"<td>{_esc(row['owner'])}</td>"
            f"<td>{_esc(row['done_when'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _grade_text_class(value: str) -> str:
    return {
        "极危": "is-danger",
        "危险": "is-danger",
        "及格": "is-warn",
        "优秀": "is-good",
    }.get(value, "is-default")


def _render(data: dict[str, Any], style_css: str) -> str:
    meta = data["meta"]
    cc = data["core_conclusion"]
    aux = data["aux_checks"]
    grade_pill_html = (
        f'<div class="win-rate-grade-wrap">'
        f'<span class="win-rate-grade-label">评级</span>'
        f'<div class="win-rate-grade-text {_grade_text_class(meta["health_level"])}">{_esc(meta["health_level"])}</div>'
        f'<button class="grade-help" type="button" aria-label="查看评级依据" aria-expanded="false">i'
        f'<div class="grade-help-tip"><strong>评级依据：</strong>综合评分 {_esc(meta["total_score_display"])}，依据评分区间规则，{_esc(meta["health_level"])} 对应当前判定。</div>'
        f'</button>'
        f'</div>'
    )
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>{_esc(meta['opportunity_name'])} - 决策链诊断报告</title>
<style>
{style_css}
</style>
</head>
<body>
<div class=\"cover\">
  <div class=\"cover-inner\">
    <div class=\"cover-head\">
      <div class=\"cover-title-block\">
        <div class=\"eyebrow\">Decision Chain Diagnosis Report</div>
        <h1>{_esc(meta['opportunity_name'])} · 决策链诊断</h1>
        <div class=\"head-tags\">
          <div class=\"head-tag-group\">
            <span class=\"head-tag-title\">积极信号</span>
            <span class=\"head-tag head-tag-good\">Sponsor 已识别</span>
            <span class=\"head-tag head-tag-good\">业务方KP 已覆盖</span>
          </div>
          <div class=\"head-tag-group\">
            <span class=\"head-tag-title\">风险信号</span>
            <span class=\"head-tag head-tag-bad\">最高决策者未触达</span>
            <span class=\"head-tag head-tag-bad\">采购方未覆盖</span>
            <span class=\"head-tag head-tag-bad\">Coach 深度不足</span>
          </div>
        </div>
        <dl class=\"cover-meta\">
          <div><dt>诊断日期</dt><dd>{_esc(meta['diagnosis_date'])}</dd></div>
        </dl>
      </div>
      <div class=\"win-rate-box\">
        <div class=\"win-rate-score-card\">
          <div class=\"win-rate-num\">{_esc(meta['total_score'])}<span class=\"win-rate-denominator\">/30</span></div>
          <div class=\"win-rate-label\">综合评分</div>
        </div>
        {grade_pill_html}
      </div>
    </div>
  </div>
</div>
<div class=\"layout\">
  <aside class=\"toc\">
    <div class=\"toc-title\">目录</div>
    <a href=\"#section-overview\" class=\"active\">一、核心诊断结论</a>
    <a href=\"#section-score\">二、决策链诊断结果</a>
    <a href=\"#section-root-cause\">三、根因分析</a>
    <a href=\"#section-risk\">四、关键风险与应对策略</a>
    <a href=\"#section-actions\">五、建议动作</a>
  </aside>
  <div class=\"container\">
    <div class=\"content\">

<div class=\"section\" id=\"section-overview\">
  <div class=\"section-title\"><span class=\"num\">一</span>核心诊断结论</div>
  <div class=\"conclusion-box\">
    <p><strong>一句话结论：</strong>{_esc(cc['one_liner'])}</p>
    <div class=\"key-insight\">决策链三要素：</div>
    {_render_list(cc['three_elements'])}
    <div class=\"key-insight\">关键行动项：</div>
    {_render_list(cc['key_actions'])}
  </div>
</div>

<div class=\"section\" id=\"section-score\">
  <div class=\"section-title\"><span class=\"num\">二</span>决策链诊断结果</div>
  <div class=\"key-insight\">三底线量化评分</div>
  <div class=\"table-wrap\">
    <table>
      <thead><tr><th>底线</th><th style=\"text-align:center\">得分</th><th>说明</th></tr></thead>
      <tbody>
        {_bottom_score_rows(data['bottom_scores'])}
      </tbody>
    </table>
  </div>
  <div class=\"alert-box alert-blue\"><strong>判定依据：</strong>{_esc(meta['judgement_basis'])}</div>
  <div class=\"key-insight\">决策链覆盖地图</div>
  <div class=\"table-wrap\">
    <table>
      <thead><tr><th>角色</th><th>姓名</th><th>职位</th><th>支持度</th><th>影响度</th><th>覆盖状态</th></tr></thead>
      <tbody>
        {_coverage_rows(data['coverage_map'])}
      </tbody>
    </table>
  </div>
  <div class=\"key-insight\">真假决策者校验</div>
  <div class=\"table-wrap\">
    <table>
      <thead><tr><th>项目</th><th>结论</th><th>说明</th></tr></thead>
      <tbody>
        {_simple_rows(aux['true_dm'])}
      </tbody>
    </table>
  </div>
  <div class=\"key-insight\">隐性权力中心观察</div>
  <div class=\"table-wrap\">
    <table>
      <thead><tr><th>项目</th><th>结论</th><th>说明</th></tr></thead>
      <tbody>
        {_simple_rows(aux['power_center'])}
      </tbody>
    </table>
  </div>
</div>

<div class=\"section\" id=\"section-root-cause\">
  <div class=\"section-title\"><span class=\"num\">三</span>根因分析</div>
  {_root_cause_blocks(data['root_causes'])}
</div>

<div class=\"section\" id=\"section-risk\">
  <div class=\"section-title\"><span class=\"num\">四</span>关键风险与应对策略</div>
  <div class=\"table-wrap\">
    <table>
      <thead><tr><th>风险</th><th>影响程度</th><th>应对策略</th><th>话术要点</th></tr></thead>
      <tbody>
        {_risk_rows(data['risks'])}
      </tbody>
    </table>
  </div>
</div>

<div class=\"section\" id=\"section-actions\">
  <div class=\"section-title\"><span class=\"num\">五</span>建议动作</div>
  <div class=\"alert-box alert-blue\"><strong>说明：</strong>建议动作用于补全决策链并建立 Coach 经营深度；“目的”列需对应三底线量化评分中待解决的具体问题。</div>
  <div class=\"table-wrap\">
    <table>
      <thead><tr><th>优先级</th><th>动作</th><th>目的</th><th>时间</th><th>负责人/对象</th><th>完成标志</th></tr></thead>
      <tbody>
        {_action_rows(data['actions'])}
      </tbody>
    </table>
  </div>
</div>

<div class=\"footer-note\">📎 本报告遵循 SFA 决策链诊断标准（sfa-decision-chain-diagnosis）。正文中的“待补充 / 无法判断 / ⚠️ 推断”仅用于诊断梳理，需后续验证。</div>

    </div>
  </div>
</div>
</body>
</html>
"""


SCHEMA_TEXT = """# sfa-decision-chain-diagnosis HTML renderer schema

必须包含以下 Markdown 章节：
- ## 概要
- ## 一、核心诊断结论
- ## 二、决策链诊断结果
- ## 三、根因分析
- ## 四、关键风险与应对策略
- ## 五、建议动作
- ## 收口要求

关键校验：
- 综合评分必须为 0-30（或 x/30），且健康等级必须与分数区间匹配：25-30=优秀，18-24=及格，12-17=危险，0-11=极危。
- 三底线量化评分必须严格包含：决策者覆盖 / Coach经营深度 / 反对者识别，且三项得分合计等于综合评分。
- 决策链覆盖地图必须严格包含：Sponsor / 最高决策者 / 业务方KP / IT方KP / 采购方 / 项目接口人。
- 支持度/影响度：高 / 中 / 低 / 无法判断。
- 覆盖状态：已覆盖 / 部分覆盖 / 未覆盖 / 无法判断。
- 建议动作必须为 3 行表格，优先级依次为 P0 / P1 / P2。
"""


def _read_input(markdown_text: str | None, input_path: str | None) -> str:
    if markdown_text:
        return markdown_text
    if input_path:
        return Path(input_path).read_text(encoding="utf-8")
    return sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render decision-chain diagnosis markdown to HTML")
    parser.add_argument("--markdown", help="直接传入 Markdown 正文")
    parser.add_argument("--input", help="从文件读取 Markdown")
    parser.add_argument("--output", help="输出 HTML 文件路径；缺省写 stdout")
    parser.add_argument("--schema", action="store_true", help="打印 Markdown 结构提示并退出")
    args = parser.parse_args()

    if args.schema:
        print(SCHEMA_TEXT)
        return 0

    try:
        markdown = _read_input(args.markdown, args.input)
        style = _read_style()
        data = _parse_markdown(markdown)
        rendered = _render(data, style)
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        return 0
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
