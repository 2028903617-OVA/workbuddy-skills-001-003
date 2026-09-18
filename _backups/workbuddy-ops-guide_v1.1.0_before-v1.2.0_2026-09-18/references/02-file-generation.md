# 02 文件生成、样式与版本管理

## 2.1 写盘前先看有没有被占用（B01）

**现象**：生成/覆盖 xlsx 抛 `PermissionError`。

**根因**：Windows 下 WPS/Excel/预览面板打开时会锁文件句柄。

✅ 探测可写性，占用就另存：
```python
def safe_save(wb, path):
    import os
    try:
        open(path, 'a').close()          # 试开
    except PermissionError:
        base, ext = os.path.splitext(path)
        i = 2
        while True:
            alt = f'{base}_v{i}{ext}'
            try:
                open(alt, 'a').close(); path = alt; break
            except PermissionError:
                i += 1
    wb.save(path)
    return path                          # ★ 一定要把新路径告诉用户
```
**不中断任务**，自动 `_v2`/`_v3` 递增并告知新文件名。docx/pptx/csv 同理。

## 2.2 `~$` 锁文件（B02）

WPS/Office 打开时生成 `~$文件名.xlsx`（约 165 字节）。**无害**，关闭后自动消失，但**任何批量遍历/匹配逻辑必须过滤 `~$` 前缀**。

## 2.3 ★ 读外部导出的 Excel 一律 `read_only=False`（B05）

**现象**：系统导出的 xlsx 用 `load_workbook(read_only=True)` 打开，只有 0~1 行、只 1 列，误报"缺少某列"。

**根因**：read_only 依赖内部流式结构，导出文件的 `dimension` 不规范导致解析失败。

✅ **读外部文件一律 `read_only=False`**。只读模式仅用于自己确认过结构的超大文件，且加兜底：
```python
wb = openpyxl.load_workbook(p, read_only=False)
```
若必须用只读，加"只读不到 3+ 列表头 → 回退非 read_only"。

## 2.4 数组公式首字符被吃掉（B04）

**现象**：写 `LOOKUP(1,0/(...))` 后 Excel 显示 `#NAME?`；解压看 XML 发现公式变成 `OOKUP(...)`。

**根因**：`ArrayFormula(ref, text)` 的 text **必须以 `=` 开头**；漏 `=` 时序列化吃掉第一个字符。**写盘不报错、读回也"正常"**，只有解压看 sheet XML 才能发现。

✅ 统一封装公式写入函数，数组公式强制 `=` 开头；交付前解压 xlsx 抽查 sheet XML。

## 2.5 覆盖写值会丢样式（B06）

赋值方式相当于重建单元格，字体/底色/数字格式/对齐回退默认。
✅ **只改 `cell.value`**，不动单元格对象；要换样式显式 `copy.copy()`。

## 2.6 重排行后样式错位（B07）

样式钉在**坐标**上，清 value 不清样式 → 重排后标题行没底色、明细行有底色。
✅ 重排后按"行类型"（表头/明细/小计/合计）**整行刷样式**并同步行高；修复后逐行 dump 填充色核对。

## 2.7 百分比与小数混排（B08）

同列大部分 `60.59%`，个别行 `0.697887` —— 该格 number_format 是 `General`（新建覆盖回退，或模板本身漏网）。

✅ 生成后**按列强制兜底统一**：比率 `0.00%`、金额 `#,##0.00`。
诊断前置：做表前先打印 `set(该列所有 number_format)`。

## 2.8 ★ 模板继承法（B09 · 硬编码美化被否）

**现象**：按旧表硬编码底色/加粗/字号，用户要求"按我调好的模板一比一复刻"。

**根因**：把"上一版样式"当成了用户的审美意志。**用户手调版才是权威。**

✅ 做法：
1. 以用户手调文件为模板打开
2. **只清 `cell.value`**，保留 font/fill/border/alignment/number_format
3. 写数据，**删掉脚本里所有硬编码样式**
4. 新增行从**语义最接近的行**（如最后一个小计行）继承
5. 要清除某项用对应类型的空对象（如 `PatternFill(fill_type=None)`），不要粗暴清整个 style

## 2.9 移动 sheet 到首位（B10）

`wb.move_sheet(name, 0)` 偏移 0 **不移动**。改用：
```python
ws = wb['目标']
wb._sheets.remove(ws)
wb._sheets.insert(0, ws)
```

## 2.10 验证不能只和上一版比（B11）

**现象**：报"与旧版数值一致"，用户打开是错的。

**根因**：只做增量对比，没对规则做独立复核；上一版本身错则错得一样。

✅ 交付前三查：
1. **数值**脱离旧版重算抽查
2. **公式**跨表引用逐个看取值
3. **样式**与权威模板逐格 diff

## 2.11 回读与自检（B12 / B13 / B14）

- 批量改 4 个只改了 3 个却报"全部改好" → **逐个文件 grep/Read 核验再汇报**
- 样式 diff 取 `fill.fgColor.rgb` 遇 theme 色报错 → 用 `str(cell.fill)` / `str(cell.border)` **整体比较**，或加 `isinstance(x.rgb, str)` 防御
- 公式比对用 `str(cell)` 全是误报 → 用 `cell.value`；ArrayFormula 用 `.text`

## 2.12 生成脚本化（可复用）

每个交付都留一个 `gen_*.py`，改数据重跑即可，**不要手改 xlsx**。
统一风格基线（本机约定）：

| 项 | 值 |
|---|---|
| 字体 | 微软雅黑 |
| 表头底色 | `4472C4` 白字加粗 |
| 次级表头 | `2E5C8A` |
| 分组行 | `D9E2F3` |
| 待确认/警示 | `FCE4D6`（橙）或 `FFF2CC`（黄） |
| 已完成 | `E2EFDA`（绿） |
| 待填 | `F2F2F2`（灰） |
| 其他 | 冻结首行、自动换行、细边框 `BFBFBF` |

模板见 `scripts/xlsx_style_base.py`。

## 2.13 md → docx

用 `scripts/md2docx.py`（支持表格、`**粗体**`、引用块灰底、分级标题）。
**回读**：docx 用 `zipfile` + 正则抽 `<w:t>`，或 python-docx 读段落核对章节齐全、无 `⟦⟧` 占位残留。

## 2.14 版本管理（C01）

- 迭代**另存新名**：`_v2` `_v3`
- 每次交付**显式声明哪一版是最终版**（"v3 取代 v1/v2"）
- 保留旧版但提醒用户别发混

## 2.15 输出格式先问场景（C06）

先问"**在哪看、用什么打开、谁看**"：
- 手机 + 微信 → **PDF 稳妥**（HTML + localhost 在手机不可用）
- 一线中老年 → 大字版
- 打印 → A4 分页

## 2.16 未覆盖的盲区（如实标注）

以下类别在两个任务中**均未出现踩坑记录**，遇到时需自行验证，勿当既有结论：
PDF 生成/拆页/合并、PPTX 生成、中文字体与嵌入、编码 GBK/UTF-8 系统性坑、中文路径、合并单元格、图片插入与打印分页、WPS 宏与云端协作。
