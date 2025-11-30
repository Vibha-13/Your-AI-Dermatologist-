import streamlit as st
from helpers import load_css, init_session

# Page imports
from pages.home import home_page
from pages.chat import chat_page
from pages.scan import scan_page
from pages.appointments import appointments_page
from pages.history import history_page

st.set_page_config(page_title="SkinSync AI", layout="wide")

# Load global CSS
st.markdown(load_css(), unsafe_allow_html=True)

# Prepare session variables
init_session(st)

# Page routing via query params
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

pages[page]()  # render the selected page
