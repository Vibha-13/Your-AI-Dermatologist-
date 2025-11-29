import streamlit as st
from PIL import Image
from io import BytesIO
from helpers import analyze_skin_image, go_to
# ========== LOAD GLOBAL CSS ==========
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_scan():
    if st.button("← Back"):
        go_to(st, "home")

    st.markdown("### 📷 Skin Image Analysis")

    uploaded = st.file_uploader("Upload a face photo", type=["png", "jpg", "jpeg"])

    if uploaded:
        img = Image.open(BytesIO(uploaded.read()))
        st.image(img, caption="Uploaded Image", use_column_width=True)

        if st.button("Analyze"):
            score, severity = analyze_skin_image(img)
            st.write(f"Redness Score: `{score:.2f}`")
            st.write(f"Severity: **{severity}**")
