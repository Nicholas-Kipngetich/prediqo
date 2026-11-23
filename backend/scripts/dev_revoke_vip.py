"""Dev-only helper: remove the VIP_USER role from the static dev user."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "prediqo-dev.db"

with sqlite3.connect(DB_PATH) as connection:
    cursor = connection.execute("DELETE FROM user_roles WHERE role_id = 2")
    print(f"Removed {cursor.rowcount} VIP role assignment(s)")
    subs = connection.execute("DELETE FROM subscriptions")
    print(f"Removed {subs.rowcount} active subscription(s)")
