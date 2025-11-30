import streamlit as st
from helpers import go_to, load_css

st.markdown(load_css(), unsafe_allow_html=True)

def scan_page():
    if st.button("← Back"):
        go_to(st, "home")

    st.write("### 📷 Skin Analysis")

    img = st.file_uploader("Upload your face photo")

    if img:
        st.image(img, caption="Uploaded Image")
        st.success("Image received! AI skin analysis module will be added soon 💗")
