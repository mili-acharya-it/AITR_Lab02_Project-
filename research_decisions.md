# Research decisions log

Literature-to-experiment decisions for *"Does evidence-aware trust calibration help? A simulation study of adaptive trust cues for autonomous research agents"*.

Evidence labels used throughout: **VERIFIED** (checked against the original source or actual execution), **INFERRED** (plausible, needs testing or checking), **UNKNOWN** (missing evidence).

> **Student action:** entries marked `[STUDENT]` need your own judgement or confirmation before submission. The AI assistant drafted this log; you must be able to defend every decision in the viva.

---

## 1. Source review

Acharya, M. (2026). *Human Trust Calibration in Human-Agent Collaboration for Autonomous Research* (literature review, 18 pp., 20 references). It is the evidence base for this study. Its text is not reused here.

## 2. Gap matrix (Prompt 02)

| # | Gap (review section) | Origin | Candidate question | Testable computationally? |
|---|---|---|---|---|
| G1 | Trust modelled at agent/task level; research agents differ by stage (§8.2, Table 4 "Evidence-aware calibration") | Review's own inference; motivated by [Okamura & Yamada 2020a,b] using situation-level reliability | Does a per-claim, evidence-aware cue reduce mis-calibration and decision cost compared with agent-level or situation-level cues? | **Yes**: simulation with a known ground-truth P(correct) |
| G2 | Limited longitudinal evaluation (§8.1) | Review inference; de Visser et al. 2020 (theory) | Do cues recover calibration after a reliability change? | Partly: non-stationary simulation (used as analysis A4) |
| G3 | Under-trust and excessive verification are overlooked (§8.5, Table 4) | Review inference | Does an over-trust-only cue (Okamura & Yamada) cause needless verification? | **Yes**: reliance decomposition |
| G4 | Human-state integration (§8.3) | Lin et al. 2022 | Does a workload signal improve calibration? | Weak: needs real physiological data. **Rejected** (no data access) |
| G5 | No autonomous-research benchmarks (§8.4) | Review inference | Build a benchmark | Out of scope for 4 weeks. **Rejected** |

**Selected:** G1 as primary, with G2 and G3 as pre-specified deeper analyses. Reason: it is the review's central claim (Eqs. 4 and 7: "Agent Reliability ≠ Evidence Quality"), it is testable without human participants, and it has a published, re-implementable baseline. `[STUDENT]`: confirm this ranking matches your own reading of your review.

## 3. Literature-to-experiment bridge (Prompt 03)

| Original paper | Status | What we take | Baseline in this study |
|---|---|---|---|
| Okamura & Yamada (2020a), PLOS ONE 15(2) e0229132 | **VERIFIED**: method, protocol and results read from the open-access paper (journals.plos.org) | Detection rule: over-trust iff user chose Auto while P_man > P_auto; TCC fires iff the current *and* ≥1 of the previous 2 checkpoints are flagged. Protocol: 30 checkpoints, auto 0.9 → 0.5 after checkpoint 6 | **Part 1 reproduction** and **B2 Adaptive TCC** |
| Okamura & Yamada (2020b), IEEE Access 8:220335–220351 | **VERIFIED** (bibliographic record and abstract only) | Adaptive TCCs beat a traditional transparency approach | Motivates B1 vs B2 |
| Chen et al. (2018) SAT; Akash et al. (2020) | Carried over from the review, **INFERRED** (not re-read) | Transparency = showing the agent's reliability | **B1 Reliability display** (a simplification; not a full SAT implementation) |
| Pynadath et al. (2019) | Carried over, **INFERRED** | Trust as a history-dependent process | Motivates the experience-based trust update in the simulated user (B0) |
| Mehrotra et al. (2024), ACM JRC 1(4):26 | **VERIFIED** (bibliographic record) | Warranted/appropriate trust terminology | Metric definitions |
| Wischnewski et al. (2023), CHI '23 art. 755 | **VERIFIED** (bibliographic record) | Need for behavioural calibration measures | Behavioural metrics (reliance, not self-report) |

## 4. Decisions

