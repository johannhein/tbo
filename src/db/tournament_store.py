import pickle
from typing import Optional

from core import Tournament
from db import get_connection


def save_tournament(tournament: Tournament, name: str) -> None:
    """Speichert ein Tournament-Objekt als BLOB."""
    if not name or not name.strip():
        raise ValueError("Der Turniername darf nicht leer sein.")

    with get_connection() as conn:
        serialized = pickle.dumps(tournament)
        conn.execute(
            """
            INSERT OR REPLACE INTO tournaments (name, data)
            VALUES (?, ?)
            """,
            (name.strip(), serialized)
        )
        conn.commit()


def load_tournament(name: str) -> Optional[Tournament]:
    """Lädt ein Tournament-Objekt aus der Datenbank (als BLOB)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT data FROM tournaments WHERE name = ?", (name,)
        ).fetchone()
        if not row:
            return None
        try:
            return pickle.loads(row[0])
        except Exception as e:
            print(f"Fehler beim Laden von {name}: {e}")
            return None


def get_all_tournament_names() -> list[str]:
    """Liefert eine Liste aller Turniernamen aus der Datenbank."""
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM tournaments").fetchall()
        return [row[0] for row in rows]


def delete_tournament(name: str) -> bool:
    """Löscht ein Turnier, falls vorhanden."""
    with get_connection() as conn:
        result = conn.execute("DELETE FROM tournaments WHERE name = ?", (name,))
        conn.commit()
        return result.rowcount > 0
