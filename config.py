import os

# 23-Pair Watchlist
SYMBOLS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "USD/CAD", "NZD/USD",
    "AUD/NZD", "AUD/CAD", "NZD/CAD", "AUD/CHF", "CAD/CHF", "GBP/JPY", "GBP/CHF",
    "GBP/AUD", "GBP/NZD", "GBP/CAD", "EUR/GBP", "EUR/JPY", "EUR/CHF", "EUR/AUD",
    "EUR/NZD", "EUR/CAD"
]

# Analysis & Engine Parameters
ATR_PERIOD = 14
TOUCH_TOLERANCE_ATR_MULT = 0.25
EXTENDED_BO_ATR_MULT = 1.0  # Extended Breakout Filter threshold
MAX_LEVEL_AGE_D1_CANDLES = 60  # Do not use levels older than 60 Daily candles
RETEST_WINDOW_H4_CANDLES = 6

# Credentials loaded from GitHub Secrets
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
