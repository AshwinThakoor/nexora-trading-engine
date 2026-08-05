from pathlib import Path
import pandas as pd

# Base project folder
BASE = Path(__file__).resolve().parents[1]

RAW = BASE / "data" / "raw"

history_file = RAW / "candles_history_xauusd_m5.csv"
main_file = RAW / "candles.csv"

print("History file:", history_file)
print("Main file:", main_file)

# Load historical candles
hist = pd.read_csv(history_file, encoding="utf-16")

print("Historical rows:", len(hist))

# If main candles already exist, merge them
if main_file.exists():
    main = pd.read_csv(main_file)
    print("Live rows:", len(main))
    df = pd.concat([main, hist])
else:
    df = hist

# Remove duplicates
df = df.drop_duplicates(subset=["symbol","timeframe","t"])

# Sort candles by time
df = df.sort_values("t")

# Save merged dataset
df.to_csv(main_file, index=False)

print("✅ Merge complete")
print("Total rows:", len(df))
print("Saved to:", main_file)