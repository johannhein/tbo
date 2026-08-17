# bvc_cup/services/auth.py
"""Hilfsfunktionen für Rollen‑ und Berechtigungs‑Checks."""

from typing import Optional
import streamlit as st


def can_edit_match(t1: str, t2: str) -> bool:
    """
    Prüft, ob der aktuell eingeloggte Nutzer das Ergebnis eines Matches
    bearbeiten darf.

    - **Admin** : darf alles editieren.
    - **Team‑Nutzer** : darf nur Matches bearbeiten, an denen das eigene
      Team (Team‑ID) beteiligt ist.
    - **Gast / Zuschauer** : hat kein Schreibrecht.

    Parameters
    ----------
    t1, t2 : str
        Die Team‑IDs der beiden Gegner im Match.

    Returns
    -------
    bool
        ``True`` wenn das Ergebnis gespeichert werden darf, sonst ``False``.
    """
    role = st.session_state.get("role")

    if role == "admin":
        return True

    if role == "team":
        my_team = st.session_state.get("team_id", "")
        # Das Team kann sowohl als t1 als auch als t2 auftreten.
        return bool(my_team) and (my_team in str(t1) or my_team in str(t2))

    # Gäste / Zuschauer
    return False