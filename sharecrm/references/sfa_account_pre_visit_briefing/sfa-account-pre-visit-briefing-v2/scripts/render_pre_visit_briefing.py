#!/usr/bin/env python3
"""Render a pre-visit customer briefing from a structured facts bundle."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from validate_pre_visit_briefing import validate_html


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "templates" / "visit.html"
VALID_MODES = {"lite", "normal", "full"}
VALID_QUERY_STATUSES = {"已读取", "无数据", "权限不足", "未触发查询", "查询失败"}
DEFAULT_COVERAGE_LABELS = (
    "客户",
    "商机",
    "联系人",
    "跟进记录",
    "日程",
    "需求/问题",
    "会议",
    "待办/任务",
    "现场拜访",
    "竞品明细",
    "合同",
    "订单/回款",
    "外部情报",
)
API_LABELS = {
    "AccountObj": "客户",
    "NewOpportunityObj": "商机",
    "ContactObj": "联系人",
    "ActiveRecordObj": "跟进记录",
    "ActivityTodoObj": "待办",
    "MethodologyTaskObj": "任务",
    "RequirementObj": "需求",
    "ActivityQuestionObj": "互动问题",
    "ScheduleObj": "日程",
    "AIMeetingObj": "会议",
    "AIMeetingChunkObj": "会议纪要",
    "CheckinsObj": "现场拜访",
    "CompetitiveLinesObj": "竞品明细",
    "ContractObj": "合同",
    "SalesOrderObj": "销售订单",
    "PaymentObj": "回款",
    "CasesObj": "服务工单",
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
    (r"\bE1\b", "客户直接表达"),
    (r"\bE2\b", "客户行为推断"),
    (r"\bE3\b", "公开线索推断"),
    (r"\bE4\b", "行业通用假设"),
    (r"\bfull\s*模式", "完整模式"),
)
COMMITMENT_STATUS_LABELS = {
    "kept": "已兑现",
    "partial": "部分兑现",
    "overdue": "逾期",
    "not_applicable": "无",
    "unknown": "未知",
}
RELATIONSHIP_CHANGE_LABELS = {
    "warming": "升温",
    "cooling": "降温",
    "stable": "稳定",
    "unknown": "未知",
}
CONFIDENCE_LABELS = {
    "confirmed": "确认",
    "inferred": "推断",
    "unknown": "未知",
}
EVENT_TYPE_LABELS = {
    "interaction": "互动",
    "commitment": "承诺",
    "stage_change": "阶段变化",
    "competitor": "竞品",
    "budget": "预算",
    "delivery": "交付",
    "payment": "回款",
    "relationship": "关系",
    "other": "其他",
}


def nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def normalize_api_names(value: Any) -> str:
    text = str(value)
    for api_name, business_label in API_LABELS.items():
        text = re.sub(rf"\b{re.escape(api_name)}\b", business_label, text)
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
    return html.escape(normalize_api_names(value), quote=True)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def localized(value: Any, labels: dict[str, str], default: str = "未知") -> str:
    raw = str(value or "").strip()
    return labels.get(raw.lower(), raw or default)


def numeric_score(value: Any) -> tuple[int, str]:
    try:
        score = max(0, min(100, round(float(value))))
        return score, str(score)
    except (TypeError, ValueError):
        return 0, "--"


def readiness_grade(readiness: dict[str, Any], score: int) -> tuple[str, str]:
    raw_grade = readiness.get("readiness_grade")
    label = raw_grade.get("label") if isinstance(raw_grade, dict) else raw_grade
    color = raw_grade.get("color") if isinstance(raw_grade, dict) else ""
    if not label:
        if score >= 80:
            label, color = "就绪", "green"
        elif score >= 60:
            label, color = "准备中", "yellow"
        elif score >= 40:
            label, color = "不足", "orange"
        else:
            label, color = "危险", "red"
    css_class = "status-pill--success" if color == "green" else "status-pill--danger" if color == "red" else "status-pill--warn"
    return str(label), css_class


def meeting_recommendation(readiness: dict[str, Any], score: int) -> str:
    if readiness.get("meeting_recommendation"):
        return str(readiness["meeting_recommendation"])
    if score >= 80:
        return "可以争取明确承诺"
    if score >= 60:
        return "可以推进，但先补最大缺口"
    if score >= 40:
        return "缩小目标，优先验证"
    return "建议延期或先补研究"


def render_risks(items: Any, mode: str) -> tuple[str, str]:
    limit = 1 if mode == "lite" else 3
    normalized = [item for item in as_list(items) if isinstance(item, dict)][:limit]
    if not normalized:
        normalized = [{"title": "当前最高风险待确认", "response": "开场先重建上下文并验证最大缺口"}]
    output: list[str] = []
    for index, item in enumerate(normalized, start=1):
        output.append(
            '<div class="alert-item">'
            f"<b>{index}</b>"
            "<div>"
            f'<strong>{escape(item.get("title") or item.get("risk"))}</strong>'
            f'<p>{escape(item.get("response") or item.get("action"), "现场确认事实并收敛下一步")}</p>'
            "</div></div>"
        )
    heading = normalized[0].get("heading") or normalized[0].get("title") or normalized[0].get("risk") or "今天先守住最高风险"
    return "".join(output), str(heading)


def render_actions(items: Any, mode: str) -> tuple[str, str]:
    limit = 1 if mode == "lite" else 3
    normalized = [item for item in as_list(items) if isinstance(item, dict)][:limit]
    if not normalized:
        normalized = [{"priority": "P0", "title": "重建会议上下文", "detail": "问客户：今天最希望先解决哪个问题？"}]
    output: list[str] = []
    for index, item in enumerate(normalized):
        priority = item.get("priority") or f"P{index}"
        hot_class = " action-step--hot" if str(priority).upper() == "P0" else ""
        output.append(
            f'<div class="action-step{hot_class}">'
            f'<span>{escape(priority)}</span>'
            "<div>"
            f'<strong>{escape(item.get("title") or item.get("action"))}</strong>'
            f'<p>{escape(item.get("detail") or item.get("question"), "现场完成一个可验证动作")}</p>'
            "</div></div>"
        )
    return "".join(output), f"{len(normalized)} 项行动"


def avatar_class(role: Any) -> str:
    value = str(role or "").lower()
    if "coach" in value or "教练" in value:
        return "avatar--coach"
    if "eb" in value or "经济决策" in value:
        return "avatar--eb"
    if "tb" in value or "技术" in value:
        return "avatar--tb"
    if "gate" in value or "守门" in value or "阻碍" in value:
        return "avatar--gate"
    return ""


def render_people(items: Any) -> str:
    normalized = [item for item in as_list(items) if isinstance(item, dict)][:6]
    if not normalized:
        normalized = [{"name": "关键决策人未知", "title": "待确认", "role": "EB 候选", "stance": "未知", "tactic": "现场识别最终拍板人与审批链"}]
    output: list[str] = []
    for item in normalized:
        name = str(item.get("name") or "未知")
        avatar = name[0] if name else "?"
        role = item.get("role") or "角色待确认"
        stance = item.get("stance") or item.get("attitude") or "未知"
        title = item.get("title") or "职务待确认"
        output.append(
            '<article class="person-card">'
            f'<span class="avatar {avatar_class(role)}">{escape(avatar, "?")}</span>'
            "<div>"
            '<div class="person-title">'
            f"<strong>{escape(name)}</strong>"
            f"<span>{escape(role)} · {escape(title)}</span>"
            "</div>"
            f'<p>当前立场：{escape(stance)}。今天打法：{escape(item.get("tactic"))}</p>'
            "</div></article>"
        )
    return "".join(output)


def render_timeline_summary(items: Any, mode: str) -> str:
    limit = 6 if mode == "full" else 4
    normalized = [item for item in as_list(items) if isinstance(item, dict)][:limit]
    if not normalized:
        normalized = [{"date": "今天", "event": "历史互动不足", "impact": "本次会议先重建上下文并确认关键承诺"}]
    return "".join(
        '<div class="timeline-row">'
        f'<span>{escape(item.get("date") or item.get("time"))}</span>'
        f'<strong>{escape(item.get("event") or item.get("content"))}</strong>'
        f'<p>{escape(item.get("impact") or item.get("visit_impact") or item.get("today_impact"), "本次拜访需现场验证其影响")}</p>'
        "</div>"
        for item in normalized
    )


def render_timeline_detail(items: Any) -> str:
    normalized = [item for item in as_list(items) if isinstance(item, dict)][:12]
    if not normalized:
        normalized = [{
            "date": "未知",
            "event_type": "other",
            "event": "关键博弈明细待补充",
            "our_action": "未知",
            "customer_reaction": "未知",
            "commitment_status": "unknown",
            "relationship_change": "unknown",
            "visit_impact": "本次拜访先核对最近一次有效沟通、关键承诺和关系变化",
            "confidence": "unknown",
        }]
    output: list[str] = []
    for item in normalized:
        event_type = localized(item.get("event_type"), EVENT_TYPE_LABELS, "其他")
        confidence = localized(item.get("confidence"), CONFIDENCE_LABELS)
        commitment = localized(item.get("commitment_status"), COMMITMENT_STATUS_LABELS)
        relationship = localized(item.get("relationship_change"), RELATIONSHIP_CHANGE_LABELS)
        output.append(
            '<article class="timeline-detail-row">'
            '<div class="timeline-detail-meta">'
            f'<strong>{escape(item.get("date") or item.get("time"))}</strong>'
            f'<span>{escape(event_type)} · {escape(confidence)}</span>'
            "</div>"
            '<div class="timeline-detail-content">'
            f'<strong>{escape(item.get("event") or item.get("content"))}</strong>'
            '<div class="timeline-detail-fields">'
            f'<div class="timeline-detail-field"><span>我方动作</span><p>{escape(item.get("our_action"))}</p></div>'
            f'<div class="timeline-detail-field"><span>客户反应</span><p>{escape(item.get("customer_reaction"))}</p></div>'
            f'<div class="timeline-detail-field"><span>承诺状态</span><p>{escape(commitment)}</p></div>'
            f'<div class="timeline-detail-field"><span>关系变化</span><p>{escape(relationship)}</p></div>'
            f'<div class="timeline-detail-field timeline-detail-field--wide"><span>对本次拜访的影响</span><p>{escape(item.get("visit_impact") or item.get("impact") or item.get("today_impact"), "本次拜访需现场验证其影响")}</p></div>'
            "</div></div></article>"
        )
    return "".join(output)


def render_timeline_notes(timeline_data: dict[str, Any]) -> str:
    turning_points = [item for item in as_list(timeline_data.get("turning_points")) if isinstance(item, dict)][:5]
    timeline_gaps = as_list(timeline_data.get("timeline_gaps"))[:5]
    if not turning_points and not timeline_gaps:
        return ""
    parts: list[str] = []
    if turning_points:
        items = "".join(
            f'<li><strong>{escape(item.get("date"))}：</strong>{escape(item.get("turning_point") or item.get("event"))}；'
            f'{escape(item.get("visit_note") or item.get("reason"), "本次拜访需确认其影响")}</li>'
            for item in turning_points
        )
        parts.append(f'<section class="timeline-note"><h3>关键转折点</h3><ul>{items}</ul></section>')
    if timeline_gaps:
        items = "".join(
            f'<li>{escape(item.get("gap") if isinstance(item, dict) else item)}</li>'
            for item in timeline_gaps
        )
        parts.append(f'<section class="timeline-note"><h3>时间线缺口</h3><ul>{items}</ul></section>')
    return '<div class="timeline-notes">' + "".join(parts) + "</div>"


def render_timeline(timeline: Any, mode: str) -> str:
    timeline_data = timeline if isinstance(timeline, dict) else {"items": as_list(timeline)}
    legacy_items = timeline_data.get("items")
    summary_items = timeline_data.get("summary_items") or legacy_items or timeline_data.get("detail_items")
    detail_items = timeline_data.get("detail_items") or legacy_items or summary_items
    time_range = timeline_data.get("time_range") or "关键事件范围待确认"
    return (
        '<div class="timeline-toolbar">'
        f'<span class="timeline-range">范围：{escape(time_range)}</span>'
        '<div class="segmented-control" role="group" aria-label="博弈编年视图">'
        '<button class="timeline-view-button is-active" type="button" data-timeline-view="summary" aria-pressed="true">摘要</button>'
        '<button class="timeline-view-button" type="button" data-timeline-view="detail" aria-pressed="false">明细</button>'
        "</div></div>"
        f'<div class="timeline-view timeline" id="timeline-summary-view" data-view="summary">{render_timeline_summary(summary_items, mode)}</div>'
        f'<div class="timeline-view timeline-detail" id="timeline-detail-view" data-view="detail" hidden>{render_timeline_detail(detail_items)}{render_timeline_notes(timeline_data)}</div>'
    )


def render_post_visit_actions(items: Any, mode: str) -> str:
    limit = 1 if mode == "lite" else 5
    normalized = [item for item in as_list(items) if isinstance(item, dict)][:limit]
    if not normalized:
        normalized = [{
            "priority": "P0",
            "action": "记录会议结论与双方承诺",
            "owner": "客户经理",
            "due": "会后30分钟内",
            "trigger": "拜访结束",
            "completion_standard": "跟进记录包含责任人、承诺和下一步日期",
        }]
    output: list[str] = []
    for index, item in enumerate(normalized, start=1):
        action = item.get("action") or item.get("title")
        output.append(
            '<label class="post-visit-item">'
            f'<input class="post-visit-check" type="checkbox" aria-label="标记会后行动 {index} 已完成">'
            '<span class="post-visit-body">'
            '<span class="post-visit-title">'
            f'<span class="post-visit-priority">{escape(item.get("priority") or f"P{index - 1}")}</span>'
            f'<strong>{escape(action)}</strong>'
            "</span>"
            '<span class="post-visit-meta">'
            f'<span>负责人：{escape(item.get("owner"), "待确认")}</span>'
            f'<span>时限：{escape(item.get("due"), "待确认")}</span>'
            f'<span>触发：{escape(item.get("trigger"), "拜访结束后按会议结果确认")}</span>'
            "</span>"
            f'<span class="post-visit-standard"><strong>完成标准：</strong>{escape(item.get("completion_standard"), "形成可核对的下一步记录")}</span>'
            "</span></label>"
        )
    return '<div class="post-visit-list">' + "".join(output) + "</div>"


def render_pains(items: Any) -> str:
    normalized = [item for item in as_list(items) if isinstance(item, dict)][:6]
    if not normalized:
        normalized = [{"pain": "核心业务痛点待确认", "product_fit": "待评估", "evidence": "证据不足", "detail": "用现场问题验证，不作为已确认事实"}]
    return "".join(
        '<div class="pain-row">'
        f'<strong>{escape(item.get("pain") or item.get("title"))}</strong>'
        f'<span>{escape(item.get("product_fit"))} · {escape(item.get("evidence"))}</span>'
        f'<p>{escape(item.get("detail") or item.get("validation_question"))}</p>'
        "</div>"
        for item in normalized
    )


def render_detail_cards(items: Any, empty_title: str, empty_detail: str) -> str:
    normalized = [item for item in as_list(items) if isinstance(item, dict)][:6]
    if not normalized:
        normalized = [{"tag": "待补充", "title": empty_title, "detail": empty_detail}]
    return "".join(
        '<div class="detail-card">'
        f'<span class="detail-tag">{escape(item.get("tag") or item.get("status"), "待确认")}</span>'
        f'<strong>{escape(item.get("title") or item.get("name"))}</strong>'
        f'<p>{escape(item.get("detail") or item.get("impact") or item.get("note"))}</p>'
        "</div>"
        for item in normalized
    )


def render_coverage(coverage: Any) -> tuple[str, str]:
    raw = coverage if isinstance(coverage, dict) else {}
    labels = list(DEFAULT_COVERAGE_LABELS)
    labels.extend(label for label in raw if label not in labels and not is_memory_output_label(label))
    output: list[str] = []
    read_labels: list[str] = []
    for label in labels:
        status = raw.get(label, "未触发查询")
        if status not in VALID_QUERY_STATUSES:
            status = "查询失败"
        if status == "已读取":
            css_class = "coverage-tag--ok"
            read_labels.append(str(label))
        elif status in {"权限不足", "查询失败"}:
            css_class = "coverage-tag--danger"
        else:
            css_class = "coverage-tag--warn"
        output.append(f'<span class="coverage-tag {css_class}">{escape(label)}：{escape(status)}</span>')
    summary = "已读取：" + "、".join(read_labels[:6]) if read_labels else "尚无已确认读取的数据源"
    if len(read_labels) > 6:
        summary += "等"
    return "".join(output), summary


def render_source_content(bundle: dict[str, Any], coverage_html: str) -> str:
    references = bundle.get("references") if isinstance(bundle.get("references"), dict) else {}
    sources = references.get("sources")
    source_text = render_source_text(sources, "CRM 客户、商机、联系人和跟进记录；必要外部情报")
    confidence_note = references.get("confidence_note") or "确认：有直接证据；推断：有行为证据；猜测：当前证据不足，必须现场验证。"
    return (
        '<div class="source-note">'
        f'<div><strong>参考来源：</strong>{escape(source_text)}</div>'
        f'<div><strong>置信度说明：</strong>{escape(confidence_note)}</div>'
        '<div><strong>数据覆盖：</strong></div>'
        f'<div class="coverage-grid">{coverage_html}</div>'
        "</div>"
    )


def render_score_board(readiness: dict[str, Any]) -> str:
    info_score, info_display = numeric_score(readiness.get("information_completeness"))
    pain_score, pain_display = numeric_score(readiness.get("pain_point_match"))
    competition_score, competition_display = numeric_score(readiness.get("competitive_risk"))
    return (
        '<section class="score-board" id="score-board" aria-label="见客就绪度分项">'
        '<div class="score-card">'
        f'<span>信息完整度</span><strong>{escape(info_display)}</strong><div class="meter"><i style="width:{info_score}%"></i></div>'
        f'<p>{escape(readiness.get("information_note"), "信息缺口见最大缺口说明")}</p></div>'
        '<div class="score-card">'
        f'<span>痛点匹配度</span><strong>{escape(pain_display)}</strong><div class="meter"><i style="width:{pain_score}%"></i></div>'
        f'<p>{escape(readiness.get("pain_note"), "仅使用有证据的痛点")}</p></div>'
        '<div class="score-card score-card--warn">'
        f'<span>竞争风险度</span><strong>{escape(competition_display)}</strong><div class="meter"><i style="width:{competition_score}%"></i></div>'
        f'<p>{escape(readiness.get("competition_note"), "竞品状态需结合现场验证")}</p></div>'
        "</section>"
    )


def render_tabs(bundle: dict[str, Any], mode: str, source_content: str) -> str:
    people = nested(bundle, "sections", "people", default=[])
    timeline = nested(bundle, "sections", "timeline", default={}) or {}
    pains = nested(bundle, "sections", "pains", default=[])
    competition = nested(bundle, "sections", "competition", default=[])
    history = nested(bundle, "sections", "history_financial", default=[])
    post_visit_actions = bundle.get("post_visit_actions") or nested(bundle, "sections", "post_visit_actions", default=[])

    tabs: list[tuple[str, str, str]] = [
        ("people", "人力地图", f'<div class="people-grid">{render_people(people)}</div>'),
    ]
    timeline_items = (timeline.get("summary_items") or timeline.get("detail_items") or timeline.get("items")) if isinstance(timeline, dict) else timeline
    timeline_triggered = bool(timeline.get("triggered")) if isinstance(timeline, dict) else bool(timeline_items)
    if timeline_triggered or timeline_items:
        tabs.append(("timeline", "博弈编年", render_timeline(timeline, mode)))
    tabs.append(("pain", "痛点矩阵", f'<div class="pain-table">{render_pains(pains)}</div>'))
    tabs.append(("post-visit", "拜访后行动", render_post_visit_actions(post_visit_actions, mode)))
    if mode == "full":
        tabs.append(("competition", "竞品分析", f'<div class="detail-grid">{render_detail_cards(competition, "竞品状态待确认", "没有充分竞品证据时不要写成无竞品")}</div>'))
        tabs.append(("history", "历史合作与财务", f'<div class="detail-grid">{render_detail_cards(history, "历史合作与财务待补充", "权限不足或未读取时必须保留状态")}</div>'))
    tabs.append(("quality", "数据质量", source_content))

    buttons: list[str] = []
    panels: list[str] = []
    for index, (key, label, content) in enumerate(tabs):
        active_class = " is-active" if index == 0 else ""
        selected = "true" if index == 0 else "false"
        hidden = "" if index == 0 else " hidden"
        buttons.append(
            f'<button class="tab-button{active_class}" type="button" role="tab" aria-selected="{selected}" '
            f'aria-controls="{key}-panel" id="{key}-tab">{escape(label)}</button>'
        )
        panels.append(
            f'<div class="tab-panel{active_class}" role="tabpanel" id="{key}-panel" aria-labelledby="{key}-tab"{hidden}>{content}</div>'
        )
    return (
        '<section class="tabs-card" id="supplemental-tabs" aria-label="补充信息页签">'
        f'<div class="tab-list" role="tablist">{"".join(buttons)}</div>'
        f'{"".join(panels)}</section>'
    )


def build_fragments(bundle: dict[str, Any], preview: bool) -> dict[str, str]:
    metadata = bundle.get("metadata") if isinstance(bundle.get("metadata"), dict) else {}
    meeting = bundle.get("meeting") if isinstance(bundle.get("meeting"), dict) else {}
    readiness = bundle.get("readiness") if isinstance(bundle.get("readiness"), dict) else {}
    mode = str(metadata.get("mode") or "normal").lower()
    if mode not in VALID_MODES:
        raise ValueError("metadata.mode 必须是 lite、normal 或 full")

    score_value, score_display = numeric_score(readiness.get("readiness"))
    grade_label, grade_class = readiness_grade(readiness, score_value)
    risk_items, risk_heading = render_risks(bundle.get("risks"), mode)
    action_items, action_count = render_actions(bundle.get("actions"), mode)
    coverage_html, coverage_summary = render_coverage(bundle.get("data_coverage"))
    source_content = render_source_content(bundle, coverage_html)
    readiness_gap = str(readiness.get("weakest_gap") or readiness.get("readiness_gap") or coverage_summary).strip()
    if memory_information_is_incomplete(metadata) and "历史关系与关键互动信息待核对" not in readiness_gap:
        readiness_gap = "；".join(item for item in (readiness_gap, "历史关系与关键互动信息待核对") if item)

    if mode == "lite":
        score_board_section = ""
        supplemental_tabs = ""
        post_visit_actions = bundle.get("post_visit_actions") or nested(bundle, "sections", "post_visit_actions", default=[])
        lite_post_visit_section = (
            '<section class="compact-source" id="lite-post-visit">'
            '<div class="section-kicker">拜访后行动</div>'
            f'{render_post_visit_actions(post_visit_actions, mode)}</section>'
        )
        lite_source_section = f'<section class="compact-source" id="lite-source"><div class="section-kicker">数据说明</div>{source_content}</section>'
    else:
        score_board_section = render_score_board(readiness)
        supplemental_tabs = render_tabs(bundle, mode, source_content)
        lite_post_visit_section = ""
        lite_source_section = ""

    return {
        "customer_name": escape(metadata.get("customer_name")),
        "briefing_mode": mode,
        "preview_mode": "true" if preview else "false",
        "customer_type": escape(metadata.get("customer_type"), "客户类型待确认"),
        "current_stage": escape(metadata.get("current_stage") or metadata.get("meeting_topic"), "会议阶段待确认"),
        "meeting_time": escape(metadata.get("meeting_time") or metadata.get("report_date") or date.today().isoformat()),
        "one_sentence_judgement": escape(meeting.get("one_sentence_judgement")),
        "meeting_context_summary": escape(meeting.get("context_summary")),
        "first_question": escape(meeting.get("first_question")),
        "readiness_ring_score": str(score_value),
        "readiness_score": escape(score_display, "--"),
        "readiness_grade": escape(grade_label),
        "readiness_status_class": grade_class,
        "meeting_recommendation": escape(meeting_recommendation(readiness, score_value)),
        "readiness_gap": escape(readiness_gap),
        "today_goal": escape(meeting.get("today_goal")),
        "biggest_risk": escape(meeting.get("biggest_risk")),
        "recommended_play": escape(meeting.get("recommended_play") or meeting.get("one_sentence_judgement"), "先验证最大缺口，再收敛下一步"),
        "key_person": escape(meeting.get("key_person")),
        "do_not_do": escape(meeting.get("do_not_do")),
        "meeting_boundary": escape(meeting.get("meeting_boundary")),
        "risk_heading": escape(risk_heading),
        "risk_items": risk_items,
        "action_count_label": escape(action_count),
        "action_items": action_items,
        "score_board_section": score_board_section,
        "supplemental_tabs": supplemental_tabs,
        "lite_post_visit_section": lite_post_visit_section,
        "lite_source_section": lite_source_section,
    }


def render(template_text: str, fragments: dict[str, str]) -> str:
    pattern = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
    unknown = sorted({name for name in pattern.findall(template_text) if name not in fragments})
    if unknown:
        raise ValueError("模板包含未定义占位符：" + "、".join(unknown))
    return pattern.sub(lambda match: fragments[match.group(1)], template_text)


def mock_bundle(mode: str = "normal") -> dict[str, Any]:
    return {
        "metadata": {
            "customer_name": "示例制造有限公司",
            "mode": mode,
            "memory_status": "部分",
            "customer_type": "多轮跟进客户",
            "current_stage": "方案评估 → 商务确认",
            "meeting_time": "2026-07-13 14:00",
        },
        "meeting": {
            "one_sentence_judgement": "锁定预算审批路径，同时确认最终拍板人与竞品比价结论。",
            "context_summary": "客户业务负责人支持推进，但预算审批和财务角色覆盖不足。今天先补齐决策链，不主动进入价格让步。",
            "first_question": "李经理，上次确认的预算申请现在走到哪一步，最终还需要谁批准？",
            "today_goal": "确认预算审批节点和明确时间表",
            "biggest_risk": "财务角色未覆盖，预算状态不清",
            "recommended_play": "借内部支持者补齐审批链，先问节点再谈条件",
            "key_person": "李经理 · 内部教练",
            "meeting_boundary": "价值与审批链未确认前不主动让价",
            "do_not_do": "未确认最终拍板人前承诺商务条件",
        },
        "readiness": {
            "information_completeness": 78,
            "pain_point_match": 84,
            "competitive_risk": 58,
            "readiness": 68,
            "readiness_grade": {"color": "yellow", "label": "准备中"},
            "weakest_gap": "财务审批人与最终拍板链尚未确认",
            "meeting_recommendation": "可以推进，但先补最大缺口",
            "information_note": "客户、商机和近期互动已读取，财务角色不足",
            "pain_note": "两个客户原话痛点可直接验证",
            "competition_note": "存在弱竞品信号，需现场确认",
        },
        "risks": [
            {"title": "预算审批路径不清", "response": "直接确认当前节点、最终审批人与预计完成时间"},
            {"title": "竞品价格信号未核实", "response": "先问内部比价结论，不主动攻击竞品"},
            {"title": "技术支持不等于商务承诺", "response": "区分技术通过与最终采购决定"},
        ],
        "actions": [
            {"priority": "P0", "title": "锁定审批路径", "detail": "问：预算现在走到哪一步，最终需要谁批准？"},
            {"priority": "P1", "title": "确认竞品结论", "detail": "问：内部比较方案后，目前最担心哪一点？"},
            {"priority": "P2", "title": "明确下一步", "detail": "会议结束前确认责任人和具体日期。"},
        ],
        "sections": {
            "people": [
                {"name": "王总", "title": "副总经理", "role": "EB 候选", "stance": "中立", "tactic": "确认其是否拥有最终预算权"},
                {"name": "李经理", "title": "销售运营负责人", "role": "Coach", "stance": "支持", "tactic": "借力补齐审批链和采购信息"},
                {"name": "陈工", "title": "IT 负责人", "role": "TB", "stance": "支持", "tactic": "确认技术侧是否仍有未决问题"},
            ],
            "timeline": {
                "triggered": True,
                "time_range": "2026-05 至今天",
                "summary_items": [
                    {"date": "2026-06-20", "event": "客户确认业务方案方向", "impact": "今天应从功能讨论转向审批路径"},
                    {"date": "2026-07-02", "event": "技术评审通过", "impact": "借力技术负责人推动商务侧"},
                    {"date": "今天", "event": "预算与采购确认会", "impact": "必须锁定最终拍板人与时间表"},
                ],
                "detail_items": [
                    {"date": "2026-05-18", "event_type": "interaction", "event": "业务负责人首次确认预测汇总痛点", "our_action": "完成现状访谈并整理场景", "customer_reaction": "认可问题，但未给出量化目标", "commitment_status": "not_applicable", "relationship_change": "warming", "visit_impact": "今天需补问量化成功标准", "confidence": "confirmed"},
                    {"date": "2026-06-20", "event_type": "stage_change", "event": "客户确认业务方案方向", "our_action": "提交业务方案和实施边界", "customer_reaction": "同意进入技术评审", "commitment_status": "kept", "relationship_change": "warming", "visit_impact": "本次不再重复功能演示，应转向审批路径", "confidence": "confirmed"},
                    {"date": "2026-07-02", "event_type": "commitment", "event": "技术评审通过，但预算节点未确认", "our_action": "补齐接口说明", "customer_reaction": "技术负责人确认无阻断项", "commitment_status": "kept", "relationship_change": "stable", "visit_impact": "借技术结论推动商务角色表态", "confidence": "confirmed"},
                    {"date": "今天", "event_type": "budget", "event": "预算与采购确认会", "our_action": "计划确认最终审批人和日期", "customer_reaction": "待会议验证", "commitment_status": "unknown", "relationship_change": "unknown", "visit_impact": "必须锁定最终拍板人与下一步时间表", "confidence": "inferred"},
                ],
                "turning_points": [
                    {"date": "2026-07-02", "turning_point": "技术评审由阻断项转为通过", "reason": "技术负责人确认无未决问题", "visit_note": "本次应把议题转向预算与审批，而不是继续演示功能"},
                ],
                "timeline_gaps": [
                    "最终预算拍板人和采购审批日期仍未确认",
                ],
            },
            "pains": [
                {"pain": "销售预测依赖手工汇总", "product_fit": "P1", "evidence": "E1", "detail": "客户原话，可直接用于价值确认"},
                {"pain": "集团客户数据分散", "product_fit": "P1", "evidence": "E2", "detail": "有多次互动证据，现场确认量化影响"},
                {"pain": "审批周期过长", "product_fit": "待评估", "evidence": "推断", "detail": "作为现场验证问题，不写成客户事实"},
            ],
            "competition": [
                {"tag": "弱信号", "title": "现有自研系统", "detail": "迁移成本是主要比较点，需确认客户是否仍考虑保留"},
            ],
            "history_financial": [
                {"tag": "历史合作", "title": "一期项目已完成", "detail": "回款状态正常；本次增购范围仍待确认"},
            ],
        },
        "post_visit_actions": [
            {"priority": "P0", "action": "记录审批链与双方承诺", "owner": "客户经理", "due": "会后30分钟内", "trigger": "拜访结束", "completion_standard": "跟进记录写明最终审批人、责任人和日期"},
            {"priority": "P0", "action": "发送会议结论确认", "owner": "客户经理", "due": "当日", "trigger": "客户给出明确下一步", "completion_standard": "客户书面确认下一步、双方责任人与时间"},
            {"priority": "P1", "action": "创建接口说明补充任务", "owner": "售前", "due": "客户约定日期", "trigger": "客户提出新的技术材料要求", "completion_standard": "材料交付并由技术负责人确认无遗漏"},
        ],
        "data_coverage": {
            "客户": "已读取",
            "商机": "已读取",
            "联系人": "已读取",
            "跟进记录": "已读取",
            "日程": "已读取",
            "需求/问题": "已读取",
            "会议": "权限不足",
            "待办/任务": "已读取",
            "现场拜访": "未触发查询",
            "竞品明细": "无数据",
            "合同": "未触发查询",
            "订单/回款": "未触发查询",
            "外部情报": "已读取",
        },
        "references": {
            "sources": ["CRM 客户、商机、联系人和跟进记录", "客户记忆", "必要外部情报"],
            "confidence_note": "确认：有 CRM、客户原话或明确事件；推断：有行为证据；猜测：证据不足，必须现场验证。",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="按固定模板渲染见客前客户简报")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="pre_visit_facts_bundle JSON 文件")
    source.add_argument("--mock", action="store_true", help="使用内置模拟数据生成预览")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), help="仅在 --mock 时覆盖模拟模式")
    parser.add_argument("--output", type=Path, required=True, help="输出 HTML 文件")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="正式 HTML 模板")
    parser.add_argument("--forbid-text", action="append", default=[], help="禁止残留的旧客户或样例文字，可重复传入")
    args = parser.parse_args()

    if args.mock:
        bundle = mock_bundle(args.mode or "normal")
    else:
        try:
            bundle = json.loads(args.input.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: 无法读取事实包：{exc}", file=sys.stderr)
            return 2
        if not isinstance(bundle, dict):
            print("ERROR: pre_visit_facts_bundle 顶层必须是 JSON 对象", file=sys.stderr)
            return 2

    try:
        template_text = args.template.read_text(encoding="utf-8")
        rendered = render(template_text, build_fragments(bundle, preview=args.mock))
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
