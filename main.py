import requests
import pandas as pd
import time
import ta
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === KONFIGURASI ===
TELEGRAM_TOKEN = '8193766880:AAFS23FHOUdAetRdJ2kHO4xkrlSrlmJjeCo'
CHAT_ID = '7671153315'
VS_CURRENCY = 'idr'

# === INISIALISASI ===
application = Application.builder().token(TELEGRAM_TOKEN).build()
app = Flask(__name__)

# === FUNGSI MENGAMBIL SEMUA COIN ===
def get_top_coins(limit=20):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={VS_CURRENCY}&order=market_cap_desc&per_page={limit}&page=1"
    res = requests.get(url).json()
    return [coin['id'] for coin in res]

# === FUNGSI MENGAMBIL DATA HARGA ===
def fetch_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={VS_CURRENCY}&days=7&interval=hourly"
    try:
        response = requests.get(url)
        data = response.json()
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except:
        return None

# === ANALISIS TEKNIKAL ===
def analyze(df):
    df['sma20'] = ta.trend.sma_indicator(df['price'], window=20)
    df['rsi'] = ta.momentum.rsi(df['price'], window=14)
