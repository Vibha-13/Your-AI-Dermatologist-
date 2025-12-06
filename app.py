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

# ---------- SESSION STATE MISC ----------
if "chat_text" not in st.session_state:
    st.session_state.chat_text = ""

# ========== ENV & API KEY ==========
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ----------- SAFE NON-BLOCKING BEAUTIFUL SPLASH -----------
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
            0% { opacity: 1; }
            80% { opacity: 1; }
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
        animation: fadeOut 1.2s ease-out 1.8s forwards;
        pointer-events: none;
    ">
        <div style="text-align:center; animation: fadeIn 1s ease-out forwards;">
            <div style="font-size:12px; letter-spacing:0.25em; color:#7a5a71; margin-bottom:6px;">
                AI · SKINCARE · DERMATOLOGY
            </div>
            <div style="font-size:42px; font-family:'Playfair Display'; color:#251320; letter-spacing:0.17em;">
                SKINSYNC
            </div>
        </div>
    </div>
    """
    st.markdown(splash_html, unsafe_allow_html=True)
    # Show it only once per session; no blocking sleep
    st.session_state.show_splash = False

# ========== BASIC CONFIG ==========
st.set_page_config(
    page_title="SkinSync — AI Dermatologist",
    page_icon="💠",
    layout="wide",
)

# ---------- Global Light Theme / Text Fix ----------
st.markdown(
    """
    <style>
    @media (prefers-color-scheme: dark) {
        html, body, [class*="css"] {
            color-scheme: light !important;
        }
    }

    /* GLOBAL TEXT COLOR so nothing is white on pink */
    html, body, [class*="css"] {
        color: #2b1826 !important;
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, h5 {
        color: #1f111a !important;
        font-family: 'Playfair Display', serif !important;
    }
    p, span, label, li, td, th, .stMarkdown, .stText {
        color: #35202b !important;
    }

    /* Header bar light */
    header[data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #2b1826 !important;
    }
    header[data-testid="stHeader"] * {
        color: #2b1826 !important;
        fill: #2b1826 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
    /* Simple fade/slide animation */
    @keyframes fadeUpSoft {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .derm-bubble, .user-bubble, .glass-box, .warn-box {
        animation: fadeUpSoft 0.35s ease-out;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- GLOBAL STYLES (ROSY / LAVENDER AESTHETIC) ----------
st.markdown("""
<style>

.stApp {
    background: linear-gradient(180deg,#fffdfd 0%,#fff7fb 30%,#feeef7 65%,#fbe5f1 100%);
}

/* -----------------------------------------------------
   🌸 CARD BASE (GLASS PREMIUM CARD)
------------------------------------------------------ */
.premium-card {
    background: rgba(255, 255, 255, 0.45);
    border-radius: 22px;
    padding: 20px 26px;
    border: 1px solid rgba(255, 255, 255, 0.55);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 18px 42px rgba(0, 0, 0, 0.10);

    /* Fade-in default (opacity 0 until animation starts) */
    opacity: 0;
    animation: cardFadeUp 0.55s ease-out forwards;
    animation-delay: var(--delay, 0ms);

    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
}

/* -----------------------------------------------------
   ✨ 1: STAGGER ANIMATION PER CARD
------------------------------------------------------ */
.premium-card:nth-child(1) { --delay: 60ms; }
.premium-card:nth-child(2) { --delay: 130ms; }
.premium-card:nth-child(3) { --delay: 200ms; }
.premium-card:nth-child(4) { --delay: 270ms; }
.premium-card:nth-child(5) { --delay: 340ms; }

/* -----------------------------------------------------
   ✨ 2: CARD FADE-UP ANIMATION
------------------------------------------------------ */
@keyframes cardFadeUp {
    0% {
        opacity: 0;
        transform: translateY(14px) scale(0.98);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* -----------------------------------------------------
   ✨ 3: SHIMMER HOVER EFFECT
------------------------------------------------------ */
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
    transform: skewX(-20deg);
    transition: 0.35s;
}

.premium-card:hover::after {
    left: 150%;
    transition: 0.8s ease-out;
}

/* -----------------------------------------------------
   ✨ 4: LAVENDER GLOW + SCALE ON HOVER
------------------------------------------------------ */
.premium-card:hover {
    transform: translateY(-5px) scale(1.01);
    background: rgba(255, 240, 255, 0.6);
    border-color: #e3c6ff;
    box-shadow: 0 28px 65px rgba(255,182,222,0.35);
}

/* -----------------------------------------------------
   💜 BUTTONS (Lavender aesthetic)
------------------------------------------------------ */
.stButton > button {
    background-color: #eadcff !important;
    color: #3a0030 !important;
    border-radius: 25px !important;
    border: 1px solid #d6c0f5 !important;
    font-weight: 600 !important;
    padding: 0.45rem 1.2rem !important;
    box-shadow: 0 8px 18px rgba(0,0,0,0.08);
    transition: 0.25s ease;
}

.stButton > button:hover {
    background-color: #d8c1ff !important;
    transform: translateY(-2px);
}

/* -----------------------------------------------------
   🌿 CHAT BUBBLES (Glass look)
------------------------------------------------------ */
.derm-bubble,
.user-bubble {
    animation: fadeUpSoft 0.35s ease-out;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 12px 16px;
}

/* Assistant bubble */
.derm-bubble {
    background: rgba(255,255,255,0.75);
}

/* User bubble */
.user-bubble {
    background: rgba(248,220,250,0.75);
    margin-left: 40px;
}

/* Small global fade animation */
@keyframes fadeUpSoft {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* -----------------------------------------------------
   ✨ GLASS BOXES (Routine sections)
------------------------------------------------------ */
.glass-box {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.08);
    border: 1px solid rgba(255,255,255,0.6);
    animation: fadeUpSoft 0.35s ease-out;
}

.warn-box {
    background: rgba(255,220,220,0.55);
    border-left: 4px solid #d40000;
    border-radius: 14px;
    padding: 12px 16px;
    backdrop-filter: blur(14px);
    animation: fadeUpSoft 0.35s ease-out;
}

/* -----------------------------------------------------
   ✨ 5: Smart Skin Coach Tagline
------------------------------------------------------ */
.smart-tagline {
    text-align: center;
    font-size: 11px;
    margin-top: 6px;
    color: #8b6a82;
    letter-spacing: 0.11em;
    animation: fadeUpSoft 0.6s ease-out;
}

</style>
""", unsafe_allow_html=True)


# ========== DB SETUP ==========

DB_PATH = "skinsync.db"

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

conn = get_connection()
c = conn.cursor()

# Safe to run on every start; IF NOT EXISTS avoids duplicates
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
c.execute(
    """CREATE TABLE IF NOT EXISTS diary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        mood TEXT,
        redness INTEGER,
        oiliness INTEGER,
        sleep_hours REAL,
        water_glasses INTEGER,
        note TEXT,
        created_at TEXT
    )"""
)
conn.commit()


# ========== SESSION STATE ==========

# Unique session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.utcnow().isoformat()

# MAIN AI DERM CHAT history
if "messages_ai" not in st.session_state:
    st.session_state.messages_ai = []

# BETA COACH chat history
if "messages_beta" not in st.session_state:
    st.session_state.messages_beta = []

# Last generated plans for both
if "last_plan_ai" not in st.session_state:
    st.session_state.last_plan_ai = None

if "last_plan_beta" not in st.session_state:
    st.session_state.last_plan_beta = None

# User profile
if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "",
        "age_bucket": "18–24",
        "skin_type": "Combination",
        "main_concern": "Acne / Breakouts",
        "sensitivity": "Normal",
        "location": "",
    }

# Current page
if "page" not in st.session_state:
    st.session_state.page = "home"

# Consent
if "consent" not in st.session_state:
    st.session_state.consent = False

# Chat inputs for both chats
if "chat_input_ai" not in st.session_state:
    st.session_state.chat_input_ai = ""

if "chat_input_beta" not in st.session_state:
    st.session_state.chat_input_beta = ""

# Pending inputs (so 1-click works properly)
if "pending_user_input_ai" not in st.session_state:
    st.session_state.pending_user_input_ai = ""

if "pending_user_input_beta" not in st.session_state:
    st.session_state.pending_user_input_beta = ""


# ---------- ROUTING FROM QUERY PARAMS ----------
qs = st.experimental_get_query_params()
if "page" in qs:
    st.session_state.page = qs["page"][0]

# ========== HELPERS ==========

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

def append_message(role: str, text: str):
    st.session_state.messages.append({"role": role, "text": text})

def build_system_prompt():
    p = st.session_state.profile
    return f"""
You are SkinSync — a warm, gentle, supportive AI skincare assistant.

User profile:
- Name: {p.get('name') or 'User'}
- Age range: {p.get('age_bucket')}
- Skin type: {p.get('skin_type')}
- Main concern: {p.get('main_concern')}
- Sensitivity: {p.get('sensitivity')}
- Location: {p.get('location') or 'Not specified'}

Your role:
- Listen carefully to what the user says.
- Ask kind follow-up questions when needed.
- Give simple science-based skincare routines.
- ALWAYS fit suggestions to their skin type and sensitivity.
- ALWAYS be cautious: you are NOT a doctor and cannot diagnose.
- Recommend dermatologist visits for painful, severe or worsening symptoms.
- Assume India/Asia skincare context unless user says otherwise.
- Use a friendly, caring tone.

STRUCTURE YOUR ANSWER LIKE THIS:
1. 💗 Short summary of what you understood  
2. 🌞 Morning routine (simple bullet points)  
3. 🌙 Night routine  
4. 🧴 1–2 DIY tips (safe ingredients only)  
5. ⚠️ When to see a dermatologist

IMPORTANT — FORMAT RULES:
- Do not output JSON.
- Do not use curly braces or square brackets.
  (Write normally, avoid symbols like {{ }} or [[ ]].)
- Always respond in natural language paragraphs or bullet points.
- NEVER produce structured data or code-like output.
- ALWAYS write in natural language paragraphs or bullet points.
- ALWAYS sound human, soft, caring — not like an API.
"""

def build_beta_prompt():
    p = st.session_state.profile
    return (
f"You are Smart Skin Coach — a warm, friendly skincare assistant.\n\n"
f"User profile:\n"
f"- Skin type: {p.get('skin_type')}\n"
f"- Main concern: {p.get('main_concern')}\n"
f"- Sensitivity: {p.get('sensitivity')}\n"
f"- Age range: {p.get('age_bucket')}\n\n"

"Your personality:\n"
"- Soft, supportive, human-like\n"
"- Explain simply, like a best friend who knows skincare\n"
"- Avoid heavy science or unnecessary jargon\n\n"

"Your goals:\n"
"- Understand what the user wants help with\n"
"- Ask clarifying questions ONLY if needed\n"
"- Provide a gentle, personalised AM + PM routine\n"
"- Give 1–2 safe DIY remedies max\n"
"- Mention lifestyle factors (hydration, sleep, stress) when relevant\n"
"- NEVER diagnose — you are not a doctor\n"
"- ALWAYS add a gentle caution if symptoms worsen\n\n"

"Formatting rules:\n"
"- NEVER output JSON\n"
"- NEVER output dictionary-like or list-like structures\n"
"- Do NOT use curly braces or square brackets\n"
  "(Avoid characters such as {{ }}, [[ ]], or code blocks)\n"
"- ALWAYS write in natural human language\n"
"- Use friendly paragraphs or bullet points only\n\n"

"Structure your response like this:\n"
"1. 💗 Understanding what the user said\n"
"2. 🌞 AM routine (bullet points)\n"
"3. 🌙 PM routine (bullet points)\n"
"4. 🧴 DIY tips (1–2 max)\n"
"5. ⚠️ When to see a dermatologist\n\n"

"ONLY output conversational text. Never output code, JSON, or structured data."
    )

def build_chat_messages():
    """
    Build the messages list with a system prompt + recent history only
    to avoid token explosions.
    """
    messages = [{"role": "system", "content": build_system_prompt()}]

    # Keep only the last 10 turns
    recent = st.session_state.messages[-10:]

    for m in recent:
        role = "assistant" if m["role"] == "assistant" else "user"
        messages.append({"role": role, "content": m["text"]})

    return messages

def call_openrouter_chat(messages, retries=1):
    if not OPENROUTER_API_KEY:
        return None, "Missing API key — please set OPENROUTER_API_KEY in your environment."

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
        "max_tokens": 650,
        "temperature": 0.65,

    }

    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content, None
        except requests.Timeout:
            if attempt < retries:
                continue
            return None, "The AI service is taking too long to respond. Please try again in a moment."
        except requests.RequestException:
            if attempt < retries:
                continue
            return None, "I’m having trouble reaching the AI service right now. Please try again soon."
        except Exception:
            return None, "Something went wrong while generating the response."

def analyze_skin_image(image: Image.Image):
    try:
        img = image.convert("RGB")
        arr = np.array(img).astype("float32")

        # basic shape check
        if len(arr.shape) != 3 or arr.shape[2] != 3:
            return 0.0, "Invalid image format — please upload a clear color photo."

        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]

        redness = r - (g + b) / 2

        # if the image is uniform (no variation)
        if np.all(redness == redness.flat[0]):
            return 0.0, "Image has no detectable color variation — try a clearer face photo."

        # safe range calculation
        diff = redness.max() - redness.min()
        if diff < 1e-6:
            diff = 1e-6  # avoid division by zero

        redness_normalized = (redness - redness.min()) / diff
        mean_red = float(np.mean(redness_normalized))

        if mean_red < 0.25:
            severity = "Very mild / almost no visible redness 🙂"
        elif mean_red < 0.45:
            severity = "Mild redness — could be light irritation or occasional acne 🌸"
        elif mean_red < 0.65:
            severity = "Moderate redness — noticeable inflammation 🔎"
        else:
            severity = "High redness — consider gentle care and maybe seeing a dermatologist if painful ⚠️"

        return mean_red, severity

    except Exception:
        return 0.0, "Unable to analyze this image — please upload a clearer photo."

# ========== SIDEBAR: SKIN PROFILE ==========
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
        "⚕️ **Important:** SkinSync gives educational skincare guidance only, "
        "not medical diagnosis or treatment."
    )
    consent = st.checkbox(
        "I understand this is **not** a substitute for a dermatologist.",
        value=st.session_state.consent,
    )
    st.session_state.consent = consent

