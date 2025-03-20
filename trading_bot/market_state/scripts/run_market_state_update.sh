#!/bin/bash

LOCK_FILE="/tmp/market_state_update.lock"
LOG_FILE="$HOME/Documents/trading_bot/logs/market_state_update.log"

# Prevent duplicate execution
if [ -e "$LOCK_FILE" ]; then
    echo "⚠ Process already running! Exiting."
    exit 1
fi
touch "$LOCK_FILE"

# Activate virtual environment
source ~/Documents/myenv/bin/activate

echo "🚀 Market state update started on $(date)" | tee -a "$LOG_FILE"

# Ensure lock file is removed on exit (even if script crashes)
trap "rm -f $LOCK_FILE" EXIT

# Function to check if Binance daily data is available
check_binance_data() {
    python3 <<EOF_PYTHON
import ccxt
from datetime import datetime, timezone

binance = ccxt.binance()
symbol = 'BTC/USDT'
since = binance.parse8601(datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z"))
ohlcv = binance.fetch_ohlcv(symbol, '1d', since=since, limit=1)

if ohlcv:
    print("✅ Binance data available.")
else:
    print("❌ Binance data not yet available.")
EOF_PYTHON
}

# Retry until Binance's daily candle is closed
while true; do
    result=$(check_binance_data)
    echo "$result" | tee -a "$LOG_FILE"

    if [[ "$result" == *"✅ Binance data available."* ]]; then
        break  # Exit loop when data is available
    fi

    echo "⚠ Binance daily candle not closed yet. Retrying in 1 hour..." | tee -a "$LOG_FILE"
    sleep 3600  # Wait 1 hour before retrying
done

# Remove today's entry
python3 ~/Documents/trading_bot/market_state/scripts/remove_todays_entry.py

# Run market state detection
python3 ~/Documents/trading_bot/market_state/scripts/generate_market_state_labels.py

# Compute missing indicators if needed
python3 ~/Documents/trading_bot/market_state/scripts/recompute_indicators.py

# Deactivate virtual environment
deactivate

# Verify that today's entry exists before finishing
TODAY=$(date -u +"%Y-%m-%d")
LAST_ENTRY=$(tail -n 1 ~/Documents/trading_bot/datasets/market_state_ready.csv | cut -d',' -f1)

if [[ "$LAST_ENTRY" != "$TODAY" ]]; then
    echo "❌ ERROR: Market state for $TODAY is missing! Re-running update..." | tee -a "$LOG_FILE"
    
    # Re-fetch Binance data and append today's entry
    python3 ~/Documents/trading_bot/market_state/scripts/fetch_latest_binance_data.py
    
    # Re-run indicator calculation
    python3 ~/Documents/trading_bot/market_state/scripts/recompute_indicators.py
fi

echo "✅ Market state updated successfully on $(date)" | tee -a "$LOG_FILE"
