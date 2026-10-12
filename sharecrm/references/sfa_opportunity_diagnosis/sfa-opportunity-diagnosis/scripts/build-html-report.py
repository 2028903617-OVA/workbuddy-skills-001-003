#!/usr/bin/env python3
"""
build-html-report.py

将 sfa-opportunity-diagnosis 的 Markdown 诊断正文渲染为 HTML 报告。

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
    "## 二、全局诊断结果",
    "## 三、关键卡点与风险暴露",
    "## 四、核心打法策略",
    "## 五、行动建议",
    "## 六、需求地图分析",
    "## 七、竞争态势分析",
    "## 八、决策链分析",
]

EXPECTED_DEMAND_ITEMS = ["表面需求", "真实推力", "推进条件", "当前错位"]
PRIORITY_TAG = {"P0": "tag-p0", "P1": "tag-p1", "P2": "tag-p2"}
EVIDENCE_TAG = {
    "confirmed": ("tag-confirmed", "已证实"),
    "inferred": ("tag-inferred", "大概率发生"),
    "unknown": ("tag-unknown", "待确认"),
}
COMPETITION_STANCES = {"进攻", "相持", "防守", "待确认"}


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
    value = re.sub(r"\*{1,2}", "", value)
    value = re.sub(r"`(.*?)`", r"\1", value)
    value = value.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    return value.strip()


def _is_placeholder(value: str) -> bool:
    stripped = value.strip().strip("`").strip()
    return (
        (stripped.startswith("<") and stripped.endswith(">"))
        or (stripped.startswith("{") and stripped.endswith("}"))
    )


def _split_rows(section: str) -> list[str]:
    return [line.strip() for line in section.splitlines()]


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
        raise ValidationError(
            f"[校验失败] {path} 列数应为 {expected_columns}，实际为 {len(cells)}"
        )
    return cells


def _extract_table(section: str, heading: str, expected_columns: int) -> list[list[str]]:
    lines = _split_rows(section)
    table_lines: list[str] = []
    in_table = False
    for line in lines:
        if line.startswith("|"):
            table_lines.append(line)
            in_table = True
        elif in_table:
            break
    if len(table_lines) < 3:
        raise ValidationError(f"[校验失败] {heading} 缺少完整表格")
    rows = [_split_table_row(table_lines[0], expected_columns, f"{heading} 表头")]
    for idx, line in enumerate(table_lines[2:], start=1):
        rows.append(_split_table_row(line, expected_columns, f"{heading} 第 {idx} 行"))
    return rows


def _extract_bullet_value(section: str, label: str, *, required: bool = True) -> str:
    pattern = rf"(?m)^-\s*(?:\*\*)?{re.escape(label)}(?:[（(][^）)]*[）)])?(?:\*\*)?[:：]\s*(.*?)\s*$"
    match = re.search(pattern, section)
    if match:
        return _clean_inline(match.group(1))
    if required:
        raise ValidationError(f"[校验失败] 缺少字段：{label}")
    return ""


def _extract_bullet_list(section: str, label: str, *, required: bool = True) -> list[str]:
    pattern = rf"(?m)^-\s*(?:\*\*)?{re.escape(label)}(?:[（(][^）)]*[）)])?(?:\*\*)?[:：]\s*(.*?)\s*$"
    match = re.search(pattern, section)
    if not match:
        if required:
            raise ValidationError(f"[校验失败] 缺少字段：{label}")
        return []

    inline_value = _clean_inline(match.group(1))
    following = section[match.end() :]
    items: list[str] = []

    numbered_pattern = r"^\s*(?:\d+[.．、)]|[①②③④⑤⑥⑦⑧⑨⑩])\s*(.+?)\s*$"
    if inline_value and re.match(numbered_pattern, inline_value):
        items.append(inline_value)
        collect_numbered_only = True
    else:
        collect_numbered_only = False

    for line in following.splitlines():
        if not line.strip():
            continue
        if re.match(r"^(?:-\s*\S|\|\s*\S|#{2,}\s*\S)", line):
            break

        bullet_match = re.match(r"^\s+-\s*(.+?)\s*$", line)
        numbered_match = re.match(numbered_pattern, line)
        if bullet_match and not collect_numbered_only:
            items.append(_clean_inline(bullet_match.group(1)))
            continue
        if numbered_match:
            items.append(_clean_inline(line))
            continue
        if items and re.match(r"^\s{2,}\S", line):
            items[-1] = f"{items[-1]} {_clean_inline(line)}".strip()
            continue
        break

    if items:
        return items
    if inline_value:
        # 兼容模型把列表压成一行的情况：
        # 1) 用分号分隔：A；B；C
        # 2) 用竖线分隔：① A | ② B | ③ C
        # 3) 仅用序号分隔：① A ② B ③ C / 1. A 2. B 3. C
        normalized = re.sub(r"\s*[|｜]\s*(?=(?:[①②③④⑤⑥⑦⑧⑨⑩]|\d+[.．、)]))", "\n", inline_value)
        normalized = re.sub(r"(?<!^)\s*(?=(?:[①②③④⑤⑥⑦⑧⑨⑩]|\d+[.．、)]))", "\n", normalized)
        parts = re.split(r"[；;\n]+", normalized)
        return [item.strip() for item in parts if item.strip()]
    return []


def _extract_paragraph_after(section: str, prefix: str) -> str:
    pattern = rf"(?ms)^{re.escape(prefix)}\s*(.+?)(?=\n(?:- |\| |## |### )|\Z)"
    match = re.search(pattern, section)
    if not match:
        raise ValidationError(f"[校验失败] 缺少字段：{prefix}")
    return _clean_inline(match.group(1))


def _find_line_value(section: str, label: str) -> str:
    pattern = (
        rf"(?m)^(?:- )?(?:\*\*)?{re.escape(label)}"
        rf"(?:[:：](?:\*\*)?|(?:\*\*)?[:：])\s*(.*?)\s*$"
    )
    match = re.search(pattern, section)
    if not match:
        raise ValidationError(f"[校验失败] 缺少字段：{label}")
    return _clean_inline(match.group(1))


def _parse_meta(section: str) -> dict[str, str]:
    return {
        "opportunity_name": _extract_bullet_value(section, "商机名称"),
        "diagnosis_date": _extract_bullet_value(section, "诊断日期"),
        "account_name": _extract_bullet_value(section, "客户"),
        "sales_stage": _extract_bullet_value(section, "当前阶段"),
        "ai_stage": _extract_bullet_value(section, "AI判定阶段"),
        "ai_stage_reason": _extract_bullet_value(section, "AI阶段判断说明", required=False),
        "amount": _extract_bullet_value(section, "商机金额"),
        "total_score": _extract_bullet_value(section, "评分总分"),
        "current_rating": _extract_bullet_value(section, "当前评级", required=False),
    }


def _parse_core_conclusion(section: str) -> dict[str, Any]:
    return {
        "one_liner": _extract_bullet_value(section, "一句话结论"),
        "win_factors": _extract_bullet_list(section, "赢单五要素"),
        "core_strategy": _extract_bullet_value(section, "核心打法策略"),
        "best_actions": _extract_bullet_list(section, "关键行动项"),
    }


def _parse_global_diagnosis(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "全局诊断结果", 3)
    data_rows = rows[1:]
    if not data_rows:
        raise ValidationError("[校验失败] 全局诊断结果至少需要 1 个评分维度")
    parsed = []
    for row in data_rows:
        dimension, score, evidence = row
        if not dimension or _is_placeholder(dimension):
            raise ValidationError("[校验失败] 全局诊断结果维度名称不能为空或使用占位符")
        source = ""
        evidence_text = evidence
        leading_source_match = re.match(r"来源[:：]\s*(.+?)(?:。|；|;)\s*(.*)$", evidence)
        if leading_source_match:
            source = _clean_inline(leading_source_match.group(1))
            evidence_text = leading_source_match.group(2).strip()
        else:
            source_match = re.search(r"来源[:：]\s*(.+)$", evidence)
            if source_match:
                source = _clean_inline(source_match.group(1))
                evidence_text = evidence[: source_match.start()].rstrip(" ，;；")
        parsed.append(
            {
                "dimension": dimension,
                "score": score,
                "evidence": _clean_inline(evidence_text),
                "source": source,
            }
        )
    return parsed


def _map_evidence_level(text: str) -> tuple[str, str]:
    value = _clean_inline(text)
    if value.startswith("已证实"):
        return "confirmed", value[len("已证实") :].strip()
    if value.startswith("大概率发生"):
        return "inferred", value[len("大概率发生") :].strip()
    if value.startswith("待确认"):
        return "unknown", value[len("待确认") :].strip()
    return "inferred", value


def _parse_risks(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "关键卡点与风险暴露", 4)
    parsed = []
    for idx, row in enumerate(rows[1:]):
        priority, risk, phenomenon, deep = row
        if priority not in PRIORITY_TAG:
            raise ValidationError(f"[校验失败] 风险表第 {idx + 1} 行优先级必须为 P0/P1/P2")
        evidence_level, deep_text = _map_evidence_level(deep)
        parsed.append(
            {
                "priority": priority,
                "risk": _clean_inline(risk),
                "phenomenon": _clean_inline(phenomenon),
                "deep_judgement": deep_text,
                "evidence_level": evidence_level,
            }
        )
    if not parsed:
        raise ValidationError("[校验失败] 风险表不能为空")
    return parsed


def _parse_strategy(section: str) -> dict[str, Any]:
    verdict = _find_line_value(section, "裁决结论")
    reason = _find_line_value(section, "核心原因")
    direction = _find_line_value(section, "调整方向")

    rows = _extract_table(section, "当前打法 vs 建议打法", 3)
    data_rows = rows[1:]
    if len(data_rows) != 3:
        raise ValidationError("[校验失败] 当前打法 vs 建议打法表必须为 3 行")

    header = rows[0]
    current_title = _clean_inline(header[0])
    suggested_title = _clean_inline(header[2])

    current_play = {
        "title": current_title,
        "doing": _clean_inline(re.sub(r"^\*\*我们现在在做什么：\*\*", "", data_rows[0][0])),
        "why_not_enough": _clean_inline(re.sub(r"^\*\*为什么不够：\*\*", "", data_rows[1][0])),
        "risk": _clean_inline(re.sub(r"^\*\*继续这样打的风险：\*\*", "", data_rows[2][0])),
    }
    suggested_play = {
        "title": suggested_title,
        "positioning": _clean_inline(re.sub(r"^\*\*新的对外定位：\*\*", "", data_rows[0][2])),
        "focus": _clean_inline(re.sub(r"^\*\*新的切入重点：\*\*", "", data_rows[1][2])),
        "why_better": _clean_inline(re.sub(r"^\*\*为什么这条路更可能赢：\*\*", "", data_rows[2][2])),
    }

    return {
        "verdict": verdict,
        "reason": reason,
        "direction": direction,
        "current_play": current_play,
        "suggested_play": suggested_play,
    }


def _parse_actions(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "行动建议", 6)
    parsed = []
    for idx, row in enumerate(rows[1:]):
        priority, action, purpose, time, owner, done_when = row
        if priority not in PRIORITY_TAG:
            raise ValidationError(f"[校验失败] 行动建议第 {idx + 1} 行优先级必须为 P0/P1/P2")
        parsed.append(
            {
                "priority": priority,
                "action": _clean_inline(action),
                "purpose": _clean_inline(purpose),
                "time": _clean_inline(time),
                "owner": _clean_inline(owner),
                "done_when": _clean_inline(done_when),
            }
        )
    if not parsed:
        raise ValidationError("[校验失败] 行动建议不能为空")
    return parsed


def _parse_demand_map(section: str) -> dict[str, Any]:
    summary = _extract_bullet_value(section, "一句话总结")
    maturity = _extract_bullet_value(section, "需求成熟度")
    alignment = _extract_bullet_value(section, "当前我方命中度")
    rows = _extract_table(section, "需求地图分析", 4)
    data_rows = rows[1:]
    if len(data_rows) != 4:
        raise ValidationError("[校验失败] 需求地图分析必须为 4 行")
    parsed_rows = []
    for idx, row in enumerate(data_rows):
        item, basis, conclusion, impact = row
        if item != EXPECTED_DEMAND_ITEMS[idx]:
            raise ValidationError(
                f"[校验失败] 需求地图分析第 {idx + 1} 行判断项应为 {EXPECTED_DEMAND_ITEMS[idx]}"
            )
        parsed_rows.append(
            {
                "item": item,
                "basis": _clean_inline(basis),
                "conclusion": _clean_inline(conclusion),
                "impact": _clean_inline(impact),
            }
        )
    closing = _extract_bullet_value(section, "收口判断")
    return {
        "summary": summary,
        "maturity": maturity,
        "alignment": alignment,
        "rows": parsed_rows,
        "closing": closing,
    }


def _parse_competition(section: str) -> dict[str, Any]:
    stance = _find_line_value(section, "当前竞争态势")
    if stance and stance not in COMPETITION_STANCES and not _is_placeholder(stance):
        raise ValidationError("[校验失败] 当前竞争态势必须为 进攻/相持/防守/待确认")
    core_judgement = _find_line_value(section, "核心判断")
    next_focus = _find_line_value(section, "下一步重点")
    rows = _extract_table(section, "竞争态势分析", 2)
    data_rows = rows[1:]
    if len(data_rows) != 3:
        raise ValidationError("[校验失败] 竞争态势分析必须为 3 行")

    def strip_label(value: str, label: str) -> str:
        return _clean_inline(re.sub(rf"^\*\*{re.escape(label)}\*\*[:：]", "", value))

    left = {
        "current": strip_label(data_rows[0][0], "当前状态"),
        "risk": strip_label(data_rows[1][0], "风险提示"),
        "action": strip_label(data_rows[2][0], "建议动作"),
    }
    right = {
        "base": strip_label(data_rows[0][1], "存量基础"),
        "resource": strip_label(data_rows[1][1], "资源条件"),
        "conversion": strip_label(data_rows[2][1], "待转化点"),
    }
    return {
        "stance": stance,
        "core_judgement": core_judgement,
        "next_focus": next_focus,
        "left": left,
        "right": right,
    }


def _parse_decision_chain(section: str) -> dict[str, Any]:
    alert_match = re.search(
        r"(?ms)^⚠️\s*\*\*决策链关键缺口：\*\*\s*(.+?)\n(.*?)(?=\n\|)",
        section,
    )
    if not alert_match:
        raise ValidationError("[校验失败] 缺少决策链关键缺口说明")
    gap_alert = _clean_inline(alert_match.group(1))
    gap_detail = _clean_inline(alert_match.group(2))
    rows = _extract_table(section, "决策链分析", 5)
    parsed_rows = []
    for row in rows[1:]:
        role, name, stance, concern, breakthrough = row
        parsed_rows.append(
            {
                "role": _clean_inline(role),
                "name": _clean_inline(name),
                "stance": _clean_inline(stance),
                "concern": _clean_inline(concern),
                "breakthrough": _clean_inline(breakthrough),
            }
        )
    if not parsed_rows:
        raise ValidationError("[校验失败] 决策链表不能为空")
    return {
        "gap_alert": gap_alert,
        "gap_detail": gap_detail,
        "rows": parsed_rows,
    }


def _parse_markdown(text: str) -> dict[str, Any]:
    normalized = _normalize(text).strip()
    if not normalized:
        raise ValidationError("[校验失败] 输入为空")

    sections = {}
    for index, heading in enumerate(REQUIRED_SECTIONS):
        next_heading = REQUIRED_SECTIONS[index + 1] if index + 1 < len(REQUIRED_SECTIONS) else None
        sections[heading] = _extract_section(normalized, heading, next_heading)

    return {
        "meta": _parse_meta(sections["## 概要"]),
        "core_conclusion": _parse_core_conclusion(sections["## 一、核心诊断结论"]),
        "global_diagnosis": _parse_global_diagnosis(sections["## 二、全局诊断结果"]),
        "risks": _parse_risks(sections["## 三、关键卡点与风险暴露"]),
        "strategy": _parse_strategy(sections["## 四、核心打法策略"]),
        "actions": _parse_actions(sections["## 五、行动建议"]),
        "demand_map": _parse_demand_map(sections["## 六、需求地图分析"]),
        "competition": _parse_competition(sections["## 七、竞争态势分析"]),
        "decision_chain": _parse_decision_chain(sections["## 八、决策链分析"]),
    }


def _global_diagnosis_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for index, row in enumerate(rows, start=1):
        score_style = _score_style(row["score"])
        source_html = (
            f"<span class=\"evidence-ref\">来源：{_esc(row['source'])}</span>"
            if row["source"]
            else ""
        )
        out.append(
            "<tr>"
            f"<td>{index}. {_esc(row['dimension'])}</td>"
            f"<td style=\"text-align:center;font-weight:700;{score_style}\">{_esc(row['score'])}</td>"
            f"<td>{_esc(row['evidence'])}{source_html}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _risk_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        tag_class = PRIORITY_TAG.get(row["priority"], "tag-p2")
        ev_class, ev_label = EVIDENCE_TAG.get(row["evidence_level"], EVIDENCE_TAG["inferred"])
        out.append(
            "<tr>"
            f"<td><span class=\"tag {tag_class}\">{_esc(row['priority'])}</span></td>"
            f"<td>{_esc(row['risk'])}</td>"
            f"<td>{_esc(row['phenomenon'])}</td>"
            f"<td><span class=\"tag {ev_class}\">{ev_label}</span> {_esc(row['deep_judgement'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _action_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        tag_class = PRIORITY_TAG.get(row["priority"], "tag-p2")
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


def _demand_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        out.append(
            "<tr>"
            f"<td>{_esc(row['item'])}</td>"
            f"<td>{_esc(row['basis'])}</td>"
            f"<td>{_esc(row['conclusion'])}</td>"
            f"<td>{_esc(row['impact'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _decision_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        stance_html = row.get("stance_html", _esc(row["stance"]))
        out.append(
            "<tr>"
            f"<td>{_esc(row['role'])}</td>"
            f"<td>{_esc(row['name'])}</td>"
            f"<td>{stance_html}</td>"
            f"<td>{_esc(row['concern'])}</td>"
            f"<td>{_esc(row['breakthrough'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _render_list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{_esc(item)}</li>" for item in items) + "</ul>"


def _score_style(score: str) -> str:
    match = re.match(r"^\s*(\d+(?:\.\d+)?)", score)
    if not match:
        return "color:#475569"
    value = float(match.group(1))
    if value >= 80:
        return "color:#16a34a"
    if value >= 60:
        return "color:#d97706"
    return "color:#dc2626"


def _split_total_score(total_score: str) -> tuple[str, str]:
    value = total_score.strip()
    match = re.match(
        r"^(?P<score>\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)(?:\s*[（(]?\s*(?P<grade>[A-Za-z][+-]?\s*级?)\s*[）)]?)?$",
        value,
    )
    if not match:
        return value, ""

    score = re.sub(r"\s*/\s*", "/", match.group("score").strip())
    grade = (match.group("grade") or "").replace(" ", "")
    if grade and not grade.endswith("级"):
        grade = f"{grade}级"
    return score, grade


def _display_account_name(value: str) -> str:
    cleaned = re.sub(r"\s*[（(][^）)]*deal_status\s*=\s*[^）)]*[）)]", "", value, flags=re.I)
    cleaned = re.sub(r"\s*[（(][^）)]*回收原因[:：][^）)]*[）)]", "", cleaned, flags=re.I)
    return _clean_inline(cleaned).strip(" /；;，,")


def _display_sales_stage(value: str) -> str:
    cleaned = re.sub(r"\s*[（(]\s*sales_stage\s*=\s*[^）)]*[）)]", "", value, flags=re.I)
    cleaned = re.sub(r"sales_stage\s*=\s*\d+\s*/?", "", cleaned, flags=re.I)
    return _clean_inline(cleaned).strip(" /；;，,")


def _display_ai_stage(value: str) -> str:
    cleaned = _clean_inline(value)
    cleaned = re.sub(r"sales_stage\s*=\s*\d+\s*/?", "", cleaned, flags=re.I)
    cleaned = re.sub(r"sales_status\s*=\s*[^；;,，\s]+\s*/?", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[；;].*$", "", cleaned).strip(" /；;，,")
    if len(cleaned) > 42:
        for sep in ["。", "，", ",", "、", "：", ":"]:
            if sep in cleaned[:42]:
                cleaned = cleaned[: cleaned.find(sep)]
                break
        else:
            cleaned = cleaned[:42].rstrip() + "…"
    return cleaned


def _strategy_summary(strategy: dict[str, Any]) -> str:
    parts = [strategy.get("direction", "").strip(), strategy.get("reason", "").strip()]
    return " ".join(part for part in parts if part)


def _competition_summary(competition: dict[str, Any]) -> str:
    return (
        f"当前竞争态势为{competition['stance']}。"
        f"{competition['core_judgement']} "
        f"下一步重点：{competition['next_focus']}"
    ).strip()


def _render_decision_stance(value: str) -> str:
    mapping = {
        "支持": "tag tag-h1",
        "中立": "tag tag-h2",
        "反对": "tag tag-p0",
        "未知": "tag tag-inferred",
    }
    css_class = mapping.get(value)
    if not css_class:
        return _esc(value)
    return f"<span class=\"{css_class}\">{_esc(value)}</span>"


def _render(data: dict[str, Any], style_css: str) -> str:
    meta = data["meta"]
    cc = data["core_conclusion"]
    strategy = data["strategy"]
    cur = strategy["current_play"]
    new = strategy["suggested_play"]
    dm = data["demand_map"]
    comp = data["competition"]
    dc = data["decision_chain"]
    sales_stage_display = _display_sales_stage(meta["sales_stage"])
    ai_stage_display = _display_ai_stage(meta["ai_stage"])
    account_name_display = _display_account_name(meta["account_name"])
    total_score, total_grade = _split_total_score(meta["total_score"])
    if not total_grade and meta.get("current_rating"):
        total_grade = meta["current_rating"].replace(" ", "")
    total_score_main, total_score_suffix = (
        total_score.split("/", 1) if "/" in total_score else (total_score, "")
    )
    total_score_suffix_html = (
        f"<span class=\"win-rate-denominator\">/{_esc(total_score_suffix)}</span>"
        if total_score_suffix
        else ""
    )
    total_grade_html = (
        f"<div class=\"win-rate-grade\">{_esc(total_grade)}</div>" if total_grade else ""
    )
    strategy_summary = _strategy_summary(strategy) or strategy["direction"] or strategy["reason"]
    competition_summary = _competition_summary(comp)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(meta['opportunity_name'])} - AI 诊断报告</title>
<style>
{style_css}
</style>
</head>
<body>
<div class="cover">
  <div class="cover-inner">
    <div class="cover-head">
      <div>
        <div class="eyebrow">Opportunity Diagnosis Report</div>
        <h1>{_esc(meta['opportunity_name'])}</h1>
        <div class="subtitle">基于 CRM 商机事实、评分结果与诊断规则生成，用于支持推进判断与行动决策。</div>
      </div>
      <div class="win-rate-box">
        <div class="win-rate-num">{_esc(total_score_main)}{total_score_suffix_html}</div>
        {total_grade_html}
        <div class="win-rate-label">商机健康度</div>
      </div>
    </div>
    <dl class="cover-meta">
      <div><dt>诊断日期</dt><dd>{_esc(meta['diagnosis_date'])}</dd></div>
      <div><dt>客户名称</dt><dd>{_esc(account_name_display)}</dd></div>
      <div><dt>当前阶段</dt><dd>{_esc(sales_stage_display)}</dd></div>
      <div><dt>AI判断阶段</dt><dd>{_esc(ai_stage_display)}</dd></div>
      <div><dt>商机金额</dt><dd>{_esc(meta['amount'])}</dd></div>
    </dl>
    <div class="pill-row">
      <span class="pill pill-slate">AI 阶段依据：{_esc(meta['ai_stage_reason']) if meta.get('ai_stage_reason') else '系统未补充'}</span>
      <span class="pill pill-amber">评分结果仅供诊断参考</span>
    </div>
  </div>
</div>

<div class="layout">
  <aside class="toc">
    <div class="toc-title">目录</div>
    <a href="#section-overview" class="active">一、核心诊断结论</a>
    <a href="#section-global">二、全局诊断结果</a>
    <a href="#section-risk">三、关键卡点与风险暴露</a>
    <a href="#section-strategy">四、核心打法策略</a>
    <a href="#section-actions">五、30天关键行动计划</a>
    <a href="#section-tabs">六、情报研判</a>
  </aside>

  <div class="container">
  <div class="content">

<div class="section" id="section-overview">
<div class="section-title"><span class="num">一</span>核心诊断结论</div>
<div class="conclusion-box">
<p><strong>一句话结论：</strong>{_esc(cc['one_liner'])}</p>
<div class="key-insight">赢单五要素：</div>
{_render_list(cc['win_factors'])}
<div class="key-insight">核心打法策略：</div>
<p>{_esc(cc['core_strategy'])}</p>
<div class="key-insight">关键行动项：</div>
{_render_list(cc['best_actions'])}
</div>
</div>

<div class="section" id="section-global">
<div class="section-title"><span class="num">二</span>全局诊断结果</div>
<div class="table-wrap">
<table>
<thead><tr><th>评估维度</th><th style="text-align:center">评分</th><th>评分依据</th></tr></thead>
<tbody>
{_global_diagnosis_rows(data['global_diagnosis'])}
</tbody>
</table>
</div>
</div>

<div class="section" id="section-risk">
<div class="section-title"><span class="num">三</span>关键卡点与风险暴露</div>
<div class="table-wrap">
<table>
<thead><tr><th>优先级</th><th>风险点</th><th>表面现象</th><th>深层判断</th></tr></thead>
<tbody>
{_risk_rows(data['risks'])}
</tbody>
</table>
</div>
</div>

<div class="section" id="section-strategy">
<div class="section-title"><span class="num">四</span>核心打法策略</div>
<div class="alert-box alert-blue" style="margin-top:14px"><strong>一句话总结：</strong>{_esc(strategy_summary)}</div>
<div style="display:grid;grid-template-columns:1fr 44px 1fr;gap:18px;margin-top:16px;align-items:stretch">
<div style="border:1px solid #fecaca;border-radius:10px;padding:18px 20px;background:#fff7f7">
<div style="font-size:14px;font-weight:700;color:#1e293b;margin-bottom:10px">{_esc(cur['title'])}</div>
<p style="font-size:13px;color:#64748b;line-height:1.8;margin-bottom:8px"><strong>我们现在在做什么：</strong>{_esc(cur['doing'])}</p>
<p style="font-size:13px;color:#64748b;line-height:1.8;margin-bottom:8px"><strong>为什么不够：</strong>{_esc(cur['why_not_enough'])}</p>
<p style="font-size:13px;color:#991b1b;line-height:1.8"><strong>继续这样打的风险：</strong>{_esc(cur['risk'])}</p>
</div>
<div style="display:flex;align-items:center;justify-content:center;font-size:24px;color:#1e40af;font-weight:800">→</div>
<div style="border:1px solid #bbf7d0;border-radius:10px;padding:18px 20px;background:#f6fff8">
<div style="font-size:14px;font-weight:700;color:#1e293b;margin-bottom:10px">{_esc(new['title'])}</div>
<p style="font-size:13px;color:#475569;line-height:1.8;margin-bottom:8px"><strong>新的对外定位：</strong>{_esc(new['positioning'])}</p>
<p style="font-size:13px;color:#475569;line-height:1.8;margin-bottom:8px"><strong>新的切入重点：</strong>{_esc(new['focus'])}</p>
<p style="font-size:13px;color:#166534;line-height:1.8"><strong>为什么这条路更可能赢：</strong>{_esc(new['why_better'])}</p>
</div>
</div>
</div>

<div class="section" id="section-actions">
<div class="section-title"><span class="num">五</span>30天关键行动计划</div>
<div class="table-wrap">
<table>
<thead><tr><th>优先级</th><th>动作</th><th>目的</th><th>时间</th><th>负责人/对象</th><th>完成标志</th></tr></thead>
<tbody>
{_action_rows(data['actions'])}
</tbody>
</table>
</div>
</div>

<div class="tabbed-section" id="section-tabs">
<div class="section-title"><span class="num">六</span>情报研判</div>
<div class="tab-nav">
<button class="tab-btn active" type="button" data-tab-target="tab-demand">需求地图分析</button>
<button class="tab-btn" type="button" data-tab-target="tab-competition">竞争态势分析</button>
<button class="tab-btn" type="button" data-tab-target="tab-decision">决策链分析</button>
</div>

<div id="tab-demand" class="tab-panel active">
<div class="section">
<div class="conclusion-box" style="margin-top:16px">
<p><strong>一句话总结：</strong>{_esc(dm['summary'])}</p>
<p style="margin-top:10px;color:#1e40af;font-weight:700">需求成熟度：{_esc(dm['maturity'])}</p>
<p style="margin-top:6px;color:#1e40af;font-weight:700">当前我方命中度：{_esc(dm['alignment'])}</p>
</div>
<div class="table-wrap">
<table>
<thead><tr><th>判断项</th><th>判断依据</th><th>当前结论</th><th>对推进的影响</th></tr></thead>
<tbody>
{_demand_rows(dm['rows'])}
</tbody>
</table>
</div>
<div class="alert-box alert-blue" style="margin-top:14px"><strong>收口判断：</strong>{_esc(dm['closing'])}</div>
</div>
</div>

<div id="tab-competition" class="tab-panel">
<div class="section">
<div class="alert-box alert-blue" style="margin-top:14px"><strong>总结：</strong>{_esc(competition_summary)}</div>
<div style="display:grid;grid-template-columns:1fr 1px 1fr;gap:20px;margin-top:16px">
<div>
<div style="font-size:13px;font-weight:700;color:#dc2626;margin-bottom:10px">🔴 竞争情况</div>
<div style="font-size:12px">
<p style="margin-bottom:6px"><strong>当前状态：</strong>{_esc(comp['left']['current'])}</p>
<p style="margin-bottom:6px"><strong>风险提示：</strong>{_esc(comp['left']['risk'])}</p>
<p><strong>建议动作：</strong>{_esc(comp['left']['action'])}</p>
</div>
</div>
<div style="background:#e2e8f0"></div>
<div>
<div style="font-size:13px;font-weight:700;color:#1e40af;margin-bottom:10px">🔵 我方优势</div>
<div style="font-size:12px">
<p style="margin-bottom:6px"><strong>存量基础：</strong>{_esc(comp['right']['base'])}</p>
<p style="margin-bottom:6px"><strong>资源条件：</strong>{_esc(comp['right']['resource'])}</p>
<p><strong>待转化点：</strong>{_esc(comp['right']['conversion'])}</p>
</div>
</div>
</div>
</div>
</div>

<div id="tab-decision" class="tab-panel">
<div class="section">
<div class="alert-box alert-red" style="margin-top:14px">
<strong>⚠️ 决策链关键缺口：</strong>{_esc(dc['gap_alert'])}<br>{_esc(dc['gap_detail'])}
</div>
<div class="table-wrap">
<table>
<thead><tr><th>角色</th><th>姓名</th><th>当前立场</th><th>核心顾虑</th><th>突破策略</th></tr></thead>
<tbody>
{_decision_rows([
    {
        **row,
        "stance_html": _render_decision_stance(row["stance"]),
    }
    for row in dc["rows"]
])}
</tbody>
</table>
</div>
</div>
</div>
</div>

<script>
const tabButtons = document.querySelectorAll('[data-tab-target]');
const tabPanels = document.querySelectorAll('.tab-panel');
tabButtons.forEach((button) => {{
  button.addEventListener('click', () => {{
    const targetId = button.getAttribute('data-tab-target');
    tabButtons.forEach((item) => item.classList.remove('active'));
    tabPanels.forEach((panel) => {{
      panel.classList.remove('active');
      panel.hidden = true;
    }});
    button.classList.add('active');
    const targetPanel = document.getElementById(targetId);
    if (targetPanel) {{
      targetPanel.classList.add('active');
      targetPanel.hidden = false;
    }}
  }});
}});

const links = document.querySelectorAll('.toc a');
const sections = [...document.querySelectorAll('#section-overview, #section-global, #section-risk, #section-strategy, #section-actions, #section-tabs')];
const observer = new IntersectionObserver((entries) => {{
  entries.forEach((entry) => {{
    if (entry.isIntersecting) {{
      links.forEach((link) => link.classList.remove('active'));
      const active = document.querySelector(`.toc a[href="#${{entry.target.id}}"]`);
      if (active) active.classList.add('active');
    }}
  }});
}}, {{ rootMargin: '-30% 0px -55% 0px', threshold: 0.1 }});
sections.forEach((section) => observer.observe(section));
</script>
<div class="footer-note">
📎 本报告遵循 SFA 商机诊断标准（sfa-opportunity-diagnosis）。正文中的"推断/未知"仅用于诊断梳理，需后续验证。
</div>
</div>
</div>
</div>
</body>
</html>
"""


