#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text-to-mindmap : 把"缩进大纲 / Markdown 标题"转成水平思维导图 SVG。

纯标准库实现，零第三方依赖。
输入：一个 .txt / .md 大纲文件
  - Markdown 标题：# 一级  ## 二级  ### 三级 ... （按 # 个数定层级）
  - 或缩进列表：每行前导空格 = 层级（默认 2 空格=1 级），可用 - * + ・ 作项目符号
  - 第一行（或第一个 # 标题）作为根节点
输出：<同名>_mindmap.svg  +  <同名>_mindmap.html（独立可双击打开，浏览器/微信皆可看）

用法：
  python make_mindmap.py input.txt
  python make_mindmap.py input.md --out result --format both
  python make_mindmap.py input.txt --max-chars 18
"""
import sys
import os
import argparse

# ---- 布局常量 ----
VGAP = 16          # 兄弟子树之间的纵向间隙
HCONN = 64         # 父子之间的横向连接间隙
PADX = 14          # 节点框左右内边距
PADY = 10          # 节点框上下内边距
LINE_H = 20        # 单行文字高度
LEVEL_W_MIN = 200  # 每层最小横向跨度（实际按节点宽度自适应）
CHAR_CJK = 13.5    # 一个 CJK 字符估算宽度
CHAR_ASC = 7.5     # 一个 ASCII 字符估算宽度
MAX_CHARS = 18     # 单行最多字符（超出自动换行）

# 各层级配色（浅色填充 + 深色描边），与 WorkBuddy 亮色主题一致
PALETTE = [
    ("#B5D4F4", "#185FA5"),  # 蓝
    ("#C0DD97", "#3B6D11"),  # 绿
    ("#FAC775", "#854F0B"),  # 琥珀
    ("#CECBF6", "#534AB7"),  # 紫
    ("#F5C4B3", "#993C1D"),  # 珊瑚
    ("#9FE1CB", "#0F6E56"),  # 青
    ("#F7C1C1", "#A32D2D"),  # 红
]


def char_width(ch):
    return CHAR_CJK if ord(ch) > 0x2E80 else CHAR_ASC


def estimate_line_width(s):
    return sum(char_width(c) for c in s)


def wrap_text(label, max_chars):
    lines = []
    cur = ""
    for ch in label:
        cur += ch
        if len(cur) >= max_chars:
            lines.append(cur)
            cur = ""
    if cur:
        lines.append(cur)
    return lines or [""]


def box_size(node, max_chars):
    lines = wrap_text(node["label"], max_chars)
    node["lines"] = lines
    w = max(estimate_line_width(ln) for ln in lines) + 2 * PADX
    h = len(lines) * LINE_H + 2 * PADY
    return w, h


def parse_outline(text):
    nodes = []
    has_heading = any(l.lstrip().startswith("#") for l in text.splitlines())
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if has_heading and raw.lstrip().startswith("#"):
            h = 0
            i = 0
            while i < len(raw) and raw[i] == "#":
                h += 1
                i += 1
            label = raw[i:].strip()
            depth = h - 1
        else:
            stripped = raw.lstrip(" \t")
            lead = len(raw) - len(stripped)
            depth = lead // 2
            label = stripped
            if label and label[0] in "-*+・•·":
                label = label[1:].strip()
        if not label:
            continue
        nodes.append((depth, label))
    # 首节点强制为根
    if nodes:
        nodes[0] = (0, nodes[0][1])
    return nodes


def build_tree(nodes):
    root = None
    stack = []
    for depth, label in nodes:
        node = {"label": label, "children": []}
        if root is None:
            root = node
            stack = [(0, node)]
            continue
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if not stack:
            stack = [(0, root)]
        stack[-1][1]["children"].append(node)
        stack.append((depth, node))
    return root


def layout(node, depth, x, cursor, max_chars):
    w, h = box_size(node, max_chars)
    node["x"] = x
    node["w"] = w
    node["h"] = h
    node["depth"] = depth
    if not node["children"]:
        node["y"] = cursor[0] + h / 2
        cursor[0] += h + VGAP
        return
    child_x = x + w + HCONN
    for c in node["children"]:
        layout(c, depth + 1, child_x, cursor, max_chars)
    node["y"] = (node["children"][0]["y"] + node["children"][-1]["y"]) / 2


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def render_svg(root, max_chars):
    # 计算总尺寸
    total_h = 0
    total_w = 0

    def measure(n):
        nonlocal total_h, total_w
        total_h = max(total_h, n["y"] + n["h"] / 2)
        total_w = max(total_w, n["x"] + n["w"])
        for c in n["children"]:
            measure(c)

    # 先布局（cursor 从 0 开始）
    cursor = [0]
    layout(root, 0, 0, cursor, max_chars)
    measure(root)
    M = 30
    W = int(total_w + M * 2)
    H = int(total_h + M * 2)

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="100%" font-family="-apple-system,Segoe UI,Microsoft YaHei,sans-serif">'
    )
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')

    # 连接线（先画，置于节点下层）
    def draw_links(n):
        px, py = n["x"] + n["w"], n["y"]
        for c in n["children"]:
            cx, cy = c["x"], c["y"]
            mx = (px + cx) / 2
            parts.append(
                f'<path d="M{px:.1f},{py:.1f} C{mx:.1f},{py:.1f} '
                f'{mx:.1f},{cy:.1f} {cx:.1f},{cy:.1f}" fill="none" '
                f'stroke="#94a3b8" stroke-width="1.4"/>'
            )
            draw_links(c)

    draw_links(root)

    # 节点
    def draw_nodes(n):
        d = n["depth"]
        fill, stroke = PALETTE[d % len(PALETTE)]
        x, y = n["x"], n["y"] - n["h"] / 2
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{n["w"]:.1f}" height="{n["h"]:.1f}" '
            f'rx="10" ry="10" fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>'
        )
        lines = n.get("lines", [n["label"]])
        for i, ln in enumerate(lines):
            ty = y + PADY + LINE_H * (i + 0.5)
            parts.append(
                f'<text x="{x + n["w"]/2:.1f}" y="{ty:.1f}" text-anchor="middle" '
                f'dominant-baseline="central" font-size="13" fill="#1f2937">{esc(ln)}</text>'
            )
        for c in n["children"]:
            draw_nodes(c)

    draw_nodes(root)
    parts.append("</svg>")
    return "\n".join(parts), W, H


def render_html(svg, title):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · 思维导图</title>
<style>
  body{{margin:0;font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif;background:#f7f8fa;color:#1f2937}}
  header{{padding:14px 20px;background:#185FA5;color:#fff;font-size:15px;font-weight:500}}
  .wrap{{overflow:auto;padding:20px}}
</style>
</head>
<body>
<header>{esc(title)} · 思维导图</header>
<div class="wrap">
{svg}
</div>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser(description="大纲转思维导图 SVG")
    ap.add_argument("input", help="输入大纲文件 (.txt/.md)")
    ap.add_argument("--out", help="输出基础名(不含扩展名)，默认与输入同名")
    ap.add_argument("--format", choices=["svg", "html", "both"], default="both")
    ap.add_argument("--max-chars", type=int, default=MAX_CHARS, help="单行最多字符数")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print(f"[错误] 找不到输入文件: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    nodes = parse_outline(text)
    if not nodes:
        print("[错误] 输入为空或无可解析节点")
        sys.exit(1)
    root = build_tree(nodes)
    svg, W, H = render_svg(root, args.max_chars)

    stem = args.out or os.path.splitext(args.input)[0] + "_mindmap"
    title = root["label"]
    if args.format in ("svg", "both"):
        with open(stem + ".svg", "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"[OK] 已生成 SVG: {stem}.svg  ({W}x{H})")
    if args.format in ("html", "both"):
        html = render_html(svg, title)
        with open(stem + ".html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[OK] 已生成 HTML: {stem}.html")
    print(f"[OK] 根节点: {title}  节点总数: {count_nodes(root)}")


def count_nodes(n):
    return 1 + sum(count_nodes(c) for c in n["children"])


if __name__ == "__main__":
    main()
