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

# ---------- GLOBAL STYLES (ROSY / LAVENDER AESTHETIC) ----------
st.markdown("""
<style>

.stApp {
    background: linear-gradient(180deg,#fffdfd 0%,#fff7fb 30%,#feeef7 65%,#fbe5f1 100%);
}

/* GLASS PREMIUM CARD */
.premium-card {
    background: rgba(255, 255, 255, 0.45);
    border-radius: 22px;
    padding: 20px 26px;
    border: 1px solid rgba(255, 255, 255, 0.55);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 18px 42px rgba(0, 0, 0, 0.10);
    transition: all 0.25s ease;
}

.premium-card:hover {
    transform: translateY(-5px) scale(1.01);
    background: rgba(255, 240, 255, 0.6);
    border-color: #e3c6ff;
    box-shadow: 0 26px 60px rgba(0, 0, 0, 0.16);
}

/* LAVENDER BUTTONS */
.stButton > button {
    background-color: #eadcff !important;
    color: #3a0030 !important;
    border-radius: 25px !important;
    border: 1px solid #d6c0f5 !important;
    font-weight: 600 !important;
    padding: 0.45rem 1.2rem !important;
    box-shadow: 0 8px 18px rgba(0,0,0,0.08);
}

.stButton > button:hover {
    background-color: #d8c1ff !important;
}

/* Chat bubbles */
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
You are SkinSync, a friendly but responsible AI dermatology assistant.

User profile:
- Name: {p.get('name') or 'User'}
- Age range: {p.get('age_bucket')}
- Skin type: {p.get('skin_type')}
- Main concern: {p.get('main_concern')}
- Sensitivity: {p.get('sensitivity')}
- Location (approx): {p.get('location') or 'not specified'}

Your goals:
- Ask gentle follow-up questions about the user's skin, lifestyle and routine.
- Give evidence-informed, simple skincare suggestions.
- Provide clear AM and PM routines, and suggest 1-2 DIY face packs with safe ingredients.
- Always be cautious: you are NOT a doctor, cannot diagnose, and must recommend in-person dermatology for severe / painful / rapidly worsening symptoms.
- Be warm, supportive, and concise. Use bullet points and headings where helpful.
- Assume user is in India/Asia unless specified; mention if actives may be irritating or need sunscreen.
- Never guarantee cures or medical outcomes.
- Try to structure your final answer like:

  1. Short summary of main issues
  2. 🌞 Morning routine (stepwise)
  3. 🌙 Night routine (stepwise)
  4. 🧴 1–2 DIY / home-care packs (with frequency)
  5. ⚠️ Caution / when to see a dermatologist
"""

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

    st.markdown('<div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">SkinSync</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;font-size:14px;margin-top:-4px;'>"
        "Your AI-powered skincare companion for gentle, science-based routines."
        "</p>",
        unsafe_allow_html=True,
    )

    prof = st.session_state.profile
    st.markdown(
        f"<p style='text-align:center;font-size:12px;margin-top:4px;opacity:0.8;'>"
        f"Signed in as <strong>{prof.get('name') or 'Guest'}</strong> · "
        f"{prof.get('skin_type')} skin · {prof.get('main_concern')}</p>",
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
    # Top nav
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 🩺 AI Derm Chat", unsafe_allow_html=True)

    # --------- CONSENT CHECK ---------
    if not st.session_state.consent:
        st.warning(
            "Please confirm in the left sidebar that you understand SkinSync is not a doctor "
            "before using the AI chat."
        )
        return

    # Small profile line
    prof = st.session_state.profile
    st.markdown(
        f"<p style='font-size:12px;opacity:0.8;'>"
        f"Profile: <strong>{prof.get('skin_type')}</strong> skin · "
        f"{prof.get('main_concern')} · sensitivity: {prof.get('sensitivity')}</p>",
        unsafe_allow_html=True,
    )

    # ---------- chat state keys ----------
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""

    if "pending_user_input" not in st.session_state:
        st.session_state.pending_user_input = ""

    with st.container():
        st.markdown('<div class="chat-card">', unsafe_allow_html=True)

        # ---------- First message ----------
        if not st.session_state.messages:
            append_message(
                "assistant",
                "Hi, I’m your SkinSync AI skincare assistant 🌿\n\n"
                "Tell me about your skin today — your main concern, how long it's been there, "
                "and what products you use. I’ll help you build a gentle AM/PM routine."
            )

        # ---------- Show conversation ----------
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

        # ---------- send callback ----------
        def handle_send():
            text = st.session_state.get("chat_input", "").strip()
            if not text:
                return
            st.session_state.pending_user_input = text
            st.session_state.chat_input = ""

        # ---------- Input + buttons ----------
        user_input = st.text_input("You:", key="chat_input")

        col1, col2 = st.columns([1, 1])
        with col1:
            st.button("Send", key="chat_send", on_click=handle_send)
        with col2:
            save_clicked = st.button("💾 Save consult", key="save_consult")

        # ==========================================================
        # PROCESS USER MESSAGE (MAIN LOGIC)
        # ==========================================================
        if st.session_state.pending_user_input:
            user_text = st.session_state.pending_user_input
            st.session_state.pending_user_input = ""

            # Trim extremely long messages
            if len(user_text) > 2000:
                user_text = user_text[:2000]
                st.info("Your message was quite long, so I trimmed it slightly to process it.")

            append_message("user", user_text)

            # ------------ Build messages (with trimming) ------------
            messages = build_chat_messages()

            # ------------ Severe keyword detection ------------
            if detect_severe_keywords(user_text):
                warn = (
                    "I noticed words like pain, pus, fever or rapid spreading. "
                    "This can be serious. I can give gentle skin-care tips, "
                    "but please consider seeing an in-person dermatologist soon. 🧑‍⚕️"
                )
                append_message("assistant", warn)
                messages.append({"role": "assistant", "content": warn})

            # ------------ API Call with spinner ------------
            with st.spinner("Thinking about your skin routine…"):
                reply_text, err = call_openrouter_chat(messages)

            if err:
                fallback = (
                    "I couldn't contact the AI engine right now, but based on what you said "
                    "I suggest keeping your routine simple: gentle cleanser, moisturizer and sunscreen. "
                    "Introduce actives slowly and always patch test first."
                )
                append_message("assistant", fallback)
                st.session_state.last_plan = fallback
                st.warning(err)
            else:
                append_message("assistant", reply_text)
                st.session_state.last_plan = reply_text

        # ---------- Download latest routine ----------
        if st.session_state.last_plan:
            st.download_button(
                "⬇️ Download routine (.txt)",
                data=st.session_state.last_plan,
                file_name="skinsync_routine.txt",
                mime="text/plain",
            )

            with st.expander("📌 View latest routine snapshot"):
                st.markdown(st.session_state.last_plan)

        # ---------- Save consult ----------
        if save_clicked:
            if st.session_state.last_plan is None:
                st.warning(
                    "No consult to save yet — send a message and get at least one AI reply first 🧾"
                )
            else:
                payload = {
                    "profile": st.session_state.profile,
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
    st.markdown("### 📋 Consult History")

    df = pd.read_sql_query(
        "SELECT id, session_id, data, created_at FROM consults ORDER BY id DESC LIMIT 100",
        conn,
    )
    if df.empty:
        st.info("No consults saved yet. After a chat, click 'Save consult' to store one.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    skin_types = []
    concerns = []

    for _, row in df.iterrows():
        try:
            data = json.loads(row["data"])
            prof = data.get("profile", {})
            skin_types.append(prof.get("skin_type", "Unknown"))
            concerns.append(prof.get("main_concern", "Unknown"))
        except Exception:
            skin_types.append("Unknown")
            concerns.append("Unknown")

    df["skin_type"] = skin_types
    df["main_concern"] = concerns

    unique_skin = ["(all)"] + sorted(set(skin_types))
    unique_concern = ["(all)"] + sorted(set(concerns))

    colf1, colf2 = st.columns(2)
    with colf1:
        filter_skin = st.selectbox("Filter by skin type", unique_skin)
    with colf2:
        filter_concern = st.selectbox("Filter by concern", unique_concern)

    filtered = df.copy()
    if filter_skin != "(all)":
        filtered = filtered[filtered["skin_type"] == filter_skin]
    if filter_concern != "(all)":
        filtered = filtered[filtered["main_concern"] == filter_concern]

    st.markdown("#### Saved consults")
    st.dataframe(
        filtered[["id", "skin_type", "main_concern", "created_at"]],
        use_container_width=True,
    )

    ids = filtered["id"].tolist()
    if ids:
        selected_id = st.selectbox("View full consult by ID", ids)
    else:
        selected_id = None

    if selected_id:
        row = df[df["id"] == selected_id].iloc[0]
        try:
            data = json.loads(row["data"])
            prof = data.get("profile", {})
            convo = data.get("conversation", [])
            last_plan = data.get("last_plan", "")

            first_user = next((m["text"] for m in convo if m["role"] == "user"), "")

            st.markdown("#### 🧑‍⚕️ Snapshot")
            st.write(f"**User:** {prof.get('name') or 'Unknown'}")
            st.write(f"**Skin type:** {prof.get('skin_type')} · **Concern:** {prof.get('main_concern')}")
            st.write(f"**Created at:** {row['created_at']}")

            st.markdown("#### 💬 First message")
            st.write(first_user or "_(empty)_")

            st.markdown("#### 🧴 Saved routine / plan")
            st.write(last_plan or "_No plan stored._")
        except Exception:
            st.write(row["data"][:500])

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

st.markdown("---")
st.caption(
    "SkinSync — advice is for educational purposes only and not a substitute for in-person dermatology. "
    "If symptoms are severe, painful, or rapidly worsening, seek medical help."
)
