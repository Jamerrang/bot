import ccxt
import pandas as pd
import time
from datetime import datetime, timezone

# Initialize Kraken API
exchange = ccxt.kraken({
    'rateLimit': 1000,
    'enableRateLimit': True
})

# Simulate Breakout Strategy for Backtesting
def backtest(symbol, timeframe='5m', limit=50, threshold=1.5, take_profit_pct=1.02, stop_loss_pct=0.98):
    """Backtest breakout strategy with exit rules (take profit and stop loss)."""
    
    # Fetch historical data
    df = pd.DataFrame(exchange.fetch_ohlcv(symbol, timeframe, limit=limit), columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Calculate ATR (simplified)
    df['ATR'] = df['high'] - df['low']
    max_high = df['high'].max()
    latest_price = df['close'].iloc[-1]
    
    # Simple breakout detection: Latest price > max high
    print(f"Checking breakout for {symbol}... Latest Price: {latest_price}, Max High: {max_high}")
    if latest_price > max_high:
        print(f"🚀 Breakout detected for {symbol} at {latest_price}")
        
        # Track the trade: Entry Price
        entry_price = latest_price
        
        # Simulate the trade by checking if price hits take profit or stop loss
        trade_pnl = 0
        for i in range(len(df) - 1, 0, -1):
            close_price = df['close'].iloc[i]
            
            # Check if price hits take profit or stop loss
            if close_price >= entry_price * take_profit_pct:
                trade_pnl = close_price - entry_price
                print(f"✅ Take profit triggered for {symbol} at {close_price}. PnL: {trade_pnl}")
                break
            elif close_price <= entry_price * stop_loss_pct:
                trade_pnl = close_price - entry_price
                print(f"❌ Stop loss triggered for {symbol} at {close_price}. PnL: {trade_pnl}")
                break
        
        # If no exit happens, assume a flat position with no profit or loss
        if trade_pnl == 0:
            print(f"⏸ No exit condition met for {symbol}, holding the position till the end.")
        
        return trade_pnl
    return 0

# Backtest for BTC/USDT and ETH/USDT
symbols = ['BTC/USDT', 'ETH/USDT']
results = []
total_pnl = 0  # To track the total profit/loss across all trades

for symbol in symbols:
    print(f"\nTesting {symbol}...")
    pnl = backtest(symbol)
    total_pnl += pnl
    results.append({
        "symbol": symbol,
        "pnl": pnl
    })
    time.sleep(1)  # Simulate time delay for each pair

# Log the results
df_results = pd.DataFrame(results)
df_results.to_csv('backtest_results_with_debug.csv', index=False)

# Print summary results
print("\nBacktest results saved to 'backtest_results_with_debug.csv'")
print(f"\nTotal Profit/Loss across all symbols: {total_pnl}")
