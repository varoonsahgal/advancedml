"""Figures for the Day 1 slide deck (site/slides/day-1.html).

Run:  python scripts/slides/figs_day1.py
Writes docs/assets/img/slides/d1-*.png. Every figure is computed from real code:
the "art" images are real models (bootstrap refits, a boosted classifier,
conformalized quantile bands, exact Shapley values) rendered on a night background.
"""
import sys
from itertools import combinations
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from make_figures import HONEY, INK, CORAL, TEAL, INDIGO, PLUM, PAPER, CARD, NIGHT, honey_cmap, duo_cmap, plt, np  # noqa: E402,F401
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

OUT = SCRIPTS.parent / "docs" / "assets" / "img" / "slides"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(2026)
CREAM, MUTED, GRID = "#FFF3C4", "#7A6E5A", "#efe6c8"
HONEY_DEEP = "#B98500"

# Slide figures are shown at ~60-70% scale, so everything is set big.
plt.rcParams.update({"font.size": 17, "axes.titlesize": 21, "axes.labelsize": 19, "xtick.labelsize": 16,
                     "ytick.labelsize": 16, "legend.fontsize": 17, "axes.linewidth": 1.2})


def save(fig, name, dpi=160):
    fig.savefig(OUT / name, dpi=dpi, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print("wrote", name)


def save_art(fig, name):
    fig.savefig(OUT / name, dpi=120, facecolor=NIGHT)
    plt.close(fig)
    print("wrote", name)


def art_axes():
    """16x9 night canvas with a soft radial glow, so a hexagon crop reads as a tile on the night slide."""
    fig = plt.figure(figsize=(16, 9), facecolor=NIGHT)
    bg = fig.add_axes([0, 0, 1, 1]); bg.set_axis_off()
    yy, xx = np.mgrid[-1:1:270j, -1:1:480j]
    glow = LinearSegmentedColormap.from_list("glow", ["#1B1711", "#2E2619"])
    bg.imshow(np.exp(-(xx ** 2 + yy ** 2) / 0.9), cmap=glow, aspect="auto", extent=(0, 1, 0, 1))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("none")
    ax.set_axis_off()
    return fig, ax


# ---------------------------------------------------------------- exact Shapley (brute force)
def exact_shapley(predict, X, background):
    """Interventional Shapley values by enumerating all 2^d coalitions.
    v(S) = E_b[ f(x_S, b_~S) ] over the background rows b."""
    n, d = X.shape
    nb = len(background)
    v = {}
    for k in range(d + 1):
        for S in combinations(range(d), k):
            Z = np.tile(background, (n, 1))
            if S:
                Z[:, list(S)] = np.repeat(X[:, list(S)], nb, axis=0)
            v[S] = predict(Z).reshape(n, nb).mean(1)
    from math import factorial
    phi = np.zeros((n, d))
    for i in range(d):
        rest = [j for j in range(d) if j != i]
        for k in range(d):
            w = factorial(k) * factorial(d - k - 1) / factorial(d)
            for S in combinations(rest, k):
                Si = tuple(sorted(S + (i,)))
                phi[:, i] += w * (v[Si] - v[S])
    return phi, v[()], v[tuple(range(d))]


# ---------------------------------------------------------------- night art
def art_refits():
    """400 bootstrap refits of a degree-9 polynomial: variance, made visible."""
    f = lambda x: np.sin(2 * np.pi * x)
    xs = np.linspace(-0.02, 1.02, 600)
    cmap = LinearSegmentedColormap.from_list("v", [CREAM, HONEY, CORAL, PLUM])
    segs, errs = [], []
    for _ in range(400):
        x = rng.uniform(0, 1, 30); y = f(x) + rng.normal(0, 0.3, 30)
        c = np.polyfit(x, y, 9)
        p = np.clip(np.polyval(c, xs), -4, 4)
        segs.append(np.c_[xs, p]); errs.append(np.mean((p - f(xs)) ** 2))
    order = np.argsort(errs)[::-1]                      # draw the wildest first, the best on top
    r = np.argsort(np.argsort(errs)) / len(errs)
    fig, ax = art_axes()
    for lw, a in ((5, 0.025), (1.3, 0.22)):
        lc = LineCollection([segs[i] for i in order], colors=cmap(r[order]), linewidths=lw, alpha=a)
        ax.add_collection(lc)
    for lw, a in ((16, 0.05), (9, 0.1), (3.2, 1.0)):
        ax.plot(xs, f(xs), color=CREAM, lw=lw, alpha=a, solid_capstyle="round")
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-2.3, 2.3)
    save_art(fig, "d1-art-refits.png")


