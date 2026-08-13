# bvc_cup/services/persistence.py
import json
import os
import random, string
from pathlib import Path
from typing import Dict, List
import pandas as pd

from config.constants import DATA_FILE, GROUP_MATCHES

from charset_normalizer import from_path

def detect_encoding(csv_path: Path) -> str:
    result = from_path(csv_path).best()
    return result.encoding if result else "utf-8"


def list_csv_files(upload_dir: Path) -> List[Path]:
    """
    Gibt eine Liste aller *.csv‑Dateien im angegebenen Ordner zurück.
    """
    upload_dir.mkdir(parents=True, exist_ok=True)   # Ordner anlegen, falls er fehlt
    return sorted(upload_dir.glob("*.csv"))


def read_teams_from_csv(csv_path: Path) -> Dict[str, dict]:
    """
    Liest die CSV‑Datei ein und gibt ein Dictionary zurück:
    {
        "<team_id>": {
            "name": "<Name>",
            "email": "<E‑Mail>",
            "email_allowed": True/False,
            "plz": "<PLZ>",
            "city": "<City>",
            "verein": "<Verein / Gruppe>",
            "merch": [ "<Merch‑Eintrag>", ... ],
            "order_comment": "<Kommentar / Nachricht>",
            "total_amount": float,
            "paid_amount": float
        },
        ...
    }
    """
    # CSV ist mit Semikolon getrennt
    df = pd.read_csv(csv_path, sep=";", dtype=str, keep_default_na=False)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    teams: Dict[str, dict] = {}
    for _, row in df.iterrows():
        team_id = str(row["Datensatz-ID"]).strip()

        # ---- Merchandise‑Spalten sammeln (alle, die "Merchandise" enthalten) ----
        merch_items: List[str] = [
            row[col] for col in df.columns
            if "Merchandise" in col and row[col] and row[col] != "[nichts]"
        ]

        # ---- Betrag‑Umwandlung (z. B. " €22,00 " → 22.0) ----
        def to_float(val: str) -> float:
            if not val:
                return 0.0
            cleaned = val.replace("€", "").replace(",", ".").replace(" ", "").replace("-", "0")
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

        total = to_float(row["Gesamtbetrag"])
        paid  = to_float(row["Bezahlter Betrag"])

        teams[team_id] = {
            "name": row["Name"],
            "email": row["E‑Mail‑Adresse"],
            "email_allowed": row["E‑Mail darf gespeichert werden"].lower() == "ja",
            "plz": row["PLZ"],
            "city": row["City"],
            "verein": row["Verein / Gruppe"],
            "merch": merch_items,
            "order_comment": row["Kommentar / Nachricht"],
            "total_amount": total,
            "paid_amount": paid,
        }

    return teams

def _generate_token(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

def _ensure_tokens(data: dict) -> dict:
    """Erzeugt fehlende Team‑ und Admin‑Tokens."""
    if "team_tokens" not in data:
        data["team_tokens"] = {}
    if "teams" in data:
        for grp, teams in data["teams"].items():
            for t_id in teams:
                data["team_tokens"].setdefault(t_id, _generate_token())
    data.setdefault("admin_token", _generate_token(8))
    return data

def load_data() -> dict:
    """Lädt das JSON‑File, führt ggf. Migrationen durch und gibt ein dict zurück."""
    default = {
        "tournament_config": None,
        "group_matches": {},
        "final_matches": {},
        "teams": {},
        "paid_status": {}
    }

    if DATA_FILE.exists():
        with DATA_FILE.open(encoding="utf-8") as f:
            data = json.load(f)

        # ---- Migration von altem 12‑Team‑Format ----
        if "tournament_config" not in data:
            from .schedule import get_final_schema
            schedule = [
                {
                    "id": f"group_{i}",
                    "time": m[1],
                    "court": m[2],
                    "t1": m[3],
                    "t2": m[4],
                    "group": m[5],
                }
                for i, m in enumerate(GROUP_MATCHES)
            ]
            data["tournament_config"] = {
                "num_teams": 12,
                "num_groups": 2,
                "num_courts": 3,
                "groups": ["A", "B"],
                "schedule": schedule,
                "final_matches_schema": get_final_schema(12),
            }
            # Teams migrieren
            data["teams"] = {}
            if "teams_a" in data:
                data["teams"]["A"] = data["teams_a"]
            if "teams_b" in data:
                data["teams"]["B"] = data["teams_b"]

        data.setdefault("paid_status", {})
        data = _ensure_tokens(data)
        return data

    # Datei existiert nicht → frische Default‑Daten
    return _ensure_tokens(default)

def save_data(data: dict) -> None:
    """Schreibt das komplette Turnier‑Dictionary zurück."""
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
