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

# ---------- Env & API Key ----------
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ---------- Config ----------
st.set_page_config(
    page_title="SkinSync — AI Dermatologist Suite",
    page_icon="💠",
    layout="wide",
)

# ---------- Styles (soft blush-pink + bounce + glow) ----------
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
        font-size: 14px;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }

    .feature-grid {
        max-width: 900px;
        margin: 2rem auto 1rem auto;
    }

    .feature-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 22px;
        padding: 18px 20px;
        text-align: left;
        box-shadow: 0 14px 32px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.9);
        transition: all 0.18s ease-out;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    .feature-card:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
    }
    .feature-emoji {
        font-size: 32px;
        margin-bottom: 4px;
    }
    .feature-title {
        font-size: 17px;
        font-weight: 600;
        color: #3d2623;
        margin-bottom: 4px;
    }
    .feature-text {
        font-size: 13px;
        color: #7d615a;
    }

    .chat-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 18px 22px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.07);
        max-width: 780px;
        margin: 1.5rem auto;
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

    .pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(129, 97, 82, 0.10);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #7a5b4a;
    }

    .metric-card {
        background: rgba(255,255,255,0.96);
        border-radius: 16px;
        padding: 14px 18px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.06);
    }

    .back-button-container {
        max-width: 780px;
        margin: 0.5rem auto 0 auto;
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
    st.session_state.messages = []  # list of {"role": "user"/"assistant", "text": str}

if "page" not in st.session_state:
    st.session_state.page = "home"

if "last_plan" not in st.session_state:
    st.session_state.last_plan = None  # last assistant response for "Save consult"

# ---------- Basic helper functions ----------
def set_page(p: str):
    st.session_state.page = p

def append_message(role: str, text: str):
    st.session_state.messages.append({"role": role, "text": text})

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

# ---------- Simple CSV-backed product/facepack data (for LLM context if needed) ----------
PRODUCT_CSV = "data/products.csv"
FACEPACK_CSV = "data/facepacks.csv"

try:
    products_df = pd.read_csv(PRODUCT_CSV)
except Exception:
    products_df = pd.DataFrame(
        columns=["name", "suitable_for", "price_range", "tags", "link", "notes"]
    )

try:
    facepacks_df = pd.read_csv(FACEPACK_CSV)
except Exception:
    facepacks_df = pd.DataFrame(
        columns=["name", "suitable_for", "am_pm", "frequency", "ingredients", "notes"]
    )

# ---------- OpenRouter real-time chat ----------
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
    """
    messages: list of dicts with role and content, in OpenAI format
    returns assistant reply text or error message
    """
    if not OPENROUTER_API_KEY:
        return None, "No OpenRouter API key found. Add OPENROUTER_API_KEY in your .env."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional but nice to have:
        "HTTP-Referer": "https://skinsync.streamlit.app",
        "X-Title": "SkinSync AI Dermatologist",
    }
    payload = {
        "model": "openai/gpt-4o-mini",  # via OpenRouter
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

# ---------- Simple “ML-like” Acne/Redness Analysis ----------
def analyze_skin_image(image: Image.Image):
    # Convert to numpy
    img = image.convert("RGB")
    arr = np.array(img).astype("float32")

    # Compute redness index: R - (G+B)/2
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    redness = r - (g + b) / 2

    # Normalize
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

# ---------- Layout helpers ----------
def render_back_to_home():
    with st.container():
        st.markdown('<div class="back-button-container">', unsafe_allow_html=True)
        if st.button("← Back to Home"):
            set_page("home")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- Pages ----------
def render_home():
    st.markdown('<div class="hero-sub">AI · SKINCARE · DERMATOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">SkinSync</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#815952;font-size:14px;'>Your AI-powered skincare companion for gentle, science-based routines.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🩺  AI Derm Chat", key="feat_chat_btn"):
                set_page("chat")
            st.markdown(
                """
                <div class="feature-card">
                  <div class="feature-emoji">🩺</div>
                  <div class="feature-title">AI Dermatologist Chat</div>
                  <div class="feature-text">Describe your skin in your own words and get a personalised routine, like chatting with a friendly derm.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            if st.button("📷  Skin Analysis", key="feat_scan_btn"):
                set_page("scan")
            st.markdown(
                """
                <div class="feature-card">
                  <div class="feature-emoji">📷</div>
                  <div class="feature-title">Skin Image Analysis</div>
                  <div class="feature-text">Upload a face photo to estimate redness and get gentle-care tips for acne and irritation.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        col3, col4 = st.columns(2)

        with col3:
            if st.button("📅  Appointments", key="feat_appt_btn"):
                set_page("appointments")
            st.markdown(
                """
                <div class="feature-card">
                  <div class="feature-emoji">📅</div>
                  <div class="feature-title">Appointments</div>
                  <div class="feature-text">Book a consultation slot that can later be wired to a real clinic backend or admin.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col4:
            if st.button("📋  Consult History", key="feat_history_btn"):
                set_page("history")
            st.markdown(
                """
                <div class="feature-card">
                  <div class="feature-emoji">📋</div>
                  <div class="feature-title">Consult History</div>
                  <div class="feature-text">View saved consults, including your last generated routine and key notes.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("For your resume / portfolio")
    st.markdown(
        """
- Real-time AI dermatologist chat using OpenRouter (LLM-driven).  
- Full-stack Streamlit app with SQLite for bookings & consult history.  
- Skin image analysis module using basic computer vision heuristics (redness index).  
- Clearly separated modules: chat, analysis, bookings, history, with a modern home dashboard UI.  
        """
    )

def render_chat():
    render_back_to_home()
    st.markdown("### 🩺 AI Derm Chat")

    with st.container():
        st.markdown('<div class="chat-card">', unsafe_allow_html=True)

        # initial greeting
        if not st.session_state.messages:
            append_message(
                "assistant",
                "Hi, I’m your SkinSync AI derm assistant 🌿\n\n"
                "Tell me about your skin today — your main concern, how long it's been there, "
                "and what products you use. I’ll help you build a gentle AM/PM routine."
            )

        # show messages
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
                # user message
                append_message("user", user_input)

                # build messages for OpenRouter
                or_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.messages:
                    or_messages.append(
                        {"role": m["role"], "content": m["text"]}
                    )

                # Red flag (local) warning if needed
                if detect_severe_keywords(user_input):
                    warn = (
                        "I noticed words like pain, pus, fever or rapid spreading. "
                        "This can be serious. I can give gentle skin-care tips, "
                        "but please consider seeing an in-person dermatologist soon. 🧑‍⚕️"
                    )
                    append_message("assistant", warn)

                reply_text, err = call_openrouter_chat(or_messages)
                if err:
                    # fallback simple response
                    fallback = (
                        "I couldn't contact the AI engine just now, but based on what you said "
                        "I suggest keeping your routine simple: gentle cleanser, moisturizer and sunscreen. "
                        "Introduce actives slowly and patch test first."
                    )
                    append_message("assistant", fallback)
                    st.session_state.last_plan = fallback
                    st.error(err)
                else:
                    append_message("assistant", reply_text)
                    st.session_state.last_plan = reply_text  # so Save consult stores latest plan

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

def render_scan():
    render_back_to_home()
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
- This shows you understand: image preprocessing, colour channels, basic CV feature engineering.  
            """
        )

def render_history():
    render_back_to_home()
    st.markdown("### 📋 Consult History")

    df = pd.read_sql_query(
        "SELECT id, session_id, data, created_at FROM consults ORDER BY id DESC LIMIT 50",
        conn,
    )
    if df.empty:
        st.info("No consults saved yet. After a chat, click 'Save consult' to store one.")
        return

    def preview(row):
        try:
            data = json.loads(row["data"])
            convo = data.get("conversation", [])
            # grab first user message and maybe last_plan
            first_user = next((m["text"] for m in convo if m["role"] == "user"), "")
            last_plan = data.get("last_plan", "")
            return f"User: {first_user[:40]}... | Plan: {last_plan[:40]}..."
        except Exception:
            return row["data"][:80]

    df["summary"] = df.apply(preview, axis=1)
    st.dataframe(df[["id", "summary", "created_at"]], use_container_width=True)

def render_appointments():
    render_back_to_home()
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
