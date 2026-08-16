import json
import yfinance as yf
import scanner

FUNDAMENTALS_FILE = "fundamentals.json"

def _find_row(df, keywords):
    if df is None or df.empty:
        return None
    for label in df.index:
        low = str(label).lower()
        if any(k in low for k in keywords):
            return df.loc[label]
    return None

def build_pl_table(df, n_periods=6):
    if df is None or df.empty:
        return []
    sales_row = _find_row(df, ["total revenue", "revenue"])
    net_income_row = _find_row(df, ["net income"])
    ebit_row = _find_row(df, ["ebit", "operating income"])
    expenses_row = _find_row(df, ["total expenses", "operating expense"])
    
    if sales_row is None:
        return []

    periods = []
    for col in reversed(df.columns[:n_periods]):
        def safe(row):
            try:
                return float(row[col]) if row is not None and col in row.index else None
            except Exception:
                return None

        sales = safe(sales_row)
        operating_profit = safe(ebit_row)
        expenses = safe(expenses_row)
        net_income = safe(net_income_row)
        
        if expenses is None and sales is not None and operating_profit is not None:
            expenses = sales - operating_profit

        opm = round(operating_profit / sales * 100, 1) if sales and operating_profit else None

        periods.append({
            "period": str(col.date()) if hasattr(col, "date") else str(col),
            "sales": sales,
            "expenses": expenses,
            "operating_profit": operating_profit,
            "opm_pct": opm,
            "net_profit": net_income,
        })
    return periods

def fetch_stock_fundamentals(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        
        fin = ticker.financials
        q_fin = ticker.quarterly_financials
        bs = ticker.balance_sheet
        cf = ticker.cashflow

        return {
            "ratios": {
                "cmp": info.get("currentPrice") or info.get("regularMarketPrice"),
                "pe": info.get("trailingPE"),
                "pb": info.get("priceToBook"),
                "roe": info.get("returnOnEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "summary": info.get("longBusinessSummary", "No summary available.")
            },
            "quarters": build_pl_table(q_fin, 5),
            "pl": build_pl_table(fin, 5)
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def build_fundamentals():
    symbols = scanner.load_tracking_list()
    results = {}
    print(f"Building Screener layout for {len(symbols)} symbols...")
    for sym in symbols:
        data = fetch_stock_fundamentals(sym)
        if data:
            results[sym] = data
            print(f"Fetched {sym}")
            
    with open(FUNDAMENTALS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print("Saved fundamentals.json successfully!")

if __name__ == "__main__":
    build_fundamentals()
