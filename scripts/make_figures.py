"""Generate every figure used on the Gradient Hive course site.

Run:  python scripts/make_figures.py
Writes PNGs into docs/assets/img/. All figures are computed from real code
(unless the caption on the site says "schematic").
"""
from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.collections import LineCollection

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets" / "img"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)

HONEY, INK, CORAL, TEAL, INDIGO, PLUM = "#F5B700", "#1F1B16", "#FF6B5B", "#1FA39A", "#3D4DB7", "#9B5DE5"
PAPER, CARD, NIGHT = "#FFF6D5", "#FFFDF4", "#16130E"
HIVE = [HONEY, INK, CORAL, TEAL, INDIGO, PLUM]
honey_cmap = LinearSegmentedColormap.from_list("honey", [NIGHT, "#3a2c0a", "#8a5f00", HONEY, "#FFE680", "#FFF8DC"])
duo_cmap = LinearSegmentedColormap.from_list("duo", [TEAL, "#bfe6df", CARD, "#ffe8a3", HONEY])

plt.rcParams.update({
    "axes.prop_cycle": plt.cycler(color=HIVE), "figure.facecolor": CARD, "axes.facecolor": CARD,
    "savefig.facecolor": CARD, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#6b6255", "axes.labelcolor": INK, "xtick.color": "#4a443b", "ytick.color": "#4a443b",
    "font.size": 12, "axes.titlesize": 14, "axes.titleweight": "bold", "font.family": "DejaVu Sans",
    "legend.frameon": False, "axes.grid": True, "grid.color": "#efe6c8", "grid.linewidth": 0.8,
})


def save(fig, name, dpi=160):
    fig.savefig(OUT / name, dpi=dpi, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", name)


def cover_axes():
    fig = plt.figure(figsize=(16, 9), facecolor=NIGHT)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=NIGHT)
    ax.set_axis_off()
    return fig, ax


def save_cover(fig, name):
    fig.savefig(OUT / name, dpi=110, facecolor=NIGHT)
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- covers
def cover_day1():
    from sklearn.svm import SVC
    n = 1800
    t = rng.uniform(0.2, 3.6 * np.pi, n)
    lab = rng.integers(0, 2, n)
    r = t / (3.6 * np.pi) * 3.0 + 0.1
    ang = t + lab * np.pi
    X = np.c_[r * np.cos(ang) * 1.55, r * np.sin(ang) * 0.85] + rng.normal(0, 0.1, (n, 2))
    clf = SVC(C=3, gamma=1.2).fit(X, lab)
    xx, yy = np.meshgrid(np.linspace(-4.8, 4.8, 800), np.linspace(-2.7, 2.7, 450))
    D = clf.decision_function(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    P = 1 / (1 + np.exp(-1.6 * D))
    fig, ax = cover_axes()
    ax.imshow(P, extent=(-4.8, 4.8, -2.7, 2.7), origin="lower", cmap=honey_cmap, alpha=0.92, aspect="auto", interpolation="bicubic")
    ax.contour(xx, yy, P, levels=np.linspace(0.05, 0.95, 14), colors=[INK], linewidths=0.6, alpha=0.45)
    ax.contour(xx, yy, P, levels=[0.5], colors=["#FFF8DC"], linewidths=2.4)
    ax.scatter(X[lab == 0, 0], X[lab == 0, 1], s=11, c=TEAL, edgecolors=NIGHT, linewidths=0.3, alpha=0.95)
    ax.scatter(X[lab == 1, 0], X[lab == 1, 1], s=11, c=CORAL, edgecolors=NIGHT, linewidths=0.3, alpha=0.95)
    ax.set_xlim(-4.8, 4.8); ax.set_ylim(-2.7, 2.7)
    save_cover(fig, "cover-day1.png")


def bumpy(x, y):
    return (0.6 * np.sin(1.3 * x) * np.cos(1.1 * y) + 0.05 * (x ** 2 + y ** 2)
            - 0.9 * np.exp(-((x - 1.6) ** 2 + (y + 1.0) ** 2)) - 0.7 * np.exp(-((x + 2.1) ** 2 + (y - 1.4) ** 2) / 0.8))


def grad_bumpy(x, y, h=1e-4):
    return ((bumpy(x + h, y) - bumpy(x - h, y)) / (2 * h), (bumpy(x, y + h) - bumpy(x, y - h)) / (2 * h))


def cover_day2():
    xx, yy = np.meshgrid(np.linspace(-6.4, 6.4, 800), np.linspace(-3.6, 3.6, 450))
    Z = bumpy(xx, yy)
    fig, ax = cover_axes()
    ax.imshow(Z, extent=(-6.4, 6.4, -3.6, 3.6), origin="lower", cmap=honey_cmap.reversed(), aspect="auto", alpha=0.9)
    ax.contour(xx, yy, Z, levels=28, colors=["#FFF8DC"], linewidths=0.5, alpha=0.35)
    cols = [CORAL, TEAL, "#FFF8DC", PLUM, HONEY]
    for k in range(70):
        p = np.array([rng.uniform(-6.2, 6.2), rng.uniform(-3.4, 3.4)])
        v = np.zeros(2); path = [p.copy()]
        for _ in range(260):
            g = np.array(grad_bumpy(*p))
            v = 0.9 * v - 0.06 * g
            p = p + v
            path.append(p.copy())
        path = np.array(path)
        ax.plot(path[:, 0], path[:, 1], color=cols[k % len(cols)], lw=1.1, alpha=0.75)
        ax.scatter(*path[0], s=10, color=cols[k % len(cols)], alpha=0.9)
        ax.scatter(*path[-1], s=26, color="#FFF8DC", edgecolors=INK, lw=0.5, zorder=5)
    ax.set_xlim(-6.4, 6.4); ax.set_ylim(-3.6, 3.6)
    save_cover(fig, "cover-day2.png")


def cover_day3():
    fig, ax = cover_axes()
    words = "the bee who learned to attend found every flower that mattered".split()
    n = len(words)
    xs = np.linspace(0.6, 15.4, n)
    heads = [(HONEY, 1.0), (CORAL, 0.8), (TEAL, 0.7), (PLUM, 0.6)]
    for hi, (col, base) in enumerate(heads):
        for i in range(n):
            logits = rng.normal(0, 1.2, i + 1)
            if hi == 0 and i > 0: logits[i - 1] += 3       # previous-token head
            if hi == 1: logits[0] += 2.5                   # sink head
            w = np.exp(logits) / np.exp(logits).sum()
            for j in range(i + 1):
                if i == j or w[j] < 0.06: continue
                x0, x1 = xs[j], xs[i]
                mid = (x0 + x1) / 2; h = (x1 - x0) * (0.32 + 0.08 * hi)
                tt = np.linspace(0, np.pi, 60)
                ax.plot(mid + (x0 - mid) * np.cos(tt), 2.0 + h * np.sin(tt) * (1 if hi % 2 == 0 else -0.55),
                        color=col, lw=0.6 + 5 * w[j], alpha=min(0.9, 0.15 + w[j]), solid_capstyle="round")
    for x, w in zip(xs, words):
        ax.scatter([x], [2.0], s=180, color="#FFF8DC", zorder=5, edgecolors=HONEY, lw=2)
        ax.text(x, 1.35 if True else 0, w, color="#FFF8DC", ha="center", va="top", fontsize=15, family="DejaVu Sans Mono", alpha=0.9)
    ax.set_xlim(0, 16); ax.set_ylim(-2.5, 9)
    save_cover(fig, "cover-day3.png")


def shape_points(kind, n, rng_):
    if kind == "spiral":
        t = np.sqrt(rng_.uniform(0, 1, n)) * 3.4 * np.pi
        p = np.c_[t * np.cos(t), t * np.sin(t)] / 6
    elif kind == "heart":
        t = rng_.uniform(0, 2 * np.pi, n)
        p = np.c_[16 * np.sin(t) ** 3, 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)] / 9
    return p + rng_.normal(0, 0.04, p.shape)


