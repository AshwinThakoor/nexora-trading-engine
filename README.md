## MT5 XAUUSD AI Trading Bot

This project is a serious **MT5 Expert Advisor + Python AI server** for trading **XAUUSD on M5**.  
It is designed for **research‑driven, risk‑controlled, explainable trading**, not martingale / grid / gambling.

---
uvicorn signal_server:app --host 127.0.0.1 --port 8000 --reload
python run_nexora_brain.py
python brain_scheduler.py
## Main components and files

- **`XAU_AI_Bot_clean.mq5` (MT5 Expert Advisor)**
  - Runs inside MT5 on a XAUUSD M5 chart.
  - Sends recent candles to the Python server.
  - Receives AI signal, confidence, SL/TP distances, and reason.
  - Applies filters (session, higher timeframe, spread, volatility, news).
  - Manages trades (risk sizing, SL/TP, break‑even, trailing).
  - Logs decisions and trades into CSV files in the MT5 *Common Files* folder.

- **`signal_server.py` (Python AI signal server)**
  - FastAPI app that listens locally (usually `http://127.0.0.1:8000`).
  - Endpoint `/signal`:
    - Accepts candles from MT5.
    - Builds ML features.
    - Runs the LightGBM model (`models/lgbm_xauusd_m5.pkl`).
    - Returns signal, confidence, SL/TP distances, AI reason, and `prob_buy`.
  - Logs every AI decision to `logs/ai_decisions.csv`.
  - Serves a small monitoring dashboard at `/dashboard` and status API at `/api/status`.

- **Model files**
  - `models/lgbm_xauusd_m5.pkl` — trained LightGBM model.
  - `models/lgbm_xauusd_m5_meta.json` — feature/meta configuration for the model.

- **Data & logs**
  - `data/raw/candles.csv` — main candle history as sent from MT5.
  - `data/raw/candles_fallback.csv` — fallback candle log if the main file is locked.
  - `logs/ai_decisions.csv` — per‑decision AI output log (from `/signal`).

- **MT5 common logs (written by the EA)**
  - In Windows, typically:  
    `C:\Users\<YOU>\AppData\Roaming\MetaQuotes\Terminal\Common\Files\`
  - `ai_trade_log.csv` — trade events (opens, closes, PnL, etc.).
  - `ai_decision_log.csv` — EA‑side decisions and blocked reasons.

- **Offline tools**
  - `tools/merge_history.py` — merges historical candles into `data/raw/candles.csv`.
  - `tools/build_training_events.py` — builds an offline **training‑events dataset** from:
    - `data/raw/candles*.csv`
    - `logs/ai_decisions.csv`
    - `ai_trade_log.csv`
    - `ai_decision_log.csv`
    - Outputs:
      - `data/processed/training_events.csv`
      - `data/processed/training_events.parquet`

---

## How to start the Python server

1. **Activate your virtual environment** (if you have one):

   ```bash
   cd path/to/mt5_ai_bot
   .venv\Scripts\activate    # Windows PowerShell/CMD (if .venv exists)
   ```

2. **Install Python dependencies** (only if not already done):

   ```bash
   pip install -r requirements.txt
   ```

   If you do not have a `requirements.txt`, make sure at least these are installed:
   - `fastapi`
   - `uvicorn`
   - `pandas`
   - `numpy`
   - `joblib`
   - `scikit-learn` (for LightGBM compatibility, if needed)

3. **Run the server**:

   ```bash
   python signal_server.py
   ```

   By default this starts a FastAPI app on `http://127.0.0.1:8000` (check your console output for the exact host/port).

---

## How to open the dashboard

Once the Python server is running:

1. Open a browser.
2. Go to:

   ```text
   http://127.0.0.1:8000/dashboard
   ```

The dashboard shows:
- Whether the model is loaded.
- Number of AI decisions.
- Candle file size.
- Closed trades / wins / losses / realized PnL (from `ai_trade_log.csv`).
- Top blocked reasons (from `ai_decision_log.csv`).
- Recent decisions (signal, confidence, SL/TP, reason).

---

## How to attach the EA in MT5

1. Place `XAU_AI_Bot_clean.ex5` / `XAU_AI_Bot_clean.mq5` into your MT5 **Experts** folder.
2. Restart MT5 or refresh the **Navigator**.
3. Open a **XAUUSD M5** chart.
4. In the **Navigator → Expert Advisors**, drag `XAU_AI_Bot_clean` onto the chart.
5. In the EA settings:
   - Allow live trading if you want it to actually open trades.
   - Allow WebRequest (if the EA uses HTTP) and add the server URL (usually `http://127.0.0.1:8000`).
   - Configure input parameters (risk, filters, etc.) as desired.
6. Make sure **AutoTrading** (top toolbar) is enabled (green).

---

## Key EA settings and filters (conceptual)

The exact input names can vary by EA version, but you will typically see:

- **Session filter**  
  - Enables or disables trading only during specific **broker/server hours** (the time shown in your MT5 Market Watch / chart, **not** your local PC clock).  
  - Look for something like `UseSessionFilter`, `SessionStart`, `SessionEnd`.

