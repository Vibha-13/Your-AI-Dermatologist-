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

/* CARD BASE (GLASS) */
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

.premium-card:hover {
    transform: translateY(-5px) scale(1.01);
    background: rgba(255, 240, 255, 0.6);
    border-color: #e3c6ff;
    box-shadow: 0 28px 65px rgba(255,182,222,0.35);
}

/* BUTTONS */
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

/* CHAT BUBBLES */
.derm-bubble {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.user-bubble {
    background: rgba(248,220,250,0.75);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 12px 16px;
    margin-left: 40px;
    margin-bottom: 8px;
}

/* GLASS BOXES */
.glass-box {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(16px);
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.08);
    border: 1px solid rgba(255,255,255,0.6);
    margin-top: 6px;
}
.warn-box {
    background: rgba(255,220,220,0.55);
    border-left: 4px solid #d40000;
    border-radius: 14px;
    padding: 12px 16px;
    margin-top: 10px;
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

if "messages_beta" not in st.session_state:
    st.session_state.messages_beta = []

if "last_plan_beta" not in st.session_state:
    st.session_state.last_plan_beta = None

if "send_guard_beta" not in st.session_state:
    st.session_state.send_guard_beta = False

# allergy list
if "allergies" not in st.session_state:
    st.session_state.allergies = []

# ==========================================
# PRODUCT DATABASE (starter version)
# ==========================================
PRODUCTS = [
    # CLEANSERS
    {
        "name": "CeraVe Foaming Cleanser",
        "brand": "CeraVe",
        "category": "cleanser",
        "skin_types": ["oily", "combination"],
        "concerns": ["acne", "oiliness"],
        "ingredients": ["ceramides", "niacinamide"],
        "strength": "gentle",
        "irritation": "low",
        "comodogenic": 0,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "mid",
        "origin": "us",
    },
    {
        "name": "Cetaphil Gentle Skin Cleanser",
        "brand": "Cetaphil",
        "category": "cleanser",
        "skin_types": ["sensitive", "normal", "dry"],
        "concerns": ["redness", "irritation"],
        "ingredients": ["glycerin"],
        "strength": "very_gentle",
        "irritation": "very_low",
        "comodogenic": 1,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "mid",
        "origin": "us",
    },
    {
        "name": "Simple Refreshing Facial Wash",
        "brand": "Simple",
        "category": "cleanser",
        "skin_types": ["all"],
        "concerns": ["sensitivity"],
        "ingredients": ["glycerin"],
        "strength": "very_gentle",
        "irritation": "very_low",
        "comodogenic": 0,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "budget",
        "origin": "global",
    },
    {
        "name": "Minimalist 2% Salicylic Acid Cleanser",
        "brand": "Minimalist",
        "category": "cleanser",
        "skin_types": ["oily", "acne", "combination"],
        "concerns": ["acne", "clogged_pores"],
        "ingredients": ["salicylic_acid"],
        "strength": "medium",
        "irritation": "medium",
        "comodogenic": 0,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "budget",
        "origin": "indian",
    },

    # MOISTURIZERS
    {
        "name": "Neutrogena Hydro Boost Water Gel",
        "brand": "Neutrogena",
        "category": "moisturizer",
        "skin_types": ["oily", "combination"],
        "concerns": ["dehydration"],
        "ingredients": ["hyaluronic_acid"],
        "strength": "hydrating",
        "irritation": "low",
        "comodogenic": 1,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "mid",
        "origin": "us",
    },
    {
        "name": "CeraVe Moisturising Lotion",
        "brand": "CeraVe",
        "category": "moisturizer",
        "skin_types": ["dry", "normal", "sensitive"],
        "concerns": ["dryness", "barrier_damage"],
        "ingredients": ["ceramides", "hyaluronic_acid"],
        "strength": "hydrating",
        "irritation": "very_low",
        "comodogenic": 1,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "mid",
        "origin": "us",
    },
    {
        "name": "Minimalist Ceramide 0.3% Moisturiser",
        "brand": "Minimalist",
        "category": "moisturizer",
        "skin_types": ["all"],
        "concerns": ["barrier_damage", "dryness"],
        "ingredients": ["ceramides"],
        "strength": "barrier",
        "irritation": "very_low",
        "comodogenic": 1,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "budget",
        "origin": "indian",
    },

    # SERUMS
    {
        "name": "The Ordinary Niacinamide 10% + Zinc",
        "brand": "The Ordinary",
        "category": "serum",
        "skin_types": ["all"],
        "concerns": ["acne", "pigmentation", "oiliness"],
        "ingredients": ["niacinamide", "zinc"],
        "strength": "gentle",
        "irritation": "low",
        "comodogenic": 0,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "budget",
        "origin": "global",
    },
    {
        "name": "Minimalist 10% Niacinamide Serum",
        "brand": "Minimalist",
        "category": "serum",
        "skin_types": ["all"],
        "concerns": ["acne", "pigmentation", "oiliness"],
        "ingredients": ["niacinamide"],
        "strength": "gentle",
        "irritation": "low",
        "comodogenic": 0,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "budget",
        "origin": "indian",
    },
    {
        "name": "Minimalist 2% Salicylic Acid Serum",
        "brand": "Minimalist",
        "category": "serum",
        "skin_types": ["oily", "acne"],
        "concerns": ["acne", "clogged_pores"],
        "ingredients": ["salicylic_acid"],
        "strength": "medium",
        "irritation": "medium",
        "comodogenic": 0,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "budget",
        "origin": "indian",
    },
    {
        "name": "The Ordinary Azelaic Acid 10%",
        "brand": "The Ordinary",
        "category": "serum",
        "skin_types": ["all"],
        "concerns": ["acne", "pigmentation", "redness"],
        "ingredients": ["azelaic_acid"],
        "strength": "medium",
        "irritation": "medium",
        "comodogenic": 0,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "mid",
        "origin": "global",
    },
    {
        "name": "Beauty of Joseon Glow Serum",
        "brand": "Beauty of Joseon",
        "category": "serum",
        "skin_types": ["combination", "normal", "dry"],
        "concerns": ["dullness", "hydration"],
        "ingredients": ["niacinamide", "propolis"],
        "strength": "gentle",
        "irritation": "low",
        "comodogenic": 1,
        "fa_safe": False,
        "adult_only": False,
        "price_range": "mid",
        "origin": "korean",
    },

    # RETINOL (adult only)
    {
        "name": "Minimalist 0.3% Retinol",
        "brand": "Minimalist",
        "category": "serum",
        "skin_types": ["normal", "dry", "combination"],
        "concerns": ["anti_aging", "texture"],
        "ingredients": ["retinol"],
        "strength": "strong",
        "irritation": "high",
        "comodogenic": 1,
        "fa_safe": False,
        "adult_only": True,
        "price_range": "budget",
        "origin": "indian",
    },

    # SUNSCREENS
    {
        "name": "Minimalist SPF 50 Multi-Vitamin",
        "brand": "Minimalist",
        "category": "sunscreen",
        "skin_types": ["all"],
        "concerns": ["sun_protection"],
        "ingredients": ["uv_filters"],
        "strength": "strong",
        "irritation": "low",
        "comodogenic": 1,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "budget",
        "origin": "indian",
    },
    {
        "name": "La Roche-Posay Anthelios SPF 50",
        "brand": "La Roche-Posay",
        "category": "sunscreen",
        "skin_types": ["all"],
        "concerns": ["sun_protection"],
        "ingredients": ["uv_filters"],
        "strength": "strong",
        "irritation": "low",
        "comodogenic": 1,
        "fa_safe": True,
        "adult_only": False,
        "price_range": "premium",
        "origin": "us",
    },
]

KNOWN_ALLERGENS = [
    "fragrance",
    "essential_oils",
    "tea_tree",
    "snail",
    "snail_mucin",
    "aloe",
    "vitamin_c",
    "niacinamide",
    "retinol",
    "bha",
    "aha",
    "salicylic_acid",
    "azelaic_acid",
]

# ==========================================
# SIDEBAR — SKIN PROFILE + ALLERGIES
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
    st.markdown("🧪 **Allergies / ingredient issues**")
    allergy_text = st.text_input(
        "Known allergies (comma separated)",
        value=", ".join(st.session_state.allergies) if st.session_state.allergies else "",
        help="Example: fragrance, niacinamide, vitamin C, aloe, snail"
    )
    if allergy_text.strip():
        parsed = [a.strip().lower().replace(" ", "_") for a in allergy_text.split(",") if a.strip()]
        st.session_state.allergies = list(sorted(set(parsed)))

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

def detect_intent(text: str) -> str:
    t = text.lower()
    greet_words = ["hi", "hello", "hey", "yo", "sup", "good morning", "good night"]
    small_talk = ["thank", "thanks", "ok", "okay", "great", "awesome", "cool"]

    if any(w in t for w in greet_words) and len(t) < 40:
        return "greeting"
    if any(w in t for w in small_talk) and len(t) < 80:
        return "small_talk"
    return "routine_request"

def extract_allergies_from_text(text: str):
    t = text.lower()
    found = []
    for a in KNOWN_ALLERGENS:
        pretty = a.replace("_", " ")
        if a in t or pretty in t:
            found.append(a)
    return list(sorted(set(found)))

def is_user_adult(profile, message_history) -> bool:
    # Simple heuristic
    age = profile.get("age_bucket", "18–24")
    if age in ["25–30", "30–40", "40+"]:
        return True
    # Look into chat messages
    for m in message_history:
        if m["role"] != "user":
            continue
        t = m["text"].lower()
        if "wrinkles" in t or "fine lines" in t or "anti-aging" in t or "anti ageing" in t:
            return True
        if "i am 2" in t or "i'm 2" in t:  # very rough heuristic
            return True
    return False

def filter_products(profile, allergies, main_intent_text, history):
    skin_type = profile.get("skin_type", "Combination").lower()
    concern = profile.get("main_concern", "").lower()
    t = (main_intent_text or "").lower()
    is_adult_flag = is_user_adult(profile, history)

    wants_acne = "acne" in t or "pimple" in t or "breakout" in t or "acne" in concern
    wants_pigment = "pigment" in t or "dark spot" in t or "mark" in t
    wants_dry = "dry" in t or "flaky" in t or "tight" in t or "dryness" in concern
    wants_oily = "oily" in t or "oil" in t or "shine" in t or "oiliness" in concern
    wants_anti_age = "anti aging" in t or "anti-age" in t or "fine lines" in t or "wrinkle" in t or "aging" in concern.lower()

    shortlist = []

    for p in PRODUCTS:
        # age filter
        if p.get("adult_only", False) and not is_adult_flag:
            continue
        # skin type heuristic
        stypes = [s.lower() for s in p["skin_types"]]
        if "all" not in stypes:
            if skin_type not in [s.replace(" ", "_") for s in stypes]:
                # slightly looser allowance: oily vs combination
                if not (skin_type == "oily" and "combination" in stypes) and not (skin_type == "combination" and "oily" in stypes):
                    continue
        # concern matching
        ctags = [c.lower() for c in p["concerns"]]
        if wants_acne and not any(c in ctags for c in ["acne", "clogged_pores", "oiliness"]):
            # skip if we specifically want acne products
            continue
        if wants_pigment and "pigmentation" not in ctags and "dark_spots" not in ctags:
            # not strict; we might still keep some hydrating products
            pass
        # allergy filter
        ingr = [i.lower() for i in p.get("ingredients", [])]
        skip = False
        for allergy in allergies:
            if allergy in ingr:
                skip = True
                break
            pretty = allergy.replace("_", " ")
            if pretty in ingr:
                skip = True
                break
        if skip:
            continue

        shortlist.append(p)

    # fallback: if filtered too harshly
    if len(shortlist) < 3:
        shortlist = PRODUCTS

    # keep unique by name
    seen = set()
    final = []
    for p in shortlist:
        if p["name"] not in seen:
            seen.add(p["name"])
            final.append(p)

    # cap to ~12 items so prompt doesn't explode
    return final[:12]

def format_products_for_prompt(products):
    # compact JSON-ish string, but as plain text
    lines = []
    for p in products:
        line = {
            "name": p["name"],
            "category": p["category"],
            "skin_types": p["skin_types"],
            "concerns": p["concerns"],
            "irritation": p["irritation"],
            "adult_only": p["adult_only"],
            "price_range": p["price_range"],
            "origin": p["origin"],
        }
        lines.append(line)
    return json.dumps(lines, ensure_ascii=False)

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
# HOME PAGE
# ==========================================
def render_home():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    st.markdown('<div class="hero-sub" style="text-align:center;color:#8a6a7f;font-size:12px;letter-spacing:0.22em;text-transform:uppercase;">AI · SKINCARE · DERMATOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title" style="font-size:34px;font-weight:700;letter-spacing:0.07em;color:#251320;text-align:center;margin-bottom:0.1rem;">SkinSync</div>', unsafe_allow_html=True)
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

    st.markdown('<div class="feature-grid" style="max-width:900px;margin:auto;">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
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
                  AI-powered personalised AM/PM routines & product picks.
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
                <div class="card-header-line" style="display:flex;align-items:center;gap:8px;">
                  <span class="card-emoji" style="font-size:20px;">📷</span>
                  <span style="font-size:15px;font-weight:600;">Skin Analysis</span>
                </div>
                <div class="card-subtitle" style="font-size:13px;color:#8b6c80;">
                  Upload a face photo to estimate redness gently.
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
                <div class="card-header-line" style="display:flex;align-items:center;gap:8px;">
                  <span class="card-emoji" style="font-size:20px;">📅</span>
                  <span style="font-size:15px;font-weight:600;">Appointments</span>
                </div>
                <div class="card-subtitle" style="font-size:13px;color:#8b6c80;">
                  Save consultation slots that can link to a clinic later.
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
                <div class="card-header-line" style="display:flex;align-items:center;gap:8px;">
                  <span class="card-emoji" style="font-size:20px;">📋</span>
                  <span style="font-size:15px;font-weight:600;">Consult History</span>
                </div>
                <div class="card-subtitle" style="font-size:13px;color:#8b6c80;">
                  View all saved chats & routines.
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
def render_chat():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 🧠 Smart Skin Coach (Beta)", unsafe_allow_html=True)

    if not st.session_state.consent:
        st.warning("Please confirm in the sidebar that you understand SkinSync is not a doctor.")
        return

    prof = st.session_state.profile
    st.markdown(
        f"<p style='font-size:12px;opacity:0.8;'>Profile: <strong>{prof['skin_type']}</strong> skin · "
        f"{prof['main_concern']} · sensitivity: {prof['sensitivity']}</p>",
        unsafe_allow_html=True,
    )

    # Chat UI
    with st.container():
        # First greeting
        if len(st.session_state.messages_beta) == 0:
            st.session_state.messages_beta.append({
                "role": "assistant",
                "text": (
                    "Hi, I'm your Smart Skin Coach 🌿\n\n"
                    "Tell me what’s bothering your skin right now — acne, dryness, redness, pigmentation, anything."
                )
            })

        # Show history
        for m in st.session_state.messages_beta:
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

        # Input
        st.text_input("You:", key="chat_input_beta")

        def handle_send():
            if st.session_state.send_guard_beta:
                return
            st.session_state.send_guard_beta = True

            txt = st.session_state.get("chat_input_beta", "").strip()
            if not txt:
                st.session_state.send_guard_beta = False
                return

            # user message
            st.session_state.messages_beta.append({"role": "user", "text": txt})
            st.session_state.chat_input_beta = ""

            # detect allergies from text
            new_allergies = extract_allergies_from_text(txt)
            if new_allergies:
                merged = set(st.session_state.allergies) | set(new_allergies)
                st.session_state.allergies = list(sorted(merged))

            # intent
            intent = detect_intent(txt)

            if intent == "greeting":
                st.session_state.messages_beta.append({
                    "role": "assistant",
                    "text": "Hi! 💗 Tell me your main skin concern — acne, dryness, redness, pigmentation, anything."
                })
                st.session_state.send_guard_beta = False
                return

            if intent == "small_talk":
                st.session_state.messages_beta.append({
                    "role": "assistant",
                    "text": "Got it 💫 Whenever you're ready, describe your skin and what you want to improve."
                })
                st.session_state.send_guard_beta = False
                return

            # severe
            if detect_severe_keywords(txt):
                st.session_state.messages_beta.append({
                    "role": "assistant",
                    "text": (
                        "I noticed words like bleeding, pus, fever or severe pain. "
                        "This can be serious — please see an in-person dermatologist soon. 🧑‍⚕️"
                    )
                })

            # product filtering
            allowed = filter_products(st.session_state.profile, st.session_state.allergies, txt, st.session_state.messages_beta)
            products_json = format_products_for_prompt(allowed)

            system_prompt = """
You are Smart Skin Coach, an AI skincare assistant.
You must use ONLY the products provided in the 'allowed_products' JSON below.
Pick the best matching products and build a gentle routine.

You respond ONLY in valid JSON. No markdown, no explanations, no extra keys.

JSON FORMAT (you may omit keys that are not relevant):
{
  "summary": "",
  "am_routine": [
    {"step": "Cleanser", "product": "name from allowed_products"},
    {"step": "Serum", "product": "name ..."},
    {"step": "Moisturizer", "product": "name ..."},
    {"step": "Sunscreen", "product": "name ..."}
  ],
  "pm_routine": [
    {"step": "Cleanser", "product": "..."},
    {"step": "Treatment", "product": "..."},
    {"step": "Moisturizer", "product": "..."}
  ],
  "diy": [
    "Short DIY/home care tip 1",
    "Short DIY/home care tip 2"
  ],
  "caution": "Short safety note if needed"
}

Rules:
- Be gentle and teen-safe by default.
- Use lower-strength actives for younger or sensitive users.
- Avoid strong retinoids and harsh exfoliation unless user clearly wants anti-aging or is adult.
- Never mention brand marketing, hype or trends, just safe choices.
"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"allowed_products = {products_json}"},
                {"role": "user", "content": txt},
            ]

            with st.spinner("Preparing a gentle routine for your skin…"):
                reply, err = call_openrouter_chat(messages)

            if err:
                fallback = {
                    "summary": "Basic routine due to connection issue.",
                    "am_routine": [
                        {"step": "Cleanser", "product": "Gentle cleanser"},
                        {"step": "Moisturizer", "product": "Lightweight moisturizer"},
                        {"step": "Sunscreen", "product": "Broad spectrum SPF 30+"},
                    ],
                    "pm_routine": [
                        {"step": "Cleanser", "product": "Gentle cleanser"},
                        {"step": "Moisturizer", "product": "Barrier-repair moisturizer"},
                    ],
                    "diy": ["Patch test new products", "Avoid picking or squeezing acne"],
                    "caution": "If symptoms worsen or are painful, see a dermatologist.",
                }
                st.session_state.last_plan_beta = fallback
                st.session_state.messages_beta.append({
                    "role": "assistant",
                    "text": "I had trouble reaching the AI service, so I generated a simple safe routine for you."
                })
                st.session_state.send_guard_beta = False
                return

            try:
                parsed = json.loads(reply)
            except Exception:
                st.session_state.last_plan_beta = {"raw_text": reply}
                st.session_state.messages_beta.append({
                    "role": "assistant",
                    "text": "I couldn't format a full routine cleanly, but here’s some guidance below."
                })
                st.session_state.send_guard_beta = False
                return

            st.session_state.last_plan_beta = parsed

            # Build cute bubble text
            bubble_parts = []
            if parsed.get("summary"):
                bubble_parts.append(f"💗 **Summary:**\n{parsed['summary']}\n")

            if parsed.get("am_routine"):
                bubble_parts.append("🌞 **AM Routine:**")
                for step in parsed["am_routine"]:
                    s = step.get("step", "Step")
                    prod = step.get("product", "")
                    bubble_parts.append(f"• {s}: {prod}")
                bubble_parts.append("")

            if parsed.get("pm_routine"):
                bubble_parts.append("🌙 **PM Routine:**")
                for step in parsed["pm_routine"]:
                    s = step.get("step", "Step")
                    prod = step.get("product", "")
                    bubble_parts.append(f"• {s}: {prod}")
                bubble_parts.append("")

            if parsed.get("diy"):
                bubble_parts.append("🧴 **DIY Care:**")
                for tip in parsed["diy"]:
                    bubble_parts.append(f"• {tip}")
                bubble_parts.append("")

            if parsed.get("caution"):
                bubble_parts.append(f"⚠️ {parsed['caution']}")

            chat_reply = "\n".join(bubble_parts) if bubble_parts else "Here’s a gentle routine based on what you shared. 💗"

            st.session_state.messages_beta.append({
                "role": "assistant",
                "text": chat_reply
            })

            st.session_state.send_guard_beta = False

        st.button("Send", on_click=handle_send)

        save_clicked = st.button("💾 Save consult")

        # show routine as cards
        plan = st.session_state.last_plan_beta
        if plan:
            if plan.get("summary"):
                st.markdown(
                    f"<div class='glass-box'><h4>💗 Summary</h4><p>{plan['summary']}</p></div>",
                    unsafe_allow_html=True
                )

            if plan.get("am_routine"):
                items = "".join([
                    f"<li><strong>{step.get('step','Step')}:</strong> {step.get('product','')}</li>"
                    for step in plan["am_routine"]
                ])
                st.markdown(
                    f"<div class='glass-box'><h4>🌞 AM Routine</h4><ul>{items}</ul></div>",
                    unsafe_allow_html=True
                )

            if plan.get("pm_routine"):
                items = "".join([
                    f"<li><strong>{step.get('step','Step')}:</strong> {step.get('product','')}</li>"
                    for step in plan["pm_routine"]
                ])
                st.markdown(
                    f"<div class='glass-box'><h4>🌙 PM Routine</h4><ul>{items}</ul></div>",
                    unsafe_allow_html=True
                )

            if plan.get("diy"):
                items = "".join([
                    f"<li>{tip}</li>" for tip in plan["diy"]
                ])
                st.markdown(
                    f"<div class='glass-box'><h4>🧴 DIY Care</h4><ul>{items}</ul></div>",
                    unsafe_allow_html=True
                )

            if plan.get("caution"):
                st.markdown(
                    f"<div class='warn-box'>⚠️ {plan['caution']}</div>",
                    unsafe_allow_html=True
                )

            st.download_button(
                "⬇️ Download routine (.txt)",
                data=json.dumps(plan, indent=2),
                file_name="skinsync_routine.txt"
            )

        if save_clicked:
            if st.session_state.last_plan_beta is None:
                st.warning("No consult to save yet!")
            else:
                payload = {
                    "profile": st.session_state.profile,
                    "conversation": st.session_state.messages_beta,
                    "last_plan": st.session_state.last_plan_beta,
                    "allergies": st.session_state.allergies,
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

# ==========================================
# 📷 IMAGE ANALYSIS PAGE
# ==========================================
def render_scan():
    render_back_to_home()
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown("### 📷 Skin Analysis", unsafe_allow_html=True)

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

    with col2:
        st.markdown("""
        <div class="glass-box">
            <h4>📘 How This Works</h4>
            <ul>
                <li>Converts image to RGB.</li>
                <li>Computes redness index (R - (G+B)/2).</li>
                <li>Normalizes values 0–1.</li>
                <li>Averages pixels.</li>
                <li>Maps to mild / moderate / high categories.</li>
            </ul>
            <p style="opacity:0.7;">
                This uses basic computer-vision preprocessing — useful to explain on your resume.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 📅 APPOINTMENTS
# ==========================================
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

# ==========================================
# 📋 CONSULT HISTORY
# ==========================================
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
        if selected_id:
            row = df[df["id"] == selected_id].iloc[0]
            try:
                data = json.loads(row["data"])
                prof = data.get("profile", {})
                convo = data.get("conversation", [])
                last_plan = data.get("last_plan", "")
                allergies = data.get("allergies", [])

                first_user = next((m["text"] for m in convo if m["role"] == "user"), "")

                st.markdown("#### 🧑‍⚕️ Snapshot")
                st.write(f"**User:** {prof.get('name') or 'Unknown'}")
                st.write(f"**Skin type:** {prof.get('skin_type')} · **Concern:** {prof.get('main_concern')}")
                st.write(f"**Allergies:** {', '.join(allergies) if allergies else 'None recorded'}")
                st.write(f"**Created at:** {row['created_at']}")

                st.markdown("#### 💬 First message")
                st.write(first_user or "_(empty)_")

                st.markdown("#### 🧴 Saved routine / plan")
                st.write(last_plan or "_No plan stored._")
            except Exception:
                st.write(row["data"][:500])

    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 📔 DAILY SKIN DIARY
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

st.markdown("---")
st.caption(
    "SkinSync — advice is for educational purposes only and not a substitute for in-person dermatology. "
    "If symptoms are severe, painful, or rapidly worsening, seek medical help."
)
