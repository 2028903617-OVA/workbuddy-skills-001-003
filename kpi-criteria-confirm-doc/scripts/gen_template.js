/**
 * 考核口径确认表 —— 可复用生成骨架（kpi-criteria-confirm-doc 技能）
 *
 * 用法：
 *   NODE_PATH=C:/Users/Administrator/.workbuddy/binaries/node/workspace/node_modules \
 *   C:/Users/Administrator/.workbuddy/binaries/node/versions/22.12.0/node.exe gen_template.js
 *
 * 说明：helper（run/para/heading/subtitle/cell/table）已封装好，每次只需改「===== 内容区 =====」部分。
 * 版本配色：A版=蓝 1F4E79 / B版=橙 C55A11 / C版=绿 548235；标题 1F3864；声明红 C00000；表头灰 F2F2F2。
 *
 * 布局铁律：
 *   1) 表格行一律 cantSplit:true（防跨页）；docx 9.6.1 的 keepWithNext 不会被序列化，别依赖。
 *   2) 用 pageBreakBefore:true 在大分组前强制分页，做"一页多节、小节不跨页"的紧凑排版。
 *   3) 页面 A4 横向、页边距 600。
 */

const docx = require('docx');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, BorderStyle, AlignmentType, ShadingType, VerticalAlign, PageOrientation,
} = docx;
const fs = require('fs');

// ===== 颜色常量 =====
const BLUE = '1F4E79';    // A版（现方案）
const ORANGE = 'C55A11';  // B版（拟调整1）
const GREEN = '548235';   // C版（拟调整2）
const GREY = 'F2F2F2';
const RED = 'C00000';     // 声明框
const TITLE = '1F3864';

// ===== helper =====
function run(text, o = {}) {
  return new TextRun({
    text,
    size: o.size || 18,
    bold: !!o.bold,
    color: o.color || '000000',
    font: 'Microsoft YaHei',
    italics: !!o.italics,
  });
}
function para(text, o = {}) {
  const children = Array.isArray(text)
    ? text.map((t) => (typeof t === 'string' ? run(t, o) : run(t.text, { bold: t.bold, color: t.color, size: t.size })))
    : [run(text, o)];
  return new Paragraph({
    alignment: o.align || AlignmentType.LEFT,
    spacing: { before: o.before != null ? o.before : 0, after: o.after != null ? o.after : 60 },
    children,
  });
}
function heading(text, color, pb = false) {
  return new Paragraph({
    pageBreakBefore: pb,            // 仅在大分组前用 true 强制分页
    spacing: { before: pb ? 220 : 160, after: 80 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color } },
    children: [run(text, { bold: true, size: 26, color })],
  });
}
function subtitle(text) {
  return new Paragraph({
    spacing: { before: 40, after: 80 },
    children: [run(text, { size: 17, color: '595959', italics: true })],
  });
}
function cell(content, o = {}) {
  const lines = Array.isArray(content) ? content : [content];
  const children = lines.map((line) => {
    const segs = Array.isArray(line) ? line : [line];
    return new Paragraph({
      alignment: o.align || AlignmentType.LEFT,
      spacing: { before: 20, after: 20 },
      children: segs.map((s) =>
        typeof s === 'string'
          ? run(s, { size: o.size || 18, bold: o.bold, color: o.color })
          : run(s.text, { size: o.size || 18, bold: s.bold || o.bold, color: s.color || o.color })
      ),
    });
  });
  return new TableCell({
    width: o.width ? { size: o.width, type: WidthType.PERCENTAGE } : undefined,
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    verticalAlign: o.valign || VerticalAlign.CENTER,
    children,
  });
}
function table(rows, opts = {}) {
  const borders = {
    top: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
    left: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
    right: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
    insideVertical: { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' },
  };
  return new Table({
    width: { size: opts.width || 100, type: WidthType.PERCENTAGE },
    borders,
    rows: rows.map((r) => new TableRow({ cantSplit: true, children: r })), // 防跨页
  });
}

// =====================================================================
// ===== 内容区（这里替换成实际考核项 / 版本 / 示例） =====
// =====================================================================
const children = [];

// 标题 + 副标题（版本说明）
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [run('【品牌】 月度绩效奖金考核口径', { bold: true, size: 32, color: TITLE })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 160 },
  children: [run('A版 = 现方案　|　B版 = 拟调整方案1　|　C版 = 拟调整方案2（请勾选其一）', { size: 18, bold: true, color: '595959' })],
}));

