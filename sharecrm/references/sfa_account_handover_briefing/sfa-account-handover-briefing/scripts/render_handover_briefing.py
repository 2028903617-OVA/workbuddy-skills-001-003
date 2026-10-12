#!/usr/bin/env python3
"""Render a team handover briefing from a structured facts bundle."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from html import escape as html_escape
from pathlib import Path
from typing import Any, Iterable

from validate_handover_briefing import validate_html


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "assets" / "templates" / "handover.html"
DEFAULT_CSS = ROOT / "assets" / "styles" / "handover.css"
VALID_MODES = {"standard", "full"}
VALID_QUERY_STATUSES = {"已读取", "无数据", "权限不足", "未触发查询", "查询失败"}
DEFAULT_COVERAGE_LABELS = (
    "客户",
    "商机",
    "联系人",
    "跟进记录",
    "待办/任务",
    "需求/问题",
    "会议",
    "竞品明细",
    "合同/订单/回款",
    "外部情报",
)
API_NAME_LABELS = {
    "AIMeetingChunkObj": "会议",
    "MethodologyTaskObj": "待办/任务",
    "ActivityQuestionObj": "需求/问题",
    "CompetitiveLinesObj": "竞品明细",
    "NewOpportunityObj": "商机",
    "ActivityTodoObj": "待办/任务",
    "ActiveRecordObj": "跟进记录",
    "AIMeetingObj": "会议",
    "SalesOrderObj": "合同/订单/回款",
    "RequirementObj": "需求/问题",
    "ScheduleObj": "会议",
    "ContactObj": "联系人",
    "ContractObj": "合同/订单/回款",
    "PaymentObj": "合同/订单/回款",
    "AccountObj": "客户",
    "CheckinsObj": "现场拜访",
    "CasesObj": "服务工单",
    "Memory": "历史信息",
}
BUSINESS_TERM_PATTERNS = (
    (r"客户\s*Memory", "历史信息"),
    (r"\bMemory\b", "历史信息"),
    (r"客户记忆", "历史信息"),
    (r"内部支持者[（(]\s*Coach\s*[）)]", "内部支持者"),
    (r"守门人[（(]\s*Gatekeeper\s*[）)]", "守门人"),
    (r"\bGatekeeper\b", "守门人"),
    (r"\bCoach\b", "内部支持者"),
    (r"\bAE\b", "客户经理"),
    (r"(?<![（(])\bEB\s*候选", "最终决策人候选（EB）"),
    (r"(?<![（(])\bEB\b", "最终决策人（EB）"),
    (r"(?<![（(])\bTB\b", "技术把关人（TB）"),
    (r"\bIT\s*负责人", "信息化负责人"),
    (r"\bIT\s*总监", "信息化总监"),
    (r"(?<![（(])\bIT\b", "信息化（IT）"),
    (r"(?<![（(])\bVP\b", "副总裁（VP）"),
    (r"(?<![（(])\bIVD\b", "体外诊断（IVD）"),
    (r"\bfull\s*模式", "完整模式"),
)


def normalize_api_names(value: Any) -> str:
    text = str(value or "")
    for api_name, label in API_NAME_LABELS.items():
        text = re.sub(rf"\b{re.escape(api_name)}\b", label, text)
    for pattern, replacement in BUSINESS_TERM_PATTERNS:
        text = re.sub(pattern, replacement, text)
    chinese_terms = r"副总裁（VP）|信息化（IT）|信息化负责人|信息化总监|内部支持者|守门人|客户经理|最终决策人（EB）|最终决策人候选（EB）|技术把关人（TB）"
    text = re.sub(rf"([\u4e00-\u9fff])\s+({chinese_terms})", r"\1\2", text)
    text = re.sub(rf"({chinese_terms})\s+([\u4e00-\u9fff])", r"\1\2", text)
    return text


def is_memory_output_label(value: Any) -> bool:
    return bool(re.search(r"(?i)(?:客户\s*)?memory|客户记忆|记忆状态", str(value or "")))


def memory_information_is_incomplete(metadata: dict[str, Any]) -> bool:
    return str(metadata.get("memory_status") or "").strip().lower() in {"partial", "insufficient", "部分", "不足"}


def render_source_text(value: Any, default: str) -> str:
    values = value if isinstance(value, list) else re.split(r"[；;]", str(value or default))
    visible = [normalize_api_names(item).strip() for item in values if item and not is_memory_output_label(item)]
    return "；".join(item for item in visible if item) or "来源待补充"


def escape(value: Any, default: str = "未知 / 待补充") -> str:
    if value is None or value == "":
        value = default
    return html_escape(normalize_api_names(value), quote=True)


def as_items(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]


def section(bundle: dict[str, Any], name: str) -> Any:
    sections = bundle.get("sections")
    if not isinstance(sections, dict):
        return {}
    return sections.get(name) or {}


def confidence_label(value: Any) -> str:
    labels = {
        "confirmed": "确认",
        "inferred": "推断",
        "unknown": "未知",
        "确认": "确认",
        "推断": "推断",
        "未知": "未知",
    }
    return labels.get(str(value or "未知"), "未知")


def confidence_class(value: Any) -> str:
    return {"确认": "badge--green", "推断": "badge--yellow", "未知": "badge--orange"}[confidence_label(value)]


def query_status_class(value: str) -> str:
    return {
        "已读取": "badge--green",
        "无数据": "badge--blue",
        "权限不足": "badge--red",
        "未触发查询": "badge--yellow",
        "查询失败": "badge--red",
    }[value]


def status_badge(value: Any) -> str:
    text = str(value or "未知")
    if text in {"已兑现", "完成", "支持", "低", "完整", "确认"}:
        class_name = "badge--green"
    elif text in {"逾期", "反对", "高", "不足", "严重"}:
        class_name = "badge--red"
    elif text in {"进行中", "部分兑现", "中", "部分", "推断"}:
        class_name = "badge--yellow"
    else:
        class_name = "badge--orange"
    return f'<span class="badge {class_name}">{escape(text)}</span>'


def qualitative_signal(status: Any, category: str) -> tuple[str, int, str]:
    raw = str(status or "未知")
    if category == "information":
        mapping = {
            "完整": ("完整", 100, "gauge--green"),
            "部分": ("部分", 60, "gauge--yellow"),
            "不足": ("不足", 25, "gauge--red"),
            "未知": ("未知", 0, "gauge--yellow"),
        }
    elif category == "relationship":
        mapping = {
            "升温": ("升温", 75, "gauge--green"),
            "稳定": ("稳定", 55, "gauge--yellow"),
            "降温": ("降温", 25, "gauge--red"),
            "未知": ("未知", 0, "gauge--yellow"),
        }
    else:
        mapping = {
            "高": ("高", 90, "gauge--red"),
            "中": ("中", 60, "gauge--yellow"),
            "低": ("低", 30, "gauge--green"),
            "未知": ("未知", 0, "gauge--yellow"),
        }
    return mapping.get(raw, mapping["未知"])


def relationship_temperature(value: Any) -> tuple[str, int]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "未知", 0
    if number < -5 or number > 5:
        return "未知", 0
    display = f"{number:+g}" if number else "0"
    return display, round((number + 5) * 10)


def render_summary_cards(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)][:6]
    if not normalized:
        normalized = [{"label": "信息状态", "value": "交接摘要待补充", "confidence": "未知"}]
    return "".join(
        '<div class="handover-summary-item">'
        f'<div class="handover-summary-item__label">{escape(item.get("label"))}</div>'
        f'<div class="handover-summary-item__value">{escape(item.get("value"))}</div>'
        f'<div class="handover-summary-item__confidence">置信度：{escape(confidence_label(item.get("confidence")))}</div>'
        "</div>"
        for item in normalized
    )


def render_context_facts(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        normalized = [{"label": "交接背景", "value": "未知，需原负责人补充"}]
    return "".join(
        '<div class="fact-row">'
        f'<div class="fact-row__label">{escape(item.get("label"))}</div>'
        f'<div class="fact-row__value">{escape(item.get("value"))}</div>'
        "</div>"
        for item in normalized
    )


def render_profile(items: Any, mobile: bool = False) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        normalized = [{"label": "客户画像", "value": "未知 / 待补充", "full_width": True}]
    output: list[str] = []
    for item in normalized:
        if mobile:
            output.append(
                '<div class="mobile-info-item">'
                f'<div class="mobile-info-label">{escape(item.get("label"))}</div>'
                f'<div class="mobile-info-value">{escape(item.get("value"))}</div>'
                "</div>"
            )
        else:
            full_class = " sidebar-info-item--full" if item.get("full_width") else ""
            output.append(
                f'<div class="sidebar-info-item{full_class}">'
                f'<div class="sidebar-info-item__label">{escape(item.get("label"))}</div>'
                f'<div class="sidebar-info-item__value">{escape(item.get("value"))}</div>'
                "</div>"
            )
    return "".join(output)


def role_class(role: Any) -> str:
    value = str(role or "Unknown").lower()
    if value == "coach":
        return "kp--coach"
    if value == "eb":
        return "kp--eb"
    if value in {"tb", "ux", "influencer"}:
        return "kp--tb"
    if value == "gatekeeper":
        return "kp--gatekeeper"
    return "kp-avatar"


def render_relationship_rows(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)][:10]
    if not normalized:
        normalized = [{"name": "关键人未知", "title": "待补充", "role": "Unknown", "temperature": None, "confidence": "未知"}]
    output: list[str] = []
    for item in normalized:
        name = str(item.get("name") or "未知")
        temperature, _ = relationship_temperature(item.get("temperature"))
        score = temperature if temperature != "未知" else str(item.get("attitude") or "未知")
        role = str(item.get("role") or "Unknown")
        note = item.get("contact_note") or item.get("evidence") or "联络注意待补充"
        output.append(
            '<div class="kp-row">'
            '<div class="kp-person">'
            f'<div class="{role_class(role)}">{escape(name[:1], "?")}</div>'
            '<div>'
            f'<div class="kp-name">{escape(name)} · {escape(item.get("title"), "职务未知")}</div>'
            f'<div class="kp-role">{escape(role)} · {escape(note)}</div>'
            "</div></div>"
            '<div class="kp-score">'
            f'{escape(score)} <span class="badge {confidence_class(item.get("confidence"))}">{escape(confidence_label(item.get("confidence")))}</span>'
            "</div></div>"
        )
    return "".join(output)


def render_commitments(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        normalized = [{"title": "暂无已确认承诺", "party": "未知", "due_date": "未知", "status": "未知", "action": "需原负责人核对"}]
    output: list[str] = []
    for item in normalized:
        meta = f'{escape(item.get("party"), "承诺方未知")} · 截止 {escape(item.get("due_date"), "未知")} · {escape(item.get("action"), "接手处理待补充")}'
        output.append(
            '<div class="commitment-row"><div>'
            f'<div class="commitment-row__title">{escape(item.get("title"))}</div>'
            f'<div class="commitment-row__meta">{meta}</div>'
            f'</div>{status_badge(item.get("status"))}</div>'
        )
    return "".join(output)


def render_timeline(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        normalized = [{"date": "未知", "title": "暂无关键博弈记录", "description": "需原负责人补充历史转折点", "confidence": "未知"}]
    output: list[str] = []
    for item in normalized:
        confidence = confidence_label(item.get("confidence"))
        dot_class = {"确认": "timeline-item__dot--green", "推断": "timeline-item__dot--orange", "未知": ""}[confidence]
        impact = item.get("impact")
        description = escape(item.get("description"))
        if impact:
            description += f'；交接影响：{escape(impact)}'
        output.append(
            '<div class="timeline-item">'
            f'<div class="timeline-marker"><div class="timeline-item__dot {dot_class}"></div></div>'
            '<div>'
            f'<div class="timeline-item__date">{escape(item.get("date"))} · {escape(confidence)}</div>'
            f'<div class="timeline-item__title">{escape(item.get("title"))}</div>'
            f'<div class="timeline-item__desc">{description}</div>'
            "</div></div>"
        )
    return "".join(output)


def render_competition_rows(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        return '<tr><td colspan="5">暂无已确认竞品记录 / 待核对</td></tr>'
    output: list[str] = []
    for item in normalized:
        result = escape(item.get("result"))
        result += f' <span class="badge {confidence_class(item.get("confidence"))}">{escape(confidence_label(item.get("confidence")))}</span>'
        output.append(
            "<tr>"
            f'<td>{escape(item.get("name"))}</td>'
            f'<td>{escape(item.get("entered_at"))}</td>'
            f'<td>{escape(item.get("stage"))}</td>'
            f'<td>{escape(item.get("strategy"))}</td>'
            f'<td>{result}</td>'
            "</tr>"
        )
    return "".join(output)


def render_mobile_competition(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        normalized = [{"name": "竞品信息待核对", "stage": "未读取", "result": "未知"}]
    return "".join(
        '<div class="mobile-compact-row"><div>'
        f'<div class="mobile-title">{escape(item.get("name"))}</div>'
        f'<div class="mobile-desc">{escape(item.get("stage"))} · {escape(item.get("strategy") or item.get("result"))}</div>'
        f'</div>{status_badge(confidence_label(item.get("confidence")))}</div>'
        for item in normalized
    )


def render_risks(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        normalized = [{"severity": "未知", "title": "暂无已确认风险", "description": "历史关系与互动信息仍需核对", "action": "接手后补查", "confidence": "未知"}]
    output: list[str] = []
    for item in normalized:
        severe = str(item.get("severity") or "未知") in {"高", "严重"}
        dot_class = " risk-row__dot--red" if severe else ""
        output.append(
            '<div class="risk-row">'
            f'<div class="risk-row__dot{dot_class}"></div><div>'
            f'<div class="risk-row__title">{escape(item.get("title"))} · {escape(item.get("severity"), "未知")}</div>'
            f'<div class="risk-row__desc">{escape(item.get("description"))}；接手处理：{escape(item.get("action"))}；置信度：{escape(confidence_label(item.get("confidence")))}</div>'
            "</div></div>"
        )
    return "".join(output)


def render_action_rows(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        normalized = [{"priority": "高", "action": "补齐交接关键信息", "why": "避免关系和承诺断档", "owner": "接手人", "completion_standard": "完成原负责人核对"}]
    return "".join(
        "<tr>"
        f'<td>{escape(item.get("priority"))}</td>'
        f'<td>{escape(item.get("action"))}<div class="mobile-desc">{escape(item.get("why"), "原因待补充")}</div></td>'
        f'<td>{escape(item.get("owner"))}</td>'
        f'<td>{escape(item.get("completion_standard"))}</td>'
        "</tr>"
        for item in normalized
    )


def render_gaps(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        normalized = [{"title": "暂无已确认缺口", "impact": "仍需接手后持续核对", "action": "核对历史关系、互动与 CRM 查询状态"}]
    return "".join(
        '<div class="gap-row">'
        f'<div class="gap-row__title">{escape(item.get("title"))}</div>'
        f'<div class="gap-row__desc">影响：{escape(item.get("impact"))}；补齐方式：{escape(item.get("action"))}</div>'
        "</div>"
        for item in normalized
    )


def render_financial_section(data: Any, enabled: bool) -> tuple[str, str]:
    if not enabled:
        return "", " handover-grid--single"
    values = data if isinstance(data, dict) else {}
    items = [item for item in as_items(values.get("items")) if isinstance(item, dict)]
    if not items:
        items = [{"label": "财务与健康状态", "value": "未知 / 待补充", "note": "权限不足或未读取时不得写成无风险"}]
    item_html = "".join(
        '<div class="health-item">'
        f'<div class="health-item__label">{escape(item.get("label"))}</div>'
        f'<div class="health-item__value">{escape(item.get("value"))}</div>'
        f'<div class="health-item__note">{escape(item.get("note"))}</div>'
        "</div>"
        for item in items
    )
    return (
        '<div class="card" id="history-financial">'
        '<div class="card-header"><span class="card-header__title">历史合作、财务与客户健康</span>'
        f'<span class="badge">{escape(values.get("scope_label"), "完整口径")}</span></div>'
        f'<div class="card-body"><div class="health-grid">{item_html}</div></div></div>',
        "",
    )


def compact_lines(items: list[dict[str, Any]], title_key: str, detail_keys: Iterable[str]) -> str:
    if not items:
        return '<span class="callout-line">未知 / 待核对</span>'
    lines: list[str] = []
    for item in items[:5]:
        details = [escape(item.get(key), "") for key in detail_keys if item.get(key) not in (None, "")]
        suffix = "；" + "；".join(details) if details else ""
        lines.append(f'<span class="callout-line"><strong>{escape(item.get(title_key))}</strong>{suffix}</span>')
    return "".join(lines)


def render_handover_notes(explicit: Any, sections: dict[str, Any], full_enabled: bool) -> str:
    normalized = [item for item in as_items(explicit) if isinstance(item, dict)]
    if normalized:
        return "".join(
            '<div class="handover-card">'
            f'<div class="handover-card__label">{escape(item.get("label"))}</div>'
            f'<div class="handover-card__content">{escape(item.get("content"))}</div>'
            "</div>"
            for item in normalized
        )

    commitments = [item for item in as_items(sections.get("commitments")) if isinstance(item, dict)]
    risks = [item for item in as_items(sections.get("risks")) if isinstance(item, dict)]
    actions = [item for item in as_items(sections.get("first_week_actions")) if isinstance(item, dict)]
    gaps = [item for item in as_items(sections.get("handover_gaps")) if isinstance(item, dict)]
    cards = [
        ("待兑现承诺", compact_lines(commitments, "title", ("status", "action"))),
        ("风险与不能踩的坑", compact_lines(risks, "title", ("description", "action"))),
        ("第一周动作", compact_lines(actions, "action", ("owner", "completion_standard"))),
        ("交接缺口", compact_lines(gaps, "title", ("impact", "action"))),
    ]
    if full_enabled:
        financial = sections.get("financial_health") if isinstance(sections.get("financial_health"), dict) else {}
        financial_items = [item for item in as_items(financial.get("items")) if isinstance(item, dict)]
        cards.append(("财务与客户健康", compact_lines(financial_items, "label", ("value", "note"))))
    return "".join(
        '<div class="handover-card">'
        f'<div class="handover-card__label">{escape(label)}</div>'
        f'<div class="handover-card__content">{content}</div>'
        "</div>"
        for label, content in cards
    )


def render_coverage(value: Any) -> str:
    raw = value if isinstance(value, dict) else {}
    normalized: dict[str, str] = {}
    for raw_label, raw_status in raw.items():
        if is_memory_output_label(raw_label):
            continue
        label = normalize_api_names(raw_label)
        status = str(raw_status or "查询失败")
        normalized[label] = status if status in VALID_QUERY_STATUSES else "查询失败"
    labels = list(DEFAULT_COVERAGE_LABELS)
    labels.extend(label for label in normalized if label not in labels)
    tags = [
        f'<span class="badge {query_status_class(normalized.get(label, "未触发查询"))}">{escape(label)}：{escape(normalized.get(label, "未触发查询"))}</span>'
        for label in labels
    ]
    return '<div class="quality-tags">' + "".join(tags) + "</div>"


def build_fragments(bundle: dict[str, Any], preview: bool) -> dict[str, str]:
    metadata = bundle.get("metadata") if isinstance(bundle.get("metadata"), dict) else {}
    customer_name = str(metadata.get("customer_name") or "").strip()
    if not customer_name:
        raise ValueError("metadata.customer_name 必填")
    mode = str(metadata.get("mode") or "standard").lower()
    if mode not in VALID_MODES:
        raise ValueError("metadata.mode 必须是 standard 或 full")

    alert = bundle.get("alert") if isinstance(bundle.get("alert"), dict) else {}
    signals = bundle.get("quality_signals") if isinstance(bundle.get("quality_signals"), dict) else {}
    information = signals.get("information") if isinstance(signals.get("information"), dict) else {}
    relationship_signal = signals.get("relationship") if isinstance(signals.get("relationship"), dict) else {}
    competition_signal = signals.get("competition") if isinstance(signals.get("competition"), dict) else {}
    info_display, info_pct, info_class = qualitative_signal(information.get("status") or metadata.get("memory_status"), "information")
    rel_display, rel_pct, rel_class = qualitative_signal(relationship_signal.get("status"), "relationship")
    comp_display, comp_pct, comp_class = qualitative_signal(competition_signal.get("status"), "competition")

    summary = bundle.get("executive_summary") if isinstance(bundle.get("executive_summary"), dict) else {}
    sections = bundle.get("sections") if isinstance(bundle.get("sections"), dict) else {}
    handover_gaps = [item for item in as_items(sections.get("handover_gaps")) if isinstance(item, dict)]
    if memory_information_is_incomplete(metadata) and not any("关键历史与关系信息" in str(item) for item in handover_gaps):
        handover_gaps.append(
            {
                "title": "关键历史与关系信息待补充",
                "impact": "接手人可能遗漏关键人物背景、历史承诺或沟通敏感点",
                "action": "由原负责人补齐关键人物、承诺和关系变化事实",
            }
        )
    sections = dict(sections)
    sections["handover_gaps"] = handover_gaps
    relationship = sections.get("relationship") if isinstance(sections.get("relationship"), dict) else {}
    competition = sections.get("competition") if isinstance(sections.get("competition"), dict) else {}
    profile = sections.get("account_profile")
    relationship_rows = render_relationship_rows(relationship.get("key_people"))
    context_facts = render_context_facts(sections.get("handover_context"))
    timeline_items = render_timeline(sections.get("timeline"))
    competition_items = competition.get("items")
    overall_score, overall_pct = relationship_temperature(relationship.get("overall_temperature"))
    financial_section, financial_grid_class = render_financial_section(sections.get("financial_health"), mode == "full")

    references = bundle.get("references") if isinstance(bundle.get("references"), dict) else {}
    source_values = references.get("sources")
    source_text = render_source_text(source_values, "CRM 客户、商机、联系人和跟进记录；原负责人交接信息；必要外部情报")

    handover_status = metadata.get("handover_status") or "待交接"
    customer_state = metadata.get("customer_state") or metadata.get("opportunity_status") or "客户状态待确认"
    alert_title = alert.get("title") or "交接关键信息待确认"
    alert_body = alert.get("body") or "请优先核对历史承诺、关键关系和未完成事项，避免接手后出现沟通断档。"
    alert_action = alert.get("action") or "第一动作：与原负责人完成口头交接。"
    handover_score_label = metadata.get("handover_score_label") or handover_status

    return {
        "report_mode": mode,
        "preview_mode": "true" if preview else "false",
        "customer_name": escape(customer_name),
        "handover_status": escape(handover_status),
        "opportunity_status": escape(customer_state),
        "opportunity_amount": escape(metadata.get("opportunity_amount"), "金额未知"),
        "new_owner": escape(metadata.get("new_owner")),
        "industry_or_segment": escape(metadata.get("industry_or_segment")),
        "handover_reason": escape(metadata.get("handover_reason")),
        "coach_summary": escape(metadata.get("coach_summary"), "关键关系待确认"),
        "original_owner": escape(metadata.get("original_owner")),
        "handover_score_label": escape(handover_score_label),
        "alert_title": escape(alert_title),
        "alert_body": escape(alert_body),
        "alert_action": escape(alert_action),
        "information_signal_class": info_class,
        "information_completeness_score": escape(info_display),
        "information_completeness_pct": str(info_pct),
        "information_completeness_note": escape(information.get("note"), "根据已读取的客户、商机、互动和历史信息判断"),
        "relationship_signal_class": rel_class,
        "relationship_temperature_score": escape(rel_display),
        "relationship_temperature_pct": str(rel_pct),
        "relationship_temperature_note": escape(relationship_signal.get("note"), "关系趋势需要具体互动证据"),
        "competition_signal_class": comp_class,
        "competitive_risk_score": escape(comp_display),
        "competitive_risk_pct": str(comp_pct),
        "competitive_risk_note": escape(competition_signal.get("note"), "未读取竞品信息时保持未知"),
        "one_sentence_conclusion": escape(summary.get("one_sentence_conclusion"), "交接结论待补充"),
        "handover_summary_cards": render_summary_cards(summary.get("items")),
        "handover_urgency": escape(metadata.get("handover_urgency"), "紧急度未知"),
        "handover_context_facts": context_facts,
        "relationship_overall_label": escape(relationship.get("overall_label"), "关系未知"),
        "relationship_overall_score": escape(overall_score),
        "relationship_overall_pct": str(overall_pct),
        "relationship_people_rows": relationship_rows,
        "account_profile_items": render_profile(profile),
        "commitment_rows": render_commitments(sections.get("commitments")),
        "timeline_items": timeline_items,
        "competitive_status_label": escape(competition.get("status_label"), "竞争状态未知"),
        "competitive_rows": render_competition_rows(competition_items),
        "competitive_note": escape(competition.get("note"), "竞品信息不足时需接手后核对"),
        "risk_rows": render_risks(sections.get("risks")),
        "first_week_action_rows": render_action_rows(sections.get("first_week_actions")),
        "financial_grid_class": financial_grid_class,
        "financial_section": financial_section,
        "handover_gap_rows": render_gaps(handover_gaps),
        "mobile_handover_context_facts": context_facts,
        "mobile_account_profile_items": render_profile(profile, mobile=True),
        "mobile_account_profile_note": escape(sections.get("account_profile_note"), "客户画像与桌面版使用同一组事实"),
        "mobile_relationship_rows": relationship_rows,
        "mobile_timeline_items": timeline_items,
        "mobile_competitive_rows": render_mobile_competition(competition_items),
        "handover_note_cards": render_handover_notes(sections.get("handover_notes"), sections, mode == "full"),
        "data_coverage": render_coverage(bundle.get("data_coverage")),
        "reference_note": escape(source_text),
        "confidence_note": escape(references.get("confidence_note"), "确认：有直接证据；推断：有行为证据；未知：当前证据不足。"),
        "data_updated_at": escape(metadata.get("data_updated_at") or metadata.get("handover_date") or date.today().isoformat()),
    }


def inline_css(template_text: str, css_text: str) -> str:
    pattern = re.compile(r'\s*<link\s+rel="stylesheet"\s+href="\.\./styles/handover\.css"\s*>')
    if not pattern.search(template_text):
        raise ValueError("正式模板缺少可内联的 handover.css 引用")
    replacement = "\n  <style>\n" + css_text + "\n  </style>"
    return pattern.sub(lambda _: replacement, template_text, count=1)


def render(template_text: str, css_text: str, fragments: dict[str, str]) -> str:
    template_text = inline_css(template_text, css_text)
    pattern = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
    unknown = sorted({name for name in pattern.findall(template_text) if name not in fragments})
    if unknown:
        raise ValueError("模板包含未定义占位符：" + "、".join(unknown))
    rendered = pattern.sub(lambda match: fragments[match.group(1)], template_text)
    if pattern.search(rendered):
        raise ValueError("渲染后仍存在模板占位符")
    return rendered


def mock_bundle(mode: str) -> dict[str, Any]:
    return {
        "metadata": {
            "customer_name": "示例区域农业服务管理中心",
            "mode": mode,
            "handover_date": "2026-07-13",
            "data_updated_at": "2026-07-13 17:30",
            "original_owner": "原负责人 王经理",
            "new_owner": "接手人 李经理",
            "handover_status": "交接中",
            "handover_score_label": "高风险交接：跟进中断 51 天，竞品在场，决策链尚未完整",
            "handover_reason": "原负责人岗位调整",
            "handover_urgency": "高",
            "memory_status": "部分",
            "customer_state": "未成交，商机处于需求确认阶段，跟进已中断 51 天",
            "opportunity_amount": "6,800,000.00 元",
            "industry_or_segment": "高端制造 · 集团型客户",
            "coach_summary": "运营总监周总 · 支持",
        },
        "alert": {
            "title": "先兑现历史承诺，再推进新方案",
            "body": "原负责人承诺的接口边界说明已逾期，客户技术负责人已两次追问。",
            "action": "第一动作：原负责人、接手人和售前共同确认交付时间。",
        },
        "quality_signals": {
            "information": {"status": "部分", "note": "客户、商机和联系人已读取，会议与回款仍需补查"},
            "relationship": {"status": "稳定", "note": "Coach 保持支持，最终预算人尚未覆盖"},
            "competition": {"status": "中", "note": "已确认一家具名竞品，报价和方案未知"},
        },
        "executive_summary": {
            "one_sentence_conclusion": "客户仍在积极评估，但接口承诺逾期和预算决策人缺失是接手后的两个最高优先级。",
            "items": [
                {"label": "当前客户状态", "value": "方案评估中，预计八月进入商务阶段", "confidence": "确认"},
                {"label": "交接原因", "value": "原负责人岗位调整", "confidence": "确认"},
                {"label": "最大风险", "value": "接口边界说明逾期", "confidence": "确认"},
                {"label": "最关键关系", "value": "运营总监周总是当前 Coach", "confidence": "推断"},
                {"label": "待兑现承诺", "value": "本周补齐接口与数据安全说明", "confidence": "确认"},
                {"label": "第一周重点", "value": "完成引荐、兑现承诺并补齐预算链", "confidence": "确认"},
            ],
        },
        "sections": {
            "handover_context": [
                {"label": "交接背景", "value": "原负责人岗位调整，客户进入方案评估关键期"},
                {"label": "当前状态", "value": "POC 已通过，预算审批链尚未完全确认"},
                {"label": "交接要求", "value": "原负责人需完成 Coach 和技术负责人的当面引荐"},
            ],
            "account_profile": [
                {"label": "行业", "value": "高端装备制造"},
                {"label": "规模", "value": "集团型客户，约 2,000 人"},
                {"label": "主要项目", "value": "集团 CRM 升级"},
                {"label": "当前阶段", "value": "方案评估"},
                {"label": "客户目标", "value": "统一客户数据与销售预测", "full_width": True},
            ],
            "account_profile_note": "客户基础事实已确认，营收和集团组织范围仍需核对。",
            "relationship": {
                "overall_label": "信任",
                "overall_temperature": 3,
                "key_people": [
                    {"name": "周总", "title": "运营总监", "role": "Coach", "temperature": 3, "attitude": "支持", "contact_note": "需要原负责人当面引荐", "confidence": "确认"},
                    {"name": "陈总", "title": "信息化负责人", "role": "TB", "temperature": 1, "attitude": "中立", "contact_note": "关注接口和数据安全", "confidence": "确认"},
                    {"name": "刘总", "title": "财务副总", "role": "EB", "temperature": None, "attitude": "未知", "contact_note": "尚未建立直接联系", "confidence": "推断"},
                ],
            },
            "commitments": [
                {"title": "接口边界说明", "party": "我方", "due_date": "2026-07-10", "status": "逾期", "action": "售前三天内补齐", "confidence": "确认"},
                {"title": "提供预算审批节点", "party": "客户", "due_date": "2026-07-18", "status": "进行中", "action": "由周总协助确认", "confidence": "推断"},
            ],
            "timeline": [
                {"date": "2026-05-20", "title": "客户启动 CRM 升级评估", "description": "运营部门牵头，周总成为主要推动者", "impact": "形成稳定 Coach", "confidence": "确认"},
                {"date": "2026-06-26", "title": "POC 通过", "description": "业务侧反馈正向，技术侧要求补接口说明", "impact": "项目进入方案评估", "confidence": "确认"},
                {"date": "2026-07-10", "title": "接口说明承诺逾期", "description": "客户技术负责人再次催问", "impact": "接手后必须优先修复信任", "confidence": "确认"},
            ],
            "competition": {
                "status_label": "存在明确竞品",
                "note": "不得把未读取的竞品报价写成我方优势。",
                "items": [
                    {"name": "竞品 A", "entered_at": "2026-06", "stage": "方案比较", "strategy": "用集团实践和接口边界回应", "result": "未决", "confidence": "确认"}
                ],
            },
            "risks": [
                {"severity": "高", "title": "历史承诺逾期", "description": "接口说明尚未交付", "action": "先兑现再谈新增范围", "confidence": "确认"},
                {"severity": "中", "title": "预算决策链缺口", "description": "财务副总态度未知", "action": "通过周总确认进入路径", "confidence": "推断"},
            ],
            "first_week_actions": [
                {"priority": "高", "action": "完成关键人当面引荐", "why": "避免关系断档", "owner": "原负责人/接手人", "completion_standard": "周总和陈总确认新接口人"},
                {"priority": "高", "action": "交付接口边界说明", "why": "修复逾期承诺", "owner": "售前", "completion_standard": "客户技术负责人书面确认"},
                {"priority": "中", "action": "补齐预算审批链", "why": "决定商务节奏", "owner": "接手人", "completion_standard": "确认最终拍板人与审批日期"},
            ],
            "handover_gaps": [
                {"title": "预算拍板人态度未知", "impact": "无法判断商务推进窗口", "action": "由周总引荐或核对审批流程"},
                {"title": "回款记录未读取", "impact": "历史合作风险无法确认", "action": "full 模式读取订单与回款"},
            ],
            "financial_health": {
                "scope_label": "完整财务口径",
                "items": [
                    {"label": "历史订单", "value": "2 笔 · 180 万元", "note": "均已完成交付"},
                    {"label": "应收金额", "value": "20 万元", "note": "预计 2026-07-31 回款"},
                    {"label": "客户健康", "value": "中", "note": "接口承诺逾期需要优先处理"},
                    {"label": "增购信号", "value": "存在", "note": "前提是完成当前项目交付"},
                ],
            },
        },
        "data_coverage": {
            "客户": "已读取",
            "商机": "已读取",
            "联系人": "已读取",
            "跟进记录": "已读取",
            "待办/任务": "已读取",
            "需求/问题": "已读取",
            "会议": "权限不足",
            "竞品明细": "已读取",
            "合同/订单/回款": "已读取" if mode == "full" else "未触发查询",
            "客户记忆": "已读取",
            "外部情报": "未触发查询",
        },
        "references": {
            "sources": ["CRM 客户、商机、联系人和跟进记录", "客户记忆", "原负责人交接信息", "必要外部情报"],
            "confidence_note": "确认：有 CRM、客户原话或明确事件；推断：有行为证据；未知：当前证据不足。",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="按固定模板渲染团队交接简报")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="handover_facts_bundle JSON 文件")
    source.add_argument("--mock", action="store_true", help="使用内置模拟数据生成预览")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="standard", help="仅在 --mock 时设置预览模式")
    parser.add_argument("--output", type=Path, required=True, help="输出 HTML 文件")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="正式 HTML 模板")
    parser.add_argument("--css", type=Path, default=DEFAULT_CSS, help="需要内联的 CSS 文件")
    parser.add_argument("--forbid-text", action="append", default=[], help="禁止残留的旧客户或样例文字，可重复传入")
    args = parser.parse_args()

    if args.mock:
        bundle = mock_bundle(args.mode)
    else:
        try:
            bundle = json.loads(args.input.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: 无法读取事实包：{exc}", file=sys.stderr)
            return 2
        if not isinstance(bundle, dict):
            print("ERROR: handover_facts_bundle 顶层必须是 JSON 对象", file=sys.stderr)
            return 2

    try:
        template_text = args.template.read_text(encoding="utf-8")
        css_text = args.css.read_text(encoding="utf-8")
        rendered = render(template_text, css_text, build_fragments(bundle, preview=args.mock))
    except (OSError, ValueError) as exc:
        print(f"ERROR: 渲染失败：{exc}", file=sys.stderr)
        return 2

    errors = validate_html(rendered, args.forbid_text)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Rendered and validated: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
