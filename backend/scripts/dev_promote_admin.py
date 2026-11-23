"""Dev-only helper: grant the static dev user the ADMIN role."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "prediqo-dev.db"

with sqlite3.connect(DB_PATH) as connection:
    row = connection.execute(
        "SELECT id FROM users WHERE firebase_uid = ?", ("dev-firebase-uid",)
    ).fetchone()
    if row is None:
        print("No dev user found. Call POST /api/v1/auth/verify first.")
    else:
        connection.execute(
            "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, 3)", (row[0],)
        )
        print(f"ADMIN role granted to dev user {row[0]}")
