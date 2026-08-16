# MT5 AI Trading Bot — Project Context

## Project goal
Build a serious professional MT5 AI trading bot for XAUUSD on M5 that can eventually become a highly profitable, well-engineered, research-driven, production-grade system.

This is NOT a toy bot.
This is NOT a martingale bot.
This is NOT a grid bot.
This is NOT a scam-style “AI bot”.

The goal is:
- robust architecture
- measurable performance
- strong risk controls
- explainable decisions
- continuous improvement
- future VPS deployment
- future self-learning / retraining workflow

---

## Current architecture
The system consists of:

1. MT5 Expert Advisor
   - file: `XAU_AI_Bot_clean.mq5`
   - runs on MT5
   - requests AI signals from local FastAPI server
   - executes trades
   - applies filters and trade management
   - logs decisions and trade outcomes

2. Python AI server
   - file: `signal_server.py`
   - FastAPI app
   - receives candle data from MT5
   - builds features
   - loads LightGBM model
   - returns:
     - signal
     - confidence
     - stop loss distance
     - take profit distance
     - reason
     - prob_buy

3. ML model
   - model file: `models/lgbm_xauusd_m5.pkl`
   - meta file: `models/lgbm_xauusd_m5_meta.json`

4. Data storage
   - candle log: `data/raw/candles.csv`
   - fallback candle log: `data/raw/candles_fallback.csv`

5. Dashboard / analytics
   - served by FastAPI
   - route: `/dashboard`
   - API route: `/api/status`

6. MT5 common logs
   - `ai_trade_log.csv`
   - `ai_decision_log.csv`

---

## Trading instrument and timeframe
- Symbol: XAUUSD
- Primary timeframe: M5
- Higher timeframe filter: usually H1
- Broker environment: MT5 retail broker
- Execution style: intraday AI-assisted systematic trading
- NOT true HFT

---

## Current strategy components
Already implemented:
- AI model inference
- confidence threshold
- session filter
- higher timeframe trend filter
- spread filter
- volatility spike filter
- news filter using CSV
- risk-based position sizing
- ATR-based SL and TP
- break-even logic
- trailing stop logic
- dashboard
- decision logging
- blocked reason logging
- trade logging

---

## Important constraints
When modifying this project:
- always preserve existing working behavior unless explicitly replacing it
- never remove risk controls without explicit approval
- never silently change thresholds or trade logic
- never switch to martingale/grid/revenge logic
- prefer clear logs and explainability
- prefer robust production-safe code
- always keep file paths aligned with current project structure
- code must be final, full, and working
- do not output partial snippets when replacing a file; output full file content
- if changing a file, provide the complete final file

---

## Coding standards
- Make minimal but correct changes
- Preserve working interfaces
- Keep logs explicit and human-readable
- Add comments for non-obvious sections
- Avoid breaking MT5 compatibility
- Avoid placeholder code
- Avoid pseudocode
- Always produce runnable code
- For Python, keep FastAPI app fully runnable
- For MQL5, keep EA fully compilable

---

## Current known goals
Short-term goals:
1. stable analytics
2. stable blocked reason reporting
3. stable trade outcome reporting
4. better feature engineering
5. stronger ML model
6. backtesting and validation
7. VPS deployment

Mid-term goals:
1. self-learning pipeline
2. retraining workflow
3. Telegram alerts
4. richer dashboard
5. multiple symbols

Long-term goals:
1. professional-grade systematic trading platform
2. portfolio-level AI trading
3. production deployment

---

## What NOT to do
Do NOT:
- add martingale
- add grid recovery
- add random indicators without purpose
- overtrade just to create activity
- weaken risk controls carelessly
- output incomplete code
- break current dashboard routes
- break MT5 ↔ FastAPI communication

---

## Development philosophy

Cursor should:
- implement requested code changes
- refactor safely
- preserve compatibility
- improve observability
- keep the system production-minded

When uncertain, Cursor should favor:
- safety
- logging
- minimal change
- explicit behavior
