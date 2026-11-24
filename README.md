# 🐝 Gradient Hive — Advanced ML Week (2026 edition)

A five-day, lab-first Advanced Machine Learning course that runs from classical ML done right to the 2026 frontier.

**Website:** https://varoonsahgal.github.io/advancedml/

| Day | Theme | Labs |
|---|---|---|
| 1 · Mon | **Classical, Sharpened**: bias–variance & double descent, gradient boosting, calibration, conformal prediction, SHAP, TabPFN | 1.1 Boosting from scratch · 1.2 Calibration & conformal · 1.3 SHAP vs TabPFN |
| 2 · Tue | **The Deep Learning Engine Room**: autodiff, init/norms/residuals, AdamW → Muon, LR schedules, grokking, scaling laws | 2.1 Autograd from scratch · 2.2 Optimizer arena · 2.3 Grokking |
| 3 · Wed | **Transformers & Beyond**: attention, RoPE/RMSNorm/SwiGLU, KV cache, sampling, speculative decoding, quantization, MoE, SSMs | 3.1 Modern GPT from scratch · 3.2 Inference engineering · 3.3 MoE & SSMs |
| 4 · Thu | **Generative Worlds**: VAE → diffusion → flow matching, CFG, latent diffusion & DiT, CLIP, VLMs | 4.1 Flow matching in 2D · 4.2 Diffusion + CFG · 4.3 CLIP |
| 5 · Fri | **LLMs, Reasoning & Agents**: LoRA, DPO, GRPO/RLVR, test-time compute, agents, RAG, MCP, evals, SAEs | 5.1 LoRA · 5.2 GRPO · 5.3 Agents + MCP · 5.4 Sparse autoencoders |

Each day page has a one-minute TL;DR, the lecture with figures and live demos, the labs, a **🍯 honey jar** of key takeaways, myth-busters, interview flashcards, a quiz and a daily challenge. There's also a printable **cheat sheet** of the whole week, a capstone guide, and a honeycomb progress tracker.

Every lab opens in Google Colab with one click and runs on a free CPU runtime (a GPU makes the generative and LLM labs faster).

## Repository layout

```
docs/                 ← the built website (GitHub Pages serves this folder)
  assets/css, js, img ← styles, interactive widgets, generated figures
site/
  pages/              ← page sources (edit these)
  labs.json           ← lab catalog that drives every lab card (+ preview captions)
  days.json           ← per-day TL;DRs, key takeaways, myths, flashcards, cheat-sheet equations
notebooks/            ← the 16 lab notebooks
scripts/
  build.py            ← static-site builder: site/ → docs/
  make_figures.py     ← regenerates every figure in docs/assets/img
requirements.txt      ← for running the notebooks locally
```

## Editing the site

```bash
python scripts/make_figures.py      # only if you change figures (needs numpy, matplotlib, scikit-learn)
python scripts/build.py             # rebuild docs/ from site/
python -m http.server -d docs 8000  # preview at http://localhost:8000
```

## Publishing with GitHub Pages

1. Push this repo to GitHub as `advancedml`.
2. **Settings → Pages → Build and deployment → Deploy from a branch → `main` / `/docs`**.
3. The site appears at `https://<user>.github.io/advancedml/`.

If you fork under a different name, change `REPO` at the top of `scripts/build.py` (it builds the Colab links) and rebuild.

## Running the notebooks locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter lab notebooks/
```

Set `LAB_FAST=1` to shrink every notebook to a quick smoke test.

On macOS, LightGBM and XGBoost need OpenMP: `brew install libomp`. Lab 1.1 skips them gracefully without it. Colab has everything preinstalled.
