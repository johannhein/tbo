from typing import List, Set, Dict, Optional

from db.db import get_connection


def get_used_courts(exclude_tournament: str | None = None) -> Set[int]:
    """
    Gibt alle bereits belegten Felder zurück.
    Optional kann das aktuelle Turnier (z. B. beim Editieren) ausgeschlossen werden.
    """
    with get_connection() as con:
        cur = con.cursor()
        if exclude_tournament:
            cur.execute(
                "SELECT court FROM tournament_courts WHERE tournament_id <> ?",
                (exclude_tournament,),
            )
        else:
            cur.execute("SELECT court FROM tournament_courts")
        return {row[0] for row in cur.fetchall()}

def set_courts(tournament_id: str, courts: List[int]) -> None:
    """
    Überschreibt die Feld‑Liste für ein bestimmtes Turnier.
    (Alle alten Einträge werden gelöscht, danach werden die neuen eingefügt.)
    """
    with get_connection() as con:
        con.execute(
            "DELETE FROM tournament_courts WHERE tournament_id = ?",
            (tournament_id,),
        )
        con.executemany(
            "INSERT INTO tournament_courts (tournament_id, court) VALUES (?, ?)",
            [(tournament_id, c) for c in courts],
        )
        con.commit()

def remove_tournament(tournament_id: str) -> None:
    """Entfernt sämtliche Einträge eines Turniers (z. B. beim Löschen)."""
    with get_connection() as con:
        con.execute("DELETE FROM tournament_courts WHERE tournament_id = ?", (tournament_id,))
        con.commit()


# ------------------------------------------------------------------ #
# 2️⃣  Feld‑Höhen‑Einstellungen
# ------------------------------------------------------------------ #
def get_global_court_heights() -> Dict[int, str]:
    """Liefert {court → height_category} für alle bereits gespeicherten Felder."""
    with get_connection() as con:
        cur = con.execute(
            "SELECT court, height_category FROM court_heights_global"
        )
        return {court: height for court, height in cur.fetchall()}


def save_court_height(court: int, day: str, year: int, height_category: str,) -> None:
    """
    Fügt einen neuen Eintrag ein oder überschreibt den bestehenden,
    wenn (court, day, year) bereits vorhanden ist.
    """
    sql = """
    INSERT INTO court_heights_global (court, day, year, height_category)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (court, day, year)               -- die UNIQUE‑Kombination
    DO UPDATE SET height_category = excluded.height_category;
    """
    # `excluded` ist ein SQLite‑Spezial‑Alias, das die Werte des zu insertenden Datensatzes enthält.
    with get_connection() as con:
        con.execute(sql, (court, day, year, height_category))
        con.commit()


def get_unique_courts() -> List[int]:
    """
    Liefert eine sortierte Liste aller unterschiedlichen `court`‑Werte
    aus der Tabelle `court_heights_global`.
    """
    sql = "SELECT DISTINCT court FROM court_heights_global ORDER BY court;"

    with get_connection() as con:
        cur = con.execute(sql)
        rows = cur.fetchall()
        courts = [row[0] for row in rows]
    return courts


def get_courts_filtered(*, day: Optional[str] = None, year: Optional[int] = None, height_category: Optional[str] = None,
                        ) -> List[int]:
    """
    Gibt eine sortierte Liste aller unterschiedlichen `court`‑Werte zurück,
    die den angegebenen Filterkriterien entsprechen.
    """
    sql = """
    SELECT DISTINCT court
    FROM court_heights_global
    WHERE 1 = 1
      AND (:day IS NULL OR day = :day)
      AND (:year IS NULL OR year = :year)
      AND (:height_category IS NULL OR height_category = :height_category)
    ORDER BY court;
    """

    params = {
        "day": day,
        "year": year,
        "height_category": height_category,
    }

    with get_connection() as con:
        cur = con.execute(sql, params)
        rows = cur.fetchall()
        courts = [row[0] for row in rows]

    return courts