- **Higher timeframe (HTF) trend filter**  
  - Uses H1 or another higher timeframe trend to allow/deny trades.  
  - Look for inputs like `UseHTFFilter`, `HTF_Timeframe`, `HTF_MinTrend`.

- **Spread filter**  
  - Blocks trades when spread is too high.  
  - Look for `UseSpreadFilter`, `MaxSpreadPoints` or similar.

- **Volatility spike filter**  
  - Blocks trades during abnormal volatility (large candles, spikes).  
  - Look for `UseVolatilityFilter`, `MaxRangeFactor`, etc.

- **News filter**  
  - Blocks trades around scheduled news events from a CSV file.  
  - Look for `UseNewsFilter`, `NewsCSVPath`, `NewsMinutesBefore`, `NewsMinutesAfter`.

- **Break‑even and trailing stop**  
  - Move SL to break‑even after price moves in your favor.
  - Trail SL as price continues in your direction.
  - Look for `UseBreakEven`, `BreakEvenTrigger`, `BreakEvenOffset`, `UseTrailingStop`, `TrailingStart`, `TrailingStep`, etc.

To turn a feature **on/off**, set the corresponding boolean input to `true/false` (or `1/0`) in the EA **Inputs** tab.

---

## Understanding the session filter and broker time

The **session filter** uses the **MT5 broker/server time**, not your local PC time.

- The “hour” used in the EA’s session logic comes from MT5 (server time), which may be:
  - 0, 1, 2, … 23 (24‑hour clock)
  - shifted several hours ahead/behind UTC and your local timezone.
- This means:
  - “London open” in broker time might not be 08:00 on your local clock.
  - If your broker server is UTC+2 and you want to trade London 07:00–12:00 UTC, you must convert that window to **server time** (e.g. 09:00–14:00 server).

**How to test if the session filter is blocking trades**

1. Attach the EA to a XAUUSD M5 chart as usual.
2. In the EA **Inputs**, find the session filter option (for example `UseSessionFilter`).
3. Temporarily set:

   - `UseSessionFilter = false` (or `0`)  

4. Keep all other risk filters (spread, volatility, news, HTF, etc.) ON.
5. Watch:
   - If AI BUY/SELL signals now result in trades, you have confirmed that the **session filter** was blocking earlier.
   - Re‑enable the session filter (`UseSessionFilter = true`) after testing so you do not weaken your normal protections.

**How to adjust London/New York hours to your broker time**

1. In MT5, look at the **current server time**:
   - Check the time shown in the Market Watch window or in the MT5 status bar.
2. Compare it to **UTC** or your desired session:
   - Example: Broker server is UTC+2 (server time = UTC time + 2 hours).
   - London core session is roughly 07:00–16:00 UTC.
   - In server time (UTC+2), this becomes:
     - Start: 09:00 server
     - End: 18:00 server
3. Set your EA inputs accordingly, for example:
   - `LondonSessionStart = 9`
   - `LondonSessionEnd = 18`
4. If you use separate London/New York sessions, convert each window from UTC to **server time** the same way, then enter those hours in the EA’s session settings.

---

## Where logs are written

**Python side**
- `data/raw/candles.csv` — raw candles from MT5.
- `data/raw/candles_fallback.csv` — fallback candle log.
- `logs/ai_decisions.csv` — every AI decision from `/signal`.
- `data/processed/training_events.csv` and `.parquet` — offline training events built by `tools/build_training_events.py`.

**MT5 side (Common Files)**
- `ai_trade_log.csv` — trade events and PnL.
- `ai_decision_log.csv` — EA‑side decision and blocked reason log.

The Python dashboard (`/dashboard`) reads these logs to show stats.

---

## What common errors mean (high‑level)

You may see **AI reason codes** in:
- `logs/ai_decisions.csv`
- the dashboard **Recent AI Decisions** table

Examples:

- `model_missing`  
  - The model files were not found or failed to load.  
  - Check `models/lgbm_xauusd_m5.pkl` and `models/lgbm_xauusd_m5_meta.json`.

- `missing_features:[...]`  
  - The model expects features that are not present in the feature builder.  
  - Usually means code and model meta are out of sync.

- `feature_count_mismatch:model=...`  
  - Number of features in the model does not match what the server computed.

- `server_exception:<...>`  
  - The `/signal` handler raised an exception.  
  - Check the Python console output for a stack trace.

On the MT5 side, **blocked reasons** in `ai_decision_log.csv` or the Experts tab can include things like:
- `BLOCKED_SESSION` — outside allowed trading hours.
- `BLOCKED_HTF_BEARISH` / `BLOCKED_HTF_BULLISH` — higher timeframe trend filter blocked.
- `BLOCKED_SPREAD` — spread too high.
- `BLOCKED_NEWS` — upcoming or current news event.
- `BLOCKED_VOL_SPIKE` — volatility spike detected.
- `BLOCKED_POSITION_EXISTS` — an existing position conflicts with a new trade.
- `TRADE_SEND_FAILED` — MT5 rejected the order (e.g. `TRADE_RETCODE_...` error).

