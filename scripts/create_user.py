"""
One-time CLI utility to create a user in the SRF Capital Studio auth database.

Usage (from project root):
    python scripts/create_user.py

Run this once before starting the app for the first time.
"""

import sys
import sqlite3
from pathlib import Path

# Ensure project root on path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import bcrypt
from app.database.db import create_user, init_db


def main() -> None:
    print("═" * 48)
    print("  SRF Capital Studio — Create User")
    print("═" * 48)

    init_db()

    username = input("\n  Username: ").strip()
    if not username:
        print("  ✗ Username cannot be empty.")
        sys.exit(1)

    import getpass
    password = getpass.getpass("  Password: ").strip()
    if len(password) < 6:
        print("  ✗ Password must be at least 6 characters.")
        sys.exit(1)

    confirm = getpass.getpass("  Confirm password: ").strip()
    if password != confirm:
        print("  ✗ Passwords do not match.")
        sys.exit(1)

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        create_user(username, password_hash)
        print(f"\n  ✓ User '{username}' created successfully.")
        print("  You can now start the app and sign in.\n")
    except sqlite3.IntegrityError:
        print(f"\n  ✗ Username '{username}' already exists.")
        sys.exit(1)


if __name__ == "__main__":
    main()
