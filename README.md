# Evidence-Aware Trust Calibration for Autonomous Research Agents: A Reproduction and Simulation Study

**AI Tools for Research: post-mid-semester project (Lab 02)**
Author: Mili Acharya, IIIT Allahabad
Follows from the literature review *"Human Trust Calibration in Human-Agent Collaboration for Autonomous Research"* (2026).

## Research question

Trust-calibration cues in the literature work at the level of the agent or the *situation*. A research agent, by contrast, is more reliable at some pipeline stages than others, and each claim it makes is backed by evidence of varying quality (review §8.2; "Agent Reliability ≠ Evidence Quality"). This project asks:

* **RQ1 (reproduction).** Does the adaptive trust-calibration cue (TCC) of Okamura & Yamada (2020, *PLOS ONE*) reproduce its qualitative effect in a simulated replica of its protocol?
* **RQ2 (extension).** In a simulated autonomous-research pipeline, does an **evidence-aware, per-claim** warranted-trust cue reduce decision cost and calibration error compared with no cue, an agent-level reliability display, and the adaptive TCC?
* **RQ3 (limits).** When does the advantage disappear: under noisy or uninformative evidence, low user compliance, or reliability drift?

Pathway **A: reproduction + extension** (assignment §3). All results come from simulated users, not human participants (see Limitations).

## Key results (50 paired seeds; all numbers from `results/`)

| Condition | Decision cost ↓ | Calibration error ↓ | Accepted errors ↓ | Needless verifications ↓ |
|---|---|---|---|---|
| B0 No cue | 1.120 | 0.166 | 0.117 | 0.274 |
| B1 Reliability display | 1.105 | 0.157 | 0.103 | 0.302 |
| B2 Adaptive TCC (Okamura & Yamada) | 1.062 | 0.170 | **0.077** | 0.340 |
| **Evidence-aware (proposed)** | **0.999** | **0.124** | 0.080 | **0.257** |
| Oracle (upper bound) | 0.814 | 0.000 | 0.059 | 0.106 |

* Decision cost is 10.8% lower than B0 and 5.9% lower than B2 (Holm-corrected paired Wilcoxon, p < 0.001; lower in 49/50 seeds vs B0 and 43/50 vs B2).
* Against B2 the gain comes entirely from **fewer needless verifications**. Accepted-error rates do not differ (p = 0.18).
* **Limits:** no gain over a stage-only cue when evidence carries no information (p = 0.56); no gain over B2 when users rarely follow cues (compliance 0.1, p = 0.40); the gain shrinks as the evidence signal gets noisier. The cue stays robust after a mid-session reliability drop.
* **Reproduction:** R1 reproduced (TCC +0.44 manual-choice rate in the storm phase). R2 (no accuracy difference) **not** reproduced; this is explained in `baseline_validation.md`.

## Repository layout

```
README.md                 this file
requirements.txt          pinned versions used for the reported results
pyproject.toml            package metadata + pytest config
configs/protocol.yaml     FROZEN experimental protocol (seeds, metrics, parameters)
data/README.md            data description (synthetic; no external data)
src/trustcal/             simulation library
  tcc.py                  Okamura & Yamada detection + firing rule
  drone.py                Part 1: reproduction protocol
  research.py             Part 2: research-pipeline simulation, conditions, metrics
  stats.py                paired Wilcoxon, Holm, bootstrap CI
  common.py               config, RNG, numerics
scripts/                  entry points (see below)
tests/test_validation.py  baseline validation checks V1–V7
notebooks/01_sanity_and_walkthrough.ipynb   executed walkthrough with outputs
results/                  genuine outputs: CSVs, logs, figures
  reproduction/  main/  analysis/  figures/  logs/
paper/                    LaTeX source, .bib, generated tables, figures, PDF
docs/research_brief.md    one-page brief (Gate G1)
docs/demo_walkthrough.md  5-minute demo script
research_decisions.md     literature-to-experiment decisions + evidence ledger
baseline_validation.md    reproduction checks and deviations
ai_assistance_log.md      AI provenance and verification log
```

