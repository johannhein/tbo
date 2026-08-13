# tbo/services/tournament_manager.py
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from config.constants import DATA_DIR

# Pfad zum Daten-Ordner
DATA_DIR.mkdir(exist_ok=True)

# Liste aller Turniere (in der Session)
Tournament = Dict[str, str]  # {"name": "TBO 2027", "file": "results_bvc_2026.json"}

def get_all_tournaments() -> List[Tournament]:
    """Liefert eine Liste aller vorhandenen Turniere."""
    tournaments = []
    for file_path in DATA_DIR.iterdir():
        if file_path.suffix == ".json" and file_path.name.startswith("results_"):
            name = file_path.name[7:-5]  # "results_bvc_2026.json" → "bvc_2026"
            tournaments.append({"name": name.replace("_", " ").title(), "file": file_path.name})
    return sorted(tournaments, key=lambda x: x["name"])

def create_new_tournament(name: str) -> str:
    """Erstellt ein neues Turnier mit dem gegebenen Namen."""
    # Sicherstellen, dass der Name gültig ist
    safe_name = name.strip().lower().replace(" ", "_")
    if not safe_name:
        raise ValueError("Turniername darf nicht leer sein.")

    # Dateiname: results_<name>.json
    filename = f"results_{safe_name}.json"
    file_path = DATA_DIR / filename

    # Prüfen, ob Datei bereits existiert
    if file_path.exists():
        raise ValueError(f"Ein Turnier mit dem Namen '{name}' existiert bereits.")

    # Leeres Turnier-Objekt erstellen
    empty_data = {
        "tournament_config": None,
        "teams": {},
        "group_matches": {},
        "final_matches": {},
        "team_tokens": {},
        "paid_status": {},
        "admin_token": ""
    }

    # Speichern
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(empty_data, f, indent=4)

    return filename

def load_tournament_data(filename: str) -> Dict:
    """Lädt die Daten eines Turniers aus der Datei."""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Turnier-Datei '{filename}' nicht gefunden.")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tournament_data(filename: str, data: Dict) -> None:
    """Speichert die Daten eines Turniers in der Datei."""
    file_path = DATA_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def delete_tournament(filename: str) -> None:
    """Löscht ein Turnier (Datei)."""
    file_path = DATA_DIR / filename
    if file_path.exists():
        file_path.unlink()