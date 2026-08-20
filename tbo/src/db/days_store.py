import json
import sqlite3
from typing import List, Optional
import pandas as pd

from config.constants import TOURNAMENT_DAYS, DB_PATH


def get_connection() -> sqlite3.Connection:
    """Einfacher Helper – öffnet (bzw. erstellt) die DB."""
    return sqlite3.connect(DB_PATH)

def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (name,),
    )
    return cur.fetchone() is not None


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table});")
    cols = [row[1] for row in cur.fetchall()]   # row[1] = column‑name
    return column in cols


def create_table_and_fill(conn: sqlite3.Connection) -> None:
    """Legt die Tabelle an und füllt sie mit Daten."""
    if not table_exists(conn, "tournament_days"):
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tournament_days (
                type    TEXT PRIMARY KEY,
                day     TEXT NOT NULL,
                height   TEXT NOT NULL,
                courts  TEXT NOT NULL
            );
            """
        )

        conn.executemany(
            "INSERT INTO tournament_days (type, day, height, courts) VALUES (?, ?, ?, ?);",
            TOURNAMENT_DAYS,
        )
        conn.commit()


def load_table(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Liefert einen DataFrame mit den Spalten:
    type, day, height, courts (als List[int] für den Multi‑Select)
    """
    query = "SELECT type, day, height, courts FROM tournament_days ORDER BY type;"
    df = pd.read_sql_query(query, conn)

    def json_to_str_list(val: str) -> List[str]:
        try:
            # JSON‑String → Python‑Liste (z. B. [1,2,4])
            raw = json.loads(val)
            # → Liste von Strings, weil das UI Strings erwartet
            return [str(i) for i in raw]
        except Exception:
            return []                     # leere Liste, falls das Feld ungültig ist

    df["courts"] = df["courts"].apply(json_to_str_list)
    return df


def upsert_row(row: pd.Series) -> None:
    """
    Fügt eine Zeile ein oder aktualisiert sie.
    `row` muss die Spalten: type, day, height, courts (List[int]) besitzen.
    """
    # Strings → ints → JSON‑String, weil wir die Daten in SQLite als int‑Liste speichern wollen
    courts_int = [int(i) for i in row["courts"]]
    row_dict = row.to_dict()
    row_dict["courts"] = json.dumps(courts_int)

    sql = """
          INSERT INTO tournament_days (type, day, height, courts)
          VALUES (:type, :day, :height, :courts)
          ON CONFLICT(type) DO UPDATE SET day    = excluded.day,
                                          height = excluded.height,
                                          courts = excluded.courts; \
          """
    with get_connection() as conn:
        conn.execute(sql, row_dict)
        conn.commit()


def delete_row(type_key: str) -> None:
    """Löscht eine Zeile anhand des Primary Keys `type`."""
    with get_connection() as conn:
        conn.execute("DELETE FROM tournament_days WHERE type = ?;", (type_key,))
        conn.commit()


def get_courts_for_type(tournament_type: str) -> Optional[List[int]]:
    """
    Gibt die Liste von Court‑IDs für den übergebenen `tournament_type` zurück.
    - Wenn der Typ nicht existiert → None
    - Wenn die Spalte leer oder ungültig ist → leere Liste []
    """
    query = """
        SELECT courts
        FROM tournament_days
        WHERE type = ?
        LIMIT 1;
    """
    with get_connection() as conn:
        cur = conn.execute(query, (tournament_type,))
        row = cur.fetchone()

    if row is None:
        return None

    courts_json = row[0]               # z. B. "[2, 3, 4, 5]"
    try:
        # JSON‑String → Python‑Liste von ints
        courts = json.loads(courts_json)
        return [int(c) for c in courts]
    except Exception:
        return []