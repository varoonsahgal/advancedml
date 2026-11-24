/* Gradient Hive — interactive widgets.
   Any element <div data-widget="NAME"></div> is turned into a live widget.
   Widgets: hero, flow, gd, biasvar, sampling, chinchilla, kvcache, lora, majority */
(function () {
  "use strict";
  const C = { honey: "#F5B700", ink: "#1F1B16", coral: "#FF6B5B", teal: "#1FA39A", indigo: "#3D4DB7", plum: "#9B5DE5", cream: "#FFF8DC", night: "#16130E", card: "#FFFDF4", grey: "#b9ae93" };
  const h = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstChild; };
  const fmt = (x, d = 2) => (Math.abs(x) >= 1e4 || (Math.abs(x) < 1e-2 && x !== 0)) ? x.toExponential(d) : x.toFixed(d);
  const human = (x) => { const u = [["T", 1e12], ["B", 1e9], ["M", 1e6], ["K", 1e3]]; for (const [s, v] of u) if (Math.abs(x) >= v) return (x / v).toFixed(x / v >= 100 ? 0 : 1) + s; return x.toFixed(0); };
  const randn = () => { let u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  function fitCanvas(cv, aspect) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.parentElement.clientWidth || 600;
    const hh = aspect ? Math.round(w / aspect) : (cv.parentElement.clientHeight || w);
    cv.width = Math.round(w * dpr); cv.height = Math.round(hh * dpr);
    cv.style.height = hh + "px";
    const ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w, h: hh };
  }
  function shell(el, title, sub, bodyHtml, stack) {
    el.classList.add("widget");
    el.innerHTML = `<div class="widget-head"><i class="dot"></i><b>${title}</b><span>${sub}</span></div><div class="widget-body ${stack ? "stack" : ""}">${bodyHtml}</div>`;
  }
  function lerpColor(stops, t) {
    t = Math.max(0, Math.min(1, t)); const n = stops.length - 1; const i = Math.min(n - 1, Math.floor(t * n)); const f = t * n - i;
    const a = stops[i], b = stops[i + 1];
    return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
  }
  const hex2rgb = (x) => [parseInt(x.slice(1, 3), 16), parseInt(x.slice(3, 5), 16), parseInt(x.slice(5, 7), 16)];

  /* =====================================================================
     FLOW MATCHING ENGINE — exact marginal velocity for an empirical target
     x_t = (1-t)·x0 + t·x1,  x0 ~ N(0,I),  x1 ~ uniform over target points
     v(x,t) = (E[x1|x_t=x] - (1-σ)x) / (1 - (1-σ)t)
     ===================================================================== */
  const SIG = 0.03;
  function velocity(px, py, t, tx, ty, out) {
    const M = tx.length, s = 1 - (1 - SIG) * t, inv = 1 / (2 * s * s);
    for (let i = 0; i < px.length; i++) {
      const x = px[i], y = py[i];
      let best = Infinity;
      for (let j = 0; j < M; j++) { const dx = x - t * tx[j], dy = y - t * ty[j]; const d = dx * dx + dy * dy; if (d < best) best = d; }
      let sw = 0, sx = 0, sy = 0;
      for (let j = 0; j < M; j++) {
        const dx = x - t * tx[j], dy = y - t * ty[j];
        const w = Math.exp(-(dx * dx + dy * dy - best) * inv);
        sw += w; sx += w * tx[j]; sy += w * ty[j];
      }
      out[0][i] = (sx / sw - (1 - SIG) * x) / s;
      out[1][i] = (sy / sw - (1 - SIG) * y) / s;
    }
  }
  function shapePoints(kind, M, text) {
    const X = [], Y = [];
    const add = (x, y) => { X.push(x); Y.push(y); };
    if (kind === "heart") for (let i = 0; i < M; i++) { const t = Math.random() * 2 * Math.PI; add(16 * Math.sin(t) ** 3 / 9.5, (13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) / 9.5 + 0.15); }
    else if (kind === "spiral") for (let i = 0; i < M; i++) { const t = Math.sqrt(Math.random()) * 3.3 * Math.PI; add(t * Math.cos(t) / 5.6, t * Math.sin(t) / 5.6); }
    else if (kind === "moons") for (let i = 0; i < M; i++) { const t = Math.random() * Math.PI; if (i % 2) add(Math.cos(t) - 0.5, Math.sin(t) - 0.25); else add(1 - Math.cos(t) - 0.5, -Math.sin(t) + 0.25); }
    else if (kind === "hex") for (let i = 0; i < M; i++) { const k = Math.floor(Math.random() * 6), f = Math.random(); const r = i % 3 === 0 ? 0.8 : 1.6; const a0 = k * Math.PI / 3 + Math.PI / 6, a1 = a0 + Math.PI / 3; add(r * ((1 - f) * Math.cos(a0) + f * Math.cos(a1)), r * ((1 - f) * Math.sin(a0) + f * Math.sin(a1))); }
    else { // text
      const cv = document.createElement("canvas"); cv.width = 600; cv.height = 300;
      const g = cv.getContext("2d"); g.fillStyle = "#000"; g.textAlign = "center"; g.textBaseline = "middle";
      const s = (text || "ML").slice(0, 10);
      let fs = 220; g.font = `900 ${fs}px Inter, Arial, sans-serif`;
      while (g.measureText(s).width > 560 && fs > 30) { fs -= 8; g.font = `900 ${fs}px Inter, Arial, sans-serif`; }
      g.fillText(s, 300, 155);
      const d = g.getImageData(0, 0, 600, 300).data, pts = [];
      for (let y = 0; y < 300; y += 2) for (let x = 0; x < 600; x += 2) if (d[(y * 600 + x) * 4 + 3] > 128) pts.push([x, y]);
      for (let i = 0; i < M && pts.length; i++) { const p = pts[Math.floor(Math.random() * pts.length)]; add((p[0] - 300) / 140, -(p[1] - 150) / 140); }
    }
    return [Float32Array.from(X), Float32Array.from(Y)];
  }

  function makeFlowSim(N, M) {
    const sim = { N, M, px: new Float32Array(N), py: new Float32Array(N), sx: new Float32Array(N), sy: new Float32Array(N), hue: [], tx: null, ty: null, t: 0, k: 0, K: 60, out: [new Float32Array(N), new Float32Array(N)] };
    const pal = [C.honey, C.coral, C.plum, C.teal, C.cream].map(hex2rgb);
    sim.reset = function () {
      for (let i = 0; i < N; i++) { sim.px[i] = randn(); sim.py[i] = randn(); }
      for (let i = 0; i < N; i++) { const a = Math.atan2(sim.py[i], sim.px[i]); sim.hue[i] = lerpColor(pal, (a / Math.PI + 1) / 2); }
      sim.sx.set(sim.px); sim.sy.set(sim.py); sim.t = 0; sim.k = 0;
    };
    sim.target = function (kind, text) { [sim.tx, sim.ty] = shapePoints(kind, M, text); };
    sim.step = function () { // one Euler step of size 1/K
      if (sim.k >= sim.K) return false;
      const dt = 1 / sim.K, t = Math.min(sim.k * dt, 0.985);
      velocity(sim.px, sim.py, t, sim.tx, sim.ty, sim.out);
      sim.sx.set(sim.px); sim.sy.set(sim.py);
      for (let i = 0; i < N; i++) { sim.px[i] += dt * sim.out[0][i]; sim.py[i] += dt * sim.out[1][i]; }
      sim.k++; sim.t = sim.k * dt; return true;
    };
    return sim;
  }

  /* ----------------------------------------------------------- HERO */
  function hero(el) {
    el.innerHTML = `<canvas></canvas><div class="stage-tag"><b>LIVE ▸ flow matching</b><br>Gaussian noise → data by integrating dx/dt = v(x,t). Same math as modern image generators. You'll build it on Day 4.</div><div class="stage-ui"></div>`;
    const cv = el.querySelector("canvas"), ui = el.querySelector(".stage-ui");
    const small = innerWidth < 700;
    const sim = makeFlowSim(small ? 700 : 1500, small ? 220 : 340);
    const shapes = [["ML", "text", "ML"], ["♥", "heart"], ["spiral", "spiral"], ["2026", "text", "2026"], ["⬢ hive", "hex"], ["moons", "moons"]];
    let cur = 0, phase = "flow", hold = 0, raf, W, H, ctx, back = 0, from = null;
    shapes.forEach(([lab], i) => { const b = h(`<button>${lab}</button>`); b.onclick = () => { cur = i; start(); }; ui.appendChild(b); });
    function resize() { ({ ctx, w: W, h: H } = fitCanvas(cv)); ctx.fillStyle = C.night; ctx.fillRect(0, 0, W, H); }
    function start() {
      [...ui.children].forEach((b, i) => b.classList.toggle("on", i === cur));
      const s = shapes[cur]; sim.target(s[1], s[2]);
      if (phase === "hold" || phase === "flow") { from = [Float32Array.from(sim.px), Float32Array.from(sim.py)]; }
      sim.reset(); sim.K = 70; phase = from ? "back" : "flow"; back = 0;
    }
    const toScreen = (x, y) => { const s = Math.min(W, H) / 4.6; return [W / 2 + x * s, H / 2 - y * s]; };
    function draw() {
      ctx.fillStyle = "rgba(22,19,14,0.20)"; ctx.fillRect(0, 0, W, H);
      if (phase === "back") { // dissolve previous shape back into the fresh noise along straight conditional paths
        back += 0.035; const f = Math.min(1, back), e = f * f * (3 - 2 * f);
        for (let i = 0; i < sim.N; i++) {
          const x = from[0][i] * (1 - e) + sim.px[i] * e, y = from[1][i] * (1 - e) + sim.py[i] * e;
          const [a, b] = toScreen(x, y); const c = sim.hue[i];
          ctx.fillStyle = `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},0.85)`; ctx.fillRect(a - 1, b - 1, 2, 2);
        }
        if (f >= 1) { phase = "flow"; from = null; }
      } else {
        if (phase === "flow") { if (!sim.step()) { phase = "hold"; hold = 0; } }
        else if (++hold > 150) { cur = (cur + 1) % shapes.length; start(); }
        for (let i = 0; i < sim.N; i++) {
          const [a, b] = toScreen(sim.sx[i], sim.sy[i]), [c2, d2] = toScreen(sim.px[i], sim.py[i]); const c = sim.hue[i];
          const col = `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},0.92)`;
          if (phase !== "hold") { ctx.strokeStyle = col; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(c2 + 0.01, d2 + 0.01); ctx.stroke(); }
          ctx.fillStyle = col; const sz = phase === "hold" ? 2.4 : 1.6; ctx.fillRect(c2 - sz / 2, d2 - sz / 2, sz, sz);
        }
        if (phase === "hold") { sim.sx.set(sim.px); sim.sy.set(sim.py); }
      }
      raf = requestAnimationFrame(draw);
    }
    resize(); addEventListener("resize", resize);
    sim.target("text", "ML"); sim.reset(); start();
    if (reduced) { sim.K = 40; while (sim.step()); phase = "hold"; for (let i = 0; i < 3; i++) draw(); cancelAnimationFrame(raf); return; }
    const vis = new IntersectionObserver((es) => es.forEach((e) => { cancelAnimationFrame(raf); if (e.isIntersecting) raf = requestAnimationFrame(draw); }));
    vis.observe(el);
  }

  /* ----------------------------------------------------------- FLOW widget */
  function flow(el) {
    shell(el, "Flow-Matching Studio", "noise → data, one Euler step at a time", `
      <div class="canvas-wrap dark"><canvas></canvas></div>
      <div class="controls">
        <label>Target distribution<div class="seg" data-k="shape"><button data-v="heart" class="on">♥ heart</button><button data-v="spiral">spiral</button><button data-v="moons">moons</button><button data-v="hex">hive</button><button data-v="text">text</button></div></label>
        <label>Your text <input type="text" value="Buzz" maxlength="8"></label>
        <label>Euler steps (NFE)<div class="seg" data-k="steps"><button data-v="1">1</button><button data-v="2">2</button><button data-v="4">4</button><button data-v="8">8</button><button data-v="32" class="on">32</button><button data-v="100">100</button></div></label>
        <label class="row" style="flex-direction:row;align-items:center;gap:8px"><input type="checkbox" checked style="accent-color:#F5B700"> draw trajectories</label>
        <div class="btns"><button class="b honey" data-act="run">▶ Sample</button><button class="b" data-act="noise">↺ New noise</button></div>
        <div class="readout">t = <b class="t">0.00</b> · step <b class="k">0</b>/<b class="K">32</b><br>particles 1200 · data points 300</div>
        <p class="hint">🔮 Predict first: what does a <b>single</b> Euler step produce? (Hint: at t=0 the velocity points every particle toward the <i>mean</i> of the data.)</p>
      </div>`);
    const cv = el.querySelector("canvas"), tin = el.querySelector("input[type=text]"), trails = el.querySelector("input[type=checkbox]");
    const sim = makeFlowSim(1200, 300); let shape = "heart", K = 32, raf, ctx, W, H, running = false, sub = 0, perStep = 3;
    const seg = (k, f) => el.querySelectorAll(`[data-k=${k}] button`).forEach((b) => b.onclick = () => { el.querySelectorAll(`[data-k=${k}] button`).forEach((x) => x.classList.toggle("on", x === b)); f(b.dataset.v); });
    seg("shape", (v) => { shape = v; run(false); }); seg("steps", (v) => { K = +v; run(false); });
    tin.addEventListener("change", () => { shape = "text"; el.querySelectorAll("[data-k=shape] button").forEach((x) => x.classList.toggle("on", x.dataset.v === "text")); run(false); });
    el.querySelector("[data-act=run]").onclick = () => run(false);
    el.querySelector("[data-act=noise]").onclick = () => run(true);
    const S = () => Math.min(W, H) / 4.8;
    const P = (x, y) => [W / 2 + x * S(), H / 2 - y * S()];
    function clear() { ctx.fillStyle = C.night; ctx.fillRect(0, 0, W, H); }
    function dots(xs, ys, col, r) { ctx.fillStyle = col; for (let i = 0; i < xs.length; i++) { const [a, b] = P(xs[i], ys[i]); ctx.fillRect(a - r / 2, b - r / 2, r, r); } }
    let keepNoise = null;
    function run(newNoise) {
      sim.target(shape, tin.value || "Buzz");
      if (newNoise || !keepNoise) { sim.reset(); keepNoise = [Float32Array.from(sim.px), Float32Array.from(sim.py)]; }
      else { sim.px.set(keepNoise[0]); sim.py.set(keepNoise[1]); sim.sx.set(sim.px); sim.sy.set(sim.py); sim.k = 0; sim.t = 0; }
      sim.K = K; perStep = Math.max(1, Math.round(60 / K)); sub = 0; clear();
      ctx.globalAlpha = 0.5; dots(sim.tx, sim.ty, "#4a3e26", 3); ctx.globalAlpha = 1;
      dots(sim.px, sim.py, C.indigo, 2);
      el.querySelector(".K").textContent = K;
      if (!running) { running = true; raf = requestAnimationFrame(loop); }
    }
    function loop() {
      if (sub === 0) { if (!sim.step()) { running = false; dots(sim.px, sim.py, C.cream, 2.4); return; } }
      const f = (sub + 1) / perStep;
      if (!trails.checked) { clear(); }
      for (let i = 0; i < sim.N; i++) {
        const x0 = sim.sx[i] + (sim.px[i] - sim.sx[i]) * (sub / perStep), y0 = sim.sy[i] + (sim.py[i] - sim.sy[i]) * (sub / perStep);
        const x1 = sim.sx[i] + (sim.px[i] - sim.sx[i]) * f, y1 = sim.sy[i] + (sim.py[i] - sim.sy[i]) * f;
        const [a, b] = P(x0, y0), [c, d] = P(x1, y1); const col = sim.hue[i];
        ctx.strokeStyle = `rgba(${col[0] | 0},${col[1] | 0},${col[2] | 0},${trails.checked ? 0.35 : 0.95})`; ctx.lineWidth = trails.checked ? 0.8 : 2.2;
        ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(c + 0.01, d + 0.01); ctx.stroke();
      }
      sub = (sub + 1) % perStep;
      el.querySelector(".t").textContent = (sim.t - (sub ? (1 - sub / perStep) / K : 0)).toFixed(2); el.querySelector(".k").textContent = sim.k;
      raf = requestAnimationFrame(loop);
    }
    ({ ctx, w: W, h: H } = fitCanvas(cv, 1.25));
    addEventListener("resize", () => { ({ ctx, w: W, h: H } = fitCanvas(cv, 1.25)); run(false); });
    run(true);
  }

  /* ----------------------------------------------------------- GD widget */
  const FUNS = {
    banana: { name: "Rosenbrock banana", f: (x, y) => (1 - x) ** 2 + 100 * (y - x * x) ** 2, g: (x, y) => [-2 * (1 - x) - 400 * x * (y - x * x), 200 * (y - x * x)], dom: [-2.2, 2.2, -1.2, 3.0], start: [-1.7, 2.6], lrs: { SGD: 6e-4, Momentum: 3e-4, RMSProp: 1e-2, Adam: 3e-2, Lion: 3e-3 }, min: [1, 1] },
    bowl: { name: "Ill-conditioned bowl", f: (x, y) => 0.5 * (x * x + 30 * y * y), g: (x, y) => [x, 30 * y], dom: [-3.2, 3.2, -2, 2], start: [-3, 1.6], lrs: { SGD: 0.06, Momentum: 0.006, RMSProp: 3e-3, Adam: 0.03, Lion: 0.01 }, min: [0, 0] },
    bumpy: { name: "Bumpy multi-modal", f: (x, y) => 0.6 * Math.sin(1.3 * x) * Math.cos(1.1 * y) + 0.05 * (x * x + y * y) - 0.9 * Math.exp(-((x - 1.6) ** 2 + (y + 1) ** 2)) - 0.7 * Math.exp(-((x + 2.1) ** 2 + (y - 1.4) ** 2) / 0.8), g: null, dom: [-5, 5, -3.1, 3.1], start: [-4, -2.4], lrs: { SGD: 0.03, Momentum: 3e-3, RMSProp: 0.01, Adam: 0.03, Lion: 0.01 }, min: [1.6, -1] },
    saddle: { name: "Saddle point", f: (x, y) => x * x - y * y + 0.12 * y ** 4, g: (x, y) => [2 * x, -2 * y + 0.48 * y ** 3], dom: [-3, 3, -3.2, 3.2], start: [-2.6, 0.001], lrs: { SGD: 3e-3, Momentum: 3e-4, RMSProp: 3e-3, Adam: 0.01, Lion: 3e-3 }, min: [0, 2.89] },
  };
  const OPTS = { SGD: C.ink, Momentum: C.coral, RMSProp: C.indigo, Adam: C.honey, Lion: C.plum };
  function stepper(name) {
    let m = [0, 0], v = [0, 0], t = 0;
    return (p, g, lr) => {
      t++;
      if (name === "SGD") return [p[0] - lr * g[0], p[1] - lr * g[1]];
      if (name === "Momentum") { m = [0.9 * m[0] + g[0], 0.9 * m[1] + g[1]]; return [p[0] - lr * m[0], p[1] - lr * m[1]]; }
      if (name === "RMSProp") { v = [0.99 * v[0] + 0.01 * g[0] ** 2, 0.99 * v[1] + 0.01 * g[1] ** 2]; return [p[0] - lr * g[0] / (Math.sqrt(v[0]) + 1e-8), p[1] - lr * g[1] / (Math.sqrt(v[1]) + 1e-8)]; }
      if (name === "Adam") {
        m = [0.9 * m[0] + 0.1 * g[0], 0.9 * m[1] + 0.1 * g[1]]; v = [0.999 * v[0] + 0.001 * g[0] ** 2, 0.999 * v[1] + 0.001 * g[1] ** 2];
        const bc1 = 1 - 0.9 ** t, bc2 = 1 - 0.999 ** t;
        return [p[0] - lr * (m[0] / bc1) / (Math.sqrt(v[0] / bc2) + 1e-8), p[1] - lr * (m[1] / bc1) / (Math.sqrt(v[1] / bc2) + 1e-8)];
      }
      if (name === "Lion") { const u = [Math.sign(0.9 * m[0] + 0.1 * g[0]), Math.sign(0.9 * m[1] + 0.1 * g[1])]; m = [0.99 * m[0] + 0.01 * g[0], 0.99 * m[1] + 0.01 * g[1]]; return [p[0] - lr * u[0], p[1] - lr * u[1]]; }
    };
  }
  function gd(el) {
    shell(el, "Optimizer Arena", "click anywhere on the landscape to drop a ball", `
      <div class="canvas-wrap"><canvas style="cursor:crosshair"></canvas></div>
      <div class="controls">
        <label>Landscape<select data-k="fn">${Object.entries(FUNS).map(([k, v]) => `<option value="${k}">${v.name}</option>`).join("")}</select></label>
        <label>Racers<div class="seg" data-k="opt">${Object.keys(OPTS).map((k) => `<button data-v="${k}" class="${k === "Lion" ? "" : "on"}" style="border-left:4px solid ${OPTS[k]}">${k}</button>`).join("")}</div></label>
        <label><span class="row">LR multiplier <output class="lro"></output></span><input type="range" min="-1" max="1" step="0.05" value="0" data-k="lr"></label>
        <div class="btns"><button class="b honey" data-act="go">▶ Race</button><button class="b" data-act="reset">Reset</button></div>
        <div class="readout lb">Click the map to choose a start.</div>
        <p class="hint">Each racer starts from a hand-tuned learning rate; the slider scales them all. On the <b>bowl</b>, SGD zig-zags across the narrow valley while Adam rescales each axis. On the <b>saddle</b>, see who escapes first. Push to ×10 and see who survives 💥.</p>
      </div>`);
    const cv = el.querySelector("canvas"), sel = el.querySelector("select"), lrIn = el.querySelector("[data-k=lr]"), lro = el.querySelector(".lro"), lb = el.querySelector(".lb");
    let F = FUNS.banana, ctx, W, H, bg, start = null, racers = [], raf, active = new Set(["SGD", "Momentum", "RMSProp", "Adam"]);
    el.querySelectorAll("[data-k=opt] button").forEach((b) => b.onclick = () => { b.classList.toggle("on"); b.classList.contains("on") ? active.add(b.dataset.v) : active.delete(b.dataset.v); go(); });
    const grad = (x, y) => F.g ? F.g(x, y) : [(F.f(x + 1e-4, y) - F.f(x - 1e-4, y)) / 2e-4, (F.f(x, y + 1e-4) - F.f(x, y - 1e-4)) / 2e-4];
    const toS = (x, y) => [(x - F.dom[0]) / (F.dom[1] - F.dom[0]) * W, (1 - (y - F.dom[2]) / (F.dom[3] - F.dom[2])) * H];
    const toW = (a, b) => [F.dom[0] + a / W * (F.dom[1] - F.dom[0]), F.dom[2] + (1 - b / H) * (F.dom[3] - F.dom[2])];
    const mult = () => 10 ** +lrIn.value;
    function render() {
      ({ ctx, w: W, h: H } = fitCanvas(cv, 1.2));
      const R = 2, gw = Math.ceil(W / R), gh = Math.ceil(H / R), vals = new Float32Array(gw * gh);
      let lo = Infinity, hi = -Infinity;
      for (let j = 0; j < gh; j++) for (let i = 0; i < gw; i++) { const [x, y] = toW(i * R, j * R); let v = F.f(x, y); v = F === FUNS.bumpy ? v : Math.log1p(v - (F === FUNS.saddle ? -12 : 0)); vals[j * gw + i] = v; lo = Math.min(lo, v); hi = Math.max(hi, v); }
      const off = document.createElement("canvas"); off.width = gw; off.height = gh; const oc = off.getContext("2d"); const img = oc.createImageData(gw, gh);
      const stops = ["#1FA39A", "#8fd1c6", "#FFFDF4", "#FFE680", "#F5B700"].map(hex2rgb).reverse();
      for (let k = 0; k < gw * gh; k++) {
        const t = (vals[k] - lo) / (hi - lo); const band = Math.floor(t * 22);
        const i = k % gw, nb = i + 1 < gw ? Math.floor((vals[k + 1] - lo) / (hi - lo) * 22) : band, nb2 = k + gw < gw * gh ? Math.floor((vals[k + gw] - lo) / (hi - lo) * 22) : band;
        let c = lerpColor(stops, t); if (nb !== band || nb2 !== band) c = c.map((z) => z * 0.86);
        img.data.set([c[0], c[1], c[2], 255], k * 4);
      }
      oc.putImageData(img, 0, 0); bg = off; paint();
    }
    function paint() {
      ctx.imageSmoothingEnabled = true; ctx.drawImage(bg, 0, 0, W, H);
      const [mx, my] = toS(...F.min); ctx.font = "22px serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillStyle = C.ink; ctx.fillText("★", mx, my);
      for (const r of racers) {
        ctx.strokeStyle = r.col; ctx.lineWidth = r.name === "Adam" ? 3 : r.name === "SGD" ? 1.4 : 2.2; ctx.beginPath();
        r.path.forEach((p, i) => { const [a, b] = toS(...p); i ? ctx.lineTo(a, b) : ctx.moveTo(a, b); }); ctx.stroke();
        const [a, b] = toS(...r.p); ctx.fillStyle = r.col; ctx.beginPath(); ctx.arc(a, b, 6, 0, 7); ctx.fill(); ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.stroke();
      }
      if (start) { const [a, b] = toS(...start); ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(a, b, 7, 0, 7); ctx.fill(); }
    }
    function go() {
      cancelAnimationFrame(raf); if (!start) start = F.start.slice();
      racers = [...active].map((n) => ({ name: n, col: OPTS[n], p: start.slice(), path: [start.slice()], st: stepper(n), dead: false }));
      let it = 0; const M = mult(); const span = Math.max(F.dom[1] - F.dom[0], F.dom[3] - F.dom[2]);
      const tick = () => {
        for (let s = 0; s < 6; s++) {
          it++;
          for (const r of racers) {
            if (r.dead) continue;
            const g = grad(...r.p); let np = r.st(r.p, g, F.lrs[r.name] * M);
            if (!isFinite(np[0]) || !isFinite(np[1]) || Math.abs(np[0]) > span * 1.5 || Math.abs(np[1]) > span * 1.5) { r.dead = true; continue; }
            r.p = np; r.path.push(np);
          }
        }
        paint();
        lb.innerHTML = `step <b>${it}</b><br>` + racers.map((r) => `<span style="color:${r.col === C.ink ? "inherit" : r.col}">■</span> ${r.name} <span style="opacity:.6">(lr ${(F.lrs[r.name] * M).toPrecision(2)})</span>: ${r.dead ? "💥 left the map" : "f = " + fmt(F.f(...r.p), 3)}`).join("<br>");
        if (it < 1500) raf = requestAnimationFrame(tick);
      };
      tick();
    }
    function setFn(k) { F = FUNS[k]; lrIn.value = 0; lro.textContent = "×1.00"; start = null; racers = []; render(); go(); }
    sel.onchange = () => setFn(sel.value);
    lrIn.oninput = () => { lro.textContent = "×" + mult().toFixed(2); }; lrIn.onchange = go;
    el.querySelector("[data-act=go]").onclick = go;
    el.querySelector("[data-act=reset]").onclick = () => setFn(sel.value);
    cv.addEventListener("pointerdown", (e) => { const r = cv.getBoundingClientRect(); start = toW(e.clientX - r.left, e.clientY - r.top); go(); });
    addEventListener("resize", () => render());
    setFn("banana");
  }

  /* ----------------------------------------------------------- Bias–variance widget */
  function legendre(x, d) { const P = [1, x]; for (let n = 1; n < d; n++) P.push(((2 * n + 1) * x * P[n] - n * P[n - 1]) / (n + 1)); return P.slice(0, d + 1); }
  function solve(A, b) { const n = b.length; A = A.map((r, i) => [...r, b[i]]); for (let c = 0; c < n; c++) { let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r; [A[c], A[p]] = [A[p], A[c]]; const v = A[c][c] || 1e-12; for (let r = 0; r < n; r++) if (r !== c) { const f = A[r][c] / v; for (let k = c; k <= n; k++) A[r][k] -= f * A[c][k]; } } return A.map((r, i) => r[n] / (r[i] || 1e-12)); }
  function polyfit(xs, ys, d, lam) {
    const Phi = xs.map((x) => legendre(2 * x - 1, d)), D = d + 1;
    const A = Array.from({ length: D }, (_, i) => Array.from({ length: D }, (_, j) => Phi.reduce((s, r) => s + r[i] * r[j], 0) + (i === j ? lam + 1e-9 : 0)));
    const b = Array.from({ length: D }, (_, i) => Phi.reduce((s, r, k) => s + r[i] * ys[k], 0));
    const w = solve(A, b); return (x) => legendre(2 * x - 1, d).reduce((s, v, i) => s + v * w[i], 0);
  }
  function biasvar(el) {
    shell(el, "Bias–Variance Lab", "fit polynomials, resample, watch the U-curve appear", `
      <div class="canvas-wrap"><canvas></canvas></div>
      <div class="controls">
        <label><span class="row">Degree (capacity) <output class="o-d"></output></span><input type="range" min="0" max="15" value="3" data-k="d"></label>
        <label><span class="row">Training points <output class="o-n"></output></span><input type="range" min="6" max="120" value="20" data-k="n"></label>
        <label><span class="row">Noise σ <output class="o-s"></output></span><input type="range" min="0" max="0.8" step="0.02" value="0.3" data-k="s"></label>
        <label><span class="row">Ridge λ <output class="o-l"></output></span><input type="range" min="-8" max="1" step="0.25" value="-8" data-k="l"></label>
        <label class="row" style="flex-direction:row;align-items:center;gap:8px"><input type="checkbox" checked style="accent-color:#F5B700"> show 25 refits (variance)</label>
        <div class="btns"><button class="b honey" data-act="resample">🎲 Resample data</button></div>
        <div class="readout ro"></div>
      </div>`);
    const cv = el.querySelector("canvas"), q = (k) => el.querySelector(`[data-k=${k}]`), ens = el.querySelector("input[type=checkbox]");
    const f = (x) => Math.sin(2 * Math.PI * x);
    let ctx, W, H, data;
    const sample = (n, s) => { const xs = Array.from({ length: n }, () => Math.random()); return [xs, xs.map((x) => f(x) + s * randn())]; };
    function draw() {
      const d = +q("d").value, n = +q("n").value, s = +q("s").value, lam = q("l").value <= -8 ? 0 : 10 ** +q("l").value;
      el.querySelector(".o-d").textContent = d; el.querySelector(".o-n").textContent = n; el.querySelector(".o-s").textContent = s.toFixed(2); el.querySelector(".o-l").textContent = lam ? lam.toExponential(1) : "0";
      if (!data || data[0].length !== n || data.s !== s) { data = sample(n, s); data.s = s; }
      ctx.fillStyle = C.card; ctx.fillRect(0, 0, W, H);
      const X = (x) => 30 + x * (W - 50), Y = (y) => H / 2 - y * (H / 5.2);
      ctx.strokeStyle = "#efe6c8"; ctx.lineWidth = 1; for (let k = -2; k <= 2; k++) { ctx.beginPath(); ctx.moveTo(30, Y(k)); ctx.lineTo(W - 20, Y(k)); ctx.stroke(); }
      const curve = (g, col, lw, a) => { ctx.strokeStyle = col; ctx.globalAlpha = a; ctx.lineWidth = lw; ctx.beginPath(); for (let i = 0; i <= 200; i++) { const x = i / 200; let y = Math.max(-2.6, Math.min(2.6, g(x))); i ? ctx.lineTo(X(x), Y(y)) : ctx.moveTo(X(x), Y(y)); } ctx.stroke(); ctx.globalAlpha = 1; };
      const grid = Array.from({ length: 60 }, (_, i) => (i + 0.5) / 60), preds = [];
      for (let r = 0; r < 25; r++) { const [xs, ys] = sample(n, s); const g = polyfit(xs, ys, d, lam); preds.push(grid.map(g)); if (ens.checked) curve(g, C.honey, 1.4, 0.35); }
      curve(f, C.ink, 2.6, 1);
      const g = polyfit(data[0], data[1], d, lam); curve(g, C.coral, 3.2, 1);
      ctx.fillStyle = C.teal; data[0].forEach((x, i) => { ctx.beginPath(); ctx.arc(X(x), Y(data[1][i]), 4, 0, 7); ctx.fill(); });
      const tr = data[0].reduce((a, x, i) => a + (g(x) - data[1][i]) ** 2, 0) / n;
      const te = grid.reduce((a, x) => a + (g(x) - f(x)) ** 2, 0) / grid.length + s * s;
      let b2 = 0, va = 0; grid.forEach((x, i) => { const m = preds.reduce((a, p) => a + p[i], 0) / preds.length; b2 += (m - f(x)) ** 2; va += preds.reduce((a, p) => a + (p[i] - m) ** 2, 0) / preds.length; });
      b2 /= grid.length; va /= grid.length;
      el.querySelector(".ro").innerHTML = `train MSE <b>${fmt(tr, 3)}</b><br>test MSE &nbsp;<b>${fmt(te, 3)}</b><br>bias² ≈ <b style="color:#1FA39A">${fmt(b2, 3)}</b><br>variance ≈ <b style="color:#FF6B5B">${fmt(Math.min(va, 99), 3)}</b><br><span style="color:#7A6E5A">${d >= n - 1 ? "⚠️ degree ≥ n−1: interpolating noise!" : b2 > 0.04 && b2 > va ? "underfitting (high bias)" : va > 0.06 ? "overfitting (high variance)" : "balanced ✓"}</span>`;
      ctx.font = "600 12px JetBrains Mono, monospace"; ctx.fillStyle = C.ink; ctx.fillText("— truth sin(2πx)", 40, 22); ctx.fillStyle = C.coral; ctx.fillText("— your fit", 200, 22); ctx.fillStyle = "#b98500"; ctx.fillText("— refits on new samples", 300, 22);
    }
    ["d", "n", "s", "l"].forEach((k) => q(k).addEventListener("input", draw)); ens.onchange = draw;
    el.querySelector("[data-act=resample]").onclick = () => { data = null; draw(); };
    const rs = () => { ({ ctx, w: W, h: H } = fitCanvas(cv, 1.5)); draw(); }; addEventListener("resize", rs); rs();
  }

  /* ----------------------------------------------------------- Sampling widget */
  function sampling(el) {
    const words = ["honey", "nectar", "pollen", "flowers", "the", "wax", "royal", "jelly", "sunshine", "math", "rust", "taxes"];
    const logits = [4.1, 3.5, 3.2, 2.9, 2.1, 1.9, 1.2, 1.0, 0.7, -0.2, -1.0, -1.6];
    shell(el, "Decoding Lab", "temperature · top-k · top-p · min-p", `
      <div><div class="bars"></div><div class="gen-out">Click “sample 24” to draw tokens…</div></div>
      <div class="controls">
        <div class="readout">prompt: <b>"The bees made sweet …"</b></div>
        <label><span class="row">Temperature <output class="oT"></output></span><input type="range" min="0.05" max="2.5" step="0.05" value="1" data-k="T"></label>
        <label><span class="row">top-k <output class="oK"></output></span><input type="range" min="1" max="12" value="12" data-k="K"></label>
        <label><span class="row">top-p <output class="oP"></output></span><input type="range" min="0.05" max="1" step="0.01" value="1" data-k="P"></label>
        <label><span class="row">min-p <output class="oM"></output></span><input type="range" min="0" max="0.6" step="0.01" value="0" data-k="M"></label>
        <div class="btns"><button class="b honey" data-act="s">🎲 sample 24</button><button class="b" data-act="r">reset</button></div>
        <div class="readout ent"></div>
      </div>`);
    const q = (k) => el.querySelector(`[data-k=${k}]`), bars = el.querySelector(".bars"), out = el.querySelector(".gen-out");
    bars.innerHTML = words.map((w) => `<div class="bar-row"><span>${w}</span><div class="track"><div class="fill"></div></div><span class="pv"></span></div>`).join("");
    function dist() {
      const T = +q("T").value, K = +q("K").value, Pp = +q("P").value, Mp = +q("M").value;
      const z = logits.map((l) => l / T), mx = Math.max(...z); let p = z.map((v) => Math.exp(v - mx)); const s = p.reduce((a, b) => a + b); p = p.map((v) => v / s);
      const order = p.map((v, i) => i).sort((a, b) => p[b] - p[a]); const keep = new Array(12).fill(true);
      order.forEach((i, r) => { if (r >= K) keep[i] = false; });
      let cum = 0; order.forEach((i) => { if (cum >= Pp) keep[i] = false; cum += p[i]; });
      const pmax = Math.max(...p); p.forEach((v, i) => { if (v < Mp * pmax) keep[i] = false; });
      const kept = p.map((v, i) => keep[i] ? v : 0), ks = kept.reduce((a, b) => a + b); const fin = kept.map((v) => v / ks);
      return { fin, keep, T, K, Pp, Mp };
    }
    function draw() {
      const { fin, keep, T, K, Pp, Mp } = dist();
      el.querySelector(".oT").textContent = T.toFixed(2); el.querySelector(".oK").textContent = K; el.querySelector(".oP").textContent = Pp.toFixed(2); el.querySelector(".oM").textContent = Mp.toFixed(2);
      bars.querySelectorAll(".bar-row").forEach((row, i) => { row.classList.toggle("cut", !keep[i]); row.querySelector(".fill").style.width = (fin[i] * 100).toFixed(1) + "%"; row.querySelector(".pv").textContent = (fin[i] * 100).toFixed(1) + "%"; });
      const H = -fin.reduce((a, v) => a + (v > 0 ? v * Math.log2(v) : 0), 0);
      el.querySelector(".ent").innerHTML = `entropy <b>${H.toFixed(2)} bits</b> · candidates <b>${keep.filter(Boolean).length}</b><br><span style="color:#7A6E5A">${T < 0.3 ? "≈ greedy: deterministic, can loop" : H > 2.8 ? "very creative… maybe too creative (taxes?!)" : "a healthy balance"}</span>`;
    }
    el.querySelectorAll("input").forEach((i) => i.addEventListener("input", draw));
    el.querySelector("[data-act=s]").onclick = () => {
      const { fin } = dist(); const toks = [];
      for (let n = 0; n < 24; n++) { let r = Math.random(), i = 0; while (i < 11 && r > fin[i]) { r -= fin[i]; i++; } toks.push(words[i]); }
      out.innerHTML = toks.map((t) => `<span class="tok">${t}</span>`).join("");
    };
    el.querySelector("[data-act=r]").onclick = () => { q("T").value = 1; q("K").value = 12; q("P").value = 1; q("M").value = 0; draw(); };
    draw();
  }

  /* ----------------------------------------------------------- Chinchilla calculator */
  function chinchilla(el) {
    shell(el, "Compute-Optimal Planner", "Chinchilla parametric fit (Hoffmann et al., 2022)", `
      <div style="width:100%"><div class="calc">
        <label>Compute budget C (FLOPs): <output class="oc"></output><input type="range" min="18" max="26.5" step="0.05" value="23" data-k="c"></label>
        <label>GPU <select data-k="g"><option value="989e12">H100 (≈989 TFLOP/s bf16 dense)</option><option value="312e12">A100 (≈312 TFLOP/s bf16)</option><option value="2250e12">B200 (≈2.25 PFLOP/s bf16 dense)</option></select></label>
        <label># GPUs <input type="number" value="256" min="1" data-k="n"></label>
        <label>MFU (utilization) <input type="number" value="0.4" step="0.05" min="0.05" max="0.9" data-k="m"></label>
      </div><div class="calc-out"></div><p class="hint" style="padding:0 20px 18px;margin:0">L(N,D) = 1.69 + 406.4/N<sup>0.34</sup> + 410.7/D<sup>0.28</sup>, C ≈ 6ND. Different fitting approaches in the paper give somewhat different splits; the popular rule of thumb is ≈20 tokens per parameter. Production models are often deliberately “over-trained” far past this point because smaller models are cheaper to serve.</p></div>`, true);
    const q = (k) => el.querySelector(`[data-k=${k}]`);
    const E = 1.69, A = 406.4, B = 410.7, a = 0.34, b = 0.28;
    function draw() {
      const Cf = 10 ** +q("c").value; el.querySelector(".oc").textContent = Cf.toExponential(1);
      const G = ((a * A) / (b * B)) ** (1 / (a + b));
      const N = G * (Cf / 6) ** (b / (a + b)), D = Cf / (6 * N), L = E + A / N ** a + B / D ** b;
      const N20 = Math.sqrt(Cf / 120), D20 = 20 * N20;
      const secs = Cf / (+q("g").value * +q("n").value * +q("m").value);
      el.querySelector(".calc-out").innerHTML = `
        <div><b>${human(N)}</b><span>params N* (parametric fit)</span></div>
        <div><b>${human(D)}</b><span>tokens D* · ${(D / N).toFixed(0)} tok/param</span></div>
        <div><b>${L.toFixed(3)}</b><span>predicted loss (nats/token)</span></div>
        <div><b>${human(N20)} · ${human(D20)}</b><span>20-tokens/param rule (N · D)</span></div>
        <div><b>${secs / 86400 < 1 ? (secs / 3600).toFixed(1) + " h" : (secs / 86400).toFixed(1) + " days"}</b><span>wall-clock on your cluster</span></div>`;
    }
    el.querySelectorAll("input,select").forEach((i) => i.addEventListener("input", draw)); draw();
  }

  /* ----------------------------------------------------------- KV-cache calculator */
  function kvcache(el) {
    const presets = { "Llama-3-8B-like": [32, 32, 8, 128], "Llama-3-70B-like": [80, 64, 8, 128], "Classic MHA 7B": [32, 32, 32, 128], "Tiny 0.5B (Qwen2.5-like)": [24, 14, 2, 64] };
    shell(el, "KV-Cache Calculator", "why long context is a memory problem", `
      <div style="width:100%"><div class="calc">
        <label>Preset <select data-k="p">${Object.keys(presets).map((k) => `<option>${k}</option>`).join("")}</select></label>
        <label>Layers <input type="number" data-k="L"></label>
        <label>Query heads <input type="number" data-k="Hq"></label>
        <label>KV heads (GQA) <input type="number" data-k="Hkv"></label>
        <label>Head dim <input type="number" data-k="d"></label>
        <label>Context length <input type="number" value="131072" data-k="T"></label>
        <label>Batch (concurrent seqs) <input type="number" value="8" data-k="B"></label>
        <label>Cache dtype <select data-k="b"><option value="2">bf16 / fp16</option><option value="1">fp8</option><option value="0.5">int4</option></select></label>
      </div><div class="calc-out"></div></div>`, true);
    const q = (k) => el.querySelector(`[data-k=${k}]`);
    const load = () => { const [L, Hq, Hkv, d] = presets[q("p").value]; q("L").value = L; q("Hq").value = Hq; q("Hkv").value = Hkv; q("d").value = d; draw(); };
    function draw() {
      const L = +q("L").value, Hq = +q("Hq").value, Hkv = +q("Hkv").value, d = +q("d").value, T = +q("T").value, B = +q("B").value, by = +q("b").value;
      const per = 2 * L * Hkv * d * by, tot = per * T * B, mha = 2 * L * Hq * d * by * T * B;
      el.querySelector(".calc-out").innerHTML = `
        <div><b>${(per / 1024).toFixed(1)} KB</b><span>per token (K and V, all layers)</span></div>
        <div><b>${(tot / 1e9).toFixed(1)} GB</b><span>total cache for batch × context</span></div>
        <div><b>${(mha / 1e9).toFixed(1)} GB</b><span>if it were full MHA (no GQA)</span></div>
        <div><b>${(Hq / Hkv).toFixed(0)}×</b><span>saving from grouped-query attention</span></div>
        <div><b>${Math.ceil(tot / 80e9)}</b><span>× 80 GB GPUs just for the cache</span></div>`;
    }
    q("p").onchange = load; el.querySelectorAll("input,select[data-k=b]").forEach((i) => i.addEventListener("input", draw)); load();
  }

  /* ----------------------------------------------------------- LoRA calculator */
  function lora(el) {
    const presets = { "8B-class (d=4096, ff=14336, 32 layers)": [4096, 14336, 32], "70B-class (d=8192, ff=28672, 80 layers)": [8192, 28672, 80], "0.5B-class (d=896, ff=4864, 24 layers)": [896, 4864, 24] };
    shell(el, "LoRA Budget Calculator", "how few parameters do you really need?", `
      <div style="width:100%"><div class="calc">
        <label>Model <select data-k="p">${Object.keys(presets).map((k) => `<option>${k}</option>`).join("")}</select></label>
        <label>Rank r: <output class="or"></output><input type="range" min="0" max="8" value="4" data-k="r"></label>
        <label>Targets <select data-k="t"><option value="attn">attention (q,k,v,o)</option><option value="all" selected>all linear (attn + MLP)</option></select></label>
        <label>Base weights <select data-k="q"><option value="2">bf16 (LoRA)</option><option value="0.5">4-bit NF4 (QLoRA)</option></select></label>
      </div><div class="calc-out"></div><p class="hint" style="padding:0 20px 18px;margin:0">Approximation: treats q,k,v,o as d×d and the SwiGLU MLP as three d×ff matrices; ignores embeddings, activations and KV-cache. Full fine-tuning with AdamW in mixed precision ≈ 16 bytes/param (weights + grads + two moments + master copy).</p></div>`, true);
    const q = (k) => el.querySelector(`[data-k=${k}]`);
    function draw() {
      const [d, ff, L] = presets[q("p").value], r = 2 ** +q("r").value, all = q("t").value === "all", bq = +q("q").value;
      el.querySelector(".or").textContent = r;
      const mats = [[d, d], [d, d], [d, d], [d, d]].concat(all ? [[d, ff], [d, ff], [ff, d]] : []);
      const base = L * (4 * d * d + 3 * d * ff);
      const full = L * mats.reduce((s, [i, o]) => s + i * o, 0), lr = L * mats.reduce((s, [i, o]) => s + r * (i + o), 0);
      const memFull = base * 16, memLora = base * bq + lr * 16;
      el.querySelector(".calc-out").innerHTML = `
        <div><b>${human(base)}</b><span>params in transformer blocks</span></div>
        <div><b>${human(lr)}</b><span>trainable LoRA params</span></div>
        <div><b>${(100 * lr / base).toFixed(3)}%</b><span>of the model is trained</span></div>
        <div><b>${(memFull / 1e9).toFixed(0)} GB</b><span>full fine-tune memory (≈)</span></div>
        <div><b>${(memLora / 1e9).toFixed(1)} GB</b><span>${bq < 1 ? "QLoRA" : "LoRA"} memory (≈)</span></div>`;
    }
    el.querySelectorAll("input,select").forEach((i) => i.addEventListener("input", draw)); draw();
  }

  /* ----------------------------------------------------------- Majority vote (test-time compute) */
  function majority(el) {
    shell(el, "Test-Time Compute Simulator", "sample N answers, take a vote", `
      <div class="canvas-wrap"><canvas></canvas></div>
      <div class="controls">
        <label><span class="row">Single-sample accuracy p <output class="op"></output></span><input type="range" min="0.1" max="0.9" step="0.01" value="0.4" data-k="p"></label>
        <label><span class="row">Samples N <output class="on"></output></span><input type="range" min="0" max="7" value="4" data-k="n"></label>
        <label><span class="row">Wrong-answer spread <output class="os"></output></span><input type="range" min="1" max="8" value="5" data-k="s"></label>
        <div class="btns"><button class="b honey" data-act="go">🗳 Run one vote</button></div>
        <div class="readout ro"></div>
        <p class="hint">If wrong answers are <b>scattered</b>, voting amplifies a weak signal. If the model's mistakes are <b>correlated</b> (spread=1), voting can make things worse once p &lt; ½ of the top competitor!</p>
      </div>`);
    const cv = el.querySelector("canvas"), q = (k) => el.querySelector(`[data-k=${k}]`);
    let ctx, W, H;
    const probs = () => { const p = +q("p").value, s = +q("s").value; const w = Array.from({ length: s }, (_, i) => 0.6 ** i); const z = w.reduce((a, b) => a + b); return [p, ...w.map((v) => (1 - p) * v / z)]; };
    const draw1 = (pr) => { let r = Math.random(), i = 0; while (i < pr.length - 1 && r > pr[i]) { r -= pr[i]; i++; } return i; };
    const vote = (pr, N) => { const c = new Array(pr.length).fill(0); for (let i = 0; i < N; i++) c[draw1(pr)]++; let best = 0; for (let i = 1; i < c.length; i++) if (c[i] > c[best] || (c[i] === c[best] && Math.random() < 0.5)) best = i; return [best, c]; };
    function curve() {
      const pr = probs(), Ns = [1, 2, 4, 8, 16, 32, 64, 128];
      return Ns.map((N) => { let ok = 0; const T = 600; for (let t = 0; t < T; t++) if (vote(pr, N)[0] === 0) ok++; return [N, ok / T]; });
    }
    function draw(one) {
      const N = 2 ** +q("n").value; el.querySelector(".op").textContent = (+q("p").value).toFixed(2); el.querySelector(".on").textContent = N; el.querySelector(".os").textContent = q("s").value;
      ctx.fillStyle = C.card; ctx.fillRect(0, 0, W, H);
      const pr = probs(), cols = [C.teal, C.coral, C.plum, C.indigo, "#b98500", "#7a6e5a", "#c58f84", "#8a7fb8", "#5f8f8a"];
      const [win, counts] = one || vote(pr, N);
      // ballot dots
      const top = 16, gh = H * 0.45, per = Math.ceil(Math.sqrt(N * (W / gh))), r = Math.min(14, (W - 40) / per / 2.4);
      let k = 0; const seq = []; counts.forEach((c, a) => { for (let i = 0; i < c; i++) seq.push(a); }); seq.sort(() => Math.random() - 0.5);
      seq.forEach((a) => { const cx = 24 + (k % per) * r * 2.4, cy = top + 12 + Math.floor(k / per) * r * 2.4; ctx.fillStyle = cols[a]; ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.fill(); k++; });
      ctx.font = "600 12px JetBrains Mono, monospace"; ctx.fillStyle = C.ink;
      ctx.fillText(`vote winner: ${win === 0 ? "✓ correct" : "✗ wrong answer #" + win}`, 24, H * 0.52);
      // accuracy curve
      const cu = curve(), x0 = 50, x1 = W - 20, y0 = H - 30, y1 = H * 0.6;
      ctx.strokeStyle = "#d9ccaa"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x0, y1); ctx.lineTo(x0, y0); ctx.lineTo(x1, y0); ctx.stroke();
      const X = (i) => x0 + i / (cu.length - 1) * (x1 - x0), Y = (a) => y0 - a * (y0 - y1);
      ctx.strokeStyle = "#cfc3a3"; ctx.setLineDash([4, 4]); ctx.beginPath(); ctx.moveTo(x0, Y(+q("p").value)); ctx.lineTo(x1, Y(+q("p").value)); ctx.stroke(); ctx.setLineDash([]);
      ctx.strokeStyle = C.honey; ctx.lineWidth = 3; ctx.beginPath(); cu.forEach(([, a], i) => i ? ctx.lineTo(X(i), Y(a)) : ctx.moveTo(X(i), Y(a))); ctx.stroke();
      cu.forEach(([n, a], i) => { ctx.fillStyle = n === N ? C.coral : C.ink; ctx.beginPath(); ctx.arc(X(i), Y(a), n === N ? 6 : 3.5, 0, 7); ctx.fill(); ctx.fillStyle = C.ink; ctx.fillText(n, X(i) - 6, y0 + 16); });
      ctx.fillText("majority-vote accuracy vs N", x0 + 4, y1 - 8); ctx.fillText("1.0", 14, y1 + 4); ctx.fillText("0", 30, y0 + 4);
      const accN = cu.find(([n]) => n === N)[1];
      el.querySelector(".ro").innerHTML = `single sample: <b>${(100 * pr[0]).toFixed(0)}%</b><br>vote of ${N}: <b>${(100 * accN).toFixed(0)}%</b><br>pass@${N} (perfect verifier): <b>${(100 * (1 - (1 - pr[0]) ** N)).toFixed(0)}%</b>`;
    }
    el.querySelectorAll("input").forEach((i) => i.addEventListener("input", () => draw()));
    el.querySelector("[data-act=go]").onclick = () => draw();
    const rs = () => { ({ ctx, w: W, h: H } = fitCanvas(cv, 1.25)); draw(); }; addEventListener("resize", rs); rs();
  }

  const REG = { hero, flow, gd, biasvar, sampling, chinchilla, kvcache, lora, majority };
  function boot() {
    document.querySelectorAll("[data-widget]").forEach((el) => {
      const f = REG[el.dataset.widget];
      if (!f || el.dataset.ready) return; el.dataset.ready = 1;
      // lazy-init when near viewport
      const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); try { f(el); } catch (err) { console.error("widget", el.dataset.widget, err); } } }, { rootMargin: "300px" });
      io.observe(el);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
