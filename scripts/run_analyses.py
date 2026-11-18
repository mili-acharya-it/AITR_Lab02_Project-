"""Deeper analyses (all pre-specified in configs/protocol.yaml):

  A1 robustness  - evidence-signal noise sweep
  A2 robustness  - uninformative evidence (beta = 0): the proposed cue's premise is false
  A3 sensitivity - user cue-compliance sweep
  A4 longitudinal / non-stationary - reliability drift mid-session
  A5 failure analysis - accepted errors broken down by stage and evidence quality
     (computed from results/main/per_claim.csv.gz; run run_main.py first)

Usage:  python scripts/run_analyses.py [--dev]
Outputs: results/analysis/*.csv
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from trustcal.common import REPO_ROOT, eval_seeds, load_config
from trustcal.research import generate_session, metrics, run_condition
from trustcal.stats import paired_comparisons

CONDS = ["no_cue", "reliability_display", "adaptive_tcc", "evidence_aware", "stage_only",
         "oracle"]
BASE = ["no_cue", "reliability_display", "adaptive_tcc", "stage_only"]


def sweep(cfg, seeds, param, values, **fixed):
    rows = []
    for v in values:
        for seed in seeds:
            sess = generate_session(cfg, seed, **{param: v}, **fixed)
            for c in CONDS:
                rows.append(dict(param=param, value=v, seed=seed, condition=c,
                                 **metrics(sess, run_condition(sess, cfg, c), cfg)))
    return pd.DataFrame(rows)


def tests_by_value(df, metric="decision_cost_per_claim"):
    out = []
    for v, g in df.groupby("value"):
        t = paired_comparisons(g, metric, "evidence_aware", BASE)
        t.insert(0, "value", v)
        out.append(t)
    return pd.concat(out, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dev", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    seeds = cfg["seeds"]["dev"] if args.dev else eval_seeds(cfg)
    out = REPO_ROOT / "results" / ("dev" if args.dev else "analysis")
    out.mkdir(parents=True, exist_ok=True)
    sw = cfg["research"]["sweeps"]

    # A1
    a1 = sweep(cfg, seeds, "evidence_noise_sd", sw["evidence_noise_sd"])
    a1.to_csv(out / "A1_noise_sweep.csv", index=False)
    tests_by_value(a1).to_csv(out / "A1_noise_tests.csv", index=False)

    # A2
    a2 = sweep(cfg, seeds, "beta", [sw["uninformative_evidence_beta"]])
    a2.to_csv(out / "A2_uninformative.csv", index=False)
    tests_by_value(a2).to_csv(out / "A2_uninformative_tests.csv", index=False)

    # A3
    a3 = sweep(cfg, seeds, "compliance_mean", sw["compliance_mean"])
    a3.to_csv(out / "A3_compliance_sweep.csv", index=False)
    tests_by_value(a3).to_csv(out / "A3_compliance_tests.csv", index=False)

    # A4 drift: metrics before/after the change point + rolling cost
    d_after = cfg["research"]["drift"]["after_claim"]
    rows, roll = [], []
    for seed in seeds:
        sess = generate_session(cfg, seed, drift=True)
        for c in CONDS:
            rec = run_condition(sess, cfg, c)
            for phase, sl in (("pre", slice(0, d_after)), ("post", slice(d_after, None))):
                sub = {k: v[sl] for k, v in rec.items()}
                s2 = type(sess)(**{f: (getattr(sess, f)[sl] if isinstance(getattr(sess, f), np.ndarray)
                                       else getattr(sess, f)) for f in sess.__dataclass_fields__})
                rows.append(dict(seed=seed, condition=f"{c}", phase=phase, **metrics(s2, sub, cfg)))
            roll.append(pd.DataFrame(dict(seed=seed, condition=c, claim=np.arange(len(sess.y)),
                                          cost=rec["cost"], t_eff=rec["t_eff"],
                                          p_true=sess.p_true)))
    a4 = pd.DataFrame(rows)
    a4.to_csv(out / "A4_drift_phases.csv", index=False)
    rc = pd.concat(roll)
    rc["abs_err"] = (rc.t_eff - rc.p_true).abs()
    rc.groupby(["condition", "claim"])[["cost", "abs_err"]].mean().reset_index() \
      .to_csv(out / "A4_drift_curve.csv", index=False)
    post = a4[a4.phase == "post"].copy()
    paired_comparisons(post, "decision_cost_per_claim", "evidence_aware", BASE) \
        .to_csv(out / "A4_drift_tests.csv", index=False)

    # A5 failure analysis from main per-claim records
    pc_path = REPO_ROOT / "results" / ("dev" if args.dev else "main") / "per_claim.csv.gz"
    if pc_path.exists():
        pc = pd.read_csv(pc_path)
        pc = pc[pc.condition.isin(CONDS)]
        pc["accepted_error"] = (pc.accept == 1) & (pc.y == 0)
        pc["unnecessary_verif"] = (pc.accept == 0) & (pc.p_true >= 0.8)
        pc["q_bin"] = pd.cut(pc.q, [0, 1/3, 2/3, 1], labels=["low", "mid", "high"],
                             include_lowest=True)
        by_stage = pc.groupby(["condition", "stage"]).agg(
            accepted_error_rate=("accepted_error", "mean"),
            unnecessary_verification=("unnecessary_verif", "mean"),
            n=("claim", "count")).reset_index()
        by_stage.to_csv(out / "A5_failures_by_stage.csv", index=False)
        by_q = pc.groupby(["condition", "q_bin"], observed=True).agg(
            accepted_error_rate=("accepted_error", "mean"),
            unnecessary_verification=("unnecessary_verif", "mean"),
            n=("claim", "count")).reset_index()
        by_q.to_csv(out / "A5_failures_by_evidence.csv", index=False)
        # residual failure mode of the proposed cue: confidently-accepted wrong claims
        ea = pc[(pc.condition == "evidence_aware") & pc.accepted_error]
        ea.groupby(["stage", "q_bin"], observed=True).size().rename("n_accepted_errors") \
          .reset_index().to_csv(out / "A5_evidence_aware_residual_errors.csv", index=False)
    else:
        print(f"[skip A5] {pc_path} missing - run scripts/run_main.py first")

    for name, d in (("A1", a1), ("A3", a3)):
        print(name, d.groupby(["value", "condition"]).decision_cost_per_claim.mean()
              .unstack().round(3).to_string(), sep="\n")
    print("A2", a2.groupby("condition").decision_cost_per_claim.mean().round(3).to_string(), sep="\n")
    print("A4", a4.groupby(["phase", "condition"]).decision_cost_per_claim.mean()
          .unstack().round(3).to_string(), sep="\n")


if __name__ == "__main__":
    main()
