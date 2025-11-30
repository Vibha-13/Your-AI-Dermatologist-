import streamlit as st
from helpers import append_message, go_to, load_css

st.markdown(load_css(), unsafe_allow_html=True)

def chat_page():
    if st.button("← Back"):
        go_to(st, "home")

    st.write("### 🩺 AI Dermatologist Chat")

    for m in st.session_state.messages:
        bubble = "derm-bubble" if m["role"] == "assistant" else "user-bubble"
        st.markdown(f"<div class='{bubble}'>{m['text']}</div>", unsafe_allow_html=True)

    text = st.text_input("Your message:")
    if st.button("Send") and text.strip():
        append_message(st, "user", text)
        append_message(st, "assistant", "I'm still upgrading! Full AI chat will return soon 💖")
