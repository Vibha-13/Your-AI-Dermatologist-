import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# ---------- Env & API Key ----------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")

try:
    import openai
    GPT_AVAILABLE = True
except Exception:
    GPT_AVAILABLE = False

# ---------- Config ----------
st.set_page_config(
    page_title="SkinSync — AI Dermatologist Suite",
    page_icon="💠",
    layout="wide",
)

# ---------- Styles ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, .stApp .css-1v3fvcr h1 {
        font-family: 'Playfair Display', serif;
    }
    .stApp {
        background: radial-gradient(circle at top left, #fdf7f3 0, #f7f0eb 30%, #f3ece7 60%, #efe6df 100%);
    }
    .chat-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 18px 22px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.06);
        max-width: 780px;
        margin: auto;
    }
    .derm-bubble {
        background: #ffffff;
        padding: 12px 16px;
        border-radius: 14px;
        margin-bottom: 8px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
    }
    .user-bubble {
        background: #f7e8e1;
        padding: 10px 14px;
        border-radius: 14px;
        margin-bottom: 8px;
        margin-left: 40px;
    }
    .brand-title {
        font-size: 38px;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: #3b2c29;
    }
    .pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(129, 97, 82, 0.08);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #7a5b4a;
    }
    .metric-card {
        background: rgba(255,255,255,0.85);
        border-radius: 16px;
        padding: 14px 18px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.05);
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

if "stage" not in st.session_state:
    st.session_state.stage = "greet"

if "patient" not in st.session_state:
    st.session_state.patient = {
        "concern": None,
        "duration": None,
        "skin_type": None,
        "routine": None,
        "allergies": None,
    }

if "use_api" not in st.session_state:
    st.session_state.use_api = False

# ---------- Helper Functions ----------
def append_message(role: str, text: str):
    st.session_state.messages.append({"role": role, "text": text})


def simple_nlu_extract_concern(text: str):
    text = (text or "").lower()
    concerns = []
    mapping = {
        "acne": ["acne", "pimple", "zit", "breakout", "pimples"],
        "pigmentation": ["pigment", "dark spot", "dark marks", "hyperpigmentation"],
        "dryness": ["dry", "flaky", "dehydr"],
        "oiliness": ["oily", "shine", "greasy"],
        "redness": ["red", "rosacea", "inflamed"],
        "sensitivity": ["sensitive", "irritat", "burning", "stinging"],
        "photoaging": ["wrinkle", "fine line", "aging", "sun spot"],
    }
    for k, phrases in mapping.items():
        for p in phrases:
            if p in text:
                concerns.append(k)
                break
    return concerns


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

# ---------- Load CSV Data ----------
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

# ---------- GPT Routine Generation ----------
def gpt_generate_routine(patient: dict) -> str | None:
    if not (GPT_AVAILABLE and (st.session_state.use_api or API_KEY)):
        return None

    prompt = f"""You are a dermatologist. Generate a personalized AM/PM skincare routine and 1-2 face packs for a user.
User profile:
- Skin type: {patient.get('skin_type','unknown')}
- Concerns: {patient.get('concern')}
- Allergies: {patient.get('allergies','none')}
- Current routine: {patient.get('routine','not specified')}

Output clearly with markdown headings:
- 🌞 Morning Routine
- 🌙 Night Routine
- 🧴 Recommended Face Packs

Give steps, ingredients and weekly frequency. Be gentle and safe."""

    try:
        key = getattr(st.session_state, "api_key", None) or API_KEY
        if not key:
            return None

        openai.api_key = key
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.65,
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ I couldn’t reach the AI engine right now: {e}"


