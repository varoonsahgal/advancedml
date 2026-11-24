"""Figures for the Day 5 slide deck (LLMs, reasoning & agents).

Run:  python scripts/slides/figs_day5.py [name ...]
Writes docs/assets/img/slides/d5-*.png. Every panel is computed from the code
below; toy/synthetic setups are labelled as such on the slides.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from make_figures import HONEY, INK, CORAL, TEAL, INDIGO, PLUM, PAPER, CARD, NIGHT, honey_cmap, duo_cmap, plt, np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "docs" / "assets" / "img" / "slides"
OUT.mkdir(parents=True, exist_ok=True)
MUTED = "#7A6E5A"
CREAM = "#F6EFD9"
div_cmap = LinearSegmentedColormap.from_list("div", [TEAL, "#9fd9d1", CARD, "#ffc2ba", CORAL])

# big type: split-slide figures are shown ~0.6x, so 18–22 pt lands at ~24–30 px on the slide
plt.rcParams.update({"font.size": 19, "axes.titlesize": 21, "axes.labelsize": 20,
                     "xtick.labelsize": 17, "ytick.labelsize": 17, "legend.fontsize": 17})


def save(fig, name, dpi=160, night=False, tight=True):
    kw = dict(bbox_inches="tight", pad_inches=0.25) if tight else {}
    fig.savefig(OUT / name, dpi=dpi, facecolor=fig.get_facecolor() if night else CARD, **kw)
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- LoRA: ΔW = BA and the parameter bill
def lora():
    rng = np.random.default_rng(3)
    d, r = 40, 4
    B = rng.normal(0, 1, (d, r))
    A = rng.normal(0, 1, (r, d))
    dW = B @ A
    assert np.linalg.matrix_rank(dW) == r
    fig = plt.figure(figsize=(8, 6.6))
    u = 2.55 / 8          # ΔW side as a fraction of fig width
    ux = u / d            # one cell, in fig-width units
    uy = ux * 8 / 6.6     # same cell in fig-height units
    top = 0.94
    sq_h = d * uy
    lim = np.abs(dW).max()

    def mat(x0, y0, M, title, sub, vmax):
        ax = fig.add_axes([x0, y0, M.shape[1] * ux, M.shape[0] * uy])
        ax.imshow(M, cmap=div_cmap, vmin=-vmax, vmax=vmax, interpolation="nearest", aspect="auto")
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(True); s.set_color(INK); s.set_linewidth(1.6)
        return ax

    y_sq = top - sq_h
    xB = 0.05
    mat(xB, y_sq, B, "", "", 2.5)
    fig.text(xB + r * ux / 2, y_sq - 0.05, "B", ha="center", fontsize=26, weight="bold", color=INK)
    fig.text(xB + r * ux / 2, y_sq - 0.10, "d×r", ha="center", fontsize=17, color=MUTED)
    xA = xB + r * ux + 0.06
    yA = y_sq + sq_h / 2 - r * uy / 2
    fig.text(xA - 0.03, y_sq + sq_h / 2, "·", ha="center", va="center", fontsize=40, color=INK)
    mat(xA, yA, A, "", "", 2.5)
    fig.text(xA + d * ux / 2, yA - 0.06, "A", ha="center", fontsize=26, weight="bold", color=INK)
    fig.text(xA + d * ux / 2, yA - 0.11, "r×k", ha="center", fontsize=17, color=MUTED)
    xW = xA + d * ux + 0.07
    fig.text(xW - 0.035, y_sq + sq_h / 2, "=", ha="center", va="center", fontsize=36, color=INK)
    mat(xW, y_sq, dW, "", "", lim * 0.8)
    fig.text(xW + d * ux / 2, y_sq - 0.05, "ΔW = BA", ha="center", fontsize=26, weight="bold", color=INK)
    fig.text(xW + d * ux / 2, y_sq - 0.10, f"d×k, rank {r}", ha="center", fontsize=17, color=MUTED)

    # parameter bill for one 4096×4096 projection
    ax = fig.add_axes([0.30, 0.06, 0.62, 0.30])
    n = 4096
    rows = [("full fine-tune", n * n, INK)] + [(f"LoRA r={k}", k * (n + n), c) for k, c in [(64, PLUM), (16, INDIGO), (8, TEAL)]]
    ys = np.arange(len(rows))[::-1]
    for y, (lab, v, c) in zip(ys, rows):
        ax.barh(y, v, color=c, height=0.62)
        pct = "" if v == n * n else f"  ({100 * v / (n * n):.2g}%)"
        txt = f"{v / 1e6:.1f}M" if v >= 1e6 else f"{v / 1e3:.0f}k"
        ax.text(v * 1.25, y, txt + pct, va="center", fontsize=17, color=INK)
    ax.set_xscale("log"); ax.set_xlim(1e4, 4e8)
    ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows], fontsize=17)
    ax.set_xlabel("trainable params, one 4096×4096 matrix", fontsize=16)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="x", labelsize=14)
    save(fig, "d5-lora.png", tight=True)


# ---------------------------------------------------------------- DPO: loss and gradient weight vs implicit-reward margin
def dpo():
    m = np.linspace(-6, 6, 600)
    loss = np.log1p(np.exp(-m))          # −log σ(m)
    w = 1 / (1 + np.exp(m))              # σ(−m) = −dL/dm
    fig, ax = plt.subplots(figsize=(8, 6.5))
    ax.axvspan(-6, 0, color=CORAL, alpha=0.08, lw=0)
    ax.axvspan(0, 6, color=TEAL, alpha=0.08, lw=0)
    ax.plot(m, loss, color=HONEY, lw=5, label="loss  −log σ(margin)")
    ax.plot(m, w, color=TEAL, lw=4, ls="--", label="gradient weight  σ(−margin)")
    ax.scatter([0], [np.log(2)], s=140, color=INK, zorder=5)
    ax.annotate("step 0: π = π_ref\nmargin 0, loss = log 2", (0, np.log(2)), (0.6, 2.6),
                fontsize=17, color=INK, arrowprops=dict(arrowstyle="->", color=INK, lw=1.6))
    ax.text(-5.7, 5.55, "prefers the loser:\nbig push", fontsize=17, color="#A3302A", va="top")
    ax.text(5.7, 5.55, "already right:\ngentle push", fontsize=17, color="#0E5F59", va="top", ha="right")
    ax.set_xlim(-6, 6); ax.set_ylim(-0.1, 5.8)
    ax.set_xlabel("implicit reward margin  β·[log-ratio(y_w) − log-ratio(y_l)]", fontsize=17)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=1, fontsize=17)
    fig.tight_layout()
    save(fig, "d5-dpo.png")


# ---------------------------------------------------------------- GRPO: one group's advantages + when the signal vanishes
def grpo():
    r = np.array([1, 0, 0, 1, 1, 0, 0, 0], float)
    A = (r - r.mean()) / (r.std() + 1e-6)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 7.2), gridspec_kw=dict(height_ratios=[1, 1.05], hspace=0.55))
    cols = [TEAL if v > 0 else CORAL for v in A]
    a1.bar(np.arange(8), A, color=cols, edgecolor=INK, lw=1.2, width=0.72)
    a1.axhline(0, color=INK, lw=1.5)
    for i, (v, rr) in enumerate(zip(A, r)):
        a1.text(i, v + (0.1 if v > 0 else -0.1), f"{v:+.2f}", ha="center", va="bottom" if v > 0 else "top", fontsize=15, color=INK)
        a1.text(i, -1.55, "✓" if rr else "✗", ha="center", fontsize=20, color=TEAL if rr else CORAL, weight="bold")
    a1.set_xticks(range(8)); a1.set_xticklabels([f"o{i + 1}" for i in range(8)])
    a1.set_ylim(-1.75, 1.75); a1.set_ylabel("advantage Â")
    a1.set_title("one prompt, G = 8 answers, 3 correct", loc="left", fontsize=19)
    a1.grid(axis="x", visible=False)
    p = np.linspace(0, 1, 400)
    for G, c in [(4, CORAL), (8, HONEY), (16, TEAL)]:
        a2.plot(p, 100 * (p ** G + (1 - p) ** G), color=c, lw=4, label=f"G = {G}")
    a2.set_xlabel("prompt pass rate p")
    a2.set_ylabel("% groups with\nzero signal", fontsize=18)
    a2.set_title("all-right or all-wrong groups teach nothing", loc="left", fontsize=19)
    a2.set_xlim(0, 1); a2.set_ylim(0, 102)
    a2.legend(loc="upper center", ncol=3, fontsize=16, bbox_to_anchor=(0.5, 0.98))
    save(fig, "d5-grpo-signal.png")


# ---------------------------------------------------------------- test-time compute: pass@k vs majority@k (Monte Carlo)
def passk():
    rng = np.random.default_rng(11)
    P, W = 400, 8
    p = rng.beta(1.1, 1.3, P)                                # per-problem single-sample accuracy
    wrong = rng.dirichlet(np.full(W, 0.5), P)               # how wrong answers are spread
    probs = np.c_[p, (1 - p)[:, None] * wrong]
    ks = 2 ** np.arange(0, 9)
    pass_k = [np.mean(1 - (1 - p) ** k) for k in ks]
    T = 300
    maj = []
    for k in ks:
        acc = 0.0
        for i in range(P):
            c = rng.multinomial(k, probs[i], size=T)
            top = c.max(1, keepdims=True)
            ties = (c == top)
            acc += np.mean(ties[:, 0] / ties.sum(1))         # random tie-break
        maj.append(acc / P)
    ceiling = np.mean(probs[:, 0] > probs[:, 1:].max(1))     # majority@∞: correct answer is the plurality
    fig, ax = plt.subplots(figsize=(16, 8.2))
    ax.plot(ks, pass_k, "-o", color=TEAL, lw=5, ms=13, label="pass@k: any of k is right (perfect verifier)")
    ax.plot(ks, maj, "-o", color=HONEY, lw=5, ms=13, label="majority@k: vote over k samples (self-consistency)")
    ax.axhline(ceiling, color=HONEY, ls=":", lw=3)
    ax.text(256, ceiling - 0.055, f"voting limit (k → ∞): {ceiling:.0%}",
            fontsize=19, color="#8a5f00", ha="right")
    ax.axhline(pass_k[0], color=MUTED, ls="--", lw=2)
    ax.text(1.08, pass_k[0] - 0.04, f"one sample: {pass_k[0]:.0%}", ha="left", fontsize=19, color=MUTED)
    ax.set_xscale("log", base=2)
    ax.set_xticks(ks); ax.set_xticklabels([str(k) for k in ks])
    ax.set_ylim(0.25, 1.0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("samples per problem k (inference compute, log scale)", fontsize=22)
    ax.set_ylabel("problems solved", fontsize=22)
    ax.tick_params(labelsize=20)
    ax.legend(loc="lower right", fontsize=21)
    fig.tight_layout()
    save(fig, "d5-passk.png", dpi=130)
    print(f"   pass@1={pass_k[0]:.3f} pass@256={pass_k[-1]:.3f} maj@256={maj[-1]:.3f} ceiling={ceiling:.3f}")


# ---------------------------------------------------------------- RAG: an embedding neighbourhood (LSA on a tiny corpus)
DOCS = {
    "LoRA": [
        "LoRA freezes the pretrained weights and trains a low-rank update BA",
        "the rank r of the LoRA adapter controls how many trainable parameters it adds",
        "LoRA adds r times d_in plus d_out trainable parameters per adapted matrix",
        "merge the LoRA update into the frozen weights for zero inference latency",
        "QLoRA trains LoRA adapters on a frozen 4-bit quantized base model",
        "choose which linear layers LoRA adapts: attention projections or all layers",
        "LoRA alpha over r scales the low-rank update",
        "full fine-tuning updates every parameter and needs optimizer state for each",
    ],
    "bees": [
        "a strong hive can produce twenty five kilograms of honey in a season",
        "worker bees build hexagonal wax cells to store honey and pollen",
        "the queen bee lays eggs while workers forage for nectar",
        "beekeepers check the hive frames for brood and honey stores",
        "bees perform a waggle dance to tell the hive where flowers are",
        "harvest honey when the cells are capped with wax",
        "smoke calms the bees before you open the hive",
        "pollen and nectar from spring flowers feed the growing colony",
    ],
    "agents": [
        "an agent calls tools in a loop until the task is done",
        "MCP servers expose tools resources and prompts to any client",
        "the model emits a tool call and your code executes the tool",
        "tool results go back into the context as observations",
        "prompt injection hides instructions inside retrieved documents",
        "an MCP client connects the host application to a tool server",
        "give agents least privilege tools and confirm side effects",
        "trace every tool call the agent makes so you can debug it",
    ],
    "diffusion": [
        "diffusion models learn to remove noise step by step",
        "flow matching regresses a velocity field from noise to data",
        "classifier free guidance trades diversity for prompt adherence",
        "the forward process adds Gaussian noise to images",
        "sampling integrates the learned ODE from noise to an image",
        "a diffusion transformer denoises latent image patches",
        "fewer sampling steps make image generation faster",
        "the noise schedule controls how fast signal is destroyed",
    ],
}
TOPIC_COL = {"LoRA": PLUM, "bees": HONEY, "agents": TEAL, "diffusion": INDIGO}


def lsa_corpus(dim=16):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    texts, topics = [], []
    for t, ds in DOCS.items():
        texts += ds; topics += [t] * len(ds)
    vec = TfidfVectorizer(stop_words="english", sublinear_tf=True).fit(texts)
    X = vec.transform(texts)
    svd = TruncatedSVD(dim, random_state=0).fit(X)
    E = svd.transform(X)
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    return vec, svd, E, texts, np.array(topics)


def rag():
    vec, svd, E, texts, topics = lsa_corpus()
    q = "how many trainable parameters does LoRA add"
    qe = svd.transform(vec.transform([q]))[0]
    qe /= np.linalg.norm(qe)
    sims = E @ qe
    top = np.argsort(-sims)[:3]
    print("   top-3:", [(texts[i], round(float(sims[i]), 2)) for i in top])
    from sklearn.manifold import MDS
    Eq = np.vstack([E, qe])
    Dm = np.clip(1 - Eq @ Eq.T, 0, None)
    Zall = MDS(2, dissimilarity="precomputed", random_state=0, n_init=8, normalized_stress="auto").fit_transform(Dm)
    Z, zq = Zall[:-1], Zall[-1]
    fig, ax = plt.subplots(figsize=(8, 6.5))
    for i in top:
        ax.plot([zq[0], Z[i, 0]], [zq[1], Z[i, 1]], color=INK, lw=2.2, zorder=1)
    for t, c in TOPIC_COL.items():
        m = topics == t
        ax.scatter(Z[m, 0], Z[m, 1], s=230, color=c, edgecolor=INK, lw=1.2, label=t, zorder=2)
    ax.scatter(Z[top, 0], Z[top, 1], s=520, facecolor="none", edgecolor=CORAL, lw=3.5, zorder=3)
    ax.scatter([zq[0]], [zq[1]], marker="*", s=1100, color=CORAL, edgecolor=INK, lw=1.5, zorder=4)
    ax.annotate("query", zq, (zq[0] + 0.03, zq[1] + 0.16), fontsize=19, color=INK, weight="bold")
    ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=4, fontsize=17, handletextpad=0.1, columnspacing=0.9, markerscale=0.8)
    ax.set_xlabel("2-D map (MDS) of cosine distances, 16-D LSA embeddings", fontsize=16, color=MUTED)
    fig.tight_layout()
    save(fig, "d5-rag.png")


# ---------------------------------------------------------------- SAE on synthetic superposition data (+ steering)
FEATS = ["bee", "honey", "Paris", "French", "Python", "bug", "DNA", "legal", "sarcasm", "sports",
         "math", "music", "weather", "food", "code", "deception", "Rome", "German", "poetry", "money",
         "space", "medicine", "chess", "love", "war", "cats", "rain", "trains", "dance", "gold", "ice", "fire"]


def sae_setup():
    import torch
    torch.manual_seed(0)
    rng = np.random.default_rng(0)
    n, d, L = len(FEATS), 12, 64
    D = rng.normal(size=(n, d)); D /= np.linalg.norm(D, axis=1, keepdims=True)    # true feature directions
    N = 40000
    act = (rng.random((N, n)) < 0.04) * rng.uniform(0.5, 1.5, (N, n))
    X = act @ D
    Xt = torch.tensor(X, dtype=torch.float32)
    We = torch.nn.Parameter(torch.randn(L, d) * 0.3)
    be = torch.nn.Parameter(torch.zeros(L))
    Wd = torch.nn.Parameter(We.detach().T.clone())
    bd = torch.nn.Parameter(torch.zeros(d))
    opt = torch.optim.Adam([We, be, Wd, bd], lr=3e-3)
    lam = 0.6
    for step in range(10000):
        idx = torch.randint(0, N, (512,))
        x = Xt[idx]
        f = torch.relu((x - bd) @ We.T + be)
        xh = f @ Wd.T + bd
        loss = ((x - xh) ** 2).sum(1).mean() + lam * (f.abs() * Wd.norm(dim=0)).sum(1).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        f = torch.relu((Xt - bd) @ We.T + be)
        xh = f @ Wd.T + bd
        fvu = float(((Xt - xh) ** 2).sum() / ((Xt - Xt.mean(0)) ** 2).sum())
        l0 = float((f > 1e-3).float().sum(1).mean())
        dec = (Wd / Wd.norm(dim=0)).T.numpy()                                       # L × d unit decoder dirs
    cos = dec @ D.T                                                                 # L × n
    match = cos.argmax(1)
    best = cos.max(0)                                                               # per true feature
    print(f"   SAE: FVU={fvu:.3f} L0={l0:.2f} (true L0={act.astype(bool).sum(1).mean():.2f}) "
          f"features recovered (cos>0.9): {(best > 0.9).sum()}/{n}")
    enc = lambda x: np.maximum((x - bd.detach().numpy()) @ We.detach().numpy().T + be.detach().numpy(), 0)
    return dict(D=D, X=X, act=act, f=f.numpy(), dec=dec, cos=cos, match=match, best=best, fvu=fvu, l0=l0, enc=enc)


_SAE = {}


def get_sae():
    if not _SAE:
        _SAE.update(sae_setup())
    return _SAE


def sae():
    S = get_sae()
    rng = np.random.default_rng(5)
    rows = rng.choice(np.where(S["act"].astype(bool).sum(1) >= 1)[0], 16, replace=False)
    X, F = S["X"][rows], S["f"][rows]
    alive = np.where(S["f"].max(0) > 1e-3)[0]
    order = alive[np.argsort(S["match"][alive], kind="stable")]
    F = F[:, order]
    fig = plt.figure(figsize=(8, 6.5))
    a1 = fig.add_axes([0.06, 0.12, 0.17, 0.74])
    a2 = fig.add_axes([0.30, 0.12, 0.66, 0.74])
    lim = np.abs(X).max()
    a1.imshow(X, cmap=div_cmap, vmin=-lim, vmax=lim, aspect="auto", interpolation="nearest")
    a2.imshow(F, cmap=LinearSegmentedColormap.from_list("w", [CARD, HONEY, "#8a5f00"]), vmin=0,
              vmax=np.percentile(F[F > 0], 95), aspect="auto", interpolation="nearest")
    for a, t, s in [(a1, "x", "12 dims, all busy"), (a2, "SAE latents f", f"{len(alive)} latents, ~{S['l0']:.1f} active per token")]:
        a.set_xticks([]); a.set_yticks([]); a.grid(False)
        for sp in a.spines.values():
            sp.set_visible(True); sp.set_color(INK); sp.set_linewidth(1.4)
        a.set_title(t, fontsize=21, loc="left")
        a.set_xlabel(s, fontsize=16, color=MUTED)
    a1.set_ylabel("16 tokens", fontsize=18)
    save(fig, "d5-sae.png")


def steer():
    S = get_sae()
    D, dec, enc = S["D"], S["dec"], S["enc"]
    names = np.array(FEATS)
    x0 = 1.0 * D[FEATS.index("Paris")] + 0.8 * D[FEATS.index("French")]
    j = int(np.argmax(S["cos"][:, FEATS.index("bee")]))                    # SAE latent that matches "bee"
    v = dec[j]
    readout = lambda x: np.exp(4 * D @ x) / np.exp(4 * D @ x).sum()        # toy unembedding over the 32 concepts
    alphas = np.linspace(0, 3, 61)
    track = ["Paris", "French", "bee"]
    probs = np.array([readout(x0 + a * v) for a in alphas])
    lat = np.array([enc((x0 + a * v)[None])[0, j] for a in alphas])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 7), gridspec_kw=dict(height_ratios=[1.6, 1], hspace=0.12), sharex=True)
    cols = {"Paris": INDIGO, "French": TEAL, "bee": HONEY, "honey": CORAL}
    for t in track:
        a1.plot(alphas, probs[:, FEATS.index(t)], lw=4.5, color=cols[t], label=f"“{t}”")
    a1.set_ylabel("readout prob.")
    a1.legend(loc="upper left", ncol=3, fontsize=17, handlelength=1.2, columnspacing=1.0)
    a1.set_ylim(0, 1)
    a2.plot(alphas, lat, lw=4.5, color=INK)
    a2.set_ylabel("“bee” latent")
    a2.set_xlabel("steering strength α   (x ← x + α·d_bee)")
    print(f"   steer: cos(d_bee, true bee)={S['cos'][j, FEATS.index('bee')]:.3f}; "
          f"P(bee) {probs[0, 0]:.3f} → {probs[-1, 0]:.3f}; top at α=0: {names[np.argmax(probs[0])]}")
    save(fig, "d5-steer.png")


# ---------------------------------------------------------------- night art
ART_BG = "#241E15"   # a shade lighter than the slide's night, so the hexagon crop reads


def art_axes(w=8.66, h=10):
    fig = plt.figure(figsize=(w, h), facecolor=ART_BG)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=ART_BG)
    ax.set_axis_off()
    return fig, ax


def art_grpo():
    """Real toy GRPO: tabular softmax policies on 8-way multiple choice, binary verifiable reward."""
    fig, ax = art_axes()
    rng = np.random.default_rng(2)
    P, K, G, steps = 48, 8, 8, 160
    curves = []
    for run in range(36):
        lr = rng.uniform(0.15, 0.6)
        prior = rng.normal(0, rng.uniform(0.6, 1.4), (P, K))
        theta = prior.copy()
        correct = rng.integers(0, K, P)
        theta[np.arange(P), correct] -= rng.uniform(0.5, 1.5)   # start below chance on some prompts
        ref = theta.copy()
        hist = []
        for s in range(steps):
            pi = np.exp(theta - theta.max(1, keepdims=True)); pi /= pi.sum(1, keepdims=True)
            hist.append(pi[np.arange(P), correct].mean())
            for i in range(P):
                o = rng.choice(K, G, p=pi[i])
                rwd = (o == correct[i]).astype(float)
                if rwd.std() == 0:
                    continue
                A = (rwd - rwd.mean()) / rwd.std()
                g = np.zeros(K)
                for a, adv in zip(o, A):
                    g += adv * (np.eye(K)[a] - pi[i])
                theta[i] += lr * (g / G - 0.02 * (theta[i] - ref[i]))
        curves.append(hist)
    t = np.arange(steps)
    for yv in np.linspace(0, 1, 6):
        ax.axhline(yv, color="#3a2f1c", lw=1.2, zorder=0)
    for c in curves:
        y = np.array(c)
        for lw, al in [(9, 0.04), (4, 0.08), (1.6, 0.55)]:
            ax.plot(t, y, color=HONEY, lw=lw, alpha=al, solid_capstyle="round")
    mean = np.mean(curves, 0)
    for lw, al in [(16, 0.08), (8, 0.25), (3.5, 1)]:
        ax.plot(t, mean, color="#FFF8DC", lw=lw, alpha=al)
    ax.scatter(t[::8], mean[::8], s=40, color="#FFF8DC", zorder=5)
    ax.set_xlim(-8, steps + 4); ax.set_ylim(-0.08, 1.12)
    save(fig, "d5-art-grpo.png", dpi=120, night=True, tight=False)


def art_sim():
    """Cosine-similarity matrix of the RAG corpus (LSA), sorted by topic: retrieval's view of the world."""
    vec, svd, E, texts, topics = lsa_corpus(dim=10)
    S = E @ E.T
    S = np.kron(S, np.ones((6, 6)))
    fig, ax = art_axes()
    ax.imshow(S, cmap=honey_cmap, vmin=-0.2, vmax=1.0, interpolation="nearest", extent=(0, 1, 0, 1), aspect="auto")
    n = len(texts)
    for k in range(1, n):
        ax.axhline(k / n, color=NIGHT, lw=1.6); ax.axvline(k / n, color=NIGHT, lw=1.6)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    save(fig, "d5-art-sim.png", dpi=120, night=True, tight=False)


