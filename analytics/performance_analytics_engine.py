from pathlib import Path
import math
import os

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = BASE_DIR / "analytics" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_TXT = OUTPUT_DIR / "performance_analytics_summary.txt"
LATEST_CSV = OUTPUT_DIR / "performance_analytics_latest.csv"
BY_SIDE_CSV = OUTPUT_DIR / "performance_by_side.csv"
BY_SESSION_CSV = OUTPUT_DIR / "performance_by_session.csv"
BY_REASON_CSV = OUTPUT_DIR / "performance_by_reason.csv"


def mt5_common_files_dir() -> Path | None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None

    return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files"


def log_candidates(filename: str) -> list[Path]:
    candidates = []
    common_dir = mt5_common_files_dir()

    if common_dir is not None:
        candidates.append(common_dir / filename)

    candidates.extend([
        BASE_DIR / "logs" / filename,
        BASE_DIR / "05_LOGS" / filename,
        BASE_DIR / filename,
    ])

    return candidates


def find_log(filename: str) -> Path | None:
    for path in log_candidates(filename):
        if path.exists():
            print(f"[FOUND] {filename}: {path}")
            return path

    print(f"[MISSING] {filename}")
    return None


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    result = df.copy()
    result.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in result.columns
    ]
    return result


def load_csv(path: Path | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame()

    for encoding in ["utf-8", "utf-16", "latin1"]:
        try:
            return normalize_columns(
                pd.read_csv(path, encoding=encoding, on_bad_lines="skip")
            )
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"[ERROR] Failed reading {path}: {e}")
            return pd.DataFrame()

    return pd.DataFrame()


