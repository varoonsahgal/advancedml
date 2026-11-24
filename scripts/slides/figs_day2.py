"""Figures for the Day 2 slide deck (The Deep Learning Engine Room).

Run:  python scripts/slides/figs_day2.py            # all figures
      python scripts/slides/figs_day2.py flow ns    # only some (names = function suffixes)
Writes docs/assets/img/slides/d2-*.png. Everything is computed from real code:
real forward/backward passes, real optimizer simulations, a real grokking run,
and the Chinchilla scaling law evaluated numerically.
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from make_figures import HONEY, INK, CORAL, TEAL, INDIGO, PLUM, PAPER, CARD, NIGHT, honey_cmap, duo_cmap, plt, np  # noqa: E402,F401
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

OUT = HERE.parents[1] / "docs" / "assets" / "img" / "slides"
OUT.mkdir(parents=True, exist_ok=True)

# Slide figures are shown ~0.75x of their pixel size, so everything is bigger than on the site.
plt.rcParams.update({
    "font.size": 15, "axes.titlesize": 17, "axes.labelsize": 15, "xtick.labelsize": 13.5,
    "ytick.labelsize": 13.5, "legend.fontsize": 13.5, "axes.titlepad": 12,
})
MUTED = "#7A6E5A"
glow_cmap = LinearSegmentedColormap.from_list("glow", ["#5a3f00", "#B98500", HONEY, "#FFE680", "#FFF8DC"])
HEX = (9.0, 10.4)   # section-divider art: aspect ≈ 0.866, the hexagon crop


def save(fig, name, dpi=160, night=False):
    kw = dict(facecolor=NIGHT) if night else dict(bbox_inches="tight", pad_inches=0.22)
    fig.savefig(OUT / name, dpi=dpi, **kw)
    plt.close(fig)
    print("wrote", name)


def night_axes(size):
    fig = plt.figure(figsize=size, facecolor=NIGHT)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=NIGHT)
    ax.set_axis_off()
    return fig, ax


# ---------------------------------------------------------------- 1. gradient-flow art
def landscape(x, y):
    """A smooth 2-D 'loss' with several basins (sum of Gaussian wells + a bowl)."""
    wells = [(-3.6, 1.3, 1.1, 1.0), (-0.6, -1.4, 0.9, 1.3), (2.4, 1.0, 1.2, 1.0), (4.6, -1.6, 0.8, 0.8),
             (0.9, 2.3, 0.6, 0.7), (-5.2, -1.9, 0.7, 0.9)]
    z = 0.035 * (x ** 2 + 2.2 * y ** 2)
    for cx, cy, s, d in wells:
        z -= d * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * s ** 2))
    return z


def fig_flow():
    nx, ny = 640, 360
    x = np.linspace(-6.4, 6.4, nx); y = np.linspace(-3.6, 3.6, ny)
    X, Y = np.meshgrid(x, y)
    Z = landscape(X, Y)
    gy, gx = np.gradient(Z, y, x)
    U, V = -gx, -gy                                   # the direction gradient descent moves
    speed = np.hypot(U, V)
    fig, ax = night_axes((16, 9))
    ax.imshow(Z, extent=(-6.4, 6.4, -3.6, 3.6), origin="lower", cmap=honey_cmap.reversed(), alpha=0.28,
              aspect="auto", interpolation="bicubic")
    ax.contour(X, Y, Z, levels=26, colors=["#F6EFD9"], linewidths=0.5, alpha=0.16)
    lw = 0.6 + 2.6 * (speed / speed.max()) ** 0.6
    ax.streamplot(x, y, U, V, density=2.6, color=np.log(speed + 1e-3), cmap=glow_cmap, linewidth=lw,
                  arrowsize=1.1, arrowstyle="-|>", minlength=0.25)
    # mark the minima the flow drains into
    from scipy.optimize import minimize
    for cx, cy in [(-3.6, 1.3), (-0.6, -1.4), (2.4, 1.0), (4.6, -1.6), (0.9, 2.3), (-5.2, -1.9)]:
        r = minimize(lambda p: landscape(p[0], p[1]), [cx, cy])
        ax.scatter(*r.x, s=260, marker="h", c=HONEY, edgecolors="#FFF8DC", linewidths=2, zorder=5)
    ax.set_xlim(-6.4, 6.4); ax.set_ylim(-3.6, 3.6)
    save(fig, "d2-flow.png", dpi=120, night=True)


# ---------------------------------------------------------------- 2. activation ridgeline art
def fig_hex_depth():
    rng = np.random.default_rng(3)
    width, depth, batch, gain = 1024, 22, 4000, 1.6
    h = rng.normal(0, 0.08, (batch, width))          # a deliberately narrow input
    hists = []
    bins = np.linspace(-1.02, 1.02, 161)
    for _ in range(depth):
        W = rng.normal(0, gain / np.sqrt(width), (width, width))
        h = np.tanh(h @ W)
        c, _ = np.histogram(h.ravel(), bins=bins, density=True)
        hists.append(c)
    mids = (bins[:-1] + bins[1:]) / 2
    fig, ax = night_axes(HEX)
    step = 0.62
    for i, c in enumerate(hists):
        c = np.minimum(c / np.percentile(c, 99.5), 1.0) * 1.7
        base = (depth - 1 - i) * step
        col = glow_cmap(0.12 + 0.88 * i / (depth - 1))
        z = 10 + i
        ax.fill_between(mids, base, base + c, color=NIGHT, zorder=z, lw=0)
        ax.fill_between(mids, base, base + c, color=col, alpha=0.22, zorder=z, lw=0)
        ax.plot(mids, base + c, color=col, lw=2.4, zorder=z)
        ax.plot(mids, base + c, color=col, lw=7, alpha=0.12, zorder=z)
    ax.set_xlim(-1.3, 1.3); ax.set_ylim(-0.8, (depth - 1) * step + 2.6)
    save(fig, "d2-hex-depth.png", dpi=110, night=True)


# ---------------------------------------------------------------- 3. Newton–Schulz art
NS_ABC = (3.4445, -4.7750, 2.0315)


def ns_poly(s):
    a, b, c = NS_ABC
    return a * s + b * s ** 3 + c * s ** 5


def fig_hex_ns():
    s0 = np.geomspace(1e-6, 1.0, 3000)
    fig, ax = night_axes(HEX)
    K = 7
    cur = s0.copy()
    for k in range(K + 1):
        col = glow_cmap(0.15 + 0.85 * k / K)
        off = (K - k) * 0.42                        # stack the iterates like a ridgeline
        ax.plot(np.log10(s0), cur + off, color=col, lw=8, alpha=0.07)
        ax.plot(np.log10(s0), cur + off, color=col, lw=2.0, alpha=0.95)
        cur = ns_poly(cur)
    ax.set_xlim(-6.15, 0.1); ax.set_ylim(-0.35, K * 0.42 + 1.6)
    save(fig, "d2-hex-ns.png", dpi=110, night=True)


# ---------------------------------------------------------------- 4. LR-schedule art
def fig_hex_lr():
    """Cosine needs a fresh curve for every budget; WSD is one trunk with cheap cooldown branches."""
    fig, ax = night_axes(HEX)
    warm = 40
    for i, Tk in enumerate(np.linspace(260, 1000, 9)):
        t = np.arange(0, int(Tk) + 1)
        lr = np.where(t < warm, t / warm, 0.5 * (1 + np.cos(np.pi * (t - warm) / (Tk - warm))))
        col = glow_cmap(0.15 + 0.35 * i / 8)
        ax.plot(t, lr, color=col, lw=7, alpha=0.08); ax.plot(t, lr, color=col, lw=1.8, alpha=0.85)
    t = np.arange(0, 1001)
    trunk = np.where(t < warm, t / warm, 1.0)
    ax.plot(t, trunk + 0.06, color="#FFF8DC", lw=10, alpha=0.08); ax.plot(t, trunk + 0.06, color="#FFF8DC", lw=3)
    for i, tb in enumerate(np.linspace(260, 1000, 9)):
        cd = 0.2 * tb
        tt = np.linspace(tb - cd, tb, 100)
        col = glow_cmap(0.65 + 0.35 * i / 8)
        y = 1.0 - (tt - (tb - cd)) / cd
        ax.plot(tt, y + 0.06, color=col, lw=8, alpha=0.1); ax.plot(tt, y + 0.06, color=col, lw=2.4)
        ax.scatter([tb], [0.06], s=60, marker="h", color=HONEY, edgecolors="#FFF8DC", lw=1, zorder=5)
    ax.set_xlim(-30, 1030); ax.set_ylim(-0.32, 1.42)
    save(fig, "d2-hex-lr.png", dpi=110, night=True)


# ---------------------------------------------------------------- grokking (shared by 2 figures)
_GROK = {}


def grok_runs():
    if _GROK:
        return _GROK
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(4)
    P, FRAC = 97, 0.3

    class ModAddNet(nn.Module):        # identical to Lab 2.3
        def __init__(self, p, d=64, hidden=256):
            super().__init__()
            self.E = nn.Embedding(p, d)
            self.W = nn.Linear(2 * d, hidden, bias=False)
            self.U = nn.Linear(hidden, p, bias=False)

        def forward(self, a, b):
            return self.U(self.W(torch.cat([self.E(a), self.E(b)], -1)) ** 2)

    g = torch.Generator().manual_seed(0)
    a, b = torch.meshgrid(torch.arange(P), torch.arange(P), indexing="ij")
    a, b = a.flatten(), b.flatten()
    y = (a + b) % P
    perm = torch.randperm(P * P, generator=g)
    tr, te = perm[:int(FRAC * P * P)], perm[int(FRAC * P * P):]
    for wd in (1.0, 0.0):
        torch.manual_seed(0)
        m = ModAddNet(P)
        opt = torch.optim.AdamW(m.parameters(), lr=3e-3, weight_decay=wd, betas=(0.9, 0.98))
        log = {k: [] for k in ("step", "train", "test", "wnorm")}
        t0 = time.time()
        for step in range(5001):
            logits = m(a[tr], b[tr])
            loss = F.cross_entropy(logits, y[tr])
            if step % 10 == 0:
                with torch.no_grad():
                    log["step"].append(step)
                    log["train"].append((logits.argmax(-1) == y[tr]).float().mean().item())
                    log["test"].append((m(a[te], b[te]).argmax(-1) == y[te]).float().mean().item())
                    log["wnorm"].append(sum((p ** 2).sum() for p in m.parameters()).sqrt().item())
            opt.zero_grad(); loss.backward(); opt.step()
        print(f"  grok run wd={wd}: final test acc {log['test'][-1]:.3f} [{time.time() - t0:.0f}s]")
        _GROK[wd] = ({k: np.array(v) for k, v in log.items()}, m.E.weight.detach().numpy().copy())
    _GROK["P"] = P
    return _GROK


def fourier_power(E):
    Fk = np.fft.rfft(E, axis=0)
    pw = (np.abs(Fk) ** 2).sum(1)[1:]
    return pw / pw.sum()


def fig_hex_grok():
    """The grokked embedding is (almost) a sum of a few Fourier modes over the token index a.
    Each ring is the frequency-k component of the learned embedding, projected onto its own 2-D plane,
    for the 4 frequencies the network chose; joining tokens a -> a+1 draws the star polygon {97/k}."""
    R = grok_runs(); P = R["P"]
    E = R[1.0][1]
    E = E - E.mean(0)
    pw = fourier_power(E)
    top = np.argsort(pw)[::-1][:4] + 1
    fig, ax = night_axes(HEX)
    cols = [HONEY, CORAL, TEAL, PLUM]
    radii = [1.0, 0.76, 0.53, 0.31]
    a = np.arange(P)
    for k, col, rad in zip(top, cols, radii):
        Fk = (np.exp(-2j * np.pi * k * a / P)[:, None] * E).sum(0)            # complex d-vector
        Ek = (2 / P) * np.real(Fk[None, :] * np.exp(2j * np.pi * k * a / P)[:, None])   # frequency-k part of E
        _, _, Vt = np.linalg.svd(Ek, full_matrices=False)
        xy = Ek @ Vt[:2].T                                                       # its own 2-D plane
        xy = xy / np.sqrt((xy ** 2).sum(1)).mean() * rad
        order = np.r_[a, 0]
        ax.plot(xy[order, 0], xy[order, 1], color=col, lw=6, alpha=0.08)
        ax.plot(xy[order, 0], xy[order, 1], color=col, lw=1.1, alpha=0.75)
        ax.scatter(xy[:, 0], xy[:, 1], s=30, c=col, edgecolors="#FFF8DC", linewidths=0.6, zorder=4)
    print("  top grokking frequencies:", top.tolist(), "power share", np.round(np.sort(pw)[::-1][:4], 3).tolist())
    ax.set_aspect("equal")
    ax.set_xlim(-1.12, 1.12); ax.set_ylim(-1.12 * HEX[1] / HEX[0], 1.12 * HEX[1] / HEX[0])
    save(fig, "d2-hex-grok.png", dpi=110, night=True)


def fig_grok():
    R = grok_runs()
    lg, E1 = R[1.0]; lg0, E0 = R[0.0]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.4, 7.2), gridspec_kw=dict(height_ratios=[1.35, 1]))
    s = np.maximum(lg["step"], 1)
    a1.plot(s, 100 * lg["train"], color=HONEY, lw=3.5, label="train")
    a1.plot(s, 100 * lg["test"], color=TEAL, lw=3.5, label="test")
    a1.plot(np.maximum(lg0["step"], 1), 100 * lg0["test"], color=MUTED, lw=2, ls="--", label="test, no weight decay")
    mem = s[np.argmax(lg["train"] >= 0.99)]; grok = s[np.argmax(lg["test"] >= 0.95)]
    a1.axvspan(mem, grok, color=CORAL, alpha=0.1)
    a1.text(np.sqrt(mem * grok), 52, f"memorized\nbut not understood\n({grok / mem:.0f}× longer)", ha="center",
            va="center", color=CORAL, fontsize=14, weight="bold")
    a1.set_xscale("log"); a1.set_ylabel("accuracy %"); a1.set_xlabel("full-batch AdamW steps (log)")
    a1.set_title("(a + b) mod 97, trained on 30% of the table")
    a1.legend(loc="upper left")
    ks = np.arange(1, len(fourier_power(E1)) + 1)
    a2.bar(ks, fourier_power(E0 - E0.mean(0)), color="#cfc4a8", width=0.9, label="no weight decay")
    a2.bar(ks, fourier_power(E1 - E1.mean(0)), color=HONEY, edgecolor=INK, lw=0.4, width=0.9, label="weight decay 1.0 (grokked)")
    a2.set_xlabel("frequency k of the token embedding"); a2.set_ylabel("share of power")
    a2.set_title("the grokked embedding uses a handful of Fourier frequencies")
    a2.legend(loc="upper left"); a2.set_xlim(0, ks[-1] + 1)
    fig.tight_layout(h_pad=1.6)
    save(fig, "d2-grok.png")


# ---------------------------------------------------------------- 5. isoFLOP art + content figure
# Chinchilla parametric law with the Besiroglu et al. (2024, Epoch AI) refit of Hoffmann et al.'s data,
# which, unlike the originally published coefficients, reproduces the ~20 tokens/parameter optimum.
CH = dict(E=1.82, A=482.01, B=2085.43, alpha=0.3478, beta=0.3658)


def chin_loss(N, D):
    return CH["E"] + CH["A"] / N ** CH["alpha"] + CH["B"] / D ** CH["beta"]


def chin_opt(C):
    a, b = CH["alpha"], CH["beta"]
    G = (a * CH["A"] / (b * CH["B"])) ** (1 / (a + b))
    N = G * (C / 6) ** (b / (a + b))
    return N, C / 6 / N


def fig_hex_isoflop():
    fig, ax = night_axes(HEX)
    Cs = np.geomspace(1e18, 1e25, 22)
    opt = []
    for i, C in enumerate(Cs):
        N = np.geomspace(3e6, 3e12, 600)
        D = C / 6 / N
        ok = (D > 1e8) & (D < 1e14)
        L = chin_loss(N[ok], D[ok])
        col = glow_cmap(i / (len(Cs) - 1))
        ax.plot(np.log10(N[ok]), L, color=col, lw=7, alpha=0.08)
        ax.plot(np.log10(N[ok]), L, color=col, lw=1.8, alpha=0.95)
        n, d = chin_opt(C)
        opt.append((np.log10(n), chin_loss(n, d)))
    opt = np.array(opt)
    ax.plot(opt[:, 0], opt[:, 1], color="#FFF8DC", lw=2.5, alpha=0.9, zorder=4)
    ax.scatter(opt[:, 0], opt[:, 1], s=120, marker="h", c=HONEY, edgecolors="#FFF8DC", linewidths=1.5, zorder=5)
    ax.set_xlim(6.6, 12.2); ax.set_ylim(1.8, 4.6)
    save(fig, "d2-hex-isoflop.png", dpi=110, night=True)


def fig_isoflop():
    fig, ax = plt.subplots(figsize=(8.4, 6.8))
    Cs = [1e19, 1e20, 1e21, 1e22, 1e23, 1e24]
    cols = [PLUM, INDIGO, TEAL, "#7fb800", HONEY, CORAL]
    opt = []
    for C, col in zip(Cs, cols):
        N = np.geomspace(1e7, 3e12, 500); D = C / 6 / N
        ok = (D > 3e8) & (D < 3e14)
        L = chin_loss(N[ok], D[ok])
        ax.plot(N[ok], L, color=col, lw=3)
        n, d = chin_opt(C); opt.append((n, chin_loss(n, d), d))
        ax.scatter([n], [chin_loss(n, d)], s=110, color=col, edgecolors=INK, zorder=5)
        vis = (L <= 3.6) & (N[ok] <= 3e12)
        xe, ye = N[ok][vis][-1], L[vis][-1]
        ax.text(xe * (1.12 if ye < 3.5 else 1.08), min(ye, 3.5), f"10$^{{{int(np.log10(C))}}}$", color=col,
                fontsize=15, weight="bold", va="center", clip_on=False)
    o = np.array(opt)
    ax.plot(o[:, 0], o[:, 1], color=INK, lw=1.8, ls="--", zorder=4)
    n70, d70 = chin_opt(5.76e23)
    ax.annotate(f"Chinchilla's budget, 5.8×10²³ FLOPs → N* ≈ {n70 / 1e9:.0f}B params,\nD* ≈ {d70 / 1e12:.1f}T tokens: ≈ {d70 / n70:.0f} tokens per parameter",
                xy=(n70, chin_loss(n70, d70)), xytext=(1.15e7, 1.72), fontsize=14, color=INK,
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5))
    ax.set_xscale("log"); ax.set_ylim(1.62, 3.6); ax.set_xlim(1e7, 3e12)
    ax.set_xlabel("parameters N  (tokens D = C / 6N;  labels = C in FLOPs)"); ax.set_ylabel("predicted loss")
    ax.set_title("isoFLOP curves: each compute budget C has a sweet spot")
    save(fig, "d2-isoflop.png")


# ---------------------------------------------------------------- 6. signal through depth
def fig_depth():
    import torch
    import torch.nn as nn
    rng = np.random.default_rng(0)
    width, depth = 512, 50
    x0 = rng.normal(0, 1, (256, width))
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.4, 7.6))
    setups = [("std = 1 (naive)", np.sqrt(width), CORAL), ("std = 0.01", 0.01 * np.sqrt(width), PLUM),
              ("Xavier: Var = 1/fan_in", 1.0, INDIGO), ("He: Var = 2/fan_in", np.sqrt(2), TEAL)]
    for name, g, col in setups:
        h, stds = x0.copy(), []
        for _ in range(depth):
            W = rng.normal(0, g / np.sqrt(width), (width, width))
            h = np.maximum(h @ W, 0)
            stds.append(h.std())
        a1.plot(np.arange(1, depth + 1), stds, lw=3.2, color=col, label=name)
    a1.set_yscale("log"); a1.set_ylim(1e-40, 1e70)
    a1.set_yticks([1e-40, 1e-20, 1, 1e20, 1e40, 1e60])
    a1.set_xlabel("layer"); a1.set_ylabel("activation std")
    a1.set_title("forward: 50 ReLU layers, width 512")
    a1.legend(loc="upper left", fontsize=12.5, ncol=2)

    torch.manual_seed(0)
    W_, L_ = 256, 48
    X = torch.randn(512, W_); Y = torch.randn(512, 1)

    def grads(residual):
        torch.manual_seed(1)
        lins = nn.ModuleList([nn.Linear(W_, W_) for _ in range(L_)])   # PyTorch default init
        norms = nn.ModuleList([nn.LayerNorm(W_) for _ in range(L_)])
        head = nn.Linear(W_, 1)
        h = X
        for lin, ln in zip(lins, norms):
            h = h + lin(torch.tanh(ln(h))) if residual else torch.tanh(lin(h))
        loss = ((head(h) - Y) ** 2).mean()
        loss.backward()
        return [lin.weight.grad.norm().item() for lin in lins]
    gp, gr = grads(False), grads(True)
    ls = np.arange(1, L_ + 1)
    a2.plot(ls, gp, lw=3.2, color=CORAL, label="plain: h = tanh(W h)")
    a2.plot(ls, gr, lw=3.2, color=TEAL, label="pre-norm residual: h = h + W tanh(LN(h))")
    a2.set_yscale("log"); a2.set_xlabel("layer (1 = nearest the input)"); a2.set_ylabel("‖∂L/∂W‖")
    a2.set_title("backward: gradient reaching each of 48 layers")
    a2.legend(loc="lower right", fontsize=12.5)
    print(f"  plain grad ratio first/last {gp[0] / gp[-1]:.2e}; residual {gr[0] / gr[-1]:.2f}")
    fig.tight_layout(h_pad=1.8)
    save(fig, "d2-depth.png")


# ---------------------------------------------------------------- 7. Adam + L2 vs AdamW
def fig_adamw():
    rng = np.random.default_rng(0)
    lr, lam, b1, b2, eps, T, n = 1e-3, 0.1, 0.9, 0.999, 1e-8, 20000, 300
    sigmas = [0.01, 0.1, 1.0, 10.0]
    cols = [TEAL, INDIGO, PLUM, CORAL]
    fig, axs = plt.subplots(2, 1, figsize=(8.4, 7.4), sharex=True)
    for ax, decoupled in zip(axs, (False, True)):
        for sig, col in zip(sigmas, cols):
            th = np.ones(n); m = np.zeros(n); v = np.zeros(n); hist = []
            for t in range(1, T + 1):
                g = sig * rng.normal(size=n)          # gradient = pure noise of scale σ (no signal)
                if not decoupled:
                    g = g + lam * th                   # L2 penalty folded into the gradient
                m = b1 * m + (1 - b1) * g; v = b2 * v + (1 - b2) * g * g
                upd = (m / (1 - b1 ** t)) / (np.sqrt(v / (1 - b2 ** t)) + eps)
                th = th - lr * (upd + (lam * th if decoupled else 0))
                if t % 50 == 0:
                    hist.append(np.abs(th).mean())
            ax.plot(np.arange(50, T + 1, 50), hist, lw=3.2, color=col, label=f"gradient scale σ = {sig:g}")
        ax.set_ylim(0, 1.08); ax.set_ylabel("mean |θ|")
    axs[0].set_title("Adam + L2: decay depends on the gradient scale")
    axs[1].set_title("AdamW: every weight decays at the same rate")
    axs[1].plot(np.arange(T), np.exp(-lr * lam * np.arange(T)), color=INK, lw=1.4, ls=":", label="e$^{-ηλt}$")
    axs[0].legend(loc="center right", fontsize=12.5)
    axs[1].legend(loc="upper right", fontsize=12.5)
    axs[1].set_xlabel("step  (η = 1e-3, λ = 0.1, gradients are pure noise)")
    fig.tight_layout(h_pad=1.4)
    save(fig, "d2-adamw-l2.png")


# ---------------------------------------------------------------- 8. Newton–Schulz on a real gradient
def newton_schulz5(G, steps=5, eps=1e-7):
    a, b, c = NS_ABC
    X = G / (np.linalg.norm(G) + eps)
    tall = X.shape[0] > X.shape[1]
    if tall:
        X = X.T
    for _ in range(steps):
        A = X @ X.T
        X = a * X + (b * A + c * A @ A) @ X
    return X.T if tall else X


def fig_ns():
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from sklearn.datasets import load_digits
    Xd, yd = load_digits(return_X_y=True)
    X = torch.tensor(Xd / 16.0, dtype=torch.float32); y = torch.tensor(yd)
    torch.manual_seed(0)
    net = nn.Sequential(nn.Linear(64, 256), nn.Tanh(), nn.Linear(256, 256), nn.Tanh(), nn.Linear(256, 10))
    buf = torch.zeros(256, 256)
    g = torch.Generator().manual_seed(0)
    for _ in range(60):                               # plain SGD steps; keep Muon's momentum buffer for layer 2
        idx = torch.randint(0, len(X), (128,), generator=g)
        net.zero_grad(); F.cross_entropy(net(X[idx]), y[idx]).backward()
        buf = 0.95 * buf + net[2].weight.grad
        with torch.no_grad():
            for p in net.parameters():
                p -= 0.1 * p.grad
    G = buf.numpy().astype(np.float64)                 # the 256×256 hidden-layer momentum
    s_before = np.linalg.svd(G / np.linalg.norm(G), compute_uv=False)
    s_after = np.linalg.svd(newton_schulz5(G), compute_uv=False)

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.4, 7.6), gridspec_kw=dict(height_ratios=[1, 1.05]))
    s = np.geomspace(1e-4, 1.0, 800)
    a1.axhspan(0.68, 1.2, color=TEAL, alpha=0.1)
    a1.plot(s, np.ones_like(s), color=INK, lw=1.6, ls=":", label="ideal UVᵀ: every σ → 1")
    cur = s.copy()
    shades = {1: "#FFD84D", 3: HONEY, 5: "#B98500"}
    for k in range(1, 6):
        cur = ns_poly(cur)
        if k in shades:
            a1.plot(s, cur, color=shades[k], lw=2.4 + 0.5 * k, label=f"{k} step{'s' if k > 1 else ''}")
    a1.set_xscale("log")
    a1.set_xlabel("input singular value σ (after dividing by ‖G‖)"); a1.set_ylabel("output σ")
    a1.set_title("3.4445σ − 4.7750σ³ + 2.0315σ⁵, iterated")
    a1.legend(loc="upper left", fontsize=12.5, ncol=2); a1.set_ylim(0, 1.95)
    r = np.arange(1, len(s_before) + 1)
    a2.semilogy(r, s_before, color=CORAL, lw=3.2, label="momentum M (divided by ‖M‖)")
    a2.semilogy(r, s_after, color=TEAL, lw=3.2, label="newton_schulz5(M)")
    a2.set_xlabel("singular value rank"); a2.set_ylabel("σ")
    a2.set_title("a real 256×256 momentum matrix (MLP on digits)")
    a2.legend(loc="lower left")
    fig.tight_layout(h_pad=1.8)
    print(f"  NS output σ range [{s_after.min():.3f}, {s_after.max():.3f}]; G cond {s_before[0] / s_before[-1]:.1e}")
    save(fig, "d2-ns-spectrum.png")


# ---------------------------------------------------------------- 9. WSD vs cosine (real training)
def fig_wsd():
    import torch
    import torch.nn as nn
    torch.manual_seed(0)
    d_in, n_tr, T, warm, peak = 16, 50000, 4000, 200, 3e-3
    teacher = nn.Sequential(nn.Linear(d_in, 256), nn.Tanh(), nn.Linear(256, 256), nn.Tanh(), nn.Linear(256, 1)).requires_grad_(False)
    with torch.no_grad():
        for mod in teacher:
            if isinstance(mod, nn.Linear):
                nn.init.normal_(mod.weight, std=1.5 / mod.in_features ** 0.5)
    Xtr = torch.randn(n_tr, d_in); ytr = teacher(Xtr) + 0.1 * torch.randn(n_tr, 1)
    Xte = torch.randn(8000, d_in); yte = teacher(Xte)          # error against the true function

    def cosine(t):
        return peak * t / warm if t < warm else peak * 0.5 * (1 + np.cos(np.pi * (t - warm) / (T - warm)))

    def wsd(t, start=int(0.8 * T), end=T):
        if t < warm:
            return peak * t / warm
        if t < start:
            return peak
        return peak * max(0.0, 1 - (t - start) / (end - start))

    def run(sched, steps, init=None):
        torch.manual_seed(1)
        net = nn.Sequential(nn.Linear(d_in, 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, 1))
        opt = torch.optim.Adam(net.parameters(), lr=peak)
        g = torch.Generator().manual_seed(2)
        t0 = 0
        if init is not None:
            net.load_state_dict(init[0]); opt.load_state_dict(init[1]); t0 = init[2]; g.set_state(init[3])
        xs, ls, ckpts = [], [], {}
        for t in range(t0, steps):
            for pg in opt.param_groups:
                pg["lr"] = sched(t)
            idx = torch.randint(0, n_tr, (32,), generator=g)
            loss = ((net(Xtr[idx]) - ytr[idx]) ** 2).mean()
            opt.zero_grad(); loss.backward(); opt.step()
            if t % 20 == 0 or t == steps - 1:
                with torch.no_grad():
                    xs.append(t + 1); ls.append(((net(Xte) - yte) ** 2).mean().item())
            if t + 1 in (1600, 2600):
                import copy
                ckpts[t + 1] = (copy.deepcopy(net.state_dict()), copy.deepcopy(opt.state_dict()), t + 1, g.get_state())
        return np.array(xs), np.array(ls), ckpts

    xc, lc, _ = run(cosine, T)
    xw, lw_, ck = run(wsd, T)
    branches = []
    for b in (1600, 2600):
        cd = 400
        xb, lb, _ = run(lambda t, b=b: wsd(t, start=b, end=b + cd), b + cd, init=ck[b])
        branches.append((b, xb, lb))

    def smooth(v, k=5):
        return np.convolve(np.pad(v, (k // 2, k // 2), mode="edge"), np.ones(k) / k, mode="valid")
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.2, 7.2), sharex=True, gridspec_kw=dict(height_ratios=[1, 2.3]))
    ts = np.arange(T)
    a1.plot(ts, [cosine(t) * 1e3 for t in ts], color=HONEY, lw=3.2, label="warmup + cosine")
    a1.plot(ts, [wsd(t) * 1e3 for t in ts], color=TEAL, lw=3.2, label="WSD")
    for b, xb, _ in branches:
        tb = np.arange(b, b + 400)
        a1.plot(tb, [wsd(t, b, b + 400) * 1e3 for t in tb], color=TEAL, lw=2, ls="--")
    a1.set_ylabel("LR (×10⁻³)"); a1.set_ylim(0, 3.5)
    a1.legend(loc="lower left", ncol=2, fontsize=12.5)
    a2.plot(xc, smooth(lc), color=HONEY, lw=3, label="warmup + cosine")
    a2.plot(xw, smooth(lw_), color=TEAL, lw=3, label="WSD")
    for i, (b, xb, lb) in enumerate(branches):
        a2.plot(xb, smooth(lb), color=TEAL, lw=2.4, ls="--", label="WSD cooldown branched off a checkpoint" if i == 0 else None)
        a2.scatter([xb[-1]], [smooth(lb)[-1]], s=70, color=TEAL, edgecolors=INK, zorder=5)
    a2.scatter([xw[-1]], [smooth(lw_)[-1]], s=90, color=TEAL, edgecolors=INK, zorder=5)
    a2.scatter([xc[-1]], [smooth(lc)[-1]], s=90, color=HONEY, edgecolors=INK, zorder=5)
    lo = min(lc.min(), lw_.min()); a2.set_ylim(lo - 0.006, lo + 0.075)
    a2.set_xlabel("training step (Adam, batch 32, teacher–student regression)"); a2.set_ylabel("test MSE")
    a2.legend(loc="upper right", fontsize=12.5)
    a1.set_title("same model, same data, two schedules")
    fig.tight_layout(h_pad=0.8)
    print(f"  final: cosine {lc[-1]:.4f}  wsd {lw_[-1]:.4f}  branches {[round(b[2][-1], 4) for b in branches]}")
    save(fig, "d2-wsd.png")


FIGS = {"flow": fig_flow, "depthart": fig_hex_depth, "nsart": fig_hex_ns, "grokart": fig_hex_grok,
        "isoart": fig_hex_isoflop, "lrart": fig_hex_lr, "depth": fig_depth, "adamw": fig_adamw, "ns": fig_ns, "wsd": fig_wsd,
        "grok": fig_grok, "isoflop": fig_isoflop}

if __name__ == "__main__":
    only = sys.argv[1:] or list(FIGS)
    for k in only:
        FIGS[k]()