def fm_velocity(x, t, data, sigma_min=0.02):
    # exact marginal velocity for linear interpolation x_t=(1-t)x0+t*x1, x0~N(0,I), x1~empirical data
    s = (1 - (1 - sigma_min) * t)
    d2 = ((x[:, None, :] - t * data[None, :, :]) ** 2).sum(-1) / (2 * s ** 2)
    w = np.exp(-(d2 - d2.min(1, keepdims=True))); w /= w.sum(1, keepdims=True)
    x1hat = w @ data
    return (x1hat - (1 - sigma_min) * x) / s


def fm_trajectories(data, n, steps=80, rng_=rng):
    x = rng_.normal(0, 1, (n, 2))
    traj = [x.copy()]
    ts = np.linspace(0, 0.995, steps + 1)
    for a, b in zip(ts[:-1], ts[1:]):
        x = x + (b - a) * fm_velocity(x, a, data)
        traj.append(x.copy())
    return np.array(traj)


def cover_day4():
    data = shape_points("spiral", 500, rng) * np.array([1.0, 1.0])
    traj = fm_trajectories(data, 900, steps=90)
    traj[..., 0] = traj[..., 0] * 1.0
    fig, ax = cover_axes()
    cm = LinearSegmentedColormap.from_list("t", [INDIGO, PLUM, CORAL, HONEY, "#FFF8DC"])
    T = traj.shape[0]
    segs, cols = [], []
    for i in range(traj.shape[1]):
        p = traj[:, i, :]
        for k in range(0, T - 1, 2):
            segs.append([p[k], p[min(k + 2, T - 1)]]); cols.append(k / T)
    lc = LineCollection(segs, colors=cm(np.array(cols)), linewidths=0.55, alpha=0.55)
    ax.add_collection(lc)
    ax.scatter(traj[0, :, 0], traj[0, :, 1], s=3, color=INDIGO, alpha=0.6)
    ax.scatter(traj[-1, :, 0], traj[-1, :, 1], s=7, color="#FFF8DC", alpha=0.95, zorder=4)
    ax.set_xlim(-4.6, 4.6); ax.set_ylim(-2.6, 2.6); ax.set_aspect("equal")
    save_cover(fig, "cover-day4.png")


def cover_day5():
    fig, ax = cover_axes()
    ax.set_xlim(-8, 8); ax.set_ylim(-4.5, 4.5); ax.set_aspect("equal")
    for r in [1.1, 2.2, 3.3, 4.4]:
        ax.add_patch(plt.Circle((0, 0), r, fill=False, color="#3a3224", lw=0.8))

    def grow(x, y, ang, spread, depth):
        if depth == 4:
            ok = rng.random() < 0.3
            ax.scatter([x], [y], s=46, color=TEAL if ok else CORAL, zorder=6, edgecolors="#FFF8DC", lw=0.6)
            return
        kids = rng.integers(2, 4) if depth < 3 else rng.integers(1, 3)
        for k in range(kids):
            a = ang + spread * ((k + 0.5) / kids - 0.5)
            r = 1.1 * (depth + 1)
            nx, ny = r * np.cos(a) * 1.75, r * np.sin(a) * 0.92
            ax.plot([x, nx], [y, ny], color=HONEY, alpha=0.25 + 0.15 * (4 - depth), lw=3.2 - 0.6 * depth)
            ax.scatter([nx], [ny], s=26 - 4 * depth, color="#FFF8DC", zorder=5, alpha=0.9)
            grow(nx, ny, a, spread / kids * 1.15, depth + 1)

    for b in range(6):
        grow(0, 0, b * np.pi / 3, np.pi / 3.2, 0)
    ax.scatter([0], [0], s=900, color=HONEY, zorder=7, edgecolors="#FFF8DC", lw=3)
    ax.text(0, 0, "?", color=INK, ha="center", va="center", fontsize=28, weight="bold", zorder=8)
    save_cover(fig, "cover-day5.png")


