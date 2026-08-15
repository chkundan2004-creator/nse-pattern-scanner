"""
fundamentals_builder.py
------------------------
Builds fundamentals.json: key ratios, recent quarterly/annual results,
and sector info for every symbol in your tracking list + universe.

This does one yfinance lookup per symbol (slower than the pattern
scan), so it runs weekly on its own schedule, same as universe_builder.py.

yfinance's exact field names shift between versions and are
inconsistent across NSE tickers, so every lookup here is best-effort:
if a value can't be found, it's saved as null rather than crashing the
whole build.
"""

import json

import yfinance as yf

import scanner

FUNDAMENTALS_FILE = "fundamentals.json"


def _find_row(df, keywords):
    """Finds the first row in a financials/balance-sheet dataframe whose
    label contains any of the given keywords (case-insensitive)."""
    if df is None or df.empty:
        return None
    for label in df.index:
        low = str(label).lower()
        if any(k in low for k in keywords):
            return df.loc[label]
    return None


def get_ratios_and_sector(ticker):
    info = {}
    try:
        info = ticker.info or {}
    except Exception:
        pass

    return {
        "pe": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        "debt_to_equity": info.get("debtToEquity"),
        "market_cap": info.get("marketCap"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }


def get_roce(ticker):
    try:
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet

        ebit_row = _find_row(financials, ["ebit", "operating income"])
        assets_row = _find_row(balance_sheet, ["total assets"])
        current_liab_row = _find_row(balance_sheet, ["current liabilities"])

        if ebit_row is None or assets_row is None or current_liab_row is None:
            return None

        ebit = ebit_row.iloc[0]
        capital_employed = assets_row.iloc[0] - current_liab_row.iloc[0]
        if not capital_employed:
            return None
        return round(float(ebit) / float(capital_employed), 4)
    except Exception:
        return None


def get_recent_results(ticker):
    """Last few quarters of revenue and net income, oldest -> newest."""
    try:
        q = ticker.quarterly_financials
        revenue_row = _find_row(q, ["total revenue", "revenue"])
        income_row = _find_row(q, ["net income"])
        if revenue_row is None or income_row is None:
            return []

        results = []
        for col in reversed(q.columns[:4]):  # last 4 quarters, oldest first
            try:
                results.append({
                    "period": str(col.date()) if hasattr(col, "date") else str(col),
                    "revenue": float(revenue_row[col]) if col in revenue_row.index else None,
                    "net_income": float(income_row[col]) if col in income_row.index else None,
                })
            except Exception:
                continue
        return results
    except Exception:
        return []


def build_fundamentals():
    tracking = set(scanner.load_watchlist())
    universe = scanner.load_universe()
    symbols = list(dict.fromkeys(list(tracking) + universe))

    data = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            entry = get_ratios_and_sector(ticker)
            entry["roce"] = get_roce(ticker)
            entry["recent_quarters"] = get_recent_results(ticker)
            data[symbol] = entry
        except Exception as e:
            print(f"Skipping fundamentals for {symbol}: {e}")
            continue

    with open(FUNDAMENTALS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Fundamentals built for {len(data)} symbols")


if __name__ == "__main__":
    build_fundamentals()
