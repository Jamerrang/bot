import sqlite3
import pandas as pd
import ccxt
import time
from datetime import datetime
from ta.trend import ADXIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator

# Database setup
DB_PATH = "market_data.db"
TABLE_NAME = "ohlcv_data"
MARKET_STATE_LOG = "market_state_log.csv"
EXCHANGE = ccxt.binance()
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"

# Ensure SQLite database exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            timestamp INTEGER PRIMARY KEY,
            open REAL, high REAL, low REAL, close REAL, volume REAL
        )
    ''')
    conn.commit()
    conn.close()

# Fetch live OHLCV data
def fetch_live_data():
    ohlcv = EXCHANGE.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=200)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    return df

# Store new data in SQLite
def store_data(df):
    conn = sqlite3.connect(DB_PATH)
    df["timestamp"] = df["timestamp"].astype(int)  # Ensure timestamp remains INTEGER
    df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
    conn.close()

# Load historical data from SQLite
def load_historical_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
    return df

# Compute indicators
def compute_indicators(df):
    df["MA_200"] = df["close"].rolling(window=200).mean()
    df["RSI"] = RSIIndicator(df["close"], window=14).rsi()
    df["ADX"] = ADXIndicator(df["high"], df["low"], df["close"], window=14).adx()
    macd = MACD(df["close"])
    df["MACD"] = macd.macd()
    df["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    df["OBV"] = OnBalanceVolumeIndicator(df["close"], df["volume"]).on_balance_volume()
    return df

# Classify market state
def classify_market_state(df):
    conditions = [
        (df["close"] > df["MA_200"]) & (df["RSI"] > 50) & (df["ADX"] > 25),  # Bullish
        (df["close"] < df["MA_200"]) & (df["RSI"] < 50) & (df["ADX"] > 25),  # Bearish
    ]
    choices = ["Bull", "Bear"]
    df["Market_State"] = "Ranging"  # Default
    df.loc[conditions[0], "Market_State"] = choices[0]
    df.loc[conditions[1], "Market_State"] = choices[1]
    return df

# Log market state
def log_market_state(df):
    df[["timestamp", "Market_State"]].to_csv(MARKET_STATE_LOG, mode='a', header=False, index=False)

# Backup database & log
def backup_data():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_db = f"backup_{timestamp}.db"
    backup_log = f"backup_{timestamp}.csv"
    pd.read_sql(f"SELECT * FROM {TABLE_NAME}", sqlite3.connect(DB_PATH)).to_csv(backup_log, index=False)
    with open(DB_PATH, 'rb') as src, open(backup_db, 'wb') as dst:
        dst.write(src.read())

# Main execution flow
def main():
    init_db()
    df_live = fetch_live_data()
    store_data(df_live)
    df_historical = load_historical_data()
    df_combined = pd.concat([df_historical, df_live]).drop_duplicates()
    df_combined = compute_indicators(df_combined)
    df_classified = classify_market_state(df_combined)
    log_market_state(df_classified)
    backup_data()

if __name__ == "__main__":
    main()

