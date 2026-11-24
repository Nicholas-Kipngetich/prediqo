"""Dev-only helper: restore the static dev user after local account-deletion tests."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "prediqo-dev.db"

with sqlite3.connect(DB_PATH) as connection:
    cursor = connection.execute(
        "UPDATE users SET status = 'ACTIVE', deleted_at = NULL, "
        "email = 'dev@prediqo.local', display_name = 'Prediqo Developer' "
        "WHERE firebase_uid = 'dev-firebase-uid'"
    )
    print(f"Restored {cursor.rowcount} dev user(s)")
