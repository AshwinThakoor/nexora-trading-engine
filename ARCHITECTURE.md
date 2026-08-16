# NEXORA Trading Engine — Architecture

NEXORA is an AI-assisted systematic-trading research platform. The full system connects MetaTrader 5 to a Python/FastAPI intelligence layer, machine-learning inference, independent risk controls, execution management, logging and offline analytics.

This public repository documents the architecture while intentionally withholding proprietary implementation details.

## 1. System overview

```mermaid
flowchart LR
    MARKET[Market / XAUUSD] --> MT5[MetaTrader 5]
    MT5 --> EA[Expert Advisor]
    EA -->|market context| API[FastAPI Signal Service]
    API --> VALIDATE[Input Validation]
    VALIDATE --> FEATURES[Feature Pipeline]
    FEATURES --> MODEL[ML Inference]
    MODEL --> POLICY[Risk & Policy Layer]
    POLICY --> DECISION{Decision}
    DECISION -->|approved| EA
    DECISION -->|blocked / hold| LOGS[Decision Logs]
    EA -->|execution| MT5
    EA --> LOGS
    LOGS --> ANALYTICS[Analytics & Monitoring]
```

The active EA, signal service, model artifacts, proprietary features and policy thresholds remain private.

## 2. Request-to-decision lifecycle

```mermaid
sequenceDiagram
    participant M as MT5 / EA
    participant A as FastAPI Layer
    participant F as Feature Pipeline
    participant L as ML Model
    participant R as Risk Policy
    participant G as Logging

    M->>A: New market/candle context
    A->>A: Validate request
    A->>F: Build model-ready representation
    F->>L: Feature vector
    L-->>A: Directional output + confidence
    A->>R: Candidate decision + context
    R-->>A: Permit / block / hold
    A->>G: Record decision metadata
    A-->>M: Structured response
    M->>G: Record execution/outcome metadata
```

This separation is intentional: **model prediction is not equivalent to permission to trade**.

## 3. Layered design

```mermaid
flowchart TB
    subgraph PRESENTATION[Monitoring / Presentation]
        DASH[Dashboard & Status Views]
        REPORTS[Research Reports]
    end

    subgraph ANALYTICS[Analytics Layer]
        TRADE[Trade Intelligence]
        PERF[Performance Analytics]
        SEG[Segment Analysis]
        MEMORY[Learning Memory]
    end

    subgraph CORE[Private Decision Runtime]
        API[FastAPI Boundary]
        FEATURE[Feature Engineering]
        MODEL[ML Inference]
        RISK[Risk / Policy]
    end

    subgraph EXECUTION[Execution Layer]
        EA[MT5 Expert Advisor]
        BROKER[Broker Environment]
    end

    subgraph DATA[Data / Observability]
        CANDLES[Candle Data]
        DECISIONS[Decision Logs]
        TRADES[Trade Logs]
        MODELS[Model Artifacts]
    end

    CANDLES --> CORE
    MODELS --> MODEL
    CORE --> EA --> BROKER
    CORE --> DECISIONS
    EA --> TRADES
    DECISIONS --> ANALYTICS
    TRADES --> ANALYTICS
    ANALYTICS --> PRESENTATION
```

## 4. Machine-learning boundary

The research system uses engineered market/candle information and has experimented with LightGBM for directional modeling and confidence scoring.

```mermaid
flowchart LR
    RAW[Market Inputs] --> CLEAN[Validation / Cleaning]
    CLEAN --> FE[Feature Engineering]
    FE --> VECTOR[Model Feature Vector]
    VECTOR --> LGBM[LightGBM Inference]
    LGBM --> PROB[Directional / Confidence Output]
    PROB --> CONTEXT[Context + Risk Evaluation]
    CONTEXT --> FINAL[Final Candidate Decision]
```

Public documentation intentionally stops at the component/interface level. Feature definitions, training recipes, fitted weights and decision thresholds are private.

## 5. Risk architecture

