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
    since = binance.parse8601((datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%dT00:00:00Z"))
    ohlcv = binance.fetch_ohlcv(symbol, timeframe="1d", since=since, limit=lookback_days)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("date", inplace=True)
    return df

# Compute technical indicators (200-MA, ADX, MACD Histogram)
def compute_indicators(df):
df["MA200"] = talib.SMA(df["close"], timeperiod=200)
    df["ADX"] = talib.ADX(df["high"], df["low"], df["close"], timeperiod=14)
    macd, macdsignal, macdhist = talib.MACD(df["close"], fastperiod=12, slowperiod=26, signalperiod=9)
    df["MACD_Histogram"] = macdhist
    df["200_MA_Status"] = np.where(df["close"] > df["200_MA"], "Above MA", "Below MA")
    return df.dropna()

# Predict market state using the ML model
def classify_market_state(df):
    features = df[["close", "200_MA", "ADX", "MACD_Histogram"]].dropna()
    df["Market_State"] = model.predict(features)
    return df

# Identify inconsistencies in classification
def detect_misclassifications(df):
    df["Misclassification"] = np.where(
        (df["Market_State"] == "Bear") & (df["200_MA_Status"] == "Above MA"),
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
    df[["close", "Market_State", "200_MA_Status", "ADX", "MACD_Histogram", "Misclassification"]].to_csv(output_file)
    print(f"✅ Market state classifications saved to: {output_file}")

    # Print summary report
    print(generate_summary(df))

if __name__ == "__main__":
    main()
