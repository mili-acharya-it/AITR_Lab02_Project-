"""Paired statistics across seeds (common random numbers => paired design)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon


def bootstrap_ci(x: np.ndarray, n_boot: int = 5000, level: float = 0.95, seed: int = 0):
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    means = x[idx].mean(axis=1)
    lo, hi = np.quantile(means, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def holm(pvals: list[float]) -> list[float]:
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def paired_comparisons(df: pd.DataFrame, metric: str, target: str, others: list[str],
                       n_boot: int = 5000, level: float = 0.95) -> pd.DataFrame:
    """Compare `target` condition with each of `others` on `metric`, paired by seed."""
    wide = df.pivot(index="seed", columns="condition", values=metric)
    rows = []
    for o in others:
        d = (wide[target] - wide[o]).to_numpy()
        if np.allclose(d, 0):
            p = 1.0
        else:
            p = float(wilcoxon(wide[target], wide[o], zero_method="wilcox").pvalue)
        lo, hi = bootstrap_ci(d, n_boot, level)
        # matched-pairs rank-biserial effect size
        nz = d[d != 0]
        if len(nz):
            ranks = pd.Series(np.abs(nz)).rank().to_numpy()
            rbc = float((ranks[nz > 0].sum() - ranks[nz < 0].sum()) / ranks.sum())
        else:
            rbc = 0.0
        rows.append(dict(metric=metric, target=target, comparator=o,
                         mean_diff=float(d.mean()), ci_low=lo, ci_high=hi,
                         p_raw=p, rank_biserial=rbc, n_pairs=len(d)))
    out = pd.DataFrame(rows)
    out["p_holm"] = holm(out["p_raw"].tolist())
    return out