# ========== LAYOUT HELPER ==========
def render_back_to_home():
    with st.container():
        st.markdown('<div class="back-button-container page-container">', unsafe_allow_html=True)
        if st.button("← Back to Home"):
            go_to("home")
        st.markdown("</div>", unsafe_allow_html=True)

# ========== PAGES ==========

def render_home():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    # ---- Hero Title ----
    st.markdown('<div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">SkinSync</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;font-size:14px;margin-top:-4px;'>"
        "Your AI-powered skincare companion for gentle, science-based routines."
        "</p>",
        unsafe_allow_html=True,
    )

    # ---- Small profile summary ----
    prof = st.session_state.profile
    st.markdown(
        f"<p style='text-align:center;font-size:12px;margin-top:4px;opacity:0.8;'>"
        f"Signed in as <strong>{prof.get('name') or 'Guest'}</strong> · "
        f"{prof.get('skin_type')} skin · {prof.get('main_concern')}</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ---- Feature Cards ----
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)

    # Row 1
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
                  View your saved consults and generated routines at a glance.
                </div>
              </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    # Row 3 (New Smart Coach Beta)
    col5, col6 = st.columns(2)
    with col5:
        st.markdown(
            """
            <a class="card-link" href="?page=chat_v2">
              <div class="premium-card">
                <div class="card-header-line">
                  <span class="card-emoji">🧠</span>
                  <span>Smart Skin Coach (Beta)</span>
                </div>
                <div class="card-subtitle">
                  Smarter, context-aware AI that remembers your concerns and regenerates variations.
                </div>
              </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='smart-tagline'>Your smarter, gentler skincare companion ✨</div>", unsafe_allow_html=True)


def render_chat():
    # Page wrapper
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 🩺 AI Derm Chat", unsafe_allow_html=True)

    # --------- CONSENT CHECK ---------
    if not st.session_state.consent:
        st.warning(
            "Please confirm in the sidebar that you understand SkinSync is not a doctor "
            "before using the AI chat."
        )
        render_back_to_home()
        return

    # Small profile line
    prof = st.session_state.profile
    st.markdown(
        f"<p style='font-size:12px;opacity:0.8;'>"
        f"{prof.get('skin_type')} skin · {prof.get('main_concern')} · "
        f"sensitivity: {prof.get('sensitivity')}</p>",
        unsafe_allow_html=True,
    )

    # ---------- chat state ----------
    messages_ai = st.session_state.messages_ai

    # Initial assistant message
    if len(messages_ai) == 0:
        messages_ai.append({
            "role": "assistant",
            "text": (
                "Hi, I’m your SkinSync dermatologist assistant 🌿\n\n"
                "Tell me about your skin today — what’s bothering you?"
            )
        })

    # ---------- Show conversation ----------
    st.markdown('<div class="chat-card">', unsafe_allow_html=True)

    for m in messages_ai:
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

    # ---------- Send callback ----------
    def handle_send_ai():
        text = st.session_state.chat_input_ai.strip()
        if text:
            st.session_state.pending_user_input_ai = text
            st.session_state.chat_input_ai = ""

    # Input box
    st.text_input("You:", key="chat_input_ai")

    # Buttons row
    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("Send", key="chat_send_ai", on_click=handle_send_ai)
    with col2:
        save_clicked = st.button("💾 Save consult", key="save_consult_ai")

    # ==========================================================
    # PROCESS USER MESSAGE
    # ==========================================================
    if st.session_state.pending_user_input_ai:
        user_text = st.session_state.pending_user_input_ai
        st.session_state.pending_user_input_ai = ""

        # Add to history
        messages_ai.append({"role": "user", "text": user_text})

        # Build system + conversation
        sys_prompt = build_system_prompt()
        payload_messages = [{"role": "system", "content": sys_prompt}]

        for m in messages_ai[-10:]:  # limit history for speed
            role = "assistant" if m["role"] == "assistant" else "user"
            payload_messages.append({"role": role, "content": m["text"]})

        # Severe keyword detection
        if detect_severe_keywords(user_text):
            warn = (
                "I noticed signs of severe irritation. I can give gentle guidance, "
                "but please consider seeing an in-person dermatologist if symptoms worsen. 🧑‍⚕️"
            )
            messages_ai.append({"role": "assistant", "text": warn})
            payload_messages.append({"role": "assistant", "content": warn})

        # API call
        with st.spinner("Thinking about your skin…"):
            reply, err = call_openrouter_chat(payload_messages)

        # Handle errors
        if err:
            fallback = (
                "I couldn't get a full response right now, but here's a quick routine:\n"
                "- 🌞 Morning: gentle cleanser → moisturizer → sunscreen\n"
                "- 🌙 Night: cleanse → moisturizer\n"
                "Introduce actives slowly and always patch test."
            )
            messages_ai.append({"role": "assistant", "text": fallback})
            st.session_state.last_plan_ai = fallback
            st.warning(err)
        else:
            # Normal successful reply
            messages_ai.append({"role": "assistant", "text": reply})
            st.session_state.last_plan_ai = reply

    # ==========================================================
    # DOWNLOAD LAST ROUTINE
    # ==========================================================
    if st.session_state.last_plan_ai:
        st.download_button(
            "⬇️ Download routine (.txt)",
            data=st.session_state.last_plan_ai,
            file_name="skinsync_routine.txt",
            mime="text/plain",
        )
        with st.expander("📌 View latest routine"):
            st.markdown(st.session_state.last_plan_ai)

    # ==========================================================
    # SAVE CONSULT
    # ==========================================================
    if save_clicked:
        if st.session_state.last_plan_ai is None:
            st.warning("No plan to save yet — send a message first.")
        else:
            payload = {
                "profile": st.session_state.profile,
                "conversation": messages_ai,
                "last_plan": st.session_state.last_plan_ai,
            }
            c.execute(
                "INSERT INTO consults (session_id, data, created_at) VALUES (?,?,?)",
                (
                    st.session_state.session_id,
                    json.dumps(payload),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            st.success("Consult saved ✔️")

    st.markdown("</div>", unsafe_allow_html=True)

    # Back button at bottom (prevents double-click issues)
    render_back_to_home()

    st.markdown("</div>", unsafe_allow_html=True)

def render_diary():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📔 Skin Diary", unsafe_allow_html=True)
    st.write("Track how your skin feels day by day — great for spotting patterns.")

    today = datetime.today().date()

    with st.form("diary_form"):
        entry_date = st.date_input("Date", value=today)
        mood = st.selectbox("Overall mood about your skin today", ["😊 Great", "😌 Okay", "😣 Not good"])
        redness = st.slider("Redness level", 0, 10, 3)
        oiliness = st.slider("Oiliness level", 0, 10, 4)
        sleep_hours = st.number_input("Sleep (hours)", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
        water_glasses = st.number_input("Water intake (glasses)", min_value=0, max_value=30, value=8, step=1)
        note = st.text_area("Notes (products used, triggers, improvements, etc.)")

        submitted = st.form_submit_button("Save diary entry")
        if submitted:
            c.execute(
                "INSERT INTO diary (entry_date, mood, redness, oiliness, sleep_hours, water_glasses, note, created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(entry_date),
                    mood,
                    int(redness),
                    int(oiliness),
                    float(sleep_hours),
                    int(water_glasses),
                    note.strip(),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            st.success("Diary entry saved 🌸")

    st.markdown("---")
    st.subheader("Recent entries")

    df = pd.read_sql_query(
        "SELECT entry_date, mood, redness, oiliness, sleep_hours, water_glasses, note "
        "FROM diary ORDER BY entry_date DESC, id DESC LIMIT 30",
        conn,
    )

    if df.empty:
        st.info("No diary entries yet — start by adding how your skin felt today.")
    else:
        st.dataframe(df, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

def render_scan():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📷 Skin Image Analysis")

    # CONSENT CHECK
    if not st.session_state.consent:
        st.warning(
            "Please confirm in the sidebar that you understand this is an educational tool "
            "only before using image analysis."
        )
        return

    col1, col2 = st.columns([1.2, 1])

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
                st.markdown("#### 🔎 Analysis result")
                st.write(f"**Redness score (0–1):** `{mean_red:.2f}`")
                st.write(f"**Severity:** {severity}")
                st.info(
                    "This is a heuristic, educational-only analysis. "
                    "Real diagnosis always requires a professional dermatologist."
                )
        else:
            st.info("No image uploaded — please upload a face photo to start analysis.")

    with col2:
        st.markdown("#### How this works (for your resume)")
        st.markdown(
            """
- Converts image to RGB  
- Computes a **redness index** (R - (G+B)/2)  
- Normalizes it between 0–1  
- Averages all pixels  
- Maps to **mild / moderate / high** categories  

This demonstrates computer-vision feature engineering:  
colour channels, normalization, and severity mapping.
            """
        )

    st.markdown("</div>", unsafe_allow_html=True)

def render_history():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📋 Consult History (Your Skin Timeline)", unsafe_allow_html=True)

    # Load last 100 consults
    df = pd.read_sql_query(
        "SELECT id, session_id, data, created_at FROM consults ORDER BY id DESC LIMIT 100",
        conn,
    )

    if df.empty:
        st.info("No consults saved yet — after a chat, click 'Save consult' to store one.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Parse all consults
    parsed_entries = []
    for _, row in df.iterrows():
        try:
            data = json.loads(row["data"])
            parsed_entries.append({
                "id": row["id"],
                "created_at": row["created_at"],
                "profile": data.get("profile", {}),
                "plan": data.get("last_plan", {}),
                "convo": data.get("conversation", []),
            })
        except:
            continue

    # Timeline renderer
    st.markdown("""
    <style>
        .timeline-dot {
            width: 12px;
            height: 12px;
            background: #c186db;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .glass-box {
            background: rgba(255, 255, 255, 0.55);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 18px;
            padding: 18px 20px;
            margin: 10px 0 20px 0;
            box-shadow: 0 12px 35px rgba(0,0,0,0.08);
            border: 1px solid rgba(255,255,255,0.6);
        }
    </style>
    """, unsafe_allow_html=True)

    def render_glass_section(title, items):
        st.markdown(f"""
        <div class="glass-box">
            <h4 style="margin-top:0;color:#381b2f;">{title}</h4>
            <ul style="color:#4a243d;">
                {''.join([f"<li>{i}</li>" for i in items])}
            </ul>
        </div>
        """, unsafe_allow_html=True)

    def render_warning(text):
        st.markdown(f"""
        <div style="
            background: rgba(255, 220, 220, 0.55);
            border-left: 4px solid #d40000;
            backdrop-filter: blur(14px);
            border-radius: 14px;
            padding: 12px 16px;
            margin-top: 12px;
            color:#5c1f1f;
        ">
        ⚠️ {text}
        </div>
        """, unsafe_allow_html=True)

    # ---- DISPLAY EACH CONSULT AS A TIMELINE ENTRY ----
    for entry in parsed_entries:
        date = entry["created_at"][:10]
        profile = entry["profile"]
        plan = entry["plan"]

        st.markdown(f"""
        <p>
            <span class="timeline-dot"></span>
            <strong>{date}</strong> — {profile.get('main_concern', 'Consultation')}
        </p>
        """, unsafe_allow_html=True)

        # Summary
        if isinstance(plan, dict) and plan.get("summary"):
            st.markdown(f"""
            <div class="glass-box">
                <h4 style="margin-top:0;color:#381b2f;">💗 Summary</h4>
                <p style="color:#4a243d;">{plan['summary']}</p>
            </div>
            """, unsafe_allow_html=True)

        # AM Routine
        if isinstance(plan, dict) and plan.get("am_routine"):
            render_glass_section("🌞 AM Routine", plan["am_routine"])

        # PM Routine
        if isinstance(plan, dict) and plan.get("pm_routine"):
            render_glass_section("🌙 PM Routine", plan["pm_routine"])

        # DIY Care
        if isinstance(plan, dict) and plan.get("diy"):
            render_glass_section("🧴 DIY Care", plan["diy"])

        # Caution
        if isinstance(plan, dict) and plan.get("caution"):
            if plan["caution"].strip():
                render_warning(plan["caution"])

        st.markdown("<hr style='opacity:0.25;'>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def detect_intent(user_text: str) -> str:
    """
    Very lightweight intent detection.
    Returns: greeting / small_talk / routine_request / skin_issue / other
    """
    if not user_text:
        return "other"
    t = user_text.lower().strip()

    greetings = ["hi", "hello", "hey", "heyy", "hii", "good morning", "good night", "good evening"]
    small_talk = ["ok", "okay", "k", "hmm", "hmmm", "ya", "yeah", "yes", "right", "fine"]

    if any(t == g or t.startswith(g + " ") for g in greetings):
        return "greeting"
    if t in small_talk:
        return "small_talk"

    routine_words = ["routine", "am routine", "pm routine", "skincare", "skin care", "regimen", "schedule"]
    if any(w in t for w in routine_words):
        return "routine_request"

    skin_words = ["acne", "pimple", "pimples", "zit", "spots", "dark spots", "pigmentation",
                  "dry", "dryness", "oily", "oiliness", "redness", "itch", "itchy",
                  "sensitive", "eczema", "peeling", "flaky", "tan", "tanning"]
    if any(w in t for w in skin_words):
        return "skin_issue"

    return "other"


def find_last_meaningful_user_message(min_words: int = 3) -> str | None:
    """
    Go through history from the end and return the last user message
    that has at least `min_words` words. This avoids 'hi', 'ok', etc.
    """
    for msg in reversed(st.session_state.messages):
        if msg.get("role") == "user":
            if len(msg.get("text", "").split()) >= min_words:
                return msg["text"]
    return None

def render_chat_v2():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 🧠 Smart Skin Coach (Beta)", unsafe_allow_html=True)

    # --------- CONSENT CHECK ---------
    if not st.session_state.consent:
        st.warning(
            "Please confirm in the sidebar that you understand SkinSync is not a doctor "
            "before using the AI coach."
        )
        render_back_to_home()
        return

    # Profile line
    prof = st.session_state.profile
    st.markdown(
        f"<p style='font-size:12px;opacity:0.8;'>"
        f"{prof.get('skin_type')} skin · {prof.get('main_concern')} · "
        f"sensitivity: {prof.get('sensitivity')}</p>",
        unsafe_allow_html=True,
    )

    # Chat state
    messages_beta = st.session_state.messages_beta

    # First welcome message
    if len(messages_beta) == 0:
        messages_beta.append({
            "role": "assistant",
            "text": (
                "Hi, I'm your Smart Skin Coach 🌿\n\n"
                "Tell me what’s bothering your skin today — dryness, acne, redness, "
                "texture, anything. I’ll help you build a gentle routine."
            )
        })

    # ---------- Show chat ----------
    st.markdown('<div class="chat-card">', unsafe_allow_html=True)

    for m in messages_beta:
        if m["role"] == "assistant":
            st.markdown(
                f"<div class='derm-bubble'><strong>Coach</strong>: {m['text']}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='user-bubble'><strong>You</strong>: {m['text']}</div>",
                unsafe_allow_html=True,
            )

    # ---------- Input handler ----------
    def handle_send_beta():
        text = st.session_state.chat_input_beta.strip()
        if text:
            st.session_state.pending_user_input_beta = text
            st.session_state.chat_input_beta = ""

    # Input box
    st.text_input("You:", key="chat_input_beta")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("Send", key="chat_send_beta", on_click=handle_send_beta)
    with col2:
        save_clicked = st.button("💾 Save consult", key="save_consult_beta")

    # ==========================================================
    # PROCESS USER MESSAGE
    # ==========================================================
    if st.session_state.pending_user_input_beta:
        user_text = st.session_state.pending_user_input_beta
        st.session_state.pending_user_input_beta = ""

        messages_beta.append({"role": "user", "text": user_text})

        # Build Beta system prompt
        sys_prompt = build_beta_prompt()

        payload_messages = [{"role": "system", "content": sys_prompt}]

        # Only last 8 messages → faster + more focused
        for m in messages_beta[-8:]:
            role = "assistant" if m["role"] == "assistant" else "user"
            payload_messages.append({"role": role, "content": m["text"]})

        # If severe symptoms
        if detect_severe_keywords(user_text):
            warn = (
                "I noticed signs of strong irritation. I can give gentle guidance, "
                "but please seek an in-person dermatologist if symptoms get worse. 🧑‍⚕️"
            )
            messages_beta.append({"role": "assistant", "text": warn})
            payload_messages.append({"role": "assistant", "content": warn})

        # API call
        with st.spinner("Thinking gently about your routine…"):
            reply_text, err = call_openrouter_chat(payload_messages)

        if err:
            fallback = (
                "I couldn’t load a full routine right now, "
                "but try this simple plan:\n\n"
                "🌞 Morning: gentle cleanser → moisturizer → sunscreen\n"
                "🌙 Night: cleanser → light moisturizer\n"
                "Take it slow and patch test everything. 💗"
            )
            messages_beta.append({"role": "assistant", "text": fallback})
            st.session_state.last_plan_beta = fallback
            st.warning(err)
        else:
            # Natural-language reply (no JSON)
            messages_beta.append({"role": "assistant", "text": reply_text})
            st.session_state.last_plan_beta = reply_text

    # ==========================================================
    # DOWNLOAD LAST ROUTINE
    # ==========================================================
    if st.session_state.last_plan_beta:
        st.download_button(
            "⬇️ Download routine (.txt)",
            data=st.session_state.last_plan_beta,
            file_name="skinsync_smartcoach.txt",
            mime="text/plain",
        )

        with st.expander("📌 View latest routine"):
            st.markdown(st.session_state.last_plan_beta)

    # ==========================================================
    # SAVE CONSULT
    # ==========================================================
    if save_clicked:
        if st.session_state.last_plan_beta is None:
            st.warning("No plan to save yet — send a message first.")
        else:
            payload = {
                "profile": st.session_state.profile,
                "conversation": messages_beta,
                "last_plan": st.session_state.last_plan_beta,
            }
            c.execute(
                "INSERT INTO consults (session_id, data, created_at) VALUES (?,?,?)",
                (
                    st.session_state.session_id,
                    json.dumps(payload),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            st.success("Consult saved ❤️")

    st.markdown("</div>", unsafe_allow_html=True)

    # Place back button at bottom (fixes double-click)
    render_back_to_home()

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
            if not name.strip():
                st.error("Please enter your name.")
            elif not is_valid_email(email):
                st.error("Please enter a valid email address.")
            else:
                c.execute(
                    "INSERT INTO bookings (name,email,city,date,time,reason,created_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (
                        name.strip(),
                        email.strip(),
                        city.strip(),
                        str(date),
                        str(time_val),
                        reason.strip() or "Skin consultation",
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

st.markdown("""
<style>

/* FORCE GLASS + LAVENDER FOR HOME PAGE CARDS */
.premium-card {
    background: rgba(255, 255, 255, 0.45) !important;
    border-radius: 22px !important;
    padding: 22px 26px !important;
    border: 1px solid rgba(255, 255, 255, 0.55) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    box-shadow: 0 18px 42px rgba(0,0,0,0.12) !important;
    transition: all 0.25s ease !important;
}

.premium-card:hover {
    transform: translateY(-5px) scale(1.01) !important;
    background: rgba(255, 240, 255, 0.55) !important;
    border-color: #e3c6ff !important;
    box-shadow: 0 26px 60px rgba(0,0,0,0.18) !important;
}

.premium-card * {
    color: #2f1a29 !important;
}

</style>
""", unsafe_allow_html=True)

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
elif page == "diary":
    render_diary()
elif page == "chat_v2":
    render_chat_v2()

st.markdown("---")
st.caption(
    "SkinSync — advice is for educational purposes only and not a substitute for in-person dermatology. "
    "If symptoms are severe, painful, or rapidly worsening, seek medical help."
)
