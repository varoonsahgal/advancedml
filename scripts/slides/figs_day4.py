"""Figures for the Day 4 slide deck (Generative Worlds).

Run:  python3 scripts/slides/figs_day4.py [name ...]
Writes docs/assets/img/slides/d4-*.png. Everything is computed from real code:
exact flow-matching fields on empirical 2-D data, closed-form class-conditional
Gaussian-mixture flows for CFG, a small MLP trained by reflow, a 2-D VAE trained on
sklearn's 8x8 digits, and a toy two-tower model trained with the CLIP loss.
Convention throughout: t = 0 is noise, t = 1 is data (except the DDPM schedule
plot, which uses DDPM's own step index: 0 = data, T = noise, and says so).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from make_figures import (HONEY, INK, CORAL, TEAL, INDIGO, PLUM, PAPER, CARD, NIGHT,  # noqa: E402
                          honey_cmap, duo_cmap, plt, np, shape_points, fm_velocity, fm_trajectories)
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle  # noqa: E402

ROOT = HERE.parents[1]
SLIDES = ROOT / "docs" / "assets" / "img" / "slides"
SLIDES.mkdir(parents=True, exist_ok=True)
CREAM = "#F6EFD9"
MUTED = "#CDBF9C"
TIME_CM = LinearSegmentedColormap.from_list("time", [INDIGO, PLUM, CORAL, HONEY, "#FFF8DC"])

# bigger type: these figures are read from the back of a room
plt.rcParams.update({"font.size": 17, "axes.titlesize": 21, "axes.labelsize": 19,
                     "xtick.labelsize": 15, "ytick.labelsize": 15, "legend.fontsize": 16})


def save(fig, name, dpi=150, night=False, tight=True):
    kw = dict(dpi=dpi, facecolor=NIGHT if night else CARD)
    if tight:
        kw.update(bbox_inches="tight", pad_inches=0.2)
    fig.savefig(SLIDES / name, **kw)
    plt.close(fig)
    print("wrote", name)


def night_axes(w, h):
    fig = plt.figure(figsize=(w, h), facecolor=NIGHT)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=NIGHT)
    ax.set_axis_off()
    return fig, ax


def hexflower(n, rng, r=0.72, jitter=0.03):
    """Points on the edges of 7 pointy-top hexagons: a little honeycomb."""
    centers = [(0.0, 0.0)] + [(np.sqrt(3) * r * np.cos(a), np.sqrt(3) * r * np.sin(a))
                              for a in np.deg2rad(np.arange(0, 360, 60))]
    ang = np.deg2rad(90 + 60 * np.arange(7))
    verts = np.c_[r * np.cos(ang), r * np.sin(ang)]
    c = np.array(centers)[rng.integers(0, 7, n)]
    e = rng.integers(0, 6, n)
    u = rng.uniform(0, 1, (n, 1))
    p = c + verts[e] * (1 - u) + verts[e + 1] * u
    return p + rng.normal(0, jitter, p.shape)


def euler_exact(x, data, steps, t_end=1.0, keep=False):
    ts = np.linspace(0, t_end, steps + 1)
    tr = [x.copy()]
    for a, b in zip(ts[:-1], ts[1:]):
        x = x + (b - a) * fm_velocity(x, a, data)
        if keep:
            tr.append(x.copy())
    return np.array(tr) if keep else x


# ============================================================ hook: film strip (16x9, night)
def filmstrip():
    rng = np.random.default_rng(11)
    data = hexflower(700, rng)
    tr = fm_trajectories(data, 1500, steps=100, rng_=np.random.default_rng(4))   # t: 0 -> 0.995
    T = tr.shape[0]
    tgrid = np.linspace(0, 1, T)
    frames = (0.0, 0.5, 0.8, 0.9, 1.0)          # most of the structure appears late, so sample late
    gap = 6.4
    fig, ax = night_axes(16, 9)
    off = lambda t: np.interp(t, frames, gap * np.arange(len(frames)))
    segs, cols = [], []
    for i in range(0, tr.shape[1], 5):
        p = tr[:, i, :].copy(); p[:, 0] += off(tgrid)
        for k in range(0, T - 1):
            segs.append([p[k], p[k + 1]]); cols.append(tgrid[k])
    ax.add_collection(LineCollection(segs, colors=TIME_CM(np.array(cols)), linewidths=0.7, alpha=0.3))
    for k, t in enumerate(frames):
        idx = int(round(t * (T - 1)))
        p = tr[idx]
        cx = gap * k
        ax.add_patch(FancyBboxPatch((-2.9 + cx, -2.9), 5.8, 5.8, boxstyle="round,pad=0,rounding_size=0.5",
                                    fc=(1, 1, 1, 0.03), ec=(0.96, 0.72, 0, 0.45), lw=1.5))
        ax.scatter(p[:, 0] + cx, p[:, 1], s=4, color=TIME_CM(min(t, 0.999)), alpha=0.95, lw=0)
        lab = "t = 0 · noise" if t == 0 else ("t = 1 · data" if t == 1 else f"t = {t:.1f}")
        ax.text(cx, -3.35, lab, ha="center", va="top", color=HONEY if t in (0, 1) else MUTED,
                fontsize=22, family="DejaVu Sans Mono", weight="bold")
    W = (len(frames) - 1) * gap + 6.6
    ax.set_xlim(-3.3, W - 3.3); ax.set_aspect("equal")
    H = W * 9 / 16
    ax.set_ylim(-H * 0.47, H * 0.53)
    save(fig, "d4-filmstrip.png", dpi=120, night=True, tight=False)


# ============================================================ section art (portrait 0.866)
SEC = (7.2, 7.2 / 0.866)


def sec_density():
    """p(x): the thing every generative model is trying to learn (KDE of the honeycomb)."""
    rng = np.random.default_rng(2)
    data = hexflower(1500, rng)
    W, H = 2.55, 2.55 / 0.866
    xx, yy = np.meshgrid(np.linspace(-W, W, 520), np.linspace(-H, H, 600))
    g = np.c_[xx.ravel(), yy.ravel()]
    bw = 0.11
    dens = np.zeros(len(g))
    for ch in np.array_split(np.arange(len(g)), 40):
        d2 = ((g[ch, None, :] - data[None]) ** 2).sum(-1)
        dens[ch] = np.exp(-d2 / (2 * bw ** 2)).sum(1)
    D = (dens / dens.max()).reshape(xx.shape)
    fig, ax = night_axes(*SEC)
    ax.imshow(np.sqrt(D), extent=(-W, W, -H, H), origin="lower", cmap=honey_cmap, aspect="auto", interpolation="bicubic")
    ax.contour(xx, yy, D, levels=np.linspace(0.08, 0.9, 9), colors=["#FFF8DC"], linewidths=0.6, alpha=0.35)
    ax.set_xlim(-W, W); ax.set_ylim(-H, H)
    save(fig, "d4-sec-density.png", dpi=110, night=True, tight=False)


def sec_flowfield():
    """Exact marginal flow-matching velocity field at t = 0.6 (streamlines) for the honeycomb."""
    rng = np.random.default_rng(5)
    data = hexflower(700, rng)
    W, H = 2.05, 2.05 / 0.866
    xx, yy = np.meshgrid(np.linspace(-W, W, 140), np.linspace(-H, H, 160))
    t = 0.75
    v = fm_velocity(np.c_[xx.ravel(), yy.ravel()], t, data)
    U, V = v[:, 0].reshape(xx.shape), v[:, 1].reshape(xx.shape)
    spd = np.hypot(U, V)
    fig, ax = night_axes(*SEC)
    bright = LinearSegmentedColormap.from_list("b", [PLUM, CORAL, HONEY, "#FFF8DC"])
    ax.streamplot(xx, yy, U, V, color=np.log1p(spd), cmap=bright, density=2.2, linewidth=1.25, arrowsize=0.9)
    ax.scatter(t * data[:, 0], t * data[:, 1], s=5, color="#FFF8DC", alpha=0.85, zorder=3)
    ax.set_xlim(-W, W); ax.set_ylim(-H, H)
    save(fig, "d4-sec-flow.png", dpi=110, night=True, tight=False)


# ============================================================ VAE latent grid (real training)
def vae_latent():
    import torch
    from torch import nn
    from sklearn.datasets import load_digits
    from scipy.stats import norm
    torch.manual_seed(0)
    X = torch.tensor(load_digits().data / 16.0, dtype=torch.float32)

    class VAE(nn.Module):
        def __init__(s):
            super().__init__()
            s.enc = nn.Sequential(nn.Linear(64, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 4))
            s.dec = nn.Sequential(nn.Linear(2, 128), nn.ReLU(), nn.Linear(128, 256), nn.ReLU(), nn.Linear(256, 64))

        def forward(s, x):
            mu, logvar = s.enc(x).chunk(2, -1)
            z = mu + torch.randn_like(mu) * (0.5 * logvar).exp()        # reparameterization trick
            return s.dec(z), mu, logvar

    m = VAE(); opt = torch.optim.Adam(m.parameters(), 2e-3)
    for step in range(6000):
        xb = X[torch.randint(0, len(X), (128,))]
        logits, mu, logvar = m(xb)
        rec = nn.functional.binary_cross_entropy_with_logits(logits, xb, reduction="sum") / len(xb)
        kl = -0.5 * (1 + logvar - mu ** 2 - logvar.exp()).sum() / len(xb)
        loss = rec + kl
        opt.zero_grad(); loss.backward(); opt.step()
    print(f"  VAE final: recon {rec.item():.1f} nats  KL {kl.item():.2f} nats")
    n = 15
    zs = norm.ppf(np.linspace(0.04, 0.96, n))
    canvas = np.zeros((n * 10, n * 10))
    with torch.no_grad():
        for i, zy in enumerate(zs[::-1]):
            for j, zx in enumerate(zs):
                img = torch.sigmoid(m.dec(torch.tensor([[zx, zy]], dtype=torch.float32))).numpy().reshape(8, 8)
                canvas[i * 10 + 1:i * 10 + 9, j * 10 + 1:j * 10 + 9] = img
    fig = plt.figure(figsize=(8, 8), facecolor=NIGHT)
    ax = fig.add_axes([0.1, 0.08, 0.88, 0.88], facecolor=NIGHT)
    ax.imshow(canvas, cmap=honey_cmap, extent=(0, n, 0, n), interpolation="nearest")
    ax.grid(False)
    for s in ax.spines.values(): s.set_visible(False)
    ticks = [0, (n - 1) / 2, n - 1]
    ax.set_xticks([t + 0.5 for t in ticks]); ax.set_xticklabels([("0" if abs(zs[int(t)]) < 0.05 else f"{zs[int(t)]:+.1f}") for t in ticks], color=MUTED)
    ax.set_yticks([t + 0.5 for t in ticks]); ax.set_yticklabels([("0" if abs(zs[int(t)]) < 0.05 else f"{zs[int(t)]:+.1f}") for t in ticks], color=MUTED)
    ax.tick_params(length=0)
    ax.set_xlabel("latent z₁", color=CREAM, fontsize=21); ax.set_ylabel("latent z₂", color=CREAM, fontsize=21)
    save(fig, "d4-vae-latent.png", night=True, tight=True)


# ============================================================ DDPM noise schedule
def alphabar():
    T = 1000
    t = np.arange(T + 1)
    beta = np.linspace(1e-4, 0.02, T)
    ab_lin = np.r_[1.0, np.cumprod(1 - beta)]
    s = 0.008
    f = np.cos((t / T + s) / (1 + s) * np.pi / 2) ** 2
    ab_cos = f / f[0]
    fig = plt.figure(figsize=(9, 7.2))
    ax = fig.add_axes([0.13, 0.42, 0.83, 0.5])
    ax.plot(t, ab_lin, color=CORAL, lw=4, label="linear β (Ho et al. 2020)")
    ax.plot(t, ab_cos, color=TEAL, lw=4, label="cosine (Nichol & Dhariwal 2021)")
    ax.fill_between(t, ab_lin, color=CORAL, alpha=0.08)
    ax.set_xlim(0, T); ax.set_ylim(0, 1.04)
    ax.set_ylabel(r"$\bar\alpha_t$  (signal kept)")
    ax.set_xlabel("DDPM step t   (0 = data  →  1000 = pure noise)")
    ax.legend(loc="upper right")
    half = np.argmin(np.abs(ab_lin - 0.5))
    ax.annotate(f"half the signal gone\nby t ≈ {half}", xy=(half, 0.5), xytext=(half + 150, 0.62),
                fontsize=16, color=INK, arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5))
    # the spiral under the linear schedule, at five steps
    rng = np.random.default_rng(1)
    x0 = shape_points("spiral", 1200, rng)
    eps = rng.normal(size=x0.shape)
    for k, step in enumerate((0, 100, 250, 500, 1000)):
        a = fig.add_axes([0.13 + k * 0.168, 0.02, 0.15, 0.2])
        xt = np.sqrt(ab_lin[step]) * x0 + np.sqrt(1 - ab_lin[step]) * eps
        a.scatter(xt[:, 0], xt[:, 1], s=1.5, color=CORAL if step else HONEY, alpha=0.8, lw=0)
        a.set_xlim(-3, 3); a.set_ylim(-3, 3); a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([]); a.grid(False)
        for sp in a.spines.values(): sp.set_visible(True); sp.set_color("#d8c88f")
        a.set_title(f"t = {step}", fontsize=16, pad=4)
    save(fig, "d4-alphabar.png")


# ============================================================ straight pairs vs curved marginal flow
def paths():
    rng = np.random.default_rng(8)
    data = hexflower(700, rng)
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.3))
    # left: training pairs (independent coupling) are straight lines that cross
    n = 70
    x0 = rng.normal(size=(n, 2)); x1 = data[rng.integers(0, len(data), n)]
    ax = axs[0]
    for a, b in zip(x0, x1):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=PLUM, lw=1.3, alpha=0.55)
    ax.scatter(data[:, 0], data[:, 1], s=3, color=HONEY, alpha=0.5)
    ax.scatter(x0[:, 0], x0[:, 1], s=26, color=INDIGO, zorder=3, label="noise x₀")
    ax.scatter(x1[:, 0], x1[:, 1], s=26, color=CORAL, zorder=3, label="data x₁")
    ax.set_title("training: straight lines that cross")
    ax.legend(loc="lower left", handletextpad=0.2, borderaxespad=0.1)
    # right: the exact marginal ODE trajectories: no crossings, so they bend
    tr = fm_trajectories(data, 160, steps=120, rng_=np.random.default_rng(3))
    ax = axs[1]
    for i in range(tr.shape[1]):
        p = tr[:, i, :]
        ax.add_collection(LineCollection(np.stack([p[:-1], p[1:]], 1), colors=TIME_CM(np.linspace(0, 0.8, len(p) - 1)), lw=1.4, alpha=0.75))
    ax.scatter(data[:, 0], data[:, 1], s=3, color=HONEY, alpha=0.5)
    ax.scatter(tr[0, :, 0], tr[0, :, 1], s=20, color=INDIGO, zorder=3)
    ax.scatter(tr[-1, :, 0], tr[-1, :, 1], s=20, color=CORAL, zorder=3)
    ax.set_title("sampling: the learned flow bends")
    for ax in axs:
        ax.set_xlim(-3, 3); ax.set_ylim(-3, 3); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for sp in ax.spines.values(): sp.set_visible(True); sp.set_color("#e3d39c")
    fig.tight_layout(w_pad=2)
    save(fig, "d4-paths.png")


# ============================================================ reflow (real MLP trained on its own couplings)
def reflow():
    import torch
    from torch import nn
    torch.manual_seed(0)
    rng = np.random.default_rng(21)
    data = hexflower(700, rng)

    # 1-rectified flow = the exact flow-matching field (a perfectly trained network)
    x0 = rng.normal(size=(16000, 2))
    x1 = np.concatenate([euler_exact(c, data, 200, t_end=0.995) for c in np.array_split(x0, 16)])

    class Net(nn.Module):
        def __init__(s):
            super().__init__()
            s.f = nn.Sequential(nn.Linear(2 + 16, 256), nn.SiLU(), nn.Linear(256, 256), nn.SiLU(),
                                nn.Linear(256, 256), nn.SiLU(), nn.Linear(256, 2))
            s.register_buffer("fr", torch.arange(1, 9, dtype=torch.float32) * np.pi)

        def forward(s, x, t):
            e = torch.cat([torch.sin(t * s.fr), torch.cos(t * s.fr)], -1)
            return s.f(torch.cat([x, e], -1))

    X0 = torch.tensor(x0, dtype=torch.float32); X1 = torch.tensor(x1, dtype=torch.float32)
    net = Net(); opt = torch.optim.AdamW(net.parameters(), 2e-3, weight_decay=0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 6000)
    for step in range(6000):
        idx = torch.randint(0, len(X0), (2048,))
        a, b = X0[idx], X1[idx]
        t = torch.rand(len(idx), 1)
        loss = ((net((1 - t) * a + t * b, t) - (b - a)) ** 2).mean()   # flow matching on (noise, own output) pairs
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    print(f"  reflow final loss {loss.item():.4f}")

    def euler_net(x, steps, keep=False):
        x = torch.tensor(x, dtype=torch.float32); tr = [x.numpy().copy()]
        with torch.no_grad():
            for k in range(steps):
                x = x + net(x, torch.full((len(x), 1), k / steps)) / steps
                tr.append(x.numpy().copy())
        return np.array(tr) if keep else x.numpy()

    def straightness(tr):            # mean squared deviation of the velocity from (end - start)
        v = np.diff(tr, axis=0) * (tr.shape[0] - 1)
        return float(((v - (tr[-1] - tr[0])[None]) ** 2).sum(-1).mean())

    zs = np.random.default_rng(5).normal(size=(2500, 2))
    tr1 = euler_exact(zs[:220], data, 100, t_end=0.995, keep=True)
    tr2 = euler_net(zs[:220], 100, keep=True)
    s1, s2 = straightness(tr1), straightness(tr2)
    print(f"  straightness gap: 1-RF {s1:.3f}  2-RF {s2:.3f}")
    fig, axs = plt.subplots(2, 4, figsize=(16, 8.6))
    rows = [("1-rectified flow\n(exact FM field)", tr1, lambda k: euler_exact(zs, data, k), s1),
            ("2-rectified flow\n(after one reflow)", tr2, lambda k: euler_net(zs, k), s2)]
    for r, (name, tr, sampler, s) in enumerate(rows):
        ax = axs[r, 0]
        for i in range(tr.shape[1]):
            p = tr[:, i, :]
            ax.add_collection(LineCollection(np.stack([p[:-1], p[1:]], 1), colors=TIME_CM(np.linspace(0, .85, len(p) - 1)), lw=1.0, alpha=0.6))
        ax.scatter(data[:, 0], data[:, 1], s=2, color=HONEY, alpha=0.45, zorder=2)
        ax.scatter(tr[-1, :, 0], tr[-1, :, 1], s=7, color=INK, zorder=3)
        ax.set_title(f"paths · bend = {s:.3f}", fontsize=19)
        ax.set_ylabel(name, fontsize=19, color=INK, weight="bold", labelpad=12)
        for c, k in enumerate((1, 2, 4)):
            x = sampler(k)
            ax = axs[r, c + 1]
            ax.scatter(x[:, 0], x[:, 1], s=2.5, color=CORAL if r == 0 else TEAL, alpha=0.7, lw=0)
            ax.set_title(f"{k} Euler step" + ("s" if k > 1 else ""), fontsize=19)
    for ax in axs.ravel():
        ax.set_xlim(-2.8, 2.8); ax.set_ylim(-2.8, 2.8); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for sp in ax.spines.values(): sp.set_visible(True); sp.set_color("#e3d39c")
    fig.tight_layout(h_pad=1.2)
    save(fig, "d4-reflow.png", dpi=130)


# ============================================================ CFG: exact class-conditional flows
MUS = np.array([[-1.1, -0.35], [1.1, -0.35], [0.0, 1.25]])
S_STD = 0.62


def gmm_velocity(x, t, cls=None):
    """Exact FM velocity for x1 ~ mixture of N(mu_k, s^2 I), x0 ~ N(0, I), x_t = (1-t)x0 + t x1."""
    s2 = S_STD ** 2
    var = t * t * s2 + (1 - t) ** 2
    comps = [cls] if cls is not None else [0, 1, 2]
    d = np.stack([x - t * MUS[k] for k in comps], 1)                              # x - t mu_k
    vk = MUS[comps][None] + ((t * s2 - (1 - t)) / var) * d                           # E[x1 - x0 | x_t, k]
    logw = -(d ** 2).sum(-1) / (2 * var)
    w = np.exp(logw - logw.max(1, keepdims=True)); w /= w.sum(1, keepdims=True)
    return (w[..., None] * vk).sum(1)


def cfg_sample(x, w, cls=2, steps=200, keep=False):
    tr = [x.copy()]
    for k in range(steps):
        t = k / steps
        vc = gmm_velocity(x, t, cls)
        v = vc if w == 0 else (1 + w) * vc - w * gmm_velocity(x, t)
        x = x + v / steps
        if keep:
            tr.append(x.copy())
    return np.array(tr) if keep else x


def cfg_sweep():
    z = np.random.default_rng(3).normal(size=(1400, 2))
    ws = (-1, 0, 1, 3, 8)
    fig, axs = plt.subplots(1, 5, figsize=(18, 5.4))
    for ax, w in zip(axs, ws):
        for k, col in enumerate((TEAL, INDIGO, HONEY)):
            ax.add_patch(Circle(MUS[k], 2 * S_STD, color=col, alpha=0.16, lw=0))
            ax.add_patch(Circle(MUS[k], 2 * S_STD, fill=False, ec=col, lw=1.5, alpha=0.6))
        tr = cfg_sample(z[:40], w, keep=True)
        for i in range(tr.shape[1]):
            ax.plot(tr[:, i, 0], tr[:, i, 1], color=PLUM, lw=0.7, alpha=0.35)
        x = cfg_sample(z, w)
        ax.scatter(x[:, 0], x[:, 1], s=4, color=CORAL, alpha=0.75, lw=0, zorder=3)
        inside = np.mean(np.linalg.norm(x - MUS[2], axis=1) < np.linalg.norm(x[:, None] - MUS[None, :2], axis=-1).min(1))
        spread = np.sqrt(np.linalg.det(np.cov(x[np.linalg.norm(x - MUS[2], axis=1) < 3].T))) ** 0.5
        ttl = {-1: "w = −1 · uncond.", 0: "w = 0 · cond."}.get(w, f"w = {w}")
        ax.set_title(ttl, fontsize=21)
        ax.text(0, -2.75, f"on-class {100 * inside:.0f}%  ·  spread {spread:.2f}", ha="center", fontsize=15, color=INK)
        ax.set_xlim(-3.3, 3.3); ax.set_ylim(-3.1, 4.6); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for sp in ax.spines.values(): sp.set_visible(True); sp.set_color("#e3d39c")
    axs[0].text(MUS[2, 0] + 1.75, MUS[2, 1] + 0.95, "class ▲", ha="center", fontsize=16, color="#8a6400", weight="bold")
    fig.tight_layout(w_pad=0.8)
    save(fig, "d4-cfg-sweep.png", dpi=130)


def sec_guidance():
    z = np.random.default_rng(9).normal(size=(260, 2)) * 1.25
    fig, ax = night_axes(*SEC)
    for k, col in enumerate((TEAL, CORAL, HONEY)):
        tr = cfg_sample(z, 3.0, cls=k, steps=120, keep=True)
        for i in range(tr.shape[1]):
            ax.plot(tr[:, i, 0], tr[:, i, 1], color=col, lw=0.8, alpha=0.38)
        ax.scatter(tr[-1, :, 0], tr[-1, :, 1], s=7, color=col, alpha=0.95, zorder=3)
    ax.scatter(z[:, 0], z[:, 1], s=4, color="#8f86d8", alpha=0.6)
    W = 3.0
    ax.set_xlim(-W, W); ax.set_ylim(-W / 0.866 + 0.3, W / 0.866 + 0.3)
    save(fig, "d4-sec-guidance.png", dpi=110, night=True, tight=False)


# ============================================================ patchify (DiT) and its section art
def _cover_crop(aspect):
    img = plt.imread(ROOT / "docs" / "assets" / "img" / "cover-day4.png")[..., :3]
    H, W = img.shape[:2]
    w = int(H * aspect)
    x0 = (W - w) // 2
    return img[:, x0:x0 + w]


def _block_mean(img, n_y, n_x):
    H, W = img.shape[:2]
    img = img[:H - H % n_y, :W - W % n_x]
    return img.reshape(n_y, img.shape[0] // n_y, n_x, img.shape[1] // n_x, 3).mean((1, 3))


def _honeycomb_image(n=256):
    """The honeycomb density, rendered with the honey colormap: our stand-in 'image'."""
    rng = np.random.default_rng(2)
    data = hexflower(1500, rng)
    W = 2.3
    xx, yy = np.meshgrid(np.linspace(-W, W, n), np.linspace(W, -W, n))
    g = np.c_[xx.ravel(), yy.ravel()]
    dens = np.zeros(len(g))
    for ch in np.array_split(np.arange(len(g)), 16):
        dens[ch] = np.exp(-((g[ch, None, :] - data[None]) ** 2).sum(-1) / (2 * 0.11 ** 2)).sum(1)
    D = np.sqrt(dens / dens.max()).reshape(n, n)
    return honey_cmap(D)[..., :3]


def patchify():
    lat = _block_mean(_honeycomb_image(), 32, 32)          # stands in for a 32x32 latent
    fig = plt.figure(figsize=(9, 6.7), facecolor=NIGHT)
    # left: latent with the 2x2 patch grid
    ax = fig.add_axes([0.02, 0.29, 0.46, 0.65], facecolor=NIGHT)
    ax.imshow(lat, interpolation="nearest", extent=(0, 32, 32, 0))
    for g in range(0, 33, 2):
        ax.axhline(g, color=NIGHT, lw=0.8, alpha=0.9); ax.axvline(g, color=NIGHT, lw=0.8, alpha=0.9)
    ax.add_patch(Rectangle((0, 16), 32, 2, fill=False, ec=CORAL, lw=2.5))
    ax.set_xlim(0, 32); ax.set_ylim(32, 0); ax.set_axis_off()
    ax.set_title("latent  32 × 32 × C", color=CREAM, fontsize=20, family="DejaVu Sans Mono")
    # right: exploded patches
    ax = fig.add_axes([0.52, 0.29, 0.46, 0.65], facecolor=NIGHT)
    for i in range(16):
        for j in range(16):
            ax.imshow(lat[2 * i:2 * i + 2, 2 * j:2 * j + 2], interpolation="nearest",
                      extent=(j * 2.5, j * 2.5 + 2, i * 2.5 + 2, i * 2.5))
    ax.add_patch(Rectangle((-0.3, 8 * 2.5 - 0.3), 16 * 2.5 - 0.4, 2.6, fill=False, ec=CORAL, lw=2.5))
    ax.set_xlim(-0.6, 16 * 2.5); ax.set_ylim(16 * 2.5, -0.6); ax.set_axis_off()
    ax.set_title("16 × 16 patches of 2 × 2", color=CREAM, fontsize=20, family="DejaVu Sans Mono")
    # bottom: one row of patches becomes 16 consecutive tokens
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.2], facecolor=NIGHT)
    for j in range(16):
        x = j * 1.3
        ax.imshow(lat[16:18, 2 * j:2 * j + 2], interpolation="nearest", extent=(x, x + 1, 1, 0))
        ax.add_patch(Rectangle((x, 0), 1, 1, fill=False, ec=CORAL, lw=1.4))
    ax.text(16 * 1.3 + 0.2, 0.5, "… 256 tokens", color=HONEY, fontsize=21, va="center", family="DejaVu Sans Mono", weight="bold")
    ax.text(0, 1.6, "one row → 16 tokens → linear embed + position → transformer", color=MUTED, fontsize=16.5, va="center", family="DejaVu Sans Mono")
    ax.set_xlim(-0.2, 16 * 1.3 + 5.6); ax.set_ylim(2.0, -0.2); ax.set_axis_off()
    save(fig, "d4-patchify.png", night=True, tight=True)


def sec_patches():
    img = _cover_crop(0.866)
    H, W = img.shape[:2]
    img = img[int(H * 0.16):int(H * 0.84), int(W * 0.16):int(W * 0.84)]     # zoom into the spiral
    img = np.clip(img * 1.6, 0, 1)
    H, W = img.shape[:2]
    p = 52
    ny, nx = H // p, W // p
    rng = np.random.default_rng(4)
    fig, ax = night_axes(*SEC)
    hi = set(map(tuple, rng.integers(1, [ny - 1, nx - 1], (8, 2))))
    for i in range(ny):
        for j in range(nx):
            lift = (i, j) in hi
            x, y = j * 1.16 + (0.1 if lift else 0), i * 1.16 - (0.1 if lift else 0)
            ax.imshow(img[i * p:(i + 1) * p, j * p:(j + 1) * p], extent=(x, x + 1, y + 1, y), interpolation="bilinear")
            if lift:
                ax.add_patch(Rectangle((x, y), 1, 1, fill=False, ec=HONEY, lw=2.6))
    ax.set_xlim(-0.2, nx * 1.16); ax.set_ylim(ny * 1.16, -0.2)
    save(fig, "d4-sec-patches.png", dpi=110, night=True, tight=False)


# ============================================================ toy CLIP: two towers + symmetric InfoNCE
def _train_clip():
    import torch
    from torch import nn
    torch.manual_seed(0)
    g = np.random.default_rng(0)
    N, dz = 6000, 12
    Z = g.normal(size=(N, dz))                                     # the shared "concept" behind each pair
    A, B = g.normal(size=(dz, 48)), g.normal(size=(dz, 32))
    IMG = np.tanh(Z @ A / 3) + 0.15 * g.normal(size=(N, 48))         # "image" features
    TXT = np.tanh(Z @ B / 3) + 0.15 * g.normal(size=(N, 32))         # "caption" features
    IMG, TXT = map(lambda a: torch.tensor(a, dtype=torch.float32), (IMG, TXT))
    f = nn.Sequential(nn.Linear(48, 128), nn.GELU(), nn.Linear(128, 32))
    gg = nn.Sequential(nn.Linear(32, 128), nn.GELU(), nn.Linear(128, 32))
    logit_scale = nn.Parameter(torch.tensor(np.log(1 / 0.07), dtype=torch.float32))
    test = torch.arange(N - 512, N)

    def sims(idx):
        with torch.no_grad():
            a = nn.functional.normalize(f(IMG[idx]), dim=-1); b = nn.functional.normalize(gg(TXT[idx]), dim=-1)
            return (a @ b.T).numpy()

    def top1(idx):
        S = sims(idx)
        return float((S.argmax(1) == np.arange(len(idx))).mean())

    before = sims(test[:6]); acc0 = top1(test)
    opt = torch.optim.Adam([*f.parameters(), *gg.parameters(), logit_scale], 2e-3)
    for step in range(1500):
        idx = torch.randint(0, N - 512, (256,))
        a = nn.functional.normalize(f(IMG[idx]), dim=-1); b = nn.functional.normalize(gg(TXT[idx]), dim=-1)
        logits = logit_scale.exp() * a @ b.T
        lab = torch.arange(len(idx))
        loss = (nn.functional.cross_entropy(logits, lab) + nn.functional.cross_entropy(logits.T, lab)) / 2
        opt.zero_grad(); loss.backward(); opt.step()
    after = sims(test[:6]); acc1 = top1(test)
    big = sims(test[:28])
    print(f"  CLIP toy: top-1 retrieval among 512 held-out pairs {acc0:.1%} -> {acc1:.1%}, tau={1 / logit_scale.exp().item():.3f}")
    return before, after, acc0, acc1, big


_CLIP = None


def clip_train():
    global _CLIP
    _CLIP = _CLIP or _train_clip()
    before, after, acc0, acc1, _ = _CLIP
    cm = LinearSegmentedColormap.from_list("c", ["#3D4DB7", "#9aa3e0", CARD, "#FFE680", HONEY, CORAL])
    fig, axs = plt.subplots(1, 2, figsize=(12, 6.6))
    for ax, S, ttl in ((axs[0], before, f"before training\nretrieval top-1: {acc0:.1%}"),
                       (axs[1], after, f"after 1,500 steps\nretrieval top-1: {acc1:.1%}")):
        ax.imshow(S, cmap=cm, vmin=-1, vmax=1); ax.grid(False)
        for i in range(len(S)):
            for j in range(len(S)):
                ax.text(j, i, f"{S[i, j]:.1f}".replace("-0.0", "0.0"), ha="center", va="center", fontsize=19,
                        color=INK, weight="bold" if i == j else "normal")
        ax.set_xticks(range(len(S))); ax.set_xticklabels([f"T{j + 1}" for j in range(len(S))], fontsize=18)
        ax.set_yticks(range(len(S))); ax.set_yticklabels([f"I{j + 1}" for j in range(len(S))], fontsize=18)
        ax.tick_params(length=0)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.set_title(ttl)
    axs[0].set_ylabel("images"); axs[0].set_xlabel("captions"); axs[1].set_xlabel("captions")
    fig.tight_layout(w_pad=3)
    save(fig, "d4-clip-train.png")


def sec_clip():
    global _CLIP
    _CLIP = _CLIP or _train_clip()
    S = _CLIP[4]
    fig, ax = night_axes(*SEC)
    n = len(S)
    ax.imshow(np.clip((S + 0.2) / 1.2, 0, 1) ** 1.6, cmap=honey_cmap, extent=(0, n, n * 1.155, 0), interpolation="nearest", aspect="auto")
    for k in range(n + 1):
        ax.axhline(k * 1.155, color=NIGHT, lw=1.2); ax.axvline(k, color=NIGHT, lw=1.2)
    ax.set_xlim(0, n); ax.set_ylim(n * 1.155, 0)
    save(fig, "d4-sec-clip.png", dpi=110, night=True, tight=False)


ALL = [filmstrip, sec_density, sec_flowfield, vae_latent, alphabar, paths, reflow, cfg_sweep, sec_guidance,
       patchify, sec_patches, clip_train, sec_clip]

if __name__ == "__main__":
    only = set(sys.argv[1:])
    for fn in ALL:
        if not only or fn.__name__ in only:
            fn()
