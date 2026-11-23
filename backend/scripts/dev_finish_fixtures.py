"""Dev-only helper: mark four scheduled sample fixtures as finished so settlement
can be exercised locally. Never use this against real data.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "prediqo-dev.db"

with sqlite3.connect(DB_PATH) as connection:
    rows = connection.execute(
        "SELECT id FROM fixtures WHERE status = 'SCHEDULED' ORDER BY kickoff_utc LIMIT 4"
    ).fetchall()
    for index, row in enumerate(rows):
        connection.execute(
            "UPDATE fixtures SET status = 'FINISHED', home_score = 2, away_score = ? "
            "WHERE id = ?",
            (1 if index % 2 == 0 else 2, row[0]),
        )
    print(f"Finished {len(rows)} sample fixtures")