def cover_home():
    data = shape_points("heart", 420, rng)
    traj = fm_trajectories(data, 700, steps=70)
    fig, ax = cover_axes()
    cm = LinearSegmentedColormap.from_list("t", [INDIGO, PLUM, CORAL, HONEY, "#FFF8DC"])
    T = traj.shape[0]
    segs, cols = [], []
    for i in range(traj.shape[1]):
        p = traj[:, i, :]
        for k in range(0, T - 1, 2):
            segs.append([p[k], p[min(k + 2, T - 1)]]); cols.append(k / T)
    ax.add_collection(LineCollection(segs, colors=cm(np.array(cols)), linewidths=0.6, alpha=0.55))
    ax.scatter(traj[-1, :, 0], traj[-1, :, 1], s=8, color="#FFF8DC", zorder=4)
    ax.set_xlim(-4.6, 4.6); ax.set_ylim(-2.6, 2.6); ax.set_aspect("equal")
    save_cover(fig, "og-image.png")


# ---------------------------------------------------------------- Day 1
def d1_bias_variance():
    f = lambda x: np.sin(2 * np.pi * x)
    xs = np.linspace(0, 1, 200)
    degs = np.arange(1, 14)
    b2, var, tot = [], [], []
    fits = {}
    for d in degs:
        preds = []
        for _ in range(200):
            x = rng.uniform(0, 1, 25); y = f(x) + rng.normal(0, 0.3, 25)
            c = np.polyfit(x, y, d)
            preds.append(np.polyval(c, xs))
        preds = np.clip(np.array(preds), -3, 3)
        if d in (1, 4, 12): fits[d] = preds[:25]
        m = preds.mean(0)
        b2.append(((m - f(xs)) ** 2).mean()); var.append(preds.var(0).mean())
    b2, var = np.array(b2), np.array(var)
    fig, axs = plt.subplots(1, 4, figsize=(17, 3.9), gridspec_kw={"width_ratios": [1, 1, 1, 1.35]})
    for ax, d, name in zip(axs[:3], (1, 4, 12), ("underfit · degree 1", "just right · degree 4", "overfit · degree 12")):
        for p in fits[d]: ax.plot(xs, p, color=HONEY, alpha=0.35, lw=1.2)
        ax.plot(xs, f(xs), color=INK, lw=2.4)
        ax.set_ylim(-2, 2); ax.set_title(name); ax.set_xticks([]); ax.set_yticks([])
    ax = axs[3]
    ax.plot(degs, b2, "-o", color=TEAL, label="bias²", lw=2.4)
    ax.plot(degs, var, "-o", color=CORAL, label="variance", lw=2.4)
    ax.plot(degs, b2 + var + 0.09, "-o", color=INK, label="total error", lw=2.4)
    ax.set_yscale("log"); ax.set_xlabel("polynomial degree (model capacity)"); ax.legend(); ax.set_title("the classic U")
    fig.tight_layout(); save(fig, "d1-bias-variance.png")


def d1_double_descent():
    n, d_in = 60, 5
    Xtr = rng.normal(size=(n, d_in)); Xte = rng.normal(size=(1000, d_in))
    w = rng.normal(size=d_in)
    g = lambda X: X @ w + np.sin(X[:, 0] * 2)
    ytr = g(Xtr) + rng.normal(0, 0.5, n); yte = g(Xte)
    Ps = np.unique(np.r_[np.arange(2, 120, 2), np.arange(120, 600, 20)])
    errs = []
    for p in Ps:
        e = []
        for s in range(15):
            W = rng.normal(size=(d_in, p)) / np.sqrt(d_in)
            Ftr, Fte = np.maximum(Xtr @ W, 0), np.maximum(Xte @ W, 0)
            beta = np.linalg.pinv(Ftr) @ ytr
            e.append(np.mean((Fte @ beta - yte) ** 2))
        errs.append(np.median(e))
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.plot(Ps, errs, color=INK, lw=2.6)
    ax.axvline(n, color=CORAL, ls="--", lw=2); ax.text(n * 1.05, max(errs) * 0.5, "interpolation threshold\n(#features = #samples)", color=CORAL)
    ax.fill_between(Ps, errs, min(errs) * 0.8, where=Ps < n, color=HONEY, alpha=0.18)
    ax.fill_between(Ps, errs, min(errs) * 0.8, where=Ps > n, color=TEAL, alpha=0.15)
    ax.text(10, min(errs) * 1.25, "classical\nregime", color="#8a5f00"); ax.text(300, min(errs) * 1.7, "modern over-\nparameterized regime", color=TEAL)
    ax.set_yscale("log"); ax.set_xscale("log"); ax.set_xlabel("# random ReLU features"); ax.set_ylabel("test MSE")
    ax.set_title("double descent — min-norm least squares on random features")
    save(fig, "d1-double-descent.png")


def d1_boosting_stages():
    from sklearn.tree import DecisionTreeRegressor
    x = np.sort(rng.uniform(0, 10, 160)); y = np.sin(x) + 0.3 * x + rng.normal(0, 0.35, x.size)
    X = x[:, None]; xs = np.linspace(0, 10, 500)[:, None]
    F = np.full_like(y, y.mean()); Fs = np.full(500, y.mean()); lr = 0.3
    snaps = {}
    for m in range(1, 101):
        r = y - F
        t = DecisionTreeRegressor(max_depth=2).fit(X, r)
        F += lr * t.predict(X); Fs = Fs + lr * t.predict(xs)
        if m in (1, 3, 10, 100): snaps[m] = (Fs.copy(), r.copy(), t.predict(xs))
    fig, axs = plt.subplots(2, 4, figsize=(17, 6.4), sharex=True, gridspec_kw={"height_ratios": [1.6, 1]})
    for j, m in enumerate((1, 3, 10, 100)):
        Fm, r, h = snaps[m]
        axs[0, j].scatter(x, y, s=12, color="#b9ae93"); axs[0, j].plot(xs, Fm, color=HONEY, lw=3)
        axs[0, j].set_title(f"after {m} tree{'s' if m > 1 else ''}"); axs[0, j].set_yticks([])
        axs[1, j].scatter(x, r, s=10, color=CORAL, alpha=0.7); axs[1, j].plot(xs, h, color=INK, lw=2)
        axs[1, j].axhline(0, color="#9a8f78", lw=0.8); axs[1, j].set_yticks([])
    axs[0, 0].set_ylabel("ensemble F(x)"); axs[1, 0].set_ylabel("residuals +\nnext tree")
    fig.tight_layout(); save(fig, "d1-boosting-stages.png")


