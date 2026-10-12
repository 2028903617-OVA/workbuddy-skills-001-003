#!/usr/bin/env python3
"""
build-html-report.py

将 sfa-leads-diagnosis 的 Markdown 诊断正文渲染为 HTML 报告。

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


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ASSETS_HTML = SKILL_DIR / "assets" / "output.html"

REQUIRED_SECTIONS = [
    "## 概要",
    "## 一、核心诊断结论",
    "## 二、全局诊断结果",
    "## 三、关键缺失项",
    "## 四、跟进策略",
    "## 五、跟进建议",
]

PRIORITY_TAG = {"P0": "tag-p0", "P1": "tag-p1", "P2": "tag-p2"}
ALLOWED_STRATEGY_VERDICTS = {"补齐关键信息", "培育推进", "转化推进"}


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
    rich_pattern = rf"(?m)^-\s*\*\*{re.escape(label)}[:：]\*\*\s*(.*?)\s*$"
    rich_match = re.search(rich_pattern, section)
    if rich_match:
        return _clean_inline(rich_match.group(1))

    pattern = rf"(?m)^-\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?[:：]\s*(.*?)\s*$"
    match = re.search(pattern, section)
    if match:
        return _clean_inline(match.group(1))

    if required:
        raise ValidationError(f"[校验失败] 缺少字段：{label}")
    return ""


def _extract_free_bullet(section: str) -> str:
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|"):
            break
        if stripped.startswith("- "):
            return _clean_inline(stripped[2:])
    return ""


def _clean_preserve_markup(text: str) -> str:
    value = text.strip()
    value = value.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    return value.strip()


def _parse_meta(section: str) -> dict[str, str]:
    return {
        "lead_name": _extract_bullet_value(section, "线索名称"),
        "diagnosis_date": _extract_bullet_value(section, "诊断日期"),
        "current_stage": _extract_bullet_value(section, "当前阶段"),
        "ai_stage": _extract_bullet_value(section, "AI判定阶段"),
        "ai_stage_reason": _extract_bullet_value(section, "AI阶段判断说明"),
        "score": _extract_bullet_value(section, "综合评分"),
        "score_summary": _extract_bullet_value(section, "综合评级"),
        "requirement_description": _extract_bullet_value(section, "需求描述"),
    }


def _parse_list_items(section: str, label: str) -> list[str]:
    lines = section.splitlines()
    start_index = None
    label_pattern = re.compile(
        rf"^-\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?[:：]\s*$"
    )

    for index, line in enumerate(lines):
        if label_pattern.match(line.strip()):
            start_index = index + 1
            break

    if start_index is None:
        raise ValidationError(f"[校验失败] 缺少列表字段：{label}")

    items = []
    for line in lines[start_index:]:
        stripped = line.strip()
        if not stripped:
            continue
        if not line.startswith(("  ", "\t")):
            break

        item_match = re.match(r"^[-*]\s+(.+)$", stripped)
        if not item_match:
            raise ValidationError(f"[校验失败] {label} 列表项格式非法：{stripped}")
        items.append(_clean_inline(item_match.group(1)))

    if not items:
        raise ValidationError(f"[校验失败] {label} 不能为空")
    return items


def _parse_core_conclusion(section: str) -> dict[str, Any]:
    return {
        "one_liner": _extract_bullet_value(section, "一句话结论"),
        "conversion_elements": _parse_list_items(section, "转化三要素"),
        "core_strategy": _extract_bullet_value(section, "核心跟进策略"),
        "key_actions": _parse_list_items(section, "关键行动项"),
    }


def _extract_table_after(text: str, marker: str, expected_columns: int, heading: str) -> list[list[str]]:
    idx = text.find(marker)
    if idx == -1:
        raise ValidationError(f"[校验失败] {heading} 缺少标记：{marker}")
    remaining = text[idx + len(marker):].lstrip()
    return _extract_table(remaining, heading, expected_columns)


def _parse_global_diagnosis(section: str) -> dict[str, Any]:
    score_match = re.search(r"\*\*(?:评分总分|评分维度总分)\*\*[:：]\s*(.+)", section)
    if not score_match:
        raise ValidationError("[校验失败] 全局诊断结果缺少评分总分")
    rows = _extract_table_after(section, score_match.group(0), 3, "全局诊断结果-评分维度")
    data_rows = rows[1:]
    if not data_rows:
        raise ValidationError("[校验失败] 全局诊断结果至少需要一个评分维度")
    parsed = [
        {
            "dimension": _clean_inline(row[0]),
            "score": _clean_inline(row[1]),
            "evidence": _clean_inline(row[2]),
        }
        for row in data_rows
    ]
    return {
        "total": _clean_inline(score_match.group(1)),
        "rows": parsed,
    }


def _parse_missing_items(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "关键缺失项", 4)
    parsed = []
    for idx, row in enumerate(rows[1:]):
        missing, status, phenomenon, deep = row
        if not any(_clean_inline(cell) for cell in row):
            continue
        parsed.append(
            {
                "missing": _clean_inline(missing),
                "status": _clean_inline(status),
                "phenomenon": _clean_inline(phenomenon),
                "deep": _clean_inline(deep),
            }
        )
    if not parsed:
        raise ValidationError("[校验失败] 关键缺失项不能为空")
    return parsed


def _parse_missing_summary(section: str) -> str:
    return _extract_free_bullet(section)


def _parse_strategy_verdict(section: str) -> dict[str, str]:
    if "### 4.1 策略裁决" not in section:
        raise ValidationError("[校验失败] 跟进策略缺少小节：### 4.1 策略裁决")

    verdict_section = section.split("### 4.1 策略裁决", 1)[1]
    if "### 4.2 当前打法 vs 建议打法" in verdict_section:
        verdict_section = verdict_section.split("### 4.2 当前打法 vs 建议打法", 1)[0]

    verdict = _extract_bullet_value(verdict_section, "裁决结论")
    verdict = verdict.lstrip("*").strip().strip("<>").strip()
    if verdict not in ALLOWED_STRATEGY_VERDICTS:
        raise ValidationError("[校验失败] 裁决结论必须为：补齐关键信息 / 培育推进 / 转化推进")

    return {
        "verdict": verdict,
        "reason": _extract_bullet_value(verdict_section, "核心原因"),
    }


def _parse_strategy_tactics(section: str) -> dict[str, Any]:
    marker = "### 4.2 当前打法 vs 建议打法"
    if marker not in section:
        raise ValidationError("[校验失败] 跟进策略缺少小节：### 4.2 当前打法 vs 建议打法")

    tactic_section = section.split(marker, 1)[1]
    rows = _extract_table(tactic_section, "当前打法 vs 建议打法", 3)
    header_current, header_arrow, header_suggested = rows[0]
    parsed = []
    for row in rows[1:]:
        current, _arrow, suggested = row
        if not any(_clean_inline(cell) for cell in row):
            continue
        parsed.append(
            {
                "current": _clean_preserve_markup(current),
                "suggested": _clean_preserve_markup(suggested),
            }
        )
    if not parsed:
        raise ValidationError("[校验失败] 当前打法 vs 建议打法不能为空")
    return {
        "current_header": _clean_inline(header_current),
        "arrow_header": _clean_inline(header_arrow) or "→",
        "suggested_header": _clean_inline(header_suggested),
        "rows": parsed,
    }


def _parse_actions(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "跟进建议", 6)
    parsed = []
    for idx, row in enumerate(rows[1:]):
        priority, action, purpose, timing, owner, done_criteria = row
        if not any(_clean_inline(cell) for cell in row):
            continue
        if priority not in PRIORITY_TAG:
            raise ValidationError(f"[校验失败] 跟进建议第 {idx + 1} 行优先级必须为 P0/P1/P2")
        parsed.append(
            {
                "priority": priority,
                "action": _clean_inline(action),
                "purpose": _clean_inline(purpose),
                "timing": _clean_inline(timing),
                "owner": _clean_inline(owner),
                "done_criteria": _clean_inline(done_criteria),
            }
        )
    if not parsed:
        raise ValidationError("[校验失败] 跟进建议不能为空")
    return parsed


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
        "missing_summary": _parse_missing_summary(sections["## 三、关键缺失项"]),
        "missing_items": _parse_missing_items(sections["## 三、关键缺失项"]),
        "strategy_verdict": _parse_strategy_verdict(sections["## 四、跟进策略"]),
        "strategy_tactics": _parse_strategy_tactics(sections["## 四、跟进策略"]),
        "actions": _parse_actions(sections["## 五、跟进建议"]),
    }


def _global_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        out.append(
            "<tr>"
            f"<td>{_esc(row['dimension'])}</td>"
            f"<td>{_esc(row['score'])}</td>"
            f"<td>{_esc(row['evidence'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _missing_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        out.append(
            "<tr>"
            f"<td>{_esc(row['missing'])}</td>"
            f"<td>{_esc(row['status'])}</td>"
            f"<td>{_esc(row['phenomenon'])}</td>"
            f"<td>{_esc(row['deep'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _render_inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return escaped.replace("\n", "<br>")


def _strategy_tactic_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        out.append(
            "<tr>"
            f"<td>{_render_inline_markup(row['current'])}</td>"
            "<td>→</td>"
            f"<td>{_render_inline_markup(row['suggested'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _action_rows(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        out.append(
            "<tr>"
            f"<td><span class=\"tag {PRIORITY_TAG[row['priority']]}\">{_esc(row['priority'])}</span></td>"
            f"<td>{_esc(row['action'])}</td>"
            f"<td>{_esc(row['purpose'])}</td>"
            f"<td>{_esc(row['timing'])}</td>"
            f"<td>{_esc(row['owner'])}</td>"
            f"<td>{_esc(row['done_criteria'])}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _rich_list_items(items: list[str]) -> str:
    return "\n".join(f"<li>{_esc(item)}</li>" for item in items)


def _split_score_value(score: str) -> tuple[str, str]:
    value = score.strip()
    if "/" not in value:
        return value, ""
    main, total = value.split("/", 1)
    return main.strip(), total.strip()


def _parse_score_fraction(score: str) -> tuple[float, int]:
    match = re.match(r"^\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*$", score)
    if not match:
        return (1.0, sys.maxsize)
    current = float(match.group(1))
    total = float(match.group(2))
    if total <= 0:
        return (1.0, sys.maxsize)
    return (current / total, int(current))


def _join_labels(labels: list[str]) -> str:
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]}与{labels[1]}"
    return f"{'、'.join(labels[:-1])}与{labels[-1]}"


def _global_summary_text(global_diag: dict[str, Any]) -> str:
    rows = global_diag["rows"]
    low_score_labels = [row["dimension"] for row in rows if _parse_score_fraction(row["score"])[0] < 0.5]
    summary = f"评分维度总分 {_esc(global_diag['total'])}，共覆盖 {len(rows)} 个评分维度。"
    if low_score_labels:
        return f"{summary} 当前相对短板集中在{_join_labels(low_score_labels)}。"
    return summary


def _missing_summary_text(data: dict[str, Any]) -> str:
    if data["missing_summary"]:
        return data["missing_summary"]
    first_item = data["missing_items"][0]
    return f"{first_item['missing']}。{first_item['deep']}"


def _rating_badge_class(score_summary: str) -> str:
    value = score_summary.strip().upper()
    if value.startswith("A"):
        return "rating-badge-a"
    if value.startswith("B"):
        return "rating-badge-b"
    if value.startswith("C"):
        return "rating-badge-c"
    return "rating-badge-default"


def _rating_badge_text(score_summary: str) -> str:
    value = score_summary.strip()
    if value.startswith("A"):
        return "建议转商机"
    if value.startswith("B"):
        return "积极跟进"
    if value.startswith("C"):
        return "月度培育并复评"
    if value.startswith("D"):
        return "降低投入或关闭"
    return value


def _render(data: dict[str, Any], style_css: str) -> str:
    meta = data["meta"]
    core = data["core_conclusion"]
    global_diag = data["global_diagnosis"]
    title = meta["lead_name"] or "线索诊断报告"
    score_main, score_total = _split_score_value(meta["score"])
    score_total_html = f"<small>/{_esc(score_total)}</small>" if score_total else ""
    strategy = data["strategy_verdict"]
    strategy_tactics = data["strategy_tactics"]
    rating_badge_class = _rating_badge_class(meta["score_summary"])
    rating_badge_text = _rating_badge_text(meta["score_summary"])
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>{_esc(title)} - 线索诊断报告</title>
<style>
{style_css}
</style>
</head>
<body>
<div class=\"cover\">
  <div class=\"cover-inner\">
    <div class=\"cover-head\">
      <div>
        <div class=\"eyebrow\">Leads Diagnosis Report</div>
        <h1>{_esc(title)}</h1>
        <div class=\"subtitle\">基于线索资料、评分结果与跟进记录生成，用于支持线索判断与推进决策。</div>
      </div>
      <div class=\"score-box\">
        <div class=\"score-num\">{_esc(score_main)}{score_total_html}</div>
        <div class=\"score-label\">综合评分</div>
      </div>
    </div>
    <dl class=\"cover-meta\">
      <div><dt>诊断日期</dt><dd>{_esc(meta['diagnosis_date'])}</dd></div>
      <div><dt>当前阶段</dt><dd>{_esc(meta['current_stage'])}</dd></div>
      <div><dt>AI判定阶段</dt><dd>{_esc(meta['ai_stage'])}</dd></div>
      <div><dt>综合评级</dt><dd><span class=\"rating-badge {rating_badge_class}\"><span class=\"rating-badge-label\">评级</span><span>{_esc(rating_badge_text)}</span></span></dd></div>
    </dl>
    <div class=\"stage-tag sales\">🧭 AI阶段判断说明：{_esc(meta['ai_stage_reason'])}</div>
    <div class=\"requirement-note\"><strong>需求描述：</strong>{_esc(meta['requirement_description'])}</div>
  </div>
</div>
<div class=\"layout\">
  <aside class=\"toc\">
    <div class=\"toc-title\">目录</div>
    <a href=\"#section-1\" class=\"active\">一、核心诊断结论</a>
    <a href=\"#section-2\">二、全局诊断结果</a>
    <a href=\"#section-3\">三、关键缺失项</a>
    <a href=\"#section-4\">四、跟进策略</a>
    <a href=\"#section-5\">五、跟进建议</a>
  </aside>
  <main class=\"content\">
    <section id=\"section-1\">
      <div class=\"section-title\"><span class=\"section-index\">一</span>核心诊断结论</div>
      <div class=\"summary-block\">
        <h3>一句话结论</h3>
        <p>{_esc(core['one_liner'])}</p>
      </div>
      <div class=\"card\">
        <div class=\"note-label\">转化三要素</div>
        <ul class=\"rich-list\">
          {_rich_list_items(core['conversion_elements'])}
        </ul>
        <div class=\"note-label\">核心跟进策略</div>
        <p>{_esc(core['core_strategy'])}</p>
        <div class=\"note-label\">关键行动项</div>
        <ul class=\"rich-list\">
          {_rich_list_items(core['key_actions'])}
        </ul>
      </div>
    </section>

    <section id=\"section-2\">
      <div class=\"section-title\"><span class=\"section-index\">二</span>全局诊断结果</div>
      <div class=\"summary-block\">
        <h3>评分维度概览</h3>
        <p>{_global_summary_text(global_diag)}</p>
      </div>
      <div class=\"card\">
        <p><strong>评分维度总分：</strong>{_esc(global_diag['total'])}</p>
      </div>
      <div class=\"table-wrap\">
        <table>
          <thead><tr><th>维度</th><th>评分</th><th>评分依据</th></tr></thead>
          <tbody>
            {_global_rows(global_diag['rows'])}
          </tbody>
        </table>
      </div>
    </section>

    <section id=\"section-3\">
      <div class=\"section-title\"><span class=\"section-index\">三</span>关键缺失项</div>
      <div class=\"summary-block\">
        <h3>当前最需要补齐的判断基础</h3>
        <p>{_esc(_missing_summary_text(data))}</p>
      </div>
      <div class=\"table-wrap\">
        <table>
          <thead><tr><th>缺失项</th><th>当前状态</th><th>表面现象</th><th>深层判断</th></tr></thead>
          <tbody>
            {_missing_rows(data['missing_items'])}
          </tbody>
        </table>
      </div>
    </section>

    <section id=\"section-4\">
      <div class=\"section-title\"><span class=\"section-index\">四</span>跟进策略</div>
      <div class=\"summary-block\">
        <h3>4.1 策略裁决</h3>
        <p><strong>裁决结论：</strong>{_esc(strategy['verdict'])}</p>
        <p><strong>核心原因：</strong>{_esc(strategy['reason'])}</p>
      </div>
      <div class=\"card\">
        <div class=\"note-label\">4.2 当前打法 vs 建议打法</div>
      </div>
      <div class=\"table-wrap\">
        <table>
          <thead><tr><th>{_esc(strategy_tactics['current_header'])}</th><th>{_esc(strategy_tactics['arrow_header'])}</th><th>{_esc(strategy_tactics['suggested_header'])}</th></tr></thead>
          <tbody>
            {_strategy_tactic_rows(strategy_tactics['rows'])}
          </tbody>
        </table>
      </div>
    </section>

    <section id=\"section-5\">
      <div class=\"section-title\"><span class=\"section-index\">五</span>跟进建议</div>
      <div class=\"summary-block\">
        <h3>当前推进要求</h3>
        <p>建议优先补齐决策链、Timeline 和真实需求成熟度，再决定是否升级投入强度，避免长期处于“有兴趣但不落地”的低效推进状态。</p>
      </div>
      <div class=\"table-wrap\">
        <table>
          <thead><tr><th>优先级</th><th>动作</th><th>目的</th><th>时间</th><th>负责人/对象</th><th>完成标志</th></tr></thead>
          <tbody>
            {_action_rows(data['actions'])}
          </tbody>
        </table>
      </div>
    </section>

    <div class=\"foot-note\"><strong>说明：</strong>本报告遵循 SFA 线索诊断标准（sfa-leads-diagnosis），正文中的判断仅用于诊断梳理，需后续验证。</div>
  </main>
</div>
<script>
  const links = document.querySelectorAll('.toc a');
  const sections = [...document.querySelectorAll('main section')];
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
</body>
</html>
"""


