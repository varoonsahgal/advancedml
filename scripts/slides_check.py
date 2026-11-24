"""Review tool for the slide decks (uses headless Google Chrome).

  python scripts/slides_check.py                    # overflow/KaTeX audit of every deck in docs/slides/
  python scripts/slides_check.py day-2              # audit one deck
  python scripts/slides_check.py day-2 --sheets OUT # also write contact sheets OUT/day-2-sheet-1.png ... (12 slides each)
  python scripts/slides_check.py day-2 --shot 7 OUT # full-size screenshot of slide 7 → OUT/day-2-07.png

Run `python scripts/build.py` first. Exit code 1 if any deck has problems.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "slides"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def chrome(args, timeout=120):
    with tempfile.TemporaryDirectory() as prof:
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               "--no-default-browser-check", f"--user-data-dir={prof}", "--virtual-time-budget=12000", *args]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def url(deck, query="", hash_=""):
    return (DOCS / f"{deck}.html").as_uri() + (f"?{query}" if query else "") + (f"#{hash_}" if hash_ else "")


def audit(deck):
    r = chrome(["--window-size=1920,1080", "--dump-dom", url(deck, "audit")], timeout=180)
    m = re.search(r'<pre id="audit">(.*?)</pre>', r.stdout, re.S)
    if not m:
        print(f"[{deck}] audit did not run (JS error?)\n{r.stderr[-800:]}")
        return False
    import html
    data = json.loads(html.unescape(m.group(1)))
    ok = not data["problems"] and not data["katexErrors"]
    print(f"[{deck}] {data['slides']} slides · {len(data['problems'])} slides with layout problems · {len(data['katexErrors'])} KaTeX errors")
    for p in data["problems"]:
        for i in p["issues"]:
            print(f"   slide {p['slide']:>3}: {i}")
    for e in data["katexErrors"]:
        print(f"   KaTeX: {e[:160]}")
    return ok


def count(deck):
    return len(re.findall(r'<div class="frame">', (DOCS / f"{deck}.html").read_text()))


def sheets(deck, out):
    out.mkdir(parents=True, exist_ok=True)
    n = count(deck)
    cols, per = 3, 12
    th = (1920 - 24 - (cols - 1) * 12) / cols * 9 / 16
    paths = []
    for k, start in enumerate(range(1, n + 1, per)):
        end = min(n, start + per - 1)
        rows = -(-(end - start + 1) // cols)
        hgt = int(rows * th + (rows + 1) * 12)
        p = out / f"{deck}-sheet-{k + 1}.png"
        chrome([f"--window-size=1920,{hgt}", f"--screenshot={p}", url(deck, f"sheet&from={start}&to={end}&cols={cols}")])
        paths.append(p)
        print("wrote", p, f"(slides {start}-{end})")
    return paths


def shot(deck, n, out):
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{deck}-{int(n):02d}.png"
    chrome(["--window-size=1920,1080", f"--screenshot={p}", url(deck, f"sheet&from={n}&to={n}&cols=1")])
    print("wrote", p)


if __name__ == "__main__":
    a = sys.argv[1:]
    decks = [x for x in a if not x.startswith("--") and (DOCS / f"{x}.html").exists()]
    if "--shot" in a:
        i = a.index("--shot")
        shot(decks[0], a[i + 1], Path(a[i + 2]))
        sys.exit(0)
    if not decks:
        decks = sorted(p.stem for p in DOCS.glob("*.html"))
    good = all([audit(d) for d in decks])
    if "--sheets" in a:
        out = Path(a[a.index("--sheets") + 1])
        for d in decks:
            sheets(d, out)
    sys.exit(0 if good else 1)