def d1_calibration():
    from sklearn.datasets import make_classification
    from sklearn.naive_bayes import GaussianNB
    from sklearn.calibration import CalibratedClassifierCV, calibration_curve
    X, y = make_classification(20000, 20, n_informative=6, n_redundant=10, random_state=1)
    Xtr, Xte, ytr, yte = X[:12000], X[12000:], y[:12000], y[12000:]
    nb = GaussianNB().fit(Xtr, ytr)
    iso = CalibratedClassifierCV(GaussianNB(), method="isotonic", cv=5).fit(Xtr, ytr)
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    ax = axs[0]
    ax.plot([0, 1], [0, 1], "--", color="#9a8f78", lw=1.5, label="perfect")
    for mdl, name, c in ((nb, "Naive Bayes (raw)", CORAL), (iso, "+ isotonic calibration", TEAL)):
        p = mdl.predict_proba(Xte)[:, 1]
        fr, mp = calibration_curve(yte, p, n_bins=12)
        bins = np.linspace(0, 1, 13); idx = np.clip(np.digitize(p, bins) - 1, 0, 11)
        ece = sum(abs(p[idx == b].mean() - yte[idx == b].mean()) * (idx == b).mean() for b in range(12) if (idx == b).any())
        ax.plot(mp, fr, "-o", color=c, lw=2.6, label=f"{name}  ECE={ece:.3f}")
    ax.set_xlabel("predicted probability"); ax.set_ylabel("observed frequency"); ax.legend(loc="upper left"); ax.set_title("reliability diagram")
    ax = axs[1]
    ax.hist(nb.predict_proba(Xte)[:, 1], bins=40, color=CORAL, alpha=0.75, label="raw")
    ax.hist(iso.predict_proba(Xte)[:, 1], bins=40, color=TEAL, alpha=0.65, label="calibrated")
    ax.set_xlabel("predicted probability"); ax.set_title("over-confidence lives at the edges"); ax.legend()
    fig.tight_layout(); save(fig, "d1-calibration.png")


def d1_conformal():
    from sklearn.ensemble import GradientBoostingRegressor
    n = 2400
    x = rng.uniform(0, 10, n); y = np.sin(x) * 2 + rng.normal(0, 0.15 + 0.12 * x, n)
    X = x[:, None]
    tr, ca, te = slice(0, 1000), slice(1000, 1600), slice(1600, n)
    alpha = 0.1
    mu = GradientBoostingRegressor(n_estimators=200, max_depth=3).fit(X[tr], y[tr])
    s = np.abs(y[ca] - mu.predict(X[ca])); qh = np.quantile(s, np.ceil((600 + 1) * (1 - alpha)) / 600)
    lo = GradientBoostingRegressor(loss="quantile", alpha=alpha / 2, n_estimators=200, max_depth=3).fit(X[tr], y[tr])
    hi = GradientBoostingRegressor(loss="quantile", alpha=1 - alpha / 2, n_estimators=200, max_depth=3).fit(X[tr], y[tr])
    E = np.maximum(lo.predict(X[ca]) - y[ca], y[ca] - hi.predict(X[ca])); qc = np.quantile(E, np.ceil(601 * (1 - alpha)) / 600)
    xs = np.linspace(0, 10, 400)[:, None]
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.6), sharey=True)
    covs = []
    for ax, (L, U, name, c) in zip(axs, (
            (mu.predict(xs) - qh, mu.predict(xs) + qh, "split conformal (constant width)", HONEY),
            (lo.predict(xs) - qc, hi.predict(xs) + qc, "conformalized quantile regression", TEAL))):
        ax.scatter(x[te], y[te], s=5, color="#b9ae93", alpha=0.6)
        ax.fill_between(xs[:, 0], L, U, color=c, alpha=0.35); ax.plot(xs[:, 0], L, color=c, lw=1.5); ax.plot(xs[:, 0], U, color=c, lw=1.5)
        ax.set_title(name); ax.set_xlabel("x")
    cov1 = np.mean(np.abs(y[te] - mu.predict(X[te])) <= qh)
    cov2 = np.mean((y[te] >= lo.predict(X[te]) - qc) & (y[te] <= hi.predict(X[te]) + qc))
    for ax, cov in zip(axs, (cov1, cov2)):
        ax.text(0.02, 0.97, f"test coverage {cov:.1%} (target 90%)", transform=ax.transAxes, va="top", color=INK,
                fontsize=12, bbox=dict(boxstyle="round,pad=0.35", fc=CARD, ec="#e0ce92"))
    fig.tight_layout(); save(fig, "d1-conformal.png")


