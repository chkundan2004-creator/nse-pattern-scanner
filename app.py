# ===========================================================================
# TAB 3: Fundamentals (Screener.in Style)
# ===========================================================================
with tabs[2]:
    if all_symbols:
        symbol = st.selectbox("Select Stock", all_symbols, key="screener_sym")
        data = fundamentals.load_fundamentals_data().get(symbol, {})
        
        if data:
            ratios = data.get("ratios", {})
            
            # --- Top Ratios Grid (Screener Style) ---
            st.markdown("### Top Ratios")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Market Cap", f"₹{ratios.get('market_cap', 0):,}" if ratios.get('market_cap') else "N/A")
            c2.metric("Current Price", f"₹{ratios.get('cmp', 'N/A')}")
            c3.metric("Stock P/E", ratios.get("pe", "N/A"))
            c4.metric("ROCE / ROE", f"{round(ratios.get('roe', 0)*100, 2)}%" if ratios.get("roe") else "N/A")
            
            st.markdown("---")
            
            # --- Sub-Tabs ---
            fund_tabs = st.tabs(["Quarterly Results", "Profit & Loss", "Peer Comparison", "About"])
            
            import pandas as pd
            
            with fund_tabs[0]:
                st.write("### Quarterly Results")
                q_data = data.get("quarters", [])
                if q_data:
                    st.dataframe(pd.DataFrame(q_data), use_container_width=True)
                else:
                    st.write("Quarterly data not available.")

            with fund_tabs[1]:
                st.write("### Profit & Loss (Annual)")
                pl_data = data.get("pl", [])
                if pl_data:
                    st.dataframe(pd.DataFrame(pl_data), use_container_width=True)
                else:
                    st.write("P&L data not available.")

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
