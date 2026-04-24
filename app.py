"""
Bynari Insight - Onboarding app for new eBay sellers

Current state: skeleton only. Routing and landing page are live so the
Streamlit Cloud deployment has something to serve. Stages 1-8 wire in
through Session 1+ work on paris-06.
"""
import streamlit as st

from pages_privacy import render as render_privacy

st.set_page_config(
    page_title="Bynari Insight",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

query_params = st.query_params
route = query_params.get("page", "home")

if route == "privacy":
    render_privacy()
else:
    st.title("Bynari Insight")
    st.write(
        "A guided walkthrough for preparing an eBay listing — "
        "category, item specifics, photos, condition, title, and description."
    )
    st.info("Coming soon. This is an early deployment placeholder while the app is built.")
    st.markdown("---")
    st.caption("Built by Bynari. [Privacy policy](?page=privacy)")
