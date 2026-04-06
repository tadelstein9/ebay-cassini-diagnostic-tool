import streamlit as st
import pandas as pd
from cassini_analyzer import analyze_listings

st.set_page_config(
    page_title="Cassini Tool",
    layout="wide",
    page_icon="📈"
)

st.title("📈 Cassini Tool")
st.markdown("**Helping eBay sellers improve titles and increase sales**")

# Navigation using clean tabs
tab1, tab2, tab3 = st.tabs(["Upload Active Listings CSV", "Prioritized Fix List", "Download Report"])

with tab1:
    st.subheader("Step 1: Upload your CSV")
    st.info("Export your Active Listings from eBay Seller Hub → Upload the CSV here.")
    
    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])
    
    if uploaded_file is not None:
        with st.spinner("Analyzing your listings for Cassini optimization..."):
            df = pd.read_csv(uploaded_file)
            results = analyze_listings(df)
        st.success(f"✅ Successfully analyzed {len(results)} listings!")

with tab2:
    if 'results' in locals():
        st.subheader("Prioritized Fix List (Fix Lowest Scores First)")
        
        # Display the main results
        display_cols = ['Priority', 'Title', 'Cassini Score', 'Main Issue', 'Suggested Title']
        st.dataframe(
            results[display_cols].style.hide(axis="index"),
            use_container_width=True
        )
        
        # Narrative Summary
        avg_score = results['Cassini Score'].mean()
        st.subheader("Summary & Action Plan")
        st.markdown(f"""
        **Your average Cassini score:** `{avg_score:.0f}/100`

        **Biggest quick win:** Add **"New without tags"** at the end of titles and move your strongest keywords to the front (Waldemar, Double Albert, Arnex, Unitas 6498, etc.).

        **Recommended Action Today:**
        1. Start with the top 10–12 listings in the table above.
        2. Use **Sell Similar** on eBay and paste the Suggested Title.
        3. Add "New without tags" in the description if needed.
        4. Turn on Promoted Listings (5–8%) for your strongest items.
        
        These changes typically move many listings from the 40-60 range up to 75+ and replicate the big weekend sales you’ve already seen.
        """)
    else:
        st.info("↑ Upload your CSV file to see prioritized fixes and suggested titles.")

with tab3:
    if 'results' in locals():
        st.subheader("Export Your Report")
        
        # CSV Download
        csv = results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full Report as CSV",
            data=csv,
            file_name="cassini_recommendations.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.info("**Mobile / iPad users:** Open the downloaded CSV in the Google Sheets or Microsoft Excel app → tap Share → Print → Save as PDF. Or simply use your browser’s Print → Save as PDF option.")
        
        st.caption("Built for USWatchMasters • Helping the eBay community")
    else:
        st.info("Upload a CSV first to generate your report.")
