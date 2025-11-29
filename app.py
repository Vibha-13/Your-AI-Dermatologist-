import streamlit as st

# ---- Import Pages ----
from pages.home import home_page
from pages.chat import chat_page
from pages.scan import scan_page
from pages.appointments import appointments_page
from pages.history import history_page


# ================================
# SESSION STATE INITIALIZATION
# ================================
if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "",
        "age_bucket": "18–24",
        "skin_type": "Combination",
        "main_concern": "Acne / Breakouts",
        "sensitivity": "Normal",
        "location": "",
    }

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_plan" not in st.session_state:
    st.session_state.last_plan = None

if "session_id" not in st.session_state:
    st.session_state.session_id = "local"


# ================================
# STREAMLIT CONFIG
# ================================
st.set_page_config(
    page_title="SkinSync AI",
    layout="wide",
)

# Load global CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ================================
# PAGE ROUTING
# ================================
pages = {
    "home": home_page,
    "chat": chat_page,
    "scan": scan_page,
    "appointments": appointments_page,
    "history": history_page,
}

# Read URL query parameters
query_params = st.query_params
page = query_params.get("page", ["home"])[0]

# Safety check → default to home
if page not in pages:
    page = "home"

# Render the selected page
pages[page]()
