import os
import time
import requests
import pandas as pd
from binance.client import Client
from ta.trend import EMAIndicator

# Telegram Info
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Binance Client
client = Client()

# Timeframes
TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1d']

# Get Symbols
def get_usdt_symbols():
    exchange_info = client.get_exchange_info()
    symbols = [s['symbol'] for s in exchange_info['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
    return symbols[:20]

# Get Data
def get_klines(symbol, interval, limit=100):
    data = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(data, columns=["Time", "Open", "High", "Low", "Close", "Volume", "CloseTime", "QuoteAssetVolume", "Trades", "TakerBuyBase", "TakerBuyQuote", "Ignore"])
    df = df[["Time", "Open", "High", "Low", "Close", "Volume"]].astype(float)
    return df

# Check EMA Compression
def check_ema_compression(df):
    df['EMA20'] = EMAIndicator(close=df['Close'], window=20).ema_indicator()
    df['EMA50'] = EMAIndicator(close=df['Close'], window=50).ema_indicator()
    df['EMA100'] = EMAIndicator(close=df['Close'], window=100).ema_indicator()
    df['EMA200'] = EMAIndicator(close=df['Close'], window=200).ema_indicator()
    latest = df.iloc[-1]
    ema_vals = [latest['EMA20'], latest['EMA50'], latest['EMA100'], latest['EMA200']]
    return max(ema_vals) - min(ema_vals) < 0.2

# Send Signal
def send_signal(symbol, tf):
    message = f"📊 Signal: {symbol} ({tf})\nEMA Compression Detected"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Error sending message:", e)

# Main Loop
def run_bot():
    print("🚀 AltTrendBot चालू आहे... Real-time सिग्नल शोधतोय.")
    while True:
        for symbol in get_usdt_symbols():
            for tf in TIMEFRAMES:
                try:
                    print(f"⏳ Checking {symbol} - {tf}")
                    df = get_klines(symbol, tf)
                    if check_ema_compression(df):
                        send_signal(symbol, tf)
                except Exception as e:
                    print(f"Error: {symbol} {tf} -", e)
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
