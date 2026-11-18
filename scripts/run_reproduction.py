"""Part 1: computational reproduction of the Okamura & Yamada (2020) TCC mechanism.

Usage:  python scripts/run_reproduction.py [--config configs/protocol.yaml] [--dev]
Outputs: results/reproduction/{per_checkpoint.csv, per_user.csv, summary.csv, tests.csv}
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from trustcal.common import REPO_ROOT, load_config
from trustcal.drone import run_reproduction, summarise_reproduction


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--dev", action="store_true", help="use dev seeds only (debugging)")
    args = ap.parse_args()
    cfg = load_config(args.config)
    seeds = cfg["seeds"]["dev"] if args.dev else list(range(cfg["reproduction"]["n_seeds"]))
    out = REPO_ROOT / "results" / ("dev" if args.dev else "reproduction")
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    df = pd.concat([run_reproduction(cfg, s) for s in seeds], ignore_index=True)
    elapsed = time.time() - t0

    per_cp = (df.groupby(["group", "t", "weather"])
                .agg(manual_rate=("auto", lambda a: 1 - a.mean()),
                     accuracy=("success", "mean"), tcc_rate=("tcc", "mean"),
                     mean_trust=("trust", "mean")).reset_index())
    per_cp.to_csv(out / "per_checkpoint.csv", index=False)

    per_user = summarise_reproduction(df)
    per_user.to_csv(out / "per_user.csv", index=False)

    summary = (per_user.groupby(["group", "weather"])
               .agg(manual_rate_mean=("manual_rate", "mean"),
                    manual_rate_sd=("manual_rate", "std"),
                    accuracy_mean=("accuracy", "mean"),
                    accuracy_sd=("accuracy", "std"),
                    tcc_per_user=("tcc_count", "mean"),
                    n_users=("user", "count")).reset_index())
    summary.to_csv(out / "summary.csv", index=False)

    # paired tests (same simulated user in both groups)
    w = per_user.pivot_table(index=["seed", "user"], columns=["group", "weather"],
                             values=["manual_rate", "accuracy"])
    tests = []
    def add(name, a, b):
        d = (a - b).to_numpy()
        p = float(wilcoxon(a, b).pvalue) if not np.allclose(d, 0) else 1.0
        tests.append(dict(test=name, mean_diff=float(d.mean()), p_value=p, n=len(d)))
    add("R1a manual_rate bad: tcc - no_tcc",
        w[("manual_rate", "tcc", "bad")], w[("manual_rate", "no_tcc", "bad")])
    add("R1b manual_rate no_tcc: bad - good",
        w[("manual_rate", "no_tcc", "bad")], w[("manual_rate", "no_tcc", "good")])
    add("R1c manual_rate tcc: bad - good",
        w[("manual_rate", "tcc", "bad")], w[("manual_rate", "tcc", "good")])
    add("R2 accuracy bad: tcc - no_tcc",
        w[("accuracy", "tcc", "bad")], w[("accuracy", "no_tcc", "bad")])
    pd.DataFrame(tests).to_csv(out / "tests.csv", index=False)

    print(summary.to_string(index=False))
    print(pd.DataFrame(tests).to_string(index=False))
    print(f"seeds={seeds} users/group={cfg['reproduction']['n_users_per_group']*len(seeds)} "
          f"runtime={elapsed:.1f}s")


if __name__ == "__main__":
    main()
