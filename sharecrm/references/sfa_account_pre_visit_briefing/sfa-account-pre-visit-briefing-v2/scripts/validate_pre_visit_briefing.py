#!/usr/bin/env python3
"""Validate a rendered pre-visit customer briefing HTML file."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


TEMPLATE_ID = "sfa-pre-visit-briefing-v2"
REQUIRED_IDS = {"report-title", "readiness-card", "command-strip", "alerts-panel", "actions-panel"}
RAW_API_NAMES = {
    "AccountObj",
    "NewOpportunityObj",
    "ContactObj",
    "ActiveRecordObj",
    "ActivityTodoObj",
    "MethodologyTaskObj",
    "RequirementObj",
    "ActivityQuestionObj",
    "ScheduleObj",
    "AIMeetingObj",
    "AIMeetingChunkObj",
    "CheckinsObj",
    "CompetitiveLinesObj",
    "ContractObj",
    "SalesOrderObj",
    "PaymentObj",
    "CasesObj",
}
FORBIDDEN_TEMPLATE_LABELS = {
    "Briefing Pro",
    "READY",
    "3 steps",
    "Customer Health",
    "Report Map",
    "Memory",
    "memory",
    "客户记忆",
    "记忆状态",
    "客户 Memory",
    "Gatekeeper",
    "Coach",
    "E1",
    "E2",
    "E3",
    "E4",
}


class PreVisitHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, set[str]]] = []
        self.ids: set[str] = set()
        self.class_counts: Counter[str] = Counter()
        self.template_ids: list[str] = []
        self.template_versions: list[str] = []
        self.modes: list[str] = []
        self.visible_text: list[str] = []
        self.external_assets: list[str] = []
        self.tab_targets: list[str] = []
        self.tab_ids: list[str] = []
        self.tab_labels: list[str] = []
        self._active_tab_label: list[str] | None = None
        self.unwrapped_tables = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        classes = set(attr_map.get("class", "").split())
        self.class_counts.update(classes)

        if element_id := attr_map.get("id"):
            self.ids.add(element_id)
        if template_id := attr_map.get("data-template-id"):
            self.template_ids.append(template_id)
        if version := attr_map.get("data-template-version"):
            self.template_versions.append(version)
        if mode := attr_map.get("data-briefing-mode"):
            self.modes.append(mode)
        if controls := attr_map.get("aria-controls"):
            self.tab_targets.append(controls)
        if tag == "button" and attr_map.get("role") == "tab":
            if element_id := attr_map.get("id"):
                self.tab_ids.append(element_id)
            self._active_tab_label = []

        if tag == "table" and not any("table-wrap" in parent_classes for _, parent_classes in self.stack):
            self.unwrapped_tables += 1

        for attr_name in ("src", "href"):
            value = attr_map.get(attr_name, "").strip()
            if value and not value.startswith("#"):
                self.external_assets.append(value)

        self.stack.append((tag, classes))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self._active_tab_label is not None:
            self.tab_labels.append("".join(self._active_tab_label).strip())
            self._active_tab_label = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if any(tag in {"style", "script"} for tag, _ in self.stack):
            return
        value = data.strip()
        if value:
            self.visible_text.append(value)
            if self._active_tab_label is not None:
                self._active_tab_label.append(value)


def validate_html(html_text: str, forbidden_text: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    parser = PreVisitHTMLParser()
    parser.feed(html_text)

    if re.search(r"\{\{[^{}]+\}\}", html_text):
        errors.append("存在未替换的模板占位符")
    if TEMPLATE_ID not in parser.template_ids:
        errors.append(f"缺少正式模板标识 {TEMPLATE_ID}")
    if "2.0" not in parser.template_versions:
        errors.append("HTML 模板版本不是 2.0")

    mode = parser.modes[0] if parser.modes else ""
    if mode not in {"lite", "normal", "full"}:
        errors.append("data-briefing-mode 必须是 lite、normal 或 full")

    missing_ids = sorted(REQUIRED_IDS - parser.ids)
    if missing_ids:
        errors.append("缺少固定节点：" + "、".join(missing_ids))
    if parser.class_counts["command-item"] != 4:
        errors.append(f"关键命令条必须恰好 4 项，当前为 {parser.class_counts['command-item']} 项")
    if parser.class_counts["readiness-ring"] != 1:
        errors.append("必须保留一个环形综合就绪度")
    if parser.class_counts["post-visit-check"] < 1:
        errors.append("必须保留至少一项可勾选的拜访后行动")

    if mode in {"normal", "full"}:
        for required_id in ("score-board", "supplemental-tabs", "people-panel", "pain-panel", "post-visit-panel", "quality-panel"):
            if required_id not in parser.ids:
                errors.append(f"{mode} 模式缺少节点：{required_id}")
        if not parser.tab_ids or parser.tab_ids[-1] != "quality-tab":
            errors.append(f"{mode} 模式的“数据质量”必须是最后一个页签")
        if not parser.tab_labels or parser.tab_labels[-1] != "数据质量":
            errors.append(f"{mode} 模式最后一个页签必须命名为“数据质量”")
    if mode == "full":
        for required_id in ("competition-panel", "history-panel"):
            if required_id not in parser.ids:
                errors.append(f"full 模式缺少节点：{required_id}")
    if mode == "lite":
        for required_id in ("lite-post-visit", "lite-source"):
            if required_id not in parser.ids:
                errors.append(f"lite 模式缺少节点：{required_id}")
        if "supplemental-tabs" in parser.ids:
            errors.append("lite 模式不应输出补充信息页签")

    if "timeline-panel" in parser.ids:
        for required_id in ("timeline-summary-view", "timeline-detail-view"):
            if required_id not in parser.ids:
                errors.append(f"博弈编年缺少视图：{required_id}")
        if parser.class_counts["timeline-view-button"] != 2:
            errors.append("博弈编年必须恰好提供“摘要 / 明细”两个切换按钮")

    missing_targets = sorted(set(parser.tab_targets) - parser.ids)
    if missing_targets:
        errors.append("页签指向不存在的面板：" + "、".join(missing_targets))
    if parser.unwrapped_tables:
        errors.append(f"存在 {parser.unwrapped_tables} 个未放入 .table-wrap 的表格")
    if parser.external_assets:
        errors.append("存在外部资源依赖：" + "、".join(parser.external_assets))

    visible_text = " ".join(parser.visible_text)
    for label in sorted(FORBIDDEN_TEMPLATE_LABELS):
        if label in visible_text:
            errors.append(f"存在未中文化的模板标签：{label}")
    for api_name in sorted(RAW_API_NAMES):
        if re.search(rf"\b{re.escape(api_name)}\b", visible_text):
            errors.append(f"用户可见区域包含 apiName：{api_name}")
    for required_text in ("数据覆盖", "参考来源", "置信度说明"):
        if required_text not in visible_text:
            errors.append(f"缺少质量字段：{required_text}")
    for required_text in ("拜访目标", "最大风险", "推荐打法", "最关键的人", "拜访后行动"):
        if required_text not in visible_text:
            errors.append(f"缺少结构化会前或会后字段：{required_text}")
    if not any(status in visible_text for status in ("已读取", "无数据", "权限不足", "未触发查询", "查询失败")):
        errors.append("数据覆盖未使用统一查询状态")

    css_checks = {
        "移动端断点": "@media (max-width: 640px)",
        "横向页签滚动": "overflow-x: auto",
        "移动端单列": "grid-template-columns: 1fr",
        "动态高度": "height: auto",
        "长文本换行": "overflow-wrap: break-word",
        "博弈视图切换": "timeline-view-button",
        "会后行动清单": "post-visit-list",
    }
    for label, snippet in css_checks.items():
        if snippet not in html_text:
            errors.append(f"缺少{label}规则")

    for value in forbidden_text or []:
        if value and value in visible_text:
            errors.append(f"存在禁止残留内容：{value}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验见客前客户简报 HTML")
    parser.add_argument("html", type=Path, help="待校验的 HTML 文件")
    parser.add_argument("--forbid-text", action="append", default=[], help="禁止残留的旧客户或样例内容，可重复传入")
    args = parser.parse_args()

    errors = validate_html(args.html.read_text(encoding="utf-8"), args.forbid_text)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"HTML validation passed: {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
