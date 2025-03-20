import ccxt
import pandas as pd
from datetime import datetime, timezone

# Initialize Binance API
binance = ccxt.binance()

# Define symbol and timeframe
symbol = 'BTC/USDT'
timeframe = '1d'

# Fetch the most recent completed daily candle
since = binance.parse8601(datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z"))
ohlcv = binance.fetch_ohlcv(symbol, timeframe, since=since, limit=1)

if ohlcv:
    # Convert to DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

    # Save to CSV
    file_path = "/Users/jameserskine/Documents/trading_bot/datasets/latest_binance_data.csv"
    df.to_csv(file_path, index=False)
    print(f"✅ Binance data saved to {file_path}")

else:
    print("❌ No Binance data available.")
