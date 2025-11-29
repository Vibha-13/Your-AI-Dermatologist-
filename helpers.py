import json
import numpy as np
from PIL import Image
import requests
from datetime import datetime
from config import OPENROUTER_API_KEY

def go_to(st, page: str):
    st.session_state.page = page
    try:
        st.experimental_set_query_params(page=page)
    except:
        pass

def detect_severe_keywords(text: str) -> bool:
    severe = ["bleeding", "pus", "severe pain", "fever", "spreading", "infection", "open sore"]
    t = (text or "").lower()
    return any(word in t for word in severe)

def append_message(st, role: str, text: str):
    st.session_state.messages.append({"role": role, "text": text})

def build_system_prompt(st):
    p = st.session_state.profile
    return f"""
You are SkinSync, a gentle AI dermatology assistant.

User profile:
- Name: {p.get('name') or 'User'}
- Age range: {p['age_bucket']}
- Skin type: {p['skin_type']}
- Main concern: {p['main_concern']}
- Sensitivity: {p['sensitivity']}
- Location: {p['location'] or 'not specified'}

Follow-ups:
- Provide AM/PM routine
- 1–2 DIY packs
- Cautions
- Warm and short
"""

def call_openrouter_chat(messages):
    if not OPENROUTER_API_KEY:
        return None, "No OPENROUTER_API_KEY found."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://skinsync.streamlit.app",
        "X-Title": "SkinSync AI",
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content, None
    except Exception as e:
        return None, str(e)

def analyze_skin_image(image: Image.Image):
    try:
        img = image.convert("RGB")
        arr = np.array(img).astype("float32")

        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]

        redness = r - (g + b) / 2
        diff = redness.max() - redness.min() or 1e-6
        normalized = (redness - redness.min()) / diff
        mean_red = float(np.mean(normalized))

        if mean_red < 0.25:
            severity = "Very mild redness 🙂"
        elif mean_red < 0.45:
            severity = "Mild redness 🌸"
        elif mean_red < 0.65:
            severity = "Moderate redness 🔎"
        else:
            severity = "High redness ⚠️"

        return mean_red, severity
    except:
        return 0.0, "Error analyzing image."
