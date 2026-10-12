#!/usr/bin/env python3
"""Validate a rendered team handover briefing HTML file."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


TEMPLATE_ID = "sfa-account-handover-briefing-v1"
TEMPLATE_VERSION = "1.0"
VALID_MODES = {"standard", "full"}
REQUIRED_IDS = {
    "handover-quality-signals",
    "handover-summary",
    "handover-overview",
    "handover-history",
    "handover-notes",
    "data-quality",
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
FORBIDDEN_LABELS = {"Memory", "memory", "客户 Memory", "客户记忆", "记忆状态", "Gatekeeper", "Coach", "full 模式"}


class HandoverHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, set[str]]] = []
        self.ids: set[str] = set()
        self.class_counts: Counter[str] = Counter()
        self.template_ids: list[str] = []
        self.template_versions: list[str] = []
        self.modes: list[str] = []
        self.preview_modes: list[str] = []
        self.tab_targets: list[str] = []
        self.tab_slices: list[str] = []
        self.visible_text: list[str] = []
        self.external_assets: list[str] = []
        self.style_count = 0
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
        if mode := attr_map.get("data-report-mode"):
            self.modes.append(mode)
        if preview := attr_map.get("data-preview"):
            self.preview_modes.append(preview)
        if target := attr_map.get("data-tab-target"):
            self.tab_targets.append(target)
        if tab_slice := attr_map.get("data-tab-slice"):
            self.tab_slices.append(tab_slice)
        if tag == "style":
            self.style_count += 1

        if tag == "table":
            wrapped = any(
                any(class_name == "table-wrap" or class_name.endswith("-table-wrap") for class_name in parent_classes)
                for _, parent_classes in self.stack
            )
            if not wrapped:
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
        value = data.strip()
        if value:
            self.visible_text.append(value)


def validate_html(html_text: str, forbidden_text: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    parser = HandoverHTMLParser()
    parser.feed(html_text)

    if re.search(r"\{\{[^{}]+\}\}", html_text):
        errors.append("存在未替换的模板占位符")
    if TEMPLATE_ID not in parser.template_ids:
        errors.append(f"缺少正式模板标识 {TEMPLATE_ID}")
    if TEMPLATE_VERSION not in parser.template_versions:
        errors.append(f"HTML 模板版本不是 {TEMPLATE_VERSION}")

    mode = parser.modes[0] if parser.modes else ""
    if mode not in VALID_MODES:
        errors.append("data-report-mode 必须是 standard 或 full")

    missing_ids = sorted(REQUIRED_IDS - parser.ids)
    if missing_ids:
        errors.append("缺少固定节点：" + "、".join(missing_ids))
    if mode == "full" and "history-financial" not in parser.ids:
        errors.append("full 模式缺少历史合作、财务与客户健康模块")
    if mode == "standard" and "history-financial" in parser.ids:
        errors.append("standard 模式不应输出历史合作、财务与客户健康模块")

    missing_tab_slices = sorted(set(parser.tab_targets) - set(parser.tab_slices))
    if missing_tab_slices:
        errors.append("页签没有对应内容区：" + "、".join(missing_tab_slices))
    if "quality" not in parser.tab_targets:
        errors.append("缺少独立的数据质量页签")
    elif parser.tab_targets[-1] != "quality":
        errors.append("数据质量页签必须位于最后")
    if parser.unwrapped_tables:
        errors.append(f"存在 {parser.unwrapped_tables} 个未放入横向滚动容器的表格")
    if parser.external_assets:
        errors.append("存在外部资源依赖：" + "、".join(parser.external_assets))
    if parser.style_count < 1:
        errors.append("最终 HTML 未内联 CSS")

    visible_text = " ".join(parser.visible_text)
    for label in sorted(FORBIDDEN_LABELS):
        if label in visible_text:
            errors.append(f"存在未中文化的模板标签：{label}")
    for api_name in sorted(RAW_API_NAMES):
        if re.search(rf"\b{re.escape(api_name)}\b", visible_text):
            errors.append(f"用户可见区域包含 apiName：{api_name}")
    unknown_object_names = sorted(set(re.findall(r"\b[A-Za-z][A-Za-z0-9_]*Obj\b", visible_text)))
    for api_name in unknown_object_names:
        if api_name not in RAW_API_NAMES:
            errors.append(f"用户可见区域包含未映射的对象 apiName：{api_name}")
    for required_text in ("数据覆盖", "参考来源", "置信度说明", "数据截止"):
        if required_text not in visible_text:
            errors.append(f"缺少质量字段：{required_text}")
    if not any(status in visible_text for status in ("已读取", "无数据", "权限不足", "未触发查询", "查询失败")):
        errors.append("数据覆盖未使用统一查询状态")
    if "交接准备度" in visible_text:
        errors.append("存在无统一计算规则的交接准备度展示")

    css_checks = {
        "移动端布局切换": "@media (max-width: 1023px)",
        "窄屏单列": "@media (max-width: 640px)",
        "移动端顶部高度自适应": "max-height: none",
        "移动端顶部状态长文本换行": "white-space: normal",
        "移动端页签独立吸顶": ".brief-tabs {\n    top: 0",
        "横向滚动": "overflow-x: auto",
        "单列网格": "grid-template-columns: 1fr",
    }
    for label, snippet in css_checks.items():
        if snippet not in html_text:
            errors.append(f"缺少{label}规则")

    for value in forbidden_text or []:
        if value and value in visible_text:
            errors.append(f"存在禁止残留内容：{value}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验团队交接简报 HTML")
    parser.add_argument("html", type=Path, help="待校验的 HTML 文件")
    parser.add_argument("--forbid-text", action="append", default=[], help="禁止残留的旧客户或样例内容，可重复传入")
    args = parser.parse_args()

    try:
        html_text = args.html.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: 无法读取 HTML：{exc}", file=sys.stderr)
        return 2

    errors = validate_html(html_text, args.forbid_text)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"HTML validation passed: {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
