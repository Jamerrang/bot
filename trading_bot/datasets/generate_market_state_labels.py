import pandas as pd
import numpy as np
import ccxt
from ta.trend import ADXIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator

# Load historical data instead of fetching from Binance
def load_historical_data(file_path):
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp')
    return df

# Compute technical indicators
def compute_indicators(df):
    df['200_MA'] = df['close'].rolling(window=200, min_periods=1).mean()
    df['RSI'] = RSIIndicator(df['close'], window=14).rsi().ffill().bfill()
    df['ADX'] = ADXIndicator(df['high'], df['low'], df['close'], window=14).adx().ffill().bfill()
    df['MACD_Histogram'] = MACD(df['close']).macd_diff().ffill().bfill()
    df['ATR'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    df['ATR'] = df['ATR'].replace(0, np.nan).ffill().bfill()
    df['OBV'] = OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume().ffill().bfill()
    
    # Ensure no zeros in ADX (replace with NaN and forward fill)
    df.loc[df['ADX'] == 0.0, 'ADX'] = np.nan
    df['ADX'] = df['ADX'].ffill().bfill()
    return df

# Define market state classification
def classify_market_state(df):
    df['Market_State'] = 'Unknown'

    bull_mask = (
        (df['close'] > df['200_MA']) & 
        (df['ADX'] > 20) &  # Lowered ADX threshold to capture earlier trends
        (df['RSI'] > 55) &  # Adjusted RSI for more aggressive Bull detection
        (df['MACD_Histogram'] > 0) & 
        (df['volume'] > df['volume'].rolling(window=30).mean())  # Extended volume window
    )
    
    bear_mask = (
        (df['close'] < df['200_MA']) & 
        (df['ADX'] > 20) &  # Lowered ADX threshold for earlier Bear trends
        (df['RSI'] < 45) & 
        (df['MACD_Histogram'] < 0) & 
        (df['OBV'] < df['OBV'].rolling(window=30).mean())  # Extended OBV window
    )
    
    ranging_mask = (
        (df['close'].between(df['200_MA'] * 0.97, df['200_MA'] * 1.03)) &  # Tightened range to better capture ranging
        (df['ADX'] < 18) &  # Lowered ADX further for better ranging detection
        (df['ATR'] < df['ATR'].rolling(window=50).mean())  # ATR check to filter volatile trends
    )

    df.loc[bull_mask, 'Market_State'] = 'Bull'
    df.loc[bear_mask, 'Market_State'] = 'Bear'
    df.loc[ranging_mask, 'Market_State'] = 'Ranging'
    
    # Reclassify Unknown states based on previous market trends
    df['Market_State'] = df['Market_State'].replace('Unknown', np.nan)
    df['Market_State'].fillna(method='ffill', inplace=True)

    return df

# Highlight questionable classifications
def highlight_questionable(df):
    df['Questionable'] = df[['RSI', 'ADX', 'MACD_Histogram', 'ATR']].isna().any(axis=1)
    df['Questionable'] = df['Questionable'] & (df['Market_State'] == 'Unknown')
    return df

# Main function
def main():
    file_path = '/Users/jameserskine/Documents/trading_bot/datasets/market_state_labeled.csv'
    df = load_historical_data(file_path)
    df = compute_indicators(df)
    df = classify_market_state(df)
    df = highlight_questionable(df)

    df.to_csv(file_path, index=False)

    print(f"Dataset saved to {file_path}. Review questionable classifications manually.")

if __name__ == '__main__':
    main()

