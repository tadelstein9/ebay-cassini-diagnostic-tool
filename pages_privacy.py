"""
Privacy policy page. Rendered when ?page=privacy appears in the URL.
Reads content from privacy_policy.md so edits are content-only.
"""
from pathlib import Path
import streamlit as st


def render():
    st.title("Privacy Policy")
    policy_path = Path(__file__).parent / "privacy_policy.md"
    if policy_path.exists():
        st.markdown(policy_path.read_text(encoding="utf-8"))
    else:
        st.error(
            "Privacy policy content is missing. "
            "This is a deployment error; please contact paul@pierotti.net."
        )
    st.markdown("---")
    st.caption("[Back to Bynari Insight](./)")
