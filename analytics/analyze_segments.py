from __future__ import annotations

"""
Offline segment analytics for the MT5 XAUUSD AI trading bot (Phase 9).

This script:
- Reads: data/processed/training_events.csv
- Slices performance by key segments:
  - decision_hour_utc
  - decision_dayofweek
  - ai_confidence_bucket
  - ai_signal_text
  - session_london_flag
  - session_newyork_flag
  - session_overlap_flag
  - ea_reason_normalized (if available)
- For each segment, reports:
  - count
  - BUY / SELL / HOLD counts
  - mean ret_fwd_1 / 3 / 6 / 12 (all events)
  - directional edge for BUY/SELL (using ret_fwd_3 by default)
  - directional hit-rate for BUY/SELL (using label_dir_3)
- Writes CSVs under:
  - data/processed/reports/segments/
- Prints a readable terminal summary of best and worst segments.

It does NOT touch:
- live trading behavior
- the MT5 EA
- signal_server.py or /signal behavior

Note:
- During early testing, the dataset can be very small.
- The best/worst segment printer therefore uses a low minimum count threshold.
- Increase that threshold later when you have much more data.
"""

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SEGMENTS_DIR = PROCESSED_DIR / "reports" / "segments"
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
        "ai_confidence_bucket": "unknown",
        "decision_hour_utc": np.nan,
        "decision_dayofweek": np.nan,
        "session_london_flag": False,
        "session_newyork_flag": False,
        "session_overlap_flag": False,
        "ea_reason_normalized": "",
        "ea_blocked_flag": False,
        "ret_fwd_1": np.nan,
        "ret_fwd_3": np.nan,
        "ret_fwd_6": np.nan,
        "ret_fwd_12": np.nan,
        "label_dir_3": "",
    }

    out = df.copy()
    for col, default in defaults.items():
        if col not in out.columns:
            out[col] = default

    out["ai_signal_text"] = out["ai_signal_text"].astype(str)
    out["ai_confidence_bucket"] = out["ai_confidence_bucket"].astype(str)
    out["ea_reason_normalized"] = out["ea_reason_normalized"].astype(str)
    out["label_dir_3"] = out["label_dir_3"].astype(str)

    # Derive ai_signal_text from ai_signal where missing
    mask_empty = out["ai_signal_text"].eq("") | out["ai_signal_text"].isna()

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

    if mask_empty.any():
        out.loc[mask_empty, "ai_signal_text"] = out.loc[mask_empty, "ai_signal"].apply(
            signal_to_text
        )

    return out


def compute_segment_table(df: pd.DataFrame, group_col: str, min_count: int = 1) -> pd.DataFrame:
    """
    Build a segment table grouped by a single column.

    For each segment:
    - count
    - buy_count / sell_count / hold_count
    - mean ret_fwd_1 / 3 / 6 / 12 (all events)
    - BUY directional edge (ret_fwd_3)
    - SELL directional edge (-ret_fwd_3)
    - BUY directional hit-rate (label_dir_3 == "UP")
    - SELL directional hit-rate (label_dir_3 == "DOWN")
    """
    if group_col not in df.columns:
        return pd.DataFrame()

    groups = df.groupby(group_col, dropna=False)
    rows: List[Dict] = []

    for key, g in groups:
        n = len(g)
        if n < min_count:
            continue

        buy_mask = g["ai_signal_text"] == "BUY"
        sell_mask = g["ai_signal_text"] == "SELL"
        hold_mask = g["ai_signal_text"] == "HOLD"

        buy_g = g[buy_mask]
        sell_g = g[sell_mask]

        row: Dict = {
            group_col: key,
            "count": int(n),
            "buy_count": int(buy_mask.sum()),
            "sell_count": int(sell_mask.sum()),
            "hold_count": int(hold_mask.sum()),
            "ret_fwd_1_mean": float(g["ret_fwd_1"].mean()),
            "ret_fwd_3_mean": float(g["ret_fwd_3"].mean()),
            "ret_fwd_6_mean": float(g["ret_fwd_6"].mean()),
            "ret_fwd_12_mean": float(g["ret_fwd_12"].mean()),
        }

        if not buy_g.empty:
            buy_ret3 = float(buy_g["ret_fwd_3"].mean())
            buy_hits = int((buy_g["label_dir_3"] == "UP").sum())
            row["buy_edge_fwd_3"] = buy_ret3
            row["buy_hit_rate_3"] = float(buy_hits / len(buy_g))
        else:
            row["buy_edge_fwd_3"] = np.nan
            row["buy_hit_rate_3"] = np.nan

        if not sell_g.empty:
            sell_ret3 = float(sell_g["ret_fwd_3"].mean())
            sell_hits = int((sell_g["label_dir_3"] == "DOWN").sum())
            row["sell_edge_fwd_3"] = -sell_ret3
            row["sell_hit_rate_3"] = float(sell_hits / len(sell_g))
        else:
            row["sell_edge_fwd_3"] = np.nan
            row["sell_hit_rate_3"] = np.nan

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def save_segment_report(df: pd.DataFrame, name: str) -> None:
    if df is None or df.empty:
        return

    SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SEGMENTS_DIR / f"{name}.csv"
    df.to_csv(out_path, index=False)


