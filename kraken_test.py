import os
import time
import ccxt
import pandas as pd
import talib
    
# ✅ Load API keys from environment variables
api_key = os.getenv("KRAKEN_API_KEY")
api_secret = os.getenv("KRAKEN_API_SECRET")

if not api_key or not api_secret:
    print("❌ API keys are missing! Set them in the terminal.")
    exit()

# ✅ Initialize Kraken API
exchange = ccxt.kraken({
    'apiKey': api_key,
    'secret': api_secret,
})

# ✅ Trading Parameters
TRAILING_STOP_PERCENT = 5
RISK_PER_TRADE = 0.02
LOG_FILE = os.path.expanduser("~/Documents/breakout_log.csv")

# ✅ Fetch Historical OHLCV Data
def get_ohlcv(symbol, timeframe='5m', limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"❌ Error fetching OHLCV for {symbol}: {e}")
        return None
    
# ✅ Calculate Technical Indicators
def calculate_indicators(df):
    if df is None or len(df) < 20:
        print("⚠️ Not enough data to calculate indicators.")
        return None

    df['RSI'] = talib.RSI(df['close'], timeperiod=14)
    df['MA20'] = talib.SMA(df['close'], timeperiod=20)
    df['MA50'] = talib.SMA(df['close'], timeperiod=50)
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    
    if 'ATR' not in df.columns or df['ATR'].isna().all():
        print("❌ ATR calculation failed. Skipping this asset.")
        return None

    return df
    
# ✅ Fetch Current Price
def get_current_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"❌ Error fetching price for {symbol}: {e}")
        return None 
        
# ✅ Log Breakout to File
def log_breakout(symbol, entry_price):
    try:
        target_price = round(entry_price * 1.05, 6)
        stop_loss = round(entry_price * 0.98, 6)
        timestamp = pd.Timestamp.utcnow()
        log_entry = f"{timestamp},{symbol},{entry_price},{target_price},{stop_loss},N/A\n"
        
        # Print log entry to check it
        print(f"Logging Breakout: {log_entry}")

        with open(LOG_FILE, "r") as f:
            lines = f.readlines() 
        
        for line in lines[-10:]:
            if symbol in line and "N/A" in line:
                print(f"⚠️ Duplicate breakout for {symbol}, already recorded.")
                return
    
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    
        print(f"✅ Breakout Logged: {symbol} at {entry_price} | Target: {target_price} | Stop: {stop_loss}")
        
        time.sleep(60)
        post_breakout_price = get_current_price(symbol)
    
        retries = 3
        while post_breakout_price is None and retries > 0:
            print(f"⚠️ Retrying post-breakout price fetch for {symbol} ({3 - retries} attempts left)...")
            time.sleep(10)
            post_breakout_price = get_current_price(symbol)
            retries -= 1  
        
        if post_breakout_price is None:
            print(f"⚠️ Warning: Could not fetch post-breakout price for {symbol}. Keeping 'N/A'.")
            return

        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        
        updated = False
        for i in range(len(lines) - 1, -1, -1):
            if symbol in lines[i] and "N/A" in lines[i]:
                parts = lines[i].strip().split(',')
                if len(parts) == 6:
                    parts[-1] = str(post_breakout_price)  # Update post-breakout price
                    lines[i] = ','.join(parts) + '\n'
                    updated = True
                    break

        if updated:
            with open(LOG_FILE, "w") as f:
                f.writelines(lines)

            print(f"✅ Updated log with post-breakout price: {post_breakout_price}")

    except Exception as e:
        print(f"❌ Error logging breakout: {e}")

# ✅ Confirm Breakout with Dynamic Adjustments
def confirm_breakout(symbol):
    timeframes = ['5m', '15m', '1h', '4h']
    confirmations = 0
    breakout_price = None
            
    # Correctly initialize the lists for ATR, RSI, and volume
    atr_values = []
    rsi_values = []
    volume_values = []
        
    # Dynamically adjust minimum confirmations based on ATR and volume
    min_confirmations = 4
    dynamic_atr_multiplier = 1
    dynamic_volume_multiplier = 1
            
    # Fetch OHLCV data for each timeframe
    for tf in timeframes:
        df = get_ohlcv(symbol, timeframe=tf)   
        if df is None or len(df) < 50:
            continue
                
        df = calculate_indicators(df)
        if df is None or 'ATR' not in df.columns:
            print(f"⚠️ Skipping {symbol} on {tf} due to missing ATR data.")
            continue
        
        recent_high = df['high'].iloc[-2]
        current_price = df['close'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]  # Example moving average
        
        atr_values.append(df['ATR'].iloc[-1])
        rsi_values.append(df['RSI'].iloc[-1])
        volume_values.append(df['volume'].iloc[-1])
    
        # Check if the current price is greater than the recent high and also if it's above the MA20
        if current_price > recent_high and current_price > ma20:
            confirmations += 1
            breakout_price = current_price

    # If no ATR values found, skip the symbol
    if not atr_values:
        print(f"❌ Skipping {symbol} - No valid ATR values found.")
        return False, None
    
    # Dynamically adjust minimum confirmations based on ATR (volatility)
    avg_atr = sum(atr_values) / len(atr_values) if atr_values else 0
    avg_rsi = sum(rsi_values) / len(rsi_values) if rsi_values else 0
    avg_volume = sum(volume_values) / len(volume_values) if volume_values else 0
    
    # Adjust confirmation threshold based on ATR (volatility)
    if avg_atr > 0.05:  # High volatility (adjust the threshold as needed)
        min_confirmations = 2  # Fewer confirmations required for high volatility
    elif avg_atr < 0.005:  # Low volatility
        min_confirmations = 6  # More confirmations required for low volatility
    
    # Adjust confirmation threshold based on volume
    if avg_volume > 5000000:  # High volume (adjust the threshold as needed)
        min_confirmations = 2  # Fewer confirmations required for high volume
    elif avg_volume < 500000:  # Low volume
        min_confirmations = 6  # More confirmations required for low volume
        
    print(f"✅ Dynamic Confirmation Adjustments: ATR: {avg_atr}, Volume: {avg_volume}")
    print(f"✅ Confirmations: {confirmations}, Minimum Required: {min_confirmations}")
        
    # Compare confirmations with the dynamic min_confirmations
    return confirmations >= min_confirmations, breakout_price

# ✅ Main Trading Loop
def main():
    print("✅ Starting Breakout Bot...")
    
    try:
        symbols = exchange.load_markets().keys()
        tradable_symbols = [s for s in symbols if any(quote in s for quote in ['/USD', '/USDT', '/USDC'])]
        print(f"✅ Found {len(tradable_symbols)} tradable assets.")
    except Exception as e:
        print(f"❌ Error loading markets: {e}")
        return
        
    while True:
        print("🔄 Checking for breakouts...")
    
        for symbol in tradable_symbols:
            print(f"🔍 Checking {symbol}...")
    
            breakout, price = confirm_breakout(symbol)
    
            if breakout:
                print(f"🚀 Breakout Confirmed: {symbol} at {price}")
                log_breakout(symbol, price)
    
        print("⏳ Sleeping for 60 seconds before next check...")
        time.sleep(60)

# ✅ Run Script
if __name__ == "__main__":
    main()

