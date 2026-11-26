import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parent / "reviewradar.db"))

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review TEXT NOT NULL,
                date TEXT,
                product TEXT,
                rating REAL,
                sentiment TEXT,
                category TEXT,
                topic TEXT,
                severity INTEGER
            )
        """)

def save_reviews(rows):
    if not rows: return
    with connect() as conn:
        for row in rows:
            conn.execute("""
                INSERT INTO reviews (review, date, product, rating, sentiment, category, topic, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(row.get("review", "")), str(row.get("date", ""))[:10], str(row.get("product", "General")),
                  row.get("rating"), row.get("sentiment"), row.get("category"), row.get("topic"), row.get("severity")))

def get_reviews():
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM reviews ORDER BY id DESC").fetchall()]

def get_stats():
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        negative = conn.execute("SELECT COUNT(*) FROM reviews WHERE sentiment='Negative'").fetchone()[0]
        positive = conn.execute("SELECT COUNT(*) FROM reviews WHERE sentiment='Positive'").fetchone()[0]
    return {"total": total, "negative": negative, "positive": positive}

def clear_reviews():
    with connect() as conn:
        conn.execute("DELETE FROM reviews")
