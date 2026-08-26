import streamlit as st
from typing import Dict, Tuple

from core import Match, MatchMode


def process_match_scores(match: Match, scores: Dict[int, Tuple[int, int]]) -> bool:
    """
    Verarbeitet die eingegebenen Satzergebnisse und fügt sie dem Match hinzu.

    - Bei Best-of-3 oder Best-of-5: Prüft, ob das Match beendet ist.
    - Bei anderen Modus: Prüft, ob alle Sätze ausgefüllt und gültig sind.

    Gibt True zurück, wenn alles erfolgreich war.
    """
    # Standard-Regel: Nur wenn es kein Best-of-3/5 ist
    modus = match.settings.modus
    if modus != MatchMode.BEST_OF_3 and modus != MatchMode.BEST_OF_5:
        end_points = match.settings.points
        # Alle Sätze müssen ausgefüllt sein
        if not all(p1 is not None and p2 is not None for p1, p2 in scores.values()):
            return False

        # Alle Sätze müssen mindestens die Punktzahl erreichen
        if not all(p1 >= end_points or p2 >= end_points for p1, p2 in scores.values()):
            return False

        # Alle Sätze hinzufügen
        try:
            for set_num, (p1, p2) in scores.items():
                match.add_set(set_num, p1, p2)
        except ValueError as e:
            st.error(f"Fehler bei Satz {set_num}: {e}")
            print(f"Fehler bei Satz {set_num}: {e}")
            return False

        return True

    # BEST_OF_3 oder BEST_OF_5 → Prüfe, ob Match beendet ist
    min_sets_to_win = 2 if MatchMode.BEST_OF_3 else 3

    # Zähle Gewinnsätze
    t1_won = sum(1 for p1, p2 in scores.values() if p1 > p2)
    t2_won = sum(1 for p1, p2 in scores.values() if p2 > p1)

    # Ist das Match beendet?
    match_finished = t1_won >= min_sets_to_win or t2_won >= min_sets_to_win

    if not match_finished:
        return False  # Match noch nicht beendet

    # Nur die gespielten Sätze hinzufügen
    try:
        for set_num, (p1, p2) in scores.items():
            if p1 is not None and p2 is not None and p1 != 0 and p2 != 0:
                print(f"Satz {set_num}: {p1}:{p2}")
                match.add_set(set_num, p1, p2)
                print(f"Score: {match.score}")  # Optional: Debugging
    except ValueError as e:
        print(f"Fehler bei Satz {set_num}: {e}")
        return False

    return True