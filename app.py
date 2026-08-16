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
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

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

/* --- Pulse strip --- */
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

/* --- Tabs --- */
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

/* --- Form inputs --- */
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
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="masthead-wrap">
      <div class="eyebrow">NSE Live Intelligence Terminal</div>
      <div class="masthead">
        <span class="bell">🔔</span>
        <h1>NSE Pattern Scanner</h1>
      </div>
      <div class="subtitle">Real-time TTM Squeeze, breakout alerts, corporate filings, and fundamentals for Indian equities.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("Tracking List")
current_list = scanner.load_tracking_list()
tracking_text = st.sidebar.text_area(
    "One NSE symbol per line (yfinance format, e.g. REDINGTON.NS)",
    value="\n".join(current_list),
    height=200,
)

if st.sidebar.button("Save tracking list"):
    new_symbols = [s.strip().upper() for s in tracking_text.splitlines() if s.strip()]
    scanner.save_tracking_list(new_symbols)
    st.sidebar.success(f"Saved {len(new_symbols)} symbols")
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Run scan now"):
    with st.spinner("Scanning..."):
        scanner.run_full_scan()
    st.rerun()

st_autorefresh(interval=30000, key="datarefresh")

components.html(
    """
    <script>
    if ("Notification" in window) {
      if (Notification.permission !== "granted" && Notification.permission !== "denied") {
        Notification.requestPermission();
      }
    }
    </script>
    """,
    height=0,
)

# Load current state
squeeze_data = scanner.load_squeeze_status()
alerts_data = scanner.load_alerts()
anns_data = announcements.load_announcements()
universe_squeeze_data = scanner.load_universe_squeeze_status()

all_symbols = sorted(list(set(current_list + list(squeeze_data.keys()))))
sq_count = sum(1 for v in squeeze_data.values() if v.get("squeeze_on"))
al_count = len(alerts_data)
an_count = len(anns_data)

# ---------------------------------------------------------------------------
# Pulse strip
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="pulse-strip">
      <div class="pulse-cell">
        <div class="pulse-label">Tracked Symbols</div>
        <div class="pulse-value">{len(current_list)}</div>
      </div>
      <div class="pulse-cell">
        <div class="pulse-label">Active Squeezes</div>
        <div class="pulse-value">{sq_count}</div>
      </div>
      <div class="pulse-cell">
        <div class="pulse-label">Recent Alerts</div>
        <div class="pulse-value">{al_count}</div>
      </div>
      <div class="pulse-cell">
        <div class="pulse-label">Filings Loaded</div>
        <div class="pulse-value">{an_count}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs(["Tracking List", "NSE Universe", "Fundamentals"])

