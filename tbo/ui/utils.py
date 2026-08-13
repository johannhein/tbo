import math
from typing import List, Dict

import streamlit as st
from pathlib import Path
import pandas as pd

from core.models import Group
from services.persistence import detect_encoding, list_csv_files, read_teams_from_csv


def show_error(msg: str) -> None:
    """Einheitliche Fehleranzeige."""
    st.error(f"❗️ {msg}")


def show_success(msg: str) -> None:
    """Einheitliche Success‑Anzeige."""
    st.success(msg)


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    """CSV einmalig einlesen und im Cache halten."""
    enc = detect_encoding(path)
    return pd.read_csv(path, dtype=str, encoding=enc, delimiter=";")


def get_tournament_types(df: pd.DataFrame) -> List[str]:
    """Alle eindeutigen Turnier‑Kategorien aus einer DataFrame."""
    if "Turnier" not in df.columns:
        show_error("Die CSV‑Datei enthält keine Spalte **Turnier**.")
        return []
    types = (
        df["Turnier"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    return sorted(types)


def get_incomplete_groups(groups: Dict[str, Group], num_groups: int, total_teams: int,) -> List[str]:
    """
    Gibt die Namen aller Gruppen zurück, die **weniger** Teams besitzen
    als die größte mögliche Gruppe.

    - `max_size = ceil(total_teams / num_groups)` → Größe der größten Gruppe
    - Jede Gruppe, deren aktuelle Größe < max_size, ist „unvollständig“.
    """
    max_size = math.ceil(total_teams / num_groups)   # z. B. 10 Teams / 3 Gruppen → 4
    incomplete = [
        name for name, grp in groups.items()
        if len(grp.teams) < max_size
    ]
    return incomplete


def get_team_column(df_category: pd.DataFrame) -> pd.DataFrame:
    """
    Gibt ein DataFrame zurück, das ausschließlich die Spalte 'Team' enthält.
    Der Index bleibt erhalten, damit wir später die anderen Spalten wieder
    korrekt zuordnen können.
    """
    # Wir behalten den originalen Index (Zeilennummer) – das erleichtert das
    # spätere Zusammenführen mit den unveränderten Spalten.
    team_df = df_category[["Team"]].reset_index(drop=True)
    return team_df


def rebuild_category_df(
    original_df: pd.DataFrame,
    edited_team_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Kombiniert das bearbeitete 'Team'-DataFrame mit den übrigen Spalten
    aus dem originalen DataFrame (Name, Verein / Gruppe, Turnier).
    """
    # Wir gehen davon aus, dass die Zeilenreihenfolge nach dem Editieren
    # (inkl. Add/Delete) mit dem Index des bearbeiteten DataFrames übereinstimmt.
    # Deshalb setzen wir den Index zurück und fügen die anderen Spalten per .join
    # wieder an.
    other_cols = original_df.drop(columns=["Team"]).reset_index(drop=True)
    rebuilt = edited_team_df.reset_index(drop=True).join(other_cols)
    return rebuilt
