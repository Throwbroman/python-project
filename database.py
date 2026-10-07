"""
database.py
-----------
SQLite persistence layer (Step 9 of the build guide).

Only four operations are needed: INSERT, SELECT, UPDATE, DELETE.
Each is wrapped in its own small function, as the guide recommends.
"""

import sqlite3
from datetime import date

DB_PATH = "fd_manager.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fixed_deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            account_no TEXT NOT NULL UNIQUE,
            principal REAL NOT NULL,
            rate REAL NOT NULL,
            start_date TEXT NOT NULL,
            tenure_years REAL NOT NULL,
            premature_closed INTEGER DEFAULT 0,
            closure_date TEXT,
            penalty_rate REAL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def insert_fd(customer, account_no, principal, rate, start_date, tenure_years,
              penalty_rate=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO fixed_deposits
            (customer, account_no, principal, rate, start_date, tenure_years, penalty_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (customer, account_no, principal, rate, start_date.isoformat(),
          tenure_years, penalty_rate))
    conn.commit()
    conn.close()


def get_all_fds():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fixed_deposits ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_fd(fd_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fixed_deposits WHERE id = ?", (fd_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_premature_closed(fd_id, closure_date: date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE fixed_deposits
        SET premature_closed = 1, closure_date = ?
        WHERE id = ?
    """, (closure_date.isoformat(), fd_id))
    conn.commit()
    conn.close()


def delete_fd(fd_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fixed_deposits WHERE id = ?", (fd_id,))
    conn.commit()
    conn.close()
