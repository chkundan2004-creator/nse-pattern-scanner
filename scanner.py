import os
import json
from datetime import datetime
import yfinance as yf

TRACKING_FILE = "tracking_list.json"
SQUEEZE_FILE = "squeeze_status.json"
ALERTS_FILE = "alerts.json"
UNIVERSE_SQUEEZE_FILE = "universe_squeeze_status.json"

DEFAULT_SYMBOLS = [
    "REDINGTON.NS",
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS"
]

def load_tracking_list():
    """Loads the user's tracking list from tracking_list.json."""
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return DEFAULT_SYMBOLS

def save_tracking_list(symbols):
    """Saves the user's tracking list to tracking_list.json."""
    with open(TRACKING_FILE, "w") as f:
        json.dump(symbols, f, indent=2)

def load_squeeze_status():
    """Loads the tracking list squeeze status."""
    if os.path.exists(SQUEEZE_FILE):
        try:
            with open(SQUEEZE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def load_alerts():
    """Loads current pattern alerts."""
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def load_universe_squeeze_status():
    """Loads the universe squeeze status."""
    if os.path.exists(UNIVERSE_SQUEEZE_FILE):
        try:
            with open(UNIVERSE_SQUEEZE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def calculate_ttm_squeeze(df):
    """Calculates TTM Squeeze status and momentum for a dataframe."""
    if df.empty or len(df) < 20:
        return {"squeeze_on": False, "momentum": 0.0}

    # 20-period SMA & Bollinger Bands (2 std dev)
    sma = df["Close"].rolling(window=20).mean()
    std = df["Close"].rolling(window=20).std()
    upper_bb = sma + (2 * std)
    lower_bb = sma - (2 * std)

    # Keltner Channels (1.5 * ATR)
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift(1)).abs()
    low_close = (df["Low"] - df["Close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=20).mean()

    upper_kc = sma + (1.5 * atr)
    lower_kc = sma - (1.5 * atr)

    # Squeeze is ON when Bollinger Bands fit inside Keltner Channels
    squeeze_on = (upper_bb.iloc[-1] < upper_kc.iloc[-1]) and (lower_bb.iloc[-1] > lower_kc.iloc[-1])
    
    # Linear Regression Momentum (simple Close vs SMA delta proxy)
    momentum = float(df["Close"].iloc[-1] - sma.iloc[-1])

    return {"squeeze_on": bool(squeeze_on), "momentum": round(momentum, 2)}

def run_full_scan():
    """Executes the full scan for all symbols in the tracking list."""
    import pandas as pd
    symbols = load_tracking_list()
    squeeze_results = {}
    alerts_results = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M IST")

    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period="3mo", interval="1d")
            if not df.empty:
                res = calculate_ttm_squeeze(df)
                res["timestamp"] = now_str
                squeeze_results[sym] = res

                if res["squeeze_on"]:
                    direction = "bullish" if res["momentum"] >= 0 else "bearish"
                    alerts_results.append({
                        "symbol": sym,
                        "direction": direction,
                        "message": f"TTM Squeeze Active with momentum {res['momentum']:+.2f}",
                        "timestamp": now_str
                    })
        except Exception:
            continue

    with open(SQUEEZE_FILE, "w") as f:
        json.dump(squeeze_results, f, indent=2)

    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts_results, f, indent=2)

    return squeeze_results, alerts_results
