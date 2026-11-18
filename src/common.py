"""Shared helpers: config loading, numerics, seeded RNG."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict:
    path = Path(path) if path else REPO_ROOT / "configs" / "protocol.yaml"
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def eval_seeds(cfg: dict) -> list[int]:
    s = cfg["seeds"]
    return list(range(s["eval_start"], s["eval_start"] + s["n_eval"]))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def logit(p, eps: float = 1e-6):
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))


def rng_for(seed: int, stream: str) -> np.random.Generator:
    """Independent, reproducible RNG per (seed, stream-name)."""
    tag = sum((i + 1) * ord(c) for i, c in enumerate(stream))
    return np.random.default_rng([seed, tag])


def uniform_range(rng: np.random.Generator, lo_hi) -> float:
    lo, hi = lo_hi
    return float(rng.uniform(lo, hi))