Exact strings depend on the EA version, but they should be human‑readable and clearly say why a trade did not open.

---

## How to stop the system safely

1. **In MT5 (EA side)**
   - Turn off **AutoTrading** (top toolbar), or
   - Remove the EA from the chart (right‑click on chart → Expert Advisors → Remove).
   - This stops new trades from being opened. Open trades will still be managed by MT5 according to your broker settings unless the EA is responsible for dynamic exits (trailing, break‑even). If you want a completely manual environment, close trades yourself.

2. **In Python (server side)**
   - Go to the terminal running `python signal_server.py`.
   - Press `Ctrl+C` once to stop the FastAPI server gracefully.

Stopping the server does **not** automatically close open trades; it only prevents new AI signals from being generated.

---

## Project phases (high‑level)

The project is being built in phases. Key phases include:

- **Phase 1–3** — Basic EA + AI signal integration, risk controls, filters.
- **Phase 4–5** — Dashboard, analytics, better blocked‑reason logging, trade outcome tracking.
- **Phase 6** — Stronger feature engineering and improved ML model.
- **Phase 7 (current)** — **Offline training‑events dataset**:
  - `tools/build_training_events.py` converts logs and candles into a clean, per‑decision dataset.
  - Output lives in `data/processed/`.
- **Future phases** — Self‑learning pipeline, retraining workflow, Telegram alerts, VPS deployment, portfolio‑level trading.

---

## How to know if the bot is actually trading

Check the following:

1. **MT5 chart**
   - EA face icon in the top‑right of the chart:
     - Smiley face (or “AutoTrading enabled” icon) should be active.
   - New orders / positions appear in the **Trade** tab.

2. **MT5 logs**
   - In the **Experts** and **Journal** tabs:
     - Look for messages like “TRADE OPENED” or clearly labeled status lines.
   - In `ai_trade_log.csv`:
     - New rows with `OPEN` / `CLOSE` events and non‑zero `volume`.

3. **Python dashboard**
   - `/dashboard`:
     - `Closed Trades`, `Wins`, `Losses`, and `Realized PnL` should start moving over time.

If AI decisions are being logged but no trades appear, it usually means **filters are blocking trades** or the EA is configured to run in a “monitor only” style.

---

## How to know if the server is offline

- In MT5:
  - Experts log may show errors like “cannot connect to server” or repeated WebRequest/HTTP failures.
  - No new AI reasons or decisions appear.

- In Python:
  - The terminal where you ran `python signal_server.py` is closed or shows errors.

- In the browser:
  - Opening `http://127.0.0.1:8000/health` or `/dashboard` fails (connection error).

When the server is offline, the EA should fall back to **no trade** (signals effectively treated as HOLD / blocked).

---

## How to know if a trade was blocked

1. **Dashboard `/dashboard`**
   - The **Blocked Reasons** table shows counts of reasons from `ai_decision_log.csv`.
   - If a reason’s count grows (e.g. `BLOCKED_SESSION`), that filter is actively blocking trades.

2. **MT5 Experts / Journal logs**
   - After each BUY/SELL AI signal, the EA should log a clear message such as:
     - `TRADE OPENED`
     - `BLOCKED_SESSION`
     - `BLOCKED_SPREAD`
     - `BLOCKED_NEWS`
     - `BLOCKED_VOL_SPIKE`
     - `BLOCKED_HTF_BULLISH` / `BLOCKED_HTF_BEARISH`
     - `BLOCKED_POSITION_EXISTS`
     - `TRADE_SEND_FAILED`

3. **`ai_decision_log.csv`**
   - Each row includes a `reason` column that records the **final EA reason** for not trading or for taking the trade.

Blocked reasons **do not** mean the AI is broken; they indicate that **risk controls or filters** are doing their job.

---

## Where the `training_events` dataset comes from

The **training‑events dataset** is built offline by:

- Running:

  ```bash
  python tools/build_training_events.py
  ```

- This script:
  - Reads:
    - `data/raw/candles.csv` and `data/raw/candles_fallback.csv`
    - `logs/ai_decisions.csv`
    - `ai_trade_log.csv` and `ai_decision_log.csv` from the MT5 Common Files folder
  - Aligns:
    - Each AI decision with:
      - EA blocked reason (if any)
      - Trade open/close (if any)
      - Forward returns from candles (1/3/6/12 bars)
    - Adds labels like:
      - `executed_flag`, `trade_result_class` (WIN / LOSS / BREAKEVEN / NO_TRADE)
      - Directional labels `label_dir_1/3/6/12`
      - Session flags and other metadata.
  - Writes:
    - `data/processed/training_events.csv`
    - `data/processed/training_events.parquet`

Each row in `training_events` corresponds to **one AI decision**, not one candle.  
This dataset is used for:
- Model retraining and validation.
- Strategy analytics (e.g. which filters hurt/help).
- Future self‑learning and LLM‑based reviewers.

