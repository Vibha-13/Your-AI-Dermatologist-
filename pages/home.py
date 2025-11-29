import streamlit as st
from helpers import go_to

def render_home():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    prof = st.session_state.profile

    st.markdown('<div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">SkinSync</div>', unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;'>Signed in as <b>{prof['name'] or 'Guest'}</b></p>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<a class='card-link' href='?page=chat'><div class='premium-card'>🩺 AI Dermatologist Chat</div></a>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            "<a class='card-link' href='?page=scan'><div class='premium-card'>📷 Skin Analysis</div></a>",
            unsafe_allow_html=True
        )
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(
            "<a class='card-link' href='?page=appointments'><div class='premium-card'>📅 Appointments</div></a>",
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            "<a class='card-link' href='?page=history'><div class='premium-card'>📋 Consult History</div></a>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)
