#!/usr/bin/env python3
"""
build-html-report.py

将 sfa-opportunity-competitive-analysis 的 Markdown 竞争分析正文渲染为 HTML 报告。

样式契约：
- 唯一样式来源是 ``assets/output.html`` 中的 <style> 块（运行时读取）。
- 脚本不得复用样式文件里的示例数据；所有可见数据必须来自输入 Markdown。

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
    "## 输入摘要",
    "## 一、核心竞争结论",
    "## 二、三件套收集状态",
    "## 三、五维竞品分析",
    "## 四、竞争对手画像",
    "## 五、竞对企业风险观察",
    "## 六、差异化定位",
    "## 七、攻防策略",
    "## 八、赢单路径",
    "## 九、情报缺口与补充计划",
    "## 收口要求",
]

EXPECTED_INTEL_ROWS = ["竞品产品功能对比", "竞品报价策略", "竞品客户关系"]
EXPECTED_DIMENSIONS = ["品牌力", "产品平台", "行业 Know-how", "本地交付", "商务成本"]
EXPECTED_PROFILE_ROWS = ["公司名称", "核心优势", "核心劣势", "报价情况", "关系覆盖", "客户倾向", "近期动作"]
EXPECTED_RISK_ROWS = ["风险等级", "主要风险类型", "是否影响供应商稳定性", "建议验证动作", "对本商机的影响"]
EXPECTED_STRATEGY_ROWS = ["产品攻防", "价格攻防", "关系攻防", "案例攻防", "风险攻防"]
EXPECTED_PRIORITIES = ["P0", "P1", "P2"]

COLLECTION_STATUS_ENUM = {"未收集", "收集中", "已完成", "无法判断"}
STANCE_ENUM = {"领先", "相持", "落后", "无法判断"}
EVIDENCE_ENUM = {"充分", "部分充分", "不足", "无法判断"}
RISK_LEVEL_ENUM = {"高", "中", "低", "无法判断"}
YES_NO_UNKNOWN_ENUM = {"是", "否", "待补充", "无法判断"}
YES_NO_UNKNOWN_NA_ENUM = {"是", "否", "不适用", "待补充", "无法判断"}
RISK_LEVEL_NA_ENUM = {"高", "中", "低", "不适用", "无法判断"}
IMPORTANCE_ENUM = {"高", "中", "低"}
PRIORITY_ENUM = {"P0", "P1", "P2"}


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
    pattern = (
        rf"(?ms)^{re.escape(heading)}\s*\n(.*?)(?=^{re.escape(next_heading)}\s*$|\Z)"
        if next_heading
        else rf"(?ms)^{re.escape(heading)}\s*\n(.*)\Z"
    )
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


def _extract_table_with_options(section: str, heading: str, expected_columns_options: list[int]) -> tuple[list[list[str]], int]:
    last_error: ValidationError | None = None
    for expected_columns in expected_columns_options:
        try:
            return _extract_table(section, heading, expected_columns), expected_columns
        except ValidationError as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise ValidationError(f"[校验失败] {heading} 缺少完整表格")


def _extract_bullet_value(section: str, label: str, *, required: bool = True) -> str:
    pattern = rf"(?m)^-\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?[:：][^\S\r\n]*(.+?)[^\S\r\n]*$"
    match = re.search(pattern, section)
    if match:
        return _clean_inline(match.group(1))
    if required:
        raise ValidationError(f"[校验失败] 缺少字段：{label}")
    return ""


def _extract_bullet_values(section: str, label: str, *, required: bool = True) -> list[str]:
    pattern = rf"(?m)^-\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?[:：][^\S\r\n]*(.*?)[^\S\r\n]*$"
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
        if line.startswith("- "):
            items.append(_clean_inline(line[2:]))
    return items


def _require_enum(value: str, allowed: set[str], path: str) -> None:
    if value not in allowed:
        raise ValidationError(f"[校验失败] {path} 必须为 {' / '.join(sorted(allowed))}")


def _parse_score_10(value: str, path: str) -> int | None:
    raw = _clean_inline(value)
    if raw in {"无法判断", "不适用"}:
        return None
    match = re.match(r"^(\d{1,2})\s*(?:/\s*10)?$", raw)
    if not match:
        raise ValidationError(f"[校验失败] {path} 必须为 0-10、x/10 或 无法判断")
    score = int(match.group(1))
    if not 0 <= score <= 10:
        raise ValidationError(f"[校验失败] {path} 必须在 0-10 之间")
    return score


def _parse_score_100(value: str, path: str) -> int | None:
    raw = _clean_inline(value)
    if raw in {"无法判断", "不适用"}:
        return None
    match = re.match(r"^(\d{1,3})\s*(?:/\s*100)?$", raw)
    if not match:
        raise ValidationError(f"[校验失败] {path} 必须为 0-100、x/100 或 无法判断")
    score = int(match.group(1))
    if not 0 <= score <= 100:
        raise ValidationError(f"[校验失败] {path} 必须在 0-100 之间")
    return score


def _score_display(value: int | None, denominator: int) -> str:
    return "无法判断" if value is None else f"{value}/{denominator}"


def _split_competitor_names(raw: str) -> list[str]:
    normalized = _clean_inline(raw)
    if not normalized:
        return []
    parts = [part.strip() for part in re.split(r"\s*(?:/|／|、|，|,|\|)\s*", normalized) if part.strip()]
    return parts[:2]


def _parse_meta(section: str) -> dict[str, Any]:
    competitors = _extract_bullet_value(section, "主要竞品")
    meta = {
        "opportunity_name": _extract_bullet_value(section, "商机名称"),
        "stage": _extract_bullet_value(section, "项目阶段"),
        "competitors": competitors,
        "analysis_scope": _extract_bullet_value(section, "主分析范围"),
        "diagnosis_date": _extract_bullet_value(section, "诊断日期"),
    }
    for key, value in meta.items():
        if not value:
            raise ValidationError(f"[校验失败] 输入摘要字段为空：{key}")
    competitor_names = _split_competitor_names(competitors)
    if not competitor_names:
        raise ValidationError("[校验失败] 主要竞品至少需要 1 个具体竞品名称")
    if len(competitor_names) > 2:
        raise ValidationError("[校验失败] 主要竞品最多支持 2 个重点竞品")
    meta["competitor_names"] = competitor_names
    meta["has_competitor_b"] = len(competitor_names) > 1
    return meta


def _parse_core_conclusion(section: str) -> dict[str, Any]:
    stance = _extract_bullet_value(section, "竞争态势")
    _require_enum(stance, STANCE_ENUM, "竞争态势")
    key_actions = _extract_bullet_values(section, "关键行动项")
    if len(key_actions) < 1:
        raise ValidationError("[校验失败] 关键行动项至少需要 1 项")
    return {
        "one_liner": _extract_bullet_value(section, "一句话结论"),
        "stance": stance,
        "strength": _extract_bullet_value(section, "核心优势"),
        "weakness": _extract_bullet_value(section, "核心短板"),
        "risk": _extract_bullet_value(section, "关键风险"),
        "key_actions": key_actions,
    }


def _parse_intel_status(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "三件套收集状态", 5)[1:]
    if len(rows) != 3:
        raise ValidationError("[校验失败] 三件套收集状态必须为 3 行")
    parsed = []
    for idx, row in enumerate(rows):
        item, status, facts, gap, impact = [_clean_inline(cell) for cell in row]
        expected = EXPECTED_INTEL_ROWS[idx]
        if item != expected:
            raise ValidationError(f"[校验失败] 三件套收集状态第 {idx + 1} 行必须为 {expected}")
        _require_enum(status, COLLECTION_STATUS_ENUM, f"三件套收集状态第 {idx + 1} 行状态")
        parsed.append({"item": item, "status": status, "facts": facts, "gap": gap, "impact": impact})
    return parsed


def _parse_competitive_scores(section: str, has_competitor_b: bool) -> dict[str, Any]:
    expected_columns = 7 if has_competitor_b else 6
    rows = _extract_table(section, "五维竞品分析", expected_columns)[1:]
    if len(rows) != 5:
        raise ValidationError("[校验失败] 五维竞品分析必须为 5 行")
    parsed_rows = []
    for idx, row in enumerate(rows):
        cleaned = [_clean_inline(cell) for cell in row]
        if has_competitor_b:
            dimension, weight_raw, our_raw, competitor_a_raw, competitor_b_raw, gap, evidence = cleaned
        else:
            dimension, weight_raw, our_raw, competitor_a_raw, gap, evidence = cleaned
            competitor_b_raw = "不适用"
        expected = EXPECTED_DIMENSIONS[idx]
        if dimension != expected:
            raise ValidationError(f"[校验失败] 五维竞品分析第 {idx + 1} 行必须为 {expected}")
        try:
            weight = int(weight_raw)
        except ValueError as exc:
            raise ValidationError(f"[校验失败] 五维竞品分析第 {idx + 1} 行权重必须为 1-5") from exc
        if not 1 <= weight <= 5:
            raise ValidationError(f"[校验失败] 五维竞品分析第 {idx + 1} 行权重必须为 1-5")
        _require_enum(gap, STANCE_ENUM, f"五维竞品分析第 {idx + 1} 行差距")
        our_score = _parse_score_10(our_raw, f"五维竞品分析第 {idx + 1} 行我方得分")
        competitor_a_score = _parse_score_10(competitor_a_raw, f"五维竞品分析第 {idx + 1} 行竞品A得分")
        competitor_b_score = _parse_score_10(competitor_b_raw, f"五维竞品分析第 {idx + 1} 行竞品B得分")
        parsed_rows.append(
            {
                "dimension": dimension,
                "weight": weight,
                "our_score": our_score,
                "our_display": _score_display(our_score, 10),
                "competitor_a_score": competitor_a_score,
                "competitor_a_display": _score_display(competitor_a_score, 10),
                "competitor_b_score": competitor_b_score,
                "competitor_b_display": "不适用" if competitor_b_raw == "不适用" else _score_display(competitor_b_score, 10),
                "gap": gap,
                "evidence": evidence,
            }
        )

    our_total = _parse_score_100(_extract_bullet_value(section, "我方加权得分"), "我方加权得分")
    competitor_a_total_raw = _extract_bullet_value(section, "竞品A加权得分")
    competitor_a_total = _parse_score_100(competitor_a_total_raw, "竞品A加权得分")
    competitor_b_total_raw = _extract_bullet_value(section, "竞品B加权得分", required=has_competitor_b) if has_competitor_b else "不适用"
    competitor_b_total = _parse_score_100(competitor_b_total_raw, "竞品B加权得分")
    stance = _extract_bullet_value(section, "竞争态势")
    _require_enum(stance, STANCE_ENUM, "五维竞品分析竞争态势")
    confidence = _extract_bullet_value(section, "可信度说明")
    return {
        "rows": parsed_rows,
        "our_total": our_total,
        "our_total_display": _score_display(our_total, 100),
        "competitor_a_total": competitor_a_total,
        "competitor_a_total_display": _score_display(competitor_a_total, 100),
        "competitor_b_total": competitor_b_total,
        "competitor_b_total_display": "不适用" if competitor_b_total_raw == "不适用" else _score_display(competitor_b_total, 100),
        "stance": stance,
        "confidence": confidence,
        "has_competitor_b": has_competitor_b,
    }


def _parse_profile(section: str, has_competitor_b: bool) -> list[dict[str, str]]:
    expected_columns = 4 if has_competitor_b else 3
    rows = _extract_table(section, "竞争对手画像", expected_columns)[1:]
    if len(rows) != 7:
        raise ValidationError("[校验失败] 竞争对手画像必须为 7 行")
    parsed = []
    for idx, row in enumerate(rows):
        cleaned = [_clean_inline(cell) for cell in row]
        if has_competitor_b:
            item, competitor_a, competitor_b, source = cleaned
        else:
            item, competitor_a, source = cleaned
            competitor_b = "不适用"
        expected = EXPECTED_PROFILE_ROWS[idx]
        if item != expected:
            raise ValidationError(f"[校验失败] 竞争对手画像第 {idx + 1} 行必须为 {expected}")
        parsed.append({"item": item, "competitor_a": competitor_a, "competitor_b": competitor_b, "source": source})
    return parsed


def _parse_enterprise_risk(section: str, has_competitor_b: bool) -> list[dict[str, str]]:
    expected_columns = 4 if has_competitor_b else 3
    rows = _extract_table(section, "竞对企业风险观察", expected_columns)[1:]
    if len(rows) != 5:
        raise ValidationError("[校验失败] 竞对企业风险观察必须为 5 行")
    parsed = []
    for idx, row in enumerate(rows):
        cleaned = [_clean_inline(cell) for cell in row]
        if has_competitor_b:
            item, competitor_a, competitor_b, source = cleaned
        else:
            item, competitor_a, source = cleaned
            competitor_b = "不适用"
        expected = EXPECTED_RISK_ROWS[idx]
        if item != expected:
            raise ValidationError(f"[校验失败] 竞对企业风险观察第 {idx + 1} 行必须为 {expected}")
        if idx == 0:
            _require_enum(competitor_a, RISK_LEVEL_ENUM, "竞品A风险等级")
            _require_enum(competitor_b, RISK_LEVEL_NA_ENUM, "竞品B风险等级")
        if idx == 2:
            _require_enum(competitor_a, YES_NO_UNKNOWN_ENUM, "竞品A是否影响供应商稳定性")
            _require_enum(competitor_b, YES_NO_UNKNOWN_NA_ENUM, "竞品B是否影响供应商稳定性")
        parsed.append({"item": item, "competitor_a": competitor_a, "competitor_b": competitor_b, "source": source})
    return parsed


def _parse_positioning(section: str) -> dict[str, str]:
    return {
        "customer_focus": _extract_bullet_value(section, "客户最关注的竞争维度"),
        "differentiator": _extract_bullet_value(section, "我方可主打的差异化点"),
        "avoidance": _extract_bullet_value(section, "需要避免正面对抗的短板"),
        "story": _extract_bullet_value(section, "差异化故事线"),
    }


def _parse_strategy(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "攻防策略", 6)[1:]
    if len(rows) != 5:
        raise ValidationError("[校验失败] 攻防策略必须为 5 行")
    parsed = []
    for idx, row in enumerate(rows):
        target_competitor, strategy_type, action, response, talk_track, evidence = [_clean_inline(cell) for cell in row]
        expected = EXPECTED_STRATEGY_ROWS[idx]
        if strategy_type != expected:
            raise ValidationError(f"[校验失败] 攻防策略第 {idx + 1} 行必须为 {expected}")
        parsed.append(
            {
                "target_competitor": target_competitor,
                "strategy_type": strategy_type,
                "action": action,
                "response": response,
                "talk_track": talk_track,
                "evidence": evidence,
            }
        )
    return parsed


def _parse_win_path(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "赢单路径", 6)[1:]
    if len(rows) != 3:
        raise ValidationError("[校验失败] 赢单路径必须为 3 行")
    parsed = []
    for idx, row in enumerate(rows):
        priority, action, purpose, time, owner, done_when = [_clean_inline(cell) for cell in row]
        expected = EXPECTED_PRIORITIES[idx]
        if priority != expected:
            raise ValidationError(f"[校验失败] 赢单路径第 {idx + 1} 行优先级必须为 {expected}")
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


def _parse_gaps(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "情报缺口与补充计划", 7)[1:]
    if not rows:
        raise ValidationError("[校验失败] 情报缺口与补充计划至少需要 1 行")
    parsed = []
    for idx, row in enumerate(rows, start=1):
        gap, importance, difficulty, method, priority, deadline, update_target = [_clean_inline(cell) for cell in row]
        if not gap:
            raise ValidationError(f"[校验失败] 情报缺口与补充计划第 {idx} 行缺口不能为空")
        _require_enum(importance, IMPORTANCE_ENUM, f"情报缺口与补充计划第 {idx} 行重要性")
        _require_enum(difficulty, IMPORTANCE_ENUM, f"情报缺口与补充计划第 {idx} 行获取难度")
        _require_enum(priority, PRIORITY_ENUM, f"情报缺口与补充计划第 {idx} 行优先级")
        parsed.append(
            {
                "gap": gap,
                "importance": importance,
                "difficulty": difficulty,
                "method": method,
                "priority": priority,
                "deadline": deadline,
                "update_target": update_target,
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

    meta = _parse_meta(sections["## 输入摘要"])
    has_competitor_b = meta["has_competitor_b"]

    return {
        "meta": meta,
        "core": _parse_core_conclusion(sections["## 一、核心竞争结论"]),
        "intel_status": _parse_intel_status(sections["## 二、三件套收集状态"]),
        "scores": _parse_competitive_scores(sections["## 三、五维竞品分析"], has_competitor_b),
        "profile": _parse_profile(sections["## 四、竞争对手画像"], has_competitor_b),
        "enterprise_risk": _parse_enterprise_risk(sections["## 五、竞对企业风险观察"], has_competitor_b),
        "positioning": _parse_positioning(sections["## 六、差异化定位"]),
        "strategy": _parse_strategy(sections["## 七、攻防策略"]),
        "win_path": _parse_win_path(sections["## 八、赢单路径"]),
        "gaps": _parse_gaps(sections["## 九、情报缺口与补充计划"]),
        "closure_requirements": _parse_closure_requirements(sections["## 收口要求"]),
    }


def _tag_class(value: str) -> str:
    if value in {"领先", "已完成", "低", "是", "充分", "P2"}:
        return "tag-good"
    if value in {"相持", "收集中", "中", "部分充分", "待补充", "P1"}:
        return "tag-warn"
    if value in {"落后", "高", "P0"}:
        return "tag-danger"
    return "tag-neutral"


def _stance_card_class(value: str) -> str:
    return {
        "领先": "stance-leading",
        "相持": "stance-even",
        "落后": "stance-lagging",
        "无法判断": "stance-unknown",
    }.get(value, "stance-unknown")


def _render_list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{_esc(item)}</li>" for item in items) + "</ul>"


def _intel_rows(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        "<tr>"
        f"<td>{_esc(row['item'])}</td>"
        f"<td><span class=\"tag {_tag_class(row['status'])}\">{_esc(row['status'])}</span></td>"
        f"<td>{_esc(row['facts'])}</td>"
        f"<td>{_esc(row['gap'])}</td>"
        f"<td>{_esc(row['impact'])}</td>"
        "</tr>"
        for row in rows
    )


def _score_rows(rows: list[dict[str, Any]], has_competitor_b: bool) -> str:
    rendered_rows = []
    for row in rows:
        columns = [
            f"<td>{_esc(row['dimension'])}</td>",
            f"<td style=\"text-align:center\">{_esc(row['weight'])}</td>",
            f"<td style=\"text-align:center;font-weight:700\">{_esc(row['our_display'])}</td>",
            f"<td style=\"text-align:center;font-weight:700\">{_esc(row['competitor_a_display'])}</td>",
        ]
        if has_competitor_b:
            columns.append(f"<td style=\"text-align:center;font-weight:700\">{_esc(row['competitor_b_display'])}</td>")
        columns.extend(
            [
                f"<td><span class=\"tag {_tag_class(row['gap'])}\">{_esc(row['gap'])}</span></td>",
                f"<td>{_esc(row['evidence'])}</td>",
            ]
        )
        rendered_rows.append("<tr>" + "".join(columns) + "</tr>")
    return "\n".join(rendered_rows)


def _simple_rows(rows: list[dict[str, str]], keys: list[str]) -> str:
    out = []
    for row in rows:
        out.append("<tr>" + "".join(f"<td>{_esc(row[key])}</td>" for key in keys) + "</tr>")
    return "\n".join(out)


def _enterprise_risk_rows(rows: list[dict[str, str]], has_competitor_b: bool) -> str:
    out = []
    for row in rows:
        competitor_a = row["competitor_a"]
        competitor_b = row["competitor_b"]
        cells = [
            f"<td>{_esc(row['item'])}</td>",
            f"<td><span class=\"tag {_tag_class(competitor_a)}\">{_esc(competitor_a)}</span></td>",
        ]
        if has_competitor_b:
            cells.append(f"<td><span class=\"tag {_tag_class(competitor_b)}\">{_esc(competitor_b)}</span></td>")
        cells.append(f"<td>{_esc(row['source'])}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return "\n".join(out)


def _strategy_rows(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        "<tr>"
        f"<td>{_esc(row['target_competitor'])}</td>"
        f"<td>{_esc(row['strategy_type'])}</td>"
        f"<td>{_esc(row['action'])}</td>"
        f"<td>{_esc(row['response'])}</td>"
        f"<td>{_esc(row['talk_track'])}</td>"
        f"<td>{_esc(row['evidence'])}</td>"
        "</tr>"
        for row in rows
    )


def _win_path_rows(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        "<tr>"
        f"<td><span class=\"tag {_tag_class(row['priority'])}\">{_esc(row['priority'])}</span></td>"
        f"<td>{_esc(row['action'])}</td>"
        f"<td>{_esc(row['purpose'])}</td>"
        f"<td>{_esc(row['time'])}</td>"
        f"<td>{_esc(row['owner'])}</td>"
        f"<td>{_esc(row['done_when'])}</td>"
        "</tr>"
        for row in rows
    )


def _gap_rows(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        "<tr>"
        f"<td>{_esc(row['gap'])}</td>"
        f"<td><span class=\"tag {_tag_class(row['importance'])}\">{_esc(row['importance'])}</span></td>"
        f"<td>{_esc(row['difficulty'])}</td>"
        f"<td>{_esc(row['method'])}</td>"
        f"<td><span class=\"tag {_tag_class(row['priority'])}\">{_esc(row['priority'])}</span></td>"
        f"<td>{_esc(row['deadline'])}</td>"
        f"<td>{_esc(row['update_target'])}</td>"
        "</tr>"
        for row in rows
    )


def _render_score_strip(scores: dict[str, Any], competitor_names: list[str]) -> str:
    items = [
        f"<div><span>我方</span><strong>{_esc(scores['our_total_display'])}</strong></div>",
        f"<div><span>{_esc(competitor_names[0])}</span><strong>{_esc(scores['competitor_a_total_display'])}</strong></div>",
    ]
    if scores["has_competitor_b"]:
        items.append(f"<div><span>{_esc(competitor_names[1])}</span><strong>{_esc(scores['competitor_b_total_display'])}</strong></div>")
    items.append(f"<div><span>竞争态势</span><strong>{_esc(scores['stance'])}</strong></div>")
    return "".join(items)


def _render_score_table_header(competitor_names: list[str], has_competitor_b: bool) -> str:
    headers = ["维度", "权重", "我方得分", f"{competitor_names[0]}得分"]
    if has_competitor_b:
        headers.append(f"{competitor_names[1]}得分")
    headers.extend(["我方相对态势", "证据说明"])
    return "<tr>" + "".join(f"<th>{_esc(header)}</th>" for header in headers) + "</tr>"


def _render_competitor_table_header(first_col: str, competitor_names: list[str], has_competitor_b: bool) -> str:
    headers = [first_col, competitor_names[0]]
    if has_competitor_b:
        headers.append(competitor_names[1])
    headers.append("证据来源")
    return "<tr>" + "".join(f"<th>{_esc(header)}</th>" for header in headers) + "</tr>"


def _render(data: dict[str, Any], style_css: str) -> str:
    meta = data["meta"]
    core = data["core"]
    scores = data["scores"]
    positioning = data["positioning"]
    competitor_names = meta["competitor_names"]
    has_competitor_b = meta["has_competitor_b"]
    profile_keys = ["item", "competitor_a"] + (["competitor_b"] if has_competitor_b else []) + ["source"]
    stance_class = _stance_card_class(core["stance"])
    title = f"{meta['opportunity_name']} - 竞争分析报告"

    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>{_esc(title)}</title>
<style>
{style_css}
</style>
</head>
<body>
<div class=\"cover\">
  <div class=\"cover-inner\">
    <div class=\"cover-main\">
      <div>
        <div class=\"eyebrow\">Opportunity Competitive Analysis Report</div>
        <h1>{_esc(meta['opportunity_name'])} · 竞争分析</h1>
        <div class=\"cover-meta\">
          <span>诊断日期：{_esc(meta['diagnosis_date'])}</span>
          <span>项目阶段：{_esc(meta['stage'])}</span>
          <span>主要竞品：{_esc(meta['competitors'])}</span>
          <span>{_esc(meta['analysis_scope'])}</span>
        </div>
      </div>
      <div class=\"stance-card {stance_class}\">
        <strong>{_esc(core['stance'])}</strong>
        <span>竞争态势</span>
      </div>
    </div>
  </div>
</div>

<div class=\"layout\">
  <aside class=\"toc\">
    <div class=\"toc-title\">目录</div>
    <a href=\"#summary\" class=\"active\">一、核心竞争结论</a>
    <a href=\"#kit\">二、三件套收集状态</a>
    <a href=\"#score\">三、五维竞品分析</a>
    <a href=\"#profile\">四、竞争对手画像</a>
    <a href=\"#enterprise-risk\">五、竞对企业风险观察</a>
    <a href=\"#positioning\">六、差异化定位</a>
    <a href=\"#strategy\">七、攻防策略</a>
    <a href=\"#path\">八、赢单路径</a>
    <a href=\"#gaps\">九、情报缺口与补充计划</a>
  </aside>

  <main class=\"container\">
    <section class=\"section\" id=\"summary\">
      <h2><span>一</span>核心竞争结论</h2>
      <div class=\"summary-grid\">
        <div class=\"summary-card wide\">
          <div class=\"card-label\">一句话结论</div>
          <p>{_esc(core['one_liner'])}</p>
        </div>
        <div class=\"summary-card\">
          <div class=\"card-label\">核心优势</div>
          <p>{_esc(core['strength'])}</p>
        </div>
        <div class=\"summary-card\">
          <div class=\"card-label\">核心短板</div>
          <p>{_esc(core['weakness'])}</p>
        </div>
        <div class=\"summary-card\">
          <div class=\"card-label\">关键风险</div>
          <p>{_esc(core['risk'])}</p>
        </div>
      </div>
      <div class=\"insight-box\"><strong>关键行动项</strong>{_render_list(core['key_actions'])}</div>
    </section>

    <section class=\"section\" id=\"kit\">
      <h2><span>二</span>三件套收集状态</h2>
      <div class=\"table-wrap\"><table>
        <thead><tr><th>件套</th><th>收集状态</th><th>已知事实</th><th>缺口</th><th>对判断的影响</th></tr></thead>
        <tbody>{_intel_rows(data['intel_status'])}</tbody>
      </table></div>
    </section>

    <section class=\"section\" id=\"score\">
      <h2><span>三</span>五维竞品分析</h2>
      <div class=\"score-strip\">{_render_score_strip(scores, competitor_names)}</div>
      <div class=\"table-wrap\"><table>
        <thead>{_render_score_table_header(competitor_names, has_competitor_b)}</thead>
        <tbody>{_score_rows(scores['rows'], has_competitor_b)}</tbody>
      </table></div>
      <div class=\"note-box\"><strong>可信度说明：</strong>{_esc(scores['confidence'])}</div>
    </section>

    <section class=\"section\" id=\"profile\">
      <h2><span>四</span>竞争对手画像</h2>
      <div class=\"table-wrap\"><table>
        <thead>{_render_competitor_table_header('项目', competitor_names, has_competitor_b)}</thead>
        <tbody>{_simple_rows(data['profile'], profile_keys)}</tbody>
      </table></div>
    </section>

    <section class=\"section\" id=\"enterprise-risk\">
      <h2><span>五</span>竞对企业风险观察</h2>
      <div class=\"table-wrap\"><table>
        <thead>{_render_competitor_table_header('项目', competitor_names, has_competitor_b)}</thead>
        <tbody>{_enterprise_risk_rows(data['enterprise_risk'], has_competitor_b)}</tbody>
      </table></div>
      <div class=\"note-box\">企业风险只作为供应商稳定性观察和客户验证建议，不替代五维竞品分析。</div>
    </section>

    <section class=\"section\" id=\"positioning\">
      <h2><span>六</span>差异化定位</h2>
      <div class=\"summary-grid\">
        <div class=\"summary-card\"><div class=\"card-label\">客户关注</div><p>{_esc(positioning['customer_focus'])}</p></div>
        <div class=\"summary-card\"><div class=\"card-label\">主打差异化</div><p>{_esc(positioning['differentiator'])}</p></div>
        <div class=\"summary-card\"><div class=\"card-label\">避免正面对抗</div><p>{_esc(positioning['avoidance'])}</p></div>
      </div>
      <div class=\"insight-box\"><strong>差异化故事线</strong><p>{_esc(positioning['story'])}</p></div>
    </section>

    <section class=\"section\" id=\"strategy\">
      <h2><span>七</span>攻防策略</h2>
      <div class=\"table-wrap\"><table>
        <thead><tr><th>目标竞品</th><th>策略类型</th><th>我方动作</th><th>应对竞品</th><th>话术要点</th><th>证据要求</th></tr></thead>
        <tbody>{_strategy_rows(data['strategy'])}</tbody>
      </table></div>
    </section>

    <section class=\"section\" id=\"path\">
      <h2><span>八</span>赢单路径</h2>
      <div class=\"table-wrap\"><table>
        <thead><tr><th>优先级</th><th>动作</th><th>目的</th><th>时间</th><th>负责人/对象</th><th>完成标志</th></tr></thead>
        <tbody>{_win_path_rows(data['win_path'])}</tbody>
      </table></div>
    </section>

    <section class=\"section\" id=\"gaps\">
      <h2><span>九</span>情报缺口与补充计划</h2>
      <div class=\"table-wrap\"><table>
        <thead><tr><th>缺口</th><th>重要性</th><th>获取难度</th><th>获取方法</th><th>优先级</th><th>截止时间</th><th>补齐后更新项</th></tr></thead>
        <tbody>{_gap_rows(data['gaps'])}</tbody>
      </table></div>
    </section>

    <div class=\"footer-note\">本报告遵循 sfa-opportunity-competitive-analysis 竞争分析诊断标准。正文中的“待补充 / 无法判断 / ⚠️ 推断”仅用于竞争分析梳理，需后续验证。</div>
  </main>
</div>
</body>
</html>
"""


