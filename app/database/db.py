"""
SQLite user store for authentication and access requests.

Database lives at app/database/users.db (auto-created on first run).
Use scripts/create_user.py to add user accounts after approving requests.
"""

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "users.db"


def init_db() -> None:
    """Create all tables if they do not exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS access_requests (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT    NOT NULL,
                email        TEXT    NOT NULL,
                status       TEXT    DEFAULT 'pending',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


# ── User management ────────────────────────────────────────────────────────────


def get_user(username: str) -> Optional[dict]:
    """Return user dict or None if not found."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row:
        return {"username": row[0], "password_hash": row[1]}
    return None


def create_user(username: str, password_hash: str) -> None:
    """Insert a new user. Raises sqlite3.IntegrityError if username exists."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()


# ── Access requests ────────────────────────────────────────────────────────────


def create_access_request(username: str, email: str) -> None:
    """Log a new access request. Does not create a user account."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO access_requests (username, email) VALUES (?, ?)",
            (username, email),
        )
        conn.commit()


def get_pending_requests() -> list[dict]:
    """Return all pending access requests."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, username, email, requested_at FROM access_requests WHERE status = 'pending'"
        ).fetchall()
    return [
        {"id": r[0], "username": r[1], "email": r[2], "requested_at": r[3]}
        for r in rows
    ]
