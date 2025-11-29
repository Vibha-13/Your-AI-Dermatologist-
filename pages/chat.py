import streamlit as st
# ========== LOAD GLOBAL CSS ==========
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from helpers import (
    append_message, detect_severe_keywords, build_system_prompt,
    call_openrouter_chat, go_to
)
from config import c, conn

def chat_page():
    if st.button("← Back"):
        go_to(st, "home")

    st.markdown("### 🩺 AI Dermatologist Chat")

    if not st.session_state.messages:
        append_message(
            st,
            "assistant",
            "Hi! I'm your SkinSync assistant 🌿 Tell me about your skin today."
        )

    for m in st.session_state.messages:
        if m["role"] == "assistant":
            st.markdown(f"<div class='derm-bubble'>{m['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='user-bubble'>{m['text']}</div>", unsafe_allow_html=True)

    user_input = st.text_input("You:", "")
    send = st.button("Send")
    save = st.button("💾 Save consult")

    if send and user_input.strip():
        append_message(st, "user", user_input)

        messages = [{"role": "system", "content": build_system_prompt(st)}]
        for m in st.session_state.messages:
            messages.append({"role": m["role"], "content": m["text"]})

        if detect_severe_keywords(user_input):
            warn = "Your symptoms sound serious — consider an in-person dermatologist."
            append_message(st, "assistant", warn)
            messages.append({"role": "assistant", "content": warn})

        reply, err = call_openrouter_chat(messages)
        if err:
            fallback = "I couldn't reach the AI engine — try again later."
            append_message(st, "assistant", fallback)
        else:
            append_message(st, "assistant", reply)
            st.session_state.last_plan = reply

    if save and st.session_state.last_plan:
        payload = {
            "profile": st.session_state.profile,
            "conversation": st.session_state.messages,
            "last_plan": st.session_state.last_plan,
        }
        c.execute(
            "INSERT INTO consults (session_id,data,created_at) VALUES (?,?,?)",
            (st.session_state.session_id, json.dumps(payload), datetime.utcnow().isoformat())
        )
        conn.commit()
        st.success("Saved!")
