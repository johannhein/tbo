import pickle
from pathlib import Path
from typing import List
import pandas as pd
from charset_normalizer import from_path
import streamlit as st

from config.constants import PICKLE_DIR
from core.models import Tournament, Group
from persistence.path import ensure_dir


def detect_encoding(csv_path: Path) -> str:
    result = from_path(csv_path).best()
    return result.encoding if result else "utf-8"


def list_csv_files(upload_dir: Path) -> List[Path]:
    """
    Gibt eine Liste aller *.csv‑Dateien im angegebenen Ordner zurück.
    """
    upload_dir.mkdir(parents=True, exist_ok=True)   # Ordner anlegen, falls er fehlt
    return sorted(upload_dir.glob("*.csv"))


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    """CSV einmalig einlesen und im Cache halten."""
    enc = detect_encoding(path)
    return pd.read_csv(path, dtype=str, encoding=enc, delimiter=";")


def save_tournament_pickle(tournament: Tournament, filename: str) -> None:
    """Speichert das Turnier in einer Datei."""
    name = f"{filename}.pkl"
    path = PICKLE_DIR / name
    with open(path, "wb") as f:
        pickle.dump(tournament, f)
    # st.success("✅ Turnier wurde gespeichert.")


def save_group(groups: List[Group], filename: str) -> None:
    """Speichert das Turnier in einer Datei."""
    name = f"{filename}.pkl"
    pickle_dir = PICKLE_DIR / "groups"
    ensure_dir(pickle_dir)
    path = pickle_dir / name
    with open(path, "wb") as f:
        pickle.dump(groups, f)


def load_pickle(path: Path) -> Tournament | None:
    """Lädt das Turnier aus der Datei, falls vorhanden."""
    if not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        st.warning(f"❌ Konnte Pickle Datei nicht laden: {e}")
        return None
