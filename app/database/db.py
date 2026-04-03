"""
SQLite user store for authentication, pending registrations, and access requests.

Database lives at app/database/users.db (auto-created on first run).
Use scripts/create_user.py to add the first admin account.
Pending users are stored in pending_users until an admin approves them.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "users.db"


def init_db() -> None:
    """Create all tables if they do not exist. Safe to call on every startup."""
    with sqlite3.connect(DB_PATH) as conn:
        # ── Active users (can log in) ─────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                is_admin      INTEGER DEFAULT 0,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migration: add is_admin to existing databases that predate this column
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        if "is_admin" not in existing_columns:
            conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")

        # ── Pending registrations (awaiting admin approval) ───────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL,
                email         TEXT    NOT NULL,
                password_hash TEXT    NOT NULL,
                status        TEXT    DEFAULT 'pending',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Legacy access_requests table (kept for backward compatibility) ────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS access_requests (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT    NOT NULL,
                email        TEXT    NOT NULL,
                status       TEXT    DEFAULT 'pending',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Auto-create admin user on first run if not present
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("wilson@srf",)
        ).fetchone()
        if not existing:
            import bcrypt as _bcrypt
            password = os.getenv("ADMIN_PASSWORD", "srf@studio")
            pw_hash = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
                ("wilson@srf", pw_hash),
            )
            print(f"[SRF] Admin user created — username: wilson@srf  password: {password}")

        # Auto-promote the named admin account every startup (idempotent)
        conn.execute(
            "UPDATE users SET is_admin = 1 WHERE username = ?", ("wilson@srf",)
        )

        conn.commit()


# ── Active user management ─────────────────────────────────────────────────────


def get_user(username: str) -> Optional[dict]:
    """Return user dict (includes is_admin) or None if not found."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT username, password_hash, is_admin FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row:
        return {"username": row[0], "password_hash": row[1], "is_admin": row[2]}
    return None


def create_user(username: str, password_hash: str, is_admin: int = 0) -> None:
    """Insert a new active user. Raises sqlite3.IntegrityError if username exists."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            (username, password_hash, is_admin),
        )
        conn.commit()


# ── Pending user registration ──────────────────────────────────────────────────


def create_pending_user(username: str, email: str, password_hash: str) -> None:
    """Store a registration request with hashed password, awaiting admin approval."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO pending_users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        conn.commit()


def get_pending_users() -> list[dict]:
    """Return all pending registration requests (status = 'pending')."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, username, email, created_at "
            "FROM pending_users WHERE status = 'pending' ORDER BY created_at ASC"
        ).fetchall()
    return [
        {"id": r[0], "username": r[1], "email": r[2], "created_at": r[3]}
        for r in rows
    ]


def approve_pending_user(user_id: int) -> None:
    """
    Promote a pending user to the active users table and mark as approved.
    Raises sqlite3.IntegrityError if the username is already taken in users.
    """
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT username, password_hash FROM pending_users WHERE id = ? AND status = 'pending'",
            (user_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"No pending request found with id={user_id}")
        conn.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 0)",
            (row[0], row[1]),
        )
        conn.execute(
            "UPDATE pending_users SET status = 'approved' WHERE id = ?",
            (user_id,),
        )
        conn.commit()


def reject_pending_user(user_id: int) -> None:
    """Mark a pending registration request as rejected."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE pending_users SET status = 'rejected' WHERE id = ?",
            (user_id,),
        )
        conn.commit()


# ── Legacy helpers (kept so old imports don't break) ──────────────────────────


def create_access_request(username: str, email: str) -> None:
    """Legacy: log an access request without password. Use create_pending_user instead."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO access_requests (username, email) VALUES (?, ?)",
            (username, email),
        )
        conn.commit()


def get_pending_requests() -> list[dict]:
    """Legacy: return old-style access_requests rows."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, username, email, requested_at FROM access_requests WHERE status = 'pending'"
        ).fetchall()
    return [
        {"id": r[0], "username": r[1], "email": r[2], "requested_at": r[3]}
        for r in rows
    ]
