import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

import scanner
import announcements
import fundamentals

st.set_page_config(page_title="NSE Pattern Scanner", layout="wide", page_icon="📈")

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; }
    .card {
        background-color: #1A1F29;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        border-left: 4px solid #444;
    }
    .card.bullish { border-left-color: #2ECC71; }
    .card.bearish { border-left-color: #E74C3C; }
    .card.squeeze-active { border-left-color: #F5B041; }
    .card.squeeze-inactive { border-left-color: #555; opacity: 0.7; }
    .card.announcement { border-left-color: #5DADE2; }
    .card b { color: #FAFAFA; }
    .card .meta { color: #9AA0A6; font-size: 0.85em; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📈 NSE Pattern Scanner")
st.caption("Squeeze → breakout scanner across 5m / 15m / 1h / 1D timeframes. Free data via yfinance (may be a few minutes delayed).")

# Refresh the page every 60 seconds — cheap, since the heavy scans below are cached.
st_autorefresh(interval=60_000, key="auto_refresh")

# ---------------------------------------------------------------------------
# Cached, expensive operations — actually re-run at most every 5 minutes,
# not on every 60-second page refresh. This is what keeps the app smooth.
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def cached_scan():
    return scanner.scan()


@st.cache_data(ttl=300)
def cached_squeeze_scan():
    return scanner.scan_active_squeezes()


@st.cache_data(ttl=300)
def cached_announcements_scan():
    return announcements.scan()


# ---------------------------------------------------------------------------
# Sidebar: tracking list management
# ---------------------------------------------------------------------------
st.sidebar.header("Tracking list")
current = scanner.load_watchlist()
text = st.sidebar.text_area(
    "One NSE symbol per line (yfinance format, e.g. REDINGTON.NS)",
    value="\n".join(current),
    height=200,
)
if st.sidebar.button("Save tracking list"):
    symbols = [s.strip() for s in text.splitlines() if s.strip()]
    scanner.save_watchlist(symbols)
    st.sidebar.success(f"Saved {len(symbols)} symbols.")

if st.sidebar.button("Run scan now"):
    cached_scan.clear()
    cached_squeeze_scan.clear()
    cached_announcements_scan.clear()
    st.rerun()

universe = scanner.load_universe()
if not universe:
    st.sidebar.warning(
        "Universe list is empty — run 'Build stock universe' once manually "
        "from the Actions tab on GitHub to fill it immediately."
    )
else:
    st.sidebar.caption(f"Universe: {len(universe)} NSE stocks, market cap ≥ ₹1500cr")

fund_data = fundamentals.load_fundamentals()
if not fund_data:
    st.sidebar.warning(
        "Fundamentals not built yet — run 'Build fundamentals' once manually "
        "from the Actions tab on GitHub to fill it immediately."
    )

# ---------------------------------------------------------------------------
# Run the (cached) scans
# ---------------------------------------------------------------------------
new_alerts = cached_scan()
squeezes = cached_squeeze_scan()
pinned = scanner.update_pinned_squeezes(squeezes)
alerts = scanner.load_alerts()
new_announcements = cached_announcements_scan()
all_announcements = announcements.load_announcements()


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------
def render_squeeze_section(source):
    rows_all = [p for p in pinned if p["source"] == source]
    tabs = st.tabs([label for _, _, label in scanner.TIMEFRAMES])
    for tab, (_, _, label) in zip(tabs, scanner.TIMEFRAMES):
        with tab:
            rows = sorted(
                [p for p in rows_all if p["timeframe"] == label],
                key=lambda x: (not x["still_active"], x["tightness_ratio"]),
            )
            if not rows:
                st.write(f"Nothing pinned on the {label} timeframe right now.")
                continue
            for s in rows:
                status = "🔎 still squeezing" if s["still_active"] else "⚪ no longer squeezing (pinned)"
                css_class = "squeeze-active" if s["still_active"] else "squeeze-inactive"
                cols = st.columns([5, 1, 1]) if source == "universe" else st.columns([6, 1])
                with cols[0]:
                    st.markdown(
                        f"""<div class="card {css_class}">
                        <b>{s['symbol']}</b> — {status}<br>
                        <span class="meta">range ₹{s['squeeze_low']}–₹{s['squeeze_high']} · last close ₹{s['last_close']}
                        · tightness {s['tightness_ratio']} · as of {s['as_of']}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                if source == "universe":
                    with cols[1]:
                        if st.button("Add to tracking", key=f"add_{s['symbol']}_{s['timeframe']}"):
                            scanner.add_to_watchlist(s["symbol"])
                            st.success(f"Added {s['symbol']}")
                    with cols[2]:
                        if st.button("Remove", key=f"remove_{s['symbol']}_{s['timeframe']}"):
                            scanner.remove_pinned_squeeze(s["symbol"], s["timeframe"])
                            st.rerun()
                else:
                    with cols[1]:
                        if st.button("Remove", key=f"remove_{s['symbol']}_{s['timeframe']}"):
                            scanner.remove_pinned_squeeze(s["symbol"], s["timeframe"])
                            st.rerun()


def render_alert_section(source):
    rows_all = [a for a in alerts if a["source"] == source]
    tabs = st.tabs([label for _, _, label in scanner.TIMEFRAMES])
    for tab, (_, _, label) in zip(tabs, scanner.TIMEFRAMES):
        with tab:
            rows = [a for a in rows_all if a["timeframe"] == label]
            if not rows:
                st.write(f"No {label} alerts yet.")
                continue
            for a in rows:
                icon = "🟢" if a["direction"] == "bullish" else "🔴"
                cols = st.columns([5, 1]) if source == "universe" else [st.container()]
                with cols[0]:
                    st.markdown(
                        f"""<div class="card {a['direction']}">
                        {icon} <b>{a['symbol']}</b> — {a['direction']} breakout<br>
                        <span class="meta">near ₹{a['close']} · candle {a['candle_time']}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                if source == "universe":
                    with cols[1]:
                        if st.button("Add to tracking", key=f"addalert_{a['symbol']}_{a['timeframe']}_{a['candle_time']}"):
                            scanner.add_to_watchlist(a["symbol"])
                            st.success(f"Added {a['symbol']}")


# ---------------------------------------------------------------------------
# Top-level views
# ---------------------------------------------------------------------------
view_tabs = st.tabs(["My tracking list", "NSE universe (₹1500cr+)", "Fundamentals"])

with view_tabs[0]:
    st.caption("Your own curated list — the source of truth for what you're actively watching.")
    st.subheader("Company announcements")
    if not all_announcements:
        st.write("No announcements yet for your tracking-list companies.")
    else:
        for a in all_announcements:
            st.markdown(
                f"""<div class="card announcement">
                📢 <b>{a['symbol']}</b> — {a['subject']}<br>
                <span class="meta">{a['date']}</span>
                </div>""",
                unsafe_allow_html=True,
            )
    st.subheader("Currently squeezing")
    render_squeeze_section("tracking")
    st.subheader("Alerts")
    render_alert_section("tracking")

with view_tabs[1]:
    st.caption(
        "Auto-built weekly from NSE's largest ~500 stocks, filtered to market cap ≥ ₹1500cr. "
        "Scanned the same way as your tracking list — click 'Add to tracking' on any setup you like."
    )
    st.subheader("Currently squeezing")
    render_squeeze_section("universe")
    st.subheader("Alerts")
    render_alert_section("universe")

with view_tabs[2]:
    st.caption("Screener-style fundamentals, built weekly for your tracking list + universe.")
    fund_tabs = st.tabs(["Ratios", "Results", "Custom screen", "Peer comparison", "Shareholding"])

    all_symbols = sorted(fund_data.keys())

    with fund_tabs[0]:
        if not all_symbols:
            st.write("No fundamentals data yet.")
        else:
            symbol = st.selectbox("Symbol", all_symbols, key="ratios_symbol")
            entry = fund_data.get(symbol, {})
            st.table({
                "Metric": ["P/E", "P/B", "ROE", "ROA", "ROCE", "Debt/Equity", "Market cap", "Sector", "Industry"],
                "Value": [
                    entry.get("pe"), entry.get("pb"), entry.get("roe"), entry.get("roa"),
                    entry.get("roce"), entry.get("debt_to_equity"), entry.get("market_cap"),
                    entry.get("sector"), entry.get("industry"),
                ],
            })

    with fund_tabs[1]:
        if not all_symbols:
            st.write("No fundamentals data yet.")
        else:
            symbol = st.selectbox("Symbol", all_symbols, key="results_symbol")
            quarters = fund_data.get(symbol, {}).get("recent_quarters", [])
            if not quarters:
                st.write("No quarterly results available for this symbol.")
            else:
                st.table(quarters)

    with fund_tabs[2]:
        st.write("Build a filter, e.g. P/E < 20 AND ROE > 0.15 (ratios are stored as decimals, so 15% = 0.15).")
        n_conditions = st.number_input("Number of conditions", min_value=1, max_value=5, value=1, step=1)
        conditions = []
        for i in range(int(n_conditions)):
            c1, c2, c3 = st.columns(3)
            metric = c1.selectbox("Metric", fundamentals.METRICS, key=f"metric_{i}")
            op = c2.selectbox("Operator", list(fundamentals.OPERATORS.keys()), key=f"op_{i}")
            value = c3.number_input("Value", key=f"value_{i}", value=0.0)
            conditions.append((metric, op, value))

        if st.button("Run screen"):
            results = fundamentals.run_screen(conditions)
            if not results:
                st.write("No matches.")
            else:
                for r in results:
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.write(f"**{r['symbol']}** — " + ", ".join(f"{m}: {r.get(m)}" for m in fundamentals.METRICS))
                    with c2:
                        if st.button("Add to tracking", key=f"screen_add_{r['symbol']}"):
                            scanner.add_to_watchlist(r["symbol"])
                            st.success(f"Added {r['symbol']}")

    with fund_tabs[3]:
        sectors = fundamentals.list_sectors()
        if not sectors:
            st.write("No sector data yet.")
        else:
            sector = st.selectbox("Sector", sectors)
            peers = fundamentals.peers_in_sector(sector)
            st.table([
                {"Symbol": p["symbol"], "P/E": p.get("pe"), "ROE": p.get("roe"), "ROCE": p.get("roce"),
                 "Debt/Equity": p.get("debt_to_equity"), "Market cap": p.get("market_cap")}
                for p in peers
            ])

    with fund_tabs[4]:
        st.caption("Best-effort — shareholding data is rarely available for NSE stocks via free sources.")
        if all_symbols:
            symbol = st.selectbox("Symbol", all_symbols, key="shareholding_symbol")
            if st.button("Check shareholding"):
                holding = fundamentals.get_shareholding(symbol)
                if holding is None:
                    st.write("Not available for this symbol.")
                else:
                    st.write(holding)

# ---------------------------------------------------------------------------
# In-app toasts + browser/desktop notifications
# ---------------------------------------------------------------------------
for a in new_alerts:
    st.toast(f"{a['symbol']} ({a['timeframe']}): {a['direction']} breakout detected", icon="🚨")
for a in new_announcements:
    st.toast(f"{a['symbol']}: {a['subject']}", icon="📢")

messages = [
    f"{a['symbol']} ({a['timeframe']}): {a['direction']} breakout near ₹{a['close']}"
    for a in new_alerts
] + [
    f"{a['symbol']}: {a['subject']}"
    for a in new_announcements
]

components.html(
    f"""
    <script>
    if (typeof Notification !== "undefined") {{
        if (Notification.permission !== "granted" && Notification.permission !== "denied") {{
            Notification.requestPermission();
        }}
        const messages = {messages!r};
        if (Notification.permission === "granted") {{
            messages.forEach(msg => new Notification("NSE Pattern Alert", {{ body: msg }}));
        }}
    }}
    </script>
    """,
    height=0,
)

st.caption(
    "First visit: your browser will ask permission to show notifications — allow it, "
    "and keep this tab open (even in the background) to keep getting live alerts."
)