def art_boosting():
    """Gradient boosting from scratch (squared loss, depth-3 trees, nu = 0.04): every one of the
    400 stages F_1 ... F_400 drawn on top of each other, from plum (early) to cream (late)."""
    from sklearn.tree import DecisionTreeRegressor
    x = np.sort(rng.uniform(0, 10, 420)); y = 1.7 * np.sin(x) + 0.25 * x + rng.normal(0, 0.35, x.size)
    xs = np.linspace(0, 10, 1400)
    F, Fs = np.full_like(y, y.mean()), np.full_like(xs, y.mean())
    segs = []
    for m in range(400):
        t = DecisionTreeRegressor(max_depth=3, min_samples_leaf=12).fit(x[:, None], y - F)     # fit the residuals = -dL/dF
        F += 0.04 * t.predict(x[:, None]); Fs = Fs + 0.04 * t.predict(xs[:, None])
        segs.append(np.c_[xs, Fs.copy()])
    cmap = LinearSegmentedColormap.from_list("stage", [PLUM, CORAL, HONEY, CREAM])
    c = cmap(np.linspace(0, 1, len(segs)) ** 0.6)
    fig, ax = art_axes()
    ax.scatter(x, y, s=16, color=CREAM, alpha=0.35, lw=0)
    ax.add_collection(LineCollection(segs, colors=c, linewidths=4, alpha=0.05))
    ax.add_collection(LineCollection(segs, colors=c, linewidths=1.2, alpha=0.55))
    for lw, a in ((14, 0.06), (7, 0.12), (2.6, 1.0)):
        ax.plot(xs, Fs, color=CREAM, lw=lw, alpha=a)
    ax.set_xlim(0, 10); ax.set_ylim(y.min() - 1.4, y.max() + 1.4)
    save_art(fig, "d1-art-boosting.png")


def cqr_bands(x, y, xs, alphas, n_knots=14):
    """Conformalized quantile regression with spline quantile regressors. Returns {alpha: (lo, hi)}."""
    from sklearn.linear_model import QuantileRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import SplineTransformer
    n = len(x); tr, ca = np.arange(n) < n // 2, np.arange(n) >= n // 2
    out = {}
    for a in alphas:
        qs = []
        for q in (a / 2, 1 - a / 2):
            m = make_pipeline(SplineTransformer(n_knots=n_knots, degree=3), QuantileRegressor(quantile=q, alpha=0, solver="highs"))
            qs.append(m.fit(x[tr, None], y[tr]))
        lo, hi = qs
        E = np.maximum(lo.predict(x[ca, None]) - y[ca], y[ca] - hi.predict(x[ca, None]))
        nc = ca.sum()
        qc = np.quantile(E, min(1, np.ceil((nc + 1) * (1 - a)) / nc), method="higher")
        out[a] = (lo.predict(xs[:, None]) - qc, hi.predict(xs[:, None]) + qc)
    return out


def art_conformal():
    """Nested CQR bands (alpha = 0.5 ... 0.02) on heteroscedastic data."""
    n = 1600
    x = rng.uniform(0, 10, n); y = 2 * np.sin(x) + 0.35 * x + rng.normal(0, 0.12 + 0.11 * x, n)
    xs = np.linspace(-0.2, 10.2, 800)
    alphas = (0.6, 0.4, 0.25, 0.1, 0.05, 0.02)
    bands = cqr_bands(x, y, xs, alphas)
    fig, ax = art_axes()
    cmap = LinearSegmentedColormap.from_list("b", [PLUM, CORAL, HONEY, CREAM])
    for k, a in enumerate(alphas[::-1]):                  # widest first
        lo, hi = bands[a]
        c = cmap(k / (len(alphas) - 1))
        ax.fill_between(xs, lo, hi, color=c, alpha=0.2, lw=0)
        ax.plot(xs, lo, color=c, lw=1.4, alpha=0.8); ax.plot(xs, hi, color=c, lw=1.4, alpha=0.8)
    ax.scatter(x, y, s=6, color=CREAM, alpha=0.55, lw=0)
    ax.set_xlim(0.35, 9.55); ax.set_ylim(-3.6, 7.4)
    save_art(fig, "d1-art-conformal.png")