# ---------------------------------------------------------------- Day 2
def d2_optimizers():
    f = lambda x, y: (1 - x) ** 2 + 100 * (y - x ** 2) ** 2
    df = lambda x, y: np.array([-2 * (1 - x) - 400 * x * (y - x ** 2), 200 * (y - x ** 2)])
    xx, yy = np.meshgrid(np.linspace(-2, 2, 500), np.linspace(-1, 3, 500))
    fig, ax = plt.subplots(figsize=(10, 6.6))
    ax.contourf(xx, yy, np.log1p(f(xx, yy)), levels=30, cmap=duo_cmap.reversed(), alpha=0.85)
    ax.contour(xx, yy, np.log1p(f(xx, yy)), levels=30, colors=["#ffffff"], linewidths=0.4, alpha=0.6)
    start = np.array([-1.7, -0.6])

    def run(kind, steps=2500):
        p = start.copy(); m = np.zeros(2); v = np.zeros(2); path = [p.copy()]
        for t in range(1, steps + 1):
            g = df(*p)
            if kind == "SGD": p = p - 1e-4 * g
            elif kind == "Momentum": m = 0.9 * m + g; p = p - 2e-5 * m
            elif kind == "RMSProp": v = 0.99 * v + 0.01 * g ** 2; p = p - 1e-2 * g / (np.sqrt(v) + 1e-8)
            elif kind == "Adam":
                m = 0.9 * m + 0.1 * g; v = 0.999 * v + 0.001 * g ** 2
                p = p - 5e-2 * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
            path.append(p.copy())
        return np.array(path)

    for kind, c in (("SGD", INK), ("Momentum", CORAL), ("RMSProp", INDIGO), ("Adam", HONEY)):
        P = run(kind)
        ax.plot(P[:, 0], P[:, 1], color=c, lw=2.6 if kind == "Adam" else 2, label=f"{kind} → f={f(*P[-1]):.1e}")
        ax.scatter(*P[-1], color=c, s=50, zorder=5, edgecolors="white")
    ax.scatter([1], [1], marker="*", s=380, color="white", edgecolors=INK, zorder=6, label="global min (1,1)")
    ax.scatter(*start, s=80, color=INK, zorder=6)
    ax.set_title("2500 steps on the Rosenbrock banana (start ●, goal ★)"); ax.legend(loc="lower right", fontsize=10, frameon=True, facecolor=CARD)
    ax.grid(False); save(fig, "d2-optimizers.png")


def d2_schedules():
    T = 1000; t = np.arange(T); w = 50
    cos = np.where(t < w, t / w, 0.5 * (1 + np.cos(np.pi * (t - w) / (T - w))))
    wsd = np.where(t < w, t / w, np.where(t < 0.8 * T, 1.0, 1 - (t - 0.8 * T) / (0.2 * T)))
    step = np.where(t < w, t / w, np.where(t < 500, 1, np.where(t < 800, 0.3, 0.09)))
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(t, cos, color=HONEY, lw=3, label="warmup + cosine")
    ax.plot(t, wsd, color=TEAL, lw=3, label="WSD (warmup–stable–decay)")
    ax.plot(t, step, color=CORAL, lw=2, ls="--", label="step decay")
    ax.annotate("branch a cooldown from\nany stable checkpoint", xy=(600, 1.0), xytext=(420, 0.45), arrowprops=dict(arrowstyle="->", color=TEAL), color=TEAL)
    ax.set_xlabel("training step"); ax.set_ylabel("LR / peak LR"); ax.legend(loc="lower left"); ax.set_title("learning-rate schedules")
    save(fig, "d2-schedules.png")


def d2_grokking():
    s = np.logspace(1, 5, 400)
    train = 1 / (1 + np.exp(-(np.log10(s) - 2.5) * 7))
    test = 0.02 + 0.97 / (1 + np.exp(-(np.log10(s) - 4.0) * 9))
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(s, train * 100, color=HONEY, lw=3, label="train accuracy")
    ax.plot(s, test * 100, color=TEAL, lw=3, label="test accuracy")
    ax.axvspan(10 ** 2.9, 10 ** 3.7, color=CORAL, alpha=0.1); ax.text(10 ** 2.95, 50, "memorized…\n…but not\nunderstood", color=CORAL)
    ax.text(10 ** 4.15, 40, "💡 grokked!".replace("💡 ", ""), color=TEAL, fontsize=14, weight="bold")
    ax.set_xscale("log"); ax.set_xlabel("optimization steps (log)"); ax.set_ylabel("accuracy %"); ax.legend(loc="upper left")
    ax.set_title("grokking (schematic) — you'll reproduce it for real in Lab 2.3")
    save(fig, "d2-grokking.png")


def d2_scaling():
    E, A, B, a, b = 1.69, 406.4, 410.7, 0.34, 0.28   # Hoffmann et al. 2022 parametric fit
    C = np.logspace(18, 25, 300)
    fig, ax = plt.subplots(figsize=(10, 5))
    Ns = np.logspace(7.5, 11.5, 9)
    cm = LinearSegmentedColormap.from_list("n", [PLUM, CORAL, HONEY])
    for i, N in enumerate(Ns):
        D = C / (6 * N); m = D > N * 0.2
        L = E + A / N ** a + B / D ** b
        ax.plot(C[m], L[m], color=cm(i / (len(Ns) - 1)), lw=1.8, alpha=0.9)
        ax.text(C[m][-1] * 1.1, L[m][-1], f"{N / 1e9:.2g}B" if N >= 1e9 else f"{N / 1e6:.0f}M", fontsize=9, color="#4a443b", va="center")
    Ngrid = np.logspace(7, 13, 2000)
    env = [min(E + A / Ngrid ** a + B / (c / (6 * Ngrid)) ** b) for c in C]
    ax.plot(C, env, color=INK, lw=3.5, label="compute-optimal frontier")
    ax.axhline(E, color=TEAL, ls=":", lw=2); ax.text(1.5e18, E + 0.03, "irreducible loss E ≈ 1.69", color=TEAL)
    ax.set_xscale("log"); ax.set_ylim(1.6, 4.2); ax.set_xlim(1e18, 4e25)
    ax.set_xlabel("training compute C (FLOPs) ≈ 6·N·D"); ax.set_ylabel("predicted loss")
    ax.set_title("Chinchilla parametric scaling law: L = E + A/Nᵅ + B/Dᵝ"); ax.legend(loc="upper right")
    save(fig, "d2-scaling.png")


