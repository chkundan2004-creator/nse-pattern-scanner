"""
scanner.py
----------
Fetches candles for each symbol in watchlist.txt, across several
timeframes, and finds every point in the last month where a
"squeeze -> breakout" pattern formed (not just on the latest candle):

  1. SQUEEZE  : a run of candles has a noticeably tighter high-low
                range than the candles before them (volatility drying
                up), sitting near a flattening moving average.
  2. BREAKOUT : the candle right after the squeeze has a much bigger
                range, closes beyond the squeeze's high (bullish) or
                low (bearish), on a volume spike.

Results are written to alerts.json (newest first). Re-running the scan
will not duplicate an alert for the same symbol/timeframe/candle time.
"""

import json
import os
from datetime import datetime, timezone, timedelta

import pandas as pd
import yfinance as yf

WATCHLIST_FILE = "watchlist.txt"
ALERTS_FILE = "alerts.json"
UNIVERSE_FILE = "universe.json"

# (yfinance interval, lookback period, human label)
# Periods pulled generously so a full month of history is available
# after yfinance's own limits per interval.
TIMEFRAMES = [
    ("5m", "1mo", "5 min"),
    ("15m", "1mo", "15 min"),
    ("60m", "3mo", "1 hour"),
    ("1d", "6mo", "1 day"),
]

LOOKBACK_DAYS = 30       # how far back to report pattern occurrences from

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


def add_to_watchlist(symbol):
    """Promotes a symbol from the universe list into the tracking list."""
    symbols = load_watchlist()
    if symbol not in symbols:
        symbols.append(symbol)
        save_watchlist(symbols)
    return symbols


def load_universe():
    """
    The scannable universe: NSE stocks with market cap >= Rs 1500 crore,
    built weekly by universe_builder.py. Empty until that has run once.
    """
    if not os.path.exists(UNIVERSE_FILE):
        return []
    with open(UNIVERSE_FILE) as f:
        return json.load(f)


def get_scan_symbols():
    """
    Combined, de-duplicated symbol list to scan: your tracking list plus
    the market-cap-filtered universe. Returns (symbols, tracking_set) so
    callers can tag each result by where it came from.
    """
    tracking = load_watchlist()
    tracking_set = set(tracking)
    universe = load_universe()
    combined = list(dict.fromkeys(tracking + universe))  # de-dupe, keep order
    return combined, tracking_set


def load_alerts():
    if not os.path.exists(ALERTS_FILE):
        return []
    with open(ALERTS_FILE) as f:
        return json.load(f)


def save_alerts(alerts):
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=2, default=str)


def find_pattern_occurrences(df):
    """
    Scans every candle in df (oldest -> newest) as a potential breakout
    point and returns a list of matches, each a dict with direction,
    close, and candle_time. Only checks candles from the last
    LOOKBACK_DAYS days forward.
    """
    needed = SQUEEZE_WINDOW * LOOKBACK_MULT + 1
    if len(df) < needed + 1:
        return []

    cutoff = None
    try:
        last_ts = df.index[-1]
        cutoff = last_ts - timedelta(days=LOOKBACK_DAYS)
    except Exception:
        pass

    matches = []

    for i in range(needed, len(df)):
        candle_time = df.index[i]
        if cutoff is not None and candle_time < cutoff:
            continue

        latest = df.iloc[i]
        squeeze = df.iloc[i - SQUEEZE_WINDOW:i]
        broader = df.iloc[i - needed:i]

        squeeze_range = (squeeze["High"] - squeeze["Low"]).mean()
        broader_range = (broader["High"] - broader["Low"]).mean()
        if broader_range == 0 or squeeze_range == 0:
            continue

        is_squeeze = (squeeze_range / broader_range) < RANGE_TIGHTNESS

        latest_range = latest["High"] - latest["Low"]
        is_big_candle = latest_range > squeeze_range * BREAKOUT_RANGE_MULT

        avg_vol = squeeze["Volume"].mean()
        is_vol_spike = avg_vol > 0 and latest["Volume"] > avg_vol * VOLUME_SPIKE_MULT

        broke_up = latest["Close"] > squeeze["High"].max()
        broke_down = latest["Close"] < squeeze["Low"].min()

        if is_squeeze and is_big_candle and is_vol_spike and broke_up:
            direction = "bullish"
        elif is_squeeze and is_big_candle and is_vol_spike and broke_down:
            direction = "bearish"
        else:
            continue

        matches.append({
            "direction": direction,
            "close": round(float(latest["Close"]), 2),
            "candle_time": str(candle_time),
        })

    return matches