MARKDOWN_SCHEMA_HINT = """\
输入必须是符合 `references/output_template.md` 固定结构的 Markdown，至少包含以下章节：

## 概要
- 线索名称：
- 诊断日期：<当前日期>
- 当前阶段：
- AI判定阶段：
- AI阶段判断说明：
- 综合评分：
- 综合评级：
- 需求描述：

## 一、核心诊断结论
- 一句话结论：
- 转化三要素：
  - <行动目标型三要素1>
  - <行动目标型三要素2>
  - <行动目标型三要素3>
- 核心跟进策略:
- 关键行动项：
  - <关键行动项1>
  - <关键行动项2>
  - <关键行动项3>

## 二、全局诊断结果
**评分总分**：<选定评分来源返回的综合得分>
| 评分维度 | 评分 | 评分依据（事实 / 判断 / 待确认问题 / 来源） |

## 三、关键缺失项
- 一句话描述最需要补齐的缺失项和原因（推荐填写，用于报告摘要）
| 缺失项 | 当前状态 | 表面现象 | 深层判断 |

## 四、跟进策略
### 4.1 策略裁决
- **裁决结论：**<补齐关键信息 / 培育推进 / 转化推进>
- **核心原因：**

### 4.2 当前打法 vs 建议打法
| 当前打法：<一句话概括当前仍在沿用的打法> | → | 建议打法：<一句话概括新的赢单主线，对应主打法类型> |

## 五、跟进建议
| 优先级 | 动作 | 目的 | 时间 | 负责人/对象 | 完成标志 |
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="渲染线索诊断 HTML 报告")
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
