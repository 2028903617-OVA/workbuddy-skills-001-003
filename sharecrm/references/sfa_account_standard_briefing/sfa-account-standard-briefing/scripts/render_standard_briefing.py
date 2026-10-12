#!/usr/bin/env python3
"""Render the standard customer briefing from a structured facts bundle."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from validate_standard_briefing import validate_html


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "templates" / "standard_briefing.html"
DEFAULT_COVERAGE_LABELS = (
    "客户",
    "商机",
    "联系人",
    "销售记录",
    "需求",
    "互动问题",
    "日程",
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
    "ActiveRecordObj": "销售记录",
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
PROFILE_FIELD_LABELS = {
    "name": "客户名称",
    "customer_no": "客户编号",
    "account_no": "客户编号",
    "level": "客户等级",
    "nature": "客户性质",
    "industry": "行业",
    "employee_count": "员工规模",
    "annual_revenue": "营收规模",
    "address": "地址",
    "website": "官网",
    "source": "客户来源",
    "account_source": "客户来源",
    "create_time": "创建时间",
    "owner": "负责人",
    "department": "部门",
    "deal_status": "成交状态",
    "last_deal_time": "最近成交时间",
    "last_deal_closed_time": "最近成交时间",
    "last_followed_time": "最后跟进时间",
    "transfer_count": "转移次数",
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
    (r"\bIT\s*现状", "信息化现状"),
    (r"\bIT\s*负责人", "信息化负责人"),
    (r"\bIT\s*总监", "信息化总监"),
    (r"(?<![（(])\bIT\b", "信息化（IT）"),
    (r"(?<![（(])\bVP\b", "副总裁（VP）"),
    (r"(?<![（(])\bIVD\b", "体外诊断（IVD）"),
    (r"\bfull\s*模式", "完整模式"),
)
VALID_QUERY_STATUSES = {"已读取", "无数据", "权限不足", "未触发查询", "查询失败"}


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
    chinese_terms = r"副总裁（VP）|信息化（IT）|信息化负责人|信息化总监|信息化现状|内部支持者|守门人|客户经理|最终决策人（EB）|最终决策人候选（EB）|技术把关人（TB）"
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


def as_items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def confidence_class(confidence: Any) -> str:
    value = str(confidence or "未知")
    if value in {"确认", "confirmed", "高"}:
        return "tag-green"
    if value in {"推断", "inferred", "中"}:
        return "tag-amber"
    return "tag-blue"


def status_class(status: Any) -> str:
    value = str(status or "未触发查询")
    if value == "已读取":
        return "tag-green"
    if value in {"权限不足", "查询失败"}:
        return "tag-red"
    if value == "无数据":
        return "tag-blue"
    return "tag-amber"


def render_list(items: Any, default: str = "未知 / 待补充") -> str:
    rendered: list[str] = []
    for item in as_items(items):
        if isinstance(item, dict):
            content = (
                item.get("text")
                or item.get("content")
                or item.get("value")
                or item.get("motivation")
                or item.get("action")
                or default
            )
            confidence = item.get("confidence")
            suffix = ""
            if confidence:
                suffix = f' <span class="tag {confidence_class(confidence)}">{escape(confidence)}</span>'
            rendered.append(f"<li>{escape(content)}{suffix}</li>")
        else:
            rendered.append(f"<li>{escape(item)}</li>")
    return "".join(rendered) if rendered else f"<li>{escape(default)}</li>"


def render_info_items(items: Any) -> str:
    normalized: list[dict[str, Any]] = []
    if isinstance(items, dict):
        normalized = [
            {"label": PROFILE_FIELD_LABELS.get(str(key), key), "value": value}
            for key, value in items.items()
        ]
    else:
        for item in as_items(items):
            if isinstance(item, dict):
                raw_label = (
                    item.get("label")
                    or item.get("field_name")
                    or item.get("display_name")
                    or item.get("api_name")
                )
                normalized.append(
                    {
                        **item,
                        "label": PROFILE_FIELD_LABELS.get(str(raw_label), raw_label),
                    }
                )
    if not normalized:
        normalized = [{"label": "信息状态", "value": "未知 / 待补充"}]
    return "".join(
        '<div class="identity-item">'
        f'<span class="identity-label">{escape(item.get("label"))}</span>'
        f'<span class="identity-value">{escape(item.get("value"))}</span>'
        "</div>"
        for item in normalized
    )


def render_table_rows(rows: Any, columns: Iterable[tuple[str, str]]) -> str:
    column_list = list(columns)
    normalized = [row for row in as_items(rows) if isinstance(row, dict)]
    if not normalized:
        return f'<tr><td colspan="{len(column_list)}">暂无记录 / 待补充</td></tr>'
    output: list[str] = []
    for row in normalized:
        cells: list[str] = []
        for key, _ in column_list:
            value = row.get(key)
            if key == "confidence":
                confidence = value or "未知"
                cells.append(f'<td><span class="tag {confidence_class(confidence)}">{escape(confidence)}</span></td>')
            else:
                cells.append(f"<td>{escape(value)}</td>")
        output.append("<tr>" + "".join(cells) + "</tr>")
    return "".join(output)


def render_kpis(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)][:6]
    if not normalized:
        normalized = [
            {"label": "商机总金额", "value": "未知", "note": "待读取商机数据"},
            {"label": "进行中商机", "value": "未知", "note": "待确认"},
            {"label": "关键联系人", "value": "未知", "note": "待读取联系人数据"},
            {"label": "最近互动", "value": "未知", "note": "待读取销售记录"},
        ]
    return "".join(
        '<div class="metric-card">'
        f'<span class="label">{escape(item.get("label"))}</span>'
        f'<span class="metric-value">{escape(item.get("value"))}</span>'
        f'<span class="metric-note">{escape(item.get("note"))}</span>'
        "</div>"
        for item in normalized
    )


def render_summary_rows(rows: Any) -> str:
    normalized = [row for row in as_items(rows) if isinstance(row, dict)]
    if not normalized:
        normalized = [{"item": "信息状态", "conclusion": "信息不足，待补充", "confidence": "未知"}]
    return "".join(
        "<tr>"
        f'<td>{escape(row.get("item"))}</td>'
        f'<td>{escape(row.get("conclusion"))}</td>'
        f'<td><span class="tag {confidence_class(row.get("confidence"))}">{escape(row.get("confidence"), "未知")}</span></td>'
        "</tr>"
        for row in normalized
    )


def render_timeline(items: Any) -> str:
    normalized = [item for item in as_items(items) if isinstance(item, dict)]
    if not normalized:
        normalized = [{"date": "未知", "counterpart": "未知", "channel": "未知", "content": "暂无关键互动记录"}]
    output: list[str] = []
    for item in normalized:
        meta_parts = [item.get("date"), item.get("counterpart"), item.get("channel")]
        meta = " · ".join(escape(part) for part in meta_parts if part not in (None, "")) or "时间与对象未知"
        details = [item.get("content"), item.get("commitment"), item.get("impact")]
        detail_text = "；".join(normalize_api_names(part) for part in details if part not in (None, ""))
        confidence = item.get("confidence")
        confidence_html = ""
        if confidence:
            confidence_html = f' <span class="tag {confidence_class(confidence)}">{escape(confidence)}</span>'
        output.append(
            '<div class="timeline-item">'
            f'<div class="timeline-meta">{meta}{confidence_html}</div>'
            f'<div class="timeline-content">{escape(detail_text, "暂无关键内容")}</div>'
            "</div>"
        )
    return "".join(output)


def render_relationship_cards(cards: Any) -> str:
    normalized = [card for card in as_items(cards) if isinstance(card, dict)]
    if not normalized:
        normalized = [{"title": "总体关系", "temperature": "未知", "evidence": "互动证据不足", "confidence": "未知"}]
    output: list[str] = []
    for card in normalized:
        confidence = card.get("confidence") or "未知"
        output.append(
            '<div class="person-card">'
            f'<span class="label">{escape(card.get("title"))}</span>'
            f'<div class="value">{escape(card.get("temperature"))}</div>'
            f'<p>{escape(card.get("evidence"))}</p>'
            f'<span class="tag {confidence_class(confidence)}">{escape(confidence)}</span>'
            "</div>"
        )
    return "".join(output)


def severity_style(severity: Any) -> tuple[str, str]:
    value = str(severity or "中")
    if value in {"高", "严重", "红色", "致命"}:
        return "note-danger", "tag-red"
    if value in {"低", "绿色"}:
        return "note-success", "tag-green"
    return "note-warning", "tag-amber"


def render_risk_cards(risks: Any) -> str:
    normalized = [risk for risk in as_items(risks) if isinstance(risk, dict)]
    if not normalized:
        normalized = [{"severity": "未知", "risk": "暂无已确认风险", "impact": "仍需结合后续数据核对", "trigger": "未知"}]
    output: list[str] = []
    for risk in normalized:
        note_class, tag_class = severity_style(risk.get("severity"))
        output.append(
            f'<div class="risk-card note {note_class}">'
            f'<span class="tag {tag_class}">{escape(risk.get("severity"), "未知")}</span>'
            f'<div class="sub-title">{escape(risk.get("risk"))}</div>'
            f'<div><strong>影响：</strong>{escape(risk.get("impact"))}</div>'
            f'<div><strong>触发条件：</strong>{escape(risk.get("trigger"))}</div>'
            f'<div><strong>缓释方向：</strong>{escape(risk.get("mitigation"))}</div>'
            "</div>"
        )
    return "".join(output)


def render_question_cards(questions: Any) -> str:
    normalized = [question for question in as_items(questions) if isinstance(question, dict)]
    if not normalized:
        normalized = [{"question": "当前最大未知项待补充", "why": "信息不足会影响客户判断", "confidence": "未知"}]
    output: list[str] = []
    for question in normalized:
        confidence = question.get("confidence") or "未知"
        output.append(
            '<div class="insight-card">'
            f'<div class="value">{escape(question.get("question"))}</div>'
            f'<p><strong>重要性：</strong>{escape(question.get("why"))}</p>'
            f'<span class="tag {confidence_class(confidence)}">{escape(confidence)}</span>'
            "</div>"
        )
    return "".join(output)


def render_action_cards(actions: Any) -> str:
    normalized = as_items(actions)
    if not normalized:
        normalized = [{"action": "暂无建议动作 / 待补充"}]
    output: list[str] = []
    for item in normalized[:5]:
        if not isinstance(item, dict):
            item = {"action": item}
        confidence = item.get("confidence")
        confidence_html = ""
        if confidence:
            confidence_html = f'<span class="tag {confidence_class(confidence)}">{escape(confidence)}</span>'
        details = []
        if item.get("purpose"):
            details.append(f'<p><strong>目的：</strong>{escape(item.get("purpose"))}</p>')
        if item.get("timing"):
            details.append(f'<p><strong>适合时机：</strong>{escape(item.get("timing"))}</p>')
        if item.get("owner_or_role"):
            details.append(f'<p><strong>责任角色：</strong>{escape(item.get("owner_or_role"))}</p>')
        output.append(
            '<div class="insight-card">'
            f'<div class="value">{escape(item.get("action") or item.get("text") or item.get("content"))}</div>'
            + "".join(details)
            + confidence_html
            + "</div>"
        )
    return "".join(output)


def render_coverage(coverage: Any) -> tuple[str, str]:
    raw = coverage if isinstance(coverage, dict) else {}
    ordered_labels = list(DEFAULT_COVERAGE_LABELS)
    ordered_labels.extend(label for label in raw if label not in ordered_labels and not is_memory_output_label(label))
    tags: list[str] = []
    read_labels: list[str] = []
    for label in ordered_labels:
        status = raw.get(label, "未触发查询")
        if status not in VALID_QUERY_STATUSES:
            status = "查询失败"
        if status == "已读取":
            read_labels.append(str(label))
        tags.append(f'<span class="tag {status_class(status)}">{escape(label)}：{escape(status)}</span>')
    if read_labels:
        visible = read_labels[:6]
        summary = "已覆盖：" + " · ".join(visible)
        if len(read_labels) > len(visible):
            summary += "等"
    else:
        summary = "数据覆盖状态待确认"
    return "".join(tags), summary


def render_history_section(history: Any, enabled: bool) -> tuple[str, str]:
    if not enabled:
        return "", ""
    data = history if isinstance(history, dict) else {}
    records = render_table_rows(
        data.get("records"),
        (("type", "类型"), ("name", "名称"), ("status", "状态"), ("amount", "金额"), ("date", "日期"), ("note", "说明")),
    )
    section = (
        '<section class="section" id="history-financial">'
        '<h2 class="section-title">历史合作、财务与客户健康</h2>'
        '<p class="section-lead">仅在 --full 或用户明确要求历史订单、回款、增购时展示。</p>'
        f'<div class="insight-card"><span class="label">总体判断</span><p class="summary-conclusion">{escape(data.get("summary"))}</p></div>'
        '<div class="sub-title">合同、订单与回款记录</div>'
        '<div class="table-wrap"><table><thead><tr><th>类型</th><th>名称</th><th>状态</th><th>金额</th><th>日期</th><th>说明</th></tr></thead>'
        f'<tbody>{records}</tbody></table></div>'
        '<div class="sub-title">客户健康、续约与增购信号</div>'
        f'<ul>{render_list(data.get("health_notes"))}</ul>'
        "</section>"
    )
    return '<button type="button" role="tab" aria-selected="false" aria-controls="history-financial" data-tab="history-financial">历史合作与财务</button>', section


def build_fragments(bundle: dict[str, Any], preview: bool) -> dict[str, str]:
    metadata = nested(bundle, "metadata", default={}) or {}
    summary = nested(bundle, "executive_summary", default={}) or {}
    sections = nested(bundle, "sections", default={}) or {}
    profile = sections.get("customer_profile") or {}
    timeline = sections.get("timeline") or {}
    relationship = sections.get("relationship_temperature") or {}
    decision = sections.get("decision_chain") or {}
    opportunity = sections.get("opportunity_overview") or {}
    pain = sections.get("pain_map") or {}
    competition = sections.get("competitive_overview") or {}
    open_questions = sections.get("open_questions") or {}
    history = sections.get("history_financial") or {}
    references = nested(bundle, "references", default={}) or {}

    coverage_tags, coverage_summary = render_coverage(bundle.get("data_coverage"))
    full_enabled = bool(history.get("enabled")) or metadata.get("mode") == "full"
    history_nav, history_section = render_history_section(history, full_enabled)

    report_date = metadata.get("report_date") or date.today().isoformat()
    health_score = metadata.get("health_score")
    if not isinstance(health_score, (int, float)) or not 0 <= health_score <= 100:
        health_score = "--"

    source_values = references.get("sources")
    source_text = render_source_text(source_values, "CRM 客户、商机、联系人和互动记录；必要外部情报")
    largest_gap = str(open_questions.get("largest_gap") or "").strip()
    if memory_information_is_incomplete(metadata) and "历史关系与关键互动信息待核对" not in largest_gap:
        largest_gap = "；".join(item for item in (largest_gap, "历史关系与关键互动信息待核对") if item)

    fragments = {
        "preview_mode": "true" if preview else "false",
        "customer_name": escape(metadata.get("customer_name")),
        "report_date": escape(report_date),
        "briefing_status": escape(metadata.get("briefing_status"), "标准版客户档案"),
        "data_scope_summary": escape(metadata.get("data_scope_summary") or coverage_summary),
        "executive_subtitle": escape(metadata.get("subtitle"), "从客户画像、决策圈、博弈时间线、商机、痛点、竞品和风险建立统一客户认知。"),
        "customer_status": escape(metadata.get("customer_status")),
        "industry_or_segment": escape(metadata.get("industry_or_segment")),
        "owner": escape(metadata.get("owner")),
        "information_completeness": escape(metadata.get("information_completeness"), "不足"),
        "health_score": escape(health_score, "--"),
        "health_grade": escape(metadata.get("health_grade"), "待评估"),
        "health_signal": escape(metadata.get("health_signal"), "当前证据不足，客户健康度待补充。"),
        "kpi_cards": render_kpis(bundle.get("kpis")),
        "one_sentence_conclusion": escape(summary.get("one_sentence_conclusion")),
        "summary_rows": render_summary_rows(summary.get("rows")),
        "priority_items": render_list(summary.get("priority_items")),
        "profile_info_items": render_info_items(profile.get("basic_info")),
        "business_status_items": render_list(profile.get("business_status")),
        "strategy_items": render_list(profile.get("strategy")),
        "system_motivation_items": render_list(profile.get("system_motivation")),
        "timeline_items": render_timeline(timeline.get("items")),
        "timeline_trend": escape(timeline.get("trend")),
        "relationship_cards": render_relationship_cards(relationship.get("cards")),
        "relationship_summary": escape(relationship.get("summary")),
        "people_rows": render_table_rows(
            decision.get("people"),
            (("name", "关键人"), ("title", "职位"), ("role", "角色"), ("attitude", "态度"), ("evidence", "影响与证据"), ("confidence", "置信度")),
        ),
        "coverage_analysis": escape(decision.get("coverage_analysis")),
        "project_origin": escape(opportunity.get("project_origin")),
        "customer_goal_items": render_list(opportunity.get("customer_goals")),
        "must_have_items": render_list(opportunity.get("must_haves")),
        "budget_items": render_info_items(opportunity.get("budget_approval")),
        "usage_rows": render_table_rows(
            opportunity.get("usage_scope"),
            (("group", "部门 / 群体"), ("scale", "规模"), ("need", "核心诉求"), ("priority", "优先级")),
        ),
        "it_rows": render_table_rows(
            opportunity.get("it_landscape"),
            (("system", "系统"), ("purpose", "用途"), ("status", "现状"), ("impact", "对项目影响")),
        ),
        "opportunity_rows": render_table_rows(
            opportunity.get("opportunities"),
            (("name", "商机"), ("stage", "状态 / 阶段"), ("amount", "金额"), ("expected_close", "预计成交日"), ("stage_age", "阶段停留"), ("confidence", "置信度")),
        ),
        "opportunity_summary": escape(opportunity.get("summary")),
        "pain_confirmed_items": render_list(pain.get("confirmed")),
        "pain_inferred_items": render_list(pain.get("inferred")),
        "pain_verify_items": render_list(pain.get("to_verify")),
        "competitor_rows": render_table_rows(
            competition.get("competitors"),
            (("name", "竞品"), ("status", "状态 / 威胁"), ("reason", "客户比较原因"), ("our_advantage", "我方优势"), ("our_weakness", "我方短板"), ("confidence", "置信度")),
        ),
        "advantage_items": render_list(competition.get("advantages")),
        "weakness_items": render_list(competition.get("weaknesses")),
        "risk_cards": render_risk_cards(open_questions.get("risks")),
        "open_question_cards": render_question_cards(open_questions.get("questions")),
        "largest_gap": escape(largest_gap),
        "data_alert_items": render_list(open_questions.get("data_alerts")),
        "action_cards": render_action_cards(open_questions.get("actions")),
        "history_nav_item": history_nav,
        "history_financial_section": history_section,
        "data_coverage_tags": coverage_tags,
        "data_cutoff": escape(metadata.get("data_cutoff") or report_date),
        "next_update": escape(metadata.get("next_update"), "下次关键互动后"),
        "reference_sources": escape(source_text),
        "confidence_note": escape(references.get("confidence_note"), "确认：有直接证据；推断：有行为证据但未被客户直接确认；未知：当前无充分证据。"),
    }
    return fragments


def render(template_text: str, fragments: dict[str, str]) -> str:
    placeholder_pattern = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
    unknown = sorted({name for name in placeholder_pattern.findall(template_text) if name not in fragments})
    if unknown:
        raise ValueError("模板包含未定义占位符：" + "、".join(unknown))
    return placeholder_pattern.sub(lambda match: fragments[match.group(1)], template_text)


def mock_bundle() -> dict[str, Any]:
    return {
        "metadata": {
            "customer_name": "示例制造有限公司",
            "report_date": "2026-07-13",
            "briefing_status": "标准版客户档案",
            "memory_status": "部分",
            "customer_status": "重点跟进",
            "industry_or_segment": "高端制造",
            "owner": "示例负责人",
            "information_completeness": "部分",
            "health_score": 72,
            "health_grade": "稳中有险",
            "health_signal": "商机与关键人覆盖较好，但预算审批链和回款安排仍需核对。",
            "data_cutoff": "2026-07-13 10:00",
            "next_update": "下次关键互动后",
        },
        "data_coverage": {
            "客户": "已读取",
            "商机": "已读取",
            "联系人": "已读取",
            "销售记录": "已读取",
            "需求": "已读取",
            "互动问题": "无数据",
            "日程": "已读取",
            "会议": "权限不足",
            "待办/任务": "已读取",
            "现场拜访": "未触发查询",
            "竞品明细": "已读取",
            "合同": "未触发查询",
            "订单/回款": "未触发查询",
            "外部情报": "已读取",
        },
        "kpis": [
            {"label": "进行中商机", "value": "3 个", "note": "合计 810 万元"},
            {"label": "关键联系人", "value": "6 人", "note": "覆盖 3 类决策角色"},
            {"label": "最近互动", "value": "3 天前", "note": "客户态度积极"},
            {"label": "最大缺口", "value": "预算审批", "note": "财务角色尚未覆盖"},
        ],
        "executive_summary": {
            "one_sentence_conclusion": "客户价值与项目意愿较高，但预算审批和财务角色覆盖不足，当前判断为有机会、需验证。",
            "rows": [
                {"item": "客户状态", "conclusion": "重点跟进，项目处于方案评估期", "confidence": "确认"},
                {"item": "主要机会", "conclusion": "集团数字化升级形成明确窗口", "confidence": "推断"},
                {"item": "主要风险", "conclusion": "预算尚未完成最终批复", "confidence": "确认"},
            ],
            "priority_items": ["核对预算审批节点", "补齐财务决策角色", "验证上线范围与成功标准"],
        },
        "sections": {
            "customer_profile": {
                "basic_info": [
                    {"label": "客户名称", "api_name": "name", "value": "示例制造有限公司"},
                    {"label": "客户编号", "api_name": "customer_no", "value": "C-00001"},
                    {"label": "客户等级", "api_name": "level", "value": "A"},
                    {"label": "主要联系人", "api_name": "primary_contact", "value": "李经理"},
                    {"label": "合作时长", "api_name": "cooperation_duration", "value": "18 个月"},
                    {"label": "商机总金额", "api_name": "opportunity_total_amount", "value": "810 万元"},
                ],
                "business_status": ["主营工业自动化设备", "收入主要来自国内大客户项目"],
                "strategy": ["未来两年推进集团数字化运营", "计划提升销售预测准确率"],
                "system_motivation": ["统一集团客户数据与销售过程", "提升销售预测准确率并降低手工汇总成本"],
            },
            "timeline": {
                "items": [
                    {"date": "2026-07-10", "counterpart": "李经理", "channel": "会议", "content": "确认方案方向", "commitment": "一周内反馈预算", "impact": "项目继续升温", "confidence": "确认"},
                    {"date": "2026-06-28", "counterpart": "王总", "channel": "拜访", "content": "强调集团统一管理诉求", "impact": "高层价值主张得到验证", "confidence": "确认"},
                ],
                "trend": "客户关注点已从功能比较转向集团管理价值，整体关系升温。",
            },
            "relationship_temperature": {
                "cards": [
                    {"title": "总体关系", "temperature": "温", "evidence": "近 30 天有 4 次有效互动", "confidence": "确认"},
                    {"title": "业务负责人", "temperature": "热", "evidence": "主动协调方案评审", "confidence": "确认"},
                ],
                "summary": "业务线支持度较高，但财务与采购关系仍为空白。",
            },
            "decision_chain": {
                "people": [
                    {"name": "王总", "title": "副总经理", "role": "EB 候选", "attitude": "支持", "evidence": "关注集团 ROI，参与方案评审", "confidence": "推断"},
                    {"name": "李经理", "title": "销售运营负责人", "role": "内部教练", "attitude": "支持", "evidence": "持续提供组织和需求信息", "confidence": "确认"},
                ],
                "coverage_analysis": "业务与高层角色已有覆盖，财务、采购和最终拍板链仍需核对。",
            },
            "opportunity_overview": {
                "project_origin": "客户在集团数字化升级过程中主动提出统一客户与销售过程管理需求。",
                "customer_goals": ["销售预测准确率提升到 80%", "统一集团客户主数据"],
                "must_haves": ["支持多组织权限", "与现有 ERP 对接"],
                "budget_approval": {"预算": "约 500 万元", "状态": "申请中", "审批链": "业务部门 → 财务 → 总经理"},
                "usage_scope": [{"group": "销售与运营", "scale": "约 600 人", "need": "统一过程与预测", "priority": "P0"}],
                "it_landscape": [{"system": "ERP", "purpose": "订单与财务", "status": "使用中", "impact": "需要主数据和订单接口"}],
                "opportunities": [{"name": "集团 CRM 升级", "stage": "方案评估", "amount": "500 万元", "expected_close": "2026-09-30", "stage_age": "12 天", "confidence": "推断"}],
                "summary": "核心项目具备明确需求和高层关注，但预算批复仍是成交前提。",
            },
            "pain_map": {
                "confirmed": ["集团客户数据分散", "销售预测依赖手工汇总"],
                "inferred": [{"text": "跨区域协同效率偏低", "confidence": "推断"}],
                "to_verify": ["现有系统替换成本", "一线团队接受度"],
            },
            "competitive_overview": {
                "competitors": [{"name": "现有自研系统", "status": "中等威胁", "reason": "迁移成本低", "our_advantage": "产品成熟度和持续服务", "our_weakness": "初始投入更高", "confidence": "推断"}],
                "advantages": ["集团型组织实践成熟", "移动端和销售过程能力完整"],
                "weaknesses": ["价格敏感度较高", "集成工作量待评估"],
            },
            "open_questions": {
                "risks": [{"severity": "高", "risk": "预算尚未批复", "impact": "可能推迟签约", "trigger": "财务未在八月底前审批", "mitigation": "补齐 ROI 和分阶段投入方案"}],
                "questions": [{"question": "最终预算由谁拍板？", "why": "决定决策链和推进节奏", "confidence": "未知"}],
                "largest_gap": "财务审批人与采购流程尚未确认。",
                "data_alerts": ["会议纪要因权限不足未读取", "外部信息与 CRM 注册地址存在差异，需核对"],
                "actions": [
                    {"action": "核对预算审批流程", "purpose": "确认最终拍板人与批复节点", "timing": "下次项目沟通前", "owner_or_role": "客户经理", "confidence": "确认"},
                    {"action": "补齐财务与采购角色", "purpose": "降低决策链覆盖风险", "timing": "方案定稿前", "owner_or_role": "客户经理", "confidence": "推断"},
                    {"action": "确认接口范围", "purpose": "评估实施工作量和硬门槛", "timing": "技术评审前", "owner_or_role": "售前顾问", "confidence": "确认"},
                ],
            },
        },
        "references": {
            "sources": ["CRM 客户、商机、联系人和销售记录", "客户记忆", "必要外部情报"],
            "confidence_note": "确认：有 CRM、客户原话或明确事件；推断：有行为证据；未知：当前没有充分证据。",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="按固定模板渲染标准版客户简报")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="briefing_facts_bundle JSON 文件")
    source.add_argument("--mock", action="store_true", help="使用内置模拟数据生成预览")
    parser.add_argument("--output", type=Path, required=True, help="输出 HTML 文件")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="正式 HTML 模板")
    parser.add_argument("--forbid-text", action="append", default=[], help="禁止残留的旧客户或样例文字，可重复传入")
    args = parser.parse_args()

    if args.mock:
        bundle = mock_bundle()
    else:
        try:
            bundle = json.loads(args.input.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: 无法读取事实包：{exc}", file=sys.stderr)
            return 2
        if not isinstance(bundle, dict):
            print("ERROR: briefing_facts_bundle 顶层必须是 JSON 对象", file=sys.stderr)
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
