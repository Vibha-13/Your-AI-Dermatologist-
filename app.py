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
import re

# ==========================================
# ENV & API KEY
# ==========================================
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ==========================================
# SPLASH SCREEN (non-blocking)
# ==========================================
if "show_splash" not in st.session_state:
    st.session_state.show_splash = True

if st.session_state.show_splash:
    splash_html = """
    <style>
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(10px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeOut {
            0% { opacity: 1;}
            80% { opacity: 1;}
            100% { opacity: 0; visibility: hidden; }
        }
    </style>

    <div style="
        position: fixed;
        inset: 0;
        background: radial-gradient(circle at top, #ffeaf6, #f3d4e5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        pointer-events: none;
        animation: fadeOut 1.2s ease-out 1.8s forwards;
    ">
        <div style="text-align:center; animation: fadeIn 1s ease-out forwards;">
            <div style="font-size:12px; letter-spacing:0.25em; color:#7a5a71;">
                AI · SKINCARE · DERMATOLOGY
            </div>
            <div style="font-size:42px; font-family:'Playfair Display'; color:#251320; letter-spacing:0.17em;">
                SKINSYNC
            </div>
        </div>
    </div>
    """
    st.markdown(splash_html, unsafe_allow_html=True)
    st.session_state.show_splash = False

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="SkinSync — Smart Skin Coach",
    page_icon="💠",
    layout="wide",
)

