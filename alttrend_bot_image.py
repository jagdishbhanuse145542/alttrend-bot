import time
import requests
from binance.client import Client
from ta.trend import EMAIndicator
import pandas as pd
import matplotlib.pyplot as plt
import threading
import http.server
import socketserver
import os

# ✅ Telegram Bot Credentials (Render वर ENV VAR म्हणून द्यायचं)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ✅ Binance client
client = Client()

# ✅ Timeframes आणि Coins
TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1d']
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]

# ✅ Send text message
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# ✅ Send chart image
def send_chart(file_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(file_path, 'rb') as f:
        files = {"photo": f}
        data = {"chat_id": CHAT_ID}
        requests.post(url, data=data, files=files)

# ✅ Get historical candles
def get_klines(symbol, interval):
    try:
        data = client.get_klines(symbol=symbol, interval=interval, limit=100)
        df = pd.DataFrame(data, columns=[
            "Time", "Open", "High", "Low", "Close", "Volume",
            "Close_time", "Quote_asset_volume", "Number_of_trades",
            "Taker_buy_base", "Taker_buy_quote", "Ignore"
        ])
        df["Open"] = df["Open"].astype(float)
        df["High"] = df["High"].astype(float)
        df["Low"] = df["Low"].astype(float)
        df["Close"] = df["Close"].astype(float)
        return df
    except Exception as e:
        print(f"Error: {symbol} {interval} - {e}")
        return None

# ✅ Plot chart and save image
def plot_chart(df, symbol, tf):
    plt.figure(figsize=(10, 4))
    plt.plot(df['Close'], label='Close Price')
    plt.plot(df['ema20'], label='EMA 20')
    plt.plot(df['ema50'], label='EMA 50')
    plt.plot(df['ema100'], label='EMA 100')
    plt.plot(df['ema200'], label='EMA 200')
    plt.title(f"{symbol} - {tf} Chart")
    plt.legend()
    chart_file = f"chart_{symbol}_{tf}.png"
    plt.savefig(chart_file)
    plt.close()
    return chart_file

# ✅ Main scanning function
def scan():
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            print(f"⏳ Checking {symbol} - {tf}")
            df = get_klines(symbol, tf)
            if df is None:
                continue
            try:
                df['ema20'] = EMAIndicator(df['Close'], window=20).ema_indicator()
                df['ema50'] = EMAIndicator(df['Close'], window=50).ema_indicator()
                df['ema100'] = EMAIndicator(df['Close'], window=100).ema_indicator()
                df['ema200'] = EMAIndicator(df['Close'], window=200).ema_indicator()

                last = df.iloc[-1]
                d = abs(last['ema20'] - last['ema50']) + abs(last['ema50'] - last['ema100']) + abs(last['ema100'] - last['ema200'])

                threshold = 0.5  # तू हे कमी-जास्त करू शकतो
                if d < threshold:
                    message = f"📊 Signal: {symbol} ({tf})\nEMA Compression Detected ✅"
                    print(message)
                    send_telegram(message)
                    chart_path = plot_chart(df, symbol, tf)
                    send_chart(chart_path)

            except Exception as e:
                print(f"Error in EMA for {symbol}-{tf}: {e}")

# ✅ Render साठी dummy HTTP server चालू ठेव
def keep_alive():
    PORT = 8080
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

# 🔁 Start dummy server in background
t = threading.Thread(target=keep_alive)
t.daemon = True
t.start()

# ✅ Start bot loop
print("🚀 AltTrendBot चालू आहे... Real-time सिग्नल शोधतोय.")
while True:
    scan()
    time.sleep(120)  # 2 मिनिटांनी पुन्हा स्कॅन करेल