// 声明框（判定前提）
children.push(table([
  [cell('重要声明（判定前提）', { width: 18, bold: true, fill: RED, color: 'FFFFFF', size: 18 }),
   cell(['凡按『回款日期 / 首次回款日期』统计的指标，',
          '仅当该笔回款『审批通过（life_status = 已回款）』后才予以判定计入；',
          '未审批通过 / 未回款的记录，不计入当月任何考核指标。'], { width: 82, size: 18 })],
], { width: 100 }));

// 通用基础规则
children.push(heading('一、基础确认规则（A / B / C 三版通用）', TITLE));
children.push(para('· 金额统计依据：按订单对象统计，金额取自订单，不从回款明细汇总。'));
children.push(para('· 时间统计依据：成交相关口径统一按回款日期统计；新增线索数按线索创建日期统计。'));
children.push(para('· 回款审批状态：按回款日期统计的指标，仅回款审批通过才计入（见上方声明）。'));
children.push(para('· 奖金标准：四项考核每项达标奖 300 元/月，四项全达标合计上限 1200 元/月。'));
children.push(para('· 统计周期与维度：自然月；匹配 人员 + 年 + 月 + 品牌。'));

// 判定逻辑（如第一成交）
children.push(heading('二、第一成交判定逻辑（A / B / C 三版通用）', TITLE));
children.push(para('· 定义：客户第一次成交，并且首次回款日期 ≤ 线索创建日期即为『第一成交』。'));
children.push(para('· 判定条件：首次回款日期 ≤ 线索创建日期，且已回款 / 已审核。'));
children.push(para('· 作用：满足即计入① 第一成交率金额。'));

// === A版（现方案，蓝色） ===
children.push(heading('三、A版 · 现方案', BLUE, true));
children.push(subtitle('（即目前系统正在跑的口径）'));
children.push(table([
  [cell('考核项', { width: 14, bold: true, fill: BLUE, color: 'FFFFFF' }),
   cell('统计口径', { width: 52, bold: true, fill: BLUE, color: 'FFFFFF' }),
   cell('示例 / 说明', { width: 34, bold: true, fill: BLUE, color: 'FFFFFF' })],
  [cell('① 第一成交率金额', { width: 14, bold: true, valign: 'center' }),
   cell('当月第一成交金额（不含变更）≥ 指标，即达标；金额按订单对象统计。', { width: 52 }),
   cell('第一成交 10 万、指标 10 万 → 达成率 100% → 发 300。', { width: 34 })],
  [cell('② 新增ABC线索数', { width: 14, bold: true, valign: 'center' }),
   cell('当月新建线索数（创建时间）− 当月新建且第一成交客户数 = 净新建；≥ 指标即达标。', { width: 52 }),
   cell('新建 10 条、其中 2 条第一成交 → 净新建 8 条。', { width: 34 })],
  [cell('③ 成交ABC顾客数', { width: 14, bold: true, valign: 'center' }),
   cell('每个客户只统计一次，第一成交 / ABC 不重复计数。', { width: 52 }),
   cell('同客户本月仅计 1 次。', { width: 34 })],
  [cell('④ 月度整体销售', { width: 14, bold: true, valign: 'center' }),
   cell('当月订单金额（不含变更）≥ 指标，即达标。', { width: 52 }),
   cell('订单 50 万、变更 0 → 实际 50 万 ≥ 指标 → 发 300。', { width: 34 })],
], { width: 100 }));

// === B版（拟调整1，橙色） ===
children.push(heading('四、B版 · 拟调整方案1', ORANGE));
children.push(subtitle('（③ 按『客户 + 回款日』联合去重）'));
children.push(table([
  [cell('考核项', { width: 14, bold: true, fill: ORANGE, color: 'FFFFFF' }),
   cell('统计口径', { width: 52, bold: true, fill: ORANGE, color: 'FFFFFF' }),
   cell('示例 / 说明', { width: 34, bold: true, fill: ORANGE, color: 'FFFFFF' })],
  [cell('③ 成交ABC顾客数', { width: 14, bold: true, valign: 'center' }),
   cell('当月有再成交（回款审批通过）的 ABC 客户，按『客户名称 + 回款日期』联合唯一值去重：同客户同回款日只计 1 个；同客户不同回款日各计 1 个。', { width: 52 }),
   cell(['客户A：8/1 回款、8/1 再回款 → 计 1 个；',
          '客户B：8/5 回款、8/19 回款 → 计 2 个。'], { width: 34 })],
], { width: 100 }));

