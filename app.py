import streamlit as st
from pages.home import home_page
from pages.chat import chat_page
from pages.scan import scan_page
from pages.appointments import appointments_page
from pages.history import history_page
import base64

st.set_page_config(
    page_title="SkinSync AI",
    layout="wide",
)

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

pages = {
    "home": home_page,
    "chat": chat_page,
    "scan": scan_page,
    "appointments": appointments_page,
    "history": history_page,
}

query_params = st.query_params
page = query_params.get("page", ["home"])[0]

if page not in pages:
    page = "home"

pages[page]()