MARKDOWN_SCHEMA_HINT = """\
输入必须是符合 `references/output_template.md` 固定结构的 Markdown，至少包含以下章节：

## 概要
- 商机名称：
- 诊断日期：
- 客户：
- 当前阶段：
- AI判定阶段：
- AI阶段判断说明：
- 商机金额：
- 评分总分：

## 一、核心诊断结论
- 一句话结论：
- 赢单五要素：
  - 项目真实性：
  - Coach：
  - 决策链：
  - 竞争壁垒：
  - 控制点：
- 核心打法策略：
- 关键行动项：
  - <行动一>
  - <行动二>
  - <行动三>

## 二、全局诊断结果
| 维度 | 评分 | 评分依据 |

## 三、关键卡点与风险暴露
| 优先级 | 风险点 | 表面现象 | 深层判断 |

## 四、核心打法策略
- **裁决结论：**
- **核心原因：**
- **调整方向：**
| 当前打法：... | → | 建议打法：... |

## 五、行动建议
| 优先级 | 动作 | 目的 | 时间 | 负责人/对象 | 完成标志 |

## 六、需求地图分析
- 一句话总结：
- 需求成熟度：
- 当前我方命中度：
| 判断项 | 判断依据 | 当前结论 | 对推进的影响 |
- 收口判断：

## 七、竞争态势分析
- **当前竞争态势**：
- **核心判断**：
- **下一步重点**：
| **竞争情况** | **我方优势** |

## 八、决策链分析
⚠️ **决策链关键缺口：** ...
| 角色 | 姓名 | 当前立场 | 核心顾虑 | 突破策略 |
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="渲染商机诊断 HTML 报告")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--markdown", help="输入 Markdown 原文")
    input_group.add_argument("--input", help="输入 Markdown 路径；兼容旧调用，缺省从 stdin 读取")
    parser.add_argument("--output", help="输出 HTML 路径，缺省写到 stdout")
    parser.add_argument(
        "--schema", action="store_true", help="打印输入 Markdown 结构提示并退出"
    )
    args = parser.parse_args()

    if args.schema:
        sys.stdout.write(MARKDOWN_SCHEMA_HINT)
        return 0

    if args.markdown is not None:
        raw = args.markdown
    elif args.input:
        try:
            raw = Path(args.input).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[校验失败] 读取输入失败：{exc}", file=sys.stderr)
            return 1
    else:
        raw = sys.stdin.read()

    try:
        data = _parse_markdown(raw)
        style_css = _read_style()
        rendered = _render(data, style_css)
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"[校验通过] 已写入：{out_path}", file=sys.stderr)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
