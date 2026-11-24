/* Gradient Hive — site behaviour: theme, nav, reveal, TOC, quizzes, lab progress, Buzz */
(function () {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode */ } },
  };

  /* ---------- theme */
  const root = document.documentElement;
  const saved = store.get("hive-theme", null);
  if (saved) root.setAttribute("data-theme", saved);
  const themeBtn = $("#themeBtn");
  const isDark = () => root.getAttribute("data-theme") === "dark" ||
    (!root.getAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
  const paintThemeBtn = () => { if (themeBtn) themeBtn.textContent = isDark() ? "☀️" : "🌙"; };
  paintThemeBtn();
  themeBtn && themeBtn.addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    root.setAttribute("data-theme", next); store.set("hive-theme", next); paintThemeBtn();
  });

  /* ---------- mobile menu */
  const menuBtn = $("#menuBtn"), links = $(".nav-links");
  menuBtn && menuBtn.addEventListener("click", () => links.classList.toggle("open"));

  /* ---------- reveal on scroll */
  const io = "IntersectionObserver" in window ? new IntersectionObserver((es) => {
    es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { rootMargin: "0px 0px -8% 0px" }) : null;
  $$(".reveal").forEach((el) => io ? io.observe(el) : el.classList.add("in"));

  /* ---------- TOC scrollspy + reading progress */
  const tocLinks = $$(".toc a[href^='#']");
  if (tocLinks.length) {
    const secs = tocLinks.map((a) => document.getElementById(a.getAttribute("href").slice(1))).filter(Boolean);
    const onScroll = () => {
      let cur = secs[0];
      for (const s of secs) if (s.getBoundingClientRect().top < 140) cur = s;
      tocLinks.forEach((a) => a.classList.toggle("active", cur && a.getAttribute("href") === "#" + cur.id));
    };
    addEventListener("scroll", onScroll, { passive: true }); onScroll();
  }

  /* ---------- labs: completion tracking */
  const done = store.get("hive-labs-done", {});
  const paintProgress = () => {
    paintHoneycomb();
    $$("[data-progress]").forEach((el) => {
      const ids = el.dataset.progress.split(",").filter(Boolean);
      const n = ids.filter((i) => done[i]).length;
      const bar = $(".bar i", el); if (bar) bar.style.width = (ids.length ? 100 * n / ids.length : 0) + "%";
      const txt = $(".count", el); if (txt) txt.textContent = `${n} / ${ids.length}`;
    });
  };
  /* honeycomb: one hex per lab, filled with honey when complete */
  function paintHoneycomb() {
    $$("[data-honeycomb]").forEach((el) => {
      let labs; try { labs = JSON.parse(el.dataset.honeycomb); } catch (e) { return; }
      if (!el.querySelector("svg")) {
        const R = 46, w = Math.sqrt(3) * R, perRow = 8, rows = Math.ceil(labs.length / perRow);
        const W = perRow * w + w / 2 + 8, H = rows * 1.5 * R + R / 2 + 8;
        let cells = "";
        labs.forEach(([id, num, title, day], i) => {
          const r = Math.floor(i / perRow), c = i % perRow;
          const cx = 4 + w / 2 + c * w + (r % 2 ? w / 2 : 0), cy = 4 + R + r * 1.5 * R;
          const pts = Array.from({ length: 6 }, (_, k) => { const a = Math.PI / 180 * (60 * k - 90); return `${(cx + (R - 3) * Math.cos(a)).toFixed(1)},${(cy + (R - 3) * Math.sin(a)).toFixed(1)}`; }).join(" ");
          const safe = String(title).replace(/[<&>"]/g, "");
          cells += `<g class="cell" data-id="${id}" tabindex="0" role="link" aria-label="Lab ${num}: ${safe}"><title>Lab ${num} · ${safe}</title><polygon points="${pts}"/><text x="${cx}" y="${cy + 2}">${num}</text><text class="sub" x="${cx}" y="${cy + 18}">DAY ${day}</text></g>`;
        });
        el.innerHTML = `<svg viewBox="0 0 ${W.toFixed(0)} ${H.toFixed(0)}" role="img" aria-label="Lab progress honeycomb">${cells}</svg><div class="hc-msg"></div>`;
        $$(".cell", el).forEach((g) => {
          const go = () => { const t = document.getElementById(g.dataset.id); if (t) t.scrollIntoView({ behavior: "smooth", block: "center" }); else location.href = "labs.html#" + g.dataset.id; };
          g.addEventListener("click", go); g.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
        });
      }
      let n = 0;
      $$(".cell", el).forEach((g) => { const d = !!done[g.dataset.id]; g.classList.toggle("done", d); n += d; });
      const msg = n === 0 ? "Your honeycomb is empty. Every hive starts with one cell. 🐝"
        : n < 6 ? `${n} cell${n > 1 ? "s" : ""} of honey. The hive is buzzing! 🍯`
        : n < 16 ? `${n}/16. Over a third of the way there, keep going! 🍯🍯`
        : "16/16. A full honeycomb! You are officially the Queen Bee. 👑🐝";
      $(".hc-msg", el).textContent = msg;
    });
  }

  $$(".lab-card").forEach((card) => {
    const id = card.dataset.lab, box = $("input[type=checkbox]", card);
    if (!box) return;
    box.checked = !!done[id]; card.classList.toggle("done", !!done[id]);
    box.addEventListener("change", () => {
      done[id] = box.checked; store.set("hive-labs-done", done);
      card.classList.toggle("done", box.checked); paintProgress();
      if (box.checked) {
        const dayIds = $$(`.lab-card[data-day="${card.dataset.day}"]`).map((c) => c.dataset.lab);
        const all = Object.keys(done).filter((k) => done[k]).length;
        if (all === 16) { confetti(80); say("<b>ALL 16 LABS DONE.</b> You filled the whole honeycomb. Queen Bee status unlocked. 👑🐝"); }
        else if (dayIds.length && dayIds.every((i) => done[i])) { confetti(45); say(`<b>Day ${card.dataset.day} complete!</b> Every lab of the day is done. Take a victory lap. 🏆`); }
        else { confetti(18); say(pick(LAB_CHEERS)); }
      }
    });
  });
  paintProgress();

  /* ---------- flashcards */
  $$(".flash").forEach((c) => c.addEventListener("click", () => c.classList.toggle("flipped")));

  /* ---------- lightbox for figures and lab previews */
  const lb = document.createElement("div"); lb.className = "lightbox"; lb.innerHTML = "<img alt=''>"; document.body.appendChild(lb);
  lb.addEventListener("click", () => lb.classList.remove("open"));
  addEventListener("keydown", (e) => { if (e.key === "Escape") lb.classList.remove("open"); });
  $$("figure.fig img, .lab-preview img").forEach((img) => img.addEventListener("click", () => {
    $("img", lb).src = img.currentSrc || img.src; $("img", lb).alt = img.alt; lb.classList.add("open");
  }));

  /* ---------- lab filters (labs page) */
  const filters = $$(".filters button");
  filters.forEach((b) => b.addEventListener("click", () => {
    filters.forEach((x) => x.classList.toggle("on", x === b));
    const f = b.dataset.filter;
    $$(".lab-card").forEach((c) => { c.style.display = (f === "all" || c.dataset.day === f) ? "" : "none"; });
  }));

  /* ---------- quizzes */
  $$(".quiz").forEach((quiz) => {
    const qs = $$(".q", quiz); let right = 0, answered = 0;
    const score = $(".quiz-score span", quiz.parentElement);
    qs.forEach((q, qi) => {
      const ans = +q.dataset.answer;
      const qt = $(".qtext", q);
      if (qt && !$(".qn", qt)) qt.insertAdjacentHTML("afterbegin", `<span class="qn">${qi + 1}</span>`);
      $$(".opt", q).forEach((opt, oi) => opt.addEventListener("click", () => {
        if (q.classList.contains("answered")) return;
        q.classList.add("answered"); answered++;
        $$(".opt", q)[ans].classList.add("right");
        if (oi === ans) { right++; } else { opt.classList.add("wrong"); }
        if (score) score.textContent = `${right} / ${qs.length}`;
        if (answered === qs.length) {
          if (right === qs.length) { confetti(40); say("<b>Perfect score!</b> You're the bee's knees. 🐝"); }
          else say(`<b>${right}/${qs.length}</b> — read the explanations, then try the lab. Every bee starts as a larva.`);
        }
      }));
    });
  });

  /* ---------- copy buttons on code blocks */
  $$("pre > code").forEach((code) => {
    const pre = code.parentElement; pre.style.position = "relative";
    const b = document.createElement("button");
    b.textContent = "copy"; b.className = "icon-btn";
    Object.assign(b.style, { position: "absolute", top: "10px", right: "10px", width: "auto", height: "28px", padding: "0 10px", font: "600 .72rem var(--font-mono)", background: "#2f281d", color: "#F6EFD9", borderColor: "#4a3e26" });
    b.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(code.innerText); b.textContent = "copied ✓"; } catch (e) { b.textContent = "select + ⌘C"; }
      setTimeout(() => (b.textContent = "copy"), 1400);
    });
    pre.appendChild(b);
  });

  /* ---------- Buzz the Backprop Bee */
  const TIPS = [
    "Tip: <b>always</b> plot your data before you model it. Bees inspect every flower.",
    "If your loss is NaN, check your learning rate first. Then your log(0)s.",
    "Gradient boosting still wins most tabular Kaggle comps in 2026. Respect the trees. 🌳",
    "Attention is just a soft, differentiable dictionary lookup. That's it. That's the trick.",
    "Calibrated probabilities are a kindness to whoever uses your model downstream.",
    "Flow matching: draw a straight line from noise to data, then learn the velocity. Beautiful.",
    "Warmup exists because Adam's second-moment estimates are garbage for the first few steps.",
    "Evals are the unit tests of ML. Write them first, like a good bee writes its honeycomb.",
    "Weight decay + patience = grokking. Sometimes understanding arrives late. 🍯",
    "A reasoning model is just an LLM that RL taught to think out loud before answering.",
    "Never trust a benchmark you didn't look at the examples of.",
    "LoRA: most of the update you need lives in a tiny low-rank subspace. Wild, right?",
  ];
  const LAB_CHEERS = [
    "<b>Lab complete!</b> Honey points awarded. 🍯",
    "<b>Buzzworthy!</b> One more cell in the honeycomb.",
    "<b>Nice!</b> Your gradients are flowing beautifully.",
    "<b>Done!</b> Treat yourself to a snack (and maybe a stretch goal).",
  ];
  const pick = (a) => a[Math.floor(Math.random() * a.length)];
  const toast = document.createElement("div"); toast.className = "toast"; document.body.appendChild(toast);
  let tt;
  function say(html) {
    toast.innerHTML = html; toast.classList.add("show");
    clearTimeout(tt); tt = setTimeout(() => toast.classList.remove("show"), 5200);
  }
  const bee = $(".flybee");
  bee && bee.addEventListener("click", () => say(pick(TIPS)));
  window.hiveSay = say;

  function confetti(n) {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const icons = ["🐝", "🍯", "⬢", "✨", "🌼"];
    for (let i = 0; i < n; i++) {
      const s = document.createElement("span"); s.className = "confetti"; s.textContent = pick(icons);
      s.style.left = Math.random() * 100 + "vw"; s.style.animationDuration = 1.8 + Math.random() * 2 + "s";
      s.style.fontSize = 14 + Math.random() * 18 + "px";
      document.body.appendChild(s); setTimeout(() => s.remove(), 4200);
    }
  }
  window.hiveConfetti = confetti;

  /* ---------- KaTeX + highlight.js (loaded with defer) */
  addEventListener("load", () => {
    if (window.renderMathInElement) {
      renderMathInElement(document.body, {
        delimiters: [{ left: "$$", right: "$$", display: true }, { left: "\\(", right: "\\)", display: false }, { left: "$", right: "$", display: false }],
        ignoredClasses: ["no-math"], throwOnError: false,
      });
    }
    if (window.hljs) $$("pre code").forEach((c) => hljs.highlightElement(c));
  });
})();
