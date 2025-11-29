import streamlit as st
import base64

# Import page functions
from pages.home import home_page
from pages.chat import chat_page
from pages.scan import scan_page
from pages.appointments import appointments_page
from pages.history import history_page

# -----------------------------
# STREAMLIT CONFIG
# -----------------------------
st.set_page_config(
    page_title="SkinSync AI",
    layout="wide",
)

# -----------------------------
# LOAD GLOBAL CSS
# -----------------------------
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# -----------------------------
# ROUTER MAP
# -----------------------------
pages = {
    "home": home_page,
    "chat": chat_page,
    "scan": scan_page,
    "appointments": appointments_page,
    "history": history_page,
}

# -----------------------------
# GET PAGE FROM QUERY PARAMS
# -----------------------------
query_params = st.query_params
page = query_params.get("page", ["home"])[0]

if page not in pages:
    page = "home"

# -----------------------------
# RENDER THE PAGE
# -----------------------------
pages[page]()
