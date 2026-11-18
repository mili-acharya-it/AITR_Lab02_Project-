# Five-minute demonstration script (submission item E)

| Time | Show | Say |
|---|---|---|
| 0:00–0:45 | `docs/research_brief.md` | The gap from my review (§8.2): trust is calibrated per agent, but a research agent's reliability depends on the stage and the evidence behind each claim. RQs 1–3. |
| 0:45–1:45 | `src/trustcal/tcc.py` + `pytest -q tests/test_validation.py -k tcc` | The Okamura & Yamada rule, re-implemented from the paper: flag over-trust when Auto is chosen while manual would be better; fire only if one of the previous two checkpoints was also flagged. The test reproduces a hand-worked sequence. |
| 1:45–2:30 | `results/figures/fig1_reproduction_manual_rate.png` | Reproduction: the TCC raises manual choices after the storm (R1 reproduced). Accuracy also differs here, unlike the paper (R2 discrepancy), because I don't model time pressure. |
| 2:30–3:30 | `src/trustcal/research.py` (`generate_session`, `run_condition`) | Ground truth T_w = σ(logit r_stage + β(q − 0.5)). Four conditions share identical claims, users and random draws, so the comparison is paired. |
| 3:30–4:20 | `fig2`, `fig3`, `paper/tables/comparisons.tex` | Cost −10.8% vs no cue, −5.9% vs TCC. vs TCC the gain is **fewer needless verifications**, not fewer accepted errors (p = 0.18). |
| 4:20–5:00 | `fig5`, `paper/tables/analyses.tex` | When it fails: no gain when evidence is uninformative or users ignore cues (compliance 0.1). Main limitation: simulated users. |

**Live-rerun option for the viva:** `python scripts/run_main.py --dev` (about 1 s), then point to a row of `results/dev/summary.csv`.

**Likely viva questions to prepare `[STUDENT]`:** Why simulation and not a user study? Why L/c = 5? Why might the logistic estimator be unfairly advantaged? What does common random numbers buy you? Why Wilcoxon and not a t-test? What does the oracle tell you?
