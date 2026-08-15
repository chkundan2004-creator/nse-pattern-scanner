"""
universe_builder.py
--------------------
Builds universe.json: NSE-listed stocks with a market cap of at least
Rs 1500 crore. Starts from NSE's official Nifty 500 list (the 500
largest NSE stocks by free-float market cap) and checks each one's
current market cap, keeping only those at or above the threshold.

This is much slower than the regular pattern scan (500 lookups), so it
runs on its own weekly schedule rather than every 15 minutes.
"""

import json

import requests
import yfinance as yf

NIFTY500_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
UNIVERSE_FILE = "universe.json"
MIN_MARKET_CAP = 1500 * 1_00_00_000  # Rs 1500 crore, in rupees


def fetch_nifty500_symbols():
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(NIFTY500_URL, headers=headers, timeout=30)
    resp.raise_for_status()

    lines = resp.text.splitlines()
    symbols = []
    for line in lines[1:]:  # skip header row
        parts = line.split(",")
        if len(parts) > 2:
            symbol = parts[2].strip().strip('"')
            if symbol:
                symbols.append(f"{symbol}.NS")
    return symbols


def get_market_cap(symbol):
    try:
        fast = yf.Ticker(symbol).fast_info
        for key in ("market_cap", "marketCap"):
            try:
                cap = fast[key]
                if cap:
                    return float(cap)
            except (KeyError, TypeError):
                continue
    except Exception as e:
        print(f"Could not get market cap for {symbol}: {e}")
    return None


def build_universe():
    symbols = fetch_nifty500_symbols()
    print(f"Fetched {len(symbols)} Nifty 500 symbols, checking market caps...")

    qualifying = []
    for symbol in symbols:
        cap = get_market_cap(symbol)
        if cap is not None and cap >= MIN_MARKET_CAP:
            qualifying.append(symbol)

    with open(UNIVERSE_FILE, "w") as f:
        json.dump(qualifying, f, indent=2)

    print(f"Universe built: {len(qualifying)} symbols with market cap >= Rs 1500cr")


if __name__ == "__main__":
    build_universe()
