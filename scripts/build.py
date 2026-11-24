"""Static-site builder for Gradient Hive.

    python scripts/build.py

Reads page sources from site/pages/**.html, wraps them in the shared layout,
expands lab placeholders, and writes the finished site into docs/ (served by
GitHub Pages: Settings → Pages → Deploy from branch → main /docs).

Page source format: an HTML comment header with `key: value` lines, then body.
Placeholders:  <!--LABS:1-->  <!--LABS:all-->  <!--PROGRESS:1-->  <!--PROGRESS:all-->
Day pages (layout: day) get a hero, sticky TOC built from <section id=.. data-toc=..>,
and prev/next pagers automatically.
"""
from pathlib import Path
import html
from urllib.parse import quote
import json
import re
import hashlib

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site" / "pages"
OUT = ROOT / "docs"
REPO = "varoonsahgal/advancedml"
BRANCH = "main"
SITE_NAME = "Gradient Hive"

LABS = json.loads((ROOT / "site" / "labs.json").read_text())
DAYDATA = json.loads((ROOT / "site" / "days.json").read_text())
DAYS = {
    1: ("Mon", "Classical, Sharpened", "days/day-1.html"),
    2: ("Tue", "The Deep Learning Engine Room", "days/day-2.html"),
    3: ("Wed", "Transformers & Beyond", "days/day-3.html"),
    4: ("Thu", "Generative Worlds", "days/day-4.html"),
    5: ("Fri", "LLMs, Reasoning & Agents", "days/day-5.html"),
}

BEE = """<svg viewBox="0 0 64 64" aria-hidden="true"><defs><clipPath id="bb{u}"><ellipse cx="35" cy="37" rx="15" ry="11"/></clipPath></defs>
<polygon points="32,2 58,17 58,47 32,62 6,47 6,17" fill="#F5B700" stroke="#1F1B16" stroke-width="2.5" stroke-linejoin="round"/>
<ellipse cx="28" cy="22" rx="7" ry="9.5" fill="#FFFDF4" stroke="#1F1B16" stroke-width="2" transform="rotate(-20 28 22)" opacity=".95"/>
<ellipse cx="39" cy="21" rx="7" ry="9.5" fill="#FFFDF4" stroke="#1F1B16" stroke-width="2" transform="rotate(18 39 21)" opacity=".95"/>
<ellipse cx="35" cy="37" rx="15" ry="11" fill="#FFE680"/>
<g clip-path="url(#bb{u})" fill="#1F1B16"><rect x="29" y="24" width="4.5" height="26"/><rect x="38" y="24" width="4.5" height="26"/><rect x="47" y="24" width="6" height="26"/></g>
<ellipse cx="35" cy="37" rx="15" ry="11" fill="none" stroke="#1F1B16" stroke-width="2.5"/>
<circle cx="18" cy="35" r="8" fill="#1F1B16"/><circle cx="15.5" cy="33" r="2.4" fill="#FFFDF4"/>
<path d="M14 28 Q10 20 7 21 M20 27 Q20 19 16 17" stroke="#1F1B16" stroke-width="2" fill="none" stroke-linecap="round"/>
<path d="M50 37 l6 0" stroke="#1F1B16" stroke-width="2.5" stroke-linecap="round"/></svg>"""


def bee(uid="x"):
    return BEE.replace("{u}", uid)


def colab(file):
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/notebooks/{file}"


def gh(file):
    return f"https://github.com/{REPO}/blob/{BRANCH}/notebooks/{file}"


DIFF = {1: "🐝 warm-up", 2: "🐝🐝 intermediate", 3: "🐝🐝🐝 spicy"}


def lab_card(lab):
    obj = "".join(f"<li>{html.escape(o)}</li>" for o in lab["objectives"])
    tags = "".join(f'<span class="chip {t[1]}">{html.escape(t[0])}</span>' for t in lab.get("tags", []))
    gpu = '<span class="chip coral">⚡ GPU optional</span>' if lab.get("gpu") else '<span class="chip teal">💻 runs on CPU</span>'
    key = '<span class="chip indigo">🔑 API key optional</span>' if lab.get("key") else ""
    return f"""<article class="lab-card reveal" data-lab="{lab['id']}" data-day="{lab['day']}" id="{lab['id']}">
  <div class="hexnum"><div><small>LAB</small>{lab['num']}</div></div>
  <div>
    <h3>{html.escape(lab['title'])}</h3>
    <div class="meta"><span class="chip honey">⏱ {lab['time']}</span><span class="chip">{DIFF[lab['difficulty']]}</span>{gpu}{key}{tags}</div>
    <p>{lab['blurb']}</p>
    {preview(lab)}
    <ul class="obj">{obj}</ul>
    <div class="actions">
      <a class="btn sm honey" href="{colab(lab['file'])}" target="_blank" rel="noopener">▶ Open in Colab</a>
      <a class="btn sm secondary" href="{gh(lab['file'])}" target="_blank" rel="noopener">View notebook</a>
      <label class="check"><input type="checkbox"> Mark complete</label>
    </div>
  </div>
</article>"""