# ===========================================================================
# TAB 1: Tracking List
# ===========================================================================
with tabs[0]:
    st.markdown(
        f'<div class="section-head"><h3>TTM Squeeze Status</h3><span class="count">{sq_count} active</span></div>',
        unsafe_allow_html=True,
    )

    if not squeeze_data:
        st.markdown(
            '<div class="empty-state">No squeeze data generated yet. Click "Run scan now" or wait for the scheduled job.</div>',
            unsafe_allow_html=True,
        )
    else:
        sq_items = [item for item in squeeze_data.items() if item[0] in current_list]
        if not sq_items:
            st.markdown(
                '<div class="empty-state">No squeeze data available for the currently tracked symbols.</div>',
                unsafe_allow_html=True,
            )
        else:
            sq_cols = st.columns(2)
            for idx, (sym, val) in enumerate(sq_items):
                col = sq_cols[idx % 2]
                sq_on = val.get("squeeze_on")
                mom = val.get("momentum", 0)
                mom_str = f"{mom:+.2f}" if mom is not None else "N/A"
                card_class = "squeeze-active" if sq_on else "squeeze-inactive"
                badge_class = "active" if sq_on else "idle"
                badge_text = "SQUEEZE ACTIVE" if sq_on else "NO SQUEEZE"

                with col:
                    st.markdown(
                        f"""
                        <div class="card {card_class}">
                          <div class="sym">{sym} <span class="badge {badge_class}">{badge_text}</span></div>
                          <div class="meta">
                            Momentum: <span class="mono">{mom_str}</span> |
                            Updated: <span class="mono">{val.get('timestamp', 'N/A')}</span>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.markdown(
        f'<div class="section-head"><h3>Pattern Alerts</h3><span class="count">{al_count} total</span></div>',
        unsafe_allow_html=True,
    )

    if not alerts_data:
        st.markdown(
            '<div class="empty-state">No active breakout alerts right now.</div>',
            unsafe_allow_html=True,
        )
    else:
        al_cols = st.columns(2)
        for idx, alert in enumerate(alerts_data):
            col = al_cols[idx % 2]
            direction = alert.get("direction", "").lower()
            badge_class = "bullish" if direction == "bullish" else "bearish"
            card_class = badge_class

            with col:
                st.markdown(
                    f"""
                    <div class="card {card_class}">
                      <div class="sym">{alert.get('symbol')} <span class="badge {badge_class}">{direction.upper()}</span></div>
                      <div class="meta">
                        {alert.get('message', '')}<br/>
                        <span class="mono">{alert.get('timestamp', '')}</span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(
        f'<div class="section-head"><h3>Corporate Filings & Announcements</h3><span class="count">{an_count} entries</span></div>',
        unsafe_allow_html=True,
    )

    if not anns_data:
        st.markdown(
            '<div class="empty-state">No corporate announcements captured yet.</div>',
            unsafe_allow_html=True,
        )
    else:
        an_cols = st.columns(2)
        for idx, ann in enumerate(anns_data):
            col = an_cols[idx % 2]
            url = ann.get("attachment_url", "")
            link_start = f'<a href="{url}" target="_blank" class="card-link">' if url else ""
            link_end = "</a>" if url else ""

            with col:
                st.markdown(
                    f"""
                    {link_start}
                    <div class="card announcement">
                      <div class="sym">{ann.get('symbol')} <span class="badge idle">FILING</span></div>
                      <div class="meta">
                        <strong>{ann.get('subject', '')}</strong><br/>
                        {ann.get('desc', '')}<br/>
                        <span class="mono">{ann.get('timestamp', '')}</span>
                      </div>
                    </div>
                    {link_end}
                    """,
                    unsafe_allow_html=True,
                )

# ===========================================================================
# TAB 2: NSE Universe
# ===========================================================================
with tabs[1]:
    u_count = len(universe_squeeze_data)
    st.markdown(
        f'<div class="section-head"><h3>Full NSE Market Squeeze Scan</h3><span class="count">{u_count} symbols</span></div>',
        unsafe_allow_html=True,
    )

    if not universe_squeeze_data:
        st.markdown(
            '<div class="empty-state">Universe list is empty — run "Build stock universe" once manually from the Actions tab on GitHub to fill it immediately.</div>',
            unsafe_allow_html=True,
        )
    else:
        active_u = {
            k: v for k, v in universe_squeeze_data.items() if v.get("squeeze_on")
        }
        st.write(
            f"Active Squeezes in Universe: **{len(active_u)}** / {len(universe_squeeze_data)}"
        )

        u_cols = st.columns(2)
        for idx, (sym, val) in enumerate(active_u.items()):
            col = u_cols[idx % 2]
            mom = val.get("momentum", 0)
            mom_str = f"{mom:+.2f}" if mom is not None else "N/A"

            with col:
                st.markdown(
                    f"""
                    <div class="card squeeze-active">
                      <div class="sym">{sym} <span class="badge active">SQUEEZE</span></div>
                      <div class="meta">
                        Momentum: <span class="mono">{mom_str}</span> |
                        Updated: <span class="mono">{val.get('timestamp', 'N/A')}</span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ===========================================================================
# TAB 3: Fundamentals
# ===========================================================================
with tabs[2]:
    fund_tabs = st.tabs(
        [
            "Overview",
            "Financials",
            "Quarterly",
            "Peer Comparison",
            "Shareholding Pattern",
        ]
    )

    with fund_tabs[0]:
        if all_symbols:
            symbol = st.selectbox(
                "Select Symbol for Fundamentals", all_symbols, key="fund_sym_overview"
            )
            if st.button("Fetch Overview"):
                with st.spinner("Fetching fundamentals..."):
                    data = fundamentals.get_company_overview(symbol)
                    if data:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Market Cap", f"₹{data.get('market_cap', 'N/A')}")
                        c2.metric("P/E Ratio", data.get("pe", "N/A"))
                        c3.metric("ROCE", f"{data.get('roce', 'N/A')}%")

                        st.write("### Business Summary")
                        st.write(
                            data.get(
                                "summary",
                                "No summary available for this company.",
                            )
                        )
                    else:
                        st.markdown(
                            '<div class="empty-state">Fundamentals not built yet — run "Build fundamentals" once manually from the Actions tab on GitHub.</div>',
                            unsafe_allow_html=True,
                        )

    with fund_tabs[1]:
        if all_symbols:
            symbol = st.selectbox("Select Symbol", all_symbols, key="fund_sym_fin")
            if st.button("Fetch Financial Statements"):
                financials = fundamentals.get_financials(symbol)
                if financials:
                    st.dataframe(financials, use_container_width=True)
                else:
                    st.write("Financial data not available.")

    with fund_tabs[2]:
        if all_symbols:
            symbol = st.selectbox("Select Symbol", all_symbols, key="fund_sym_qtr")
            if st.button("Fetch Quarterly Results"):
                qtr = fundamentals.get_quarterly_results(symbol)
                if qtr:
                    st.dataframe(qtr, use_container_width=True)
                else:
                    st.write("Quarterly data not available.")

    with fund_tabs[3]:
        if all_symbols:
            symbol = st.selectbox("Select Symbol", all_symbols, key="fund_sym_peers")
            if st.button("Fetch Peer Comparison") or f"peers_{symbol}" in st.session_state:
                if st.session_state.get("peers_symbol") != symbol:
                    st.session_state[f"peers_{symbol}"] = fundamentals.get_peer_comparison(symbol)
                    st.session_state["peers_symbol"] = symbol

                peers = st.session_state.get(f"peers_{symbol}")
                if peers:
                    st.dataframe(peers, use_container_width=True)
                else:
                    st.write("Peer comparison data not available.")

    with fund_tabs[4]:
        if all_symbols:
            symbol = st.selectbox("Symbol", all_symbols, key="shareholding_symbol")
            if st.button("Check shareholding"):
                holding = fundamentals.get_shareholding(symbol)
                if holding is None:
                    st.write("Not available for this symbol.")
                else:
                    st.write(holding)
