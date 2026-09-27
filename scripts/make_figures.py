#!/usr/bin/env python3
"""README figures. The numbers are the per-seed values in the RESULTS / REPLICATIONS files named beside each
row (pasted run output); nothing here is estimated.  python scripts/make_figures.py"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
S1, S2 = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.axisbelow": True})

# (label, gains per seed, baseline acc per seed, companion acc per seed, source)
RUNS = [
    ("C001 synthetic\nQwen 1.5B CPU", [13.90, 13.89, 13.90], [0.8, 0.6, 0.9], [0.8, 0.8, 0.8],
     "experiments/C001_context_economy/RESULTS.md"),
    ("C001 synthetic\nQwen 1.5B Adreno", [13.90, 13.89, 13.90], [0.8, 0.6, 0.8], [0.8, 0.9, 0.8],
     "experiments/C001_context_economy/REPLICATIONS.md (R-ADRENO)"),
    ("C001 synthetic\nPhi-3-mini CPU", [13.57, 13.57, 13.55], [0.3, 0.6, 0.0], [0.5, 0.6, 0.5],
     "experiments/C001_context_economy/REPLICATIONS.md (R-PHI)"),
    ("C001 synthetic\nGemma 4 31B (NVIDIA)", [13.50], [0.9], [0.9], "experiments/C004_model_sweep/RESULTS.md"),
    ("C002 real logcat\nQwen 1.5B CPU", [2.67, 2.75, 2.86], [0.625, 0.375, 0.625], [0.875, 0.625, 0.75],
     "experiments/C002_real_log/RESULTS.md"),
]


def header(fig, t, sub):
    fig.text(0.02, 0.97, t, color=INK, fontsize=12, fontweight="bold", va="top")
    fig.text(0.02, 0.89, sub, color=INK2, fontsize=9, va="top")


def gains():
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(RUNS))
    means = [np.mean(r[1]) for r in RUNS]
    ax.bar(x, means, 0.55, color=[S1] * 4 + [S2])
    for i, r in enumerate(RUNS):
        ax.scatter([i] * len(r[1]), r[1], s=18, color=INK, zorder=3)
        ax.text(i, means[i] + 0.5, f"{means[i]:.2f}×", ha="center", color=INK2, fontsize=9)
    ax.set_xticks(x, [r[0] for r in RUNS], fontsize=8)
    ax.set_ylabel("large-model tokens: baseline ÷ companion")
    ax.set_ylim(0, 16)
    ax.grid(axis="x", visible=False)
    header(fig, "Token saving: large on a log built to repeat itself, modest on a real one",
           "Bars are means; dots are seeds. On real logcat the saving comes from deterministic lookups, not deduplication.")
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    fig.savefig(os.path.join(ROOT, "figures", "token_gain.png"), dpi=160)
    plt.close(fig)


def accuracy():
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(RUNS))
    b = [np.mean(r[2]) for r in RUNS]
    c = [np.mean(r[3]) for r in RUNS]
    ax.bar(x - 0.19, b, 0.36, color=S2, label="model alone")
    ax.bar(x + 0.19, c, 0.36, color=S1, label="with companion")
    for i in range(len(RUNS)):
        ax.text(x[i] - 0.19, b[i] + 0.02, f"{b[i]:.2f}", ha="center", color=INK2, fontsize=8)
        ax.text(x[i] + 0.19, c[i] + 0.02, f"{c[i]:.2f}", ha="center", color=INK2, fontsize=8)
    ax.set_xticks(x, [r[0] for r in RUNS], fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("answer accuracy (mean over seeds)")
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    ax.grid(axis="x", visible=False)
    header(fig, "Accuracy: never lower on average, higher where the model misreads the log",
           "The companion answers plain lookups from the log itself; it hands everything else to the model.")
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    fig.savefig(os.path.join(ROOT, "figures", "accuracy.png"), dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "figures"), exist_ok=True)
    gains()
    accuracy()
    print("wrote figures/token_gain.png, figures/accuracy.png")