def preview(lab):
    img = OUT / "assets" / "img" / "labs" / f"{lab['id']}.png"
    if not img.exists():
        return ""
    cap = html.escape(lab.get("preview", "a key result from this lab"))
    return (f'<figure class="lab-preview"><img src="{{{{root}}}}assets/img/labs/{lab["id"]}.png" alt="{cap}" loading="lazy">'
            f'<figcaption><b>What you\'ll build:</b> {cap}</figcaption></figure>')


def tldr(d):
    items = "".join(f"<li>{t}</li>" for t in DAYDATA[d]["tldr"])
    return f'<div class="tldr"><div class="tldr-head">⚡ The one-minute version</div><ul>{items}</ul></div>'


def takeaways(d):
    items = "".join(f'<li><span class="num">{i + 1}</span><div>{t}</div></li>' for i, t in enumerate(DAYDATA[d]["takeaways"]))
    return f'<ol class="honeyjar">{items}</ol>'


def myths(d):
    return '<div class="myths">' + "".join(
        f'<div class="myth"><div class="m"><span>MYTH</span>{m}</div><div class="r"><span>REALITY</span>{r}</div></div>'
        for m, r in DAYDATA[d]["myths"]) + "</div>"


def cards(d):
    return '<div class="flashcards">' + "".join(
        f'<button class="flash" aria-label="Flip card"><span class="inner"><span class="front"><small>Q{i + 1}</small>{q}<em>tap to flip ↻</em></span>'
        f'<span class="back"><small>A{i + 1}</small>{a}</span></span></button>'
        for i, (q, a) in enumerate(DAYDATA[d]["cards"])) + "</div>"


def cheatsheet():
    out = []
    for d in DAYS:
        k = str(d)
        eqs = "".join(f'<div class="cs-eq"><b>{html.escape(n)}</b><span>$${e}$$</span></div>' for n, e in DAYDATA[k]["equations"])
        tk = "".join(f"<li>{t}</li>" for t in DAYDATA[k]["takeaways"])
        out.append(f"""<section class="cs-day">
  <div class="cs-title"><span class="cs-hex">{d}</span><div><small>Day {d} · {DAYS[d][0]}</small><h2>{DAYS[d][1]}</h2></div></div>
  <div class="cs-grid"><div><h4>Key equations</h4>{eqs}</div><div><h4>Key takeaways</h4><ul>{tk}</ul></div></div>
</section>""")
    return "\n".join(out)


def honeycomb():
    data = json.dumps([[l["id"], l["num"], l["title"], l["day"]] for l in LABS]).replace('"', "&quot;")
    return f'<div class="honeycomb" data-honeycomb="{data}"></div>'


def labs_for(day):
    labs = LABS if day == "all" else [l for l in LABS if str(l["day"]) == str(day)]
    return labs


def progress_box(day):
    ids = ",".join(l["id"] for l in labs_for(day))
    return f'<div class="progress" data-progress="{ids}"><b>Lab progress</b> <span class="count muted mono"></span><div class="bar"><i></i></div></div>'


def expand(body, meta=None):
    d = (meta or {}).get("day")
    if d:
        body = body.replace("<!--TLDR-->", tldr(d)).replace("<!--TAKEAWAYS-->", takeaways(d))
        body = body.replace("<!--MYTHS-->", myths(d)).replace("<!--CARDS-->", cards(d))
    body = body.replace("<!--CHEATSHEET-->", cheatsheet()).replace("<!--HONEYCOMB-->", honeycomb())
    body = re.sub(r"<!--LABS:(\w+)-->", lambda m: '<div class="labs">' + "\n".join(lab_card(l) for l in labs_for(m.group(1))) + "</div>", body)
    body = re.sub(r"<!--PROGRESS:(\w+)-->", lambda m: progress_box(m.group(1)), body)
    return body


def parse(path):
    text = path.read_text()
    m = re.match(r"\s*<!--(.*?)-->", text, re.S)
    meta = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def nav(root, active):
    def a(href, label, key, cls=""):
        on = " active" if key == active else ""
        return f'<a class="{cls}{on}" href="{root}{href}">{label}</a>'
    days = "".join(a(DAYS[d][2], str(d), f"day{d}") .replace('<a class="', f'<a title="Day {d}: {DAYS[d][1]}" class="') for d in DAYS)
    return f"""<header class="nav"><div class="wrap">
  <a class="brand" href="{root}index.html">{bee('n')}<span>{SITE_NAME}<small>Advanced ML Week · 2026</small></span></a>
  <button class="icon-btn menu-btn" id="menuBtn" aria-label="Menu">☰</button>
  <nav class="nav-links">
    <div class="nav-days">{days}</div>
    {a('labs.html', 'Labs', 'labs')}
    {a('playground.html', 'Playground', 'playground')}
    {a('capstone.html', 'Capstone', 'capstone')}
    {a('cheatsheet.html', 'Cheat sheet', 'cheatsheet')}
    {a('resources.html', 'Resources', 'resources')}
    <button class="icon-btn" id="themeBtn" aria-label="Toggle dark mode">🌙</button>
  </nav>
</div></header>"""


