from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

TRADE_LOG_CANDIDATES = [
    BASE_DIR / "logs" / "ai_trade_log.csv",
    BASE_DIR / "logs" / "ai_trade_log(2).csv",
    BASE_DIR / "logs" / "ai_trade_log(3).csv",
]

DECISION_LOG_CANDIDATES = [
    BASE_DIR / "logs" / "ai_decision_log.csv",
    BASE_DIR / "logs" / "ai_decisions.csv",
    BASE_DIR / "logs" / "ai_decision_log(3).csv",
]

OUTPUT_DIR = BASE_DIR / "analytics" / "learning"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def find_first_existing(paths):
    for path in paths:
        if path.exists():
            print(f"[FOUND] {path}")
            return path
    return None


def load_csv(path: Path) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="utf-16")
    except Exception as e:
        print(f"[ERROR] Failed loading {path}: {e}")
        return pd.DataFrame()


def find_profit_column(df: pd.DataFrame):
    for col in df.columns:
        if col.lower() in ["profit", "pnl", "realized_profit"]:
            return col
    return None


def build_trade_memory(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"status": "no_trade_data"}

    profit_col = find_profit_column(trades)

    if not profit_col:
        return {
            "status": "profit_column_not_found",
            "available_columns": list(trades.columns)
        }

    trades[profit_col] = pd.to_numeric(trades[profit_col], errors="coerce").fillna(0)

    wins = trades[trades[profit_col] > 0]
    losses = trades[trades[profit_col] < 0]

    memory = {
        "total_closed_trades": len(wins) + len(losses),
        "wins": len(wins),
        "losses": len(losses),
        "winrate": round(len(wins) / max(len(wins) + len(losses), 1) * 100, 2),
        "net_profit": round(trades[profit_col].sum(), 2),
        "avg_win": round(wins[profit_col].mean(), 2) if len(wins) else 0,
        "avg_loss": round(losses[profit_col].mean(), 2) if len(losses) else 0,
        "largest_win": round(trades[profit_col].max(), 2),
        "largest_loss": round(trades[profit_col].min(), 2),
    }

    if "side" in trades.columns:
        side_report = trades.groupby("side")[profit_col].agg(
            trades="count",
            net_profit="sum",
            avg_profit="mean"
        ).reset_index()

        side_report.to_csv(OUTPUT_DIR / "memory_by_side.csv", index=False)

    if "note" in trades.columns:
        note_report = trades.groupby("note")[profit_col].agg(
            trades="count",
            net_profit="sum",
            avg_profit="mean"
        ).reset_index().sort_values("net_profit")

        note_report.to_csv(OUTPUT_DIR / "memory_by_exit_note.csv", index=False)

    return memory


def build_decision_memory(decisions: pd.DataFrame) -> dict:
    if decisions.empty:
        return {"status": "no_decision_data"}

    memory = {
        "total_decisions": len(decisions)
    }

    if "signal" in decisions.columns:
        signal_report = decisions["signal"].value_counts().reset_index()
        signal_report.columns = ["signal", "count"]
        signal_report.to_csv(OUTPUT_DIR / "memory_signal_distribution.csv", index=False)

    if "confidence" in decisions.columns:
        decisions["confidence"] = pd.to_numeric(decisions["confidence"], errors="coerce")

        decisions["confidence_bucket"] = pd.cut(
            decisions["confidence"],
            bins=[0, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00],
            labels=["0-50", "50-60", "60-70", "70-80", "80-90", "90-100"],
            include_lowest=True
        )

        confidence_report = decisions["confidence_bucket"].value_counts().sort_index().reset_index()
        confidence_report.columns = ["confidence_bucket", "count"]
        confidence_report.to_csv(OUTPUT_DIR / "memory_confidence_distribution.csv", index=False)

        memory["avg_confidence"] = round(decisions["confidence"].mean(), 4)
        memory["max_confidence"] = round(decisions["confidence"].max(), 4)
        memory["min_confidence"] = round(decisions["confidence"].min(), 4)

    if "reason" in decisions.columns:
        reason_report = decisions["reason"].value_counts().head(50).reset_index()
        reason_report.columns = ["reason", "count"]
        reason_report.to_csv(OUTPUT_DIR / "memory_top_reasons.csv", index=False)

    return memory


def save_memory_report(trade_memory: dict, decision_memory: dict):
    output_file = OUTPUT_DIR / "learning_memory_summary.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("NEXORA PHASE 16.4 — LEARNING MEMORY ENGINE\n")
        f.write("=" * 60 + "\n\n")

        f.write("[TRADE MEMORY]\n")
        f.write("-" * 40 + "\n")
        for key, value in trade_memory.items():
            f.write(f"{key}: {value}\n")

        f.write("\n[DECISION MEMORY]\n")
        f.write("-" * 40 + "\n")
        for key, value in decision_memory.items():
            f.write(f"{key}: {value}\n")

        f.write("\n[NEXT INTELLIGENCE OBJECTIVE]\n")
        f.write("-" * 40 + "\n")
        f.write("Identify conditions that repeatedly cause losses.\n")
        f.write("Use memory reports to tune confidence thresholds, regimes, sessions, and risk.\n")

    print(f"[OK] Saved: {output_file}")


def main():
    print("Starting Nexora Phase 16.4 Learning Memory Engine...")

    trade_path = find_first_existing(TRADE_LOG_CANDIDATES)
    decision_path = find_first_existing(DECISION_LOG_CANDIDATES)

    trades = load_csv(trade_path)
    decisions = load_csv(decision_path)

    trade_memory = build_trade_memory(trades)
    decision_memory = build_decision_memory(decisions)

    save_memory_report(trade_memory, decision_memory)

    print("Done.")


if __name__ == "__main__":
    main()