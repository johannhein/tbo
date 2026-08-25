-- -----------------------------------------------------------------
-- Tabelle für die Feld‑Belegung (wie bereits definiert)
-- -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tournament_courts (
    id            INTEGER PRIMARY KEY,
    tournament_id TEXT NOT NULL,
    court         INTEGER NOT NULL
);

-- -----------------------------------------------------------------
-- Tabelle für globale Feld‑Höhen (String‑ID als PK)
-- -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS court_heights_global (
    court           INTEGER NOT NULL,
    day             TEXT    NOT NULL,
    year            INTEGER NOT NULL,
    height_category TEXT    NOT NULL,
    UNIQUE (court, day, year)
);

-- -----------------------------------------------------------------
-- Tabelle zum Abspeichern der erstellten Turniere als BLOB
-- -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tournaments
(
    name TEXT PRIMARY KEY,
    data BLOB,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
