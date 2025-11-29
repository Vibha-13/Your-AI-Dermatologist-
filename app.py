import streamlit as st
from config import setup_database, setup_session
from pages.home import render_home
from pages.chat import render_chat
from pages.scan import render_scan
from pages.history import render_history
from pages.appointments import render_appointments

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="SkinSync AI", layout="wide")

# ----------------------------
# LOAD EXTERNAL CSS
# ----------------------------
try:
    with open("style.css") as f:
        st.markdown("<style>" + f.read() + "</style>", unsafe_allow_html=True)
except:
    st.error("style.css missing!")

# ----------------------------
# FLOATING PARTICLES (Layer 4)
# ----------------------------
particle_html = ""
for i in range(5):
    particle_html += (
        f"<div class='particle' style='top:{10+i*20}%; "
        f"left:{15+i*12}%; animation-delay:{i*1.2}s;'></div>"
    )
st.markdown(particle_html, unsafe_allow_html=True)

# ----------------------------
# PARALLAX BACKLIGHT (Layer 4)
# ----------------------------
st.markdown("<div class='parallax-bg'></div>", unsafe_allow_html=True)

# ----------------------------
# DATABASE + SESSION
# ----------------------------
setup_database()
setup_session(st)

# ----------------------------
# PAGE ROUTING
# ----------------------------
page = st.session_state.page

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

# ----------------------------
# FOOTER
# ----------------------------
st.caption(
    "SkinSync — educational skincare guidance. Severe or painful symptoms should be checked by a dermatologist."
)
