import os
import pandas as pd

# ✅ Define the correct breakout log file path
LOG_FILE = os.path.expanduser("~/Documents/breakout_log.csv")

# ✅ Ensure the file exists
if not os.path.exists(LOG_FILE):
    print("❌ No breakout log file found. Run the bot first!")
    exit()

# ✅ Correct column headers based on log format
columns = ["timestamp", "symbol", "price", "RSI", "volume", "MA20", "MA50", "ATR"]

# ✅ Load entire breakout log
df = pd.read_csv(
    LOG_FILE,
    names=columns, 
    header=None,
    parse_dates=["timestamp"],
    dtype={"symbol": str, "price": float, "RSI": float, "volume": float, "MA20": float, "MA50": float, "ATR": float}
)

# ✅ Drop invalid timestamps
df.dropna(subset=["timestamp"], inplace=True)

# ✅ Ensure timestamps are sorted
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
df = df.sort_values(by="timestamp", ascending=True)

# ✅ Debugging Output
print(f"🕒 Newest breakout timestamp: {df['timestamp'].max()}")
print(f"🕒 Oldest breakout timestamp: {df['timestamp'].min()}")
print(f"✅ Total Breakouts in Dataset: {len(df)}")

# ✅ Ensure previous high exists before calculating success
if "previous_high" not in df.columns:
    df["previous_high"] = df.groupby("symbol")["price"].shift(1)

# ✅ Calculate breakout success rate
df["success"] = df["previous_high"].notna() & (df["price"] > df["previous_high"])

# ✅ Define Stop-Loss & Target Prices (Adjust as Needed)
df["target_price"] = df["price"] * 1.03  # 3% profit target
df["stop_loss"] = df["price"] * 0.97  # 3% stop loss

# ✅ Determine if trade hit target or stop-loss
df["hit_target"] = df["price"] >= df["target_price"]
df["hit_stop"] = df["price"] <= df["stop_loss"]

# ✅ Calculate profit per trade
df["profit"] = df["hit_target"] * (df["target_price"] - df["price"]) - df["hit_stop"] * (df["price"] - df["stop_loss"])

# ✅ Calculate total profit and win rate
total_profit = df["profit"].sum()
win_rate = df["hit_target"].mean() * 100

# ✅ Print Updated Statistics
print("\n📊 **Full Breakout Performance & Profitability Summary**")
print(f"🔹 Total Breakouts Analyzed: {len(df)}")
print(f"✅ Winning Trades: {df['hit_target'].sum()} ({win_rate:.2f}%)")
print(f"❌ Stopped Out Trades: {df['hit_stop'].sum()}")
print(f"💰 Estimated Total Profit: {total_profit:.4f} (assumes 1 unit per trade)")

# ✅ Display best-performing assets
best_assets = df[df["success"] == True]["symbol"].value_counts().head(5)
if not best_assets.empty:
    print("\n🚀 Best Performing Assets:")
    print(best_assets)

# ✅ Display worst-performing assets
worst_assets = df[df["success"] == False]["symbol"].value_counts().head(5)
if not worst_assets.empty:
    print("\n⚠️ Worst Performing Assets:")
    print(worst_assets)

# ✅ Save Analysis to CSV
output_file = os.path.expanduser("~/Documents/full_breakout_analysis.csv")
df.to_csv(output_file, index=False)
print(f"\n📂 Full Analysis saved to '{output_file}'")