# ---------- Rule-based fallback ----------
def generate_rule_based_plan(patient: dict) -> str:
    concerns = patient.get("concern") or []
    if isinstance(concerns, str):
        concerns = simple_nlu_extract_concern(concerns)
    skin_type = (patient.get("skin_type") or "").lower()

    lines: list[str] = []
    lines.append("Okaaay lovely — here’s a **safe starter plan** based on what you told me 💖\n")

    # Morning
    lines.append("### 🌞 Morning Routine")
    lines.append("- Gentle, low-foam cleanser")
    if skin_type == "dry":
        lines.append("- Hydrating toner or essence (optional)")
        lines.append("- Creamy moisturizer with ceramides + hyaluronic acid")
    elif skin_type == "oily":
        lines.append("- Lightweight gel moisturizer (non-comedogenic)")
    else:
        lines.append("- Lightweight daily moisturizer")

    if "pigmentation" in concerns:
        lines.append("- Vitamin C or niacinamide serum for spots")
    if "acne" in concerns:
        lines.append("- 2–3x/week: BHA (salicylic) or azelaic acid, very thin layer")
    lines.append("- Broad spectrum sunscreen SPF 30+ (every single morning)")

    # Night
    lines.append("\n### 🌙 Night Routine")
    lines.append("- Remove makeup / sunscreen (oil or balm cleanser if you wear makeup)")
    lines.append("- Gentle second cleanse")
    if "photoaging" in concerns:
        lines.append("- Low-strength retinoid 2–3x/week (skip if pregnant / planning)")
    elif "acne" in concerns:
        lines.append("- Azelaic or niacinamide serum on breakout-prone areas")
    lines.append("- Moisturizer to seal everything in")

    # Face pack ideas
    lines.append("\n### 🧴 Simple Face Pack Ideas (DIY)")
    if skin_type == "dry":
        lines.append("- **Honey + yogurt** 1–2x/week — 10 minutes, then rinse with lukewarm water.")
    if "acne" in concerns or skin_type == "oily":
        lines.append("- **Multani mitti + aloe gel** 1x/week — avoid if skin feels too tight.")
    if "pigmentation" in concerns:
        lines.append("- **Curd + a *pinch* of turmeric** 1x/week — always patch-test first.")

    lines.append("\n### 📝 General tips")
    lines.append("- Introduce only one new active at a time.")
    lines.append("- Patch test on jawline / behind ear for 2–3 days.")
    lines.append("- If pain, pus, fever or rapidly spreading rash → see an in-person dermatologist quickly.")

    # Products from CSV
    if not products_df.empty:
        lines.append("\n### 💄 Some starter-friendly product types from the library")
        def match_row(row):
            suits = [s.strip() for s in str(row.suitable_for).split("|")]
            if "all" in suits:
                return True
            if skin_type and skin_type in suits:
                return True
            for c in concerns:
                if c in suits:
                    return True
            return False
        matched = products_df[products_df.apply(match_row, axis=1)]
        for _, r in matched.head(6).iterrows():
            lines.append(f"- **{r['name']}** ({r.get('price_range','')}) — {r.get('notes','')}")
    else:
        lines.append("\n_(Add products to `data/products.csv` to show product suggestions here.)_")

    return "\n".join(lines)


def generate_recommendation():
    patient = st.session_state.patient

    if GPT_AVAILABLE and (st.session_state.use_api or API_KEY):
        ai_plan = gpt_generate_routine(patient)
        if ai_plan:
            append_message("assistant", ai_plan)
            st.session_state.stage = "recommend"
            return

    # Fallback
    rule_plan = generate_rule_based_plan(patient)
    append_message("assistant", rule_plan)
    st.session_state.stage = "recommend"


# ---------- Pages ----------

def render_home():
    col1, col2 = st.columns([2, 1.4])
    with col1:
        st.markdown('<div class="pill">AI · Dermatology · Skincare</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-title">SkinSync — AI Dermatologist Suite</div>', unsafe_allow_html=True)
        st.markdown(
            "A calm, clinical-but-cute space where users describe their skin, and your AI derm builds a safe, "
            "personalised routine — plus appointments and history tracking."
        )
        st.markdown("**Use this project in your resume as:**")
        st.markdown("- AI-powered dermatology assistant (LLM + rule engine)")
        st.markdown("- Full-stack Streamlit app with SQLite")
        st.markdown("- Multi-step conversational form + booking system")
    with col2:
        st.markdown("### Snapshot")
        with st.container():
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("**Tech stack**  \n`Python · Streamlit · SQLite · LLM (optional)`")
            st.markdown("**Key features**  \nChat triage · AM/PM routines · DIY packs · bookings")
            st.markdown("**Focus**  \nUser empathy · safety · clean UX")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("How a recruiter might see this project")
    st.markdown(
        """
- ✅ Demonstrates practical use of AI in healthcare / skincare.  
- ✅ Shows database skills (bookings + consult history).  
- ✅ Shows product thinking (flow from complaint → routine → booking).  
- ✅ Clean enough UI to look like an internal clinic tool or MVP startup app.  
        """
    )