def first_existing_column(df: pd.DataFrame, names: list[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name

    return None


def safe_round(value: float, digits: int = 2):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0

    if math.isinf(number):
        return "INF"

    if not math.isfinite(number):
        return 0.0

    return round(number, digits)


def profit_factor(gross_profit: float, gross_loss_abs: float):
    if gross_loss_abs == 0:
        return float("inf") if gross_profit > 0 else 0.0

    return gross_profit / gross_loss_abs


def parse_timestamp_series(df: pd.DataFrame) -> pd.Series:
    ts_col = first_existing_column(
        df,
        ["ts", "timestamp", "time", "datetime", "date"],
    )

    if ts_col is None:
        return pd.Series(pd.NaT, index=df.index)

    return pd.to_datetime(df[ts_col], errors="coerce")


def classify_session(timestamp) -> str:
    if pd.isna(timestamp):
        return "UNKNOWN"

    hour = int(timestamp.hour)

    if 0 <= hour < 7:
        return "ASIA"

    if 7 <= hour < 12:
        return "LONDON"

    if 12 <= hour < 17:
        return "LONDON_NY_OVERLAP"

    if 17 <= hour < 22:
        return "NEW_YORK"

    return "OFF_HOURS"


def prepare_closed_trades(trade_df: pd.DataFrame) -> pd.DataFrame:
    if trade_df.empty:
        return pd.DataFrame()

    profit_col = first_existing_column(
        trade_df,
        ["profit", "pnl", "realized_profit", "net_profit"],
    )

    if profit_col is None:
        print("[STOP] No profit column found in trade log.")
        return pd.DataFrame()

    trades = trade_df.copy()
    trades["profit_value"] = pd.to_numeric(
        trades[profit_col],
        errors="coerce",
    ).fillna(0.0)

    event_col = first_existing_column(trades, ["event_type", "event", "type"])
    if event_col is not None:
        closed = trades[
            trades[event_col].astype(str).str.upper().str.strip() == "CLOSE"
        ].copy()
    else:
        closed = trades.copy()

    if closed.empty:
        closed = trades[trades["profit_value"] != 0].copy()

    side_col = first_existing_column(closed, ["side", "direction", "trade_side"])
    if side_col is not None:
        closed["side_label"] = (
            closed[side_col]
            .astype(str)
            .str.upper()
            .str.strip()
            .replace({"1": "BUY", "-1": "SELL", "0": "HOLD", "": "UNKNOWN"})
        )
    else:
        signal_col = first_existing_column(closed, ["signal"])
        if signal_col is not None:
            signal = pd.to_numeric(closed[signal_col], errors="coerce").fillna(0)
            closed["side_label"] = signal.map({1: "BUY", -1: "SELL"}).fillna("UNKNOWN")
        else:
            closed["side_label"] = "UNKNOWN"

    reason_col = first_existing_column(
        closed,
        ["note", "reason", "setup", "detail", "retcode_desc"],
    )
    if reason_col is not None:
        closed["reason_setup"] = (
            closed[reason_col].astype(str).str.strip().replace("", "UNKNOWN")
        )
    else:
        closed["reason_setup"] = "UNKNOWN"

    closed["timestamp"] = parse_timestamp_series(closed)
    closed["session"] = closed["timestamp"].apply(classify_session)

    return closed.sort_values("timestamp", na_position="last").reset_index(drop=True)


def calculate_max_drawdown(profits: pd.Series) -> float:
    if profits.empty:
        return 0.0

    equity = profits.astype(float).cumsum()
    running_peak = pd.concat([
        pd.Series([0.0]),
        equity,
    ], ignore_index=True).cummax().iloc[1:].reset_index(drop=True)
    drawdown = equity.reset_index(drop=True) - running_peak
    return abs(float(drawdown.min())) if not drawdown.empty else 0.0


def performance_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "net_profit": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "max_drawdown": 0.0,
            "expectancy": 0.0,
        }

    profit = df["profit_value"].astype(float)
    wins = profit[profit > 0]
    losses = profit[profit < 0]
    total_trades = int(len(df))
    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss_abs = abs(float(losses.sum())) if not losses.empty else 0.0
    net_profit = float(profit.sum())

    return {
        "total_trades": total_trades,
        "winning_trades": int(len(wins)),
        "losing_trades": int(len(losses)),
        "win_rate": safe_round((len(wins) / total_trades) * 100 if total_trades else 0),
        "net_profit": safe_round(net_profit),
        "gross_profit": safe_round(gross_profit),
        "gross_loss": safe_round(gross_loss_abs),
        "profit_factor": safe_round(profit_factor(gross_profit, gross_loss_abs), 4),
        "average_win": safe_round(wins.mean() if not wins.empty else 0),
        "average_loss": safe_round(losses.mean() if not losses.empty else 0),
        "largest_win": safe_round(profit.max() if not profit.empty else 0),
        "largest_loss": safe_round(profit.min() if not profit.empty else 0),
        "max_drawdown": safe_round(calculate_max_drawdown(profit)),
        "expectancy": safe_round(net_profit / total_trades if total_trades else 0),
    }


def grouped_performance(df: pd.DataFrame, column: str) -> pd.DataFrame:
    output_columns = [
        column,
        "total_trades",
        "winning_trades",
        "losing_trades",
        "win_rate",
        "net_profit",
        "gross_profit",
        "gross_loss",
        "profit_factor",
        "average_win",
        "average_loss",
        "largest_win",
        "largest_loss",
        "max_drawdown",
        "expectancy",
    ]

    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=output_columns)

    rows = []
    for value, group in df.groupby(column, dropna=False):
        row = {column: value if str(value).strip() else "UNKNOWN"}
        row.update(performance_metrics(group))
        rows.append(row)

    report = pd.DataFrame(rows)
    return report.sort_values(
        by=["net_profit", "total_trades"],
        ascending=[False, False],
    ).reset_index(drop=True)


def best_label(report: pd.DataFrame, column: str) -> str:
    if report.empty or column not in report.columns:
        return "UNKNOWN"

    return str(report.iloc[0][column])


def worst_label(report: pd.DataFrame, column: str) -> str:
    if report.empty or column not in report.columns:
        return "UNKNOWN"

    return str(report.sort_values("net_profit", ascending=True).iloc[0][column])


def count_matching(df: pd.DataFrame, column: str, value: str) -> int:
    if df.empty or column not in df.columns:
        return 0

    return int((df[column].astype(str).str.upper() == value.upper()).sum())


def build_latest_summary(
    closed_trades: pd.DataFrame,
    decision_df: pd.DataFrame,
    execution_df: pd.DataFrame,
    side_report: pd.DataFrame,
    session_report: pd.DataFrame,
    reason_report: pd.DataFrame,
    paths: dict[str, Path | None],
) -> dict:
    summary = performance_metrics(closed_trades)

    stage_col = first_existing_column(decision_df, ["stage"])
    execution_stage_col = first_existing_column(execution_df, ["stage"])

    summary.update({
        "best_side": best_label(side_report, "side_label"),
        "worst_side": worst_label(side_report, "side_label"),
        "best_session": best_label(session_report, "session"),
        "worst_session": worst_label(session_report, "session"),
        "best_reason_setup": best_label(reason_report, "reason_setup"),
        "worst_reason_setup": worst_label(reason_report, "reason_setup"),
        "trade_log_rows": int(len(closed_trades)),
        "decision_log_rows": int(len(decision_df)),
        "execution_log_rows": int(len(execution_df)),
        "blocked_decisions": count_matching(decision_df, stage_col, "BLOCKED") if stage_col else 0,
        "blocked_executions": (
            count_matching(execution_df, execution_stage_col, "BLOCKED_FILTER")
            if execution_stage_col else 0
        ),
        "trade_log_path": str(paths.get("trade") or ""),
        "decision_log_path": str(paths.get("decision") or ""),
        "execution_log_path": str(paths.get("execution") or ""),
    })

    return summary


