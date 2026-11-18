#!/usr/bin/env bash
# Regenerate every result, figure and table in the paper from scratch.
# Usage: bash scripts/run_all.sh        (from the repository root; ~10 s on a laptop CPU)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p results/logs
python -m pytest -q                       2>&1 | tee results/logs/tests.log
python scripts/run_reproduction.py        2>&1 | tee results/logs/run_reproduction.log
python scripts/run_main.py                2>&1 | tee results/logs/run_main.log
python scripts/run_analyses.py            2>&1 | tee results/logs/run_analyses.log
python scripts/make_figures.py            2>&1 | tee results/logs/make_figures.log
python scripts/make_tables.py             2>&1 | tee results/logs/make_tables.log
echo "Done. Compare with the committed CSVs:  git status results/"
