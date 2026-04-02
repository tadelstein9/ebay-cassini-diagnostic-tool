import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

try:
    from cassini_score import calculate_cassini_score
except ImportError:
    def calculate_cassini_score(listing_data):
        return {"overall_score": 75}

st.set_page_config(page_title="eBay Cassini Diagnostic Tool", layout="wide")

st.title("📊 eBay Cassini Diagnostic Tool")
st.markdown("**Built for hurting sellers** — Fix zero views and failing sales")

tab1, tab2, tab3 = st.tabs(["🏠 Home", "📱 New Listing Optimizer", "📊 Portfolio Analyzer"])

with tab1:
    st.markdown("### Welcome")
    st.markdown("This free tool helps eBay sellers understand why listings get zero views and gives clear fixes.")
    st.markdown("""
    - **New Listing Optimizer** — Build or upgrade listings with live Cassini scoring
    - **Portfolio Analyzer** — Upload your CSV and see exactly which listings to fix first
    """)
    st.caption("Made with Tom Adelstein for the eBay community. Free and open source.")

with tab2:
    st.subheader("New Listing / Sell Similar Optimizer")
    st.info("Full version coming in next update.")

with tab3:
    st.subheader("📊 Portfolio Analyzer")
    uploaded_file = st.file_uploader("Upload your Active Listings CSV from Seller Hub", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success(f"Loaded {len(df)} listings")
        df["Cassini_Score"] = df.apply(lambda row: calculate_cassini_score({"title": str(row.get('Title', ''))})["overall_score"], axis=1)
        st.metric("Average Cassini Score", f"{df['Cassini_Score'].mean():.1f}/100")
        st.subheader("Stale Listings (Sell Similar Candidates)")
        st.dataframe(df.sort_values("Cassini_Score").head(10)[["Title", "Cassini_Score"]])
        st.download_button("Download Full Report", df.to_csv(index=False), "portfolio_report.csv")

st.caption("This tool is free and open source. Built to help sellers struggling with Cassini.")
