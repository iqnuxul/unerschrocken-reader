#!/usr/bin/env python3
"""德语图书馆生成器。

  python3 src/site.py pages                       重新生成书架 index.html 和各书目录页（不需要密码）
  python3 src/site.py build src/books/momo/kapitel1.js ...
                                                  生成并加密章节精读页（需要密码，见下）

每本书一个文件夹 src/books/<slug>/：
  book.json     书的信息（见 src/README.md）
  kapitelN.js 或 <名字>_chN_data.js   第 N 章数据：const PAGE_TITLES = {...}; const data = [...];
  （可选）封面图放 img/ 下，在 book.json 的 cover 里写路径

密码：book.json 里 password_secret 写 Secret 名（如 MOMO_PASSWORD）。
在 GitHub Actions 里从仓库 Secrets 读取；本地运行时用同名环境变量。
"""
import html, json, os, re, subprocess, sys, tempfile, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(ROOT, "src", "books")
SALT = "f2b4c6dd6e8a536cea0b8226272fe21b"
AFDIAN = '<a href="https://afdian.com/a/einwohnervonb612" target="_blank" rel="noopener"'
esc = html.escape
CH_RE = r"(?:kapitel|_ch)(\d+)(?:_data)?\.js$"   # kapitel5.js 或 money_ch5_data.js

# ---------- 读取 ----------
def load_books():
    books = []
    for d in sorted(glob.glob(os.path.join(BOOKS, "*", "book.json"))):
        b = json.load(open(d, encoding="utf-8"))
        b["slug"] = os.path.basename(os.path.dirname(d))
        b.setdefault("prefix", b["slug"])
        b.setdefault("chapters", [])
        books.append(b)
    return sorted(books, key=lambda b: (b.get("month", "9999"), b["slug"]))

def index_file(b):
    return b.get("legacy", {}).get("index") or f"{b['prefix']}-index.html"

def chapter_file(b, n):
    if n == 1 and b.get("legacy", {}).get("first_page"):
        return b["legacy"]["first_page"]
    return f"{b['prefix']}{n}.html"

def chapter_key(b, n):
    if n == 1 and b.get("legacy", {}).get("first_key"):
        return b["legacy"]["first_key"]
    return f"{b['prefix']}{n}"

def data_files(b):
    out = {}
    for f in glob.glob(os.path.join(BOOKS, b["slug"], "*.js")):
        m = re.search(CH_RE, os.path.basename(f))
        if m: out[int(m.group(1))] = f
    return out

def chapter_info(b, n):
    if n <= len(b["chapters"]):
        return b["chapters"][n - 1]
    f = data_files(b).get(n)
    title = ""
    if f:
        m = re.search(r"Kapitel\s*\d+\s*[:：]\s*(.+?)\s*(\(S\.|$)", open(f, encoding="utf-8").readline())
        if m: title = m.group(1)
    return {"de": title or f"Kapitel {n}", "zh": "", "page": ""}

def published(b):
    return [n for n in sorted(set(range(1, len(b["chapters"]) + 1)) | set(data_files(b)))
            if os.path.exists(os.path.join(ROOT, chapter_file(b, n)))]

# ---------- 颜色 ----------
def mix(c, other, t):
    a = [int(c[i:i + 2], 16) for i in (1, 3, 5)]; o = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * (1 - t) + y * t):02x}" for x, y in zip(a, o))

def palette(b):
    if "palette" in b: return b["palette"]["light"], b["palette"]["dark"]
    c = b["color"]
    return [c, mix(c, "#ffffff", .86), "#2e7d4f", "#dcefe2"], [mix(c, "#ffffff", .4), mix(c, "#16141a", .78), "#7fcf9c", "#1d3426"]

