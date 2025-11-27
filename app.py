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

# ----------- SAFE NON-BLOCKING BEAUTIFUL SPLASH -----------
if "show_splash" not in st.session_state:
    st.session_state.show_splash = True

if st.session_state.show_splash:
    st.markdown("""
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

            /* ⭐ Smooth fade-out: lasts 1.2s, starts after 1.8s */
            animation: fadeOut 1.2s ease-out 1.8s forwards;
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
    """, unsafe_allow_html=True)

    # Match the CSS (1.8s delay + 1.2s fade = ~3s total)
    import time
    time.sleep(3)
    st.session_state.show_splash = False

# ========== BASIC CONFIG ==========
st.set_page_config(
    page_title="SkinSync — AI Dermatologist",
    page_icon="💠",
    layout="wide",
)

# ---------- Global Light Theme / Text Fix ----------
st.markdown("""
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
""", unsafe_allow_html=True)

# ---------- GLOBAL STYLES (ROSY AESTHETIC) ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    .stApp {
        background: linear-gradient(
            180deg,
            #fffdfd 0%,
            #fff7fb 30%,
            #feeef7 65%,
            #fbe5f1 100%
        );
    }

    /* Page fade-in */
    .page-container {
        animation: fadeInUp 0.3s ease-out;
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Hero */
    .hero-title {
        font-size: 34px;
        font-weight: 700;
        letter-spacing: 0.07em;
        color: #251320;
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
            rgba(255,255,255,0.98),
            rgba(255,246,252,0.99)
        );
        border-radius: 22px;
        padding: 18px 22px;
        border: 1px solid rgba(255,255,255,0.9);
        box-shadow: 0 18px 40px rgba(0,0,0,0.08);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
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
            rgba(255,255,255,1),
            rgba(255,242,249,1)
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

    /* Chat card & bubbles */
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
        padding: 12px 16px;
        border-radius: 14px;
        margin-bottom: 8px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        color: #251320 !important;
    }
    .user-bubble {
        background: #fbe3f4;
        padding: 12px 16px;
        border-radius: 14px;
        margin-bottom: 8px;
        margin-left: 40px;
        color: #251320 !important;
    }

    /* Back button */
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

    /* Inputs & buttons */
    input, textarea, .stTextInput, .stTextArea {
        color: #251320 !important;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > textarea {
        background: #ffffff !important;
        color: #251320 !important;
        border-radius: 14px !important;
        border: 1px solid #edd3e4 !important;
    }
    ::placeholder {
        color: #a27d98 !important;
        opacity: 1 !important;
    }
    .stTextInput label, .stTextArea label {
        color: #5c3b52 !important;
    }

    .stButton > button {
        background: #251320 !important;
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

# ========== DB SETUP ==========
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
if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "",
        "age_bucket": "18–24",
        "skin_type": "Combination",
        "main_concern": "Acne / Breakouts",
        "sensitivity": "Normal",
        "location": "",
    }

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

# ========== SIDEBAR: SKIN PROFILE (Tier-1) ==========
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
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 🩺 AI Derm Chat", unsafe_allow_html=True)

    prof = st.session_state.profile
    st.markdown(
        f"<p style='font-size:12px;opacity:0.8;'>"
        f"Profile: <strong>{prof.get('skin_type')}</strong> skin · "
        f"{prof.get('main_concern')} · sensitivity: {prof.get('sensitivity')}</p>",
        unsafe_allow_html=True,
    )

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

                messages = [{"role": "system", "content": build_system_prompt()}]
                for m in st.session_state.messages:
                    messages.append({"role": m["role"], "content": m["text"]})

                if detect_severe_keywords(user_input):
                    warn = (
                        "I noticed words like pain, pus, fever or rapid spreading. "
                        "This can be serious. I can give gentle skin-care tips, "
                        "but please consider seeing an in-person dermatologist soon. 🧑‍⚕️"
                    )
                    append_message("assistant", warn)
                    messages.append({"role": "assistant", "content": warn})

                reply_text, err = call_openrouter_chat(messages)
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

        # Tier-1: Download routine button
        if st.session_state.last_plan:
            st.download_button(
                "⬇️ Download routine (.txt)",
                data=st.session_state.last_plan,
                file_name="skinsync_routine.txt",
                mime="text/plain",
            )

            # Tier-2: Routine snapshot section
            with st.expander("📌 View latest routine snapshot"):
                st.markdown(st.session_state.last_plan)

        if save_clicked:
            if st.session_state.last_plan is None:
                st.warning("No consult to save yet — send a message and get at least one AI reply first 🧾")
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
        "SELECT id, session_id, data, created_at FROM consults ORDER BY id DESC LIMIT 100",
        conn,
    )
    if df.empty:
        st.info("No consults saved yet. After a chat, click 'Save consult' to store one.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---- Tier-2: derive skin_type & concern from stored profile for filtering ----
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
    selected_id = st.selectbox("View full consult by ID", ids)
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
