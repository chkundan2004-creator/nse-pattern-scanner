"""
fundamentals.py
-----------------
Read-side helpers for fundamentals.json (built weekly by
fundamentals_builder.py): loading it, running custom ratio screens,
and grouping by sector for peer comparison. Also has a best-effort
shareholding lookup, done live since yfinance has no reliable NSE
shareholding data to pre-build.
"""

import json
import os

import yfinance as yf

FUNDAMENTALS_FILE = "fundamentals.json"

OPERATORS = {
    ">": lambda a, b: a is not None and a > b,
    "<": lambda a, b: a is not None and a < b,
    ">=": lambda a, b: a is not None and a >= b,
    "<=": lambda a, b: a is not None and a <= b,
}

METRICS = ["pe", "pb", "roe", "roa", "roce", "debt_to_equity", "market_cap"]


def load_fundamentals():
    if not os.path.exists(FUNDAMENTALS_FILE):
        return {}
    with open(FUNDAMENTALS_FILE) as f:
        return json.load(f)


def run_screen(conditions):
    """conditions: list of (metric, operator_symbol, value). Returns
    symbols (with their data) that satisfy every condition (AND)."""
    data = load_fundamentals()
    matches = []
    for symbol, entry in data.items():
        ok = True
        for metric, op, value in conditions:
            fn = OPERATORS.get(op)
            if fn is None or not fn(entry.get(metric), value):
                ok = False
                break
        if ok:
            matches.append({"symbol": symbol, **entry})
    return matches


def peers_in_sector(sector):
    data = load_fundamentals()
    return [{"symbol": s, **e} for s, e in data.items() if e.get("sector") == sector]


def list_sectors():
    data = load_fundamentals()
    sectors = {e.get("sector") for e in data.values() if e.get("sector")}
    return sorted(sectors)


def get_shareholding(symbol):
    """Best-effort — yfinance rarely has this for NSE stocks, so this
    commonly returns 'not available'. Kept separate/live rather than
    pre-built since there's no reliable free bulk source for it."""
    try:
        ticker = yf.Ticker(symbol)
        holders = ticker.major_holders
        if holders is None or holders.empty:
            return None
        return holders.to_dict()
    except Exception:
        return None
