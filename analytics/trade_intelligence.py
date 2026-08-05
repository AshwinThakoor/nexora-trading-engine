import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

TRADE_LOG_PATH = BASE_DIR / "logs" / "ai_trade_log.csv"
DECISION_LOG_PATH = BASE_DIR / "logs" / "ai_decisions.csv"

OUTPUT_DIR = BASE_DIR / "analytics" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"[MISSING] {path}")
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="utf-16")


def analyze_trade_log(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"status": "no_trade_data"}

    result = {}

    result["total_rows"] = len(df)

    profit_col = None
    for col in df.columns:
        if col.lower() in ["profit", "pnl", "realized_profit"]:
            profit_col = col
            break

    if profit_col:
        df[profit_col] = pd.to_numeric(df[profit_col], errors="coerce").fillna(0)

        wins = df[df[profit_col] > 0]
        losses = df[df[profit_col] < 0]

        result["total_profit"] = round(df[profit_col].sum(), 2)
        result["winning_trades"] = len(wins)
        result["losing_trades"] = len(losses)
        result["winrate_percent"] = round((len(wins) / max(len(wins) + len(losses), 1)) * 100, 2)
        result["average_win"] = round(wins[profit_col].mean(), 2) if len(wins) else 0
        result["average_loss"] = round(losses[profit_col].mean(), 2) if len(losses) else 0
        result["largest_win"] = round(df[profit_col].max(), 2)
        result["largest_loss"] = round(df[profit_col].min(), 2)

    return result


def analyze_decision_log(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"status": "no_decision_data"}

    result = {}
    result["total_decisions"] = len(df)

    if "signal" in df.columns:
        result["signal_counts"] = df["signal"].value_counts().to_dict()

    if "confidence" in df.columns:
        df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
        result["average_confidence"] = round(df["confidence"].mean(), 4)
        result["max_confidence"] = round(df["confidence"].max(), 4)
        result["min_confidence"] = round(df["confidence"].min(), 4)

        df["confidence_bucket"] = pd.cut(
            df["confidence"],
            bins=[0, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00],
            labels=["0-50", "50-60", "60-70", "70-80", "80-90", "90-100"],
            include_lowest=True
        )

        bucket_report = df["confidence_bucket"].value_counts().sort_index()
        bucket_report.to_csv(OUTPUT_DIR / "confidence_bucket_report.csv")

    if "reason" in df.columns:
        reason_report = df["reason"].value_counts().head(30)
        reason_report.to_csv(OUTPUT_DIR / "top_decision_reasons.csv")

    return result


def save_summary(summary: dict):
    output_file = OUTPUT_DIR / "trade_intelligence_summary.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("NEXORA PHASE 16.1 — TRADE INTELLIGENCE REPORT\n")
        f.write("=" * 60 + "\n\n")

        for section, data in summary.items():
            f.write(f"\n[{section.upper()}]\n")
            f.write("-" * 40 + "\n")
            if isinstance(data, dict):
                for key, value in data.items():
                    f.write(f"{key}: {value}\n")
            else:
                f.write(str(data) + "\n")

    print(f"[OK] Report saved to: {output_file}")


def main():
    print("Starting Nexora Phase 16.1 Trade Intelligence Analysis...")

    trade_df = load_csv(TRADE_LOG_PATH)
    decision_df = load_csv(DECISION_LOG_PATH)

    summary = {
        "trade_log_analysis": analyze_trade_log(trade_df),
        "decision_log_analysis": analyze_decision_log(decision_df),
    }

    save_summary(summary)

    print("Done.")


if __name__ == "__main__":
    main()