import streamlit as st
from helpers import go_to, load_css

st.markdown(load_css(), unsafe_allow_html=True)

def home_page():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    prof = st.session_state.profile

    st.markdown("""
        <div class="parallax-hero">
            <div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>
            <div class="hero-title">SkinSync</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="derm-orb"></div>', unsafe_allow_html=True)

    st.write(f"### Signed in as **{prof['name']}**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🩺 AI Dermatologist Chat"):
            go_to(st, "chat")

    with col2:
        if st.button("📷 Skin Analysis"):
            go_to(st, "scan")

    col3, col4 = st.columns(2)

    with col3:
        if st.button("📅 Appointments"):
            go_to(st, "appointments")

    with col4:
        if st.button("📋 Consult History"):
            go_to(st, "history")

    st.markdown("</div>", unsafe_allow_html=True)
