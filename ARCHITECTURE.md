# Architecture

This repository contains the NEXORA Trading Engine experimental research system.

## Components

- `signal_server.py` — FastAPI signal server for MT5 compatibility.
- `analytics/` — offline analytics, feature engineering, and reporting scripts.
- `tools/` — dataset merge and training event build utilities.
- `models/` — excluded runtime model artifacts.
- `data/` and `logs/` — excluded runtime data and logs.

## Safety boundary

This repo is a demo/research export only. It is not approved for live trading.