def find_active_squeeze(df):
    """
    Checks only the most recent window: is this symbol *currently*
    sitting in a squeeze right now, regardless of whether it has broken
    out yet? Useful for picking a stock to watch and confirm the
    breakout detector fires later.
    """
    needed = SQUEEZE_WINDOW * LOOKBACK_MULT + 1
    if len(df) < needed:
        return None

    squeeze = df.iloc[-SQUEEZE_WINDOW:]
    broader = df.iloc[-needed:-SQUEEZE_WINDOW]

    squeeze_range = (squeeze["High"] - squeeze["Low"]).mean()
    broader_range = (broader["High"] - broader["Low"]).mean()
    if broader_range == 0:
        return None

    ratio = squeeze_range / broader_range
    if ratio >= RANGE_TIGHTNESS:
        return None

    return {
        "squeeze_high": round(float(squeeze["High"].max()), 2),
        "squeeze_low": round(float(squeeze["Low"].min()), 2),
        "last_close": round(float(df.iloc[-1]["Close"]), 2),
        "tightness_ratio": round(float(ratio), 2),  # lower = tighter
        "as_of": str(df.index[-1]),
    }


def scan_active_squeezes():
    """Returns, per symbol/timeframe, whether it's currently squeezing.
    Each result is tagged source='tracking' or source='universe'."""
    symbols, tracking_set = get_scan_symbols()
    results = []

    for symbol in symbols:
        source = "tracking" if symbol in tracking_set else "universe"
        for interval, period, label in TIMEFRAMES:
            try:
                df = yf.Ticker(symbol).history(period=period, interval=interval)
            except Exception as e:
                print(f"Failed to fetch {symbol} {interval}: {e}")
                continue

            if df is None or df.empty:
                continue

            info = find_active_squeeze(df)
            if info:
                results.append({"symbol": symbol, "timeframe": label, "source": source, **info})

    return results


PINNED_FILE = "pinned_squeezes.json"


def load_pinned_squeezes():
    if not os.path.exists(PINNED_FILE):
        return []
    with open(PINNED_FILE) as f:
        return json.load(f)


def save_pinned_squeezes(pinned):
    with open(PINNED_FILE, "w") as f:
        json.dump(pinned, f, indent=2, default=str)


def update_pinned_squeezes(current_squeezes):
    """
    Adds any newly-qualifying squeeze to the pinned list, and refreshes
    the numbers for ones already pinned. Never removes an entry just
    because it stopped squeezing on this scan — only remove_pinned_squeeze
    (a manual user action) does that.
    """
    pinned = load_pinned_squeezes()
    by_key = {(p["symbol"], p["timeframe"]): p for p in pinned}
    active_keys = {(s["symbol"], s["timeframe"]) for s in current_squeezes}

    for s in current_squeezes:
        key = (s["symbol"], s["timeframe"])
        if key in by_key:
            by_key[key].update(s)
            by_key[key]["still_active"] = True
        else:
            entry = dict(s)
            entry["still_active"] = True
            entry["pinned_at"] = datetime.now(timezone.utc).isoformat()
            by_key[key] = entry

    for key, entry in by_key.items():
        if key not in active_keys:
            entry["still_active"] = False

    save_pinned_squeezes(list(by_key.values()))
    return list(by_key.values())


def remove_pinned_squeeze(symbol, timeframe):
    pinned = load_pinned_squeezes()
    pinned = [p for p in pinned if not (p["symbol"] == symbol and p["timeframe"] == timeframe)]
    save_pinned_squeezes(pinned)


def scan():
    """
    Keeps only the single most recent breakout per symbol+timeframe —
    a new breakout replaces the old one for that pair rather than
    stacking up. A notification only fires when that latest breakout
    actually changes (a genuinely new candle), not on every scan.
    """
    symbols, tracking_set = get_scan_symbols()
    existing = load_alerts()
    existing_map = {(a["symbol"], a["timeframe"]): a for a in existing}
    updated_map = dict(existing_map)
    new_alerts = []

    for symbol in symbols:
        source = "tracking" if symbol in tracking_set else "universe"
        for interval, period, label in TIMEFRAMES:
            try:
                df = yf.Ticker(symbol).history(period=period, interval=interval)
            except Exception as e:
                print(f"Failed to fetch {symbol} {interval}: {e}")
                continue

            if df is None or df.empty:
                continue

            occurrences = find_pattern_occurrences(df)
            if not occurrences:
                continue

            latest = max(occurrences, key=lambda r: r["candle_time"])
            key = (symbol, label)
            prev = existing_map.get(key)

            if prev is not None and prev.get("candle_time") == latest["candle_time"]:
                continue  # nothing new for this symbol+timeframe

            alert = {
                "symbol": symbol,
                "timeframe": label,
                "source": source,
                "direction": latest["direction"],
                "close": latest["close"],
                "candle_time": latest["candle_time"],
                "detected_at": datetime.now(timezone.utc).isoformat(),
            }
            new_alerts.append(alert)
            updated_map[key] = alert

    combined = list(updated_map.values())
    combined.sort(key=lambda a: a["candle_time"], reverse=True)
    save_alerts(combined)

    return new_alerts


if __name__ == "__main__":
    found = scan()
    print(f"Scan complete. {len(found)} new alert(s).")
    for a in found:
        print(a)