# ---------- 章节精读页 ----------
def build_page(b, n, datafile, out):
    h = open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8").read()
    src = open(datafile, encoding="utf-8").read()
    m = re.search(r"const PAGE_TITLES\s*=\s*\{(.*?)\};", src, re.S)
    titles = {}
    if m:
        for k, v in re.findall(r'(\d+)\s*:\s*"((?:[^"\\]|\\.)*)"', m.group(1)): titles[int(k)] = json.loads(f'"{v}"')
    body = src[src.index("[", src.index("const data")) + 1:src.rindex("]")].strip().rstrip(",")
    for p in sorted({int(x) for x in re.findall(r"^\[(\d+),", body, re.M)}):
        titles.setdefault(p, "")
    pages = "const PAGES = {\n" + ",\n".join(f"  {k}: {json.dumps(v, ensure_ascii=False)}" for k, v in sorted(titles.items())) + "\n};"
    h = h.replace("const PAGES = {\n};", pages, 1).replace("const S = [\n];", "const S = [\n" + body + "\n];", 1)
    info = chapter_info(b, n)
    sub = f"第 {n} 章 · {info['de']}"
    lt, dk = palette(b)
    avatar = (f'<img class="avatar" src="{b["cover"]}" alt="{esc(b["title"])}" style="width:96px">' if b.get("cover") else "")
    rep = [('<title>Wu Zetian 逐句精读</title>', f'<title>{esc(b["title"])} 逐句精读</title>'),
           ('"wz-p"+p', f'"{b["prefix"]}-p"+p'), ('speak("Kaiserin")', f'speak({json.dumps(b.get("speak_word", "Guten Tag"))})'),
           ('<img class="avatar" src="img/wu.png" alt="Wu Zetian" style="width:78px"><div><h1>Wu Zetian</h1>', f'{avatar}<div><h1>{esc(b["title"])}</h1>'),
           ('<div class="sub">Kaiserin · 624–705</div>', f'<div class="sub">{esc(sub)}</div>'),
           ('内容整理自 Pénélope Bagieu《Unerschrocken》德语版', f'内容节选自 {esc(b["author"])}《{esc(b["title"])}》（{esc(b["zh"])}）德语版'),
           ('"wz_"+k', f'"{chapter_key(b, n)}_"+k'), ('"wz_"+k', f'"{chapter_key(b, n)}_"+k'),
           ('--teal:#b3261e; --teal-soft:#fbe4e1; --red:#c79a1a; --red-soft:#f8efd2;', '--teal:%s; --teal-soft:%s; --red:%s; --red-soft:%s;' % tuple(lt)),
           ('--teal:#f29b94; --teal-soft:#3d2220; --red:#e6c35c; --red-soft:#38301a;', '--teal:%s; --teal-soft:%s; --red:%s; --red-soft:%s;' % tuple(dk)),
           ('--teal:#f29b94; --teal-soft:#3d2220; --red:#e6c35c; --red-soft:#38301a;', '--teal:%s; --teal-soft:%s; --red:%s; --red-soft:%s;' % tuple(dk)),
           ('href="./"', f'href="{index_file(b)}"'), ('href="./"', f'href="{index_file(b)}"')]
    for o, nw in rep:
        assert o in h, o
        h = h.replace(o, nw, 1)
    open(out, "w", encoding="utf-8").write(h)

def secrets():
    s = {}
    try: s = json.loads(os.environ.get("SECRETS_JSON") or "{}")
    except ValueError: pass
    return s

def build(files):
    books = {b["slug"]: b for b in load_books()}
    sec = secrets()
    for f in files:
        f = os.path.abspath(f)
        m = re.search(r"src/books/([^/]+)/[^/]*?" + CH_RE, f)
        if not m or not os.path.exists(f) or m.group(1) not in books:
            print(f"跳过 {f}"); continue
        b, n = books[m.group(1)], int(m.group(2))
        name = b.get("password_secret", "BOOK_PASSWORD")
        pw = sec.get(name) or os.environ.get(name)
        if not pw:
            sys.exit(f"缺少密码 {name}：请在仓库 Settings → Secrets and variables → Actions 里添加")
        with tempfile.TemporaryDirectory() as tmp:
            plain = os.path.join(tmp, chapter_file(b, n))
            build_page(b, n, f, plain)
            subprocess.run(["npx", "--yes", "staticrypt@3.5.4", plain, "-p", pw, "-s", SALT,
                            "--short", "--remember", "false", "-d", ROOT], check=True, cwd=tmp,
                           stdout=subprocess.DEVNULL)
        print(f"✓ {b['zh']} 第 {n} 章 → {chapter_file(b, n)}")

