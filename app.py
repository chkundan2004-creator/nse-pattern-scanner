import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timezone

import scanner
import announcements
import fundamentals

st.set_page_config(page_title="NSE Pattern Scanner", layout="wide", page_icon="📈")

# ---------------------------------------------------------------------------
# Design system
# ---------------------------------------------------------------------------
# A trading-terminal identity: warm charcoal base (not pure black), a single
# brass/gold accent standing in for the exchange bell, muted up/down colors
# (not neon), Space Grotesk for headers, IBM Plex Mono for every number so
# prices actually read like a ticker.
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
    :root {
        --ink-950: #08090D;
        --ink-900: #10131A;
        --ink-850: #161A22;
        --ink-800: #1C212B;
        --line-700: #262B36;
        --line-600: #333A47;
        --gold-500: #C9A24B;
        --gold-300: #E9CE8C;
        --gold-glow: rgba(201,162,75,0.18);
        --mint-500: #3EAE7A;
        --mint-300: #7ED3AA;
        --mint-glow: rgba(62,174,122,0.16);
        --coral-500: #D9636B;
        --coral-300: #EB9BA0;
        --coral-glow: rgba(217,99,107,0.16);
        --blue-500: #5B8DB8;
        --text-100: #F2F3F6;
        --text-500: #8A90A0;
        --text-600: #676D7C;
    }

    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }

    .stApp {
        background:
            radial-gradient(ellipse 900px 400px at 15% -10%, var(--gold-glow) 0%, transparent 60%),
            var(--ink-950);
    }
    body, .stApp, p, div, span, label { font-family: 'Inter', sans-serif; color: var(--text-100); }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; letter-spacing: -0.015em; }
    .mono { font-family: 'IBM Plex Mono', monospace; }
    .block-container { padding-top: 2.2rem !important; max-width: 1180px; }

    /* --- Masthead --- */
    .masthead-wrap { margin-bottom: 26px; }
    .eyebrow {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.72em; letter-spacing: 0.16em;
        text-transform: uppercase; color: var(--gold-500); margin-bottom: 6px;
    }
    .masthead { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
    .masthead h1 {
        font-size: 2.1em !important; margin: 0 !important;
        background: linear-gradient(90deg, var(--text-100) 30%, var(--gold-300) 100%);
        -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
    }
    .masthead .bell {
        font-size: 1.3em; filter: drop-shadow(0 0 10px var(--gold-glow));
    }
    .subtitle { color: var(--text-500); font-size: 0.95em; margin-bottom: 24px; }

    /* --- Pulse strip: signature element --- */
    .pulse-strip {
        display: flex; gap: 0; border: 1px solid var(--line-700);
        border-radius: 14px; overflow: hidden; margin-bottom: 28px;
        background: linear-gradient(180deg, var(--ink-850) 0%, var(--ink-900) 100%);
        box-shadow: 0 8px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.03);
    }
    .pulse-cell {
        flex: 1; padding: 16px 20px; border-right: 1px solid var(--line-700);
        transition: background-color 0.15s ease; position: relative;
    }
    .pulse-cell:hover { background-color: rgba(201,162,75,0.05); }
    .pulse-cell:last-child { border-right: none; }
    .pulse-label {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.7em; letter-spacing: 0.1em;
        color: var(--text-600); text-transform: uppercase; margin-bottom: 6px;
    }
    .pulse-value {
        font-family: 'IBM Plex Mono', monospace; font-size: 1.9em; font-weight: 600; color: var(--gold-300);
        line-height: 1;
    }

    /* --- Section headers --- */
    .section-head { display: flex; align-items: baseline; gap: 10px; margin: 28px 0 12px 0; }
    .section-head h3 { margin: 0 !important; font-size: 1.15em !important; }
    .section-head .count {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.75em; color: var(--text-600);
        background: var(--ink-850); border: 1px solid var(--line-700); border-radius: 20px;
        padding: 1px 9px;
    }

    /* --- Sidebar --- */
    section[data-testid="stSidebar"] {
        background-color: var(--ink-900); border-right: 1px solid var(--line-700);
    }
    section[data-testid="stSidebar"] h2 {
        font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8em !important;
        letter-spacing: 0.12em; text-transform: uppercase; color: var(--gold-500) !important;
        border-bottom: 1px solid var(--line-700); padding-bottom: 10px; margin-bottom: 14px !important;
    }

    /* --- Tabs, restyled as a segmented control --- */
    div[data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line-700); margin-bottom: 4px; }
    button[data-baseweb="tab"] {
        font-family: 'Inter', sans-serif; font-weight: 500; color: var(--text-500);
        background-color: transparent; border-radius: 8px 8px 0 0; transition: color 0.15s ease;
    }
    button[data-baseweb="tab"]:hover { color: var(--gold-300); }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--gold-300); border-bottom: 2px solid var(--gold-500);
    }

    /* --- Buttons --- */
    div[data-testid="stButton"] button {
        border-radius: 7px; border: 1px solid var(--line-700); background-color: var(--ink-800);
        color: var(--text-100); font-size: 0.83em; transition: all 0.15s ease;
    }
    div[data-testid="stButton"] button:hover {
        border-color: var(--gold-500); color: var(--gold-300); background-color: var(--ink-850);
        box-shadow: 0 0 0 1px var(--gold-500);
    }

    /* --- Cards --- */
    .card {
        background: linear-gradient(180deg, var(--ink-850) 0%, var(--ink-900) 100%);
        border: 1px solid var(--line-700);
        border-left: 3px solid var(--line-600);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        height: 100%;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(0,0,0,0.4);
        border-color: var(--line-600);
    }
    .card.bullish { border-left-color: var(--mint-500); }
    .card.bullish:hover { box-shadow: 0 10px 24px rgba(0,0,0,0.4), 0 0 0 1px var(--mint-glow); }
    .card.bearish { border-left-color: var(--coral-500); }
    .card.bearish:hover { box-shadow: 0 10px 24px rgba(0,0,0,0.4), 0 0 0 1px var(--coral-glow); }
    .card.squeeze-active { border-left-color: var(--gold-500); }
    .card.squeeze-active:hover { box-shadow: 0 10px 24px rgba(0,0,0,0.4), 0 0 0 1px var(--gold-glow); }
    .card.squeeze-inactive { border-left-color: var(--line-700); opacity: 0.6; }
    .card.announcement { border-left-color: var(--blue-500); }
    .card .sym { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05em; }
    .card .meta { color: var(--text-500); font-size: 0.82em; margin-top: 5px; line-height: 1.5; }
    .card .meta .mono { color: var(--text-500); }

    div[data-testid="column"] { padding: 0 6px !important; }

    /* --- Badges --- */
    .badge {
        display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.66em;
        letter-spacing: 0.07em; text-transform: uppercase; padding: 3px 9px; border-radius: 20px;
        margin-left: 7px; vertical-align: middle;
    }
    .badge.bullish { background: var(--mint-glow); color: var(--mint-300); }
    .badge.bearish { background: var(--coral-glow); color: var(--coral-300); }
    .badge.active { background: var(--gold-glow); color: var(--gold-300); }
    .badge.idle { background: rgba(138,144,160,0.1); color: var(--text-600); }

    .empty-state {
        color: var(--text-600); font-size: 0.88em; padding: 22px 18px; font-style: italic;
        background: var(--ink-900); border: 1px dashed var(--line-700); border-radius: 10px;
        text-align: center;
    }

    a.card-link { text-decoration: none; color: inherit; display: block; height: 100%; }
    a.card-link .card { cursor: pointer; }
    a.card-link:hover .card { border-color: var(--line-600); }

    /* --- Form inputs: fix the dark-text-on-white-box bug --- */
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input {
        background-color: var(--ink-800) !important;
        color: var(--text-100) !important;
        border: 1px solid var(--line-700) !important;
        font-family: 'IBM Plex Mono', monospace !important;
        border-radius: 7px !important;
    }
    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus {
        border-color: var(--gold-500) !important; box-shadow: 0 0 0 1px var(--gold-500) !important;
    }
    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-testid="stTextInput"] input::placeholder {
        color: var(--text-600) !important;
    }
    div[data-baseweb="select"] > div {
        background-color: var(--ink-800) !important;
        border-color: var(--line-700) !important;
        border-radius: 7px !important;
    }
    div[data-baseweb="select"] * { color: var(--text-100) !important; }
    div[data-baseweb="popover"] ul {
        background-color: var(--ink-900) !important;
        border: 1px solid var(--line-700) !important;
    }
    div[data-baseweb="popover"] li:hover { background-color: var(--ink-800) !important; }

    hr { border-color: var(--line-700) !important; margin: 26px 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="masthead-wrap">
    <div class="eyebrow">Live · NSE · Pattern intelligence</div>
    <div class="masthead"><span class="bell">🔔</span><h1>NSE Pattern Scanner</h1></div>
    <div class="subtitle">Squeeze → breakout scanner across 5m / 15m / 1h / 1D · free data via yfinance, a few minutes delayed</div>
    </div>""",
    unsafe_allow_html=True,
)

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
# Pulse strip — signature element: an at-a-glance terminal-style readout
# ---------------------------------------------------------------------------
today_str = datetime.now(timezone.utc).date().isoformat()
alerts_today = sum(1 for a in alerts if str(a.get("detected_at", "")).startswith(today_str))
still_squeezing = sum(1 for p in pinned if p["still_active"])

st.markdown(
    f"""
    <div class="pulse-strip">
        <div class="pulse-cell"><div class="pulse-label">Tracking</div><div class="pulse-value">{len(current)}</div></div>
        <div class="pulse-cell"><div class="pulse-label">Squeezing now</div><div class="pulse-value">{still_squeezing}</div></div>
        <div class="pulse-cell"><div class="pulse-label">Alerts today</div><div class="pulse-value">{alerts_today}</div></div>
        <div class="pulse-cell"><div class="pulse-label">Universe</div><div class="pulse-value">{len(universe)}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------
TIMEFRAME_TO_TV_INTERVAL = {
    "5 min": "5",
    "15 min": "15",
    "1 hour": "60",
    "1 day": "D",
}


def chart_url(symbol, timeframe=None):
    """TradingView chart link for a symbol, opened at the same timeframe
    the breakout/squeeze was detected on."""
    base = symbol.replace(".NS", "").replace(".BO", "")
    url = f"https://www.tradingview.com/chart/?symbol=NSE:{base}"
    interval = TIMEFRAME_TO_TV_INTERVAL.get(timeframe)
    if interval:
        url += f"&interval={interval}"
    return url


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
                st.markdown(f'<div class="empty-state">Nothing pinned on the {label} timeframe right now.</div>', unsafe_allow_html=True)
                continue

            if source == "tracking":
                # 2-column grid — a real dashboard feel instead of a stacked list
                grid = st.columns(2)
                for i, s in enumerate(rows):
                    with grid[i % 2]:
                        status_label = "SQUEEZING" if s["still_active"] else "IDLE"
                        status_class = "active" if s["still_active"] else "idle"
                        css_class = "squeeze-active" if s["still_active"] else "squeeze-inactive"
                        st.markdown(
                            f"""<a class="card-link" href="{chart_url(s['symbol'], s['timeframe'])}" target="_blank">
                            <div class="card {css_class}">
                            <span class="sym">{s['symbol']}</span><span class="badge {status_class}">{status_label}</span>
                            <div class="meta">range <span class="mono">₹{s['squeeze_low']}–₹{s['squeeze_high']}</span>
                            &nbsp;·&nbsp; last close <span class="mono">₹{s['last_close']}</span>
                            &nbsp;·&nbsp; tightness <span class="mono">{s['tightness_ratio']}</span>
                            &nbsp;·&nbsp; as of {s['as_of']}</div>
                            </div></a>""",
                            unsafe_allow_html=True,
                        )
                        if st.button("Remove", key=f"remove_{s['symbol']}_{s['timeframe']}"):
                            scanner.remove_pinned_squeeze(s["symbol"], s["timeframe"])
                            st.rerun()
                continue

            for s in rows:
                status_label = "SQUEEZING" if s["still_active"] else "IDLE"
                status_class = "active" if s["still_active"] else "idle"
                css_class = "squeeze-active" if s["still_active"] else "squeeze-inactive"
                cols = st.columns([5, 1, 1])
                with cols[0]:
                    st.markdown(
                        f"""<a class="card-link" href="{chart_url(s['symbol'], s['timeframe'])}" target="_blank">
                        <div class="card {css_class}">
                        <span class="sym">{s['symbol']}</span><span class="badge {status_class}">{status_label}</span>
                        <div class="meta">range <span class="mono">₹{s['squeeze_low']}–₹{s['squeeze_high']}</span>
                        &nbsp;·&nbsp; last close <span class="mono">₹{s['last_close']}</span>
                        &nbsp;·&nbsp; tightness <span class="mono">{s['tightness_ratio']}</span>
                        &nbsp;·&nbsp; as of {s['as_of']}</div>
                        </div></a>""",
                        unsafe_allow_html=True,
                    )
                with cols[1]:
                    if st.button("Add to tracking", key=f"add_{s['symbol']}_{s['timeframe']}"):
                        scanner.add_to_watchlist(s["symbol"])
                        st.success(f"Added {s['symbol']}")
                with cols[2]:
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
                st.markdown(f'<div class="empty-state">No {label} alerts yet.</div>', unsafe_allow_html=True)
                continue

            if source == "tracking":
                grid = st.columns(2)
                for i, a in enumerate(rows):
                    badge_class = "bullish" if a["direction"] == "bullish" else "bearish"
                    with grid[i % 2]:
                        st.markdown(
                            f"""<a class="card-link" href="{chart_url(a['symbol'], a['timeframe'])}" target="_blank">
                            <div class="card {a['direction']}">
                            <span class="sym">{a['symbol']}</span><span class="badge {badge_class}">{a['direction']}</span>
                            <div class="meta">breakout near <span class="mono">₹{a['close']}</span>
                            &nbsp;·&nbsp; candle {a['candle_time']}</div>
                            </div></a>""",
                            unsafe_allow_html=True,
                        )
                continue

            for a in rows:
                badge_class = "bullish" if a["direction"] == "bullish" else "bearish"
                cols = st.columns([5, 1])
                with cols[0]:
                    st.markdown(
                        f"""<a class="card-link" href="{chart_url(a['symbol'], a['timeframe'])}" target="_blank">
                        <div class="card {a['direction']}">
                        <span class="sym">{a['symbol']}</span><span class="badge {badge_class}">{a['direction']}</span>
                        <div class="meta">breakout near <span class="mono">₹{a['close']}</span>
                        &nbsp;·&nbsp; candle {a['candle_time']}</div>
                        </div></a>""",
                        unsafe_allow_html=True,
                    )
                with cols[1]:
                    if st.button("Add to tracking", key=f"addalert_{a['symbol']}_{a['timeframe']}_{a['candle_time']}"):
                        scanner.add_to_watchlist(a["symbol"])
                        st.success(f"Added {a['symbol']}")


def section_head(title, count):
    st.markdown(
        f'<div class="section-head"><h3>{title}</h3><span class="count">{count}</span></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Top-level views
# ---------------------------------------------------------------------------
view_tabs = st.tabs(["My tracking list", "NSE universe (₹1500cr+)", "Fundamentals"])

with view_tabs[0]:
    st.caption("Your own curated list — the source of truth for what you're actively watching.")
    section_head("Company announcements", len(all_announcements))
    if not all_announcements:
        st.markdown('<div class="empty-state">No announcements yet for your tracking-list companies.</div>', unsafe_allow_html=True)
    else:
        grid = st.columns(2)
        for i, a in enumerate(all_announcements):
            with grid[i % 2]:
                st.markdown(
                    f"""<a class="card-link" href="{chart_url(a['symbol'])}" target="_blank">
                    <div class="card announcement">
                    <span class="sym">{a['symbol']}</span>
                    <div class="meta">{a['subject']}<br>{a['date']}</div>
                    </div></a>""",
                    unsafe_allow_html=True,
                )
    section_head("Currently squeezing", sum(1 for p in pinned if p["source"] == "tracking"))
    render_squeeze_section("tracking")
    section_head("Alerts", sum(1 for a in alerts if a["source"] == "tracking"))
    render_alert_section("tracking")

with view_tabs[1]:
    st.caption(
        "Auto-built weekly from NSE's largest ~500 stocks, filtered to market cap ≥ ₹1500cr. "
        "Scanned the same way as your tracking list — click 'Add to tracking' on any setup you like."
    )
    section_head("Currently squeezing", sum(1 for p in pinned if p["source"] == "universe"))
    render_squeeze_section("universe")
    section_head("Alerts", sum(1 for a in alerts if a["source"] == "universe"))
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
# Browser/desktop notifications only — no in-app toasts, since seeing the
# alert on-screen already covers you while the tab is actually open in
# front of you. The notification below only fires when the tab is
# backgrounded or unfocused.
# ---------------------------------------------------------------------------
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
        const tabIsHiddenOrUnfocused = document.hidden || !document.hasFocus();
        if (Notification.permission === "granted" && tabIsHiddenOrUnfocused) {{
            messages.forEach(msg => new Notification("NSE Pattern Alert", {{ body: msg }}));
        }}
    }}
    </script>
    """,
    height=0,
)

st.caption(
    "First visit: your browser will ask permission to show notifications — allow it. "
    "Notifications only pop up while this tab is in the background or unfocused, "
    "not while you're actively looking at it."
)
