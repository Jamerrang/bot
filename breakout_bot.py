import ccxt
import time
from datetime import datetime, timezone
import pandas as pd
import threading

# Initialize Kraken API
exchange = ccxt.kraken({
    'rateLimit': 1000,
    'enableRateLimit': True
})

# Fetch all trading pairs from Kraken, ensuring more pairs are included
def get_all_trading_pairs():
    """Fetch all available trading pairs from Kraken and include both USDT and USD pairs."""
    try:
        markets = exchange.load_markets()
        return [pair for pair in markets if pair.endswith(("/USDT", "/USD"))]  # Include USD pairs too
    except Exception as e:
        print(f"❌ Error fetching trading pairs: {e}")
        return []

# Use all available USDT/USD pairs instead of hardcoding
trading_pairs = get_all_trading_pairs()
print(f"✅ Loaded {len(trading_pairs)} trading pairs from Kraken.")

tracking_intervals = [300, 900, 3600]  # 5 min, 15 min, 1 hour
breakout_data = []
breakout_threshold = 50  # How many past candles to check for breakouts

def fetch_latest_price(symbol):
    """Fetches the latest price for a given trading pair."""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"❌ Error fetching price for {symbol}: {e}")
        return None

def fetch_historical_high(symbol, timeframe="5m", limit=breakout_threshold):
    """Fetches the highest price from the last 'N' candles."""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        highs = [candle[2] for candle in ohlcv]  # Extract high prices
        return max(highs) if highs else None
    except Exception as e:
        print(f"❌ Error fetching OHLCV for {symbol}: {e}")
        return None

def log_breakout(symbol, breakout_price):
    """Logs the breakout event and schedules price tracking."""
    timestamp = datetime.now(timezone.utc).isoformat()
    breakout_record = {
        "timestamp": timestamp,
        "symbol": symbol,
        "breakout_price": breakout_price,
        "post_prices": {interval: None for interval in tracking_intervals}
    }
    breakout_data.append(breakout_record)
    print(f"[{timestamp}] 🚀 Breakout detected: {symbol} at {breakout_price}")

    for interval in tracking_intervals:
        threading.Timer(interval, fetch_post_breakout_price, args=(breakout_record, interval)).start()
        
def fetch_post_breakout_price(record, interval):
    """Fetches post-breakout prices after a set time interval."""
    post_price = fetch_latest_price(record["symbol"])
    record["post_prices"][interval] = post_price
    print(f"[{datetime.now(timezone.utc).isoformat()}] 🕒 {interval // 60} min post-breakout price for {record['symbol']}: {post_price}")
    
def save_to_csv():
    """Saves breakout and post-breakout data to CSV."""
    df = pd.DataFrame(breakout_data)
    df.to_csv("/Users/jameserskine/Documents/breakout_log.csv", index=False)
    print("✅ Breakout data saved to CSV.")
    
# Continuous Execution Loop
while True:
    print(f"\n🔄 [{datetime.now(timezone.utc).isoformat()}] Checking all trading pairs ({len(trading_pairs)})...\n")

    for pair in trading_pairs:
        latest_price = fetch_latest_price(pair)
        historical_high = fetch_historical_high(pair)
        
        if latest_price and historical_high:
            print(f"🔍 Checking {pair}: Price={latest_price}, Historical High={historical_high}")
            # Relaxing the breakout conditions
            if latest_price > historical_high:
                log_breakout(pair, latest_price)
            else:
                print(f"❌ No breakout detected for {pair}.")
    
    # Sleep before next cycle
    print("⏳ Waiting 60 seconds before the next check...\n")
    time.sleep(60)

