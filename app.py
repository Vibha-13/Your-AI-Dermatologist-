# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")  # should match .env

# Optional: GPT API
try:
    import openai
    GPT_AVAILABLE = True
except:
    GPT_AVAILABLE = False

# ---------- Config ----------
st.set_page_config(page_title="SkinSync — Luxe Derm Chat", page_icon="💠", layout="centered")

# ---------- Styles ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1,h2,h3,.stApp .css-1v3fvcr h1{font-family: 'Playfair Display', serif;}
.stApp { background: linear-gradient(180deg, #fbfaf9 0%, #f6f2ee 100%); }
.css-1dq8tca { border-radius: 18px; padding: 18px; }
.derm-bubble { background: white; padding: 12px 16px; border-radius: 12px; box-shadow: 0 6px 18px rgba(0,0,0,0.08); }
.user-bubble { background: #f3eae6; padding: 10px 14px; border-radius: 12px; }
.brand { color: #3b2e2b; }
.small-muted { color:#6b5b55; font-size:12px }
</style>
""", unsafe_allow_html=True)

# ---------- Database ----------
DB_PATH = "skinsync.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,email TEXT,city TEXT,date TEXT,time TEXT,reason TEXT,created_at TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS consults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,data TEXT,created_at TEXT
)''')
conn.commit()

# ---------- Session State ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.utcnow().isoformat()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stage" not in st.session_state:
    st.session_state.stage = "greet"
if "patient" not in st.session_state:
    st.session_state.patient = {"concern": None, "duration": None, "skin_type": None, "routine": None, "allergies": None}
if "use_api" not in st.session_state:
    st.session_state.use_api = False

# ---------- Helpers ----------
def append_message(role, text):
    st.session_state.messages.append({"role": role, "text": text})

def simple_nlu_extract_concern(text):
    text = (text or "").lower()
    concerns = []
    mapping = {
        "acne": ["acne","pimple","zit","spot"],
        "pigmentation": ["pigment","dark spot","hyperpigmentation"],
        "dryness": ["dry","flaky","dehydr"],
        "oiliness": ["oily","shine","greasy"],
        "redness": ["red","rosacea"],
        "sensitivity": ["sensitive","irritat"],
        "photoaging": ["wrinkle","fine line","aging","sun spot"]
    }
    for k,v in mapping.items():
        for s in v:
            if s in text:
                concerns.append(k)
                break
    return concerns

def detect_severe_keywords(text):
    severe = ["bleeding","pus","severe pain","fever","spreading","infection","open sore"]
    t = (text or "").lower()
    return any(s in t for s in severe)

# ---------- Load CSVs ----------
PRODUCT_CSV = "data/products.csv"
FACEPACK_CSV = "data/facepacks.csv"
try:
    products_df = pd.read_csv(PRODUCT_CSV)
except:
    products_df = pd.DataFrame(columns=["name","suitable_for","price_range","tags","link","notes"])
try:
    facepacks_df = pd.read_csv(FACEPACK_CSV)
except:
    facepacks_df = pd.DataFrame(columns=["name","suitable_for","am_pm","frequency","ingredients","notes"])

# ---------- GPT Routine Generation ----------
def gpt_generate_routine(patient):
    if not GPT_AVAILABLE or not st.session_state.use_api:
        return None
    prompt = f"""
You are a dermatologist. Generate a personalized AM/PM skincare routine and 1-2 face packs for a user.
User profile:
- Skin type: {patient.get('skin_type','unknown')}
- Concerns: {patient.get('concern')}
- Allergies: {patient.get('allergies','none')}
- Current routine: {patient.get('routine','not specified')}

Output clearly with:
- 🌞 Morning Routine
- 🌙 Night Routine
- 🧴 Recommended Face Packs
Include steps, ingredients, and frequency.
"""
    try:
        # Use environment key by default
        key = st.session_state.api_key if hasattr(st.session_state,'api_key') else os.getenv("OPENAI_API_KEY")
        openai.api_key = key
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating GPT routine: {e}"

# ---------- Generate Recommendation ----------
def generate_recommendation():
    patient = st.session_state.patient
    # GPT dynamic routine
    if st.session_state.use_api or os.getenv("OPENAI_API_KEY"):
        gpt_text = gpt_generate_routine(patient)
        if gpt_text:
            append_message("assistant", gpt_text)
            st.session_state.stage = "recommend"
            return
    # CSV fallback
    concerns = patient.get("concern") or []
    if isinstance(concerns,str): concerns = simple_nlu_extract_concern(concerns)
    skin_type = (patient.get("skin_type") or "").lower()
    allergies = (patient.get("allergies") or "").lower()
    lines = []
    lines.append("Okaaay lovely — here’s your **tailored skincare plan** 💖\n")

    # AM Routine
    lines.append("### 🌞 Morning Routine")
    am_routine = facepacks_df[(facepacks_df.am_pm=="AM") & (facepacks_df.suitable_for.str.contains(skin_type, case=False, na=False))]
    for _, r in am_routine.iterrows():
        lines.append(f"- {r['name']} ({r['ingredients']}) — {r['notes']}")

    # PM Routine
    lines.append("\n### 🌙 Night Routine")
    pm_routine = facepacks_df[(facepacks_df.am_pm=="PM") & (facepacks_df.suitable_for.str.contains(skin_type, case=False, na=False))]
    for _, r in pm_routine.iterrows():
        lines.append(f"- {r['name']} ({r['ingredients']}) — {r['notes']}")

    # Face Packs
    lines.append("\n### 🧴 Recommended Face Packs / Masks")
    fp = facepacks_df[(facepacks_df.suitable_for.str.contains(skin_type, case=False, na=False)) & (facepacks_df.am_pm=="Both")]
    for _, r in fp.iterrows():
        lines.append(f"- {r['name']} ({r['ingredients']}) — {r['notes']}")

    # Starter products
    lines.append("\n### 💄 Starter Products")
    if not products_df.empty:
        def match_row(row):
            suits = [s.strip() for s in str(row.suitable_for).split("|")]
            if "all" in suits: return True
            if skin_type and skin_type in suits: return True
            for c in concerns:
                if c in suits: return True
            return False
        matched = products_df[products_df.apply(match_row, axis=1)]
        for _, r in matched.head(6).iterrows():
            lines.append(f"- {r['name']} ({r.get('price_range','')}) — {r.get('notes','')}")
    else:
        lines.append("- No products loaded. Add data/products.csv")

    # Lifestyle tips
    lines.append("\n### 📝 Lifestyle Tips")
    lines.append("- Sleep well, hydrate, balanced diet")
    lines.append("- Patch test new actives; see in-person derm if worsening")
    append_message("assistant","\n".join(lines))
    st.session_state.stage = "recommend"

# ---------- Initial greeting ----------
if st.session_state.stage=="greet" and not st.session_state.messages:
    append_message("assistant","Welcome to SkinSync — your luxe derm friend. What's your main skin concern today? 🌿")
    st.session_state.stage="greet"

# ---------- Chat Display ----------
for m in st.session_state.messages:
    if m['role']=='assistant':
        st.markdown(f"<div class='derm-bubble'><strong>Derm</strong>: {m['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='user-bubble'><strong>You</strong>: {m['text']}</div>", unsafe_allow_html=True)

# ---------- GPT API Key input ----------
if GPT_AVAILABLE:
    key_input = st.sidebar.text_input("Optional: Enter OpenAI API Key for personalized routines", type="password")
    if key_input:
        st.session_state.api_key = key_input
        st.session_state.use_api = True

# ---------- User Input ----------
user_input = st.text_input("You:", key="input_box")
if st.button("Send"):
    if not user_input.strip():
        st.warning("Please type something 💗")
    else:
        st.session_state.messages.append({"role":"user","text":user_input})
        stage = st.session_state.stage
        patient = st.session_state.patient

        if stage in ["greet","concern"]:
            concerns = simple_nlu_extract_concern(user_input)
            if detect_severe_keywords(user_input):
                append_message("assistant","Red-flag symptoms detected. Consider seeing a doctor. Book appointment?")
                st.session_state.stage="offer_escalation"
            elif concerns:
                patient['concern']=concerns
                append_message("assistant",f"Got it — noted: {', '.join(concerns)}. When did this start?")
                st.session_state.stage="duration"
            else:
                append_message("assistant","Could you specify your main concern (acne/pigmentation/dryness/oiliness/redness)?")
                st.session_state.stage="concern"

        elif stage=="duration":
            patient['duration']=user_input
            append_message("assistant","Thanks — what's your skin type? (dry/oily/combination/sensitive)")
            st.session_state.stage="skin_type"

        elif stage=="skin_type":
            patient['skin_type']=user_input.lower()
            append_message("assistant","Nice — tell me your current routine briefly.")
            st.session_state.stage="routine"

        elif stage=="routine":
            patient['routine']=user_input
            append_message("assistant","Any allergies or ingredients you avoid? (or type 'no')")
            st.session_state.stage="allergies"

        elif stage=="allergies":
            patient['allergies']=user_input
            append_message("assistant","Great — crafting your tailored routine 💖")
            generate_recommendation()

        elif stage=="offer_escalation":
            if "yes" in user_input.lower():
                append_message("assistant","Please fill the booking form on the right.")
                st.session_state.stage="booking"
            else:
                append_message("assistant","Alright — what's your skin type?")
                st.session_state.stage="skin_type"

        elif stage=="recommend":
            append_message("assistant","Would you like to book an appointment or save this consult? (book/save/none)")
            st.session_state.stage="post_recommend"

        elif stage=="post_recommend":
            if "book" in user_input.lower():
                append_message("assistant","Please fill the booking form in the sidebar.")
                st.session_state.stage="booking"
            elif "save" in user_input.lower():
                data = json.dumps(patient)
                c.execute('INSERT INTO consults (session_id,data,created_at) VALUES (?,?,?)',
                          (st.session_state.session_id,data,datetime.utcnow().isoformat()))
                conn.commit()
                append_message("assistant","Saved your consult.")
                st.session_state.stage="done"
            else:
                append_message("assistant","Type 'restart' anytime to begin a new consult.")
                st.session_state.stage="done"
        st.experimental_rerun()

# ---------- Sidebar ----------
st.sidebar.header("Upload & Book")
uploaded = st.sidebar.file_uploader("Upload face photo (optional)", type=["png","jpg","jpeg"])
if uploaded:
    st.sidebar.image(uploaded, caption="Uploaded image", use_column_width=True)

st.sidebar.markdown("### Book an Appointment")
with st.sidebar.form("booking_form"):
    name = st.text_input("Full name")
    email = st.text_input("Email")
    city = st.text_input("City")
    date = st.date_input("Preferred date", min_value=datetime.today())
    time = st.time_input("Preferred time")
    reason = st.text_area("Reason", value=str(patient.get("concern") or "Skin consultation"))
    submitted = st.form_submit_button("Book appointment")
    if submitted:
        c.execute('INSERT INTO bookings (name,email,city,date,time,reason,created_at) VALUES (?,?,?,?,?,?,?)',
                  (name or "Anonymous", email, city, str(date), str(time), reason, datetime.utcnow().isoformat()))
        conn.commit()
        st.success("Appointment requested — provisional booking saved.")
        append_message("assistant",f"Booked provisional slot for {name or 'Anonymous'} on {date} at {time} in {city}.")
        st.experimental_rerun()

st.caption("SkinSync — advice is non-diagnostic. Seek licensed professional if severe symptoms.")
