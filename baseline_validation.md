# Baseline validation report (Gate G2, Prompt 10)

Baselines validated: **B2, Okamura & Yamada (2020a) adaptive TCC** (re-implemented), plus the components every condition shares (claim generator, estimators, experience-based trust user, statistics).
Official code: none located. **UNKNOWN** whether any exists. The implementation follows the paper's text (verified at journals.plos.org, DOI 10.1371/journal.pone.0229132).

Commands: `python -m pytest -q` (12 passed, see `results/logs/tests.log`) and `python scripts/run_reproduction.py` (`results/reproduction/`).

## 1. Implementation audit against the original method

| Element | Original (paper) | This implementation | Verdict |
|---|---|---|---|
| Trust signal | Inferred from choice behaviour: Auto ⇒ trust exceeds self-confidence | User picks Auto with P = σ(k·(T − P_man)) | VERIFIED: consistent with the paper's choice-based definition |
| Over-trust flag | Auto chosen while P_man > P_auto | `is_over_trust()` in `src/trustcal/tcc.py` | VERIFIED (unit test V1) |
| Firing rule | Current flagged AND ≥1 of the previous 2 flagged | `TCCDetector(window=3)` | VERIFIED (unit test V1, hand-worked 7-step sequence) |
| Under-trust | Defined, not tested | Implemented, **off** by default | VERIFIED (faithful) |
| Protocol | 30 checkpoints; auto 90% → 50% after checkpoint 6 | Same (`configs/protocol.yaml`) | VERIFIED |
| P_man estimate | System estimates the user's manual success | Running mean of manual outcomes, prior 0.75 (weight 4) | UNCERTAIN: the paper's exact estimator was not extracted; ours is a reasonable stand-in |
| TCC modality | Visual / audio / verbal / anthropomorphic, shown 2 s | Abstract: compliance probability ∈ U(0.4, 0.8) to reverse Auto → Manual, plus a trust drop of 0.05 | Acceptable adaptation: modality differences cannot be simulated. **Not** a claim about any specific cue type |
| Participants | 116 humans | 2,000 simulated users per group (10 seeds × 200) | Acceptable adaptation (D-03, D-04): only qualitative directions are compared |
| Time pressure | 22 checkpoints in 8.5 min | Not modelled | **NEEDS CORRECTION / reported**: likely cause of the R2 discrepancy below |

## 2. Unit and sanity checks (all executed, all pass)

| ID | Check | Result |
|---|---|---|
| V1 | TCC fires exactly at t = 2 and t = 7 in a hand-worked sequence; never fires without Auto | PASS |
| V2 | Claim generator is calibrated: expected calibration error < 0.01 over 200k claims (see the notebook for the per-bin table; max bin gap ≈ 0.011) | PASS |
| V3 | Per-stage Beta estimator converges (±0.02); L2-logistic recovers the evidence effect β = 4 (±0.25) | PASS |
| V4 | B0 experience-based trust converges to true reliability (0.7 ± 0.03) under full feedback | PASS |
| V5 | Determinism: same seed ⇒ identical claims and metrics; common random numbers across conditions | PASS |
| V6 | Oracle has zero calibration error and bounds every condition | PASS |
| V7 | Holm correction reproduces a textbook example | PASS |

## 3. Qualitative reproduction of the published findings (RQ1)

Source: `results/reproduction/summary.csv`, `tests.csv` (paired Wilcoxon, n = 2,000 simulated users).

| Published finding | Simulation | Verdict |
|---|---|---|
| R1: TCC groups increased manual choices in bad weather | TCC − no-TCC manual rate in storm: **+0.443** (0.779 vs 0.335), p < 0.001 | **Reproduced (direction)** |
| R1: the no-TCC group "did not change" | No-TCC manual rate rose 0.174 → 0.335 (+0.161, p < 0.001) | **Partial discrepancy**: simulated users still learn from observed failures (learning rate 0.02–0.08, 50% outcome visibility). Humans in the original may have had less outcome feedback or more inertia |
| R2: accuracy did not differ significantly (TCC groups numerically higher) | TCC − no-TCC accuracy in storm: **+0.106**, p < 0.001 | **Discrepancy**: same direction as the paper's numerical trend, but significant here. Likely causes: (i) no time-pressure or manual-speed cost in the simulation; (ii) n = 2,000 vs ~23 per group gives far more power |

**Conclusion.** The re-implemented mechanism behaves as the paper describes: it fires only after sustained over-trust, and only once reliability drops (zero TCCs in good weather). It reproduces the main qualitative effect (R1). The R2 discrepancy is explained and reported, not tuned away. B2 is therefore accepted as the adaptive-calibration baseline for Part 2, with the caveat that our "TCC" is an abstract cue with a fixed compliance probability.

## 4. Discrepancies that do / do not invalidate the comparison

* **Do not invalidate:** cue modality, participant count, P_man estimator. These affect the size of the effect, not the comparison logic, and every Part 2 condition shares the same user model.
* **Could bias the comparison:** in Part 2 the evidence-aware estimator uses the same logistic form as the data generator. This favours the proposed method; it is mitigated in part by A1 (noise) and A2 (uninformative evidence) and listed as a threat to validity. A misspecified-generator test is recommended follow-up.

## 5. Further checks required `[STUDENT]`

- [ ] Re-read §2 ("Method") of Okamura & Yamada 2020a and confirm how P_man was estimated; update §1 if it differs.
- [ ] Check whether the authors released code or data (search the paper's Data Availability statement).
- [ ] Re-run `bash scripts/run_all.sh` on your own machine and confirm the CSVs are byte-identical (`git status results/`).
