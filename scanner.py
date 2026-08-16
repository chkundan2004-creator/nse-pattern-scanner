import os
import json
import pandas as pd
import yfinance as yf

TRACKING_FILE = "tracking_list.json"
SQUEEZE_FILE = "squeeze_status.json"
UNIVERSE_SQUEEZE_FILE = "universe_squeeze_status.json"
ALERTS_FILE = "alerts.json"

DEFAULT_SYMBOLS = ["REDINGTON.NS", "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

def load_tracking_list():
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_SYMBOLS
    return DEFAULT_SYMBOLS

def save_tracking_list(symbols):
    with open(TRACKING_FILE, "w") as f:
        json.dump(symbols, f, indent=2)

def calculate_ttm_squeeze(df):
    """Calculates TTM Squeeze status and momentum."""
    if df is None or len(df) < 20:
        return {"squeeze_on": False, "momentum": 0.0}
    
    try:
        # 20-period SMA & Standard Deviation for Bollinger Bands
        df['sma'] = df['Close'].rolling(window=20).mean()
        df['std'] = df['Close'].rolling(window=20).std()
        df['bb_upper'] = df['sma'] + (2 * df['std'])
        df['bb_lower'] = df['sma'] - (2 * df['std'])
        
        # Keltner Channels (20-period EMA + 1.5 * ATR)
        df['tr'] = pd.concat([
            df['High'] - df['Low'],
            (df['High'] - df['Close'].shift(1)).abs(),
            (df['Low'] - df['Close'].shift(1)).abs()
        ], axis=1).max(axis=1)
        df['atr'] = df['tr'].rolling(window=20).mean()
        df['kc_upper'] = df['sma'] + (1.5 * df['atr'])
        df['kc_lower'] = df['sma'] - (1.5 * df['atr'])
        
        latest = df.iloc[-1]
        
        # Squeeze is ON if Bollinger Bands are inside Keltner Channels
        squeeze_on = bool(
            (latest['bb_lower'] > latest['kc_lower']) and 
            (latest['bb_upper'] < latest['kc_upper'])
        )
        
        # Simple momentum indicator
        momentum = float(latest['Close'] - df['Close'].iloc[-20]) if len(df) >= 20 else 0.0
        
        return {"squeeze_on": squeeze_on, "momentum": round(momentum, 2)}
    except Exception as e:
        print(f"Error calculating squeeze: {e}")
        return {"squeeze_on": False, "momentum": 0.0}

def scan_symbol(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3m", interval="1d")
        if df.empty:
            return None
        return calculate_ttm_squeeze(df)
    except Exception as e:
        print(f"Failed to scan {symbol}: {e}")
        return None

def run_full_scan():
    symbols = load_tracking_list()
    squeeze_results = {}
    alerts = []
    
    print(f"Starting scan for {len(symbols)} tracked symbols...")
    for sym in symbols:
        res = scan_symbol(sym)
        if res:
            squeeze_results[sym] = res
            if res.get("squeeze_on"):
                alerts.append({"symbol": sym, "type": "TTM Squeeze Active", "momentum": res.get("momentum")})
    
    with open(SQUEEZE_FILE, "w") as f:
        json.dump(squeeze_results, f, indent=2)
        
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=2)
        
    print("Scan completed successfully!")

def load_squeeze_status():
    if os.path.exists(SQUEEZE_FILE):
        try:
            with open(SQUEEZE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def load_universe_squeeze_status():
    if os.path.exists(UNIVERSE_SQUEEZE_FILE):
        try:
            with open(UNIVERSE_SQUEEZE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def load_alerts():
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

if __name__ == "__main__":
    run_full_scan()