SCHEMA_TEXT = """# sfa-opportunity-competitive-analysis HTML renderer schema

必须包含以下 Markdown 章节：
- ## 输入摘要
- ## 一、核心竞争结论
- ## 二、三件套收集状态
- ## 三、五维竞品分析
- ## 四、竞争对手画像
- ## 五、竞对企业风险观察
- ## 六、差异化定位
- ## 七、攻防策略
- ## 八、赢单路径
- ## 九、情报缺口与补充计划
- ## 收口要求

关键校验：
- 三件套必须严格包含：竞品产品功能对比 / 竞品报价策略 / 竞品客户关系。
- 输入摘要必须包含“主分析范围”，并说明最多 2 个重点竞品，其他竞品进入情报缺口。
- 五维分析必须严格包含：品牌力 / 产品平台 / 行业 Know-how / 本地交付 / 商务成本。
- 主分析竞品最多 2 个；`主要竞品` 必须填写 1-2 个具体竞对名称。
- 双竞品模式下沿用现有 A/B 结构；单竞品模式下，五维分析、竞争对手画像、竞对企业风险观察允许省略竞品B列。
- 权重必须为 1-5；得分必须为 0-10、x/10、不适用 或 无法判断。
- 竞争态势和差距只能为：领先 / 相持 / 落后 / 无法判断。
- 竞对企业风险观察必须包含：风险等级 / 主要风险类型 / 是否影响供应商稳定性 / 建议验证动作 / 对本商机的影响。
- 赢单路径必须为 3 行表格，优先级依次为 P0 / P1 / P2。
"""


def _read_input(markdown_text: str | None, input_path: str | None) -> str:
    if markdown_text:
        return markdown_text
    if input_path:
        return Path(input_path).read_text(encoding="utf-8")
    return sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render competition intelligence markdown to HTML")
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
