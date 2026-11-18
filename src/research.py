"""Part 2 - extension: trust calibration in a simulated autonomous-research pipeline.

A research agent emits a stream of claims. Each claim comes from one pipeline
stage (retrieval, extraction, summarisation, synthesis) and carries an
evidence-quality score q in [0, 1] (e.g. how many consistent, traceable sources
support it). The probability that a claim is correct depends on both:

    T_warranted = P(correct) = sigmoid( logit(r_stage) + beta * (q - 0.5) )

which operationalises the review's distinction "Agent Reliability != Evidence
Quality" (Eq. 7) and its warranted-trust function T_w = f(R, A, E, U, C) (Eq. 4).

A simulated user decides per claim to ACCEPT or VERIFY. Verifying costs c,
accepting a wrong claim costs L, so the cost-optimal rule is
accept iff T_warranted >= tau* = 1 - c/L.

Conditions differ ONLY in what calibration support the system provides.
All conditions share the same claim stream, user parameters and random draws
(common random numbers), so differences are attributable to the condition.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .common import logit, rng_for, sigmoid, uniform_range
from .tcc import TCCDetector

CONDITIONS = ("no_cue", "reliability_display", "adaptive_tcc", "evidence_aware",
              "stage_only", "evidence_only", "oracle")


# --------------------------------------------------------------------------- session
@dataclass
class Session:
    stage: np.ndarray        # int stage index per claim
    q: np.ndarray            # true evidence quality
    q_obs: np.ndarray        # evidence signal seen by the system (noisy)
    p_true: np.ndarray       # warranted trust (true P(correct))
    y: np.ndarray            # 1 if claim correct
    u_dec: np.ndarray
    u_obs: np.ndarray
    u_comp: np.ndarray
    trust0: float
    lr: float
    compliance: float


def generate_session(cfg: dict, seed: int, *, evidence_noise_sd: float | None = None,
                     beta: float | None = None, compliance_mean: float | None = None,
                     drift: bool = False) -> Session:
    rc = cfg["research"]
    n = rc["n_claims"]
    rel = np.array(rc["stage_reliability"], dtype=float)
    beta = rc["evidence_effect_beta"] if beta is None else beta
    sd = rc["evidence_noise_sd"] if evidence_noise_sd is None else evidence_noise_sd

    rng_c = rng_for(seed, "claims")
    stage = rng_c.integers(0, len(rel), size=n)
    a, b = rc["evidence_quality_dist"]
    q = rng_c.beta(a, b, size=n)
    noise = rng_c.normal(0.0, 1.0, size=n)          # drawn once, scaled by sd
    q_obs = np.clip(q + sd * noise, 0.0, 1.0)
    u_y = rng_c.uniform(size=n)

    rel_t = np.tile(rel, (n, 1))
    if drift:
        d = rc["drift"]
        rel_t[d["after_claim"]:] = np.array(d["stage_reliability_after"], dtype=float)
    r_claim = rel_t[np.arange(n), stage]
    p_true = sigmoid(logit(r_claim) + beta * (q - 0.5))
    y = (u_y < p_true).astype(int)

    rng_u = rng_for(seed, "user")
    uc = rc["user"]
    trust0 = uniform_range(rng_u, uc["trust0"])
    lr = uniform_range(rng_u, uc["learning_rate"])
    lo, hi = uc["compliance"]
    if compliance_mean is not None:
        half = (hi - lo) / 2
        lo, hi = max(0.0, compliance_mean - half), min(1.0, compliance_mean + half)
    compliance = float(rng_u.uniform(lo, hi))

    rng_d = rng_for(seed, "draws")
    return Session(stage=stage, q=q, q_obs=q_obs, p_true=p_true, y=y,
                   u_dec=rng_d.uniform(size=n), u_obs=rng_d.uniform(size=n),
                   u_comp=rng_d.uniform(size=n),
                   trust0=trust0, lr=lr, compliance=compliance)


# --------------------------------------------------------------------------- estimators
class StageBeta:
    """Per-stage Beta-Bernoulli reliability estimate (situation-level)."""

    def __init__(self, n_stages: int, prior=(8.0, 2.0)):
        self.a = np.full(n_stages, float(prior[0]))
        self.b = np.full(n_stages, float(prior[1]))

    def update(self, s: int, y: int):
        self.a[s] += y
        self.b[s] += 1 - y

    def mean(self, s: int) -> float:
        return float(self.a[s] / (self.a[s] + self.b[s]))

    def pooled(self) -> float:
        return float(self.a.sum() / (self.a.sum() + self.b.sum()))


class PooledBeta(StageBeta):
    def __init__(self, prior=(8.0, 2.0)):
        super().__init__(1, prior)


class L2Logistic:
    """Logistic regression with Gaussian prior (L2 towards prior mean), Newton fit."""

    def __init__(self, prior_mean: np.ndarray, l2: float = 1.0):
        self.m = np.asarray(prior_mean, dtype=float)
        self.w = self.m.copy()
        self.l2 = l2

    def fit(self, X: np.ndarray, y: np.ndarray, iters: int = 25):
        w = self.w.copy()
        for _ in range(iters):
            p = sigmoid(X @ w)
            g = X.T @ (p - y) + self.l2 * (w - self.m)
            H = (X * (p * (1 - p))[:, None]).T @ X + self.l2 * np.eye(len(w))
            step = np.linalg.solve(H, g)
            w -= step
            if np.max(np.abs(step)) < 1e-8:
                break
        self.w = w

    def predict(self, x: np.ndarray) -> float:
        return float(sigmoid(x @ self.w))


def _features(kind: str, stage: int, q_obs: float, n_stages: int) -> np.ndarray:
    if kind == "full":
        x = np.zeros(n_stages + 1)
        x[stage] = 1.0
        x[-1] = q_obs - 0.5
        return x
    if kind == "evidence_only":
        return np.array([1.0, q_obs - 0.5])
    raise ValueError(kind)


# --------------------------------------------------------------------------- simulation
def run_condition(sess: Session, cfg: dict, condition: str) -> dict:
    if condition not in CONDITIONS:
        raise ValueError(condition)
    rc = cfg["research"]
    uc, sc = rc["user"], rc["system"]
    n, n_st = len(sess.y), len(rc["stage_reliability"])
    c, L = rc["cost_verify"], rc["cost_accepted_error"]
    tau = 1.0 - c / L
    k = uc["choice_sharpness"]
    alpha = 1.0 if condition == "oracle" else sess.compliance

    trust = sess.trust0
    stage_est = StageBeta(n_st, sc["beta_prior"])
    pooled_est = PooledBeta(sc["beta_prior"])
    prior_logit = float(logit(sc["beta_prior"][0] / sum(sc["beta_prior"])))
    model_kind = {"evidence_aware": "full", "evidence_only": "evidence_only"}.get(condition)
    model = None
    if model_kind == "full":
        model = L2Logistic(np.r_[np.full(n_st, prior_logit), 0.0], sc["logistic_l2"])
    elif model_kind == "evidence_only":
        model = L2Logistic(np.array([prior_logit, 0.0]), sc["logistic_l2"])
    obs_X, obs_y = [], []
    det = TCCDetector(window=cfg["reproduction"]["tcc_window"])

    rec = {k_: np.zeros(n) for k_ in ("accept", "t_eff", "cue", "cost", "tcc")}
    for i in range(n):
        s, qo, y = int(sess.stage[i]), float(sess.q_obs[i]), int(sess.y[i])

        cue = np.nan
        if condition == "reliability_display":
            cue = pooled_est.pooled()
        elif condition == "stage_only":
            cue = stage_est.mean(s)
        elif condition in ("evidence_aware", "evidence_only"):
            cue = model.predict(_features(model_kind, s, qo, n_st))
        elif condition == "oracle":
            cue = float(sess.p_true[i])

        t_eff = trust if np.isnan(cue) else (1 - alpha) * trust + alpha * cue
        accept = bool(sess.u_dec[i] < sigmoid(k * (t_eff - tau)))

        fired = False
        if condition == "adaptive_tcc":
            # mapping of the original rule: "Auto" = accept, P_man <-> tau (value of
            # verifying), P_auto <-> stage-level (situation-level) reliability estimate
            fired = det.step(accept, tau, stage_est.mean(s))
            if fired:
                trust = max(0.0, trust - uc["tcc_trust_drop"])
                if sess.u_comp[i] < alpha:
                    accept = False

        observed = (not accept) or (sess.u_obs[i] < uc["p_observe_accepted_outcome"])
        if observed:
            trust += sess.lr * (y - trust)
            stage_est.update(s, y)
            pooled_est.update(0, y)
            if model is not None:
                obs_X.append(_features(model_kind, s, qo, n_st))
                obs_y.append(y)
        if model is not None and (i + 1) % sc["refit_every"] == 0 and obs_y:
            model.fit(np.array(obs_X), np.array(obs_y, dtype=float))

        rec["accept"][i] = accept
        rec["t_eff"][i] = t_eff
        rec["cue"][i] = cue
        rec["tcc"][i] = fired
        rec["cost"][i] = (L if (accept and y == 0) else 0.0) if accept else c
    return rec


def metrics(sess: Session, rec: dict, cfg: dict) -> dict:
    rc = cfg["research"]
    tau = 1.0 - rc["cost_verify"] / rc["cost_accepted_error"]
    acc = rec["accept"].astype(bool)
    y = sess.y.astype(bool)
    opt_accept = sess.p_true >= tau
    ver = ~acc
    n_ver = int(ver.sum())
    return dict(
        decision_cost_per_claim=float(rec["cost"].mean()),
        calibration_error=float(np.mean(np.abs(rec["t_eff"] - sess.p_true))),
        appropriate_reliance=float(np.mean(acc == opt_accept)),
        accepted_error_rate=float(np.mean(acc & ~y)),
        unnecessary_verification=float(np.mean(ver & opt_accept)),
        verification_rate=float(np.mean(ver)),
        verification_efficiency=float((ver & ~y).sum() / n_ver) if n_ver else float("nan"),
        tcc_count=int(rec["tcc"].sum()),
        claim_accuracy=float(y.mean()),
    )

