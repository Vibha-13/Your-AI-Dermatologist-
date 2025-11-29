import streamlit as st
from datetime import datetime
from config import c, conn
from helpers import go_to
# ========== LOAD GLOBAL CSS ==========
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_appointments():
    if st.button("← Back"):
        go_to(st, "home")

    st.markdown("### 📅 Book Appointment")

    with st.form("form"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        city = st.text_input("City")
        date = st.date_input("Preferred date", min_value=datetime.today())
        time = st.time_input("Preferred time")
        reason = st.text_area("Reason")

        submit = st.form_submit_button("Book")

        if submit:
            c.execute(
                "INSERT INTO bookings (name,email,city,date,time,reason,created_at) VALUES (?,?,?,?,?,?,?)",
                (name, email, city, str(date), str(time), reason, datetime.utcnow().isoformat())
            )
            conn.commit()
            st.success("Appointment saved!")
