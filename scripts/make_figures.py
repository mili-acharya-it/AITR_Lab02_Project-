"""Regenerate every figure in the paper from the saved CSVs (no simulation re-run).

Usage:  python scripts/make_figures.py
Outputs: results/figures/*.{png,pdf}  and a copy in paper/figures/
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from trustcal.common import REPO_ROOT

R = REPO_ROOT / "results"
FIG = R / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# Validated categorical palette (fixed order, never cycled); entity -> colour is fixed.
COL = {"no_cue": "#2a78d6", "reliability_display": "#eb6834", "adaptive_tcc": "#1baf7a",
       "evidence_aware": "#6250d6", "stage_only": "#eda100", "evidence_only": "#e87ba4",
       "oracle": "#52514e", "no_tcc": "#2a78d6", "tcc": "#1baf7a"}
LBL = {"no_cue": "No cue (B0)", "reliability_display": "Reliability display (B1)",
       "adaptive_tcc": "Adaptive TCC (B2)", "evidence_aware": "Evidence-aware (proposed)",
       "stage_only": "Stage-only (ablation)", "evidence_only": "Evidence-only (ablation)",
       "oracle": "Oracle (upper bound)", "no_tcc": "No TCC", "tcc": "TCC"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "savefig.dpi": 300, "savefig.bbox": "tight",
    "font.family": "DejaVu Sans"})


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}")
    plt.close(fig)


# Fig 1 - reproduction: manual-choice rate per checkpoint
pc = pd.read_csv(R / "reproduction" / "per_checkpoint.csv")
fig, ax = plt.subplots(figsize=(5.2, 2.6))
ax.axvspan(6.5, 30.5, color="#f0efec", zorder=0)
ax.text(18.5, 0.97, "storm: P(auto) = 0.5", ha="center", va="top", color=INK2, fontsize=8)
ax.text(3.5, 0.97, "P(auto) = 0.9", ha="center", va="top", color=INK2, fontsize=8)
for g in ("no_tcc", "tcc"):
    d = pc[pc.group == g]
    ax.plot(d.t, d.manual_rate, color=COL[g], lw=2, marker="o", ms=3, label=LBL[g])
    ax.annotate(LBL[g], (30, d.manual_rate.iloc[-1]), xytext=(4, 0),
                textcoords="offset points", va="center", color=INK, fontsize=8)
ax.set(xlabel="Checkpoint", ylabel="Manual-choice rate", ylim=(0, 1), xlim=(0.5, 30.5))
ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.62), fontsize=8)
save(fig, "fig1_reproduction_manual_rate")

# Fig 2 - main comparison: decision cost with 95% bootstrap CI
s = pd.read_csv(R / "main" / "summary.csv").set_index("condition")
order = ["no_cue", "reliability_display", "adaptive_tcc", "stage_only", "evidence_only",
         "evidence_aware", "oracle"]
fig, ax = plt.subplots(figsize=(5.2, 2.8))
y = np.arange(len(order))[::-1]
m = s.loc[order, "decision_cost_per_claim_mean"]
lo = m - s.loc[order, "decision_cost_per_claim_ci_low"]
hi = s.loc[order, "decision_cost_per_claim_ci_high"] - m
ax.barh(y, m, height=0.62, color=[COL[c] for c in order], edgecolor="white", linewidth=2)
ax.errorbar(m, y, xerr=[lo, hi], fmt="none", ecolor=INK, elinewidth=1, capsize=2)
for yi, v in zip(y, m):
    ax.text(v + 0.03, yi, f"{v:.3f}", va="center", fontsize=8, color=INK)
ax.set_yticks(y, [LBL[c] for c in order])
ax.set_xlabel("Decision cost per claim (lower is better), mean ± 95% CI, 50 seeds")
ax.set_xlim(0, 1.3)
ax.grid(axis="y", visible=False)
save(fig, "fig2_main_decision_cost")

# Fig 3 - over- vs under-reliance decomposition
order3 = ["no_cue", "reliability_display", "adaptive_tcc", "evidence_aware", "oracle"]
fig, axes = plt.subplots(1, 2, figsize=(5.6, 2.4), sharey=True)
for ax, met, title in ((axes[0], "accepted_error_rate", "Over-reliance\n(accepted wrong claims / N)"),
                       (axes[1], "unnecessary_verification", "Under-reliance\n(needless verifications / N)")):
    v = s.loc[order3, f"{met}_mean"]
    yy = np.arange(len(order3))[::-1]
    ax.barh(yy, v, height=0.62, color=[COL[c] for c in order3], edgecolor="white", linewidth=2)
    for yi, val in zip(yy, v):
        ax.text(val + 0.005, yi, f"{val:.3f}", va="center", fontsize=7.5, color=INK)
    ax.set_title(title, fontsize=8.5, color=INK)
    ax.set_xlim(0, max(v) * 1.35)
    ax.grid(axis="y", visible=False)
axes[0].set_yticks(np.arange(len(order3))[::-1], [LBL[c] for c in order3])
save(fig, "fig3_reliance_decomposition")

# Fig 4 - robustness to evidence noise, Fig 5 - compliance sensitivity
for fname, file, xlabel in (
        ("fig4_noise_robustness", "A1_noise_sweep.csv", "Evidence-signal noise SD"),
        ("fig5_compliance_sensitivity", "A3_compliance_sweep.csv", "Mean cue compliance")):
    d = pd.read_csv(R / "analysis" / file)
    g = d.groupby(["value", "condition"]).decision_cost_per_claim.agg(["mean", "sem"]).reset_index()
    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    for c in ["no_cue", "reliability_display", "adaptive_tcc", "stage_only", "evidence_aware"]:
        gg = g[g.condition == c]
        ax.errorbar(gg.value, gg["mean"], yerr=1.96 * gg["sem"], color=COL[c], lw=2,
                    marker="o", ms=4, capsize=2, label=LBL[c])
    ax.set(xlabel=xlabel, ylabel="Decision cost per claim")
    ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.0, 0.5))
    save(fig, fname)

# Fig 6 - drift: rolling cost
dc = pd.read_csv(R / "analysis" / "A4_drift_curve.csv")
fig, ax = plt.subplots(figsize=(5.2, 2.6))
for c in ["no_cue", "reliability_display", "adaptive_tcc", "evidence_aware"]:
    d = dc[dc.condition == c].sort_values("claim")
    ax.plot(d.claim, d.cost.rolling(30, min_periods=30).mean(), color=COL[c], lw=2, label=LBL[c])
ax.axvline(150, color=INK2, lw=1, ls="--")
ax.text(153, 0.82, "reliability drop\n(summarisation, synthesis)",
        fontsize=7.5, color=INK2, va="bottom")
ax.set(xlabel="Claim index", ylabel="Decision cost\n(30-claim rolling mean)", ylim=(0.8, 1.35))
ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.0, 0.5))
save(fig, "fig6_drift")

# Fig 7 - failure analysis by stage
fs = pd.read_csv(R / "analysis" / "A5_failures_by_stage.csv")
stages = ["retrieval", "extraction", "summarisation", "synthesis"]
conds = ["no_cue", "adaptive_tcc", "evidence_aware"]
fig, ax = plt.subplots(figsize=(5.2, 2.5))
w = 0.26
for j, c in enumerate(conds):
    v = fs[fs.condition == c].set_index("stage").loc[stages, "accepted_error_rate"]
    ax.bar(np.arange(4) + (j - 1) * w, v, width=w - 0.02, color=COL[c], label=LBL[c])
ax.set_xticks(np.arange(4), stages)
ax.set_ylabel("Accepted-error rate")
ax.legend(fontsize=7)
ax.grid(axis="x", visible=False)
save(fig, "fig7_failures_by_stage")

dst = REPO_ROOT / "paper" / "figures"
dst.mkdir(parents=True, exist_ok=True)
for f in FIG.glob("*.pdf"):
    shutil.copy(f, dst / f.name)
print("figures written:", sorted(p.name for p in FIG.glob("*.png")))

