# -*- coding: utf-8 -*-
"""
md -> docx 通用转换（支持标题分级 / 表格 / 粗体 / 引用块 / 编号列表 / 分隔线）
风格：微软雅黑、标题 1F3864、表头 D9E2F3、引用块 FFF2CC 灰底

用法:
    python md2docx.py <源.md> <目标.docx>
"""
import re
import sys
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT = '微软雅黑'


def set_font(run, size=10.5, bold=False, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT)


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), hexcolor)
    tcPr.append(shd)


def bottom_border(par, color='BFBFBF', sz='6'):
    pPr = par._p.get_or_add_pPr()
    pbdr = OxmlElement('w:pBdr')
    bt = OxmlElement('w:bottom')
    bt.set(qn('w:val'), 'single')
    bt.set(qn('w:sz'), sz)
    bt.set(qn('w:space'), '2')
    bt.set(qn('w:color'), color)
    pbdr.append(bt)
    pPr.append(pbdr)


def inline(par, text, size=10.5):
    """处理 **粗体** 与 `代码`"""
    for pt in re.split(r'(\*\*.+?\*\*|`.+?`)', text):
        if not pt:
            continue
        if pt.startswith('**') and pt.endswith('**'):
            set_font(par.add_run(pt[2:-2]), size, True)
        elif pt.startswith('`') and pt.endswith('`'):
            set_font(par.add_run(pt[1:-1]), size - 0.5, False, 'C00000')
        else:
            set_font(par.add_run(pt), size)


def main(src, dst):
    doc = Document()
    for s in doc.sections:
        s.left_margin = Cm(2.2)
        s.right_margin = Cm(2.2)
        s.top_margin = Cm(2.0)
        s.bottom_margin = Cm(2.0)

    lines = open(src, encoding='utf-8').read().split('\n')
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()

        # 表格
        if ln.startswith('|') and i + 1 < len(lines) \
                and set(lines[i + 1].replace('|', '').strip()) <= set('-: '):
            header = [c.strip() for c in ln.strip('|').split('|')]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            t = doc.add_table(rows=1 + len(rows), cols=len(header))
            t.style = 'Table Grid'
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for c, h in enumerate(header):
                cell = t.cell(0, c)
                cell.text = ''
                inline(cell.paragraphs[0], h, 10)
                shade(cell, 'D9E2F3')
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r, row in enumerate(rows, 1):
                for c in range(len(header)):
                    cell = t.cell(r, c)
                    cell.text = ''
                    inline(cell.paragraphs[0], row[c] if c < len(row) else '', 9.5)
            doc.add_paragraph()
            continue

        if ln.startswith('# '):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_font(p.add_run(ln[2:]), 18, True, '1F3864')
            p.paragraph_format.space_after = Pt(10)
        elif ln.startswith('## '):
            p = doc.add_paragraph()
            set_font(p.add_run(ln[3:]), 14, True, '1F3864')
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            bottom_border(p, '4472C4', '8')
        elif ln.startswith('### '):
            p = doc.add_paragraph()
            set_font(p.add_run(ln[4:]), 12, True, '2E5C8A')
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
        elif ln.startswith('> '):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.5)
            inline(p, ln[2:], 10)
            pPr = p._p.get_or_add_pPr()
            shd = OxmlElement('w:shd')
            shd.set(qn('w:val'), 'clear')
            shd.set(qn('w:fill'), 'FFF2CC')
            pPr.append(shd)
        elif ln.strip() in ('---', '***'):
            bottom_border(doc.add_paragraph())
        elif re.match(r'^\d+\.\s', ln):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.space_after = Pt(3)
            inline(p, ln)
        elif ln.startswith('- '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.space_after = Pt(2)
            inline(p, ln[2:])
        elif ln.startswith('*') and ln.endswith('*') and len(ln) > 2:
            r = doc.add_paragraph().add_run(ln.strip('*'))
            set_font(r, 9, False, '7F7F7F')
            r.italic = True
        elif ln.strip() == '':
            pass
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            inline(p, ln)
        i += 1

    doc.save(dst)
    print('SAVED:', dst)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
