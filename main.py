import requests, pandas as pd, numpy as np, time, datetime, threading
import matplotlib.pyplot as plt
from flask import Flask
from ta.trend import ema_indicator
from ta.momentum import rsi
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = '8193766880:AAFS23FHOUdAetRdJ2kHO4xkrlSrlmJjeCo'
CHAT_ID = '7671153315'

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

COINS = ['bitcoin', 'shiba-inu', 'ethereum']

def fetch_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "idr", "days": "1", "interval": "hourly"}
    r = requests.get(url, params=params).json()
    df = pd.DataFrame(r['prices'], columns=['time', 'price'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df.set_index('time', inplace=True)
    return df

def detect_snr(prices, n=10):
    highs = prices.rolling(n).max()
    lows = prices.rolling(n).min()
    return highs.dropna(), lows.dropna()

def analyze(coin):
    df = fetch_data(coin)
    df['ema5'] = ema_indicator(df['price'], 5)
    df['ema9'] = ema_indicator(df['price'], 9)
    df['rsi'] = rsi(df['price'], 14)
    df.dropna(inplace=True)

    highs, lows = detect_snr(df['price'])
    signal, entry, sl, tp, alert = None, None, None, None, None

    last = df.iloc[-1]
    if last['ema5'] > last['ema9'] and last['rsi'] < 70:
        signal = "BUY (Scalping)"
        entry = round(last['price'])
        sl = round(entry * 0.99)
        tp = round(entry * 1.01)

    support = lows.iloc[-1] if not lows.empty else None
    resistance = highs.iloc[-1] if not highs.empty else None
    price = last['price']
    if support and price < support:
        alert = f"Price just broke support at {support:.2f}"
    if resistance and price > resistance:
        alert = f"Price just broke resistance at {resistance:.2f}"

    # Plot
    plt.figure(figsize=(10, 4))
    df['price'].plot(label='Price')
    df['ema5'].plot(label='EMA5')
    df['ema9'].plot(label='EMA9')
    if support: plt.axhline(support, color='green', linestyle='--', label='Support')
    if resistance: plt.axhline(resistance, color='red', linestyle='--', label='Resistance')
    plt.title(f"{coin.upper()} Analysis")
    plt.legend()
    plt.tight_layout()
    plt.savefig("chart.png")
    plt.close()

    msg = f"**{coin.upper()}**\n"
    if signal:
        msg += f"{signal} signal detected.\nEntry: {entry}\nTP: {tp}\nSL: {sl}\n"
    if alert:
        msg += f"\n⚠️ {alert}"

    return msg, "chart.png"

async def send_signal():
    for coin in COINS:
        msg, img = analyze(coin)
        await application.bot.send_photo(chat_id=CHAT_ID, photo=open(img, 'rb'), caption=msg, parse_mode="Markdown")

async def coin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = update.message.text[1:].replace(" ", "-").lower()
    if coin:
        msg, img = analyze(coin)
        await update.message.reply_photo(open(img, 'rb'), caption=msg, parse_mode="Markdown")

application.add_handler(CommandHandler(["start", "help"], lambda u, c: u.message.reply_text("Ketik /btc atau /scalp btc")))
application.add_handler(CommandHandler(COINS + ["btc", "eth", "shib", "scalp"], coin_command))

def auto_run():
    while True:
        try:
            asyncio.run(send_signal())
        except Exception as e:
            print("Error:", e)
        time.sleep(3600)  # tiap 1 jam

threading.Thread(target=auto_run, daemon=True).start()

@app.route('/')
def home():
    return 'Bot aktif.'

if __name__ == '__main__':
    application.run_polling()