def print_best_worst(
    df: pd.DataFrame,
    key_col: str,
    metric_col: str,
    label: str,
    top_n: int = 5,
    min_count: int = 3,
) -> None:
    """
    Print best and worst segments by a given metric.

    Early testing note:
    - min_count is intentionally low because small datasets are common at first.
    - Increase this later when you have many more events.
    """
    if df is None or df.empty or metric_col not in df.columns:
        print(f"No data for {label}.")
        return

    sub = df.dropna(subset=[metric_col]).copy()
    sub = sub[sub["count"] >= min_count]

    if sub.empty:
        print(f"No segments with count >= {min_count} for {label}.")
        return

    print(f"\n{label}: top {top_n} by {metric_col}")
    top = sub.sort_values(metric_col, ascending=False).head(top_n)
    for _, row in top.iterrows():
        print(
            f"  {key_col}={row[key_col]!r}, count={int(row['count'])}, "
            f"{metric_col}={row[metric_col]:.5f}"
        )

    print(f"\n{label}: bottom {top_n} by {metric_col}")
    bottom = sub.sort_values(metric_col, ascending=True).head(top_n)
    for _, row in bottom.iterrows():
        print(
            f"  {key_col}={row[key_col]!r}, count={int(row['count'])}, "
            f"{metric_col}={row[metric_col]:.5f}"
        )


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

    segment_cols = [
        "decision_hour_utc",
        "decision_dayofweek",
        "ai_confidence_bucket",
        "ai_signal_text",
        "session_london_flag",
        "session_newyork_flag",
        "session_overlap_flag",
    ]

    if "ea_reason_normalized" in df.columns:
        segment_cols.append("ea_reason_normalized")

    all_results: Dict[str, pd.DataFrame] = {}

    for col in segment_cols:
        print_section(f"Segment: {col}")

        seg_df = compute_segment_table(df, col, min_count=1)
        all_results[col] = seg_df

        if seg_df.empty:
            print("No data.")
            continue

        safe_name = col.replace(" ", "_")
        save_segment_report(seg_df, f"segments_by_{safe_name}")

        print(f"Total segments: {len(seg_df)}")

        print_best_worst(
            seg_df,
            key_col=col,
            metric_col="buy_edge_fwd_3",
            label=f"{col} (BUY edge)",
            top_n=5,
            min_count=3,
        )

        print_best_worst(
            seg_df,
            key_col=col,
            metric_col="sell_edge_fwd_3",
            label=f"{col} (SELL edge)",
            top_n=5,
            min_count=3,
        )

    print_section("Done")
    print(f"Segment reports saved (if any) under: {SEGMENTS_DIR}")


if __name__ == "__main__":
    main()