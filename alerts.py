import pandas as pd
import requests

TELEGRAM_BOT_TOKEN = "7978817256:AAFF-ZMYSEFSNGiJxumkRfjrMsj3UI1AT7Y"
CHAT_ID = 6363167802

def send_telegram_message(symbol, price, df):
    if isinstance(df, dict):
        df = pd.DataFrame(df)  # ✅ Convert dictionary to DataFrame

    latest_close = df['close'].iloc[-1]
    high = df['high'].iloc[-1]  # ✅ Ensure this column exists

    message = (
        f"🚀 {symbol} breakout! 📈\n"
        f"Price: {price}\n"
        f"Check Kraken for details.\n\n"
        f"🔹 RSI: {df['RSI'].iloc[-1]:.2f}\n"
        f"🔹 MA20: {df['MA20'].iloc[-1]:.2f}, MA50: {df['MA50'].iloc[-1]:.2f}\n"
        f"🔹 % Change: {(latest_close / high - 1) * 100:.2f}%"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=payload)
    return response.json()  # ✅ For debugging purposes

# ✅ Test the function only when running the script directly
if __name__ == "__main__":
    send_telegram_message('TEST/USD', 99999, {
        'close': [99999], 'high': [100000], 'RSI': [70], 'MA20': [98000], 'MA50': [97000]
    })


