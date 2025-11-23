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

# ---------- Env & API Key ----------
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ---------- Config ----------
st.set_page_config(
    page_title="SkinSync — AI Dermatologist Suite",
    page_icon="💠",
    layout="wide",
)

# ---------- Global Styles ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif;
    }
    .stApp {
        background: radial-gradient(circle at top left, #fff7f4 0, #fceee8 30%, #f7e4dd 60%, #f1dbd2 100%);
    }

    /* Splash screen */
    .splash-wrapper {
        position: fixed;
        inset: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at top left, #ffeae1 0, #f7d4c7 40%, #eebfb0 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: splashFade 1.4s ease-out forwards;
    }
    .splash-inner {
        text-align: center;
    }
    .splash-title {
        font-family: 'Playfair Display', serif;
        font-size: 52px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #2f1713;
        position: relative;
        display: inline-block;
        padding: 0 10px;
        overflow: hidden;
    }
    .splash-title::after {
        content: "";
        position: absolute;
        top: 0;
        left: -50%;
        width: 50%;
        height: 100%;
        background: linear-gradient(120deg, transparent, rgba(255,255,255,0.8), transparent);
        transform: skewX(-20deg);
        animation: shine 1.1s ease-out forwards;
        animation-delay: 0.1s;
    }
    .splash-sub {
        margin-top: 0.75rem;
        font-size: 13px;
        letter-spacing: 0.26em;
        text-transform: uppercase;
        color: #5e3a35;
    }

    @keyframes shine {
        0% { left: -60%; }
        100% { left: 130%; }
    }
    @keyframes splashFade {
        0% { opacity: 1; }
        100% { opacity: 0; }
    }

    /* Page fade-in */
    .page-container {
        animation: fadeInUp 0.35s ease-out;
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Hero */
    .hero-title {
        font-size: 40px;
        font-weight: 700;
        letter-spacing: 0.05em;
        color: #3a2220;
        text-align: center;
        margin-bottom: 0.1rem;
    }
    .hero-sub {
        text-align: center;
        color: #7b5b54;
        font-size: 13px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
    }

    /* Feature grid & glossy cards */
    .feature-grid {
        max-width: 900px;
        margin: 2rem auto 1rem auto;
    }
    .card-link {
        text-decoration: none;
        color: inherit;
    }
    .premium-card {
        background: linear-gradient(
            135deg,
            rgba(255,255,255,0.82),
            rgba(255,246,241,0.98)
        );
        border-radius: 22px;
        padding: 18px 22px;
        border: 1px solid rgba(255,255,255,0.92);
        box-shadow: 0 18px 46px rgba(0,0,0,0.10);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        transition: transform 0.18s ease-out,
                    box-shadow 0.18s ease-out,
                    border-color 0.18s ease-out,
                    background 0.18s ease-out;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .premium-card:hover {
        transform: translateY(-6px) scale(1.01) rotate3d(1,-1,0,2deg);
        box-shadow: 0 26px 60px rgba(0,0,0,0.22);
        border-color: #f0bba7;
        background: linear-gradient(
            145deg,
            rgba(255,255,255,0.94),
            rgba(255,242,236,0.98)
        );
    }
    .card-header-line {
        font-size: 16px;
        font-weight: 600;
        color: #3b2220;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .card-emoji {
        font-size: 20px;
    }
    .card-subtitle {
        font-size: 13px;
        color: #84615a;
    }

    .chat-card {
        background: rgba(255,255,255,0.96);
        border-radius: 18px;
        padding: 18px 22px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.07);
        max-width: 780px;
        margin: 1.5rem auto;
        backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.9);
    }
    .derm-bubble {
        background: #ffffff;
        padding: 10px 14px;
        border-radius: 14px;
        margin-bottom: 8px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
    }
    .user-bubble {
        background: #f8ded5;
        padding: 10px 14px;
        border-radius: 14px;
        margin-bottom: 8px;
        margin-left: 40px;
    }

    .back-button-container {
        max-width: 780px;
        margin: 0.5rem auto 0 auto;
    }
    .back-button-container button {
        background: rgba(255,255,255,0.85) !important;
        border-radius: 999px !important;
        border: 1px solid rgba(255,255,255,0.9) !important;
        font-size: 13px;
        color: #7a5851 !important;
        padding: 4px 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DB Setup ----------
DB_PATH = "skinsync.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

c.execute(
    """CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        city TEXT,
        date TEXT,
        time TEXT,
        reason TEXT,
        created_at TEXT
    )"""
)

c.execute(
    """CREATE TABLE IF NOT EXISTS consults (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        data TEXT,
        created_at TEXT
    )"""
)
conn.commit()

# ---------- Session State ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.utcnow().isoformat()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_plan" not in st.session_state:
    st.session_state.last_plan = None

if "splash_done" not in st.session_state:
    st.session_state.splash_done = False

# This will be synced with query params further down
if "page" not in st.session_state:
    st.session_state.page = "home"

# ---------- Navigation Helpers ----------
def go_to(page: str):
    st.session_state.page = page
    try:
        st.experimental_set_query_params(page=page)
    except Exception:
        pass

def detect_severe_keywords(text: str) -> bool:
    severe = [
        "bleeding",
        "pus",
        "severe pain",
        "fever",
        "spreading",
        "infection",
        "open sore",
    ]
    t = (text or "").lower()
    return any(word in t for word in severe)

def append_message(role: str, text: str):
    st.session_state.messages.append({"role": role, "text": text})

# ---------- OpenRouter Chat ----------
SYSTEM_PROMPT = """
You are SkinSync, a friendly but responsible AI dermatology assistant.
Your goals:
- Ask gentle follow-up questions about the user's skin, lifestyle and routine.
- Give evidence-informed, simple skincare suggestions.
- Provide clear AM and PM routines, and suggest 1-2 DIY face packs with safe ingredients.
- Always be cautious: you are NOT a doctor, cannot diagnose, and must recommend in-person dermatology for severe / painful / rapidly worsening symptoms.
- Be warm, supportive, and concise. Use bullet points and headings where helpful.
- Assume user is in India/Asia unless specified; mention if actives may be irritating or need sunscreen.
- Never guarantee cures or medical outcomes.
"""

def call_openrouter_chat(messages):
    if not OPENROUTER_API_KEY:
        return None, "No OpenRouter API key found. Add OPENROUTER_API_KEY in your .env."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://skinsync.streamlit.app",
        "X-Title": "SkinSync AI Dermatologist",
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "temperature": 0.65,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content, None
    except Exception as e:
        return None, f"Error calling OpenRouter: {e}"

# ---------- CV-like redness analysis ----------
def analyze_skin_image(image: Image.Image):
    img = image.convert("RGB")
    arr = np.array(img).astype("float32")

    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    redness = r - (g + b) / 2

    redness_normalized = (redness - redness.min()) / (redness.ptp() + 1e-6)
    mean_red = float(redness_normalized.mean())

    if mean_red < 0.25:
        severity = "Very mild / almost no visible redness 🙂"
    elif mean_red < 0.45:
        severity = "Mild redness — could be light irritation or occasional acne 🌸"
    elif mean_red < 0.65:
        severity = "Moderate redness — noticeable inflammation, monitor products used 🔎"
    else:
        severity = "High redness — consider gentle care and, if painful, in-person dermatologist visit ⚠️"

    return mean_red, severity

# ---------- Splash Screen ----------
def render_splash():
    st.markdown(
        """
        <div class="splash-wrapper">
          <div class="splash-inner">
            <div class="splash-sub">AI · SKINCARE · DERMATOLOGY</div>
            <div class="splash-title">SkinSync</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Show splash once per session
if not st.session_state.splash_done:
    render_splash()
    # small delay then mark splash done and rerun
    time.sleep(1.5)
    st.session_state.splash_done = True
    st.experimental_rerun()

# ---------- Sync page with query params ----------
qs = st.experimental_get_query_params()
if "page" in qs:
    st.session_state.page = qs["page"][0]

# ---------- Layout helpers ----------
def render_back_to_home():
    with st.container():
        st.markdown('<div class="back-button-container page-container">', unsafe_allow_html=True)
        if st.button("← Back to Home"):
            go_to("home")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- Pages ----------
def render_home():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    st.markdown('<div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">SkinSync</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#815952;font-size:15px;margin-top:-5px;'>"
        "Your AI-powered skincare companion for gentle, science-based routines."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    # Row 1
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
                  Describe your skin and get a personalised, gentle AM/PM routine.
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
                  <span>Skin Analysis</span>
                </div>
                <div class="card-subtitle">
                  Upload a face photo to estimate redness and get gentle-care tips.
                </div>
              </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    # Row 2
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
                  Book consultation slots that can later link to a real clinic backend.
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
                  See your saved consults and generated routines at a glance.
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
    st.markdown("### 🩺 AI Derm Chat", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="chat-card">', unsafe_allow_html=True)

        if not st.session_state.messages:
            append_message(
                "assistant",
                "Hi, I’m your SkinSync AI derm assistant 🌿\n\n"
                "Tell me about your skin today — your main concern, how long it's been there, "
                "and what products you use. I’ll help you build a gentle AM/PM routine."
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
        cols = st.columns([1, 1])
        with cols[0]:
            send_clicked = st.button("Send", key="chat_send")
        with cols[1]:
            save_clicked = st.button("💾 Save consult", key="save_consult")

        if send_clicked:
            if not user_input.strip():
                st.warning("Please type something 💗")
            else:
                append_message("user", user_input)

                or_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.messages:
                    or_messages.append({"role": m["role"], "content": m["text"]})

                if detect_severe_keywords(user_input):
                    warn = (
                        "I noticed words like pain, pus, fever or rapid spreading. "
                        "This can be serious. I can give gentle skin-care tips, "
                        "but please consider seeing an in-person dermatologist soon. 🧑‍⚕️"
                    )
                    append_message("assistant", warn)

                reply_text, err = call_openrouter_chat(or_messages)
                if err:
                    fallback = (
                        "I couldn't contact the AI engine right now, but based on what you said "
                        "I suggest keeping your routine simple: gentle cleanser, moisturizer and sunscreen. "
                        "Introduce actives slowly and always patch test first."
                    )
                    append_message("assistant", fallback)
                    st.session_state.last_plan = fallback
                    st.error(err)
                else:
                    append_message("assistant", reply_text)
                    st.session_state.last_plan = reply_text

        if save_clicked:
            if st.session_state.last_plan is None:
                st.warning("No consult to save yet — send a message and get at least one AI reply first 🧾")
            else:
                payload = {
                    "conversation": st.session_state.messages,
                    "last_plan": st.session_state.last_plan,
                }
                c.execute(
                    "INSERT INTO consults (session_id,data,created_at) VALUES (?,?,?)",
                    (
                        st.session_state.session_id,
                        json.dumps(payload),
                        datetime.utcnow().isoformat(),
                    ),
                )
                conn.commit()
                st.success("Consult saved to history ✅")

        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_scan():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📷 Skin Image Analysis")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        uploaded = st.file_uploader(
            "Upload a clear face photo (front-facing, good lighting)",
            type=["png", "jpg", "jpeg"],
        )
        if uploaded is not None:
            image = Image.open(BytesIO(uploaded.read()))
            st.image(image, caption="Uploaded image", use_column_width=True)

            if st.button("Analyze redness & inflammation"):
                mean_red, severity = analyze_skin_image(image)
                st.markdown("#### 🔎 Analysis result")
                st.write(f"**Redness score (0 to 1):** {mean_red:.2f}")
                st.write(f"**Severity:** {severity}")
                st.info(
                    "This is a heuristic, educational-only analysis. "
                    "Real diagnosis always needs an in-person dermatologist."
                )
        else:
            st.info("No image uploaded yet — upload a face photo to start analysis.")

    with col2:
        st.markdown("#### How this works (for your resume)")
        st.markdown(
            """
- Converts the image to RGB, then computes a **redness index** per pixel.  
- Normalises the value to a 0–1 range and takes the mean.  
- Maps the mean redness value to **mild / moderate / high** categories.  
- Shows you understand image preprocessing, colour channels and basic CV feature engineering.  
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
        st.info("No consults saved yet. After a chat, click 'Save consult' to store one.")
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
        time = st.time_input("Preferred time")
        reason = st.text_area("Reason for visit", value="Skin consultation")
        submitted = st.form_submit_button("Book appointment")
        if submitted:
            c.execute(
                "INSERT INTO bookings (name,email,city,date,time,reason,created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    name or "Anonymous",
                    email,
                    city,
                    str(date),
                    str(time),
                    reason,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            st.success(
                "Appointment requested — provisional booking saved. "
                "A clinic admin can now see it below."
            )

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

# ---------- Routing ----------
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
    "SkinSync — advice is for educational purposes only and not a substitute for in-person dermatology. "
    "If symptoms are severe, painful, or rapidly worsening, seek medical help."
)
