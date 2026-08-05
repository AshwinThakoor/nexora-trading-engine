# Model and Data Policy

This repository export is intentionally focused on source code, documentation, and tooling.

## What belongs in this repository

- Python server code and app logic.
- MT5 signal server integration code.
- Data-processing and analytics tooling.
- Documentation, architecture notes, and readme information.

## What does not belong in this repository

- Trained model artifacts:
  - `models/*.pkl`
  - `models/*.joblib`
  - `models/*.json` model metadata files used only for runtime.
- Runtime data and logs:
  - `data/*.csv`, `data/*.parquet`
  - `logs/*.csv`
  - local MT5 common files like `ai_trade_log.csv` and `ai_decision_log.csv`
- Generated analytics outputs and reports:
  - `analytics/reports/*`
  - `analytics/features/*.txt`
  - `analytics/learning/*.txt`
  - `analytics/regimes/*.txt`
- Backup or historical phase snapshots of the signal server:
  - `signal_server_backup.py`
  - `signal_server_old.py`
  - `signal_server_phase13_5_backup.py`
  - `signal_server_phase15_backup.py`

## Recommended workflow for using this export

1. Keep source-controlled files limited to code, docs, and tooling.
2. Use local data and model training pipelines to reproduce generated artifacts.
3. Keep runtime outputs and model binaries out of git to maintain a clean, portable repo.
4. Add additional `.gitignore` rules for any new local artifacts created during development.

## Rebuilding models and reports

Use the tools in `tools/` and the Python application scripts to rebuild datasets and analytics when needed.

- `tools/build_training_events.py` for training event datasets.
- `tools/merge_history.py` for candle history merging.
- `analytics/` code for feature extraction and report generation.