DIAB = ["age", "bmi", "bp", "s3", "s5", "s6"]
DIAB_LABEL = {"age": "age", "bmi": "BMI", "bp": "blood pressure", "s3": "HDL", "s5": "triglycerides (log)", "s6": "glucose"}


def diabetes_model():
    from sklearn.datasets import load_diabetes
    from sklearn.ensemble import HistGradientBoostingRegressor
    d = load_diabetes(scaled=False)
    idx = [d.feature_names.index(f) for f in DIAB]
    X, y = d.data[:, idx], d.target
    m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_depth=3, random_state=0).fit(X, y)
    return X, y, m


def art_shap():
    """Beeswarm of exact (brute-force) Shapley values for a GBDT on the diabetes data."""
    X, y, m = diabetes_model()
    bg = X[rng.choice(len(X), 80, replace=False)]
    phi, base, _ = exact_shapley(m.predict, X, bg)
    order = np.argsort(np.abs(phi).mean(0))
    cmap = LinearSegmentedColormap.from_list("fv", [TEAL, CREAM, HONEY, CORAL])
    fig, ax = art_axes()
    for row, j in enumerate(order):
        v = phi[:, j]
        fv = (X[:, j] - X[:, j].min()) / np.ptp(X[:, j])
        # beeswarm: within each narrow bin, stack points alternately above/below the row line
        w = np.ptp(phi) / 140
        bins = np.round(v / w).astype(int)
        off = np.zeros(len(v))
        for bb in np.unique(bins):
            ii = np.where(bins == bb)[0]
            k = np.arange(len(ii))
            off[ii] = ((k + 1) // 2) * np.where(k % 2, 1, -1)
        off *= 0.4 / max(1, np.abs(off).max())
        ax.scatter(v, row + off, s=34, c=cmap(fv), alpha=0.95, edgecolors=NIGHT, linewidths=0.4)
        ax.axhline(row, color="#3a3122", lw=1, zorder=0)
    ax.axvline(0, color="#5b4e36", lw=1.5, zorder=0)
    lim = np.abs(phi).max() * 1.05
    ax.set_xlim(-lim * 0.75, lim); ax.set_ylim(-0.7, len(order) - 0.3)
    save_art(fig, "d1-art-shap.png")


# ---------------------------------------------------------------- content figures
def double_descent_ridge():
    """Min-norm vs ridge on random ReLU features: explicit regularization removes the spike."""
    n, d_in = 60, 5
    Xtr = rng.normal(size=(n, d_in)); Xte = rng.normal(size=(2000, d_in))
    w = rng.normal(size=d_in)
    g = lambda X: X @ w + np.sin(2 * X[:, 0])
    ytr = g(Xtr) + rng.normal(0, 0.5, n); yte = g(Xte)
    Ps = np.unique(np.r_[np.arange(4, 120, 2), np.arange(120, 1000, 30)])
    lams = (0.0, 1e-3, 1e-1)
    errs = {l: [] for l in lams}
    for p in Ps:
        e = {l: [] for l in lams}
        for s in range(25):
            W = rng.normal(size=(d_in, p)) / np.sqrt(d_in)
            Ftr, Fte = np.maximum(Xtr @ W, 0), np.maximum(Xte @ W, 0)
            for l in lams:
                if l == 0:
                    beta = np.linalg.pinv(Ftr) @ ytr                       # minimum-norm least squares
                else:
                    beta = Ftr.T @ np.linalg.solve(Ftr @ Ftr.T + l * p * np.eye(n), ytr)   # ridge, dual form
                e[l].append(np.mean((Fte @ beta - yte) ** 2))
        for l in lams:
            errs[l].append(np.median(e[l]))
    fig, ax = plt.subplots(figsize=(8.4, 6.6))
    ax.axvspan(Ps[0], n, color=HONEY, alpha=0.10, lw=0); ax.axvspan(n, Ps[-1], color=TEAL, alpha=0.07, lw=0)
    for l, c, lw, lab in zip(lams, (INK, CORAL, TEAL), (3.4, 2.6, 2.6), ("min-norm (λ = 0)", "ridge λ = 10⁻³", "ridge λ = 10⁻¹")):
        ax.plot(Ps, errs[l], color=c, lw=lw, label=lab)
    ax.axvline(n, color=CORAL, ls="--", lw=2)
    ax.text(n * 1.08, max(errs[0.0]) * 0.55, "interpolation\nthreshold\n(p = n = 60)", color=CORAL, fontsize=17, va="top")
    ax.text(5, 0.42, "classical", color="#8a5f00", fontsize=18, fontweight="bold")
    ax.text(130, 0.42, "over-\nparameterized", color=TEAL, fontsize=18, fontweight="bold", va="bottom")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("# random ReLU features p"); ax.set_ylabel("test MSE (median of 25 draws)")
    ax.set_xlim(Ps[0], Ps[-1]); ax.set_ylim(0.3, None)
    ax.legend(loc="upper left")
    fig.tight_layout(); save(fig, "d1-double-descent-ridge.png")


def shrinkage():
    """Validation loss vs number of trees for four learning rates (sklearn GBR, depth-3 trees)."""
    from sklearn.datasets import make_friedman1
    from sklearn.ensemble import GradientBoostingRegressor
    X, y = make_friedman1(3000, noise=1.5, random_state=0)
    Xtr, ytr, Xva, yva = X[:800], y[:800], X[800:], y[800:]
    fig, ax = plt.subplots(figsize=(8.4, 6.6))
    for lr, c, n in ((1.0, CORAL, 400), (0.3, PLUM, 600), (0.1, INDIGO, 1500), (0.03, TEAL, 3000)):
        m = GradientBoostingRegressor(n_estimators=n, learning_rate=lr, max_depth=3, random_state=0).fit(Xtr, ytr)
        val = np.array([np.mean((p - yva) ** 2) for p in m.staged_predict(Xva)])
        k = np.arange(1, n + 1)
        ax.plot(k, val, color=c, lw=2.8, label=f"ν = {lr:g}")
        b = val.argmin()
        ax.plot(k[b], val[b], "o", ms=13, color=c, mec=INK, mew=1.6, zorder=5)
        print(f"  lr={lr}: best val MSE {val[b]:.3f} at {k[b]} trees")
    ax.axhline(1.5 ** 2, color=MUTED, ls=":", lw=2); ax.text(1.2, 1.5 ** 2 * 1.06, "noise floor σ² = 2.25", color=MUTED, fontsize=16)
    ax.set_xscale("log"); ax.set_ylim(1.8, 9); ax.set_xlim(1, 3500)
    ax.set_xlabel("number of trees"); ax.set_ylabel("validation MSE")
    ax.legend(loc="upper right", title="learning rate", title_fontsize=16)
    fig.tight_layout(); save(fig, "d1-shrinkage.png")


def ece(p, y, bins=10):
    idx = np.clip((p * bins).astype(int), 0, bins - 1)
    return sum(abs(p[idx == b].mean() - y[idx == b].mean()) * (idx == b).mean() for b in range(bins) if (idx == b).any())


def temperature():
    """An over-fit model is over-confident; one temperature fitted on validation data fixes it.
    Model: barely-regularized logistic regression with 100 features and only 400 training rows."""
    from scipy.optimize import minimize_scalar
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegression
    X, y = make_classification(10400, 100, n_informative=10, n_redundant=0, flip_y=0.05, class_sep=0.8, random_state=4)
    tr, va, te = slice(0, 400), slice(400, 5400), slice(5400, None)
    z = LogisticRegression(C=1e4, max_iter=5000).fit(X[tr], y[tr]).decision_function(X)   # logits
    nll = lambda T: np.mean(np.logaddexp(0, -(2 * y[va] - 1) * z[va] / T))
    T = minimize_scalar(nll, bounds=(0.05, 50), method="bounded").x
    p_raw, p_T = 1 / (1 + np.exp(-z[te])), 1 / (1 + np.exp(-z[te] / T))
    acc_raw, acc_T = np.mean((p_raw > 0.5) == y[te]), np.mean((p_T > 0.5) == y[te])
    assert acc_raw == acc_T
    fig, ax = plt.subplots(figsize=(8.4, 6.8))
    ax.plot([0, 1], [0, 1], "--", color="#9a8f78", lw=2, label="perfectly calibrated")
    edges = np.linspace(0, 1, 11)
    for p, c, name in ((p_raw, CORAL, "over-fit model"), (p_T, TEAL, f"temperature T = {T:.1f}")):
        idx = np.clip(np.digitize(p, edges) - 1, 0, 9)
        mp = np.array([p[idx == b].mean() for b in range(10) if (idx == b).sum() > 20])
        fr = np.array([y[te][idx == b].mean() for b in range(10) if (idx == b).sum() > 20])
        ax.plot(mp, fr, "-o", color=c, lw=3.2, ms=10, label=f"{name}  ·  ECE {ece(p, y[te]):.3f}")
    ax.fill_between([0, 0.5], [0, 0.5], [0.5, 0.5], color=CORAL, alpha=0.07, lw=0)
    ax.fill_between([0.5, 1], [0.5, 0.5], [0.5, 1], color=CORAL, alpha=0.07, lw=0)
    ax.text(0.97, 0.19, "shaded = over-confident", ha="right", va="bottom", color=CORAL, fontsize=17, fontweight="bold")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
    ax.set_xlabel("predicted probability"); ax.set_ylabel("observed frequency")
    ax.legend(loc="upper left", fontsize=15.5)
    ax.text(0.97, 0.03, f"accuracy {acc_raw:.1%} → {acc_T:.1%}\n(unchanged)", transform=ax.transAxes, ha="right", fontsize=16, color=INK)
    fig.tight_layout(); save(fig, "d1-temperature.png")
    print(f"  T={T:.2f} ECE raw {ece(p_raw, y[te]):.3f} -> {ece(p_T, y[te]):.3f}")


def coverage():
    """Distribution of split-conformal coverage over random calibration sets vs the Beta law."""
    from scipy.stats import beta as Beta
    from sklearn.ensemble import GradientBoostingRegressor
    alpha = 0.1
    f = lambda x: 2 * np.sin(x) + 0.3 * x
    x = rng.uniform(0, 10, 1000); y = f(x) + rng.normal(0, 0.5 + 0.1 * x)
    mu = GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=0).fit(x[:, None], y)
    xt = rng.uniform(0, 10, 200_000); st = np.sort(np.abs(f(xt) + rng.normal(0, 0.5 + 0.1 * xt) - mu.predict(xt[:, None])))
    fig, ax = plt.subplots(figsize=(8.4, 6.6))
    grid = np.linspace(0.6, 1.0, 800)
    for n, c in ((20, PLUM), (500, HONEY_DEEP)):
        k = int(np.ceil((n + 1) * (1 - alpha)))
        covs = []
        for _ in range(5000):
            xc = rng.uniform(0, 10, n); sc = np.abs(f(xc) + rng.normal(0, 0.5 + 0.1 * xc) - mu.predict(xc[:, None]))
            q = np.sort(sc)[k - 1]                                     # the k-th smallest score
            covs.append(np.searchsorted(st, q, side="right") / len(st))
        covs = np.array(covs)
        ax.hist(covs, bins=np.linspace(0.6, 1, 81), density=True, color=c, alpha=0.35, edgecolor="none")
        ax.plot(grid, Beta(k, n + 1 - k).pdf(grid), color=c, lw=3, label=f"n = {n}: mean {covs.mean():.3f}  (theory {k / (n + 1):.3f})")
        print(f"  n={n}: mean coverage {covs.mean():.4f}, theory {k/(n+1):.4f}, P(cov<0.85)={np.mean(covs<0.85):.3f}")
    ax.axvline(1 - alpha, color=CORAL, lw=2.4, ls="--"); ax.text(0.895, ax.get_ylim()[1] * 0.97, "target 1 − α = 0.9  ", color=CORAL, ha="right", va="top", fontsize=17)
    ax.set_xlim(0.62, 1.0); ax.set_yticks([])
    ax.set_xlabel("test coverage of one calibrated interval"); ax.set_ylabel("density (5,000 calibration draws)")
    ax.legend(loc="upper left", fontsize=15, title="histogram = simulation · line = Beta(k, n+1−k)", title_fontsize=14.5)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.25)
    fig.tight_layout(); save(fig, "d1-coverage.png")


