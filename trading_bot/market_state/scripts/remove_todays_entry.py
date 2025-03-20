import pandas as pd
from datetime import datetime, timezone

# Load dataset
file_path = "~/Documents/trading_bot/datasets/market_state_ready.csv"
df = pd.read_csv(file_path, parse_dates=["timestamp"])

# Get today's UTC date
today_utc = datetime.now(timezone.utc).date()

# Ensure we only remove today's date (not the last row blindly)
df = df[df["timestamp"].dt.date != today_utc]

# Save updated dataset
df.to_csv(file_path, index=False)
print(f"✅ Removed today's entry ({today_utc}). Ready dataset saved.")

