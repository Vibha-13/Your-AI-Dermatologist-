import streamlit as st
from helpers import c, go_to, load_css

st.markdown(load_css(), unsafe_allow_html=True)

def history_page():
    if st.button("← Back"):
        go_to(st, "home")

    st.write("### 📋 Consult History")

    rows = c.execute("SELECT data, created_at FROM consults ORDER BY id DESC").fetchall()

    if not rows:
        st.info("No saved consultations yet.")
        return

    for data, created in rows:
        st.write(f"**{created}**")
        st.json(data)
        st.markdown("---")