# ==========================================
# GLOBAL LIGHT MODE FIX
# ==========================================
st.markdown("""
<style>
@media (prefers-color-scheme: dark) {
    html, body, [class*="css"] {
        color-scheme: light !important;
    }
}
html, body, [class*="css"] {
    color: #2b1826 !important;
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, h4, h5 {
    color: #1f111a !important;
    font-family: 'Playfair Display', serif !important;
}
p, span, label, li, td, th {
    color: #35202b !important;
}
header[data-testid="stHeader"] {
    background-color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# GLOBAL STYLE (Glass UI + Animations)
# ==========================================
st.markdown("""
<style>

.stApp {
    background: linear-gradient(180deg,#fffdfd 0%,#fff7fb 30%,#feeef7 65%,#fbe5f1 100%);
}

/* -----------------------------------------------------
   🌸 CARD BASE (GLASS)
------------------------------------------------------ */
.premium-card {
    background: rgba(255,255,255,0.45);
    border-radius: 22px;
    padding: 20px 26px;
    border: 1px solid rgba(255,255,255,0.55);
    backdrop-filter: blur(16px);
    box-shadow: 0 18px 42px rgba(0,0,0,0.10);

    opacity: 0;
    animation: cardFadeUp 0.55s ease-out forwards;
    animation-delay: var(--delay, 0ms);

    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
}

.premium-card:nth-child(1) { --delay: 60ms; }
.premium-card:nth-child(2) { --delay: 130ms; }
.premium-card:nth-child(3) { --delay: 200ms; }
.premium-card:nth-child(4) { --delay: 270ms; }
.premium-card:nth-child(5) { --delay: 340ms; }

@keyframes cardFadeUp {
    0% { opacity: 0; transform: translateY(14px) scale(0.98); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* PREMIUM SHIMMER */
.premium-card::after {
    content: "";
    position: absolute;
    top: 0;
    left: -150%;
    width: 200%;
    height: 100%;
    background: linear-gradient(
        120deg,
        transparent 0%,
        rgba(255,255,255,0.25) 50%,
        transparent 100%
    );
    transform: skewX(-22deg);
}

.premium-card:hover::after {
    left: 150%;
    transition: 0.8s ease-out;
}

/* BUTTONS */
.stButton > button {
    background-color: #eadcff !important;
    color: #3a0030 !important;
    border-radius: 25px !important;
    border: 1px solid #d6c0f5 !important;
    font-weight: 600 !important;
}
.stButton > button:hover {
    background-color: #d8c1ff !important;
}

/* CHAT BUBBLES */
.derm-bubble {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 12px 16px;
}
.user-bubble {
    background: rgba(248,220,250,0.75);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 12px 16px;
    margin-left: 40px;
}

/* GLASS BOXES */
.glass-box {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(16px);
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.08);
}
.warn-box {
    background: rgba(255,220,220,0.55);
    border-left: 4px solid #d40000;
    border-radius: 14px;
    padding: 12px 16px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# DB SETUP
# ==========================================
DB_PATH = "skinsync.db"

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_connection()
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

c.execute("""
CREATE TABLE IF NOT EXISTS diary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT,
    mood TEXT,
    redness INTEGER,
    oiliness INTEGER,
    sleep_hours REAL,
    water_glasses INTEGER,
    note TEXT,
    created_at TEXT
)
""")

conn.commit()

# ==========================================
# SESSION STATE SETUP
# ==========================================
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.utcnow().isoformat()

if "messages_beta" not in st.session_state:
    st.session_state.messages_beta = []

if "last_plan_beta" not in st.session_state:
    st.session_state.last_plan_beta = None

if "page" not in st.session_state:
    st.session_state.page = "home"

if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "",
        "age_bucket": "18–24",
        "skin_type": "Combination",
        "main_concern": "Acne / Breakouts",
        "sensitivity": "Normal",
        "location": "",
    }

if "consent" not in st.session_state:
    st.session_state.consent = False

# ==========================================
# SIDEBAR — SKIN PROFILE
# ==========================================
with st.sidebar:
    st.markdown("#### 🌸 Your Skin Profile")

    p = st.session_state.profile

    p["name"] = st.text_input("Name (optional)", value=p["name"])

    p["age_bucket"] = st.selectbox(
        "Age range",
        ["<18", "18–24", "25–30", "30–40", "40+"],
        index=["<18", "18–24", "25–30", "30–40", "40+"].index(p["age_bucket"]),
    )

    p["skin_type"] = st.selectbox(
        "Skin type",
        ["Dry", "Oily", "Combination", "Normal", "Sensitive"],
        index=["Dry", "Oily", "Combination", "Normal", "Sensitive"].index(p["skin_type"]),
    )

    concerns_list = [
        "Acne / Breakouts",
        "Pigmentation / Dark spots",
        "Dryness / Flakiness",
        "Oiliness / Shine",
        "Redness / Sensitivity",
        "Anti-aging / Fine lines",
    ]
    if p["main_concern"] not in concerns_list:
        p["main_concern"] = concerns_list[0]

    p["main_concern"] = st.selectbox(
        "Main concern",
        concerns_list,
        index=concerns_list.index(p["main_concern"]),
    )

    p["sensitivity"] = st.selectbox(
        "Sensitivity",
        ["Normal", "Slightly sensitive", "Very sensitive"],
        index=["Normal", "Slightly sensitive", "Very sensitive"].index(p["sensitivity"]),
    )

    p["location"] = st.text_input("Location (city, optional)", value=p["location"])

    st.session_state.profile = p

    st.markdown("---")
    st.markdown(
        "⚕️ **Important:** This assistant gives educational skincare guidance only."
    )

    consent = st.checkbox(
        "I understand this is **not** a substitute for a dermatologist.",
        value=st.session_state.consent,
    )
    st.session_state.consent = consent


# ==========================================
# HELPERS
# ==========================================

def go_to(page: str):
    st.session_state.page = page
    try:
        st.experimental_set_query_params(page=page)
    except Exception:
        pass


def is_valid_email(email: str) -> bool:
    if not email:
        return False
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None


def detect_severe_keywords(text: str) -> bool:
    severe = ["bleeding", "pus", "severe pain", "fever", "spreading", "infection", "open sore"]
    t = (text or "").lower()
    return any(word in t for word in severe)

def detect_intent(text: str):
    if not text:
        return "empty"

    t = text.lower().strip()

    greetings = [
        "hi", "hii", "hiii", "hello", "hey", "heyy", "helo",
        "hlo", "yo", "hola", "namaste", "hie"
    ]

    smalltalk = [
        "how are you", "whats up", "what’s up", "wyd",
        "doing good", "cool", "ok", "okay", "k", "gm", "gn"
    ]

    # Greeting only
    if t in greetings:
        return "greeting"

    # A small non-skin message
    if any(phrase in t for phrase in smalltalk):
        return "small_talk"

    return "meaningful"

# ==========================================
# API CALLER — OpenRouter
# ==========================================
def call_openrouter_chat(messages, retries=1):
    if not OPENROUTER_API_KEY:
        return None, "Missing API key."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://skinsync.streamlit.app",
        "X-Title": "SkinSync Smart Skin Coach",
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "temperature": 0.65,
    }

    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content, None

        except requests.Timeout:
            if attempt < retries:
                continue
            return None, "The AI service is taking too long to respond."

        except requests.RequestException:
            if attempt < retries:
                continue
            return None, "Network issue — please try again."

        except Exception:
            return None, "Unexpected error occurred."


# ==========================================
# IMAGE ANALYSIS (REDNESS)
# ==========================================
def analyze_skin_image(image: Image.Image):
    try:
        img = image.convert("RGB")
        arr = np.array(img).astype("float32")

        if len(arr.shape) != 3 or arr.shape[2] != 3:
            return 0.0, "Invalid image — must be a clear color photo."

        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]

        redness = r - (g + b) / 2

        diff = redness.max() - redness.min()
        if diff < 1e-6:
            diff = 1e-6

        normalized = (redness - redness.min()) / diff
        mean_red = float(np.mean(normalized))

        if mean_red < 0.25:
            sev = "Very mild redness 🙂"
        elif mean_red < 0.45:
            sev = "Mild redness — light irritation 🌸"
        elif mean_red < 0.65:
            sev = "Moderate redness 🔎"
        else:
            sev = "High redness — be gentle, consider dermatologist advice ⚠️"

        return mean_red, sev

    except Exception:
        return 0.0, "Could not process this image."

# ==========================================
# HOME PAGE
# ==========================================
def render_home():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    # Title + Subtitle
    st.markdown('<div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">SkinSync</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;font-size:14px;margin-top:-6px;'>"
        "Your personalised skincare intelligence — routines, scans, diary & more."
        "</p>",
        unsafe_allow_html=True,
    )

    prof = st.session_state.profile
    st.markdown(
        f"""
        <p style='text-align:center;font-size:12px;margin-top:4px;opacity:0.75;'>
        Signed in as <strong>{prof.get('name') or 'Guest'}</strong> ·  
        {prof.get('skin_type')} skin · {prof.get('main_concern')}
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ------------------------------------------------
    # Cards Grid
    # ------------------------------------------------
    st.markdown('<div class="feature-grid" style="max-width:900px;margin:auto;">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # -------------- Smart Skin Coach --------------
    with col1:
        st.markdown(
            """
            <a class="card-link" href="?page=chat">
              <div class="premium-card">
                <div class="card-header-line" style="display:flex;align-items:center;gap:8px;">
                  <span class="card-emoji" style="font-size:20px;">🧠</span>
                  <span style="font-size:15px;font-weight:600;">Smart Skin Coach</span>
                </div>
                <div class="card-subtitle" style="font-size:13px;color:#8b6c80;">
                  AI-powered personalised AM/PM routines.
                </div>
              </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    # -------------- Skin Analysis --------------
    with col2:
        st.markdown(
            """
            <a class="card-link" href="?page=scan">
              <div class="premium-card">
                <div class="card-header-line" style="display:flex;align-items:center;gap:8px;">
                  <span class="card-emoji" style="font-size:20px;">📷</span>
                  <span style="font-size:15px;font-weight:600;">Skin Analysis</span>
                </div>
                <div class="card-subtitle" style="font-size:13px;color:#8b6c80;">
                  Upload a face photo to estimate redness.
                </div>
              </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    col3, col4 = st.columns(2)

    # -------------- Appointments --------------
    with col3:
        st.markdown(
            """
            <a class="card-link" href="?page=appointments">
              <div class="premium-card">
                <div class="card-header-line" style="display:flex;align-items:center;gap:8px;">
                  <span class="card-emoji" style="font-size:20px;">📅</span>
                  <span style="font-size:15px;font-weight:600;">Appointments</span>
                </div>
                <div class="card-subtitle" style="font-size:13px;color:#8b6c80;">
                  Book consultation slots instantly.
                </div>
              </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    # -------------- History --------------
    with col4:
        st.markdown(
            """
            <a class="card-link" href="?page=history">
              <div class="premium-card">
                <div class="card-header-line" style="display:flex;align-items:center;gap:8px;">
                  <span class="card-emoji" style="font-size:20px;">📋</span>
                  <span style="font-size:15px;font-weight:600;">Consult History</span>
                </div>
                <div class="card-subtitle" style="font-size:13px;color:#8b6c80;">
                  View all saved routines & scans.
                </div>
              </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
# ==========================================
# SMART SKIN COACH (MAIN CHAT)
# ==========================================
# ==========================================
# SMART SKIN COACH (MAIN CHAT)
# ==========================================
def render_chat():
    import json

    # Top navigation
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 🧠 Smart Skin Coach (Beta)", unsafe_allow_html=True)

    # ----------------------------------------
    # CONSENT CHECK
    # ----------------------------------------
    if not st.session_state.consent:
        st.warning(
            "Please confirm in the left sidebar that you understand SkinSync is not a doctor."
        )
        return

    # Profile mini line
    prof = st.session_state.profile
    st.markdown(
        f"""
        <p style='font-size:12px;opacity:0.8;'>
            Profile: <strong>{prof.get('skin_type')}</strong> skin · {prof.get('main_concern')} 
            · sensitivity: {prof.get('sensitivity')}
        </p>
        """,
        unsafe_allow_html=True,
    )

    # ----------------------------------------
    # SESSION STATE for CHAT
    # ----------------------------------------
    if "messages_beta" not in st.session_state:
        st.session_state.messages_beta = []

    if "chat_input_beta" not in st.session_state:
        st.session_state.chat_input_beta = ""

    if "pending_beta" not in st.session_state:
        st.session_state.pending_beta = ""

    if "last_plan_beta" not in st.session_state:
        st.session_state.last_plan_beta = None

    # ----------------------------------------
    # Chat Container
    # ----------------------------------------
    with st.container():
        st.markdown('<div class="chat-card">', unsafe_allow_html=True)

        # First bot greeting if empty
        if len(st.session_state.messages_beta) == 0:
            st.session_state.messages_beta.append({
                "role": "assistant",
                "text": (
                    "Hi, I’m your Smart Skin Coach 🌿\n\n"
                    "Tell me what’s bothering your skin right now — "
                    "acne, dryness, redness, pigmentation, anything."
                )
            })

        # Show conversation bubbles
        for m in st.session_state.messages_beta:
            if m["role"] == "assistant":
                st.markdown(
                    f"<div class='derm-bubble'><strong>Coach</strong>: {m['text']}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div class='user-bubble'><strong>You</strong>: {m['text']}</div>",
                    unsafe_allow_html=True
                )

        # ----------------------------------------
        # SEND HANDLER (prevents double click)
        # ----------------------------------------
        def handle_send_beta():
            txt = st.session_state.get("chat_input_beta", "").strip()
            if txt:
                st.session_state.pending_beta = txt
                st.session_state.chat_input_beta = ""

        # Input box
        st.text_input("You:", key="chat_input_beta")

        col1, col2 = st.columns(2)
        with col1:
            st.button("Send", key="send_beta", on_click=handle_send_beta)
        with col2:
            save_clicked = st.button("💾 Save consult", key="save_beta")

        # ----------------------------------------
        # PROCESS USER MESSAGE
        # ----------------------------------------
        if st.session_state.pending_beta:
            user_text = st.session_state.pending_beta
            st.session_state.pending_beta = ""

            # Add user's message
            st.session_state.messages_beta.append({
                "role": "user",
                "text": user_text,
            })

            # ------------- INTENT DETECTION (greetings & small talk) ------------
            intent = detect_intent(user_text)

            if intent == "greeting":
                st.session_state.messages_beta.append({
                    "role": "assistant",
                    "text": "Hi! 💗 Tell me your main skin concern — acne, dryness, redness, pigmentation, anything."
                })
                return

            if intent == "small_talk":
                st.session_state.messages_beta.append({
                    "role": "assistant",
                    "text": "I’m here whenever you’re ready 💫 Tell me what’s bothering your skin."
                })
                return

            # Severe keyword check
            if detect_severe_keywords(user_text):
                warn = (
                    "I noticed words like bleeding, pus, fever or severe pain. "
                    "This can be serious — consider seeing a dermatologist soon. 🧑‍⚕️"
                )
                st.session_state.messages_beta.append({"role": "assistant", "text": warn})

            # Build messages for API
            messages = [{
                "role": "system",
                "content": """
You are Smart Skin Coach.

Respond ONLY in JSON with keys:
{
 "summary": "",
 "am_routine": [],
 "pm_routine": [],
 "diy": [],
 "caution": ""
}

NO markdown. NO bullet points outside JSON. NO explanations outside JSON.
                """,
            }]

            # Add last few turns for context
            for m in st.session_state.messages_beta[-6:]:
                api_role = "assistant" if m["role"] == "assistant" else "user"
                messages.append({"role": api_role, "content": m["text"]})

            # Call API
            with st.spinner("Preparing your gentle routine…"):
                reply_text, err = call_openrouter_chat(messages)

            # If API error
            if err:
                fallback = {
                    "summary": "Basic routine due to network issue.",
                    "am_routine": ["Cleanser", "Moisturizer", "Sunscreen"],
                    "pm_routine": ["Cleanser", "Moisturizer"],
                    "diy": ["Patch test everything"],
                    "caution": "Visit dermatologist if severe.",
                }
                st.session_state.last_plan_beta = fallback
                st.session_state.messages_beta.append({
                    "role": "assistant",
                    "text": "Basic fallback routine generated.",
                })

            else:
                # JSON parse
                try:
                    parsed = json.loads(reply_text)
                    st.session_state.last_plan_beta = parsed
                    st.session_state.messages_beta.append({
                        "role": "assistant",
                        "text": "Your personalised routine is ready ✔️",
                    })
                except:
                    st.session_state.last_plan_beta = {"raw": reply_text}
                    st.session_state.messages_beta.append({
                        "role": "assistant",
                        "text": "I couldn't format JSON, but here’s my advice.",
                    })

        # ----------------------------------------
        # SHOW ROUTINE (Glass UI)
        # ----------------------------------------
        plan = st.session_state.last_plan_beta
        if plan:

            if "summary" in plan:
                st.markdown(f"""
                <div class="glass-box">
                    <h4>💗 Summary</h4>
                    {plan['summary']}
                </div>
                """, unsafe_allow_html=True)

            if "am_routine" in plan:
                am_html = "".join([f"<li>{s}</li>" for s in plan["am_routine"]])
                st.markdown(f"""
                <div class="glass-box">
                    <h4>🌞 AM Routine</h4>
                    <ul>{am_html}</ul>
                </div>
                """, unsafe_allow_html=True)

            if "pm_routine" in plan:
                pm_html = "".join([f"<li>{s}</li>" for s in plan["pm_routine"]])
                st.markdown(f"""
                <div class="glass-box">
                    <h4>🌙 PM Routine</h4>
                    <ul>{pm_html}</ul>
                </div>
                """, unsafe_allow_html=True)

            if "diy" in plan:
                diy_html = "".join([f"<li>{s}</li>" for s in plan["diy"]])
                st.markdown(f"""
                <div class="glass-box">
                    <h4>🧴 DIY Care</h4>
                    <ul>{diy_html}</ul>
                </div>
                """, unsafe_allow_html=True)

            if "caution" in plan:
                st.markdown(f"""
                <div class="warn-box">
                    ⚠️ {plan['caution']}
                </div>
                """, unsafe_allow_html=True)

            # Download
            st.download_button(
                "⬇️ Download routine (.txt)",
                data=json.dumps(plan, indent=2),
                file_name="skinsync_routine.txt"
            )

        # ----------------------------------------
        # SAVE CONSULT
        # ----------------------------------------
        if save_clicked:
            if st.session_state.last_plan_beta is None:
                st.warning("No consult to save yet!")
            else:
                payload = {
                    "profile": st.session_state.profile,
                    "conversation": st.session_state.messages_beta,
                    "last_plan": st.session_state.last_plan_beta,
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
                st.success("Saved to history! 💗")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 📷 IMAGE ANALYSIS PAGE
# ==========================================
def render_scan():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📷 Skin Analysis", unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1])

    # ---------- LEFT: IMAGE UPLOAD ----------
    with col1:
        uploaded = st.file_uploader(
            "Upload a clear face photo (front-facing, good lighting)",
            type=["png", "jpg", "jpeg"],
        )

        if uploaded:
            img_bytes = uploaded.read()
            image = Image.open(BytesIO(img_bytes))
            st.image(image, caption="Uploaded image", use_column_width=True)

            if st.button("Analyze redness & inflammation"):
                mean_red, severity = analyze_skin_image(image)

                st.markdown(f"""
                <div class="glass-box">
                    <h4>🔎 Analysis Result</h4>
                    <p><strong>Redness score:</strong> {mean_red:.2f}</p>
                    <p><strong>Severity:</strong> {severity}</p>
                </div>
                """, unsafe_allow_html=True)

                st.info(
                    "This is a heuristic, educational-only analysis. "
                    "Real diagnosis always requires a dermatologist."
                )

        else:
            st.info("No image uploaded — please upload a face photo to start analysis.")

    # ---------- RIGHT: HOW IT WORKS ----------
    with col2:
        st.markdown("""
        <div class="glass-box">
            <h4>📘 How This Works</h4>
            <ul>
                <li>Converts image to RGB</li>
                <li>Computes redness index (R - (G+B)/2)</li>
                <li>Normalizes values 0–1</li>
                <li>Averages pixels</li>
                <li>Maps to mild / moderate / high</li>
            </ul>
            <p style="opacity:0.7;">
                This uses basic computer-vision preprocessing — useful for your resume.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
# BACK BUTTON
# ==========================================
def render_back_to_home():
    st.markdown(
        """
        <a href="?page=home" style="text-decoration:none;">
            <button style="
                margin-top:10px;
                background:#eadcff;
                padding:6px 12px;
                border-radius:20px;
                border:1px solid #d6c0f5;
                font-size:13px;
            ">← Back to Home</button>
        </a>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# 📔 DAILY SKIN DIARY (optional)
# ==========================================
def render_diary():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📔 Daily Skin Diary")

    with st.form("diary_form"):
        mood = st.selectbox("Mood today", ["😊 Good", "😐 Okay", "😣 Bad"])
        redness = st.slider("Redness level", 0, 10, 2)
        oiliness = st.slider("Oiliness level", 0, 10, 3)
        sleep_hours = st.number_input("Sleep hours", 0.0, 24.0, 7.0)
        water = st.number_input("Water intake (glasses)", 0, 30, 6)
        note = st.text_area("Notes")

        submitted = st.form_submit_button("Save to Diary")

        if submitted:
            c.execute(
                "INSERT INTO diary (entry_date,mood,redness,oiliness,sleep_hours,water_glasses,note,created_at)"
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(datetime.today().date()),
                    mood,
                    redness,
                    oiliness,
                    sleep_hours,
                    water,
                    note,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            st.success("Diary entry saved 💗")

    st.markdown("### Recent Entries")
    df = pd.read_sql_query(
        "SELECT entry_date, mood, redness, oiliness, sleep_hours, water_glasses, note "
        "FROM diary ORDER BY id DESC LIMIT 30",
        conn,
    )
    st.dataframe(df, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# PAGE ROUTER
# ==========================================
def router():
    query = st.experimental_get_query_params()
    page = query.get("page", ["home"])[0]

    st.session_state.page = page

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
    elif page == "diary":
        render_diary()
    else:
        render_home()
# ==========================================
# RUN APP
# ==========================================
router()