def mondrian():
    """Marginal coverage hides a minority group; Mondrian (group-wise) conformal fixes it."""
    from sklearn.ensemble import GradientBoostingRegressor
    alpha = 0.1

    def draw(n):
        g = (rng.uniform(size=n) < 0.15).astype(int)
        x = rng.uniform(0, 10, n)
        y = 2 * np.sin(x) + g + rng.normal(0, np.where(g, 2.0, 0.5))
        return np.c_[x, g], y, g

    Xtr, ytr, _ = draw(3000)
    mu = GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=0).fit(Xtr, ytr)
    res = {"marginal": {"all": [], 0: [], 1: []}, "mondrian": {"all": [], 0: [], 1: []}}
    wid = {"marginal": {0: [], 1: []}, "mondrian": {0: [], 1: []}}
    qtl = lambda s: np.quantile(s, min(1, np.ceil((len(s) + 1) * (1 - alpha)) / len(s)), method="higher")
    for _ in range(300):
        Xc, yc, gc = draw(1000); Xt, yt, gt = draw(4000)
        sc, st = np.abs(yc - mu.predict(Xc)), np.abs(yt - mu.predict(Xt))
        qm = qtl(sc)
        qg = {k: qtl(sc[gc == k]) for k in (0, 1)}
        for name, qt in (("marginal", np.full(len(st), qm)), ("mondrian", np.where(gt == 1, qg[1], qg[0]))):
            ok = st <= qt
            res[name]["all"].append(ok.mean())
            for k in (0, 1):
                res[name][k].append(ok[gt == k].mean()); wid[name][k].append(2 * qt[gt == k].mean())
    fig, ax = plt.subplots(figsize=(8.4, 6.6))
    cats = ["everyone", "group A\n(85%, quiet)", "group B\n(15%, noisy)"]
    xs = np.arange(3)
    for j, (name, c, lab) in enumerate((("marginal", HONEY, "split conformal"), ("mondrian", TEAL, "Mondrian (per group)"))):
        vals = [np.mean(res[name][k]) for k in ("all", 0, 1)]
        bars = ax.bar(xs + (j - 0.5) * 0.38, vals, 0.36, color=c, edgecolor=INK, lw=1.4, label=lab)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.0%}", ha="center", va="bottom", fontsize=17, fontweight="bold", color=INK)
        print(f"  {name}: cov all/A/B = {vals}, width A/B = {np.mean(wid[name][0]):.2f}/{np.mean(wid[name][1]):.2f}")
    ax.axhline(1 - alpha, color=CORAL, ls="--", lw=2.4); ax.text(1.56, 0.89, "target\n90%", color=CORAL, ha="center", va="top", fontsize=16, fontweight="bold")
    ax.set_xticks(xs, cats); ax.set_ylim(0.4, 1.08); ax.set_ylabel("empirical coverage (300 runs)")
    ax.set_yticks([0.4, 0.6, 0.8, 1.0], ["40%", "60%", "80%", "100%"])
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=2, fontsize=16); ax.grid(axis="x", visible=False); ax.set_axisbelow(True)
    fig.tight_layout(); save(fig, "d1-mondrian.png")


