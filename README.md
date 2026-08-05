# NEXORA Trading Engine

This repository is an experimental research/demo system for MT5 signal generation.
It is not approved for live trading and provides no profitability guarantee.

## Important notes

- Experimental research/demo system only.
- Not approved for live trading.
- No profitability guarantee.
- Model weights and private datasets are excluded from source control.
- Full functionality requires Windows and MT5 compatibility.

## What this repository contains

- `signal_server.py` — Python signal server for MT5-compatible signal generation.
- `analytics/` — offline analytics, feature engineering, and reporting scripts.
- `tools/` — utilities for dataset merging and training-event creation.
- `docs/media/SCREENSHOT_PLAN.md` — planned repository review screenshots.

## What is excluded from source control

- `data/` — runtime candle and dataset files.
- `models/` — model weight binaries.
- `logs/` — runtime log files.
- Local backups, archives, caches, `.venv`, and generated database files.

## Safe CI workflow

CI should only perform safe validation checks:

- Validate Python syntax with `python -m compileall .`
- Validate Python file parsing with AST (`ast.parse`).
- Validate YAML syntax for GitHub workflows.
- Validate Markdown links for internal documentation.

## Not safe for CI

- Starting MT5 or broker connections.
- Live trading.
- Executing MT5 Expert Advisors.
