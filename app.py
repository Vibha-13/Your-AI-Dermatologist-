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
    page_title="SkinSync — AI Dermatologist",
    page_icon="💠",
    layout="wide",
)

# Force light mode on devices that are in dark mode
st.markdown("""
    <style>
    @media (prefers-color-scheme: dark) {
        html, body, [class*="css"] {
            color-scheme: light !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Global Styles (clean girl rosy aesthetic) ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Playfair+Display', 'Playfair Display', serif;
    }

    .stApp {
        background: linear-gradient(
            180deg,
            #fffafb 0%,
            #fef3f7 30%,
            #f9e7f1 65%,
            #f4dde9 100%
        );
    }

    /* Splash screen */
    .splash-wrapper {
        position: fixed;
        inset: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at top, #fff5fb 0, #f6ddea 40%, #f1cfe3 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }
    .splash-inner {
        text-align: center;
    }
    .splash-title {
        font-family: 'Playfair Display', serif;
        font-size: 44px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #2b1826;
        position: relative;
        display: inline-block;
        padding: 0 10px;
        overflow: hidden;
    }
    .splash-title::after {
        content: "";
        position: absolute;
        top: 0;
        left: -60%;
        width: 50%;
        height: 100%;
        background: linear-gradient(120deg, transparent, rgba(255,255,255,0.85), transparent);
        transform: skewX(-20deg);
        animation: shine 1.1s ease-out forwards;
        animation-delay: 0.1s;
    }
    .splash-sub {
        margin-bottom: 0.8rem;
        font-size: 11px;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        color: #7a5a71;
    }

    @keyframes shine {
        0% { left: -60%; }
        100% { left: 130%; }
    }

    /* Page fade-in */
    .page-container {
        animation: fadeInUp 0.35s ease-out;
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Hero */
    .hero-title {
        font-size: 38px;
        font-weight: 700;
        letter-spacing: 0.07em;
        color: #2b1826;
        text-align: center;
        margin-bottom: 0.1rem;
    }
    .hero-sub {
        text-align: center;
        color: #8a6a7f;
        font-size: 12px;
        letter-spacing: 0.22em;
        text-transform: uppercase;
    }

    /* Feature grid & cards */
    .feature-grid {
        max-width: 900px;
        margin: 2.3rem auto 1.6rem auto;
    }
    .card-link {
        text-decoration: none;
        color: inherit;
    }
    .premium-card {
        background: linear-gradient(
            135deg,
            rgba(255,255,255,0.96),
            rgba(255,245,251,0.98)
        );
        border-radius: 22px;
        padding: 18px 22px;
        border: 1px solid rgba(255,255,255,0.9);
        box-shadow: 0 18px 40px rgba(0,0,0,0.08);
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
        box-shadow: 0 26px 60px rgba(0,0,0,0.18);
        border-color: #f1b9d3;
        background: linear-gradient(
            140deg,
            rgba(255,255,255,0.98),
            rgba(255,242,249,0.99)
        );
    }
    .card-header-line {
        font-size: 15px;
        font-weight: 600;
        color: #2f1a29;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .card-emoji {
        font-size: 20px;
    }
    .card-subtitle {
        font-size: 13px;
        color: #8b6c80;
    }

    .chat-card {
        background: rgba(255,255,255,0.98);
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
        color: #2b1826;
    }
    .user-bubble {
        background: #fbe3f0;
        padding: 10px 14px;
        border-radius: 14px;
        margin-bottom: 8px;
        margin-left: 40px;
        color: #2b1826;
    }

    .back-button-container {
        max-width: 780px;
        margin: 0.6rem auto 0 auto;
    }
    .back-button-container button {
        background: #ffffff !important;
        border-radius: 999px !important;
        border: 1px solid rgba(222,174,203,0.9) !important;
        font-size: 13px;
        color: #7f556f !important;
        padding: 4px 16px !important;
        box-shadow: 0 8px 18px rgba(0,0,0,0.06);
    }

    /* Inputs & buttons (light theme override) */
    .stTextInput > div > div > input,
    .stTextArea > div > textarea {
        background: #ffffff !important;
        color: #2b1826 !important;
        border-radius: 14px !important;
        border: 1px solid #edd3e4 !important;
    }

    .stButton > button {
        background: #2b1826 !important;
        color: #ffffff !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 0.4rem 1.2rem !important;
        font-size: 14px !important;
        box-shadow: 0 10px 22px rgba(0,0,0,0.18);
    }
    .stButton > button:hover {
        background: #3a2033 !important;
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

if "page" not in st.session_state:
    st.session_state.page = "home"

# ---------- Helpers ----------
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
    # Balanced: fast + good reasoning
    "model": "meta-llama/llama-3-70b-instruct",
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
    # Convert to numpy safely
    img = image.convert("RGB")
    arr = np.array(img).astype("float32")

    # If the image is somehow empty or corrupted
    if arr.size == 0:
        return 0.0, "Image corrupted or unreadable — please upload a clearer photo."

    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]

    # Compute redness
    redness = r - (g + b) / 2.0

    # Normalize safe
    ptp = redness.ptp()

    # Prevent division errors
    if ptp < 1e-6:  
        # This means the entire image has almost identical color everywhere
        return 0.0, "Unable to detect redness — try a clearer face image with normal lighting."

    redness_normalized = (redness - redness.min()) / (ptp + 1e-6)
    mean_red = float(redness_normalized.mean())

    # Grading
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
        <style>
        .splash-wrapper {
            position: fixed;
            inset: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at top, #fff5fb 0, #f6ddea 40%, #f1cfe3 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 99999;
            animation: fadeOutSplash 0.8s ease-out forwards;
            animation-delay: 2.2s; /* show splash fully first */
        }

        @keyframes fadeOutSplash {
            0% { opacity: 1; }
            100% { opacity: 0; visibility: hidden; }
        }

        .splash-inner {
            text-align: center;
        }

        .splash-title {
            font-family: 'Playfair Display', serif;
            font-size: 44px;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: #2b1826;
            position: relative;
            display: inline-block;
            padding: 0 10px;
        }

        /* Shine animation */
        .splash-title::after {
            content: "";
            position: absolute;
            top: 0;
            left: -80%;
            width: 60%;
            height: 100%;
            background: linear-gradient(120deg, transparent, rgba(255,255,255,0.85), transparent);
            transform: skewX(-20deg);
            animation: shine 1.3s ease-out forwards;
            animation-delay: 0.4s; /* show text first, then shine */
        }

        @keyframes shine {
            0% { left: -80%; }
            100% { left: 130%; }
        }

        .splash-sub {
            margin-bottom: 0.8rem;
            font-size: 11px;
            letter-spacing: 0.28em;
            text-transform: uppercase;
            color: #7a5a71;
            opacity: 0;
            animation: fadeInSub 0.7s ease-out forwards;
            animation-delay: 0.3s;
        }

        @keyframes fadeInSub {
            from { opacity: 0; transform: translateY(6px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        </style>

        <div class="splash-wrapper">
            <div class="splash-inner">
                <div class="splash-sub">AI · SKINCARE · DERMATOLOGY</div>
                <div class="splash-title">SKINSYNC</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



# ---------- Sync with query params ----------
qs = st.experimental_get_query_params()
if "page" in qs:
    st.session_state.page = qs["page"][0]

# ---------- Layout Helpers ----------
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
        "<p style='text-align:center;color:#7f627b;font-size:14px;margin-top:-4px;'>"
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

                # Only keep the last ~10 messages for speed
                recent_history = st.session_state.messages[-10:]
  
                   for m in recent_history:
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
- Shows understanding of image preprocessing, colour channels and basic CV feature engineering.  
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
