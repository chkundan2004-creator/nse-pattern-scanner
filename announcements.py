"""
announcements.py
-----------------
Polls NSE's public corporate-announcements feed and flags new
announcements (board meetings, results, corporate actions, other
material disclosures) for symbols in your tracking list.

NSE doesn't publish an officially documented API for this — this uses
the same public endpoint their own website's announcements page calls.
It can break if NSE changes their site; if that happens the scan just
logs an error and returns nothing rather than crashing the whole app.
"""

import json
import os
from datetime import datetime, timezone

import requests

WATCHLIST_FILE = "watchlist.txt"
ANNOUNCEMENTS_FILE = "announcements.json"
NSE_HOME = "https://www.nseindia.com/"
NSE_API = "https://www.nseindia.com/api/corporate-announcements?index=equities"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    with open(WATCHLIST_FILE) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def load_announcements():
    if not os.path.exists(ANNOUNCEMENTS_FILE):
        return []
    with open(ANNOUNCEMENTS_FILE) as f:
        return json.load(f)


def save_announcements(items):
    with open(ANNOUNCEMENTS_FILE, "w") as f:
        json.dump(items, f, indent=2, default=str)


def fetch_all_announcements():
    """One call fetches announcements for ALL NSE companies — we filter
    down to the watchlist ourselves, which keeps this to a single
    request per scan instead of one per symbol."""
    session = requests.Session()
    session.headers.update(HEADERS)
    session.get(NSE_HOME, timeout=15)  # sets the cookies the API needs
    resp = session.get(NSE_API, timeout=15)
    resp.raise_for_status()
    return resp.json()


def scan():
    watchlist = load_watchlist()
    # NSE's own API uses plain symbols, without the .NS suffix yfinance needs
    watchlist_symbols = {s.replace(".NS", "").replace(".BO", "") for s in watchlist}

    try:
        all_items = fetch_all_announcements()
    except Exception as e:
        print(f"Failed to fetch NSE announcements: {e}")
        return []

    existing = load_announcements()
    seen_keys = {(a["symbol"], a["subject"], a["date"]) for a in existing}
    new_items = []

    for item in all_items:
        symbol = item.get("symbol", "")
        if symbol not in watchlist_symbols:
            continue

        subject = item.get("desc") or item.get("subject") or item.get("attchmntText") or "Announcement"
        date = item.get("an_dt") or item.get("sort_date") or ""

        key = (symbol, subject, date)
        if key in seen_keys:
            continue

        entry = {
            "symbol": symbol,
            "subject": subject,
            "date": date,
            "attachment": item.get("attchmntFile", ""),
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
        new_items.append(entry)
        seen_keys.add(key)

    if new_items:
        combined = new_items + existing
        combined = combined[:200]
        save_announcements(combined)

    return new_items


if __name__ == "__main__":
    found = scan()
    print(f"Announcement scan complete. {len(found)} new item(s).")
    for a in found:
        print(a)
