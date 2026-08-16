import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
import pandas as pd

import scanner
import announcements
import fundamentals

st.set_page_config(
    page_title="NSE Pattern Scanner",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# Design System & Styling
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
  background: radial-gradient(ellipse 900px 400px at 15% -10%, var(--gold-glow) 0%, transparent 60%), var(--ink-950);
}
body, .stApp, p, div, span, label { font-family: 'Inter', sans-serif; color: var(--text-100); }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; }

/* Force Sidebar Dark Styling */
section[data-testid="stSidebar"] {
  background-color: var(--ink-900) !important;
  border-right: 1px solid var(--line-700) !important;
}
section[data-testid="stSidebar"] * {
  color: var(--text-100) !important;
}
section[data-testid="stSidebar"] textarea {
  background-color: var(--ink-800) !important;
  color: var(--text-100) !important;
  border: 1px solid var(--line-700) !important;
}
section[data-testid="stSidebar"] h2 {
  color: var(--gold-500) !important;
}

/* Pulse strip */
.pulse-strip {
  display: flex; gap: 0; border: 1px solid var(--line-700);
  border-radius: 14px; overflow: hidden; margin-bottom: 28px;
  background: linear-gradient(180deg, var(--ink-850) 0%, var(--ink-900) 100%);
}
.pulse-cell { flex: 1; padding: 16px 20px; border-right: 1px solid var(--line-700); }
.pulse-cell:last-child { border-right: none; }
.pulse-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.7em; color: var(--text-600); text-transform: uppercase; }
.pulse-value { font-family: 'IBM Plex Mono', monospace; font-size: 1.9em; font-weight: 600; color: var(--gold-300); }

/* Cards */
.card {
  background: linear-gradient(180deg, var(--ink-850) 0%, var(--ink-900) 100%);
  border: 1px solid var(--line-700); border-left: 3px solid var(--line-600);
  border-radius: 10px; padding: 14px 18px; margin-bottom: 10px;
}
.card.squeeze-active { border-left-color: var(--gold-500); }
.card.squeeze-inactive { border-left-color: var(--line-700); opacity: 0.6; }
.card.bullish { border-left-color: var(--mint-500); }
.card.bearish { border-left-color: var(--coral-500); }
.card.announcement { border-left-color: var(--blue-500); }
.card .sym { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05em; }
.card .meta { color: var(--text-500); font-size: 0.82em; margin-top: 5px; }
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div style="margin-bottom:26px;">
      <div style="font-family:'IBM Plex Mono'; font-size:0.72em; color:var(--gold-500); text-transform:uppercase;">NSE Live Intelligence Terminal</div>
      <h1 style="font-size:2.1em; margin:0; background:linear-gradient(90deg,#F2F3F6,#E9CE8C); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">NSE Pattern Scanner</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar
st.sidebar.header("Tracking List")
current_list = scanner.load_tracking_list()
tracking_text = st.sidebar.text_area(
    "One NSE symbol per line", value="\n".join(current_list), height=200
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

# Data loading
squeeze_data = scanner.load_squeeze_status()
alerts_data = scanner.load_alerts()
anns_data = announcements.load_announcements()
universe_squeeze_data = scanner.load_universe_squeeze_status()

all_symbols = sorted(list(set(current_list + list(squeeze_data.keys()))))
sq_count = sum(1 for v in squeeze_data.values() if v.get("squeeze_on"))

# Pulse strip
st.markdown(
    f"""
    <div class="pulse-strip">
      <div class="pulse-cell"><div class="pulse-label">Tracked Symbols</div><div class="pulse-value">{len(current_list)}</div></div>
      <div class="pulse-cell"><div class="pulse-label">Active Squeezes</div><div class="pulse-value">{sq_count}</div></div>
      <div class="pulse-cell"><div class="pulse-label">Recent Alerts</div><div class="pulse-value">{len(alerts_data)}</div></div>
      <div class="pulse-cell"><div class="pulse-label">Filings Loaded</div><div class="pulse-value">{len(anns_data)}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Tab Creation
tabs = st.tabs(["Tracking List", "NSE Universe", "Fundamentals"])

# ===========================================================================
# TAB 1: Tracking List
# ===========================================================================
with tabs[0]:
    st.write("### TTM Squeeze Status")
    sq_items = [item for item in squeeze_data.items() if item[0] in current_list]
    if not sq_items:
        st.info("No squeeze data available.")
    else:
        cols = st.columns(2)
        for idx, (sym, val) in enumerate(sq_items):
            sq_on = val.get("squeeze_on")
            card_class = "squeeze-active" if sq_on else "squeeze-inactive"
            badge = "SQUEEZE ACTIVE" if sq_on else "NO SQUEEZE"
            with cols[idx % 2]:
                st.markdown(
                    f"""<div class="card {card_class}"><div class="sym">{sym} ({badge})</div>
                    <div class="meta">Momentum: {val.get('momentum', 0):+.2f}</div></div>""",
                    unsafe_allow_html=True,
                )

# ===========================================================================
# TAB 2: NSE Universe
# ===========================================================================
with tabs[1]:
    st.write("### Full NSE Market Squeeze Scan")
    active_u = {k: v for k, v in universe_squeeze_data.items() if v.get("squeeze_on")}
    if not active_u:
        st.info("Universe list empty or no active squeezes.")
    else:
        cols = st.columns(2)
        for idx, (sym, val) in enumerate(active_u.items()):
            with cols[idx % 2]:
                st.markdown(
                    f"""<div class="card squeeze-active"><div class="sym">{sym} (SQUEEZE)</div>
                    <div class="meta">Momentum: {val.get('momentum', 0):+.2f}</div></div>""",
                    unsafe_allow_html=True,
                )

# ===========================================================================
# TAB 3: Fundamentals (Screener.in Style)
# ===========================================================================
with tabs[2]:
    if all_symbols:
        symbol = st.selectbox("Select Stock", all_symbols, key="screener_sym")
        data = fundamentals.load_fundamentals_data().get(symbol, {})

        if data:
            ratios = data.get("ratios", {})

            st.markdown("### Top Ratios")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Market Cap", f"₹{ratios.get('market_cap', 0):,}" if ratios.get("market_cap") else "N/A")
            c2.metric("Current Price", f"₹{ratios.get('cmp', 'N/A')}")
            c3.metric("Stock P/E", ratios.get("pe", "N/A"))
            c4.metric("ROCE / ROE", f"{round(ratios.get('roe', 0)*100, 2)}%" if ratios.get("roe") else "N/A")

            st.markdown("---")

            fund_tabs = st.tabs(["Quarterly Results", "Profit & Loss", "Peer Comparison", "About"])

            with fund_tabs[0]:
                st.write("### Quarterly Results")
                q_data = data.get("quarters", [])
                st.dataframe(pd.DataFrame(q_data), use_container_width=True) if q_data else st.write("Quarterly data not available.")

            with fund_tabs[1]:
                st.write("### Profit & Loss (Annual)")
                pl_data = data.get("pl", [])
                st.dataframe(pd.DataFrame(pl_data), use_container_width=True) if pl_data else st.write("P&L data not available.")

            with fund_tabs[2]:
                st.write("### Peer Comparison")
                peers = fundamentals.get_peer_comparison(symbol)
                if peers:
                    st.dataframe(pd.DataFrame(peers), use_container_width=True)

            with fund_tabs[3]:
                st.write("### About Company")
                st.write(ratios.get("summary", "No business summary available."))
        else:
            st.info("No data built yet for this symbol. Run 'Build fundamentals' from GitHub Actions.")
