"""Part 1 - computational reproduction of the Okamura & Yamada (2020) protocol.

The original study used 116 human participants in an online drone simulator:
30 checkpoints, automatic inspection 90% reliable in good weather and 50% after
the sixth checkpoint (thunderstorm); no-TCC control vs four TCC groups.

We cannot reproduce *human* results.  What we reproduce is the *mechanism*:
the detection rule and the TCC, applied to a population of simulated users whose
trust is inferred from Auto/Manual choices.  We then check whether the
qualitative pattern reported in the paper appears:
  R1  TCC groups increase manual choices in bad weather; no-TCC group changes little.
  R2  Accuracy differences between groups are small.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .common import rng_for, sigmoid, uniform_range
from .tcc import TCCDetector


@dataclass
class DroneUser:
    p_man: float
    trust0: float
    lr: float
    compliance: float


def sample_users(cfg: dict, seed: int) -> list[DroneUser]:
    r = cfg["reproduction"]
    u = r["user"]
    rng = rng_for(seed, "drone-users")
    return [
        DroneUser(
            p_man=uniform_range(rng, u["p_man"]),
            trust0=uniform_range(rng, u["trust0"]),
            lr=uniform_range(rng, u["learning_rate"]),
            compliance=uniform_range(rng, u["compliance"]),
        )
        for _ in range(r["n_users_per_group"])
    ]


def run_user(user: DroneUser, cfg: dict, draws: dict, use_tcc: bool) -> dict:
    r = cfg["reproduction"]
    u = r["user"]
    n = r["n_checkpoints"]
    trust = user.trust0
    # system's running estimate of the user's manual success (prior mean 0.75, weight 4)
    man_succ, man_n = 3.0, 4.0
    det = TCCDetector(window=r["tcc_window"])
    rows = []
    for t in range(n):
        p_auto = r["p_auto_good"] if t < r["storm_after"] else r["p_auto_bad"]
        p_choose_auto = sigmoid(u["choice_sharpness"] * (trust - user.p_man))
        chose_auto = draws["choice"][t] < p_choose_auto
        p_man_est = man_succ / man_n
        fire = det.step(chose_auto, p_man_est, p_auto)
        flagged_over = chose_auto and p_man_est > p_auto
        reversed_ = False
        if use_tcc and fire:
            trust = max(0.0, trust - u["tcc_trust_drop"])
            if draws["comply"][t] < user.compliance:
                chose_auto = False
                reversed_ = True
        if chose_auto:
            success = draws["outcome"][t] < p_auto
            if draws["observe"][t] < u["p_observe_auto_outcome"]:
                trust += user.lr * (float(success) - trust)
        else:
            success = draws["outcome"][t] < user.p_man
            man_succ += float(success)
            man_n += 1.0
        rows.append(
            dict(t=t + 1, weather="good" if t < r["storm_after"] else "bad",
                 auto=int(chose_auto), success=int(success), tcc=int(use_tcc and fire),
                 flagged_over=int(flagged_over), reversed=int(reversed_), trust=trust)
        )
    return {"rows": rows}


def run_reproduction(cfg: dict, seed: int) -> pd.DataFrame:
    """Return one row per (user, group, checkpoint)."""
    users = sample_users(cfg, seed)
    n = cfg["reproduction"]["n_checkpoints"]
    out = []
    for i, user in enumerate(users):
        rng = rng_for(seed * 10_000 + i, "drone-draws")
        draws = {k: rng.uniform(size=n) for k in ("choice", "comply", "outcome", "observe")}
        for group, use in (("no_tcc", False), ("tcc", True)):
            res = run_user(user, cfg, draws, use)
            for row in res["rows"]:
                row.update(user=i, group=group, seed=seed)
                out.append(row)
    return pd.DataFrame(out)


def summarise_reproduction(df: pd.DataFrame) -> pd.DataFrame:
    per_user = (
        df.groupby(["seed", "group", "user", "weather"])
        .agg(manual_rate=("auto", lambda a: 1 - a.mean()),
             accuracy=("success", "mean"),
             tcc_count=("tcc", "sum"))
        .reset_index()
    )
    return per_user
