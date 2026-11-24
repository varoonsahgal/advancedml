/* Gradient Hive slide engine.
   →/Space/PgDn next · ←/PgUp back · Home/End · O overview · F fullscreen · N notes · ? help
   URL: #12 opens slide 12.  ?print → one slide per page (then Ctrl/Cmd+P).
   Review modes: ?audit (overflow report in <pre id="audit">), ?sheet&from=1&to=12&cols=3 (contact sheet). */
(function () {
  const W = 1920, H = 1080;
  const qs = new URLSearchParams(location.search);
  const body = document.body;
  const stage = document.querySelector(".stage");
  const frames = [...document.querySelectorAll(".frame")];
  const N = frames.length;
  frames.forEach((f, i) => f.setAttribute("data-n", i + 1));
  const frags = frames.map((f) => [...f.querySelectorAll(".f")]);
  let idx = 0, step = 0;

  const mode = qs.has("audit") || qs.has("print") ? "flat" : qs.has("sheet") ? "sheet" : "present";
  body.classList.add(mode);

  function renderMath(done) {
    const go = () => {
      try {
        if (window.renderMathInElement) renderMathInElement(document.body, {
          delimiters: [{ left: "$$", right: "$$", display: true }, { left: "$", right: "$", display: false }, { left: "\\(", right: "\\)", display: false }],
          throwOnError: false, ignoredClasses: ["nomath"],
        });
        if (window.hljs) document.querySelectorAll("pre code").forEach((el) => hljs.highlightElement(el));
      } catch (e) { console.warn(e); }
      fitMath();
      (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => { fitMath(); done && done(); });
    };
    if (document.readyState === "complete") go(); else window.addEventListener("load", go);
  }

  // shrink display math that is wider than its box (down to 55%)
  function fitMath() {
    document.querySelectorAll(".equation, .eqsm, .fitx").forEach((el) => {
      if (el.dataset.fs0 === undefined) el.dataset.fs0 = el.style.fontSize || "";
      el.style.fontSize = el.dataset.fs0;   // keep any author-set size as the starting point
      const cw = el.clientWidth - (parseFloat(getComputedStyle(el).paddingLeft) + parseFloat(getComputedStyle(el).paddingRight));
      const inner = el.querySelector(".katex-display > .katex, .katex") || el;
      const w = inner.scrollWidth;
      if (cw > 0 && w > cw) {
        const fs = parseFloat(getComputedStyle(el).fontSize);
        el.style.fontSize = Math.max(fs * 0.55, fs * cw / w * 0.97) + "px";
      }
    });
  }

  // ------------------------------------------------------------ flat (print / audit)
  const revealAll = () => document.querySelectorAll("[data-slide-class]").forEach((el) => el.closest(".slide").classList.add(el.dataset.slideClass));
  if (mode === "flat") {
    revealAll();
    renderMath(() => {
      if (!qs.has("audit")) return;
      Promise.all([document.fonts ? document.fonts.ready : 0, ...[...document.images].map((im) => im.complete ? 0 : new Promise((r) => { im.onload = im.onerror = r; }))])
        .then(() => setTimeout(audit, 400));
    });
    return;
  }

  function audit() {
    const out = [];
    frames.forEach((f, i) => {
      const s = f.querySelector(".slide");
      const R = s.getBoundingClientRect();
      const foot = s.querySelector(".sf");
      const limitB = foot && getComputedStyle(foot).display !== "none" ? R.bottom - 72 : R.bottom - 8;
      const issues = [];
      s.querySelectorAll("*").forEach((el) => {
        if (el.closest(".sf") || el.closest(".notes") || el.matches("img.bg") || el.closest("svg") && el.tagName !== "svg") return;
        if (el.closest(".katex") && !el.classList.contains("katex")) return;
        const cs = getComputedStyle(el);
        if (cs.display === "none" || cs.position === "absolute" && el.closest(".takeaway") && el === s) return;
        const r = el.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return;
        const name = el.tagName.toLowerCase() + (el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).join(".") : "");
        const txt = (el.textContent || "").trim().slice(0, 50);
        if (r.right > R.right + 2) issues.push(`${name} overflows right by ${Math.round(r.right - R.right)}px «${txt}»`);
        if (r.left < R.left - 2) issues.push(`${name} overflows left by ${Math.round(R.left - r.left)}px «${txt}»`);
        if (r.bottom > limitB + 2 && !el.closest(".full")) issues.push(`${name} runs into footer/bottom by ${Math.round(r.bottom - limitB)}px «${txt}»`);
        if (r.top < R.top - 2) issues.push(`${name} overflows top by ${Math.round(R.top - r.top)}px «${txt}»`);
        if ((el.tagName === "CODE" || el.classList.contains("equation") || el.classList.contains("eqsm")) &&
            (cs.overflowX !== "visible" && el.scrollWidth > el.clientWidth + 2 || cs.overflowY !== "visible" && el.scrollHeight > el.clientHeight + 2))
          issues.push(`${name} content clipped (${el.scrollWidth}×${el.scrollHeight} in ${el.clientWidth}×${el.clientHeight}) «${txt}»`);
        if (el.tagName === "IMG" && (!el.complete || el.naturalWidth === 0)) issues.push(`broken image ${el.getAttribute("src")}`);
      });
      // keep only the outermost offender per text
      const uniq = [...new Set(issues)].slice(0, 6);
      if (uniq.length) out.push({ slide: i + 1, issues: uniq });
    });
    const katexErr = [...document.querySelectorAll(".katex-error")].map((e) => e.getAttribute("title") || e.textContent);
    const pre = document.createElement("pre");
    pre.id = "audit";
    pre.textContent = JSON.stringify({ slides: N, problems: out, katexErrors: katexErr });
    body.appendChild(pre);
    console.log("AUDIT", pre.textContent);
  }

  // ------------------------------------------------------------ contact sheet
  if (mode === "sheet") {
    const cols = +(qs.get("cols") || 3), from = +(qs.get("from") || 1), to = +(qs.get("to") || N);
    stage.style.setProperty("--cols", cols);
    const k = (1920 - 24 - (cols - 1) * 12) / cols / W;
    frames.forEach((f, i) => { f.querySelector(".slide").style.setProperty("--k", k); if (i + 1 < from || i + 1 > to) f.classList.add("hide"); });
    revealAll();
    renderMath();
    return;
  }

  // ------------------------------------------------------------ presenter
  const ui = document.createElement("div");
  ui.className = "ui";
  ui.innerHTML = `<a href="${body.dataset.home || "../slides.html"}" title="All decks">⌂</a><button data-a="prev" title="Back (←)">←</button><span class="count"></span><button data-a="next" title="Next (→)">→</button><button data-a="ov" title="Overview (O)">▦</button><button data-a="notes" title="Speaker notes (N)">✎</button><button data-a="fs" title="Fullscreen (F)">⛶</button><button data-a="help" title="Keys (?)">?</button>`;
  body.appendChild(ui);
  const count = ui.querySelector(".count");
  const notes = document.createElement("div"); notes.className = "notes-panel"; body.appendChild(notes);
  const help = document.createElement("div"); help.className = "help";
  help.innerHTML = `<div><h3>🐝 Keys</h3><kbd>→</kbd><kbd>Space</kbd> next<br><kbd>←</kbd> back<br><kbd>Home</kbd><kbd>End</kbd> first / last<br><kbd>O</kbd><kbd>Esc</kbd> overview<br><kbd>F</kbd> fullscreen<br><kbd>N</kbd> speaker notes<br><kbd>B</kbd> blackout<br><kbd>12</kbd> then <kbd>Enter</kbd> jump to slide 12<br><kbd>P</kbd> printable version (save as PDF)</div>`;
  body.appendChild(help);
  const ovt = document.createElement("div"); ovt.className = "ov-title";
  ovt.innerHTML = `<span>▦</span> ${document.title} · click a slide to jump · Esc to return`;
  body.appendChild(ovt);
  const toast = document.createElement("div"); toast.className = "toast"; body.appendChild(toast);
  let toastT; const say = (m) => { toast.textContent = m; toast.classList.add("on"); clearTimeout(toastT); toastT = setTimeout(() => toast.classList.remove("on"), 1300); };

  function fit() {
    if (body.classList.contains("overview")) {
      const w = frames[0].getBoundingClientRect().width;
      frames.forEach((f) => f.querySelector(".slide").style.setProperty("--k", w / W));
      return;
    }
    const s = Math.min(innerWidth / W, innerHeight / H);
    stage.style.transform = `translate(${-W * s / 2}px, ${-H * s / 2}px) scale(${s})`;
  }

  function show(i, st, fromHash) {
    i = Math.max(0, Math.min(N - 1, i));
    const changed = i !== idx;
    idx = i;
    const fr = frags[i];
    step = st === "end" ? fr.length : Math.max(0, Math.min(fr.length, st || 0));
    frames.forEach((f, j) => { f.classList.toggle("active", j === i); f.setAttribute("aria-hidden", j === i ? "false" : "true"); });
    const s = frames[i].querySelector(".slide");
    fr.forEach((el, j) => el.classList.toggle("on", j < step));
    // fragments may switch classes on the slide (e.g. quiz answers)
    [...s.querySelectorAll("[data-slide-class]")].forEach((el) => s.classList.toggle(el.dataset.slideClass, el.classList.contains("on")));
    count.textContent = `${i + 1} / ${N}`;
    const n = frames[i].querySelector(".notes");
    notes.innerHTML = `<b>Slide ${i + 1}</b> · ` + (n ? n.innerHTML : "<i>No notes for this slide.</i>");
    if (!fromHash && changed) history.replaceState(null, "", "#" + (i + 1));
    if (changed) { // restart entrance animations
      s.style.animation = "none"; void s.offsetWidth; s.style.animation = "";
    }
  }
  const next = () => { if (step < frags[idx].length) show(idx, step + 1); else if (idx < N - 1) show(idx + 1, 0); };
  const prev = () => { if (step > 0) show(idx, step - 1); else if (idx > 0) show(idx - 1, "end"); };

  function toggleOverview(on) {
    const want = on === undefined ? !body.classList.contains("overview") : on;
    body.classList.toggle("overview", want);
    body.classList.toggle("present", !want);
    fit();
    if (want) frames[idx].scrollIntoView({ block: "center" });
  }

  function fromHash() {
    const m = location.hash.match(/(\d+)/);
    if (m) show(+m[1] - 1, 0, true);
  }

  let typed = "", typedT;
  document.addEventListener("keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key;
    if (help.classList.contains("on") && k !== "?") { help.classList.remove("on"); return; }
    if (/^\d$/.test(k)) { typed += k; clearTimeout(typedT); typedT = setTimeout(() => (typed = ""), 1500); say("go to " + typed); return; }
    if (k === "Enter" && typed) { show(+typed - 1, 0); typed = ""; if (body.classList.contains("overview")) toggleOverview(false); return; }
    if (body.classList.contains("overview")) {
      if (k === "Escape" || k === "o" || k === "O" || k === "Enter") toggleOverview(false);
      return;
    }
    switch (k) {
      case "ArrowRight": case "ArrowDown": case "PageDown": case " ": case "l": case "j": e.preventDefault(); next(); break;
      case "ArrowLeft": case "ArrowUp": case "PageUp": case "h": case "k": e.preventDefault(); prev(); break;
      case "Home": show(0, 0); break;
      case "End": show(N - 1, "end"); break;
      case "o": case "O": case "Escape": toggleOverview(); break;
      case "f": case "F": fullscreen(); break;
      case "n": case "N": body.classList.toggle("show-notes"); break;
      case "b": case "B": case ".": stage.style.visibility = stage.style.visibility === "hidden" ? "" : "hidden"; break;
      case "p": case "P": window.open(location.pathname + "?print", "_blank"); break;
      case "?": help.classList.toggle("on"); break;
    }
  });
  function fullscreen() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen();
    else document.exitFullscreen && document.exitFullscreen();
  }
  ui.addEventListener("click", (e) => {
    const a = e.target.closest("button")?.dataset.a;
    if (a === "next") next(); else if (a === "prev") prev(); else if (a === "ov") toggleOverview();
    else if (a === "notes") body.classList.toggle("show-notes"); else if (a === "fs") fullscreen(); else if (a === "help") help.classList.toggle("on");
  });
  stage.addEventListener("click", (e) => {
    if (body.classList.contains("overview")) {
      const f = e.target.closest(".frame");
      if (f) { show(frames.indexOf(f), 0); toggleOverview(false); }
      return;
    }
    if (e.target.closest("a, button, input, label")) return;
    // click right two-thirds → next, left third → back
    const x = e.clientX / innerWidth;
    if (x > 0.33) next(); else prev();
  });
  let tx = null, ty = null;
  stage.addEventListener("touchstart", (e) => { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, { passive: true });
  stage.addEventListener("touchend", (e) => {
    if (tx === null) return;
    const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) (dx < 0 ? next : prev)();
    tx = null;
  });
  let hideT;
  document.addEventListener("mousemove", () => { ui.classList.add("show"); body.style.cursor = ""; clearTimeout(hideT); hideT = setTimeout(() => { ui.classList.remove("show"); if (!body.classList.contains("overview")) body.style.cursor = "none"; }, 2200); });
  addEventListener("resize", fit);
  addEventListener("hashchange", fromHash);

  renderMath();
  fit();
  show(0, 0, true);
  fromHash();
})();
