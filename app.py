# app.py
# eBay Cassini Diagnostic Tool - Clean Free Version
# April 05, 2026

import streamlit as st
import pandas as pd
from cassini_analyzer import analyze_listings, get_summary

st.set_page_config(
    page_title="eBay Cassini Diagnostic Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.markdown("### 📊 Cassini Tool")
    st.markdown("**Free Version**")
    st.markdown("---")
    st.markdown("**Navigation**")
    st.markdown("- Upload Active Listings CSV")
    st.markdown("- Prioritized Fix List")
    st.markdown("- Suggested Titles")
    st.markdown("- CSV Report")
    st.markdown("---")
    st.caption("Built for USWatchMasters\nHelping sellers improve titles and increase sales")

st.title("📊 eBay Cassini Diagnostic Tool")
st.markdown("**Free version** — Upload your Seller Hub Active Listings CSV and get prioritized fixes + suggested titles.")

st.markdown("---")

uploaded_file = st.file_uploader(
    "Upload your eBay Active Listings CSV", 
    type=["csv"], 
    help="Best results with the 'All active listings' report from Seller Hub > Reports"
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        st.success(f"✅ Loaded {len(df)} active listings")

        with st.spinner("Analyzing for Cassini optimization..."):
            report = analyze_listings(df)
            summary = get_summary(report)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Listings", summary["Total Listings"])
        with col2:
            st.metric("Average Cassini Score", summary["Average Cassini Score"])
        with col3:
            st.metric("CRITICAL to Fix", summary["CRITICAL to Fix"])
        with col4:
            st.metric("HIGH Priority", summary["HIGH Priority"])

        st.info(f"**{summary['High Potential Items']}** high-potential listings (Waldemar, Double Albert, Arnex/Unitas). Fix CRITICAL and HIGH first.")

        st.subheader("🔥 Prioritized Fix List")
        st.markdown("**Fix order:** CRITICAL → HIGH → MEDIUM → GOOD")

        display_cols = ["Priority", "Cassini Score", "Title", "Suggested Title", "Issues", "Fixes", "Available Qty", "Price", "Views"]
        st.dataframe(report[display_cols], use_container_width=True, hide_index=True)

        csv = report.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full Report as CSV",
            data=csv,
            file_name="cassini_diagnostic_report.csv",
            mime="text/csv"
        )

        st.success("""💡 **Pro Tip for New eBay Form:**
Copy the Suggested Title and paste it when creating a new listing.
Add "New without tags" at the very end of the title.
Put detailed condition info in the Description field if the label is missing.""")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Make sure it's a valid eBay Active Listings CSV from Seller Hub.")

else:
    st.info("👆 Upload your Active Listings CSV to begin analysis.")

st.caption("Free tool by Tom Adelstein • USWatchMasters • Optimized for 2026 eBay changes")
