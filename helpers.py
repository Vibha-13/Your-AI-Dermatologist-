import os
import json
from datetime import datetime
import sqlite3

# Correct universal CSS loader for Streamlit Cloud
def load_css():
    base = os.path.dirname(os.path.abspath(__file__))
    root_css = os.path.join(base, "style.css")       # try same folder
    parent_css = os.path.join(base, "..", "style.css")  # try root folder

    css_path = root_css if os.path.exists(root_css) else parent_css

    with open(css_path, "r") as f:
        return f"<style>{f.read()}</style>"


# Simple internal router
def go_to(st, page_name):
    st.query_params(page=page_name)


# SQLite connection
conn = sqlite3.connect("skinsync.db", check_same_thread=False)
c = conn.cursor()

# Create tables if not existing
c.execute("""
CREATE TABLE IF NOT EXISTS consults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    data TEXT,
    created_at TEXT
)
""")

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

conn.commit()


# Session initializer
def init_session(st):
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "profile" not in st.session_state:
        st.session_state.profile = {"name": "Guest"}

    if "session_id" not in st.session_state:
        st.session_state.session_id = "user_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    if "last_plan" not in st.session_state:
        st.session_state.last_plan = None


# Chat helpers
def append_message(st, role, text):
    st.session_state.messages.append({"role": role, "text": text})