## Setup

Tested on Linux, Python 3.13.18, CPU only (2 cores). See `results/logs/environment.txt`.

```bash
git clone <this-repo-url> && cd AITR_Lab02_MHM2026006_EvidenceAwareTrust
python -m venv .venv && source .venv/bin/activate      # [TEST REQUIRED] on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Reproduce everything (≈10 s)

```bash
bash scripts/run_all.sh
```

Or step by step. Every command below was executed to produce the committed results:

| Step | Command | Output |
|---|---|---|
| Validation tests | `python -m pytest -q` | 12 passed |
| Part 1 reproduction | `python scripts/run_reproduction.py` | `results/reproduction/` |
| Part 2 main comparison | `python scripts/run_main.py` | `results/main/` |
| Deeper analyses A1–A5 | `python scripts/run_analyses.py` | `results/analysis/` |
| Figures | `python scripts/make_figures.py` | `results/figures/`, `paper/figures/` |
| LaTeX tables | `python scripts/make_tables.py` | `paper/tables/` |
| Paper | `cd paper && latexmk -pdf main.tex` | `paper/main.pdf` |
| Notebook | `jupyter nbconvert --to notebook --execute --inplace notebooks/01_sanity_and_walkthrough.ipynb` | [TEST REQUIRED] (executed here with `nbclient`) |

Add `--dev` to any `run_*.py` script to use the debugging seeds (written to `results/dev/`, git-ignored).

**Determinism:** results depend only on the seeds and `configs/protocol.yaml`. Re-running should reproduce the committed CSVs exactly with the pinned versions. With other NumPy versions, small floating-point differences are possible [TEST REQUIRED].

## Experimental design in brief

* **Ground truth:** each claim has stage *s* and evidence quality *q*; P(correct) = σ(logit r_s + β(q − 0.5)), with r = (0.92, 0.85, 0.75, 0.60) for retrieval, extraction, summarisation and synthesis, and β = 4.
* **Simulated user:** experience-based trust (learning rate 0.05–0.15), accepts a claim with P = σ(15·(T_eff − 0.8)), sees the outcomes of accepted claims only 30% of the time, and follows a displayed cue with weight ~U(0.3, 0.7).
* **Costs:** verification = 1, accepted wrong claim = 5, so the optimal rule is "accept iff P(correct) ≥ 0.8".
* **Fairness:** common random numbers (identical claims, user and random draws per seed in every condition); paired Wilcoxon signed-rank tests with Holm correction; 95% bootstrap CIs.
* **Deeper analyses:** ablation (stage-only / evidence-only), robustness to evidence noise and to uninformative evidence, sensitivity to compliance, non-stationary drift, and failure analysis by stage and evidence level.

## Limitations

1. **Simulated users, not people.** Effect sizes say nothing about real users; only the mechanisms are compared. A human pilot is the most valuable follow-up.
2. The proposed estimator shares the generator's logistic form, which favours it; a misspecified-generator test is pending.
3. Stage reliabilities and the cost ratio are illustrative assumptions, not measurements of real LLM agents.
4. The reproduction is from the paper's text (no official code found); the cue modality is abstracted to a compliance probability.

## Credits and citation

* Re-implemented mechanism: K. Okamura and S. Yamada, "Adaptive trust calibration for human-AI collaboration," *PLOS ONE* 15(2): e0229132, 2020. doi:10.1371/journal.pone.0229132
* AI assistance: Claude (Anthropic). See `ai_assistance_log.md` for exactly what was AI-generated and how it was verified.
* Code licence: MIT (`LICENSE`). Paper text © the author.

## Minimum reproduction checklist (for a second student)

- [ ] `pip install -r requirements.txt` succeeds
- [ ] `python -m pytest -q` → 12 passed
- [ ] `bash scripts/run_all.sh` finishes without errors
- [ ] `git status results/` shows no modified CSVs (results byte-identical)
- [ ] `results/main/summary.csv`: evidence_aware decision cost = 0.9991
- [ ] `cd paper && latexmk -pdf main.tex` builds the paper