def shap_waterfall():
    """Exact Shapley values (all 64 coalitions) for one patient; they sum to f(x) - E[f]."""
    X, y, m = diabetes_model()
    bg = X[rng.choice(len(X), 120, replace=False)]
    preds = m.predict(X)
    i = int(np.argsort(preds)[int(0.93 * len(preds))])
    phi, base, fx = exact_shapley(m.predict, X[i:i + 1], bg)
    phi, base, fx = phi[0], base[0], fx[0]
    assert abs(phi.sum() - (fx - base)) < 1e-6
    order = np.argsort(np.abs(phi))
    fig, ax = plt.subplots(figsize=(8.6, 6.6))
    cum = base + np.r_[0, np.cumsum(phi[order])]
    for r, j in enumerate(order):
        start, v = cum[r], phi[j]
        c = CORAL if v > 0 else TEAL
        ax.barh(r, v, left=start, color=c, edgecolor=INK, lw=1.2, height=0.62)
        ax.text(start + v + (1.5 if v > 0 else -1.5), r, f"{v:+.1f}", va="center", ha="left" if v > 0 else "right", fontsize=17, fontweight="bold", color=INK)
        if r < len(order) - 1:
            ax.plot([start + v] * 2, [r + 0.31, r + 0.69], color=MUTED, lw=1.2)
    val = lambda j: f"{X[i, j]:.0f}" if DIAB[j] in ("age", "bp", "s3", "s6") else f"{X[i, j]:.1f}"
    ax.set_yticks(range(len(order)), [f"{DIAB_LABEL[DIAB[j]]} = {val(j)}" for j in order])
    ax.axvline(base, color=MUTED, ls=":", lw=2); ax.axvline(fx, color=INK, ls="-", lw=2)
    ax.text(base + 2, -0.95, f"E[f(X)] = {base:.0f}  (average patient)", ha="left", color=MUTED, fontsize=16)
    ax.text(fx - 3, len(order) - 0.3, f"f(x) = {fx:.0f}  (this patient)", ha="right", color=INK, fontsize=17, fontweight="bold")
    ax.set_ylim(-1.3, len(order) + 0.1)
    lo, hi = min(cum.min(), base) - 22, max(cum.max(), fx) + 22
    ax.set_xlim(lo, hi); ax.set_xlabel("predicted disease progression (one year)")
    ax.grid(axis="y", visible=False); ax.set_axisbelow(True)
    fig.tight_layout(); save(fig, "d1-shap-waterfall.png")
    print(f"  patient {i}: base {base:.1f}, f(x) {fx:.1f}, sum phi {phi.sum():.2f}")


