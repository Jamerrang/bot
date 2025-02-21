import os
import pandas as pd
import ccxt
import numpy as np

# ✅ Define the breakout log file path
LOG_FILE = os.path.expanduser("~/Documents/breakout_log.csv")

# ✅ Ensure the file exists
if not os.path.exists(LOG_FILE):
    print("❌ No breakout log file found. Run the bot first!")
    exit()

# ✅ Load breakout data
columns = ["timestamp", "symbol", "price", "RSI", "volume", "MA20", "MA50", "ATR"]
df = pd.read_csv(
    LOG_FILE,
    names=columns,
    header=None,
    parse_dates=["timestamp"],
    dtype={"symbol": str, "price": float, "RSI": float, "volume": float, "MA20": float, "MA50": float, "ATR": float}
)
# ✅ Only analyze the last 100 breakouts to speed up processing
df = df.tail(100)


# ✅ Drop rows where timestamp parsing failed
df.dropna(subset=["timestamp"], inplace=True)

# ✅ Ensure timestamps are in UTC
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

# ✅ Define Stop-Loss & Target Prices
df["target_price"] = df["price"] * 1.05  # Example: 5% profit target
df["stop_loss"] = df["price"] * 0.98  # Example: 2% stop loss

# ✅ Initialize Kraken API for fetching historical data
exchange = ccxt.kraken()

def check_trade_outcome(symbol, breakout_time, breakout_price, target_price, stop_loss):
    """Fetch future OHLCV data to determine if the breakout hit the target price or stop loss."""
    try:
        # Fetch OHLCV (1-hour candles) for 4 hours after breakout
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', since=int(breakout_time.timestamp() * 1000), limit=4)
        df_ohlcv = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_ohlcv['timestamp'] = pd.to_datetime(df_ohlcv['timestamp'], unit='ms')

        if df_ohlcv.empty:
            return False, False  # No price data available
        
        # ✅ Check if target price or stop loss was hit
        max_high = df_ohlcv['high'].max()  # Highest price in next 4 hours
        min_low = df_ohlcv['low'].min()  # Lowest price in next 4 hours

        hit_target = max_high >= target_price
        hit_stop = min_low <= stop_loss

        return hit_target, hit_stop
    except Exception as e:
        print(f"❌ Error fetching OHLCV for {symbol}: {e}")
        return False, False

# ✅ Apply function to check each breakout
df['hit_target'], df['hit_stop'] = zip(*df.apply(lambda row: check_trade_outcome(
    row['symbol'], row['timestamp'], row['price'], row['target_price'], row['stop_loss']), axis=1))

# ✅ Calculate profit per trade
df["profit"] = df["hit_target"] * (df["target_price"] - df["price"]) - df["hit_stop"] * (df["price"] - df["stop_loss"])

# ✅ Calculate total profit and win rate
total_profit = df["profit"].sum()
win_rate = df["hit_target"].mean() * 100  # % of trades that hit target price

print(f"✅ Total Profit: {total_profit:.2f}")
print(f"✅ Winning Trades: {df['hit_target'].sum()} ({win_rate:.2f}%)")

# ✅ Summary Statistics
print("\n📊 **Breakout Performance & Profitability Summary**")
print(f"🔹 Total Breakouts: {len(df)}")
print(f"✅ Winning Trades: {df['hit_target'].sum()} ({win_rate:.2f}%)")
print(f"❌ Stopped Out Trades: {df['hit_stop'].sum()}")
print(f"💰 Estimated Total Profit: {total_profit:.4f} (assumes 1 unit per trade)")

# ✅ Ensure timestamps are properly formatted
df['timestamp'] = df['timestamp'].astype(str)

# ✅ Save Analysis to CSV
output_file = os.path.expanduser("~/Documents/breakout_analysis.csv")
df.to_csv(output_file, index=False)

print(f"\n📂 Analysis saved to '{output_file}'")

