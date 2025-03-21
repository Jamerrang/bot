import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv("/Users/jameserskine/Documents/trading_bot/experimental/market_state/datasets/market_state_labeled.csv")

# Compute 10th percentile ATR threshold
atr_10th = df['ATR'].quantile(0.10)

# Initialize label list
labels = []

for i in range(len(df)):
    if i < 3:
        labels.append("Unknown")
        continue

    close = df.loc[i, 'close']
    ma_200 = df.loc[i, '200_MA']
    macd = df.loc[i, 'MACD_Histogram']
    adx = df.loc[i, 'ADX']
    atr = df.loc[i, 'ATR']

    # Default to None for fallback
    label = None

    # Step 1: Primary Bull/Bear logic
    if close > ma_200 and macd > 0:
        label = "Bull"
    elif close < ma_200 and macd < 0:
        label = "Bear"

    # Step 2: Ranging override — only if no clear Bull/Bear and it's truly sideways
    if label is None:
        if adx < 20 and atr < atr_10th:
            label = "Ranging"
        else:
            # Fallback to trend bias if no clear Ranging match
            label = "Bull" if close > ma_200 else "Bear"

    labels.append(label)

# Assign final labels and export
df['market_state'] = labels
df.to_csv("experimental_market_state_labels.csv", index=False)
print("✅ Live-style logic updated with cautious Ranging filter.")