def art_superposition():
    """Elhage et al. toy model: 6 sparse features in 2 dims, trained -> a hexagon of directions."""
    import torch
    torch.manual_seed(0)
    n, m = 6, 2
    W = torch.nn.Parameter(torch.randn(m, n) * 0.1)
    b = torch.nn.Parameter(torch.zeros(n))
    opt = torch.optim.Adam([W, b], lr=1e-2)
    for step in range(10000):
        x = torch.rand(4096, n) * (torch.rand(4096, n) < 0.03)
        xh = torch.relu(x @ W.T @ W + b)
        loss = ((x - xh) ** 2).sum(1).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    Wn = W.detach().numpy()
    norms = np.linalg.norm(Wn, axis=0)
    print(f"   superposition: feature norms {np.round(norms, 2)}")
    fig, ax = art_axes()
    th = np.linspace(0, 2 * np.pi, 400)
    for rr in [0.4, 0.8, 1.2, 1.6]:
        ax.plot(1.25 * rr * np.cos(th), 1.25 * rr * np.sin(th), color="#3a2f1c", lw=1.2)
    cols = [HONEY, CORAL, TEAL, PLUM, "#7d8cff", "#FFE680"]
    s = 1.55 / norms.max()
    pts = []
    for i in range(n):
        vx, vy = Wn[:, i] * s
        pts.append((vx, vy))
        for lw, al in [(22, 0.05), (12, 0.12), (5, 1)]:
            ax.plot([0, vx], [0, vy], color=cols[i], lw=lw, alpha=al, solid_capstyle="round")
        ax.scatter([vx], [vy], s=520, color=cols[i], edgecolor=ART_BG, lw=3, zorder=5)
    ang = np.argsort([np.arctan2(y, x) for x, y in pts])
    poly = np.array([pts[i] for i in ang] + [pts[ang[0]]])
    ax.plot(poly[:, 0], poly[:, 1], color=CREAM, lw=1.6, alpha=0.5, ls="--")
    ax.scatter([0], [0], s=300, color=CREAM, zorder=6)
    ax.set_xlim(-2.0, 2.0); ax.set_ylim(-2.31, 2.31)
    ax.set_aspect("equal")
    save(fig, "d5-art-superposition.png", dpi=120, night=True, tight=False)


ALL = [lora, dpo, grpo, passk, rag, sae, steer, art_grpo, art_sim, art_superposition]

if __name__ == "__main__":
    only = set(sys.argv[1:])
    for fn in ALL:
        if not only or fn.__name__ in only:
            fn()
