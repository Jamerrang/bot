import pandas as pd
import numpy as np
from ta.trend import ADXIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator

# Load dataset
file_path = "~/Documents/trading_bot/datasets/market_state_ready.csv"
df = pd.read_csv(file_path, parse_dates=["timestamp"])

# Ensure required columns exist
required_cols = ["close", "high", "low", "open", "volume"]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

# Drop existing indicator values (forcing recomputation)
df.drop(columns=["200_MA", "RSI", "ADX", "MACD_Histogram", "ATR", "OBV"], errors="ignore", inplace=True)

# Compute indicators from scratch
df["200_MA"] = df["close"].rolling(window=200, min_periods=1).mean()
df["RSI"] = RSIIndicator(df["close"], window=14).rsi().ffill().bfill()
df["ADX"] = ADXIndicator(df["high"], df["low"], df["close"], window=14).adx().ffill().bfill()
df["MACD_Histogram"] = MACD(df["close"]).macd_diff().ffill().bfill()
df["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
df["ATR"] = df["ATR"].replace(0, np.nan).ffill().bfill()
df["OBV"] = OnBalanceVolumeIndicator(df["close"], df["volume"]).on_balance_volume().ffill().bfill()

# Fill any remaining NaNs
df.fillna(method='ffill', inplace=True)
df.fillna(method='bfill', inplace=True)

# Save updated dataset
df.to_csv(file_path, index=False)
print("✅ Indicators recomputed and dataset updated.")
