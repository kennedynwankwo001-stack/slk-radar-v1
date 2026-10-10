import requests
import json
import os
import time
from config import SYMBOLS, TWELVE_DATA_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ATR_PERIOD, EXTENDED_BO_ATR_MULT
from slk_engine import calculate_atr, detect_key_levels, evaluate_drd

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading state.json: {e}")
            return {}
    return {}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error saving state.json: {e}")

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram tokens missing. Outputting message to console:")
        print(message)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            print(f"Telegram API Error: {r.text}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def fetch_candles(symbol, interval, size=70):
    if not TWELVE_DATA_API_KEY:
        print("CRITICAL ERROR: TWELVE_DATA_API_KEY secret is missing or empty!")
        return []
        
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={size}&timezone=UTC&apikey={TWELVE_DATA_API_KEY}"
    try:
        res = requests.get(url).json()
        if "values" in res:
            raw = res["values"]
            raw.reverse()
            candles = []
            for c in raw:
                candles.append({
                    'datetime': c['datetime'],
                    'open': float(c['open']),
                    'high': float(c['high']),
                    'low': float(c['low']),
                    'close': float(c['close'])
                })
            return candles
        elif "message" in res:
            print(f"Twelve Data API Warning for {symbol} ({interval}): {res['message']}")
    except Exception as e:
        print(f"Error fetching {symbol} {interval}: {e}")
    return []

def run_radar_scan():
    state = load_state()
    print("🚀 Starting SLK Radar scan across 23 pairs...")
    
    for idx, pair in enumerate(SYMBOLS, start=1):
        print(f"[{idx}/{len(SYMBOLS)}] Scanning {pair}...")
        
        d1_candles = fetch_candles(pair, "1day", size=70)
        time.sleep(8)  # Rate limit spacer between Daily and 4H requests
        
        h4_candles = fetch_candles(pair, "4h", size=30)
        time.sleep(8)  # Rate limit spacer before moving to next pair
        
        if not d1_candles or not h4_candles:
            print(f"⚠️ Skipping {pair} due to missing candle data.")
            continue
            
        atr = calculate_atr(d1_candles, ATR_PERIOD)
        levels = detect_key_levels(d1_candles, atr)
        drd = evaluate_drd(d1_candles, levels, atr)
        
        if not drd:
            print(f"  └ No active Daily Rejection (DRD) on {pair}.")
            continue
            
        # Extended Breakout Filter Check
        latest_h4 = h4_candles[-1]
        dist_from_lvl = abs(latest_h4['close'] - drd['level']['price'])
        is_extended = dist_from_lvl >= (EXTENDED_BO_ATR_MULT * atr)
        
        alert_key = f"{pair}_{drd['bias']}_{drd['level']['price']}"
        
        if alert_key not in state:
            status_text = "⚠️ Extended / Low Probability (Awaiting Retest)" if is_extended else "✅ Confirmed H4 Structure Break"
            
            msg = (
                f"🔔 *SLK RADAR: {pair}*\n"
                f"• *Daily Bias:* {drd['bias']}\n"
                f"• *DRD Grade:* {drd['grade']} ({drd['score']}/5)\n"
                f"• *Key Level:* `{drd['level']['price']:.5f}` ({drd['level']['type']})\n"
                f"• *PD Sweep:* {'Yes' if drd['pd_sweep'] else 'No'}\n"
                f"• *H4 Status:* {status_text}\n"
                f"• *Target:* External Range Liquidity (ERL)\n"
            )
            
            print(f"✨ MATCH FOUND! Sending alert for {pair}...")
            send_telegram_alert(msg)
            state[alert_key] = {"pair": pair, "bias": drd['bias'], "sent_at": time.time()}
            save_state(state)
        else:
            print(f"  └ Setup for {pair} already alerted previously.")

    print("🎉 SLK Radar scan complete!")

if __name__ == "__main__":
    run_radar_scan()