# ---------------------------------------------------------------- Day 3
def d3_attention_heads():
    toks = "Buzz saw the hive . Buzz flew to the".split()
    n = len(toks)
    heads = {}
    L = np.full((n, n), -1.0)
    prev = L.copy(); [prev.__setitem__((i, i - 1), 4) for i in range(1, n)]; prev[0, 0] = 4
    sink = L.copy(); sink[:, 0] = 3.5
    ind = rng.normal(0, 0.4, (n, n))
    for i in range(n):
        for j in range(1, i):
            if toks[j - 1] == toks[i]: ind[i, j] += 5
    for name, Lg in (("previous-token head", prev), ("attention-sink head", sink), ("induction head", ind)):
        Lg = Lg + rng.normal(0, 0.3, (n, n))
        Lg[np.triu_indices(n, 1)] = -np.inf
        W = np.exp(Lg - Lg.max(1, keepdims=True)); W /= W.sum(1, keepdims=True)
        heads[name] = W
    fig, axs = plt.subplots(1, 3, figsize=(17, 5.6))
    cm = LinearSegmentedColormap.from_list("a", [CARD, "#FFE680", HONEY, CORAL, INK])
    for ax, (name, W) in zip(axs, heads.items()):
        ax.imshow(W, cmap=cm, vmin=0, vmax=1); ax.grid(False)
        ax.set_xticks(range(n)); ax.set_xticklabels(toks, rotation=60, fontsize=10)
        ax.set_yticks(range(n)); ax.set_yticklabels(toks, fontsize=10); ax.set_title(name)
    axs[0].set_ylabel("query (current token)"); axs[1].set_xlabel("key (attended-to token)")
    fig.tight_layout(); save(fig, "d3-attention-heads.png")


def d3_rope():
    fig = plt.figure(figsize=(15, 4.8))
    d = 64; base = 10000
    thetas = base ** (-np.arange(0, d, 2) / d)
    for k, (pair, c) in enumerate(((0, CORAL), (8, HONEY), (24, TEAL))):
        ax = fig.add_subplot(1, 4, k + 1, projection="polar")
        for m in range(0, 12):
            a = m * thetas[pair]
            ax.annotate("", xy=(a, 1), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=c, alpha=0.25 + 0.06 * m, lw=2))
        ax.set_yticks([]); ax.set_title(f"dims {2 * pair}-{2 * pair + 1}: θ={thetas[pair]:.3g}", fontsize=11)
    ax = fig.add_subplot(1, 4, 4)
    q = rng.normal(size=d); kv = q + rng.normal(0, 0.3, d)
    def rot(v, m):
        v2 = v.reshape(-1, 2); c, s = np.cos(m * thetas), np.sin(m * thetas)
        return np.c_[v2[:, 0] * c - v2[:, 1] * s, v2[:, 0] * s + v2[:, 1] * c].ravel()
    rel = np.arange(0, 400)
    sc = [rot(q, 500) @ rot(kv, 500 - r) for r in rel]
    ax.plot(rel, sc, color=INDIGO, lw=1.6); ax.set_xlabel("relative distance m−n"); ax.set_title("q·k depends only on m−n", fontsize=12)
    fig.tight_layout(); save(fig, "d3-rope.png")


def d3_sampling():
    words = ["honey", "nectar", "pollen", "flowers", "the", "wax", "royal", "jelly", "sunshine", "math", "rust", "taxes"]
    logits = np.array([4.1, 3.5, 3.2, 2.9, 2.1, 1.9, 1.2, 1.0, 0.7, -0.2, -1.0, -1.6])
    def sm(z, T): e = np.exp((z - z.max()) / T); return e / e.sum()
    fig, axs = plt.subplots(1, 4, figsize=(18, 4.4), sharey=True)
    p = sm(logits, 1.0)
    configs = [("temperature 0.5", sm(logits, 0.5), None), ("temperature 1.5", sm(logits, 1.5), None),
               ("top-k = 4", p, np.arange(12) < 4), ("top-p = 0.8", p, np.r_[True, np.cumsum(p)[:-1] < 0.8])]
    for ax, (name, q, keep) in zip(axs, configs):
        cols = [HONEY if (keep is None or keep[i]) else "#d9d0b6" for i in range(12)]
        ax.barh(range(12)[::-1], q, color=cols, edgecolor=INK, lw=0.6)
        if keep is not None:
            qq = np.where(keep, q, 0); qq /= qq.sum()
            ax.barh(range(12)[::-1], qq, color="none", edgecolor=CORAL, lw=2, ls="--")
        ax.set_title(name); ax.set_xlim(0, 0.8)
    axs[0].set_yticks(range(12)[::-1]); axs[0].set_yticklabels(words)
    fig.suptitle('next token after "The bees made sweet …"', y=1.03, fontsize=14)
    fig.tight_layout(); save(fig, "d3-sampling.png")


def d3_kv_memory():
    ctx = np.logspace(np.log10(1024), np.log10(1_048_576), 200)
    layers, heads, hd = 32, 32, 128
    cfg = {"MHA (32 KV heads)": 2 * layers * heads * hd * 2, "GQA (8 KV heads)": 2 * layers * 8 * hd * 2,
           "MQA (1 KV head)": 2 * layers * 1 * hd * 2, "MLA-style latent (576 dims)": layers * 576 * 2}
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for (name, bpt), c in zip(cfg.items(), (CORAL, HONEY, TEAL, INDIGO)):
        ax.plot(ctx, ctx * bpt / 1e9, lw=3, color=c, label=f"{name}: {bpt / 1024:.0f} KB/token")
    ax.axhline(80, color=INK, ls=":", lw=1.5); ax.text(1200, 90, "one 80 GB GPU", color=INK)
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("context length (tokens)"); ax.set_ylabel("KV-cache size (GB, fp16, batch 1)")
    ax.set_title("KV-cache memory for a 32-layer, d=4096 model"); ax.legend(loc="upper left", fontsize=10)
    save(fig, "d3-kv-memory.png")


def d3_moe():
    E, T = 16, 8192
    bias = rng.normal(0, 1.2, E)
    logits = rng.normal(0, 1, (T, E)) + bias
    top = np.argsort(-logits, 1)[:, :2]
    unb = np.bincount(top.ravel(), minlength=E) / (2 * T)
    bal = np.clip(1 / E + rng.normal(0, 0.006, E), 0, None); bal /= bal.sum()
    fig, ax = plt.subplots(figsize=(11, 3.8))
    x = np.arange(E)
    ax.bar(x - 0.2, unb, 0.4, color=CORAL, label="no balancing loss (collapse-prone)")
    ax.bar(x + 0.2, bal, 0.4, color=TEAL, label="with load-balancing")
    ax.axhline(1 / E, color=INK, ls="--", lw=1.4); ax.text(E - 0.5, 1 / E + 0.005, "ideal 1/E", ha="right")
    ax.set_xticks(x); ax.set_xlabel("expert id"); ax.set_ylabel("fraction of tokens"); ax.legend(); ax.set_title("token routing across 16 experts (top-2, illustrative)")
    save(fig, "d3-moe.png")


