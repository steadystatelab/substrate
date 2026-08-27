import sqlite3
import os
from pathlib import Path

DB_PATH = Path(os.environ.get("TELEMETRY_DB_PATH", "data/telemetry.db"))

def init_db():
    """
    Auto-provisions the data/ directory and initializes the database schema.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                mouse_entropy REAL,
                context_fragmentation REAL,
                keyboard_idle_seconds REAL,
                window_title TEXT,
                mode TEXT
            )
        """)
        conn.commit()

def insert_snapshot(mouse_entropy, context_fragmentation, keyboard_idle_seconds, window_title, mode):
    """
    Inserts a single telemetry snapshot into the database.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO telemetry_snapshots (
                mouse_entropy,
                context_fragmentation,
                keyboard_idle_seconds,
                window_title,
                mode
            ) VALUES (?, ?, ?, ?, ?)
        """, (mouse_entropy, context_fragmentation, keyboard_idle_seconds, window_title, mode))
        conn.commit()