| ID | Decision | Reason | Evidence | Status |
|---|---|---|---|---|
| D-01 | Remain in the review's area; narrow to G1 | Assignment continuity rule; G1 is the review's main proposal | Review §8.2, §9, §13 | Done |
| D-02 | **Pathway A** (reproduction + extension), with a controlled comparison inside the extension | A verified published mechanism exists that can be re-implemented | Okamura & Yamada 2020a | Done |
| D-03 | Use **simulated users**, not human participants | No ethics approval and no time for a user study in 4 weeks; a simulation gives known ground truth (T_warranted), which human studies lack | Assignment §7 allows a "justified equivalent design" | Done. **Main threat to validity**, reported in the paper |
| D-04 | Reproduce the *mechanism*, not the human numbers | Simulated users cannot reproduce human effect sizes; only qualitative directions (R1, R2) are compared | Paper §4.1 | Done |
| D-05 | Primary metric = expected decision cost (c = 1 per verification, L = 5 per accepted wrong claim) | Single, decision-relevant quantity that penalises both over- and under-reliance; τ* = 0.8 | Review Eq. 2 & 5 used as secondary metrics | Frozen in `configs/protocol.yaml` |
| D-06 | Common random numbers: every condition sees the same claims, user and draws per seed; paired Wilcoxon + Holm | Removes between-condition noise; fair comparison | `tests/test_validation.py::test_determinism_and_crn` | Done |
| D-07 | **Protocol frozen** (configs/protocol.yaml v1.0) before any evaluation-seed run; dev seeds 1000–1004 used only for debugging | Prevent tuning on test results | SHA-256 in `results/logs/protocol_sha256.txt` | Done |
| D-08 | Pre-run edit: added `reproduction.n_seeds: 10` to the config | The number of reproduction seeds was unspecified; set before the eval run | This log | Done (logged change) |
| D-09 | Post-dev, pre-eval edit: added the `stage_only` ablation to the sweep analyses (A1–A4) | Without it, A2 (uninformative evidence) cannot tell whether gains come from the evidence term | Dev run output | Done (logged change; no eval results had been viewed) |
| D-10 | B2 = TCC **without** a reliability display | Isolates the adaptive-cue mechanism. The original study also showed a reliability indicator, so B1 and B2 bracket it | Okamura & Yamada 2020a | `[STUDENT]` accept or rerun with B1+B2 combined |
| D-11 | Over-trust detection only in B2 (under-trust off) | Faithful to the original: under-trust was defined but not tested there | Okamura & Yamada 2020a | Done |
| D-12 | Report the R2 reproduction discrepancy (accuracy *does* differ in simulation) rather than tune it away | Integrity; the cause is explainable (no time-pressure model) | `results/reproduction/tests.csv` | Reported in the paper §5.1 |
| D-13 | Figure 6 label moved | Label overlapped the curves (visual check) | Rendered figure | Done |
| D-14 | Wall-clock runtime moved from `summary.csv` to `runtime.csv`; gzip written with a fixed timestamp | A clean rerun showed 2 of 39 result files were not byte-identical (timing column, gzip header); the contents were identical | Fresh-copy rerun + SHA-256 comparison | Done: all 39 files now byte-identical |

## 5. Evidence ledger for key claims in the paper

| Claim | Label | Source |
|---|---|---|
| The evidence-aware cue lowers decision cost vs B0/B1/B2 (−10.8% / −9.6% / −5.9%) | **VERIFIED** (execution) | `results/main/summary.csv`, `comparisons.csv` |
| It does **not** reduce accepted errors vs B2 (p = 0.18) | **VERIFIED** (execution) | `results/main/comparisons.csv` |
| The gain disappears when evidence is uninformative (vs stage-only, p = 0.56) | **VERIFIED** (execution) | `results/analysis/A2_uninformative_tests.csv` |
| No advantage over B2 at low compliance (0.1; p = 0.40) | **VERIFIED** (execution) | `results/analysis/A3_compliance_tests.csv` |
| Results transfer to real users | **UNKNOWN** | Requires a user study |
| The stage reliabilities (0.92/0.85/0.75/0.60) are realistic for LLM research agents | **INFERRED** | Illustrative assumption, not measured |
| The logistic form of P(correct \| stage, evidence) is realistic | **INFERRED**. Also favours the proposed estimator, which uses the same form | Threat to validity, paper §6 |

## 6. Next actions `[STUDENT]`

1. Re-read the papers marked INFERRED in §3 and update this table.
2. Decide on D-10.
3. Optional high-value follow-ups (ranked by information gained per unit cost): (i) a misspecified generator, where the estimator's form ≠ the true form; (ii) B1 + B2 combined; (iii) a small pilot with 5–10 real participants on the same claim stream.
