"""Baseline validation and sanity tests (see baseline_validation.md, checks V1-V7)."""
import copy

import numpy as np
import pytest

from trustcal.common import load_config, sigmoid
from trustcal.research import (L2Logistic, StageBeta, generate_session, metrics,
                               run_condition)
from trustcal.stats import holm
from trustcal.tcc import TCCDetector

CFG = load_config()


# V1 - TCC firing rule matches the paper's description ----------------------------
def test_tcc_requires_current_and_one_of_previous_two():
    det = TCCDetector(window=3)
    # (chose_auto, p_man, p_auto): over-trust iff auto and p_man > p_auto
    seq = [(True, .8, .5), (True, .8, .5), (False, .8, .5), (False, .8, .5),
           (True, .8, .5), (True, .8, .9), (True, .8, .5)]
    fired = [det.step(*s) for s in seq]
    #  t1: flagged, no history -> no;  t2: flagged & t1 flagged -> yes
    #  t3,t4: not flagged -> no;  t5: flagged, prev two not flagged -> no
    #  t6: not flagged (p_auto > p_man) -> no;  t7: flagged & t5 flagged -> yes
    assert fired == [False, True, False, False, False, False, True]


def test_tcc_never_fires_without_auto_choice():
    det = TCCDetector(window=3)
    assert not any(det.step(False, 0.9, 0.1) for _ in range(10))


# V2 - claim generator is calibrated: empirical correctness matches T_warranted ----
def test_generator_calibration():
    cfg = copy.deepcopy(CFG)
    cfg["research"]["n_claims"] = 200_000
    s = generate_session(cfg, seed=1000)
    bins = np.linspace(0, 1, 11)
    idx = np.digitize(s.p_true, bins) - 1
    ece = 0.0
    for b in range(10):
        m = idx == b
        if m.sum() > 200:
            ece += m.mean() * abs(s.y[m].mean() - s.p_true[m].mean())
    assert ece < 0.01


# V3 - estimators recover the generating parameters with enough data --------------
def test_stage_beta_converges():
    rng = np.random.default_rng(1001)
    est = StageBeta(2, prior=(8, 2))
    for _ in range(20_000):
        s = int(rng.integers(0, 2))
        est.update(s, int(rng.uniform() < (0.9 if s == 0 else 0.5)))
    assert abs(est.mean(0) - 0.9) < 0.02 and abs(est.mean(1) - 0.5) < 0.02


def test_logistic_recovers_evidence_effect():
    rng = np.random.default_rng(1002)
    q = rng.uniform(size=20_000)
    X = np.c_[np.ones_like(q), q - 0.5]
    y = (rng.uniform(size=q.size) < sigmoid(0.5 + 4.0 * (q - 0.5))).astype(float)
    m = L2Logistic(np.array([0.0, 0.0]), l2=1.0)
    m.fit(X, y)
    assert abs(m.w[0] - 0.5) < 0.1 and abs(m.w[1] - 4.0) < 0.25


# V4 - experience-based trust (baseline B0) converges to reliability --------------
def test_user_trust_converges_under_full_feedback():
    cfg = copy.deepcopy(CFG)
    rc = cfg["research"]
    rc["n_claims"] = 4000
    rc["stage_reliability"] = [0.7, 0.7, 0.7, 0.7]
    rc["evidence_effect_beta"] = 0.0
    rc["user"]["p_observe_accepted_outcome"] = 1.0
    rc["user"]["learning_rate"] = [0.02, 0.02]
    s = generate_session(cfg, seed=1003)
    rec = run_condition(s, cfg, "no_cue")
    assert abs(rec["t_eff"][-500:].mean() - 0.7) < 0.03


# V5 - determinism and common random numbers --------------------------------------
def test_determinism_and_crn():
    a = generate_session(CFG, seed=1004)
    b = generate_session(CFG, seed=1004)
    assert np.array_equal(a.y, b.y) and np.array_equal(a.q_obs, b.q_obs)
    r1 = metrics(a, run_condition(a, CFG, "evidence_aware"), CFG)
    r2 = metrics(b, run_condition(b, CFG, "evidence_aware"), CFG)
    assert r1 == r2


# V6 - oracle is an upper bound on calibration error ------------------------------
@pytest.mark.parametrize("cond", ["no_cue", "reliability_display", "adaptive_tcc",
                                  "evidence_aware"])
def test_oracle_has_zero_calibration_error_and_bounds_others(cond):
    s = generate_session(CFG, seed=1000)
    o = metrics(s, run_condition(s, CFG, "oracle"), CFG)
    m = metrics(s, run_condition(s, CFG, cond), CFG)
    assert o["calibration_error"] < 1e-12
    assert o["calibration_error"] <= m["calibration_error"]


# V7 - statistics helper ------------------------------------------------------------
def test_holm_known_values():
    # classic example: p = [0.01, 0.04, 0.03] -> [0.03, 0.06, 0.06]
    assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])

