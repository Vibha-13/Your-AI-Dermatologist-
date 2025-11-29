import streamlit as st
from config import setup_database, setup_session
from pages.home import render_home
from pages.chat import render_chat
from pages.scan import render_scan
from pages.history import render_history
from pages.appointments import render_appointments

st.set_page_config(page_title="SkinSync AI", layout="wide")

setup_database()
setup_session(st)

page = st.session_state.page

st.markdown("<style>" + open("style.css").read() + "</style>", unsafe_allow_html=True)


if page == "home":
    render_home()
elif page == "chat":
    render_chat()
elif page == "scan":
    render_scan()
elif page == "history":
    render_history()
elif page == "appointments":
    render_appointments()
