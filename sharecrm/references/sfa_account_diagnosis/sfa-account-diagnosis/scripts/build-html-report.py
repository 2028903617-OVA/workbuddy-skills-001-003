#!/usr/bin/env python3
"""
build-html-report.py

将 sfa-account-diagnosis 的 Markdown 客户经营洞察正文渲染为 HTML 报告。

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
    "## 页头摘要",
    "## 一、客户当前状态",
    "## 二、客户真实关注点",
    "## 三、组织突破口",
    "## 四、增长空间",
    "## 五、经营建议",
    "## 附：经营风险提示",
]

EXPECTED_FOCUS_ITEMS = ["表面关注点", "深层驱动", "当前约束", "当前错位"]
EXPECTED_ORG_ITEMS = ["当前入口条线", "杠杆角色", "拍板关键", "隐性阻力", "推荐突破路径"]
EXPECTED_GROWTH_ITEMS = ["当前主机会", "潜在扩展方向", "复制可能性", "战略合作空间", "是否值得追加投入"]
PRIORITY_TAG = {"P0": "tag-p0", "P1": "tag-p1", "P2": "tag-p2"}


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
        raise ValidationError(
            f"[校验失败] {path} 列数应为 {expected_columns}，实际为 {len(cells)}"
        )
    return cells


def _extract_table(section: str, heading: str, expected_columns: int) -> list[list[str]]:
    lines = [line.strip() for line in section.splitlines()]
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
    pattern = rf"(?m)^-\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?[:：]\s*(.+?)\s*$"
    match = re.search(pattern, section)
    if match:
        return _clean_inline(match.group(1))
    if required:
        raise ValidationError(f"[校验失败] 缺少字段：{label}")
    return ""


def _validate_items(rows: list[list[str]], expected: list[str], heading: str) -> None:
    data_rows = rows[1:]
    if len(data_rows) != len(expected):
        raise ValidationError(f"[校验失败] {heading} 必须为 {len(expected)} 行")
    for idx, row in enumerate(data_rows):
        if row[0] != expected[idx]:
            raise ValidationError(
                f"[校验失败] {heading} 第 {idx + 1} 行判断项应为 {expected[idx]}"
            )


def _parse_meta(section: str) -> dict[str, str]:
    return {
        "account_name": _extract_bullet_value(section, "客户名称"),
        "current_status": _extract_bullet_value(section, "当前状态"),
        "owner": _extract_bullet_value(section, "负责人"),
        "account_level": _extract_bullet_value(section, "客户级别"),
        "total_score": _extract_bullet_value(section, "评分总分"),
        "score_conclusion": _extract_bullet_value(section, "评分结论"),
        "temperature": _extract_bullet_value(section, "当前合作温度"),
        "topic": _extract_bullet_value(section, "本轮洞察主题"),
    }


def _parse_status(section: str) -> dict[str, Any]:
    rows = _extract_table(section, "客户当前状态", 5)
    if len(rows) < 2:
        raise ValidationError("[校验失败] 客户当前状态至少需要一个评分维度")
    return {
        "summary": _extract_bullet_value(section, "一句话判断"),
        "tag": _extract_bullet_value(section, "当前状态标签"),
        "rows": [
            {
                "dimension": _clean_inline(row[0]),
                "current": _clean_inline(row[1]),
                "fact": _clean_inline(row[2]),
                "judgement": _clean_inline(row[3]),
                "question": _clean_inline(row[4]),
            }
            for row in rows[1:]
        ],
    }


def _parse_focus(section: str) -> dict[str, Any]:
    rows = _extract_table(section, "客户真实关注点", 4)
    _validate_items(rows, EXPECTED_FOCUS_ITEMS, "客户真实关注点")
    return {
        "summary": _extract_bullet_value(section, "一句话判断"),
        "alignment": _extract_bullet_value(section, "当前我方命中度"),
        "rows": [
            {
                "item": _clean_inline(row[0]),
                "basis": _clean_inline(row[1]),
                "conclusion": _clean_inline(row[2]),
                "impact": _clean_inline(row[3]),
            }
            for row in rows[1:]
        ],
    }


def _parse_org(section: str) -> dict[str, Any]:
    rows = _extract_table(section, "组织突破口", 4)
    _validate_items(rows, EXPECTED_ORG_ITEMS, "组织突破口")
    return {
        "summary": _extract_bullet_value(section, "一句话判断"),
        "rows": [
            {
                "item": _clean_inline(row[0]),
                "basis": _clean_inline(row[1]),
                "conclusion": _clean_inline(row[2]),
                "impact": _clean_inline(row[3]),
            }
            for row in rows[1:]
        ],
    }


def _parse_growth(section: str) -> dict[str, Any]:
    rows = _extract_table(section, "增长空间", 3)
    _validate_items(rows, EXPECTED_GROWTH_ITEMS, "增长空间")
    return {
        "summary": _extract_bullet_value(section, "一句话判断"),
        "rows": [
            {
                "item": _clean_inline(row[0]),
                "conclusion": _clean_inline(row[1]),
                "description": _clean_inline(row[2]),
            }
            for row in rows[1:]
        ],
    }


def _parse_actions(section: str) -> dict[str, Any]:
    rows = _extract_table(section, "经营建议", 5)
    return {
        "strategy": _extract_bullet_value(section, "当前经营策略"),
        "reason": _extract_bullet_value(section, "策略判断说明"),
        "rows": [
            {
                "action": _clean_inline(row[0]),
                "purpose": _clean_inline(row[1]),
                "problem": _clean_inline(row[2]),
                "owner": _clean_inline(row[3]),
                "cadence": _clean_inline(row[4]),
            }
            for row in rows[1:]
        ],
    }


def _parse_risks(section: str) -> list[dict[str, str]]:
    rows = _extract_table(section, "经营风险提示", 5)
    parsed = []
    for idx, row in enumerate(rows[1:]):
        priority, risk, source, impact, direction = row
        if priority not in PRIORITY_TAG:
            raise ValidationError(f"[校验失败] 经营风险提示第 {idx + 1} 行优先级必须为 P0/P1/P2")
        parsed.append(
            {
                "priority": priority,
                "risk": _clean_inline(risk),
                "source": _clean_inline(source),
                "impact": _clean_inline(impact),
                "direction": _clean_inline(direction),
            }
        )
    if not parsed:
        raise ValidationError("[校验失败] 经营风险提示不能为空")
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
        "meta": _parse_meta(sections["## 页头摘要"]),
        "status": _parse_status(sections["## 一、客户当前状态"]),
        "focus": _parse_focus(sections["## 二、客户真实关注点"]),
        "org": _parse_org(sections["## 三、组织突破口"]),
        "growth": _parse_growth(sections["## 四、增长空间"]),
        "actions": _parse_actions(sections["## 五、经营建议"]),
        "risks": _parse_risks(sections["## 附：经营风险提示"]),
    }


def _score_html(total_score: str) -> str:
    value = total_score.strip()
    match = re.match(r"^(?P<main>\d+(?:\.\d+)?)(?:\s*/\s*(?P<den>\d+(?:\.\d+)?))?", value)
    if not match:
        return _esc(value)
    main = match.group("main")
    den = match.group("den")
    return f"{_esc(main)}<small>/{_esc(den)}</small>" if den else _esc(main)


def _rows_status(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        "<tr>"
        f"<td>{_esc(row['dimension'])}</td>"
        f"<td>{_esc(row['current'])}</td>"
        f"<td>{_esc(row['fact'])}</td>"
        f"<td>{_esc(row['judgement'])}</td>"
        f"<td>{_esc(row['question'])}</td>"
        "</tr>"
        for row in rows
    )


def _rows_four_col(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        "<tr>"
        f"<td>{_esc(row['item'])}</td>"
        f"<td>{_esc(row['basis'])}</td>"
        f"<td>{_esc(row['conclusion'])}</td>"
        f"<td>{_esc(row['impact'])}</td>"
        "</tr>"
        for row in rows
    )


def _rows_growth(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        "<tr>"
        f"<td>{_esc(row['item'])}</td>"
        f"<td>{_esc(row['conclusion'])}</td>"
        f"<td>{_esc(row['description'])}</td>"
        "</tr>"
        for row in rows
    )


def _rows_actions(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        "<tr>"
        f"<td>{_esc(row['action'])}</td>"
        f"<td>{_esc(row['purpose'])}</td>"
        f"<td>{_esc(row['problem'])}</td>"
        f"<td>{_esc(row['owner'])}</td>"
        f"<td>{_esc(row['cadence'])}</td>"
        "</tr>"
        for row in rows
    )


def _expansion_seed_label(rows: list[dict[str, str]]) -> str:
    target = next(
        (row for row in rows if row["item"] == "是否值得追加投入"),
        None,
    )
    if not target:
        return "待定"

    verdict = f"{target['conclusion']} {target['description']}".strip()
    negative_markers = ("不值得", "暂不", "不建议", "否", "暂缓", "暂停")
    tbd_markers = ("待定", "待观察", "观察", "视情况", "条件性", "有待")
    if any(marker in verdict for marker in negative_markers):
        return "否"
    if any(marker in verdict for marker in tbd_markers):
        return "待定"
    return "是"


def _risk_cards(rows: list[dict[str, str]]) -> str:
    out = []
    for row in rows:
        tag_class = PRIORITY_TAG.get(row["priority"], "tag-p2")
        out.append(
            "<div class=\"risk-card\">"
            f"<h4><span class=\"tag {tag_class}\">{_esc(row['priority'])}</span>{_esc(row['risk'])}</h4>"
            f"<p><strong>来源：</strong>{_esc(row['source'])}<br>"
            f"<strong>影响：</strong>{_esc(row['impact'])}<br>"
            f"<strong>方向：</strong>{_esc(row['direction'])}</p>"
            "</div>"
        )
    return "\n".join(out)


def _render(data: dict[str, Any], style_css: str) -> str:
    meta = data["meta"]
    status = data["status"]
    focus = data["focus"]
    org = data["org"]
    growth = data["growth"]
    actions = data["actions"]
    expansion_seed = _expansion_seed_label(growth["rows"])

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(meta['account_name'])}客户经营洞察报告</title>
<style>
{style_css}
</style>
</head>
<body>
<div class="cover">
  <div class="cover-inner">
    <div class="cover-head">
      <div>
        <div class="eyebrow">Account Insight Report</div>
        <h1>{_esc(meta['account_name'])}客户经营洞察报告</h1>
        <div class="subtitle">基于 CRM、客户经营事实与结构化判断结果生成，用于支持客户经营决策。</div>
      </div>
      <div class="score-box">
        <div class="score-num">{_score_html(meta['total_score'])}</div>
        <div class="score-label">经营健康度</div>
      </div>
    </div>
    <dl class="cover-meta">
      <div><dt>客户级别</dt><dd>{_esc(meta['account_level'])}</dd></div>
      <div><dt>负责人</dt><dd>{_esc(meta['owner'])}</dd></div>
      <div><dt>当前状态</dt><dd>{_esc(meta['current_status'])}</dd></div>
      <div><dt>合作温度</dt><dd>{_esc(meta['temperature'])}</dd></div>
      <div><dt>洞察主题</dt><dd>{_esc(meta['topic'])}</dd></div>
    </dl>
  </div>
</div>

<div class="layout">
  <aside class="toc">
    <div class="toc-title">目录</div>
    <a href="#section-1" class="active">一、客户当前状态</a>
    <a href="#section-2">二、客户真实关注点</a>
    <a href="#section-3">三、组织突破口</a>
    <a href="#section-4">四、增长空间</a>
    <a href="#section-5">五、经营建议</a>
    <a href="#section-6">附：经营风险提示</a>
  </aside>

  <main class="content">
    <section id="section-1">
      <div class="section-title"><span class="section-index">一</span>客户当前状态</div>
      <div class="summary-block">
        <h3>一句话判断</h3>
        <p>{_esc(status['summary'])}</p>
        <div class="pill-row">
          <span class="pill pill-blue">当前状态标签：{_esc(status['tag'])}</span>
        </div>
      </div>
      <table>
        <thead><tr><th>维度</th><th>当前判断</th><th>事实</th><th>判断</th><th>待确认问题</th></tr></thead>
        <tbody>
{_rows_status(status['rows'])}
        </tbody>
      </table>
    </section>

    <section id="section-2">
      <div class="section-title"><span class="section-index">二</span>客户真实关注点</div>
      <div class="summary-block">
        <h3>一句话判断</h3>
        <p>{_esc(focus['summary'])}</p>
        <div class="pill-row">
          <span class="pill pill-blue">当前我方命中度：{_esc(focus['alignment'])}</span>
        </div>
      </div>
      <table>
        <thead><tr><th>判断项</th><th>判断依据</th><th>当前结论</th><th>对经营的影响</th></tr></thead>
        <tbody>
{_rows_four_col(focus['rows'])}
        </tbody>
      </table>
    </section>

    <section id="section-3">
      <div class="section-title"><span class="section-index">三</span>组织突破口</div>
      <div class="summary-block">
        <h3>一句话判断</h3>
        <p>{_esc(org['summary'])}</p>
      </div>
      <table>
        <thead><tr><th>判断项</th><th>判断依据</th><th>当前结论</th><th>对经营的影响</th></tr></thead>
        <tbody>
{_rows_four_col(org['rows'])}
        </tbody>
      </table>
    </section>

    <section id="section-4">
      <div class="section-title"><span class="section-index">四</span>增长空间</div>
      <div class="summary-block">
        <h3>一句话判断</h3>
        <p>{_esc(growth['summary'])}</p>
      </div>
      <table>
        <thead><tr><th>判断项</th><th>当前结论</th><th>说明</th></tr></thead>
        <tbody>
{_rows_growth(growth['rows'])}
        </tbody>
      </table>
    </section>

    <section id="section-5">
      <div class="section-title"><span class="section-index">五</span>经营建议</div>
      <div class="summary-block">
        <h3>当前经营策略</h3>
        <p>{_esc(actions['strategy'])}</p>
        <div class="pill-row">
          <span class="pill pill-blue">策略判断：{_esc(actions['reason'])}</span>
          <span class="pill pill-green">扩展预埋：{_esc(expansion_seed)}</span>
        </div>
      </div>
      <table>
        <thead><tr><th>动作</th><th>目的</th><th>预期解决的问题</th><th>负责人/对象</th><th>节奏</th></tr></thead>
        <tbody>
{_rows_actions(actions['rows'])}
        </tbody>
      </table>
    </section>

    <section id="section-6">
      <div class="section-title"><span class="section-index">附</span>经营风险提示</div>
      <div class="risk-grid">
{_risk_cards(data['risks'])}
      </div>
    </section>

    <div class="foot-note"><strong>说明：</strong>本报告遵循 SFA 客户经营洞察标准（sfa-account-diagnosis）。正文内容来自输入 Markdown，评分与判断需以后续客户经营事实持续校准。</div>
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

## 页头摘要
- 客户名称：
- 当前状态：
- 负责人：
- 客户级别：
- 评分总分：
- 评分结论：
- 当前合作温度：
- 本轮洞察主题：

## 一、客户当前状态
- 一句话判断：
- 当前状态标签：
| 维度 | 当前判断 | 事实 | 判断 | 待确认问题 |

## 二、客户真实关注点
- 一句话判断：
- 当前我方命中度：
| 判断项 | 判断依据 | 当前结论 | 对经营的影响 |

## 三、组织突破口
- 一句话判断：
| 判断项 | 判断依据 | 当前结论 | 对经营的影响 |

## 四、增长空间
- 一句话判断：
| 判断项 | 当前结论 | 说明 |

## 五、经营建议
- 当前经营策略：
- 策略判断说明：
| 动作 | 目的 | 预期解决的问题 | 负责人/对象 | 节奏 |

## 附：经营风险提示
| 优先级 | 风险点 | 来源 | 影响 | 优先化解方向 |
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="渲染客户经营洞察 HTML 报告")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--markdown", help="输入 Markdown 原文")
    input_group.add_argument("--input", help="输入 Markdown 路径；兼容旧调用，缺省从 stdin 读取")
    parser.add_argument("--output", help="输出 HTML 路径，缺省写到 stdout")
    parser.add_argument("--schema", action="store_true", help="打印输入 Markdown 结构提示并退出")
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
