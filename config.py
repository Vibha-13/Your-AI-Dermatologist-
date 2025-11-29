import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

DB_PATH = "skinsync.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

def setup_database():
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

def setup_session(st):
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
