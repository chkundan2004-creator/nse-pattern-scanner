import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

import scanner

st.set_page_config(page_title="NSE Pattern Scanner", layout="wide")
st.title("NSE Pattern Scanner")
st.caption("Squeeze -> breakout scanner across 5m / 15m / 1h / 1D timeframes. Free data via yfinance (may be a few minutes delayed).")

# Refresh the whole page every 60 seconds while it's open, so alerts stay current.
st_autorefresh(interval=60_000, key="auto_refresh")

# --- Sidebar: editable watchlist ---
st.sidebar.header("Watchlist")
current = scanner.load_watchlist()
text = st.sidebar.text_area(
    "One NSE symbol per line (yfinance format, e.g. REDINGTON.NS)",
    value="\n".join(current),
    height=200,
)
if st.sidebar.button("Save watchlist"):
    symbols = [s.strip() for s in text.splitlines() if s.strip()]
    scanner.save_watchlist(symbols)
    st.sidebar.success(f"Saved {len(symbols)} symbols.")

manual_scan = st.sidebar.button("Run scan now")

# --- Run a scan (manual click, or every auto-refresh) ---
new_alerts = scanner.scan()

if manual_scan and not new_alerts:
    st.sidebar.info("Scanned - no new pattern found this time.")

# --- Alert feed ---
st.subheader("Alerts")
alerts = scanner.load_alerts()

if not alerts:
    st.write("No alerts yet. Alerts will appear here as soon as a pattern is detected.")
else:
    for a in alerts:
        icon = "🟢" if a["direction"] == "bullish" else "🔴"
        st.write(
            f"{icon} **{a['symbol']}** — {a['timeframe']} — {a['direction']} "
            f"breakout near ₹{a['close']} — candle {a['candle_time']}"
        )

# --- In-app toast for brand new alerts this run ---
for a in new_alerts:
    st.toast(f"{a['symbol']} ({a['timeframe']}): {a['direction']} breakout detected", icon="🚨")

# --- Browser/desktop notifications ---
# Runs in the user's browser. Needs one-time permission grant.
if new_alerts:
    messages = [
        f"{a['symbol']} ({a['timeframe']}): {a['direction']} breakout near ₹{a['close']}"
        for a in new_alerts
    ]
else:
    messages = []

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
