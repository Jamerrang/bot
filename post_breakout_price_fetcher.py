import pandas as pd
import os

# Define the path for the breakout log
breakout_log_path = os.path.expanduser("~/Documents/breakout_log.csv")

# Load the breakout log
if os.path.exists(breakout_log_path):
    df = pd.read_csv(breakout_log_path)
    print(df.tail(10))  # Display the last 10 entries for validation
else:
    print(f"Error: {breakout_log_path} not found.")
