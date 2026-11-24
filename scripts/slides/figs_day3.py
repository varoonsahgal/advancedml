"""Slide figures for the Day 3 deck (Transformers & Beyond).

Run:  python scripts/slides/figs_day3.py
Writes docs/assets/img/slides/d3-*.png. Every figure is computed from real code:
the attention, RoPE, roofline, KV-cache, speculative-decoding, sampling, MoE-balancing
and SSM numbers below are the actual formulas/algorithms, run on small synthetic inputs.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from make_figures import HONEY, INK, CORAL, TEAL, INDIGO, PLUM, PAPER, CARD, NIGHT, honey_cmap, duo_cmap, plt, np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_rgb  # noqa: E402

OUT = HERE.parents[1] / "docs" / "assets" / "img" / "slides"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(3)

# slide-sized type: these figures are shown ~800-1600 px wide on a 1920 canvas
plt.rcParams.update({
    "font.size": 19, "axes.titlesize": 22, "axes.labelsize": 20, "xtick.labelsize": 17,
    "ytick.labelsize": 17, "legend.fontsize": 17, "axes.titlepad": 14, "axes.linewidth": 1.3,
})
MUTED = "#7A6E5A"
NIGHT_INK = "#F6EFD9"
heat = LinearSegmentedColormap.from_list("heat", [CARD, "#FFE680", HONEY, CORAL, INK])


def save(fig, name, dpi=160, night=False):
    fig.savefig(OUT / name, dpi=dpi, bbox_inches="tight", pad_inches=0.3,
                facecolor=NIGHT if night else CARD)
    plt.close(fig)
    print("wrote", OUT / name)


def save_art(fig, name, dpi=120):
    """Full-bleed night art: no bbox trimming so the aspect ratio is exact."""
    fig.savefig(OUT / name, dpi=dpi, facecolor=NIGHT)
    plt.close(fig)
    print("wrote", OUT / name)


def art_axes(w=8.66, h=10.0):          # 0.866 aspect = the section-divider hexagon
    fig = plt.figure(figsize=(w, h), facecolor=NIGHT)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=NIGHT)
    ax.set_axis_off()
    return fig, ax


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def rope(x, pos, base=10000.0):
    """Rotate consecutive pairs of x (..., d) by pos * theta_i, theta_i = base^(-2i/d)."""
    d = x.shape[-1]
    th = base ** (-np.arange(0, d, 2) / d)
    ang = np.asarray(pos)[..., None] * th
    c, s = np.cos(ang), np.sin(ang)
    x1, x2 = x[..., 0::2], x[..., 1::2]
    out = np.empty_like(x)
    out[..., 0::2] = x1 * c - x2 * s
    out[..., 1::2] = x1 * s + x2 * c
    return out


# ------------------------------------------------------------ 1. causal attention art
def art_causal():
    """Three real causal attention heads on a sequence with a repeated segment,
    blended additively (honey = RoPE-local head, teal = induction head, coral = sink head)."""
    T, d = 36, 64
    vocab = rng.normal(size=(50, d))
    seg = rng.integers(1, 50, 12)
    toks = np.r_[0, seg, rng.integers(1, 50, 5), seg, rng.integers(1, 50, 6)][:T]
    E = vocab[toks]
    pos = np.arange(T)
    mask = np.triu(np.ones((T, T), bool), 1)

    def head(logits):
        logits = np.where(mask, -np.inf, logits)
        return softmax(logits)
    # local head: q = k = same direction, RoPE makes the score decay with distance
    u = rng.normal(size=d)
    qk = rope(np.tile(u, (T, 1)), pos * 3.0)
    local = head(qk @ qk.T / np.sqrt(d) * 2.2)
    # induction head: query for token i matches the key of the token *after* an earlier copy of i
    prevE = np.r_[E[:1] * 0, E[:-1]]                       # key j carries token j-1 (previous-token head output)
    ind = head(E @ prevE.T / np.sqrt(d) * 3.0)
    # sink head: every query weakly matches token 0
    sinklog = np.full((T, T), 0.0); sinklog[:, 0] = 3.0
    sink = head(sinklog + rng.normal(0, 0.25, (T, T)))

    img = np.zeros((T, T, 3))
    for W, col, g in ((local, HONEY, 1.0), (ind, TEAL, 1.15), (sink, CORAL, 0.9)):
        img += (W[..., None] ** 0.55) * np.array(to_rgb(col)) * g
    img = np.clip(img, 0, 1)
    fig, ax = art_axes()
    night = np.array(to_rgb(NIGHT))
    for i in range(T):
        for j in range(T):
            if j > i:
                c = night + 0.025
            else:
                c = np.clip(night + img[i, j], 0, 1)
            ax.add_patch(plt.Rectangle((j + 0.07, T - 1 - i + 0.07), 0.86, 0.86, color=c, lw=0))
    pad = T * 0.19                     # keep the matrix inside the hexagon crop
    ax.set_xlim(-pad, T + pad); ax.set_ylim(T / 2 - (T + 2 * pad) * 1.155 / 2, T / 2 + (T + 2 * pad) * 1.155 / 2)
    ax.set_aspect("auto")
    save_art(fig, "d3-art-causal.png")


# ------------------------------------------------------------ 2. why divide by sqrt(d_k)
def sqrt_dk():
    ds = 2 ** np.arange(3, 12)
    n_keys, trials = 64, 400
    res = {"raw": [], "scaled": []}
    jac = {"raw": [], "scaled": []}
    for d in ds:
        q = rng.normal(size=(trials, 1, d)); K = rng.normal(size=(trials, n_keys, d))
        s = (q * K).sum(-1)
        for name, z in (("raw", s), ("scaled", s / np.sqrt(d))):
            p = softmax(z)
            res[name].append(p.max(-1).mean())
            # Frobenius norm of the softmax Jacobian diag(p) - p p^T
            J = np.einsum("ti,ij->tij", p, np.eye(n_keys)) - p[:, :, None] * p[:, None, :]
            jac[name].append(np.linalg.norm(J, axis=(1, 2)).mean())
    fig, axs = plt.subplots(2, 1, figsize=(8, 7.2), sharex=True)
    for ax, data, yl in ((axs[0], res, "max attention weight"), (axs[1], jac, "softmax gradient size")):
        ax.plot(ds, data["raw"], "o-", color=CORAL, lw=3.5, ms=9, label=r"$q\cdot k$  (unscaled)")
        ax.plot(ds, data["scaled"], "o-", color=TEAL, lw=3.5, ms=9, label=r"$q\cdot k/\sqrt{d_k}$")
        ax.set_ylabel(yl)
    axs[0].set_ylim(0, 1.05); axs[0].legend(loc="center right")
    axs[0].text(ds[-1], res["raw"][-1] - 0.1, "near one-hot", color=CORAL, ha="right", va="top", fontweight="bold")
    axs[1].set_ylim(0, None)
    axs[1].text(ds[-1], jac["raw"][-1] + 0.05, "gradient → 0", color=CORAL, ha="right", va="bottom", fontweight="bold")
    axs[1].set_xscale("log", base=2); axs[1].set_xlabel(r"head dimension $d_k$  (64 random keys)")
    fig.tight_layout(h_pad=1.2)
    save(fig, "d3-sqrt-dk.png")


# ------------------------------------------------------------ 3. RoPE art: every pair is a clock
def art_rope():
    d, M = 64, 400
    th = 10000 ** (-np.arange(0, d, 2) / d)
    fig, ax = art_axes()
    cm = LinearSegmentedColormap.from_list("r", [TEAL, HONEY, CORAL, PLUM])
    for i in range(0, 32):
        r = 1.0 + i * 0.42
        m = np.arange(M)
        a = m * th[i] + np.pi / 2
        # the trail of positions 0..M on ring i (ring radius only separates the pairs)
        col = cm(i / 31)
        ax.scatter(r * np.cos(a), r * np.sin(a), s=7 + 8 * (m / M), color=col,
                   alpha=np.clip(0.18 + 0.75 * (m / M), 0, 1), lw=0)
        ax.scatter([r * np.cos(a[-1])], [r * np.sin(a[-1])], s=60, color=col, edgecolors=NIGHT_INK, lw=1.2, zorder=5)
    R = 1.0 + 31 * 0.42 + 0.8
    ax.set_xlim(-R, R); ax.set_ylim(-R * 1.155, R * 1.155)
    save_art(fig, "d3-art-rope.png")


# ------------------------------------------------------------ 4. RoPE: scores are Toeplitz
def rope_toeplitz():
    d, T = 64, 96
    q = rng.normal(size=d)
    k = q + rng.normal(0, 0.5, d)
    pos = np.arange(T)
    Q = rope(np.tile(q, (T, 1)), pos)
    Kr = rope(np.tile(k, (T, 1)), pos)
    S = Q @ Kr.T
    fig = plt.figure(figsize=(8, 7.4))
    ax = fig.add_axes([0.13, 0.36, 0.74, 0.6])
    lim = np.abs(S).max()
    im = ax.imshow(S, cmap=heat, vmin=S.min(), vmax=S.max())
    ax.grid(False); ax.set_xlabel("key position $n$"); ax.set_ylabel("query position $m$")
    ax.set_title(r"$\langle R_m q,\ R_n k\rangle$: constant along every diagonal")
    for off in (-40, 0, 40):
        x = np.arange(max(0, off), min(T, T + off)); ax.plot(x, x - off, color=INK, lw=1.2, ls=":", alpha=0.6)
    ax2 = fig.add_axes([0.13, 0.07, 0.74, 0.19])
    offs = np.arange(-T + 1, T)
    prof = np.array([np.mean(np.diag(S, o)) for o in offs])
    ax2.plot(offs, prof, color=INDIGO, lw=2.6)
    ax2.set_xlabel("offset $n-m$"); ax2.set_ylabel("score"); ax2.set_xlim(offs[0], offs[-1])
    ax2.set_yticks([])
    save(fig, "d3-rope-toeplitz.png")


# ------------------------------------------------------------ 5. roofline: decode is memory-bound
def roofline():
    peak, bw = 989.0, 3.35           # H100-SXM-class: dense bf16 TFLOP/s, HBM TB/s
    I = np.logspace(-0.5, 4, 400)
    perf = np.minimum(peak, bw * I)
    ridge = peak / bw
    fig, ax = plt.subplots(figsize=(8, 6.6))
    ax.fill_between(I, 0.1, 2600, where=I <= ridge, color="#FFE3DF", alpha=0.7, lw=0)
    ax.fill_between(I, 0.1, 2600, where=I >= ridge, color="#DDF3EF", alpha=0.7, lw=0)
    ax.plot(I, perf, color=INK, lw=4)
    ax.text(0.45, 1500, "memory-bound", color="#A3302A", fontsize=21, fontweight="bold", va="center")
    ax.text(9000, 1500, "compute-bound", color="#0E5F59", fontsize=21, fontweight="bold", va="center", ha="right")
    # a bf16 weight matrix read once per step serves B tokens: ~2B FLOPs per 2 bytes -> intensity ~ B
    pts = [(1, "decode, batch 1", CORAL, (1.5, 2.4), "left"), (32, "decode, batch 32", HONEY, (45, 60), "left"),
           (4096, "prefill, 4k prompt", TEAL, (5500, 420), "right")]
    for x, lab, c, (tx, ty), ha in pts:
        y = min(peak, bw * x)
        ax.scatter([x], [y], s=260, color=c, edgecolors=INK, lw=2, zorder=5)
        ax.text(tx, ty, f"{lab}\n{100 * y / peak:.1f}% of peak" if y < peak else f"{lab}\n100% of peak",
                fontsize=18, color=INK, ha=ha, va="top")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(I[0], I[-1]); ax.set_ylim(0.5, 2600)
    ax.set_xlabel("arithmetic intensity (FLOPs per byte read)")
    ax.set_ylabel("attainable TFLOP/s")
    ax.set_title("Roofline, H100-class GPU (989 TFLOP/s, 3.35 TB/s)", fontsize=20)
    ax.grid(True, which="major")
    save(fig, "d3-roofline.png")


# ------------------------------------------------------------ 6. KV-cache memory
def kv_cache():
    L, Hq, dh, b = 32, 32, 128, 2
    ctx = np.logspace(np.log2(1024), np.log2(1 << 20), 200, base=2)
    cfg = [("MHA · 32 KV heads", 32, CORAL), ("GQA · 8 KV heads", 8, HONEY), ("MQA · 1 KV head", 1, TEAL)]
    fig, ax = plt.subplots(figsize=(8, 6.6))
    for name, hkv, c in cfg:
        bpt = 2 * L * hkv * dh * b
        ax.plot(ctx, ctx * bpt / 2 ** 30, lw=4.5, color=c, label=f"{name}: {bpt // 1024} KiB/token")
    ax.axhline(80, color=INK, ls=":", lw=2); ax.text(1100, 95, "one 80 GB GPU", color=INK, fontsize=18)
    x = 131072
    for hkv, c in ((32, CORAL), (8, HONEY), (1, TEAL)):
        y = x * 2 * L * hkv * dh * b / 2 ** 30
        ax.scatter([x], [y], s=150, color=c, edgecolors=INK, lw=1.8, zorder=5)
        ax.text(x * 1.25, y, f"{y:g} GiB", va="center", fontsize=18, fontweight="bold", color=INK)
    ax.axvline(x, color=MUTED, lw=1.2, ls="--"); ax.text(x / 1.15, 0.06, "128k", ha="right", color=MUTED, fontsize=17)
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xticks([2 ** 10, 2 ** 13, 2 ** 16, 2 ** 19 + 2 ** 19]); ax.set_xticklabels(["1k", "8k", "64k", "1M"])
    ax.set_ylim(0.04, 1500)
    ax.set_xlabel("context length (tokens)"); ax.set_ylabel("KV cache, one sequence (GiB)")
    ax.set_title("32 layers, 32 query heads × 128 dims, fp16", fontsize=20)
    ax.legend(loc="upper left", fontsize=17)
    save(fig, "d3-kv-cache.png")


# ------------------------------------------------------------ 7. speculative decoding is exact
def specdec():
    V = 8
    p = softmax(rng.normal(0, 1.1, V))                # target model
    q = softmax(np.log(p) + rng.normal(0, 0.9, V))     # a decent but imperfect draft
    N = 200_000
    x = rng.choice(V, N, p=q)
    acc = rng.random(N) < np.minimum(1, p[x] / q[x])
    resid = np.maximum(0, p - q); resid /= resid.sum()
    out = np.where(acc, x, rng.choice(V, N, p=resid))
    emp = np.bincount(out, minlength=V) / N
    alpha = np.minimum(p, q).sum()
    fig, axs = plt.subplots(2, 1, figsize=(8, 7.6), gridspec_kw=dict(height_ratios=[1.05, 1]))
    ax = axs[0]; w = 0.27; i = np.arange(V)
    ax.bar(i - w, q, w, color="#d9d0b6", edgecolor=INK, lw=0.8, label="draft  q")
    ax.bar(i, p, w, color=HONEY, edgecolor=INK, lw=0.8, label="target  p")
    ax.bar(i + w, emp, w, color=TEAL, edgecolor=INK, lw=0.8, label="speculative output")
    ax.set_xticks(i); ax.set_xticklabels([f"t{k}" for k in i]); ax.set_ylabel("probability")
    ax.set_title(f"200k samples: output matches p (max error {np.abs(emp - p).max():.3f})", fontsize=19)
    ax.set_ylim(0, 0.44)
    ax.legend(fontsize=15, loc="upper center", ncol=3, handlelength=1.2, columnspacing=1.0)
    ax = axs[1]
    a = np.linspace(0, 0.98, 200)
    for k, c in ((2, TEAL), (4, HONEY), (8, CORAL)):
        ax.plot(a, (1 - a ** (k + 1)) / (1 - a), lw=3.5, color=c, label=f"k = {k} drafted")
    ax.axvline(alpha, color=INK, ls=":", lw=1.8)
    ax.text(alpha + 0.015, 8.6, f"this draft:\nα = {alpha:.2f}", ha="left", va="top", fontsize=16, color=INK)
    ax.set_xlabel("acceptance rate α"); ax.set_ylabel("tokens per\ntarget pass")
    ax.set_ylim(1, 9); ax.set_xlim(0, 1); ax.legend(loc="upper left", fontsize=15)
    fig.tight_layout(h_pad=1.6)
    save(fig, "d3-specdec.png")


# ------------------------------------------------------------ 8. sampling art: temperature ridgeline
def art_sampling():
    """One Zipf-like next-token distribution, p ~ rank^(-0.9/T), at 16 temperatures (cold at the back).
    Tokens are laid out with the most likely in the middle so each ridge reads as a mountain."""
    V = 81
    logits = -0.9 * np.log(np.arange(1, V + 1))
    order = np.r_[np.arange(V - 1, 0, -2), np.arange(0, V, 2)]          # rank layout: ... 3 1 0 2 4 ...
    temps = np.geomspace(0.6, 3.0, 16)
    fig, ax = art_axes()
    cm = LinearSegmentedColormap.from_list("s", [CORAL, HONEY, TEAL, INDIGO, PLUM])
    xs = np.linspace(0.04, 0.96, V)
    scale = 3.0 / softmax(logits / temps[0]).max()
    for j, T in enumerate(temps):
        pr = softmax(logits / T)[order]
        y0 = (len(temps) - 1 - j) * 0.5
        col = cm(j / (len(temps) - 1))
        z = j + 1
        ax.fill_between(xs, y0 - 0.02, y0 + scale * pr, color=NIGHT, lw=0, zorder=z)
        ax.fill_between(xs, y0, y0 + scale * pr, color=col, alpha=0.16, lw=0, zorder=z)
        ax.plot(xs, y0 + scale * pr, color=col, lw=2.6, zorder=z, solid_joinstyle="round")
    ax.set_xlim(-0.08, 1.08); ax.set_ylim(-1.6, 15 * 0.5 + 4.6)
    save_art(fig, "d3-art-sampling.png")


# ------------------------------------------------------------ 9. sampling knobs on one distribution
def sampling():
    words = ["honey", "nectar", "pollen", "flowers", "the", "wax", "royal", "jelly", "sunshine", "math", "rust", "taxes"]
    logits = np.array([4.1, 3.5, 3.2, 2.9, 2.1, 1.9, 1.2, 1.0, 0.7, -0.2, -1.0, -1.6])
    p = softmax(logits)
    keep_p = np.r_[True, np.cumsum(p)[:-1] < 0.9]
    keep_min = p >= 0.1 * p.max()
    panels = [("T = 0.5", softmax(logits / 0.5), None), ("T = 1.0", p, None), ("T = 1.5", softmax(logits / 1.5), None),
              ("top-p = 0.9", p, keep_p), ("min-p = 0.1", p, keep_min)]
    fig, axs = plt.subplots(1, 5, figsize=(17, 6.2), sharey=True)
    y = np.arange(12)[::-1]
    for ax, (name, pr, keep) in zip(axs, panels):
        if keep is None:
            ax.barh(y, pr, color=HONEY, edgecolor=INK, lw=0.8, height=0.75)
            ax.set_title(name, color=INK)
        else:
            ax.barh(y, pr, color=np.where(keep, HONEY, "#e4dcc4"), edgecolor=INK, lw=0.8, height=0.75)
            r = np.where(keep, pr, 0); r /= r.sum()
            ax.barh(y, r, color="none", edgecolor=CORAL, lw=2.4, ls="--", height=0.75)
            ax.set_title(f"{name}\nkeeps {keep.sum()} tokens", color=INK)
        ax.set_xlim(0, 0.82); ax.set_xticks([0, 0.4, 0.8]); ax.grid(axis="y", visible=False)
    axs[0].set_yticks(y); axs[0].set_yticklabels(words, fontsize=19)
    axs[2].set_xlabel("probability")
    fig.tight_layout(w_pad=1.2)
    save(fig, "d3-sampling.png")


# ------------------------------------------------------------ 10. MoE load balancing (aux-loss-free bias)
def moe_load():
    """Top-2 routing over 8 experts with a skewed router. Left: no balancing. Right: the
    DeepSeek-V3-style bias update b_e += gamma * sign(mean_load - load_e), applied to selection only."""
    E, k, steps, B, gamma = 8, 2, 300, 1024, 0.01
    skew = np.array([1.2, 0.9, 0.5, 0.1, -0.2, -0.5, -0.8, -1.2])
    runs = {}
    for name, use_bias in (("no balancing", False), ("bias balancing", True)):
        b = np.zeros(E); hist = []
        r = np.random.default_rng(0)
        for _ in range(steps):
            s = r.normal(0, 1, (B, E)) + skew
            top = np.argsort(-(s + b), 1)[:, :k]
            load = np.bincount(top.ravel(), minlength=E) / (B * k)
            hist.append(load)
            if use_bias:
                b += gamma * np.sign(load.mean() - load)
        runs[name] = np.array(hist).T
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 6.6), sharey=True)
    for ax, (name, H) in zip(axs, runs.items()):
        im = ax.imshow(H, aspect="auto", cmap=heat, vmin=0, vmax=0.4, interpolation="nearest")
        ax.grid(False)
        last = H[:, -20:].mean(1)
        ax.set_title(f"{name}\nbusiest: {last.max() * E:.1f}× fair share", fontsize=19)
        ax.set_xlabel("training step")
    axs[0].set_yticks(range(E)); axs[0].set_ylabel("expert")
    cb = fig.colorbar(im, ax=axs, fraction=0.04, pad=0.03); cb.set_label("share of routed tokens")
    cb.ax.axhline(1 / E, color=INK, lw=2)
    save(fig, "d3-moe-load.png")


# ------------------------------------------------------------ 11. SSM "attention matrices"
def ssm_kernel():
    """Effective mixing matrix y = M x of a diagonal SSM: M[t,s] = sum_n C_n (prod_{r=s+1..t} Abar_r,n) Bbar_s,n.
    LTI: fixed Delta (Toeplitz, decaying). Selective: Delta_t = f(x_t), large on 'marker' tokens."""
    T, N = 40, 8
    A = -np.linspace(0.5, 4, N)
    Bv, Cv = np.ones(N), np.ones(N) / N
    markers = np.zeros(T, bool); markers[[0, 12, 23, 31]] = True

    def mix(delta):
        Abar = np.exp(delta[:, None] * A)            # (T, N) zero-order hold
        Bbar = delta[:, None] * Bv                    # Euler approximation used by Mamba for B
        logA = np.log(Abar)
        cum = np.cumsum(logA, 0)
        M = np.zeros((T, T))
        for t in range(T):
            for s in range(t + 1):
                M[t, s] = (Cv * np.exp(cum[t] - cum[s]) * Bbar[s]).sum()
        return M
    lti = mix(np.full(T, 0.25))
    sel = mix(np.where(markers, 2.5, 0.02))
    fig, axs = plt.subplots(1, 2, figsize=(12, 6.4))
    for ax, M, name in ((axs[0], lti, "LTI SSM (S4-style): fixed Δ"), (axs[1], sel, "selective SSM (Mamba): Δ = f(x)")):
        Mm = np.ma.masked_where(np.triu(np.ones((T, T), bool), 1), M / M.max(1, keepdims=True))
        ax.imshow(Mm ** 0.6, cmap=heat, vmin=0, vmax=1, interpolation="nearest")
        ax.set_facecolor("#F1EAD4"); ax.grid(False); ax.set_title(name, fontsize=20)
        ax.set_xlabel("input position s"); ax.set_xticks([0, 10, 20, 30]); ax.set_yticks([0, 10, 20, 30])
    axs[0].set_ylabel("output position t")
    for m in np.where(markers)[0]:
        axs[1].annotate("", (m, -0.7), (m, -3.6), arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=3), annotation_clip=False)
    axs[1].set_title("selective SSM (Mamba): Δ = f(x)", fontsize=20, pad=40)
    axs[0].set_title("LTI SSM (S4-style): fixed Δ", fontsize=20, pad=40)
    fig.tight_layout(w_pad=2.5)
    save(fig, "d3-ssm-kernel.png")


# ------------------------------------------------------------ 12. SSM art: S4D-Lin decaying kernels
def art_ssm():
    """Real parts of S4D-Lin modes K_n(t) = exp(dt * A_n * t), A_n = -1/2 + i*pi*n, as a ridgeline."""
    N = 16
    tau = np.linspace(0, 4.0, 1200)               # continuous time (Delta * step index)
    t = tau / tau[-1]
    fig, ax = art_axes()
    cm = LinearSegmentedColormap.from_list("k", [HONEY, CORAL, PLUM, INDIGO, TEAL])
    for n in range(N):
        An = -0.5 + 1j * np.pi * n
        K = np.exp(An * tau).real
        y0 = (N - 1 - n) * 0.62
        col = cm(n / (N - 1))
        ax.plot(t, y0 + 0.95 * K, color=col, lw=2.4, zorder=N - n)
    ax.set_xlim(-0.12, 1.08); ax.set_ylim(-1.6, (N - 1) * 0.62 + 2.4)
    save_art(fig, "d3-art-ssm.png")


if __name__ == "__main__":
    for f in (art_causal, sqrt_dk, art_rope, rope_toeplitz, roofline, kv_cache, specdec,
              art_sampling, sampling, moe_load, ssm_kernel, art_ssm):
        f()
