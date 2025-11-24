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

# ========== ENV & API KEY ==========
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ========== BASIC CONFIG ==========
st.set_page_config(
    page_title="SkinSync — AI Dermatologist",
    page_icon="💠",
    layout="wide",
)

# ---------- Force light theme + readable text everywhere ----------
st.markdown("""
<style>
/* prevent dark-mode madness on mobile */
:root {
    color-scheme: light !important;
}

/* top Streamlit header - make it light */
header[data-testid="stHeader"] {
    background-color: #fdf7f0 !important;
    color: #3b2618 !important;
}
header[data-testid="stHeader"] * {
    color: #3b2618 !important;
    fill:  #3b2618 !important;
}

/* global text colours for beige background */
html, body, [class*="css"] {
    color: #3a291d !important;
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    color: #25170f !important;
    font-family: 'Playfair Display', serif !important;
}
p, span, label, li, td, th {
    color: #3a291d !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- GLOBAL STYLES: luxury beige aesthetic ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    .stApp {
        background: radial-gradient(circle at top, #fffaf3 0, #f6ecdf 40%, #f1e3d3 100%);
    }

    /* ---------- Splash overlay (non-blocking, simple fade) ---------- */
    .splash-overlay {
        position: fixed;
        inset: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at top, #fff7ee 0, #f4e2cf 45%, #e7d1b9 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: splashFadeOut 1.4s ease-out forwards;
    }
    .splash-inner {
        text-align: center;
    }
    .splash-title {
        font-family: 'Playfair Display', serif;
        font-size: 40px;
        letter-spacing: 0.20em;
        text-transform: uppercase;
        color: #271910;
        padding: 0 14px;
    }
    .splash-sub {
        margin-bottom: 0.6rem;
        font-size: 11px;
        letter-spacing: 0.26em;
        text-transform: uppercase;
        color: #8c6a4e;
    }
    @keyframes splashFadeOut {
        0%   { opacity: 1; }
        70%  { opacity: 1; }
        100% { opacity: 0; visibility: hidden; pointer-events: none; }
    }

    /* page section fade */
    .page-container {
        animation: fadeInUp 0.30s ease-out;
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Hero */
    .hero-title {
        font-size: 34px;
        font-weight: 700;
        letter-spacing: 0.09em;
        color: #271910;
        text-align: center;
        margin-bottom: 0.1rem;
    }
    .hero-sub {
        text-align: center;
        color: #8b6a4c;
        font-size: 12px;
        letter-spacing: 0.22em;
        text-transform: uppercase;
    }

    /* Feature grid & cards */
    .feature-grid {
        max-width: 900px;
        margin: 2.2rem auto 1.6rem auto;
    }
    .card-link {
        text-decoration: none;
        color: inherit;
    }
    .premium-card {
        background: linear-gradient(
            135deg,
            rgba(255,255,255,0.97),
            rgba(250,242,231,0.99)
        );
        border-radius: 22px;
        padding: 18px 22px;
        border: 1px solid rgba(255,255,255,0.9);
        box-shadow: 0 18px 40px rgba(105,73,46,0.12);
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
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 26px 60px rgba(75,50,31,0.22);
        border-color: #e3c29a;
        background: linear-gradient(
            140deg,
            rgba(255,255,255,1),
            rgba(248,238,224,1)
        );
    }
    .card-header-line {
        font-size: 15px;
        font-weight: 600;
        color: #2d1a10;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .card-emoji {
        font-size: 20px;
    }
    .card-subtitle {
        font-size: 13px;
        color: #947359;
    }

    /* Chat card & bubbles */
    .chat-card {
        background: rgba(255,255,255,0.98);
        border-radius: 18px;
        padding: 18px 22px;
        box-shadow: 0 12px 30px rgba(91,59,42,0.15);
        max-width: 780px;
        margin: 1.5rem auto;
        backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.9);
    }
    .derm-bubble {
        background: #ffffff;
        padding: 12px 16px;
        border-radius: 14px;
        margin-bottom: 8px;
        box-shadow: 0 4px 14px rgba(88,57,38,0.10);
        color: #25170f !important;
    }
    .user-bubble {
        background: #f9ebdd;
        padding: 12px 16px;
        border-radius: 14px;
        margin-bottom: 8px;
        margin-left: 40px;
        color: #25170f !important;
    }

    /* Back button */
    .back-button-container {
        max-width: 780px;
        margin: 0.6rem auto 0 auto;
    }
    .back-button-container button {
        background: #f3e4d5 !important;
        border-radius: 999px !important;
        border: 1px solid rgba(206,164,116,0.9) !important;
        font-size: 13px;
        color: #7a5637 !important;
        padding: 4px 16px !important;
        box-shadow: 0 8px 18px rgba(119,83,52,0.20);
    }

    /* Inputs */
    input, textarea, .stTextInput, .stTextArea {
        color: #25170f !important;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > textarea {
        background: #ffffff !important;
        color: #25170f !important;
        border-radius: 14px !important;
        border: 1px solid #e4c9a6 !important;
    }
    ::placeholder {
        color: #a17c5a !important;
        opacity: 1 !important;
    }
    .stTextInput label, .stTextArea label {
        color: #765337 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- BUTTON OVERRIDE (so text/icons are visible) ----------
st.markdown("""
<style>
.stButton > button {
    background-color: #5b3b2a !important;
    color: #ffffff !important;
    border-radius: 16px !important;
    padding: 0.55rem 1.2rem !important;
    font-weight: 600 !important;
    border: none !important;
    box-shadow: 0 6px 16px rgba(63,38,23,0.35);
}
.stButton > button:hover {
    background-color: #6e4733 !important;
    color: #ffffff !important;
    transform: translateY(-1px) scale(1.01);
    transition: 0.12s ease-out;
}
.stButton > button:disabled {
    background-color: #8c6a53 !important;
    color: #ffffffa8 !important;
}
.stButton svg {
    fill: #ffffff !important;
    stroke: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# ========== DATABASE ==========
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

# ========== SESSION STATE ==========
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.utcnow().isoformat()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_plan" not in st.session_state:
    st.session_state.last_plan = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "splash_shown" not in st.session_state:
    st.session_state.splash_shown = False

# ========== HELPERS ==========

def go_to(page: str):
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
        return None, "No OPENROUTER_API_KEY found in environment."
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

# ========== SPLASH (CSS overlay, no blocking) ==========

def show_splash_overlay():
    st.markdown(
        """
        <div class="splash-overlay">
          <div class="splash-inner">
            <div class="splash-sub">AI · SKINCARE · DERMATOLOGY</div>
            <div class="splash-title">SKINSYNC</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Read query param first so we know where we are
qs = st.experimental_get_query_params()
if "page" in qs:
    st.session_state.page = qs["page"][0]

# Show overlay once at session start on home
if not st.session_state.splash_shown and st.session_state.page == "home":
    show_splash_overlay()
    st.session_state.splash_shown = True

# ========== LAYOUT HELPERS ==========

def render_back_to_home():
    with st.container():
        st.markdown('<div class="back-button-container page-container">', unsafe_allow_html=True)
        if st.button("← Back to Home"):
            go_to("home")
        st.markdown("</div>", unsafe_allow_html=True)

# ========== PAGES ==========

def render_home():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    st.markdown('<div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">SkinSync</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;font-size:14px;margin-top:-4px;'>"
        "Your AI-powered skincare companion for gentle, science-based routines."
        "</p>",
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
                "Hi, I’m your SkinSync AI skincare assistant 🌿\n\n"
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
        col_left, col_right = st.columns([1, 1])
        with col_left:
            send_clicked = st.button("Send", key="chat_send")
        with col_right:
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
                    or_messages.append({"role": "assistant", "content": warn})

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
- Shows understanding of basic computer vision & image preprocessing.  
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
        time_val = st.time_input("Preferred time")
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
                    str(time_val),
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

# ========== ROUTING ==========

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
