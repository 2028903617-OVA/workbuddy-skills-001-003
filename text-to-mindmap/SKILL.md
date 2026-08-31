---
name: text-to-mindmap
description: 把缩进大纲或 Markdown 标题文本转换成水平思维导图（SVG + 独立 HTML），零第三方依赖。当用户说"画个思维导图""把这段大纲转成导图""整理成脑图""文本→导图"，或需要把结构化要点可视化时使用。
agent_created: true
---

# Text To Mindmap（文本→思维导图）

## Overview

把一段结构化文本（缩进大纲或 Markdown 标题）渲染成水平布局的思维导图，输出**独立 SVG** 与**可双击打开的 HTML**（微信/浏览器皆可看）。纯标准库实现，无需安装任何第三方包，适合离线、反复复用。

适用场景：
- 会议纪要、项目拆解、考核口径、业务流程等要点需要"一眼看清层级"
- 把已有 Markdown / 大纲笔记快速变成可转发给一线人员的图
- 作为其他流程的产物（如工资提成规则、函数逻辑）的可视化收尾

## 输入格式（两种都支持，自动识别）

**方式 A：Markdown 标题**
```
# 工资提成
## 欣暖家
### 第一成交金额
### ABC线索数量
## 乾鑫格力
### 月销售指标
```

**方式 B：缩进列表（2 空格=1 级，-/*/+/・ 作项目符号均可）**
```
工资提成
  - 欣暖家
    - 第一成交金额
    - ABC线索数量
  - 乾鑫格力
    - 月销售指标
```
第一行（或第一个 `#` 标题）作为根节点；其余按层级挂到最近的上层节点。

## 运行方式

使用托管 Python（推荐，已隔离）：
```
C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe ^
  C:/Users/Administrator/.workbuddy/skills/text-to-mindmap/scripts/make_mindmap.py ^
  input.txt
```
参数：
- `input`：大纲文件（.txt / .md），必填
- `--out 基础名`：输出文件名（不含扩展名），默认 `<输入同名>_mindmap`
- `--format svg|html|both`：默认 `both`
- `--max-chars 18`：单行最多字符数，超出自动换行（CJK 按字宽估算）

## 输出

- `<基础名>.svg`：矢量图，可嵌入文档或转 PNG
- `<基础名>.html`：独立页面，顶部标题栏 + 可滚动画布，手机微信直接打开
- 节点按层级配色（蓝→绿→琥珀→紫→珊瑚→青→红循环），父子用贝塞尔曲线连接

## 注意事项

- 节点文本过长会自动换行，无需手动拆；超大导图用 HTML 横向滚动查看
- 不调用任何外部网络/API，全部本机生成，符合"学习机不写生产"的约束
- 若要把导图再改成交互式或换布局（如右侧放射），改 `scripts/make_mindmap.py` 的 `layout()` 与 `render_svg()` 即可