# ---------- 目录页与书架 ----------
HEAD = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{title}</title>
<style>
:root{{color-scheme:light;--ink:#1f1b24;--muted:#6b6672;--line:#e7e2da}}
*{{box-sizing:border-box}}
body{{margin:0;background:#fff;color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}}
.wrap{{max-width:960px;margin:0 auto;padding:48px 16px 60px;text-align:center}}
h1{{font-family:"Songti SC","Noto Serif CJK SC",Georgia,serif;font-weight:700;margin:0;font-size:clamp(34px,7vw,52px);letter-spacing:.04em}}
.de{{font-family:"Iowan Old Style",Palatino,Georgia,serif;font-style:italic;font-size:22px;color:var(--muted);margin:2px 0 0}}
.sub{{color:var(--muted);margin:10px auto 28px;max-width:56ch;font-size:15px}}
.credit{{margin:-12px 0 30px;font-size:14px;color:var(--muted)}}.credit a{{color:inherit;border-bottom:1px dotted currentColor;text-decoration:none}}
.back{{text-align:left;margin:-28px 0 18px;font-size:14px}}.back a{{color:var(--muted);text-decoration:none}}
footer{{color:var(--muted);font-size:13px;margin-top:40px}}
{css}
</style>
</head>
<body><div class="wrap">
"""
FOOT = f"""<footer>为爱发电：{AFDIAN} style="color:inherit">小怪</a><br>仅供语言学习，原作版权归作者与出版社所有。留言需要 GitHub 账号。</footer>
</div></body></html>
"""

def cover_html(b, cls="cv"):
    if b.get("cover"):
        return f'<img class="{cls}" src="{esc(b["cover"])}" alt="{esc(b["title"])}">'
    return (f'<div class="{cls} ph" style="--c:{b["color"]}"><b>{esc(b["zh"])}</b><i>{esc(b["title"])}</i>'
            f'<span>{esc(b["author"])}</span></div>')

SHELF_CSS = """
.year{display:flex;align-items:baseline;gap:10px;margin:34px 0 14px;text-align:left;border-bottom:2px solid var(--ink);padding-bottom:6px}
.year b{font-size:30px;font-family:Georgia,serif}.year span{color:var(--muted);font-size:14px}
.shelf{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px;text-align:left}
.bk{display:flex;gap:14px;padding:14px;border:1px solid var(--line);border-radius:14px;color:inherit;text-decoration:none;background:#fff;min-width:0}
a.bk{border:2px solid var(--ink);box-shadow:4px 4px 0 var(--c);transition:transform .15s}a.bk:hover{transform:translate(-2px,-2px)}
.bk .cv{flex:0 0 86px;width:86px;height:120px;object-fit:contain;object-position:top;border-radius:6px}
.ph{background:var(--c);color:#fff;padding:8px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden}
.ph b{font-size:15px;line-height:1.25}.ph i{font-size:11px;font-family:Georgia,serif;line-height:1.2;opacity:.9}.ph span{font-size:10px;opacity:.8}
.bk .tx{min-width:0;flex:1}
.bk .m{font-size:13px;font-weight:700;color:var(--c)}
.bk h3{margin:0;font-size:18px;line-height:1.3}
.bk .t{font-family:"Iowan Old Style",Palatino,Georgia,serif;font-size:14px;color:var(--muted);line-height:1.3}
.bk .a{font-size:12.5px;color:var(--muted);margin-top:2px}.bk .a em{font-style:normal;border:1px solid var(--line);border-radius:999px;padding:0 7px;margin-left:4px}
.bk p{margin:6px 0 6px;font-size:13px;line-height:1.45}
.st{display:inline-block;font-size:12px;border-radius:999px;padding:1px 9px;background:#f1eee9;color:var(--muted)}
a.bk .st{background:var(--c);color:#fff}
"""

def build_shelf(books):
    years = {}
    for b in books:
        years.setdefault(b.get("month", "")[:4], []).append(b)
    out = HEAD.format(title="德语线上图书馆", css=SHELF_CSS)
    out += ('<h1>德语线上图书馆</h1>\n<div class="de">Deutsche Bibliothek</div>\n'
            '<div class="sub">读书会书单 · 逐句精读：点单词发音，中文可遮住自测，每页可留言讨论</div>\n'
            f'<p class="credit">♥ 为爱发电：{AFDIAN}>小怪</a></p>\n')
    for y, bs in years.items():
        months = [int(b["month"][5:7]) for b in bs]
        out += f'<div class="year"><b>{y}</b><span>{min(months)}–{max(months)} 月</span></div>\n<div class="shelf">\n'
        for b in bs:
            link = b.get("link")
            if not link and published(b): link = index_file(b)
            status = b.get("status") or (f"{len(published(b))} 章已上线" if link else "即将开始")
            tag = "a" if link else "div"
            href = f' href="{esc(link)}"' if link else ""
            out += (f'<{tag} class="bk"{href} style="--c:{b["color"]}">{cover_html(b)}<div class="tx">'
                    f'<div class="m">{int(b["month"][5:7])} 月</div><h3>{esc(b["zh"])}</h3><div class="t">{esc(b["title"])}</div>'
                    f'<div class="a">{esc(b["author"])}' + (f'<em>{esc(b["tag"])}</em>' if b.get("tag") else "") + '</div>'
                    f'<p>{esc(b.get("note", ""))}</p><span class="st">{esc(status)}</span></div></{tag}>\n')
        out += "</div>\n"
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out + FOOT)

INDEX_CSS = """
.chs{max-width:640px;margin:0 auto;text-align:left;display:flex;flex-direction:column;gap:10px}
.ch{display:flex;align-items:center;gap:14px;padding:12px 16px;border:2px solid var(--ink);border-radius:14px;color:inherit;text-decoration:none;background:#fff}
a.ch{box-shadow:4px 4px 0 var(--c);transition:transform .15s}a.ch:hover{transform:translate(-2px,-2px)}
.ch.off{opacity:.5;border-style:dashed}
.ch .n{flex:0 0 32px;height:32px;border-radius:50%;background:var(--c);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700}
.ch .t{flex:1;min-width:0}.ch b{display:block;font-family:"Iowan Old Style",Palatino,Georgia,serif;font-size:18px}.ch i{font-style:normal;color:var(--muted);font-size:14px}
.ch .p,.ch em{font-size:13px;color:var(--muted);font-style:normal;white-space:nowrap}a.ch em{color:var(--c);font-weight:600}
@media(max-width:520px){.ch .p{display:none}}
.cover{height:200px;width:auto;margin:6px auto 18px;display:block}
.cover.ph{width:150px;border-radius:10px;text-align:left}.cover.ph b{font-size:22px}.cover.ph i{font-size:14px}.cover.ph span{font-size:12px}
.soon{color:var(--muted);border:2px dashed var(--line);border-radius:14px;padding:22px}
"""

def build_index(b):
    pub = set(published(b))
    nums = sorted(set(range(1, len(b["chapters"]) + 1)) | set(data_files(b)) | pub)
    rows = ""
    for n in nums:
        c = chapter_info(b, n)
        inner = (f'<span class="n">{n}</span><span class="t"><b>{esc(c["de"])}</b><i>{esc(c.get("zh", ""))}</i></span>'
                 + (f'<span class="p">S. {c["page"]}</span>' if c.get("page") else ""))
        rows += (f'<a class="ch" href="{chapter_file(b, n)}">{inner}<em>开始读 →</em></a>\n' if n in pub
                 else f'<div class="ch off">{inner}<em>待更新</em></div>\n')
    if not rows:
        rows = '<div class="soon">章节即将上线</div>\n'
    out = HEAD.format(title=f'{esc(b["zh"])} · 目录', css=INDEX_CSS)
    out += (f'<p class="back"><a href="./">← 返回书架</a></p>\n<h1>{esc(b["zh"])}</h1>\n<div class="de">{esc(b["title"])}</div>\n'
            f'<div class="sub">{esc(b["author"])} · 按章节逐句精读（页面密码另设）</div>\n'
            f'<div style="--c:{b["color"]}">{cover_html(b, "cover")}\n<div class="chs">\n{rows}</div></div>\n')
    open(os.path.join(ROOT, index_file(b)), "w", encoding="utf-8").write(out + FOOT)

def pages():
    books = load_books()
    n = 0
    for b in books:
        if not b.get("link") and (published(b) or data_files(b) or b["chapters"]):
            build_index(b); n += 1
    build_shelf(books)
    print(f"✓ 书架和 {n} 个目录页已更新")

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "pages": pages()
    elif len(sys.argv) >= 3 and sys.argv[1] == "build": build(sys.argv[2:])
    else: print(__doc__)
