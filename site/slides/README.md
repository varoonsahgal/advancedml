# Slide decks: authoring guide

Each `site/slides/<name>.html` becomes `docs/slides/<name>.html`, a 1920×1080 deck that runs in the browser.

```bash
python scripts/build.py --deck day-3          # build one deck (or no flag: the whole site)
python scripts/slides_check.py day-3          # overflow / clipping / KaTeX / broken-image audit
python scripts/slides_check.py day-3 --sheets OUTDIR   # contact sheets, 12 slides per PNG
python scripts/slides_check.py day-3 --shot 7 OUTDIR   # one slide at full size
```

`welcome.html` is the reference deck: it uses almost every layout below.

## File format

```html
<!--
title: Day 3 · Transformers & Beyond      (deck title)
label: Day 3 · Transformers               (footer text)
kicker: Day 3 · Wednesday                 (small label on the Slides page card)
order: 3                                  (order on the Slides page)
cover: cover-day3.png                     (card image, relative to docs/assets/img/)
day: 3                                    (enables the RECAP/MYTHS/INTERVIEW/EQUATIONS placeholders)
blurb: One sentence for the Slides page card.
-->
<section class="slide ...">...</section>
<section class="slide ...">...</section>
```

* Every slide is a top-level `<section class="slide ...">`. **Never nest `<section>` inside a slide.**
* `{{img}}` → `../assets/img/`; `{{root}}` → `../` (the site root).
* Footer, slide number and progress bar are added automatically. Add `nofoot` to hide them.
* `<aside class="notes">…</aside>` inside a slide holds speaker notes (press **N**).
* `class="f"` on an element makes it a step (revealed on the next click). Add `data-slide-class="answered"` to a step to mark a quiz answer.
* Math: `$inline$` and `$$display$$` (KaTeX). Code: `<pre><code class="language-python">…</code></pre>`. Escape `<` as `&lt;` inside code.

## Auto-generated slides (placeholders)

| Placeholder | Becomes |
|---|---|
| `<!--LAB:lab07-->` | Lab launch slide from `site/labs.json`: hex number, objectives, preview image, Colab button |
| `<!--RECAP-->` | 🍯 "What to remember" slides from `days.json` takeaways (auto-split into 2 slides when there are more than 6) |
| `<!--MYTHS-->` | One myth-vs-reality slide per myth in `days.json` (3) |
| `<!--INTERVIEW-->` | 💼 Interview corner: Q&A slides from `days.json` flashcards, with answers revealed step by step (2) |
| `<!--EQUATIONS-->` | Formula-sheet slide: the 6 cheat-sheet equations for the day |

## Layouts (`class="slide …"`)

| Class | Use | Skeleton |
|---|---|---|
| `cover` | Deck opener (night + full-bleed art) | `<img class="bg" src=…>` `<div class="badge"><div><small>DAY</small>3</div></div>` `.kicker` `h1` (use `<em>` for honey words) `p.lede` `.chips` |
| `section` | Part divider (night, giant outlined number, hexagon-cropped image) | `<div><div class="num">02</div><h2>…</h2><p>…</p></div><div class="hexart"><img …></div>`; use `hexart contain` for plots on light backgrounds |
| *(default)* | Title + anything | `.kicker` `h2` then content (`.cards`, `.stats`, `.callout`, `.grid2`, `.timeline`, `.agenda`, `.vs`, `.qa`, …) |
| `split` | Text + visual side by side | `<div class="text">.kicker h2 p/ul</div><figure class="media"><img><figcaption></figcaption></figure>`. Modifiers: `media-wide`, `text-wide`, `media-left`. The visual can also be `<div class="diagram"><svg>…</svg></div>` |
| `full` | One big figure edge to edge | `<img class="bg" src=…><div class="overlay"><div class="kicker">…</div><h2>…</h2></div><div class="caption">…</div>`. Add `night` (+ `cover-img` to crop-fill) for dark art |
| `statement` | One sentence, very big | `.kicker` `p.big` (`.big.md` is smaller) `p.by`. Add `night` for a dark version; `div.quote-mark` for a quote |
| `takeaway` | 🍯 Honey key-takeaway slide | `<div class="label">🍯 Key takeaway</div><p class="big">… <b>highlighted phrase</b> …</p><p class="sub">…</p>`. Keep `.big` under ~110 characters |
| `myth` | Hand-written myth buster | `.kicker` `<div class="mvr"><div class="m"><span>✗ MYTH</span><p>…</p></div><div class="r"><span>✓ REALITY</span><p>…</p></div></div>` |
| `quiz` | Multiple choice with reveal | `.kicker` `h2` `<div class="opts"><div class="opt" data-l="A">…</div><div class="opt" data-l="B" data-correct>…</div>…</div><p class="explain f" data-slide-class="answered"><b>B.</b> why…</p>` |
| `eq` | Equation + annotated terms | `.kicker` `h2` `<div class="equation">$$…$$</div><div class="terms"><div class="term coral"><b>name</b>meaning</div>…</div>`; `.equation.sm` is smaller |
| `night` | Dark version of any default slide | add to any slide |

## Components

* `.cards` (3 columns; `.c2`, `.c4`, `.c5`) → `.card` (`teal coral indigo plum ink hi`) with `.ico` emoji, `h3`, `p`
* `.stats` → `.stat` (`.hi`) with `<b>42<small>%</small></b><span>label</span>`
* `.timeline` → `.ev` (`.hi`) with `<b>2017</b><span><strong>Title</strong>detail</span>` (up to 7 events)
* `.vs` → two `div`s (one may be `.hi`), each with `h3` + `ul`
* `.callout` (`teal coral indigo plum`): one highlighted note
* `.agenda` → `.slot` (`.lab`, `.fun`) with `<span class="t">09:15</span><div><b>…</b><span class="d">…</span></div><span class="chip">…</span>`
* `.grid2`, `.grid3`, `.row`: plain layout helpers. `.imgrow`: images in a row. `.chips` → `.chip` (`honey teal coral indigo plum`)
* `figure.media` (`.dark` for night art, `.bare` without the frame); `.codewin` wraps a `pre` in a window frame; `pre.sm` / `pre.lg` set code size

## Sizes and limits

The canvas is 1920×1080 with 128px side margins, and the bottom 128px is reserved for the footer. Body text is 34px; `h2` is 74px. A slide holds roughly a title plus **5 bullets**, **3–5 cards**, **one figure**, or **~14 lines of code at the default size** (`pre.sm`: ~18 lines). If the audit reports overflow, cut words; don't shrink fonts below 24px.

## Figures

New slide figures go in `docs/assets/img/slides/` (prefix `dN-`) and are generated by `scripts/slides/figs_dayN.py`, which imports the shared palette and `rcParams` from `scripts/make_figures.py`. Use shapes that fit slides: about 8×6.5 in for split slides and 16×9 for full-bleed or night art.