def footer(root):
    days = "".join(f'<a href="{root}{DAYS[d][2]}">Day {d} · {DAYS[d][1]}</a>' for d in DAYS)
    return f"""<footer class="site"><div class="wrap">
  <div><div class="brand" style="color:#F6EFD9">{bee('f')}<span>{SITE_NAME}<small style="color:#cdbf9c">Advanced ML Week · 2026</small></span></div>
  <p style="margin-top:14px">A five-day, lab-first journey from gradient boosting to reasoning agents. Built for curious practitioners who learn by building. 🐝</p></div>
  <div><h4>The week</h4>{days}</div>
  <div><h4>Hands-on</h4><a href="{root}labs.html">All 16 labs</a><a href="{root}playground.html">Interactive playground</a><a href="{root}capstone.html">Capstone: Hive Demo Day</a><a href="https://github.com/{REPO}" target="_blank" rel="noopener">GitHub repo</a></div>
  <div><h4>Support</h4><a href="{root}resources.html#setup">Setup guide</a><a href="{root}resources.html#reading">Reading list</a><a href="{root}resources.html#glossary">Glossary</a><a href="{root}resources.html#instructors">Instructor notes</a><a href="{root}cheatsheet.html">Printable cheat sheet</a></div>
</div></footer>"""


def day_hero(meta, root):
    d = int(meta["day"])
    chips = "".join(f'<span class="chip">{c.strip()}</span>' for c in meta.get("chips", "").split("|") if c.strip())
    return f"""<header class="day-hero">
  <img class="bg" src="{root}assets/img/cover-day{d}.png" alt="">
  <div class="wrap">
    <div class="kicker" style="color:#F5B700">Day {d} · {DAYS[d][0]}</div>
    <h1>{meta['headline']}</h1>
    <p class="lede">{meta['lede']}</p>
    <div class="meta"><span class="chip honey">{len(labs_for(d))} labs</span>{chips}</div>
  </div>
</header>"""


def day_layout(meta, body, root):
    d = int(meta["day"])
    toc = "".join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in re.findall(r'<section id="([\w-]+)" data-toc="([^"]+)"', body))
    prev_ = f'<a class="prev" href="{root}{DAYS[d - 1][2]}"><small>← Day {d - 1}</small><b>{DAYS[d - 1][1]}</b></a>' if d > 1 else f'<a class="prev" href="{root}index.html"><small>← Home</small><b>Course overview</b></a>'
    next_ = f'<a class="next" href="{root}{DAYS[d + 1][2]}"><small>Day {d + 1} →</small><b>{DAYS[d + 1][1]}</b></a>' if d < 5 else f'<a class="next" href="{root}capstone.html"><small>Finale →</small><b>Capstone: Hive Demo Day</b></a>'
    return f"""{day_hero(meta, root)}
<div class="wrap layout">
  <aside class="toc"><h4>On this day</h4><ol>{toc}</ol>{progress_box(d)}</aside>
  <article class="content">{body}<nav class="pager">{prev_}{next_}</nav></article>
</div>"""


def ver(rel_asset):
    return hashlib.md5((OUT / rel_asset).read_bytes()).hexdigest()[:8]


def page(meta, body, rel):
    depth = rel.count("/")
    root = "../" * depth
    body = expand(body, meta).replace("{{root}}", root)
    cnt = iter(range(10_000))
    body = re.sub(r"\{\{bee\}\}", lambda m: bee(f"s{next(cnt)}"), body)
    if meta.get("layout") == "day":
        body = day_layout(meta, body, root)
    title = f"{meta['title']} · {SITE_NAME}" if meta.get("title") else SITE_NAME
    desc = html.escape(meta.get("description", "A hands-on Advanced ML week: classical ML to 2026 frontier."))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{root}assets/img/og-image.png">
<meta name="theme-color" content="#F5B700">
<link rel="icon" href="data:image/svg+xml,{quote(bee('i').replace(chr(10), ''))}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&family=Inter:wght@400..800&family=JetBrains+Mono:wght@400..700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
<link rel="stylesheet" href="{root}assets/css/style.css?v={ver("assets/css/style.css")}">
<script>try{{var t=localStorage.getItem("hive-theme");if(t)document.documentElement.setAttribute("data-theme",JSON.parse(t))}}catch(e){{}}</script>
</head>
<body>
{nav(root, meta.get('active', ''))}
<main>
{body}
</main>
{footer(root)}
<button class="flybee" aria-label="Ask Buzz for a tip">{bee('b')}</button>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="{root}assets/js/main.js?v={ver("assets/js/main.js")}"></script>
<script src="{root}assets/js/widgets.js?v={ver("assets/js/widgets.js")}"></script>
</body>
</html>
"""


def main():
    n = 0
    for src in sorted(SRC.rglob("*.html")):
        rel = src.relative_to(SRC).as_posix()
        meta, body = parse(src)
        out = OUT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(meta, body, rel))
        n += 1
        print("built", rel)
    (OUT / ".nojekyll").write_text("")
    print(f"{n} pages → {OUT}")


if __name__ == "__main__":
    main()