def write_summary_txt(summary: dict, reports: dict[str, pd.DataFrame]):
    with open(SUMMARY_TXT, "w", encoding="utf-8") as f:
        f.write("NEXORA PERFORMANCE ANALYTICS ENGINE\n")
        f.write("=" * 70 + "\n\n")

        f.write("Overall Performance\n")
        f.write("-" * 70 + "\n")
        for key in [
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
            "net_profit",
            "gross_profit",
            "gross_loss",
            "profit_factor",
            "average_win",
            "average_loss",
            "largest_win",
            "largest_loss",
            "max_drawdown",
            "expectancy",
        ]:
            f.write(f"{key}: {summary.get(key, '')}\n")

        f.write("\nBest / Worst Segments\n")
        f.write("-" * 70 + "\n")
        for key in [
            "best_side",
            "worst_side",
            "best_session",
            "worst_session",
            "best_reason_setup",
            "worst_reason_setup",
        ]:
            f.write(f"{key}: {summary.get(key, '')}\n")

        f.write("\nLog Coverage\n")
        f.write("-" * 70 + "\n")
        for key in [
            "trade_log_rows",
            "decision_log_rows",
            "execution_log_rows",
            "blocked_decisions",
            "blocked_executions",
            "trade_log_path",
            "decision_log_path",
            "execution_log_path",
        ]:
            f.write(f"{key}: {summary.get(key, '')}\n")

        f.write("\nTop Side Performance\n")
        f.write("-" * 70 + "\n")
        f.write(reports["side"].head(5).to_string(index=False))
        f.write("\n\nTop Session Performance\n")
        f.write("-" * 70 + "\n")
        f.write(reports["session"].head(5).to_string(index=False))
        f.write("\n\nTop Reason / Setup Performance\n")
        f.write("-" * 70 + "\n")
        f.write(reports["reason"].head(10).to_string(index=False))
        f.write("\n")


def save_outputs(
    summary: dict,
    side_report: pd.DataFrame,
    session_report: pd.DataFrame,
    reason_report: pd.DataFrame,
):
    pd.DataFrame([summary]).to_csv(LATEST_CSV, index=False)
    side_report.to_csv(BY_SIDE_CSV, index=False)
    session_report.to_csv(BY_SESSION_CSV, index=False)
    reason_report.to_csv(BY_REASON_CSV, index=False)
    write_summary_txt(
        summary,
        {
            "side": side_report,
            "session": session_report,
            "reason": reason_report,
        },
    )

    print(f"[OK] Saved: {SUMMARY_TXT}")
    print(f"[OK] Saved: {LATEST_CSV}")
    print(f"[OK] Saved: {BY_SIDE_CSV}")
    print(f"[OK] Saved: {BY_SESSION_CSV}")
    print(f"[OK] Saved: {BY_REASON_CSV}")


def main():
    print("Starting Nexora Performance Analytics Engine...")

    paths = {
        "trade": find_log("ai_trade_log.csv"),
        "decision": find_log("ai_decision_log.csv"),
        "execution": find_log("ai_execution_log.csv"),
    }

    trade_df = load_csv(paths["trade"])
    decision_df = load_csv(paths["decision"])
    execution_df = load_csv(paths["execution"])

    closed_trades = prepare_closed_trades(trade_df)
    side_report = grouped_performance(closed_trades, "side_label")
    session_report = grouped_performance(closed_trades, "session")
    reason_report = grouped_performance(closed_trades, "reason_setup")

    summary = build_latest_summary(
        closed_trades,
        decision_df,
        execution_df,
        side_report,
        session_report,
        reason_report,
        paths,
    )

    save_outputs(summary, side_report, session_report, reason_report)

    print("Done.")


if __name__ == "__main__":
    main()
