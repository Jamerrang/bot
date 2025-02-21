import ccxt
import pandas as pd
import time
from datetime import datetime

# Initialize Kraken API
exchange = ccxt.kraken()

# Fetch all trading pairs from Kraken, ensuring more pairs are included
def get_all_trading_pairs():
    try:
        markets = exchange.load_markets()
        return [pair for pair in markets if pair.endswith(("/USDT", "/USD"))]
    except Exception as e:
        print(f"❌ Error fetching trading pairs: {e}")
        return []

# Use all available USDT/USD pairs instead of hardcoding
trading_pairs = get_all_trading_pairs()
print(f"✅ Loaded {len(trading_pairs)} trading pairs from Kraken.")

# Backtesting function for the last 24 hours
def backtest(symbol):
    print(f"Testing {symbol}...")

    # Fetch historical data for the last 24 hours (1-hour timeframe)
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=24)

    # Extract the closing prices and calculate percentage change
    closes = [candle[4] for candle in ohlcv]  # Close price is the 5th item
    price_change_percent = ((closes[-1] - closes[0]) / closes[0]) * 100
    print(f"Price change for {symbol} in the last 24 hours: {price_change_percent:.2f}%")

    # Breakout detection logic
    historical_high = max([candle[2] for candle in ohlcv])  # Highest high in the last 24 hours
    latest_price = closes[-1]  # Latest close price

    if latest_price > historical_high:
        print(f"🚀 Breakout detected for {symbol} at {latest_price} (Historical High: {historical_high})")
    else:
        print(f"❌ No breakout detected for {symbol}. Latest Price: {latest_price}, Historical High: {historical_high}")

    return price_change_percent

# Run the backtest for all trading pairs
results = []
for pair in trading_pairs:
    try:
        price_change = backtest(pair)
        results.append({'pair': pair, 'price_change_percent': price_change})
    except Exception as e:
        print(f"❌ Error testing {pair}: {e}")

# Save the results to a CSV file
df = pd.DataFrame(results)
df.to_csv('backtest_results_last_24_hours.csv', index=False)
print("✅ Backtest results saved to 'backtest_results_last_24_hours.csv'.")

