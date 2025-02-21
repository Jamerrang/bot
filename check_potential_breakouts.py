import pandas as pd

# Load the breakout log
log_file = "~/Documents/breakout_log.csv"
df = pd.read_csv(log_file, names=["timestamp", "pair", "price"])

# Filter breakouts
print(df.tail(20))  # Show the last 20 entries
