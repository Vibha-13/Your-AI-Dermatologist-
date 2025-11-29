import streamlit as st
from helpers import go_to

# ========== LOAD GLOBAL CSS ==========
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def home_page():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    prof = st.session_state.profile

    # ----------------------------
    # Parallax Floating Hero Text
    # ----------------------------
    st.markdown(
        """
        <div class="parallax-hero">
            <div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>
            <div class="hero-title">SkinSync</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ----------------------------
    # Interactive Floating Orb (Layer 5)
    # ----------------------------
    st.markdown(
        """
        <div class="derm-orb"></div>
        """,
        unsafe_allow_html=True
    )

    # Basic user info
    st.markdown(
        f"<p style='text-align:center;font-size:14px;margin-top:-4px;'>"
        f"Signed in as <strong>{prof['name'] or 'Guest'}</strong>"
        f"</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ----------------------------
    # Feature Cards (3D Tilt + Glow)
    # ----------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <a class="card-link" href="?page=chat">
                <div class="premium-card tilt-card glow">
                    <div class="card-header-line">
                        <span class="card-emoji">🩺</span>
                        <span>AI Dermatologist Chat</span>
                    </div>
                    <div class="card-subtitle">
                        Describe your skin and get a personalised routine.
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <a class="card-link" href="?page=scan">
                <div class="premium-card tilt-card glow">
                    <div class="card-header-line">
                        <span class="card-emoji">📷</span>
                        <span>Skin Analysis</span>
                    </div>
                    <div class="card-subtitle">
                        Upload a face photo for redness analysis.
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            """
            <a class="card-link" href="?page=appointments">
                <div class="premium-card tilt-card glow">
                    <div class="card-header-line">
                        <span class="card-emoji">📅</span>
                        <span>Appointments</span>
                    </div>
                    <div class="card-subtitle">
                        Book consultation slots easily.
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
            <a class="card-link" href="?page=history">
                <div class="premium-card tilt-card glow">
                    <div class="card-header-line">
                        <span class="card-emoji">📋</span>
                        <span>Consult History</span>
                    </div>
                    <div class="card-subtitle">
                        View saved routines & chats.
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
