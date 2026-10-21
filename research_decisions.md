# Research Decisions Log

**Project:** Human Trust Calibration in Human-Agent Collaboration for
Autonomous Research\
**Researcher:** Mili Acharya\
**Status:** Initial log --- based only on the uploaded 19-page
literature review\
**Last updated:** 2026-10-20

## Evidence labels

-   **VERIFIED** --- directly supported by the current review or a
    supplied artifact. This means verified against that artifact, not
    independently verified against the original publication.
-   **INFERRED** --- a reasoned interpretation or proposed next step
    that still needs testing.
-   **UNKNOWN** --- evidence is missing; do not treat as fact.

## Current project state

### Scope of the existing review

-   **VERIFIED:** The review covers trust calibration in human-agent,
    human-AI, human-robot, and human-autonomy collaboration.
-   **VERIFIED:** It classifies prior approaches as reliability-based,
    transparency-based, explanation-based, human-state-based, adaptive,
    and mutually adaptive.
-   **VERIFIED:** It proposes an evidence-aware adaptive framework for
    autonomous research, combining research context, agent
    capability/reliability, evidence quality, human state and reliance,
    verification requirements, and adaptive communication.
-   **VERIFIED:** Proposed evaluation dimensions include trust
    calibration, appropriate reliance, verification efficiency,
    research-output quality, workload, situation awareness, and team
    performance.
-   **VERIFIED:** The review acknowledges that the framework is
    conceptual and that its proposed metrics are not a validated
    measurement scale.

### Current gap claims in the review

-   **VERIFIED (as claims made by the review, not yet independently
    confirmed):** Limited longitudinal evaluation; insufficient
    claim-level evidence awareness; limited integration of human-state
    information with evidence quality and agent reliability; few
    standardized autonomous-research benchmarks; insufficient attention
    to both over-trust and under-trust; heterogeneous evaluation
    measures.
-   **UNKNOWN:** Whether these gaps remain open after a sufficiently
    comprehensive and current search of the original literature.
-   **UNKNOWN:** Whether an existing system or benchmark already
    implements the proposed combination of mechanisms.
-   **UNKNOWN:** Which gap is both novel and experimentally testable
    within the researcher's available time and computing resources.

## Decision log

### D-001 --- Treat the review as the starting artifact, not as proof of novelty

-   **Status:** Adopted provisionally
-   **Decision:** Use the uploaded review to define the initial
    conceptual scope, but independently verify the central gap against
    primary sources and closely neighboring work before claiming
    novelty.
-   **Reason:** A gap stated in a literature review is a research
    hypothesis, not proof that no prior work addresses it.
-   **Evidence:** Uploaded review, Sections 3--8 and 12--14; especially
    the stated research gaps and limitations.
-   **Next actions:** Obtain the literature-search strategy, screening
    records, reference library, and study-extraction/comparison table if
    available. Check the most relevant primary studies and newer
    neighboring work.
-   **Open questions:** What databases and date range were searched?
    What inclusion/exclusion criteria were used? Were full texts
    checked? How were claims and limitations extracted?

### D-002 --- Do not assume the proposed framework is implemented or validated

-   **Status:** Adopted
-   **Decision:** Describe the framework as conceptual until code, a
    formal algorithm, or experimental outputs establish otherwise.
-   **Reason:** The review itself says empirical validation is still
    required.
-   **Evidence:** Uploaded review, Sections 9, 10, 14, and 15.
-   **Next actions:** Ask whether any implementation, notebook,
    prototype, pilot data, or experimental output already exists.
-   **Open questions:** Is the intended contribution a software system,
    a trust-calibration algorithm, a benchmark, or an empirical
    comparison?

### D-003 --- Keep agent reliability separate from claim-level evidence quality

-   **Status:** Working hypothesis; not yet an experimentally validated
    design choice
-   **Decision:** Preserve this distinction when designing candidate
    baselines and metrics.
-   **Reason:** The review argues that an agent can perform a task
    reliably while a particular generated claim is weakly supported.
-   **Evidence:** Uploaded review, Sections 2.3, 8.2, 9, and 13.
-   **Next actions:** Define observable operational measures for agent
    reliability, claim support, evidence quality, and appropriate
    reliance; inspect existing operationalizations in primary studies.
-   **Open questions:** How will claim support be labeled? Who or what
    establishes the ground truth? How will evidence quality be measured
    reproducibly?

### D-004 --- Avoid selecting metrics before defining the experiment

-   **Status:** Adopted provisionally
-   **Decision:** Treat the review's metrics as candidate dimensions,
    not as finalized validated measures.
-   **Reason:** Metric definitions, denominators, labels, and baselines
    must match the task and data.
-   **Evidence:** Uploaded review, Sections 9--10 and 14.
-   **Next actions:** Specify the task, unit of analysis, outcomes,
    ground truth, comparison conditions, and evaluation protocol before
    finalizing metrics.
-   **Open questions:** Will the study use simulated users, a
    human-participant experiment, retrospective interaction logs, or a
    benchmark-only evaluation?

## Evidence still required

1.  **Review provenance:** Search queries, databases, search dates, date
    range, inclusion/exclusion criteria, screening counts, and any
    protocol.
2.  **Study-level evidence:** Reference manager export (BibTeX/RIS),
    full texts where available, and the review's extraction/comparison
    spreadsheet.
3.  **Implementation state:** Existing code, notebooks, repository
    archive, configuration files, and dependency/environment
    information, if any.
4.  **Experiment state:** Dataset files and licenses, annotation guide,
    pilot outputs, logs, metric calculations, plots, and random seeds,
    if any.
5.  **Feasibility constraints:** Available compute, access to human
    participants, expected deadline, and whether external APIs or paid
    services are allowed.

## Next actions (in order)

1.  Collect review provenance and study-level evidence.
2.  Verify the strongest neighboring work and narrow the candidate gap.
3.  Map each relevant study to its method, data, outcome, limitation,
    and possible baseline.
4.  Choose one feasible research question and define falsifiable
    hypotheses.
5.  Specify a reproducible experimental protocol before implementation.
6.  Implement and test a baseline; record environment, seeds, and exact
    commands.
7.  Run planned comparisons and report all results, including negative
    results and failures.
8.  Update this log whenever a decision changes, recording the reason
    and supporting evidence.

## Change-entry template

### D-XXX --- Short decision title

-   **Date:**
-   **Status:** Proposed / Adopted / Rejected / Superseded
-   **Decision:**
-   **Reason:**
-   **Evidence/source:** Include exact citation, file name,
    page/section, URL/DOI where verified, or output path.
-   **Alternatives considered:**
-   **Risks/limitations:**
-   **Next action:**
-   **Open questions:**
