from __future__ import annotations

"""
Offline validation / analytics script for the MT5 XAUUSD AI trading bot.

This script reads:
- data/processed/training_events.csv

and prints a human-readable performance summary to the terminal, plus
optionally writes grouped CSV reports under:
- data/processed/reports/

It does NOT:
- modify live trading behavior
- touch MT5 or the FastAPI server
- change the /signal route or any EA logic
"""

import os
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = PROCESSED_DIR / "reports"
TRAINING_EVENTS_CSV = PROCESSED_DIR / "training_events.csv"


def load_events() -> pd.DataFrame:
    if not TRAINING_EVENTS_CSV.exists():
        print(f"ERROR: training_events.csv not found at {TRAINING_EVENTS_CSV}")
        return pd.DataFrame()

    df = pd.read_csv(TRAINING_EVENTS_CSV)
    if df.empty:
        print("WARNING: training_events.csv is empty.")
        return df

    return df


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure key columns exist with safe defaults so analytics do not crash
    if the schema evolves.
    """
    defaults = {
        "ai_signal": 0.0,
        "ai_signal_text": "",
        "ai_confidence": 0.0,
        "ai_confidence_bucket": "unknown",
        "ea_blocked_flag": False,
        "session_london_flag": False,
        "session_newyork_flag": False,
        "session_overlap_flag": False,
        "ret_fwd_1": np.nan,
        "ret_fwd_3": np.nan,
        "ret_fwd_6": np.nan,
        "ret_fwd_12": np.nan,
        "label_dir_1": "",
        "label_dir_3": "",
        "label_dir_6": "",
        "label_dir_12": "",
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    # Normalize types
    df["ai_signal_text"] = df["ai_signal_text"].astype(str)
    df["ai_confidence_bucket"] = df["ai_confidence_bucket"].astype(str)

    # If ai_signal_text is missing or empty, derive it from ai_signal
    mask_empty = df["ai_signal_text"].eq("") | df["ai_signal_text"].isna()
    if mask_empty.any():
        def signal_to_text(x: float) -> str:
            try:
                v = int(x)
            except Exception:
                return "HOLD"
            if v > 0:
                return "BUY"
            if v < 0:
                return "SELL"
            return "HOLD"

        df.loc[mask_empty, "ai_signal_text"] = df.loc[mask_empty, "ai_signal"].apply(
            signal_to_text
        )

    return df


def summarize_basic_counts(df: pd.DataFrame) -> Dict[str, int]:
    total_events = len(df)

    signal_counts = df["ai_signal_text"].value_counts().to_dict()

    blocked_counts = df["ea_blocked_flag"].value_counts().to_dict()
    blocked = int(blocked_counts.get(True, 0))
    not_blocked = int(blocked_counts.get(False, 0))

    return {
        "total_events": int(total_events),
        "buy_events": int(signal_counts.get("BUY", 0)),
        "sell_events": int(signal_counts.get("SELL", 0)),
        "hold_events": int(signal_counts.get("HOLD", 0)),
        "blocked_events": blocked,
        "non_blocked_events": not_blocked,
    }


def summarize_forward_returns_by_signal(df: pd.DataFrame) -> pd.DataFrame:
    group = df.groupby("ai_signal_text", dropna=False)
    agg = group[["ret_fwd_1", "ret_fwd_3", "ret_fwd_6", "ret_fwd_12"]].mean()
    agg = agg.rename_axis("ai_signal_text").reset_index()
    return agg


def summarize_forward_returns_by_confidence(df: pd.DataFrame) -> pd.DataFrame:
    group = df.groupby("ai_confidence_bucket", dropna=False)
    agg = group[["ret_fwd_1", "ret_fwd_3", "ret_fwd_6", "ret_fwd_12"]].mean()
    agg = agg.rename_axis("ai_confidence_bucket").reset_index()
    # Sort buckets in a sensible order if they exist
    bucket_order = ["low", "medium", "high", "very_high", "unknown"]
    agg["bucket_order"] = agg["ai_confidence_bucket"].apply(
        lambda x: bucket_order.index(x) if x in bucket_order else len(bucket_order)
    )
    agg = agg.sort_values("bucket_order").drop(columns=["bucket_order"])
    return agg


def summarize_forward_returns_by_session(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, label in [
        ("session_london_flag", "London"),
        ("session_newyork_flag", "NewYork"),
        ("session_overlap_flag", "Overlap"),
    ]:
        if col not in df.columns:
            continue
        for flag_val in [False, True]:
            sub = df[df[col] == flag_val]
            if sub.empty:
                continue
            stats = {
                "session": label,
                "flag": flag_val,
                "count": int(len(sub)),
                "ret_fwd_1_mean": float(sub["ret_fwd_1"].mean()),
                "ret_fwd_3_mean": float(sub["ret_fwd_3"].mean()),
                "ret_fwd_6_mean": float(sub["ret_fwd_6"].mean()),
                "ret_fwd_12_mean": float(sub["ret_fwd_12"].mean()),
            }
            rows.append(stats)
    return pd.DataFrame(rows)


def compute_directional_hitrate(
    df: pd.DataFrame, label_col: str = "label_dir_3"
) -> pd.DataFrame:
    """
    Basic directional hit-rate for BUY and SELL signals.

    - For BUY: success when label_dir_3 == "UP"
    - For SELL: success when label_dir_3 == "DOWN"
    - HOLD is ignored for hit-rate.
    """
    if label_col not in df.columns:
        return pd.DataFrame()

    subset = df[df["ai_signal_text"].isin(["BUY", "SELL"])].copy()
    if subset.empty:
        return pd.DataFrame()

    def is_hit(row: pd.Series) -> bool:
        sig = row["ai_signal_text"]
        label = str(row[label_col])
        if sig == "BUY":
            return label == "UP"
        if sig == "SELL":
            return label == "DOWN"
        return False

    subset["hit"] = subset.apply(is_hit, axis=1)

    group = subset.groupby("ai_signal_text")
    stats = group["hit"].agg(["count", "sum"]).reset_index()
    stats = stats.rename(columns={"count": "n_events", "sum": "n_hits"})
    stats["hit_rate"] = stats["n_hits"] / stats["n_events"]
    stats["label_horizon"] = label_col
    return stats


def save_report(df: pd.DataFrame, name: str) -> None:
    if df is None or df.empty:
        return
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"{name}.csv"
    df.to_csv(out_path, index=False)


def print_section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    df = load_events()
    if df.empty:
        return

    df = ensure_columns(df)

    # 1–3: basic counts
    counts = summarize_basic_counts(df)
    print_section("Basic Event Counts")
    print(f"Total events:           {counts['total_events']}")
    print(f"BUY events:             {counts['buy_events']}")
    print(f"SELL events:            {counts['sell_events']}")
    print(f"HOLD events:            {counts['hold_events']}")
    print(f"Blocked events:         {counts['blocked_events']}")
    print(f"Non-blocked events:     {counts['non_blocked_events']}")

    # 4: average forward returns by signal
    by_signal = summarize_forward_returns_by_signal(df)
    print_section("Average Forward Returns by Signal (per decision)")
    if by_signal.empty:
        print("No data.")
    else:
        for _, row in by_signal.iterrows():
            sig = row["ai_signal_text"]
            print(
                f"{sig:>4} | "
                f"ret_fwd_1={row['ret_fwd_1']:.5f}, "
                f"ret_fwd_3={row['ret_fwd_3']:.5f}, "
                f"ret_fwd_6={row['ret_fwd_6']:.5f}, "
                f"ret_fwd_12={row['ret_fwd_12']:.5f}"
            )
    save_report(by_signal, "forward_returns_by_signal")

    # 5: average forward returns by confidence bucket
    by_conf = summarize_forward_returns_by_confidence(df)
    print_section("Average Forward Returns by Confidence Bucket")
    if by_conf.empty:
        print("No data.")
    else:
        for _, row in by_conf.iterrows():
            bucket = row["ai_confidence_bucket"]
            print(
                f"{bucket:>10} | "
                f"ret_fwd_1={row['ret_fwd_1']:.5f}, "
                f"ret_fwd_3={row['ret_fwd_3']:.5f}, "
                f"ret_fwd_6={row['ret_fwd_6']:.5f}, "
                f"ret_fwd_12={row['ret_fwd_12']:.5f}"
            )
    save_report(by_conf, "forward_returns_by_confidence_bucket")

    # 6: average forward returns by session flags
    by_session = summarize_forward_returns_by_session(df)
    print_section("Average Forward Returns by Session Flags")
    if by_session.empty:
        print("No data.")
    else:
        for _, row in by_session.iterrows():
            flag_str = "ON " if row["flag"] else "OFF"
            print(
                f"{row['session']:>7} {flag_str} | n={row['count']:<6} "
                f"ret_fwd_1={row['ret_fwd_1_mean']:.5f}, "
                f"ret_fwd_3={row['ret_fwd_3_mean']:.5f}, "
                f"ret_fwd_6={row['ret_fwd_6_mean']:.5f}, "
                f"ret_fwd_12={row['ret_fwd_12_mean']:.5f}"
            )
    save_report(by_session, "forward_returns_by_session_flags")

    # 7: basic directional hit-rate for BUY/SELL using label_dir_3
    hitrate = compute_directional_hitrate(df, label_col="label_dir_3")
    print_section("Directional Hit-Rate (using label_dir_3)")
    if hitrate.empty:
        print("No data.")
    else:
        for _, row in hitrate.iterrows():
            sig = row["ai_signal_text"]
            print(
                f"{sig:>4} | n={row['n_events']:<6} hits={row['n_hits']:<6} "
                f"hit_rate={row['hit_rate']:.3f} (label={row['label_horizon']})"
            )
    save_report(hitrate, "directional_hitrate_label_dir_3")

    print_section("Done")
    print(f"Reports (if any) saved under: {REPORTS_DIR}")


if __name__ == "__main__":
    main()

