# -*- coding: utf-8 -*-
"""
敏感词扫描（对外文件交付前必跑）
★ 要点：打印命中行的【上下文原文】，由人工判断是否误报（命中常在免责句里）

用法:
    python scan_secrets.py <文件路径> [额外关键词,逗号分隔]

★ 默认词表是「跨行业通用」的内部口径词，不含任何具体公司/平台/品牌。
  使用时把你自己的平台名、供应商名、内部对象 API 前缀通过第二个参数追加：
      python scan_secrets.py a.docx "我的平台名,供应商A,内部对象前缀"
"""
import sys
import os

# 通用内部口径词（可跨组织使用，无特定主体信息）
DEFAULT_WORDS = [
    # 费用与议价（内部口径）
    '人天', '核减', '自做', '议价', '压价', '砍价', '报价单',
    # 我方内部判定
    '可自做', '建议核减', '议价点',
    # 选型（对外一般不提）
    '替换', '换平台', '更换系统',
]


def scan(path, extra=None):
    words = list(DEFAULT_WORDS)
    if extra:
        words += [w.strip() for w in extra.split(',') if w.strip()]

    if not os.path.exists(path):
        print('文件不存在:', path)
        return 2

    try:
        text = open(path, encoding='utf-8').read()
    except Exception:
        # 可能是 docx/xlsx，尝试二进制粗扫
        data = open(path, 'rb').read()
        text = data.decode('utf-8', errors='ignore')

    lines = text.split('\n')
    hits = []
    for i, line in enumerate(lines, 1):
        for w in words:
            if w in line:
                hits.append((i, w, line.strip()[:160]))
                break

    print('=' * 70)
    print('扫描文件:', path)
    print('扫描词数:', len(words), ' 总行数:', len(lines))
    print('=' * 70)

    if not hits:
        print('✅ 零命中')
        return 0

    print(f'⚠️  命中 {len(hits)} 处（必须逐条看上下文判断是否为误报）:\n')
    for ln, w, ctx in hits:
        print(f'  [行{ln}] 词「{w}」')
        print(f'         {ctx}')
    print()
    print('判断规则：')
    print('  - 出现在「本件不含…」等免责/说明句里 → 误报，保留')
    print('  - 出现在正文描述里 → 真泄漏，必须改')
    return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    p = sys.argv[1]
    extra = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(scan(p, extra))
