"""Part 2 main comparison: evidence-aware cue vs three baselines (+ ablations, oracle).

Usage:  python scripts/run_main.py [--config configs/protocol.yaml] [--dev]
Outputs: results/main/{per_seed_metrics.csv, per_claim.csv.gz, summary.csv, comparisons.csv}
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from trustcal.common import REPO_ROOT, eval_seeds, load_config
from trustcal.research import generate_session, metrics, run_condition
from trustcal.stats import bootstrap_ci, paired_comparisons

METRICS = ["decision_cost_per_claim", "calibration_error", "appropriate_reliance",
           "accepted_error_rate", "unnecessary_verification", "verification_rate",
           "verification_efficiency"]


def all_conditions(cfg):
    rc = cfg["research"]
    return rc["conditions"] + rc["ablations"] + rc["reference"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dev", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    seeds = cfg["seeds"]["dev"] if args.dev else eval_seeds(cfg)
    out = REPO_ROOT / "results" / ("dev" if args.dev else "main")
    out.mkdir(parents=True, exist_ok=True)
    stages = cfg["research"]["stages"]

    rows, claims, runtime = [], [], {}
    for seed in seeds:
        sess = generate_session(cfg, seed)
        for cond in all_conditions(cfg):
            t0 = time.perf_counter()
            rec = run_condition(sess, cfg, cond)
            runtime[cond] = runtime.get(cond, 0.0) + time.perf_counter() - t0
            rows.append(dict(seed=seed, condition=cond, **metrics(sess, rec, cfg)))
            claims.append(pd.DataFrame(dict(
                seed=seed, condition=cond, claim=np.arange(len(sess.y)),
                stage=[stages[s] for s in sess.stage], q=sess.q.round(4),
                q_obs=sess.q_obs.round(4), p_true=sess.p_true.round(4), y=sess.y,
                accept=rec["accept"].astype(int), t_eff=rec["t_eff"].round(4),
                cue=np.round(rec["cue"], 4), tcc=rec["tcc"].astype(int), cost=rec["cost"])))
    df = pd.DataFrame(rows)
    df.to_csv(out / "per_seed_metrics.csv", index=False)
    # mtime=0 makes the gzip byte-identical across runs (header otherwise stores a timestamp)
    pd.concat(claims).to_csv(out / "per_claim.csv.gz", index=False,
                             compression={"method": "gzip", "mtime": 0})

    st = cfg["statistics"]
    summ = []
    for cond, g in df.groupby("condition", sort=False):
        r = dict(condition=cond, n_seeds=len(g))
        for m in METRICS:
            x = g[m].to_numpy()
            lo, hi = bootstrap_ci(x, st["bootstrap_ci"]["n_boot"], st["bootstrap_ci"]["level"])
            r.update({f"{m}_mean": x.mean(), f"{m}_sd": x.std(ddof=1),
                      f"{m}_ci_low": lo, f"{m}_ci_high": hi})
        summ.append(r)
    pd.DataFrame(summ).to_csv(out / "summary.csv", index=False)
    # wall-clock timing is machine-dependent, so it is kept out of summary.csv (deterministic)
    pd.DataFrame([dict(condition=c, runtime_ms_per_session=1000 * t / len(seeds))
                  for c, t in runtime.items()]).to_csv(out / "runtime.csv", index=False)

    baselines = ["no_cue", "reliability_display", "adaptive_tcc"]
    comps = pd.concat([paired_comparisons(df, m, "evidence_aware", baselines,
                                          st["bootstrap_ci"]["n_boot"])
                       for m in METRICS], ignore_index=True)
    # ablation: full model vs its two components
    abl = pd.concat([paired_comparisons(df, m, "evidence_aware",
                                        ["stage_only", "evidence_only"])
                     for m in ["decision_cost_per_claim", "calibration_error"]],
                    ignore_index=True)
    comps["family"], abl["family"] = "main", "ablation"
    pd.concat([comps, abl]).to_csv(out / "comparisons.csv", index=False)

    cols = ["condition"] + [f"{m}_mean" for m in METRICS[:5]]
    print(pd.DataFrame(summ)[cols].round(4).to_string(index=False))
    print(comps[comps.metric == "decision_cost_per_claim"].round(5).to_string(index=False))
    print(abl.round(5).to_string(index=False))


if __name__ == "__main__":
    main()
