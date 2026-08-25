import sqlite3

from config.constants import DB_PATH, SQL_SCHEMA_PATH


def get_connection():
    """Stellt eine Verbindung zur Datenbank her."""
    con = sqlite3.connect(DB_PATH, timeout=30, isolation_level="DEFERRED")
    con.execute("PRAGMA journal_mode=WAL;")
    return con


def init_db(con: sqlite3.Connection) -> None:
    """Liest das Schema‑File und führt es aus."""
    with open(SQL_SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql_script = f.read()
    con.executescript(sql_script)
    con.commit()
