import pandas as pd
import numpy as np
import ccxt
import pickle
import talib
from datetime import datetime, timedelta

# Load the pre-trained ML model
MODEL_PATH = "/Users/jameserskine/Documents/trading_bot_backup/models/final_version/xgboost_market_state_vFINAL.pkl"
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# Fetch historical BTC data using CCXT (Binance OHLCV)
def fetch_historical_data(symbol="BTC/USDT", exchange="binance", lookback_days=1095):
    binance = ccxt.binance()
    since = binance.milliseconds() - (1095 * 24 * 60 * 60 * 1000)  # Get data from 3 years ago
    ohlcv = binance.fetch_ohlcv(symbol, timeframe="1d", since=since, limit=lookback_days)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("date", inplace=True)
    print("🔎 Sample BTC Data:\n", df.head(10))
    return df

# Compute technical indicators (matching model features)
def compute_indicators(df):
    df["MA50"] = talib.SMA(df["close"], timeperiod=50)
    df["MA200"] = talib.SMA(df["close"], timeperiod=200)
    df["ATR"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=14)
    df["BB_Width"] = (talib.BBANDS(df["close"], timeperiod=20)[0] - talib.BBANDS(df["close"], timeperiod=20)[2]) / df["close"]
    df["BB_Width"] = pd.to_numeric(df["BB_Width"], errors="coerce").fillna(0)
    df["Price_StdDev"] = df["close"].rolling(20).std()
    df["ADX"] = talib.ADX(df["high"], df["low"], df["close"], timeperiod=14)
    return df.dropna()

# Predict market state using the ML model
def classify_market_state(df):
    features = df[["MA50", "MA200", "ATR", "BB_Width", "ADX", "Price_StdDev"]].dropna()
    
    print("🔎 Sample Feature Data for Prediction:\n", features.head())
    
    predictions = model.predict(features)
    print("🔮 Model Predictions (Raw):\n", predictions[:10])

    # Map numerical predictions to text labels
    label_mapping = {0: "Bull", 1: "Bear", 2: "Ranging"}
    df = df.loc[features.index]  # Ensure only valid rows are assigned predictions
    df["Market_State"] = [label_mapping.get(pred, "Unknown") for pred in predictions]

    # Apply rolling mode smoothing (3-day window)
    for i in range(2, len(df)):
        recent_modes = df["Market_State"].iloc[i-2:i+1].mode()
        if not recent_modes.empty:
            df.at[df.index[i], "Market_State"] = recent_modes[0]

    # 🔥 Override model predictions for stronger trend signals
    df.loc[(df["ADX"] > 25) & (df["MA200"] < df["close"]), "Market_State"] = "Bull"
    df.loc[(df["ADX"] > 25) & (df["MA200"] > df["close"]), "Market_State"] = "Bear"

    return df

# Identify inconsistencies in classification
def detect_misclassifications(df):
    df["Misclassification"] = np.where(
        (df["Market_State"] == "Bear") & (df["MA200"] < df["close"]),
        "⚠️ Potential Misclassification",
        ""
    )
    return df

# Generate classification summary report
def generate_summary(df):
    summary = df["Market_State"].value_counts(normalize=True) * 100
    flip_count = (df["Market_State"] != df["Market_State"].shift(1)).sum()
    report = f"""
    📊 Market State Classification Summary:
    --------------------------------------
    Bull Market: {summary.get('Bull', 0):.2f}%
    Bear Market: {summary.get('Bear', 0):.2f}%
    Ranging Market: {summary.get('Ranging', 0):.2f}%
    
    🔄 Rapid Classification Flips: {flip_count}
    """
    return report

# Main function
def main():
    print("📥 Fetching historical BTC data...")
    df = fetch_historical_data()

    print("📊 Computing technical indicators...")
    df = compute_indicators(df)

    print("🧠 Running ML model predictions...")
    df = classify_market_state(df)

    print("🔍 Identifying potential misclassifications...")
    df = detect_misclassifications(df)

    # Save to CSV
    output_file = "/Users/jameserskine/Documents/trading_bot/logs/market_state_classifications.csv"
    df[["close", "Market_State", "MA200", "ADX", "BB_Width", "Price_StdDev", "Misclassification"]].to_csv(output_file)
    print(f"✅ Market state classifications saved to: {output_file}")

    # Print summary report
    print(generate_summary(df))

if __name__ == "__main__":
    main()