# ---------------------------------------------------------------- Day 4
def d4_forward():
    x1 = shape_points("spiral", 1500, rng)
    eps = rng.normal(size=x1.shape)
    fig, axs = plt.subplots(1, 6, figsize=(18, 3.4))
    for ax, t in zip(axs, (1.0, 0.8, 0.6, 0.4, 0.2, 0.0)):
        xt = t * x1 + (1 - t) * eps
        ax.scatter(xt[:, 0], xt[:, 1], s=3, color=HONEY if t > 0.5 else (CORAL if t > 0 else INDIGO), alpha=0.8)
        ax.set_xlim(-3, 3); ax.set_ylim(-3, 3); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"t = {t:.1f}")
    axs[0].set_title("t = 1 (data)"); axs[-1].set_title("t = 0 (pure noise)")
    fig.suptitle("noising path  xₜ = t·x_data + (1−t)·ε   — sampling runs it from t = 0 (noise) to t = 1 (data)", y=1.05)
    save(fig, "d4-forward.png")


def d4_trajectories():
    fig, axs = plt.subplots(1, 2, figsize=(13, 5.4))
    data = shape_points("heart", 400, rng)
    cm = LinearSegmentedColormap.from_list("t", [INDIGO, PLUM, CORAL, HONEY])
    for ax, steps, name in ((axs[0], 100, "100 Euler steps"), (axs[1], 4, "4 Euler steps")):
        tr = fm_trajectories(data, 500, steps=steps, rng_=np.random.default_rng(3))
        for i in range(0, tr.shape[1], 2):
            pts = tr[:, i, :]; segs = np.stack([pts[:-1], pts[1:]], 1)
            ax.add_collection(LineCollection(segs, colors=cm(np.linspace(0, 1, len(segs))), lw=0.8, alpha=0.5))
        ax.scatter(tr[-1, :, 0], tr[-1, :, 1], s=6, color=INK, zorder=3)
        ax.set_xlim(-3.2, 3.2); ax.set_ylim(-3, 2.8); ax.set_aspect("equal"); ax.set_title(name); ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("probability-flow ODE: noise → data (exact flow-matching field on an empirical heart)", y=1.0)
    save(fig, "d4-trajectories.png")


def d4_cfg():
    mus = {0: np.array([-1.1, 0.0]), 1: np.array([1.1, 0.0]), 2: np.array([0.0, 1.4])}
    cov = 0.5

    def score(x, cls, sig):
        s2 = cov + sig ** 2
        comps = [cls] if cls is not None else list(mus)
        d = np.stack([x - mus[c] for c in comps], 1)
        logw = -(d ** 2).sum(-1) / (2 * s2); w = np.exp(logw - logw.max(1, keepdims=True)); w /= w.sum(1, keepdims=True)
        return -(w[..., None] * d).sum(1) / s2

    fig, axs = plt.subplots(1, 4, figsize=(17, 4.2))
    for ax, wgt in zip(axs, (0.0, 1.0, 3.0, 7.0)):
        x = rng.normal(0, 3, (900, 2))
        for sig in np.geomspace(3, 0.05, 80):
            for _ in range(3):
                eta = 0.15 * sig ** 2
                s = score(x, None, sig) + (1 + wgt) * (score(x, 2, sig) - score(x, None, sig)) if wgt > 0 else score(x, 2, sig)
                x = x + eta * s + np.sqrt(2 * eta) * rng.normal(size=x.shape)
        for c, col in zip(mus, (TEAL, INDIGO, HONEY)):
            ax.add_patch(plt.Circle(mus[c], np.sqrt(cov) * 2, color=col, alpha=0.12))
        ax.scatter(x[:, 0], x[:, 1], s=4, color=CORAL, alpha=0.7)
        ax.set_xlim(-4, 4); ax.set_ylim(-2.5, 4.5); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title("conditional (w=0)" if wgt == 0 else f"guidance w = {wgt:g}")
    fig.suptitle("classifier-free guidance on a 3-class Gaussian mixture: sharper, less diverse samples of class ▲", y=1.04)
    save(fig, "d4-cfg.png")


def d4_clip():
    caps = ["a bee on a sunflower", "a cat asleep on a laptop", "a city skyline at night", "a bowl of ramen", "a red sports car", "a snowy mountain"]
    n = len(caps)
    I = rng.normal(size=(n, 32)); T = I + rng.normal(0, 0.6, (n, 32))
    I /= np.linalg.norm(I, axis=1, keepdims=True); T /= np.linalg.norm(T, axis=1, keepdims=True)
    S = I @ T.T
    fig, ax = plt.subplots(figsize=(8.6, 6.6))
    cm = LinearSegmentedColormap.from_list("c", [CARD, "#FFE680", HONEY, CORAL])
    ax.imshow(S, cmap=cm); ax.grid(False)
    for i in range(n):
        for j in range(n): ax.text(j, i, f"{S[i, j]:.2f}", ha="center", va="center", fontsize=10, color=INK)
    ax.set_xticks(range(n)); ax.set_xticklabels(caps, rotation=35, ha="right"); ax.set_yticks(range(n)); ax.set_yticklabels([f"🖼 image {i + 1}".replace("🖼 ", "") for i in range(n)])
    ax.set_title("CLIP objective: matched pairs on the diagonal"); save(fig, "d4-clip.png")


