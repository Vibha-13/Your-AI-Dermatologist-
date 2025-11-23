import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import numpy as np
import requests
import time

# ========= ENV / API ==========
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ========= STREAMLIT CONFIG ==========
st.set_page_config(
    page_title="SkinSync — AI Dermatology",
    page_icon="💠",
    layout="wide",
)

# ========= GLOBAL CSS (clean girl aesthetic + splash) ==========
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=Playfair+Display:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Background: soft neutral clean-girl */
.stApp {
    background: linear-gradient(180deg, #fffefd 0%, #f6f3f2 40%, #efeceb 100%);
}

/* Animated Splash Screen */
.animated-splash {
    position: fixed;
    inset: 0;
    background: linear-gradient(180deg, #f9f7f6 0%, #f4efed 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 99999;
}
.splash-text {
    font-family: 'Playfair Display', serif;
    font-size: 64px;
    letter-spacing: 0.18em;
    color: #2d2220;
    position: relative;
    opacity: 0;
    animation: splashFadeIn 1.2s ease-out forwards,
               splashSlideUp 1.2s ease-out forwards;
}
.splash-text::after {
    content: "";
    position: absolute;
    top: 0;
    left: -150%;
    width: 60%;
    height: 100%;
    background: linear-gradient(120deg, transparent, rgba(255,255,255,0.7), transparent);
    animation: splashShine 1.4s ease-out forwards;
    animation-delay: 0.3s;
}

@keyframes splashFadeIn {
    0% { opacity: 0; }
    40% { opacity: 1; }
    100% { opacity: 1; }
}
@keyframes splashSlideUp {
    0% { transform: translateY(26px); }
    100% { transform: translateY(0); }
}
@keyframes splashShine {
    0% { left: -150%; }
    100% { left: 150%; }
}

/* Page fade-in */
.page-container {
    animation: fadeInUp 0.4s ease-out;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Hero */
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 40px;
    text-align: center;
    color: #2d2220;
    margin-bottom: 4px;
}
.hero-sub {
    text-align: center;
    color: #8a7b77;
    font-size: 13px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
}
.hero-tagline {
    text-align:center;
    color:#7b6a66;
    font-size: 14px;
    margin-top: 2px;
}

/* Feature grid & cards */
.feature-grid {
    max-width: 900px;
    margin: 2rem auto 1rem auto;
}
.card-link {
    text-decoration: none;
    color: inherit;
}
.premium-card {
    background: rgba(255,255,255,0.86);
    border-radius: 22px;
    padding: 20px 22px;
    border: 1px solid rgba(238,233,230,0.95);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow: 0 18px 40px rgba(0,0,0,0.06);
    transition: all 0.2s ease;
}
.premium-card:hover {
    transform: translateY(-6px) scale(1.01);
    box-shadow: 0 26px 60px rgba(0,0,0,0.12);
    border-color: #e1d6d1;
}
.card-header-line {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 16px;
    color: #362a28;
}
.card-emoji { font-size: 22px; }
.card-subtitle {
    font-size: 13px;
    color: #7a6965;
    margin-top: 3px;
}

/* Chat + bubbles */
.chat-card {
    background: rgba(255,255,255,0.88);
    padding: 20px 24px;
    border-radius: 20px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.06);
    border: 1px solid rgba(240,237,235,0.9);
}
.derm-bubble {
    background: white;
    padding: 12px 16px;
    border-radius: 16px;
    margin-bottom: 8px;
}
.user-bubble {
    background: #f3e9e7;
    padding: 12px 16px;
    border-radius: 16px;
    margin-left: 40px;
    margin-bottom: 8px;
}

/* Back button */
.back-button-container {
    max-width: 780px;
    margin: 0.5rem auto 0 auto;
}
.back-button-container button {
    background: white !important;
    border: 1px solid #e3dbd7 !important;
    color: #756864 !important;
    border-radius: 999px !important;
    padding: 4px 16px !important;
    font-size: 13px;
}

/* Helper text */
.small-muted {
    color:#9a8e8a;
    font-size:12px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ========= DB ==========
conn = sqlite3.connect("skinsync.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    city TEXT,
    date TEXT,
    time TEXT,
    reason TEXT,
    created_at TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS consults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    data TEXT,
    created_at TEXT
)
""")
conn.commit()

# ========= STATE ==========
if "page" not in st.session_state:
    st.session_state.page = "home"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_plan" not in st.session_state:
    st.session_state.last_plan = None

if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.utcnow().isoformat()

if "splash_done" not in st.session_state:
    st.session_state.splash_done = False

# ========= NAV HELPERS ==========
def go(page: str):
    st.session_state.page = page
    try:
        st.experimental_set_query_params(page=page)
    except Exception:
        pass

def detect_severe_keywords(text: str) -> bool:
    severe = ["bleeding", "pus", "severe pain", "fever", "spreading", "infection", "open sore"]
    t = (text or "").lower()
    return any(word in t for word in severe)

def append_message(role: str, text: str):
    st.session_state.messages.append({"role": role, "text": text})

# ========= ANIMATED SPLASH (runs once, no rerun loop) ==========
def render_animated_splash():
    st.markdown(
        """
        <div class="animated-splash">
            <div class="splash-text">SKINSYNC</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # let animation play
    time.sleep(2.1)

if not st.session_state.splash_done:
    render_animated_splash()
    st.session_state.splash_done = True
    st.stop()

# ========= SYNC PAGE FROM URL (for ?page=chat etc.) ==========
qs = st.experimental_get_query_params()
if "page" in qs:
    st.session_state.page = qs["page"][0]

# ========= OPENROUTER CHAT ==========
SYSTEM_PROMPT = """
You are SkinSync, a clean, minimal, premium AI skincare assistant.
You:
- Ask a few gentle follow-up questions.
- Suggest simple, safe AM & PM routines.
- Mention sunscreen and patch-testing.
- Avoid diagnosing, and recommend in-person dermatology for severe / painful / rapidly worsening issues.
Keep answers warm, short, structured with headings and bullet points.
"""

def call_openrouter(messages):
    if not OPENROUTER_API_KEY:
        return None, "Missing OpenRouter API key (OPENROUTER_API_KEY)."

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "X-Title": "SkinSync AI Dermatology",
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
                "temperature": 0.7,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"], None
    except Exception as e:
        return None, f"{e}"

# ========= IMAGE ANALYSIS ==========
def analyze_skin_image(image: Image.Image):
    img = image.convert("RGB")
    arr = np.array(img).astype("float32")

    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    redness = r - (g + b) / 2

    redness_norm = (redness - redness.min()) / (redness.ptp() + 1e-6)
    mean_red = float(redness_norm.mean())

    if mean_red < 0.25:
        severity = "Very mild / almost no visible redness 🙂"
    elif mean_red < 0.45:
        severity = "Mild redness — could be light irritation or occasional acne 🌸"
    elif mean_red < 0.65:
        severity = "Moderate redness — noticeable inflammation, monitor products used 🔎"
    else:
        severity = "High redness — consider gentle care and, if painful, in-person dermatologist visit ⚠️"

    return mean_red, severity

# ========= COMMON UI ==========
def render_back_to_home():
    with st.container():
        st.markdown('<div class="back-button-container page-container">', unsafe_allow_html=True)
        if st.button("← Back to Home"):
            go("home")
        st.markdown("</div>", unsafe_allow_html=True)

# ========= PAGES ==========
def render_home():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">SkinSync</div>', unsafe_allow_html=True)
    st.markdown(
        "<p class='hero-tagline'>A calm, clinically-minded skincare companion — not a replacement for your dermatologist.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <a class="card-link" href="?page=chat">
              <div class="premium-card">
                <div class="card-header-line">
                  <span class="card-emoji">🩺</span>
                  <span>AI Dermatologist Chat</span>
                </div>
                <div class="card-subtitle">
                  Talk about your skin like with a friend and get a simple, gentle routine.
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
              <div class="premium-card">
                <div class="card-header-line">
                  <span class="card-emoji">📷</span>
                  <span>Skin Image Analysis</span>
                </div>
                <div class="card-subtitle">
                  Estimate redness/inflammation from a photo and get care tips.
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
              <div class="premium-card">
                <div class="card-header-line">
                  <span class="card-emoji">📅</span>
                  <span>Appointments</span>
                </div>
                <div class="card-subtitle">
                  Log consultation requests that can later connect to a real clinic backend.
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
              <div class="premium-card">
                <div class="card-header-line">
                  <span class="card-emoji">📋</span>
                  <span>Consult History</span>
                </div>
                <div class="card-subtitle">
                  View saved consults and the last routine suggested for you.
                </div>
              </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_chat():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 🩺 AI Derm Chat")

    with st.container():
        st.markdown('<div class="chat-card">', unsafe_allow_html=True)

        if not st.session_state.messages:
            append_message(
                "assistant",
                "Hi, I’m your SkinSync AI skincare assistant 🤍\n\n"
                "Tell me about your skin — your main concern, how long it’s been there, "
                "and what you currently use. I’ll help you build a gentle AM / PM routine."
            )

        for m in st.session_state.messages:
            if m["role"] == "assistant":
                st.markdown(
                    f"<div class='derm-bubble'><strong>Derm</strong>: {m['text']}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='user-bubble'><strong>You</strong>: {m['text']}</div>",
                    unsafe_allow_html=True,
                )

        user_input = st.text_input("You:", key="chat_input")
        col_a, col_b = st.columns(2)
        with col_a:
            send_clicked = st.button("Send", key="chat_send")
        with col_b:
            save_clicked = st.button("💾 Save consult", key="save_consult")

        if send_clicked:
            if not user_input.strip():
                st.warning("Please type something 🤍")
            else:
                append_message("user", user_input)

                msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.messages:
                    msgs.append({"role": m["role"], "content": m["text"]})

                if detect_severe_keywords(user_input):
                    warn = (
                        "I see words like pain, pus, fever or spreading. "
                        "That can be serious. I can still help with gentle skincare suggestions, "
                        "but please consider seeing an in-person dermatologist soon. 🧑‍⚕️"
                    )
                    append_message("assistant", warn)

                reply, err = call_openrouter(msgs)
                if err or reply is None:
                    fallback = (
                        "I couldn't reach the AI engine just now, but a safe starting point is:\n"
                        "- Gentle, non-stripping cleanser\n"
                        "- Simple moisturizer suited to your skin type\n"
                        "- Broad-spectrum sunscreen in the morning\n\n"
                        "Introduce any active (niacinamide, salicylic acid, retinol) slowly and patch-test first."
                    )
                    append_message("assistant", fallback)
                    st.session_state.last_plan = fallback
                    if err:
                        st.error(err)
                else:
                    append_message("assistant", reply)
                    st.session_state.last_plan = reply

        if save_clicked:
            if st.session_state.last_plan is None:
                st.warning("No consult to save yet — let me respond at least once first 🧾")
            else:
                payload = {
                    "conversation": st.session_state.messages,
                    "last_plan": st.session_state.last_plan,
                }
                c.execute(
                    "INSERT INTO consults (session_id, data, created_at) VALUES (?, ?, ?)",
                    (st.session_state.session_id, json.dumps(payload), datetime.utcnow().isoformat()),
                )
                conn.commit()
                st.success("Consult saved to history 🤍")

        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_scan():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📷 Skin Image Analysis")

    col1, col2 = st.columns([1.3, 1])

    with col1:
        uploaded = st.file_uploader(
            "Upload a clear face photo (front-facing, natural light if possible)",
            type=["png", "jpg", "jpeg"],
        )
        if uploaded is not None:
            img = Image.open(BytesIO(uploaded.read()))
            st.image(img, caption="Uploaded image", use_column_width=True)

            if st.button("Analyze redness & inflammation"):
                mean_red, severity = analyze_skin_image(img)
                st.markdown("#### 🔎 Analysis result")
                st.write(f"**Redness score (0–1):** `{mean_red:.2f}`")
                st.write(f"**Severity:** {severity}")
                st.info(
                    "This is a simple educational tool based on colour values, not a diagnosis. "
                    "For anything worrying, always see a real dermatologist."
                )
        else:
            st.info("Upload a face photo to begin analysis 🤍")

    with col2:
        st.markdown("#### Under the hood (for your resume)")
        st.markdown(
            """
- Converts the image to RGB and computes a **redness index**: `R - (G + B) / 2`.  
- Normalises values between 0–1 and averages them.  
- Maps that mean into **mild / moderate / high redness** buckets.  
- Demonstrates basic image preprocessing + hand-crafted feature engineering.  
            """
        )
    st.markdown("</div>", unsafe_allow_html=True)

def render_history():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📋 Consult History")

    df = pd.read_sql_query(
        "SELECT id, session_id, data, created_at FROM consults ORDER BY id DESC LIMIT 50",
        conn,
    )
    if df.empty:
        st.info("No consults saved yet. After a chat, click **“Save consult”** to store one.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    def preview(row):
        try:
            data = json.loads(row["data"])
            convo = data.get("conversation", [])
            first_user = next((m["text"] for m in convo if m["role"] == "user"), "")
            last_plan = data.get("last_plan", "")
            return f"User: {first_user[:40]}... | Plan: {last_plan[:40]}..."
        except Exception:
            return row["data"][:80]

    df["summary"] = df.apply(preview, axis=1)
    st.dataframe(df[["id", "summary", "created_at"]], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_appointments():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📅 Appointments")

    with st.form("booking_form_main"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        city = st.text_input("City")
        date = st.date_input("Preferred date", min_value=datetime.today())
        preferred_time = st.time_input("Preferred time")
        reason = st.text_area("Reason for visit", value="Skin consultation")
        submitted = st.form_submit_button("Book appointment")
        if submitted:
            c.execute(
                """
                INSERT INTO bookings (name, email, city, date, time, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name or "Anonymous",
                    email,
                    city,
                    str(date),
                    str(preferred_time),
                    reason,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            st.success("Appointment request logged 🤍")

    st.markdown("---")
    st.subheader("Recent appointment requests")
    df = pd.read_sql_query(
        "SELECT id, name, city, date, time, reason, created_at "
        "FROM bookings ORDER BY id DESC LIMIT 50",
        conn,
    )
    if df.empty:
        st.info("No appointment requests yet.")
    else:
        st.dataframe(df, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ========= ROUTING ==========
page = st.session_state.page

if page == "home":
    render_home()
elif page == "chat":
    render_chat()
elif page == "scan":
    render_scan()
elif page == "appointments":
    render_appointments()
elif page == "history":
    render_history()

st.markdown("---")
st.caption(
    "SkinSync is for educational skincare guidance only. "
    "It does not diagnose or replace in-person dermatology. "
    "If symptoms are severe, painful, or rapidly worsening, please seek medical care."
)
