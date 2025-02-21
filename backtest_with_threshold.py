import ccxt
import time
import pandas as pd

# Initialize Kraken API
exchange = ccxt.kraken({
    'rateLimit': 1000,
    'enableRateLimit': True
})

# Define symbols to test
symbols = ["BTC/USDT", "ETH/USDT"]

# Track results
backtest_results = []

# Fetch historical data for a given symbol
def fetch_historical_data(symbol, timeframe='5m', limit=200):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    return pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

# Run backtest for each symbol
for symbol in symbols:
    print(f"Testing {symbol}...")

    # Fetch historical data
    df = fetch_historical_data(symbol)
    max_high = df['high'].max()
    latest_price = exchange.fetch_ticker(symbol)['last']

    # Breakout Threshold (0.1% above the max high)
    breakout_threshold = max_high * 1.001

    # Check if price exceeds breakout threshold
    if latest_price > breakout_threshold:
        print(f"🚀 Breakout detected for {symbol}! Latest Price: {latest_price}, Max High: {max_high}")
        backtest_results.append({
            'symbol': symbol,
            'breakout_price': latest_price,
            'status': 'Success'
        })
    else:
        print(f"❌ No breakout detected for {symbol}. Latest Price: {latest_price}, Max High: {max_high}")
        backtest_results.append({
            'symbol': symbol,
            'breakout_price': latest_price,
            'status': 'No Breakout'
        })

    time.sleep(1)  # To avoid rate-limiting issues

# Save results to CSV
df_results = pd.DataFrame(backtest_results)
df_results.to_csv('/Users/jameserskine/Documents/backtest_results_with_threshold.csv', index=False)
print(f"Backtest results saved to 'backtest_results_with_threshold.csv'")

# Print total profit/loss
total_profit_loss = sum([1 if result['status'] == 'Success' else 0 for result in backtest_results])
print(f"Total Profit/Loss across all symbols: {total_profit_loss}")
