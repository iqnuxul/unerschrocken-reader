#!/usr/bin/env python3
"""生成一章精读页（明文）。用法：
  python3 src/build.py src/data/money-kapitel3.js money3.html "第 3 章 · 章节标题" money3
参数：数据文件  输出文件  页头副标题  进度存档名（每章不同）
数据文件里要有 const PAGE_TITLES = {...}; 和 const data = [...];
生成后用 StatiCrypt 加密（见 src/README.md）。"""
import sys, json, re, os
datafile, out, sub, key = sys.argv[1:5]
here = os.path.dirname(os.path.abspath(__file__))
h = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
src = open(datafile, encoding='utf-8').read()
m = re.search(r'const PAGE_TITLES\s*=\s*(\{.*?\});', src, re.S)
titles = {int(k): v for k, v in json.loads(re.sub(r'(\d+)\s*:', r'"\1":', m.group(1)).replace(',\n}', '\n}')).items()}
body = src[src.index('[', src.index('const data')) + 1:src.rindex(']')].strip().rstrip(',')
pages = "const PAGES = {\n" + ",\n".join(f'  {k}: {json.dumps(v, ensure_ascii=False)}' for k, v in sorted(titles.items())) + "\n};"
h = h.replace('const PAGES = {\n};', pages, 1).replace('const S = [\n];', 'const S = [\n' + body + '\n];', 1)
rep = [('<title>Wu Zetian 逐句精读</title>', '<title>Ein Hund namens Money 逐句精读</title>'),
 ('"wz-p"+p', '"money-p"+p'), ('speak("Kaiserin")', 'speak("Money")'),
 ('<img class="avatar" src="img/wu.png" alt="Wu Zetian" style="width:78px"><div><h1>Wu Zetian</h1>',
  '<img class="avatar" src="img/money.png" alt="Money und Kira" style="width:96px"><div><h1>Ein Hund namens Money</h1>'),
 ('<div class="sub">Kaiserin · 624–705</div>', f'<div class="sub">{sub}</div>'),
 ('内容整理自 Pénélope Bagieu《Unerschrocken》德语版', '内容节选自 Bodo Schäfer《Ein Hund namens Money》（小狗钱钱）德语版'),
 ('"wz_"+k', f'"{key}_"+k'), ('"wz_"+k', f'"{key}_"+k'),
 ('--teal:#b3261e; --teal-soft:#fbe4e1; --red:#c79a1a; --red-soft:#f8efd2;', '--teal:#d2691e; --teal-soft:#fbe8d6; --red:#2e7d4f; --red-soft:#dcefe2;'),
 ('--teal:#f29b94; --teal-soft:#3d2220; --red:#e6c35c; --red-soft:#38301a;', '--teal:#f0a868; --teal-soft:#3d2a1a; --red:#7fcf9c; --red-soft:#1d3426;'),
 ('--teal:#f29b94; --teal-soft:#3d2220; --red:#e6c35c; --red-soft:#38301a;', '--teal:#f0a868; --teal-soft:#3d2a1a; --red:#7fcf9c; --red-soft:#1d3426;'),
 ('href="./"', 'href="money-index.html"'), ('href="./"', 'href="money-index.html"')]
for o, n in rep:
    assert o in h, o
    h = h.replace(o, n, 1)
open(out, 'w', encoding='utf-8').write(h)
print(f"{out}: {len(titles)} 页")
