#!/usr/bin/env python3
"""Validate a rendered standard customer briefing HTML file."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


TEMPLATE_ID = "sfa-standard-briefing-v3"
REQUIRED_SECTION_IDS = {
    "overview",
    "profile",
    "decision-map",
    "timeline",
    "opportunity",
    "pain",
    "competition",
    "open-questions",
    "next-actions",
    "data-quality",
}
EXPECTED_TAB_IDS = [
    "overview",
    "profile",
    "decision-map",
    "timeline",
    "opportunity",
    "pain",
    "competition",
    "open-questions",
    "next-actions",
    "data-quality",
]
FORBIDDEN_TEMPLATE_LABELS = {
    "Customer 360 Intelligence",
    "Account Intelligence Report",
    "Customer Health",
    "Report Map",
    "Memory",
    "memory",
    "客户记忆",
    "记忆状态",
    "客户 Memory",
    "IT 现状",
    "REF",
}
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


class BriefingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, set[str]]] = []
        self.ids: set[str] = set()
        self.template_ids: list[str] = []
        self.preview_modes: list[str] = []
        self.visible_text: list[str] = []
        self.external_assets: list[str] = []
        self.unwrapped_tables = 0
        self.identity_labels: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        classes = set(attr_map.get("class", "").split())

        if element_id := attr_map.get("id"):
            self.ids.add(element_id)
        if template_id := attr_map.get("data-template-id"):
            self.template_ids.append(template_id)
        if preview_mode := attr_map.get("data-preview"):
            self.preview_modes.append(preview_mode)

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
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if any(tag in {"style", "script"} for tag, _ in self.stack):
            return
        stripped = data.strip()
        if stripped:
            self.visible_text.append(stripped)
            if any("identity-label" in classes for _, classes in self.stack):
                self.identity_labels.append(stripped)


def validate_html(html_text: str, forbidden_text: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    parser = BriefingHTMLParser()
    parser.feed(html_text)

    if re.search(r"\{\{[^{}]+\}\}", html_text):
        errors.append("存在未替换的模板占位符")
    if TEMPLATE_ID not in parser.template_ids:
        errors.append(f"缺少正式模板标识 {TEMPLATE_ID}")

    tab_ids = re.findall(r'<button[^>]+role="tab"[^>]+data-tab="([^"]+)"', html_text)
    if not tab_ids:
        errors.append("缺少顶部横向页签导航")
    else:
        expected_tab_ids = EXPECTED_TAB_IDS.copy()
        if "history-financial" in tab_ids:
            expected_tab_ids.insert(-1, "history-financial")
        if tab_ids != expected_tab_ids:
            errors.append("页签顺序或结构不符合标准版要求")
    if not re.search(r'data-tab="data-quality"[^>]*>\s*数据质量\s*</button>', html_text):
        errors.append("缺少独立的数据质量页签")
    if "数据来源与置信度" not in " ".join(parser.visible_text):
        errors.append("数据质量页签缺少来源与置信度内容")
    if not re.search(r'data-tab="decision-map"[^>]*>\s*决策圈图谱\s*</button>', html_text):
        errors.append("缺少合并后的决策圈图谱页签")
    if not re.search(r'data-tab="next-actions"[^>]*>\s*后续建议动作\s*</button>', html_text):
        errors.append("缺少独立的后续建议动作页签")
    if re.search(r'<span[^>]+class="[^"]*\bnum\b[^"]*"', html_text):
        errors.append("页签内容标题仍包含序号徽标")

    missing_sections = sorted(REQUIRED_SECTION_IDS - parser.ids)
    if missing_sections:
        errors.append("缺少固定章节：" + "、".join(missing_sections))

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
    for label in parser.identity_labels:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", label):
            errors.append(f"基本信息字段显示了 apiName：{label}")

    for required_text in ("数据覆盖", "参考来源", "置信度说明", "数据截止"):
        if required_text not in visible_text:
            errors.append(f"缺少质量字段：{required_text}")

    if not any(status in visible_text for status in ("已读取", "无数据", "权限不足", "未触发查询", "查询失败")):
        errors.append("数据覆盖未使用统一查询状态")

    css_checks = {
        "移动端断点": "@media (max-width: 760px)",
        "窄屏断点": "@media (max-width: 420px)",
        "页面横向溢出保护": "overflow-x: hidden",
        "移动端动态高度": "max-height: none",
        "移动端长文本换行": "overflow-wrap: break-word",
        "移动端页签触控滚动": "-webkit-overflow-scrolling: touch",
        "表格横向滚动": "overflow-x: auto",
        "移动端单列": "grid-template-columns: 1fr",
    }
    for label, snippet in css_checks.items():
        if snippet not in html_text:
            errors.append(f"缺少{label}规则")

    if forbidden_text:
        for value in forbidden_text:
            if value and value in visible_text:
                errors.append(f"存在禁止残留内容：{value}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验标准版客户简报 HTML")
    parser.add_argument("html", type=Path, help="待校验的 HTML 文件")
    parser.add_argument(
        "--forbid-text",
        action="append",
        default=[],
        help="禁止出现在用户可见区域的旧客户或样例内容，可重复传入",
    )
    args = parser.parse_args()

    html_text = args.html.read_text(encoding="utf-8")
    errors = validate_html(html_text, args.forbid_text)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"HTML validation passed: {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
