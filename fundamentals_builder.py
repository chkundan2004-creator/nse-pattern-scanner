"""
fundamentals_builder.py
------------------------
Builds fundamentals.json: multi-period financial tables (quarterly
results, annual P&L, balance sheet, cash flow), key ratios, and sector
info — laid out the same way Screener.in shows them (periods across
the top, line items down the side).

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


def _period_label(col):
    return str(col.date()) if hasattr(col, "date") else str(col)


def get_ratios_and_sector(ticker):
    info = {}
    try:
        info = ticker.info or {}
    except Exception:
        pass

    return {
        "cmp": info.get("currentPrice") or info.get("regularMarketPrice"),
        "pe": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        "debt_to_equity": info.get("debtToEquity"),
        "dividend_yield": info.get("dividendYield"),
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


def build_pl_table(df, n_periods):
    """Sales / Expenses / Operating Profit / OPM% / Net Profit, one row
    per line item, oldest -> newest — same shape as Screener's P&L and
    Quarters pages."""
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
        try:
            sales = float(sales_row[col]) if col in sales_row.index else None
        except Exception:
            sales = None

        def safe(row):
            try:
                return float(row[col]) if row is not None and col in row.index else None
            except Exception:
                return None

        net_income = safe(net_income_row)
        operating_profit = safe(ebit_row)
        expenses = safe(expenses_row)
        if expenses is None and sales is not None and operating_profit is not None:
            expenses = sales - operating_profit  # fallback estimate

        opm = round(operating_profit / sales * 100, 1) if sales and operating_profit is not None else None

        periods.append({
            "period": _period_label(col),
            "sales": sales,
            "expenses": expenses,
            "operating_profit": operating_profit,
            "opm_pct": opm,
            "net_profit": net_income,
        })
    return periods


def build_balance_sheet_table(balance_sheet, n_periods=6):
    if balance_sheet is None or balance_sheet.empty:
        return []

    equity_row = _find_row(balance_sheet, ["common stock", "share capital", "equity capital"])
    reserves_row = _find_row(balance_sheet, ["retained earnings", "reserves"])
    borrowings_row = _find_row(balance_sheet, ["total debt", "long term debt"])
    total_liab_row = _find_row(balance_sheet, ["total liabilities net minority interest", "total liab"])
    fixed_assets_row = _find_row(balance_sheet, ["net ppe", "property plant"])
    investments_row = _find_row(balance_sheet, ["long term investments", "investments"])
    total_assets_row = _find_row(balance_sheet, ["total assets"])

    periods = []
    for col in reversed(balance_sheet.columns[:n_periods]):
        def safe(row):
            try:
                return float(row[col]) if row is not None and col in row.index else None
            except Exception:
                return None

        total_liab = safe(total_liab_row)
        equity = safe(equity_row)
        reserves = safe(reserves_row)
        borrowings = safe(borrowings_row)
        other_liab = None
        if total_liab is not None:
            known = sum(v for v in [equity, reserves, borrowings] if v is not None)
            other_liab = total_liab - known

        total_assets = safe(total_assets_row)
        fixed_assets = safe(fixed_assets_row)
        investments = safe(investments_row)
        other_assets = None
        if total_assets is not None:
            known = sum(v for v in [fixed_assets, investments] if v is not None)
            other_assets = total_assets - known

        periods.append({
            "period": _period_label(col),
            "equity_capital": equity,
            "reserves": reserves,
            "borrowings": borrowings,
            "other_liabilities": other_liab,
            "total_liabilities": total_liab,
            "fixed_assets": fixed_assets,
            "investments": investments,
            "other_assets": other_assets,
            "total_assets": total_assets,
        })
    return periods


def build_cash_flow_table(cashflow, n_periods=6):
    if cashflow is None or cashflow.empty:
        return []

    cfo_row = _find_row(cashflow, ["operating activities", "cash from operat"])
    cfi_row = _find_row(cashflow, ["investing activities", "cash from invest"])
    cff_row = _find_row(cashflow, ["financing activities", "cash from financ"])

    periods = []
    for col in reversed(cashflow.columns[:n_periods]):
        def safe(row):
            try:
                return float(row[col]) if row is not None and col in row.index else None
            except Exception:
                return None

        cfo, cfi, cff = safe(cfo_row), safe(cfi_row), safe(cff_row)
        net = None
        if None not in (cfo, cfi, cff):
            net = cfo + cfi + cff

        periods.append({
            "period": _period_label(col),
            "cfo": cfo,
            "cfi": cfi,
            "cff": cff,
            "net_cash_flow": net,
        })
    return periods


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
            entry["quarterly"] = build_pl_table(ticker.quarterly_financials, n_periods=8)
            entry["annual_pl"] = build_pl_table(ticker.financials, n_periods=6)
            entry["balance_sheet"] = build_balance_sheet_table(ticker.balance_sheet, n_periods=6)
            entry["cash_flow"] = build_cash_flow_table(ticker.cashflow, n_periods=6)
            data[symbol] = entry
        except Exception as e:
            print(f"Skipping fundamentals for {symbol}: {e}")
            continue

    with open(FUNDAMENTALS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Fundamentals built for {len(data)} symbols")


if __name__ == "__main__":
    build_fundamentals()
