# Excluded Files and Artifacts

This repository export is intended to keep the trading-engine source clean, focused, and recruiter-ready.

## Excluded artifact classes

- `data/`, `models/`, `logs/`
  - Runtime CSV logs, raw candle data, model binaries, and generated datasets are excluded.
- `analytics/reports/`
  - Generated analysis summaries and live report outputs are excluded.
- `analytics/features/*.txt`, `analytics/learning/*.txt`, `analytics/regimes/*.txt`
  - Generated feature/regime summary files are excluded.
- Backup and historical signal server snapshots:
  - `signal_server_backup.py`
  - `signal_server_old.py`
  - `signal_server_phase13_5_backup.py`
  - `signal_server_phase15_backup.py`
- Local environment and audit files:
  - `.venv/`, `.venv-1/`, `.venv-2/`, `.venv-3/`
  - `__pycache__/`
  - `*.csv`, `*.parquet`, `*.pkl`, `*.joblib`, `*.ex5`, `*.zip`, `*.sql`
  - `project_tree.txt`, `repository_structure.txt`, `mt5_ai_bot_git_backup/`

## Why these are excluded

- They are either generated from local runs,
- or they contain binary / training artifacts that should not be part of the clean source export.

## What remains in repository source

- Production trading-server and Python application code.
- Project documentation and architecture notes.
- Offline tooling for rebuilding datasets from local data.
- Scripts for model training, analytics, and signal server operation.
