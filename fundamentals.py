import os
import json
import yfinance as yf

FUNDAMENTALS_FILE = "fundamentals.json"

def load_fundamentals_data():
    """Loads cached fundamentals data from fundamentals.json."""
    if os.path.exists(FUNDAMENTALS_FILE):
        try:
            with open(FUNDAMENTALS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_company_overview(symbol):
    """Fetches key company overview metrics."""
    data = load_fundamentals_data()
    if symbol in data:
        return data[symbol]
    
    # Fallback live fetch if missing from JSON
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "market_cap": info.get("marketCap", "N/A"),
            "pe": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else "N/A",
            "roce": round(info.get("returnOnEquity", 0) * 100, 2) if info.get("returnOnEquity") else "N/A",
            "summary": info.get("longBusinessSummary", "No summary available for this company.")
        }
    except Exception:
        return None

def get_financials(symbol):
    """Fetches financial statements."""
    try:
        ticker = yf.Ticker(symbol)
        return ticker.financials.to_dict() if not ticker.financials.empty else None
    except Exception:
        return None

def get_quarterly_results(symbol):
    """Fetches quarterly financial results."""
    try:
        ticker = yf.Ticker(symbol)
        return ticker.quarterly_financials.to_dict() if not ticker.quarterly_financials.empty else None
    except Exception:
        return None

def get_peer_comparison(symbol):
    """Fetches basic peer data."""
    overview = get_company_overview(symbol)
    if overview:
        return [{
            "symbol": symbol,
            "pe": overview.get("pe"),
            "roe": overview.get("roce"),
            "roce": overview.get("roce"),
            "debt_to_equity": "N/A",
            "market_cap": overview.get("market_cap")
        }]
    return None

def get_shareholding(symbol):
    """Fetches shareholding breakdown if available."""
    try:
        ticker = yf.Ticker(symbol)
        holders = ticker.major_holders
        return holders.to_dict() if holders is not None and not holders.empty else None
    except Exception:
        return None
def build_all_fundamentals():
    """Generates fundamentals.json for tracked symbols when triggered by GitHub Actions."""
    import scanner
    symbols = scanner.load_tracking_list()
    results = {}
    print(f"Building fundamentals for {len(symbols)} symbols...")
    for sym in symbols:
        try:
            overview = get_company_overview(sym)
            if overview:
                results[sym] = overview
                print(f"Successfully fetched {sym}")
        except Exception as e:
            print(f"Error fetching {sym}: {e}")

    with open(FUNDAMENTALS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print("Saved fundamentals.json successfully!")

if __name__ == "__main__":
    build_all_fundamentals()
