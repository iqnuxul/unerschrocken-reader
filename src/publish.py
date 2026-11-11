#!/usr/bin/env python3
"""把小狗钱钱的章节数据生成为加密精读页，并在目录里点亮该章。
用法：MONEY_PASSWORD=... python3 src/publish.py src/data/money-kapitel3.js [更多文件...]
GitHub Actions 会自动调用（见 .github/workflows/publish-money.yml）。"""
import os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALT = "f2b4c6dd6e8a536cea0b8226272fe21b"   # 与已上线章节一致
password = os.environ.get("MONEY_PASSWORD")
if not password:
    sys.exit("缺少 MONEY_PASSWORD（仓库 Settings → Secrets and variables → Actions 里添加）")

def publish(datafile):
    name = os.path.basename(datafile)
    m = re.fullmatch(r"money-kapitel(\d+)\.js", name)
    if not m:
        print(f"跳过 {name}：文件名应为 money-kapitelN.js"); return
    n = int(m.group(1))
    head = open(datafile, encoding="utf-8").readline()
    t = re.search(r"Kapitel\s*\d+\s*[:：]\s*(.+?)\s*(\(S\.|$)", head)
    sub = f"第 {n} 章" + (f" · {t.group(1)}" if t else "")
    out = "money.html" if n == 1 else f"money{n}.html"
    key = "money" if n == 1 else f"money{n}"
    with tempfile.TemporaryDirectory() as tmp:
        plain = os.path.join(tmp, out)
        subprocess.run([sys.executable, os.path.join(ROOT, "src", "build.py"), datafile, plain, sub, key], check=True)
        subprocess.run(["npx", "--yes", "staticrypt@3.5.4", plain, "-p", password, "-s", SALT,
                        "--short", "--remember", "false", "-d", ROOT], check=True, cwd=tmp)
    # 在目录里点亮这一章
    idx = os.path.join(ROOT, "money-index.html")
    h = open(idx, encoding="utf-8").read()
    pat = re.compile(r'<div class="ch off">(<span class="n">%d</span>.*?)<em>待更新</em></div>' % n)
    h2 = pat.sub(lambda mm: f'<a class="ch" href="{out}">{mm.group(1)}<em>开始读 →</em></a>', h)
    if h2 != h:
        open(idx, "w", encoding="utf-8").write(h2)
    print(f"✓ 第 {n} 章 → {out}")

files = sys.argv[1:]
if not files:
    files = sorted(os.path.join(ROOT, "src", "data", f) for f in os.listdir(os.path.join(ROOT, "src", "data")))
for f in files:
    if os.path.exists(f):
        publish(f)