def shap_correlated():
    """Duplicate a feature and SHAP splits its credit, differently for every random seed."""
    from sklearn.ensemble import GradientBoostingRegressor
    n = 3000
    x1, x2 = rng.normal(size=n), rng.normal(size=n)
    x1c = x1 + rng.normal(0, 0.05, n)
    y = 2 * x1 + x2 + rng.normal(0, 0.3, n)
    Xe = np.c_[x1, x1c, x2][:400]; bg = np.c_[x1, x1c, x2][400:500]
    rows = []
    m = GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=0).fit(np.c_[x1, x2], y)
    phi, _, _ = exact_shapley(m.predict, Xe[:, [0, 2]], bg[:, [0, 2]])
    a = np.abs(phi).mean(0); rows.append(("x₁ only", a[0], 0.0, a[1]))
    for s in range(5):
        m = GradientBoostingRegressor(n_estimators=200, max_depth=3, max_features=2, subsample=0.8, random_state=s).fit(np.c_[x1, x1c, x2], y)
        phi, _, _ = exact_shapley(m.predict, Xe, bg)
        a = np.abs(phi).mean(0); rows.append((f"+ copy · seed {s}", a[0], a[1], a[2]))
    fig, ax = plt.subplots(figsize=(8.6, 6.6))
    for r, (lab, a1, a1c, a2) in enumerate(rows[::-1]):
        ax.barh(r, a1, color=HONEY, edgecolor=INK, lw=1.2, height=0.64, label="x₁" if r == 0 else None)
        ax.barh(r, a1c, left=a1, color=CORAL, edgecolor=INK, lw=1.2, height=0.64, label="x₁ copy (ρ ≈ 0.999)" if r == 0 else None)
        ax.barh(r, a2, left=a1 + a1c, color=TEAL, edgecolor=INK, lw=1.2, height=0.64, label="x₂" if r == 0 else None)
        if a1c > 0:
            ax.text(a1 / 2, r, f"{a1 / (a1 + a1c):.0%}", ha="center", va="center", fontsize=15, fontweight="bold", color=INK)
            ax.text(a1 + a1c / 2, r, f"{a1c / (a1 + a1c):.0%}", ha="center", va="center", fontsize=15, fontweight="bold", color=INK)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows[::-1]])
    ax.set_xlabel("mean |SHAP value| (exact)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3, fontsize=16, handlelength=1.2, columnspacing=1.2)
    ax.grid(axis="y", visible=False); ax.set_axisbelow(True)
    fig.tight_layout(); save(fig, "d1-shap-corr.png")


if __name__ == "__main__":
    jobs = [art_refits, art_boosting, art_conformal, art_shap, double_descent_ridge, shrinkage,
            temperature, coverage, mondrian, shap_waterfall, shap_correlated]
    only = sys.argv[1:]
    for k, fn in enumerate(jobs):
        if not only or fn.__name__ in only:
            rng = np.random.default_rng(2026 + k)      # each figure is reproducible on its own
            fn()
