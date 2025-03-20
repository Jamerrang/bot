import pandas as pd
import ccxt
import talib
from datetime import datetime, timedelta, timezone

# ✅ Load dataset
labeled_file = "~/Documents/trading_bot/datasets/market_state_labeled.csv"
labeled = pd.read_csv(labeled_file)

# ✅ Fix timestamp parsing issue
def parse_timestamp(ts):
    """Convert timestamp to datetime while handling different formats."""
    try:
        return pd.to_datetime(ts, format="ISO8601", utc=True)
    except ValueError:
        return pd.to_datetime(ts.split("+")[0], utc=True)  # Remove timezone manually

labeled["timestamp"] = labeled["timestamp"].apply(parse_timestamp)

# ✅ REMOVE incorrect March 18 live row (07:59:57)
labeled = labeled[~labeled["timestamp"].astype(str).str.contains("07:59:57")]

# ✅ REMOVE duplicate March 17 entries (keep Binance data)
labeled["date"] = labeled["timestamp"].dt.date  # Extract just the date
labeled = labeled.drop_duplicates(subset=["date"], keep="last").drop(columns=["date"])

# ✅ Identify missing dates, but **do not fetch March 18 yet** since Binance has not closed the daily candle
today_utc = datetime.now(timezone.utc).date()
missing_dates = [datetime(2025, 3, 17).date()]

if today_utc > datetime(2025, 3, 18).date():
    missing_dates.append(datetime(2025, 3, 18).date())

existing_dates = set(labeled["timestamp"].dt.date.values)
dates_to_fetch = [d for d in missing_dates if d not in existing_dates]

if not dates_to_fetch:
    print("✅ No missing data detected. Market state is up to date.")
    exit()

print(f"📡 Fetching missing OHLCV for: {dates_to_fetch} from Binance")

# **Fetch OHLCV from Binance**
def fetch_binance_data(start_date, end_date):
    print(f"📡 Fetching OHLCV data from Binance ({start_date} to {end_date})...")
    try:
        binance = ccxt.binance()
        since = binance.parse8601(f"{start_date}T00:00:00Z")
        ohlcv = binance.fetch_ohlcv('BTC/USDT', '1d', since=since, limit=(end_date - start_date).days + 1)

        if not ohlcv:
            print("❌ Binance returned no data.")
            return None

        new_rows = []
        for row in ohlcv:
            timestamp = datetime.utcfromtimestamp(row[0] / 1000).replace(tzinfo=timezone.utc)
            if timestamp.date() in dates_to_fetch:
                new_rows.append({
                    "timestamp": timestamp,
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5]
                })

        print(f"✅ Fetched {len(new_rows)} rows from Binance.")
        return pd.DataFrame(new_rows)

    except Exception as e:
        print(f"⚠️ Binance fetch error: {e}")
        return None

# **Fetch data from Binance**
new_data_df = fetch_binance_data(min(dates_to_fetch), max(dates_to_fetch) + timedelta(days=1))

if new_data_df is not None:
    new_data_df["timestamp"] = pd.to_datetime(new_data_df["timestamp"], utc=True)

    # ✅ Drop any remaining duplicates **before** appending
    labeled["date"] = labeled["timestamp"].dt.date
    new_data_df["date"] = new_data_df["timestamp"].dt.date
    labeled = labeled[~labeled["date"].isin(new_data_df["date"])].drop(columns=["date"])
    new_data_df = new_data_df.drop(columns=["date"])

    # ✅ Append new Binance-fetched data
    labeled = pd.concat([labeled, new_data_df], ignore_index=True)

else:
    print("❌ No new OHLCV data available from Binance.")

# ✅ Ensure timestamps are sorted correctly **after** updates
labeled = labeled.sort_values("timestamp").reset_index(drop=True)

# **Compute Technical Indicators**
labeled["200_MA"] = labeled["close"].rolling(window=200).mean()
labeled["RSI"] = talib.RSI(labeled["close"], timeperiod=14)
labeled["ADX"] = talib.ADX(labeled["high"], labeled["low"], labeled["close"], timeperiod=14)
labeled["MACD_Histogram"] = talib.MACD(labeled["close"], fastperiod=12, slowperiod=26, signalperiod=9)[2]
labeled["ATR"] = talib.ATR(labeled["high"], labeled["low"], labeled["close"], timeperiod=14)
labeled["OBV"] = talib.OBV(labeled["close"], labeled["volume"])

# ✅ Market state classification
def classify_market(row):
    if row["RSI"] > 70:
        return "Bull"
    elif row["RSI"] < 30:
        return "Bear"
    else:
        return "Ranging"

labeled["market_state"] = labeled.apply(classify_market, axis=1)

# ✅ Convert timestamps to strings before saving
labeled["timestamp"] = labeled["timestamp"].astype(str)

# ✅ Save updated dataset
labeled.to_csv("~/Documents/trading_bot/datasets/market_state_labeled.csv", index=False)

print("✅ Market state updated successfully:")
print(labeled.tail(5))
