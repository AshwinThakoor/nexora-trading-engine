from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

TRADE_LOG_CANDIDATES = [
    BASE_DIR / "logs" / "ai_trade_log.csv",
    BASE_DIR / "logs" / "ai_trade_log(2).csv",
    BASE_DIR / "logs" / "ai_trade_log(3).csv",
    BASE_DIR / "logs" / "ai_trade_log.xlsx",
    BASE_DIR / "05_LOGS" / "ai_trade_log.csv",
]

REGIME_DATA_PATH = BASE_DIR / "analytics" / "regimes" / "candles_with_regimes.csv"

OUTPUT_DIR = BASE_DIR / "analytics" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def find_first_existing(paths):
    for path in paths:
        if path.exists():
            print(f"[FOUND] {path}")
            return path

    print("[MISSING] No trade log found in expected locations.")
    return None


def load_csv(path: Path) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame()

    if not path.exists():
        print(f"[MISSING] {path}")
        return pd.DataFrame()

    try:
        if path.suffix.lower() == ".xlsx":
            return pd.read_excel(path)

        return pd.read_csv(path)

    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="utf-16")

    except Exception as e:
        print(f"[ERROR] Failed loading {path}: {e}")
        return pd.DataFrame()


def analyze_trade_performance(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"status": "no_trade_data"}

    result = {}

    profit_col = None

    for col in df.columns:
        if col.lower() in ["profit", "pnl", "realized_profit"]:
            profit_col = col
            break

    if not profit_col:
        return {
            "status": "profit_column_not_found",
            "available_columns": list(df.columns)
        }

    df[profit_col] = pd.to_numeric(
        df[profit_col],
        errors="coerce"
    ).fillna(0)

    wins = df[df[profit_col] > 0]
    losses = df[df[profit_col] < 0]

    total_closed = len(wins) + len(losses)

    result["total_trades"] = total_closed
    result["winning_trades"] = len(wins)
    result["losing_trades"] = len(losses)

    result["winrate_percent"] = round(
        (len(wins) / max(total_closed, 1)) * 100,
        2
    )

    result["total_profit"] = round(
        df[profit_col].sum(),
        2
    )

    result["average_win"] = round(
        wins[profit_col].mean(),
        2
    ) if len(wins) else 0

    result["average_loss"] = round(
        losses[profit_col].mean(),
        2
    ) if len(losses) else 0

    result["largest_win"] = round(
        df[profit_col].max(),
        2
    )

    result["largest_loss"] = round(
        df[profit_col].min(),
        2
    )

    cumulative = df[profit_col].cumsum()
    drawdown = cumulative - cumulative.cummax()

    result["max_drawdown"] = round(
        drawdown.min(),
        2
    )

    return result


def analyze_regimes(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    if "regime" not in df.columns:
        print("[ERROR] No regime column found.")
        return pd.DataFrame()

    report = df["regime"].value_counts().reset_index()
    report.columns = ["regime", "count"]

    return report


def save_outputs(performance: dict, regime_report: pd.DataFrame):
    summary_path = OUTPUT_DIR / "performance_summary.txt"
    regime_path = OUTPUT_DIR / "regime_distribution.csv"

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("NEXORA PHASE 16.3 — PERFORMANCE REPORT\n")
        f.write("=" * 60 + "\n\n")

        for key, value in performance.items():
            f.write(f"{key}: {value}\n")

    print(f"[OK] Saved: {summary_path}")

    if not regime_report.empty:
        regime_report.to_csv(regime_path, index=False)
        print(f"[OK] Saved: {regime_path}")


def main():
    print("Starting Nexora Phase 16.3 Performance Tracking...")

    trade_log_path = find_first_existing(
        TRADE_LOG_CANDIDATES
    )

    trade_df = load_csv(trade_log_path)
    regime_df = load_csv(REGIME_DATA_PATH)

    performance = analyze_trade_performance(
        trade_df
    )

    regime_report = analyze_regimes(
        regime_df
    )

    save_outputs(
        performance,
        regime_report
    )

    print("Done.")


if __name__ == "__main__":
    main()