A central design principle is that the ML model proposes information; a separate safety layer controls whether that information can become an execution candidate.

```mermaid
flowchart TD
    SIGNAL[Model Candidate] --> CHECKS[Independent Safety Checks]
    CHECKS --> POSITION[Position / Exposure Policy]
    CHECKS --> SESSION[Session / Market Context]
    CHECKS --> VOL[Volatility / Execution Context]
    CHECKS --> CONF[Confidence Policy]
    POSITION --> GATE{Risk Gate}
    SESSION --> GATE
    VOL --> GATE
    CONF --> GATE
    GATE -->|permit| CANDIDATE[Execution Candidate]
    GATE -->|reject| HOLD[No Trade / Defensive Hold]
    CANDIDATE --> MANAGEMENT[Trade Management]
```

Exact parameter values and active rules are not published.

## 6. Observability and analytics loop

NEXORA records decisions and outcomes so behavior can be investigated rather than treated as a black box.

```mermaid
flowchart LR
    DECISION[Decision Events] --> STORE[Local Protected Logs]
    OUTCOME[Trade Outcomes] --> STORE
    STORE --> CLEAN[Normalization]
    CLEAN --> PERF[Performance Metrics]
    CLEAN --> SEG[Segment Analysis]
    CLEAN --> CONF[Confidence Analysis]
    PERF --> MEMORY[Research Memory]
    SEG --> MEMORY
    CONF --> MEMORY
    MEMORY --> REVIEW[Human Research / Model Review]
    REVIEW -. future controlled iteration .-> SYSTEM[Private System]
```

The public `learning_memory.py` should be understood as an **analysis feedback mechanism**, not an autonomous system that rewrites live strategy code.

## 7. Public versus private architecture

```mermaid
flowchart TB
    FULL[Full NEXORA System]
    FULL --> PUBLIC[Public Portfolio Surface]
    FULL --> PRIVATE[Private IP Surface]

    PUBLIC --> A1[Architecture Documentation]
    PUBLIC --> A2[Performance Analytics]
    PUBLIC --> A3[Training-event Evaluation]
    PUBLIC --> A4[Trade Intelligence]
    PUBLIC --> A5[Safe Data Utilities]
    PUBLIC --> A6[CI / Security Documentation]

    PRIVATE --> P1[Active Signal Service]
    PRIVATE --> P2[Complete MT5 EA]
    PRIVATE --> P3[Model Artifacts]
    PRIVATE --> P4[Feature Formulas]
    PRIVATE --> P5[Thresholds / Scoring]
    PRIVATE --> P6[Execution & Risk Parameters]
```

## 8. Failure-safety philosophy

The architecture favors conservative failure behavior:

- malformed or unavailable inputs should not silently become trade approvals;
- missing model/context information should degrade toward HOLD/no-trade behavior;
- prediction and execution remain separated;
- risk controls should not be bypassed merely to increase trade frequency;
- runtime decisions should leave enough metadata for investigation;
- model/data artifacts and credentials are kept outside public source control.

## 9. Technology map

| Area | Technology / approach |
|---|---|
| Language | Python |
| API architecture | FastAPI / REST |
| ML research | LightGBM, feature engineering, confidence analysis |
| Trading integration | MetaTrader 5 / Expert Advisor architecture |
| Data analysis | Pandas, NumPy |
| Research instrument | XAUUSD |
| Primary research timeframe | M5 |
| Environment | Windows + WSL/Ubuntu workflow |
| Packaging/deployment research | Docker |
| Observability | Structured decision/trade logs + analytics |
| Source control | Git / GitHub |

## 10. Architectural status

The system is an active research project undergoing validation and forward-testing. The architecture is designed to support progressively stronger testing, backtesting, observability and deployment practices, but the project is **not presented as an audited production trading platform or as having guaranteed profitability**.

For repository-level details, see `PROJECT_STRUCTURE.md`. For the rationale and development scope, see `PROJECT_CONTEXT.md`.