def render_chat():
    st.markdown("### 🩺 AI Derm Chat")
    with st.container():
        st.markdown('<div class="chat-card">', unsafe_allow_html=True)

        # initial greeting
        if st.session_state.stage == "greet" and not st.session_state.messages:
            append_message(
                "assistant",
                "Welcome to SkinSync — your luxe derm friend. What's your main skin concern today? 🌿",
            )
            st.session_state.stage = "greet"

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
        if st.button("Send", key="chat_send"):
            if not user_input.strip():
                st.warning("Please type something 💗")
            else:
                st.session_state.messages.append({"role": "user", "text": user_input})
                stage = st.session_state.stage
                patient = st.session_state.patient

                if stage in ["greet", "concern"]:
                    concerns = simple_nlu_extract_concern(user_input)
                    if detect_severe_keywords(user_input):
                        append_message(
                            "assistant",
                            "I see some red-flag words (pain / pus / fever / spreading). "
                            "I really recommend an in-person doctor check. "
                            "If you want, you can still continue and I’ll give gentle-care tips.",
                        )
                        st.session_state.stage = "offer_escalation"
                    elif concerns:
                        patient["concern"] = concerns
                        append_message(
                            "assistant",
                            f"Got it — noted: {', '.join(concerns)}. "
                            "How long has this been going on? (days / weeks / months)",
                        )
                        st.session_state.stage = "duration"
                    else:
                        append_message(
                            "assistant",
                            "Could you name your main concern in one or two words? "
                            "(acne / pigmentation / dryness / oiliness / redness / sensitivity)",
                        )
                        st.session_state.stage = "concern"

                elif stage == "duration":
                    patient["duration"] = user_input
                    append_message(
                        "assistant",
                        "Thanks. How would you describe your skin type overall? "
                        "(dry / oily / combination / sensitive / not sure)",
                    )
                    st.session_state.stage = "skin_type"

                elif stage == "skin_type":
                    patient["skin_type"] = user_input.lower()
                    append_message(
                        "assistant",
                        "Nice. Briefly list your current routine "
                        "(e.g., cleanser + moisturizer + sunscreen / only face wash / etc.).",
                    )
                    st.session_state.stage = "routine"

                elif stage == "routine":
                    patient["routine"] = user_input
                    append_message(
                        "assistant",
                        "Any known allergies or ingredients that irritate you? "
                        "(fragrance, alcohol, retinol, etc.) — or type 'no'.",
                    )
                    st.session_state.stage = "allergies"

                elif stage == "allergies":
                    patient["allergies"] = user_input
                    append_message(
                        "assistant",
                        "Thank you, that’s enough for a safe starting plan. "
                        "Let me think for a second… 💭",
                    )
                    generate_recommendation()

                elif stage == "offer_escalation":
                    append_message(
                        "assistant",
                        "Noted. We’ll stay on the safer side with recommendations, "
                        "but please keep an eye on symptoms and visit a doctor if they worsen.",
                    )
                    st.session_state.stage = "skin_type"

                elif stage == "recommend":
                    append_message(
                        "assistant",
                        "If you’d like, you can now book a consultation slot in the *Appointments* page, "
                        "or just tweak the routine by telling me what you liked / didn’t like.",
                    )

        st.markdown("</div>", unsafe_allow_html=True)


def render_history():
    st.markdown("### 📋 Consult History (Admin View)")
    df = pd.read_sql_query(
        "SELECT id, session_id, data, created_at FROM consults ORDER BY id DESC LIMIT 50",
        conn,
    )
    if df.empty:
        st.info("No consults saved yet. After a chat, you can extend the app to save consults into this table.")
        return

    def preview(row):
        try:
            data = json.loads(row["data"])
            return f"{data.get('concern')} · {data.get('skin_type')}"
        except Exception:
            return row["data"][:80]

    df["summary"] = df.apply(preview, axis=1)
    st.dataframe(df[["id", "summary", "created_at"]], use_container_width=True)


def render_appointments():
    st.markdown("### 📅 Book an Appointment")

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


# ---------- Sidebar: API + Navigation + Upload ----------
with st.sidebar:
    st.markdown("#### Optional AI Engine Key")
    if GPT_AVAILABLE:
        key_input = st.text_input(
            "OpenAI-compatible API key (OpenAI / OpenRouter)",
            type="password",
            help="Leave blank to use rule-based recommendations only.",
        )
        if key_input:
            st.session_state.api_key = key_input
            st.session_state.use_api = True
    else:
        st.caption("LLM library not available — using rule-based engine only.")

    st.markdown("---")
    st.markdown("#### Navigation")
    page = st.radio(
        "Go to",
        ["🏠 Overview", "🩺 AI Derm Chat", "📋 Consult History", "📅 Appointments"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("#### Upload reference photo (optional)")
    uploaded = st.file_uploader(
        "Face photo (for future ML analysis)",
        type=["png", "jpg", "jpeg"],
    )
    if uploaded is not None:
        st.image(uploaded, caption="Uploaded image", use_column_width=True)
        st.caption(
            "Currently used only for display. "
            "In a future version, you can attach a CNN-based acne/redness severity model here."
        )

# ---------- Main Routing ----------
if page == "🏠 Overview":
    render_home()
elif page == "🩺 AI Derm Chat":
    render_chat()
elif page == "📋 Consult History":
    render_history()
elif page == "📅 Appointments":
    render_appointments()

st.markdown("---")
st.caption(
    "SkinSync — advice is for educational purposes only and not a substitute for in-person dermatology. "
    "If symptoms are severe, painful, or rapidly worsening, seek medical help."
)