// === C版（拟调整2，绿色） ===
children.push(heading('五、C版 · 拟调整方案2', GREEN, true));
children.push(subtitle('（③ 按『客户信息』唯一值去重，同客户本月仅计 1 个）'));
children.push(table([
  [cell('考核项', { width: 14, bold: true, fill: GREEN, color: 'FFFFFF' }),
   cell('统计口径', { width: 52, bold: true, fill: GREEN, color: 'FFFFFF' }),
   cell('示例 / 说明', { width: 34, bold: true, fill: GREEN, color: 'FFFFFF' })],
  [cell('③ 成交ABC顾客数', { width: 14, bold: true, valign: 'center' }),
   cell('当月有再成交（回款审批通过）的 ABC 客户，按『客户信息』唯一值去重：同客户本月仅计 1 个。', { width: 52 }),
   cell('客户A：8/1 成交、8/2 再成交 → 同客户本月 → 仅计 1 个。', { width: 34 })],
], { width: 100 }));

// 差异一览
children.push(heading('六、A版 vs B版 vs C版 关键差异一览', TITLE));
children.push(table([
  [cell('考核项', { width: 16, bold: true, fill: GREY }),
   cell('A版（现方案）', { width: 28, bold: true, fill: GREY }),
   cell('B版（拟调整1）', { width: 28, bold: true, fill: GREY }),
   cell('C版（拟调整2）', { width: 28, bold: true, fill: GREY })],
  [cell('③ 成交ABC顾客数', { width: 16, bold: true, valign: 'center' }),
   cell('第一成交 / ABC 不重复计数', { width: 28 }),
   cell('客户 + 回款日去重', { width: 28 }),
   cell('客户信息当月去重', { width: 28 })],
  [cell('对奖金影响', { width: 16, bold: true, valign: 'center' }),
   cell('口径最窄、成本最可控', { width: 28 }),
   cell('同客户分多回款日成交可多计', { width: 28 }),
   cell('③口径比A版宽、比B版低', { width: 28 })],
], { width: 100 }));

// 确认签字
children.push(heading('七、确认签字', TITLE));
children.push(para('请勾选最终采用方案（可整表选 A / B / C，也可逐项选择）：'));
children.push(table([
  [cell('考核项', { width: 34, bold: true, fill: GREY }),
   cell('采用方案', { width: 42, bold: true, fill: GREY }),
   cell('签字', { width: 24, bold: true, fill: GREY })],
  [cell('① 第一成交率金额', { width: 34 }), cell('□ A　□ B', { width: 42, align: AlignmentType.CENTER }), cell('__________', { width: 24, align: AlignmentType.CENTER })],
  [cell('② 新增ABC线索数', { width: 34 }), cell('□ A', { width: 42, align: AlignmentType.CENTER }), cell('__________', { width: 24, align: AlignmentType.CENTER })],
  [cell('③ 成交ABC顾客数', { width: 34 }), cell('□ A　□ B　□ C', { width: 42, align: AlignmentType.CENTER }), cell('__________', { width: 24, align: AlignmentType.CENTER })],
  [cell('④ 月度整体销售', { width: 34 }), cell('□ A　□ B', { width: 42, align: AlignmentType.CENTER }), cell('__________', { width: 24, align: AlignmentType.CENTER })],
], { width: 100 }));
children.push(para('意见 / 修改建议：'));
children.push(table([
  [cell('（如对上述口径有调整，请填写）', { width: 100 })],
  [cell('', { width: 100 })],
], { width: 100 }));
children.push(para('确认人（签字）：___________________', { before: 160 }));
children.push(para('日期：______年______月______日'));

// =====================================================================
// ===== 输出 =====
// =====================================================================
const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 16838, height: 11906 },
        orientation: PageOrientation.LANDSCAPE,
        margin: { top: 600, bottom: 600, left: 600, right: 600 },
      },
    },
    children,
  }],
});

const OUT = process.argv[2] || '考核口径确认表_模板.docx';
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log('WROTE', OUT, 'bytes=', buf.length);
}).catch((e) => { console.error('ERR', e); process.exit(1); });
