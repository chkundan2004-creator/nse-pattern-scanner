"""
scanner.py
----------
Fetches recent price/volume candles for each symbol in watchlist.txt,
across several timeframes, and checks whether a "squeeze -> breakout"
pattern has just formed:

  1. SQUEEZE  : a run of recent candles has a noticeably tighter
                high-low range than the candles before them (volatility
                drying up), sitting near a flattening moving average.
  2. BREAKOUT : the very latest candle has a much bigger range than the
                squeeze candles, closes beyond the squeeze's high (bullish)
                or low (bearish), on a volume spike.

Results are written to alerts.json (newest first). Re-running the scan
will not duplicate an alert for the same symbol/timeframe/candle time.
"""

import json
import os
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

WATCHLIST_FILE = "watchlist.txt"
ALERTS_FILE = "alerts.json"

# (yfinance interval, lookback period, human label)
TIMEFRAMES = [
    ("5m", "5d", "5 min"),
    ("15m", "5d", "15 min"),
    ("60m", "1mo", "1 hour"),
    ("1d", "6mo", "1 day"),
]

SQUEEZE_WINDOW = 10      # candles considered "the squeeze"
LOOKBACK_MULT = 3        # how many squeeze-windows back to compare against
RANGE_TIGHTNESS = 0.6    # squeeze range must be < 60% of the broader range
BREAKOUT_RANGE_MULT = 1.5
VOLUME_SPIKE_MULT = 1.8


def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    with open(WATCHLIST_FILE) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def save_watchlist(symbols):
    with open(WATCHLIST_FILE, "w") as f:
        f.write("\n".join(symbols) + "\n")


def load_alerts():
    if not os.path.exists(ALERTS_FILE):
        return []
    with open(ALERTS_FILE) as f:
        return json.load(f)


def save_alerts(alerts):
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=2, default=str)


def detect_squeeze_breakout(df):
    """df must have columns Open, High, Low, Close, Volume, sorted oldest -> newest."""
    needed = SQUEEZE_WINDOW * LOOKBACK_MULT + 1
    if len(df) < needed:
        return None

    latest = df.iloc[-1]
    squeeze = df.iloc[-(SQUEEZE_WINDOW + 1):-1]
    broader = df.iloc[-needed:-1]

    squeeze_range = (squeeze["High"] - squeeze["Low"]).mean()
    broader_range = (broader["High"] - broader["Low"]).mean()
    if broader_range == 0:
        return None

    is_squeeze = (squeeze_range / broader_range) < RANGE_TIGHTNESS

    latest_range = latest["High"] - latest["Low"]
    is_big_candle = squeeze_range > 0 and latest_range > squeeze_range * BREAKOUT_RANGE_MULT

    avg_vol = squeeze["Volume"].mean()
    is_vol_spike = avg_vol > 0 and latest["Volume"] > avg_vol * VOLUME_SPIKE_MULT

    broke_up = latest["Close"] > squeeze["High"].max()
    broke_down = latest["Close"] < squeeze["Low"].min()

    if is_squeeze and is_big_candle and is_vol_spike and broke_up:
        direction = "bullish"
    elif is_squeeze and is_big_candle and is_vol_spike and broke_down:
        direction = "bearish"
    else:
        return None

    return {
        "direction": direction,
        "close": round(float(latest["Close"]), 2),
        "candle_time": str(latest.name),
    }


def scan():
    symbols = load_watchlist()
    existing = load_alerts()
    seen_keys = {(a["symbol"], a["timeframe"], a["candle_time"]) for a in existing}
    new_alerts = []

    for symbol in symbols:
        for interval, period, label in TIMEFRAMES:
            try:
                df = yf.Ticker(symbol).history(period=period, interval=interval)
            except Exception as e:
                print(f"Failed to fetch {symbol} {interval}: {e}")
                continue

            if df is None or df.empty:
                continue

            result = detect_squeeze_breakout(df)
            if result is None:
                continue

            key = (symbol, label, result["candle_time"])
            if key in seen_keys:
                continue

            alert = {
                "symbol": symbol,
                "timeframe": label,
                "direction": result["direction"],
                "close": result["close"],
                "candle_time": result["candle_time"],
                "detected_at": datetime.now(timezone.utc).isoformat(),
            }
            new_alerts.append(alert)
            seen_keys.add(key)

    if new_alerts:
        combined = new_alerts + existing
        combined = combined[:200]  # keep the file small
        save_alerts(combined)

    return new_alerts


if __name__ == "__main__":
    found = scan()
    print(f"Scan complete. {len(found)} new alert(s).")
    for a in found:
        print(a)
