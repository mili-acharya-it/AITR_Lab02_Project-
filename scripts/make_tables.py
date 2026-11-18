"""Generate LaTeX tables for the paper directly from the result CSVs.

Usage:  python scripts/make_tables.py
Outputs: paper/tables/*.tex   (numbers are never typed by hand)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from trustcal.common import REPO_ROOT

R = REPO_ROOT / "results"
T = REPO_ROOT / "paper" / "tables"
T.mkdir(parents=True, exist_ok=True)
NAME = {"no_cue": "B0 No cue", "reliability_display": "B1 Reliability display",
        "adaptive_tcc": "B2 Adaptive TCC", "evidence_aware": "\\textbf{Evidence-aware}",
        "stage_only": "Ablation: stage-only", "evidence_only": "Ablation: evidence-only",
        "oracle": "\\textit{Oracle (bound)}"}


def fmt_p(p):
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


# Table: reproduction
s = pd.read_csv(R / "reproduction" / "summary.csv")
t = pd.read_csv(R / "reproduction" / "tests.csv")
lines = ["\\begin{tabular}{llrrr}", "\\toprule",
         "Group & Weather & Manual rate & Accuracy & TCCs/user \\\\", "\\midrule"]
for _, r in s.sort_values(["group", "weather"], ascending=[True, False]).iterrows():
    g = "No TCC" if r.group == "no_tcc" else "TCC"
    lines.append(f"{g} & {r.weather} & {r.manual_rate_mean:.3f} ({r.manual_rate_sd:.3f}) & "
                 f"{r.accuracy_mean:.3f} ({r.accuracy_sd:.3f}) & {r.tcc_per_user:.2f} \\\\")
lines += ["\\midrule", "\\multicolumn{5}{l}{Paired Wilcoxon tests (n = %d simulated users)} \\\\"
          % int(t.n.iloc[0])]
for _, r in t.iterrows():
    lines.append(f"\\multicolumn{{3}}{{l}}{{{r.test.replace('_', ' ')}}} & "
                 f"$\\Delta$={r.mean_diff:+.3f} & p {fmt_p(r.p_value)} \\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
(T / "reproduction.tex").write_text("\n".join(lines))

# Table: main results
s = pd.read_csv(R / "main" / "summary.csv").set_index("condition")
order = ["no_cue", "reliability_display", "adaptive_tcc", "evidence_aware",
         "stage_only", "evidence_only", "oracle"]
mets = [("decision_cost_per_claim", "Cost$\\downarrow$"), ("calibration_error", "$E_{trust}\\downarrow$"),
        ("appropriate_reliance", "AppRel$\\uparrow$"), ("accepted_error_rate", "AccErr$\\downarrow$"),
        ("unnecessary_verification", "UnnVer$\\downarrow$"),
        ("verification_efficiency", "VE$\\uparrow$")]
lines = ["\\begin{tabular}{l" + "r" * len(mets) + "}", "\\toprule",
         "Condition & " + " & ".join(h for _, h in mets) + " \\\\", "\\midrule"]
for c in order:
    if c == "stage_only" or c == "oracle":
        lines.append("\\midrule")
    cells = [f"{s.loc[c, m + '_mean']:.3f}" for m, _ in mets]
    lines.append(f"{NAME[c]} & " + " & ".join(cells) + " \\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
(T / "main.tex").write_text("\n".join(lines))

# Table: paired comparisons for the proposed condition
cp = pd.read_csv(R / "main" / "comparisons.csv")
lines = ["\\begin{tabular}{llrrrr}", "\\toprule",
         "Metric & vs. & $\\Delta$ mean & 95\\% CI & $r_{rb}$ & $p_{Holm}$ \\\\", "\\midrule"]
short = {"decision_cost_per_claim": "Cost", "calibration_error": "$E_{trust}$",
         "appropriate_reliance": "AppRel", "accepted_error_rate": "AccErr",
         "unnecessary_verification": "UnnVer"}
for _, r in cp[cp.metric.isin(short)].iterrows():
    lines.append(f"{short[r.metric]} & {NAME[r.comparator]} & {r.mean_diff:+.4f} & "
                 f"[{r.ci_low:+.4f}, {r.ci_high:+.4f}] & {r.rank_biserial:+.2f} & "
                 f"{fmt_p(r.p_holm)} \\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
(T / "comparisons.tex").write_text("\n".join(lines))

# Table: deeper analyses summary (cost, mean over seeds)
rows = []
for file, label in (("A1_noise_sweep.csv", "Noise SD"), ("A3_compliance_sweep.csv", "Compliance")):
    d = pd.read_csv(R / "analysis" / file)
    g = d.groupby(["value", "condition"]).decision_cost_per_claim.mean().unstack()
    for v, r in g.iterrows():
        rows.append((f"{label} = {v:g}", r))
a2 = pd.read_csv(R / "analysis" / "A2_uninformative.csv").groupby("condition") \
    .decision_cost_per_claim.mean()
rows.append(("Uninformative evidence ($\\beta$=0)", a2))
a4 = pd.read_csv(R / "analysis" / "A4_drift_phases.csv")
for ph in ("pre", "post"):
    rows.append((f"Drift, {ph}-change", a4[a4.phase == ph].groupby("condition")
                 .decision_cost_per_claim.mean()))
cols = ["no_cue", "reliability_display", "adaptive_tcc", "stage_only", "evidence_aware", "oracle"]
hdr = ["B0", "B1", "B2", "Stage", "\\textbf{EA}", "Oracle"]
lines = ["\\begin{tabular}{l" + "r" * len(cols) + "}", "\\toprule",
         "Setting & " + " & ".join(hdr) + " \\\\", "\\midrule"]
for lab, r in rows:
    best = min(r[c] for c in cols if c != "oracle")
    cells = [(f"\\textbf{{{r[c]:.3f}}}" if (c != "oracle" and abs(r[c] - best) < 1e-12)
              else f"{r[c]:.3f}") for c in cols]
    lines.append(f"{lab} & " + " & ".join(cells) + " \\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
(T / "analyses.tex").write_text("\n".join(lines))
print("tables written:", sorted(p.name for p in T.glob("*.tex")))
