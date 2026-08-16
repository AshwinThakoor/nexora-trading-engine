# NEXORA Trading Engine — Project Context

## Purpose

NEXORA is an independent AI-assisted systematic-trading research project created to explore machine-learning signals, robust risk controls, explainable decisions, analytics and MT5 integration.

This public repository is a **sanitized portfolio export**. It demonstrates engineering decisions and selected implementation work while intentionally withholding proprietary strategy and execution logic.

## Full-system architecture

The private/full project is organized into the following layers:

1. **MetaTrader 5 integration** — an Expert Advisor communicates with the Python signal service and handles broker-side execution and trade management.
2. **Python/FastAPI signal service** — validates incoming market data, coordinates feature/inference components and returns structured decisions.
3. **Machine-learning layer** — experiments include LightGBM-based directional modeling and confidence scoring.
4. **Risk/policy layer** — separates prediction from permission to trade and applies defensive controls.
5. **Data/logging layer** — records candles, model decisions and trade outcomes for analysis.
6. **Analytics/monitoring layer** — evaluates outcomes, confidence distributions, decision reasons and system behavior.

## Research scope

- Primary instrument: XAUUSD
- Primary research timeframe: M5
- Environment: MetaTrader 5
- Style: intraday AI-assisted systematic trading
- Current status: research, validation and forward-testing; not presented as an audited production system

## Engineering principles

- Preserve risk controls and fail safely.
- Keep prediction, risk and execution concerns modular.
- Log decisions and blocked reasons for explainability.
- Validate inputs and avoid silent behavior changes.
- Prefer measurable evaluation over trading frequency.
- Keep credentials, datasets, model artifacts and proprietary logic outside the public repository.
- Avoid martingale, grid recovery and other uncontrolled risk escalation.

## Public/private boundary

The public showcase may include architecture, selected analytics/reporting code, safe utilities and engineering documentation.

The following remain private: complete EA implementation, active signal-server implementation, model artifacts, training data, proprietary feature formulas, exact thresholds/scoring rules, detailed risk parameterization, execution overrides and private trading logs.

## Development workflow

AI-assisted development tools may be used as productivity aids for implementation, review and debugging. Architecture choices, validation, integration decisions and project ownership remain the responsibility of the project author.

## Direction

Near-term work focuses on validation, analytics quality, backtesting/forward-testing discipline, model experimentation and observability. Longer-term research may explore retraining workflows, richer monitoring and broader portfolio-level experimentation.
