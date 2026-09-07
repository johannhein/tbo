import random
import streamlit as st
from typing import Dict, Tuple

from config import MATCH_MODE_TO_SETS
from core import Match, MatchMode, Tournament
from core.models import StageType


def simulate_a_match(match: Match, stage_name: str, *, num_sets: int = None, points: int = None,
                     modus: MatchMode = None, tiebreak_points: int = None):
    modus = modus or match.settings.modus
    points = points or match.settings.points
    tiebreak_points = tiebreak_points or match.settings.tiebreak
    num_sets = num_sets or len(MATCH_MODE_TO_SETS[modus])

    scores = {}
    sets_won = [0, 0]  # [Team1, Team2]

    # Simuliere Sätze nur, solange das Match noch offen ist
    for set_idx in range(num_sets):
        # Ist dieser Satz ein Tiebreak? (nur bei BEST_OF_3, 3. Satz)
        is_tiebreak = (modus == MatchMode.BEST_OF_3 and set_idx == 2)
        target = tiebreak_points if is_tiebreak else points
        min_diff = 2

        # Nur simulieren, wenn das Match noch offen ist
        # Bei BEST_OF_3: nur 3. Satz, wenn 1:1
        if modus == MatchMode.BEST_OF_3 and set_idx == 2:
            if sets_won[0] == 1 and sets_won[1] == 1:
                # Nur wenn 1:1 → Tiebreak simulieren
                pass
            else:
                # Match entschieden → 3. Satz nicht nötig
                # Setze 0:0 (oder überspringe)
                continue  # Überspringe Simulation

        # Zufällige Startpunkte
        p1 = random.randint(1, target)
        p2 = random.randint(1, target)

        # Solange: Abstand zu klein oder noch kein Team target erreicht hat
        while not ((p1 >= target or p2 >= target) and abs(p1 - p2) >= min_diff):
            if p1 > p2 or p1 == p2:
                p1 += 1
            else:
                p2 += 1

        scores[set_idx + 1] = (p1, p2)

        # Zähle Sätze
        if p1 > p2:
            sets_won[0] += 1
        else:
            sets_won[1] += 1

        # Setze in Session-State für die Anzeige in der UI
        key_a = f"{stage_name}_set_{match.id}_a{set_idx}"
        key_b = f"{stage_name}_set_{match.id}_b{set_idx}"
        st.session_state[key_a] = p1
        st.session_state[key_b] = p2

    # Aktualisiere Match-Status
    process_match_scores(match=match, scores=scores)


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
            # print(f"Fehler bei Satz {set_num}: {e}")
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
                # print(f"Satz {set_num}: {p1}:{p2}")
                match.add_set(set_num, p1, p2)
                # print(f"Score: {match.score}")  # Optional: Debugging
    except ValueError as e:
        # print(f"Fehler bei Satz {set_num}: {e}")
        return False

    return True


def simulate_random_results(tournament: Tournament, stage_name: str):
    """Simuliert zufällige Ergebnisse für alle Matches der Runde."""
    # todo später ersetzen
    stage = tournament.stages[stage_name]
    if stage.type == StageType.GROUP:
        groups = stage.groups

        for group in groups:
            modus = group.settings.modus
            points = group.settings.points
            tiebreak_points = group.settings.tiebreak
            num_sets = len(MATCH_MODE_TO_SETS[modus])

            for match in group.match_list:
                simulate_a_match(match=match, stage_name=stage_name, modus=modus, points=points,
                                 tiebreak_points=tiebreak_points, num_sets=num_sets)
    else:
        matches = stage.match_list

        for match in matches:
            simulate_a_match(match=match, stage_name=stage_name)

    st.success("✅ Zufällige Ergebnisse wurden erfolgreich simuliert und in die Eingabefelder eingetragen!")
