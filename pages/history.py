import streamlit as st
import pandas as pd
import json
from config import conn
from helpers import go_to
from helpers import load_css
st.markdown(load_css(), unsafe_allow_html=True)



def history_page():
    if st.button("← Back"):
        go_to(st, "home")

    st.markdown("### 📋 Consult History")

    df = pd.read_sql_query(
        "SELECT id, session_id, data, created_at FROM consults ORDER BY id DESC LIMIT 100",
        conn,
    )

    if df.empty:
        st.info("No saved consults.")
        return

    ids = df["id"].tolist()
    selected = st.selectbox("Pick a consult ID", ids)

    if selected:
        row = df[df["id"] == selected].iloc[0]
        data = json.loads(row["data"])
        st.write("### Profile")
        st.json(data["profile"])

        st.write("### Routine")
        st.markdown(data["last_plan"])