# ---------------------------------------------------------------- Day 5
def d5_test_time():
    Ns = np.array([1, 2, 4, 8, 16, 32, 64, 128])
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.6))
    for p, c in ((0.3, CORAL), (0.45, HONEY), (0.6, TEAL)):
        wrong = np.array([0.35, 0.25, 0.2, 0.12, 0.08]) * (1 - p)
        probs = np.r_[p, wrong]
        acc = []
        for N in Ns:
            draws = rng.choice(6, size=(4000, N), p=probs)
            counts = np.stack([(draws == k).sum(1) for k in range(6)], 1)
            win = counts.argmax(1)
            acc.append((win == 0).mean())
        axs[0].plot(Ns, acc, "-o", color=c, lw=2.6, label=f"single-sample acc {p:.0%}")
        axs[1].plot(Ns, 1 - (1 - p) ** Ns, "-o", color=c, lw=2.6, label=f"p = {p:.0%}")
    axs[0].set_xscale("log", base=2); axs[0].set_title("majority vote (self-consistency)"); axs[0].set_xlabel("samples N"); axs[0].set_ylabel("accuracy"); axs[0].legend()
    axs[1].set_xscale("log", base=2); axs[1].set_title("pass@N with a perfect verifier"); axs[1].set_xlabel("samples N"); axs[1].legend()
    fig.suptitle("test-time compute: spending more inference FLOPs buys accuracy", y=1.03)
    fig.tight_layout(); save(fig, "d5-test-time.png")


def d5_quant():
    w = rng.standard_t(4, 4096) * 0.02
    w[rng.choice(4096, 6)] *= 14
    def q_absmax(x, bits=4):
        qmax = 2 ** (bits - 1) - 1; s = np.abs(x).max() / qmax
        return np.round(x / s).clip(-qmax - 1, qmax) * s, s
    wq, s = q_absmax(w)
    G = w.reshape(-1, 64); wg = np.concatenate([q_absmax(g)[0] for g in G])
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.3))
    axs[0].hist(w, bins=200, color=HONEY, alpha=0.9)
    for k in range(-8, 8): axs[0].axvline(k * s, color=CORAL, lw=0.8, alpha=0.8)
    axs[0].set_xlim(-0.25, 0.25); axs[0].set_title("per-tensor int4 grid (red) vs weight histogram"); axs[0].set_xlabel("weight value")
    e1, e2 = np.mean((w - wq) ** 2), np.mean((w - wg) ** 2)
    axs[1].bar(["per-tensor\nabsmax int4", "group-wise (g=64)\nabsmax int4"], [e1, e2], color=[CORAL, TEAL])
    axs[1].set_yscale("log"); axs[1].set_ylabel("reconstruction MSE"); axs[1].set_title(f"outliers wreck per-tensor scales ({e1 / e2:.0f}× worse)")
    fig.tight_layout(); save(fig, "d5-quant.png")


def d5_grpo():
    rewards = np.array([1, 0, 0, 1, 1, 0, 0, 0], float) + np.array([0.2, 0.2, 0, 0.2, 0.2, 0, 0.2, 0])
    adv = (rewards - rewards.mean()) / (rewards.std() + 1e-6)
    fig, axs = plt.subplots(1, 2, figsize=(14, 4))
    labels = [f"o{i + 1}" for i in range(8)]
    axs[0].bar(labels, rewards, color=[TEAL if r >= 1 else "#c9bfa5" for r in rewards], edgecolor=INK)
    axs[0].axhline(rewards.mean(), color=INK, ls="--"); axs[0].set_title("rewards for 8 sampled answers to ONE prompt"); axs[0].text(7.4, rewards.mean() + 0.04, "group mean", ha="right")
    axs[1].bar(labels, adv, color=[TEAL if a > 0 else CORAL for a in adv], edgecolor=INK)
    axs[1].axhline(0, color=INK); axs[1].set_title("group-relative advantage  Âᵢ = (rᵢ − mean) / std")
    fig.tight_layout(); save(fig, "d5-grpo.png")


def d5_superposition():
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.2))
    ang = np.pi / 2 + np.arange(5) * 2 * np.pi / 5
    cols = [HONEY, CORAL, TEAL, INDIGO, PLUM]
    names = ["‘bee’", "‘Python code’", "‘French’", "‘DNA’", "‘sarcasm’"]
    for a, c, nm in zip(ang, cols, names):
        axs[0].annotate("", xy=(np.cos(a), np.sin(a)), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=c, lw=3))
        axs[0].text(1.22 * np.cos(a), 1.22 * np.sin(a), nm, ha="center", va="center", color=c, fontsize=13, weight="bold")
    axs[0].set_xlim(-1.6, 1.6); axs[0].set_ylim(-1.5, 1.6); axs[0].set_aspect("equal"); axs[0].grid(False); axs[0].set_xticks([]); axs[0].set_yticks([])
    axs[0].set_title("superposition: 5 sparse features squeezed into 2 dims")
    l0 = np.linspace(5, 200, 100)
    for k, (nm, c) in enumerate((("ReLU + L1 SAE", CORAL), ("TopK SAE", TEAL), ("JumpReLU SAE", INDIGO))):
        fvu = 0.03 + (0.5 - 0.04 * k) / (1 + (l0 / (18 - 4 * k)) ** 0.8)
        axs[1].plot(l0, fvu, lw=3, color=c, label=nm)
    axs[1].set_xlabel("L0 (active latents per token)"); axs[1].set_ylabel("fraction of variance unexplained")
    axs[1].set_title("SAE sparsity–fidelity frontier (schematic)"); axs[1].legend()
    fig.tight_layout(); save(fig, "d5-superposition.png")


if __name__ == "__main__":
    import sys
    only = set(sys.argv[1:])
    for fn in [cover_day1, cover_day2, cover_day3, cover_day4, cover_day5, cover_home,
               d1_bias_variance, d1_double_descent, d1_boosting_stages, d1_calibration, d1_conformal,
               d2_optimizers, d2_schedules, d2_grokking, d2_scaling,
               d3_attention_heads, d3_rope, d3_sampling, d3_kv_memory, d3_moe,
               d4_forward, d4_trajectories, d4_cfg, d4_clip,
               d5_test_time, d5_quant, d5_grpo, d5_superposition]:
        if not only or fn.__name__ in only:
            fn()
