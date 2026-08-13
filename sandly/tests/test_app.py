import json
import pytest
import sys
import os
import pandas as pd

# Füge das Hauptverzeichnis zum Pfad hinzu, damit app.py importiert werden kann
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import calculate_ranking, get_final_ranking_list, get_all_final_matches, load_data

@pytest.fixture
def turnier_daten():
    """Lädt die Ergebnisse mit der App-Logik (inkl. Migration)."""
    # Simulate loading from disk
    data = load_data()
    
    # Reale Namen durch generische ersetzen (Sicherheitsvorgabe)
    if "A" in data["teams"]:
        for key in data["teams"]["A"]:
            data["teams"]["A"][key] = f"Team {key}"
    if "B" in data["teams"]:
        for key in data["teams"]["B"]:
            data["teams"]["B"][key] = f"Team {key}"
        
    return data

def test_gruppen_rangliste_berechnung(turnier_daten):
    """Testet, ob die Gruppenrangliste korrekt berechnet wird (Punkte, Differenz)."""
    schedule = turnier_daten["tournament_config"]["schedule"]
    df_a = calculate_ranking("A", turnier_daten["teams"]["A"], turnier_daten["group_matches"], schedule)
    df_b = calculate_ranking("B", turnier_daten["teams"]["B"], turnier_daten["group_matches"], schedule)
    
    # Es müssen 6 Teams pro Gruppe sein
    assert len(df_a) == 6
    assert len(df_b) == 6
    
    # Überprüfe Spalten (Mindestanforderung)
    expected_columns = ["Name", "Satzpunkte", "Punkte Diff"]
    for col in expected_columns:
        assert col in df_a.columns
    
    # Der Erstplatzierte muss mindestens so viele Punkte haben wie der Letztplatzierte
    assert df_a.iloc[0]["Satzpunkte"] >= df_a.iloc[-1]["Satzpunkte"]
    assert df_b.iloc[0]["Satzpunkte"] >= df_b.iloc[-1]["Satzpunkte"]
    
    # Sicherstellen, dass keine echten Namen auftauchen
    for team in df_a["Name"]:
        assert team.startswith("Team A")

def test_final_matches_generierung(turnier_daten):
    """Testet die dynamische Zuteilung der Finalspiele basierend auf den Vorrunden."""
    matches = get_all_final_matches(turnier_daten)
    
    # Y, Z, W, X, HF1, HF2, Fin_kl, Fin_gr, Platz 9/10, Platz 11/12 = 10 Spiele
    assert len(matches) == 10
    
    for match in matches:
        assert len(match) == 5 # title, info, t1, t2, m_id
        title, info, t1, t2, m_id = match
        
        # Stelle sicher, dass die Teams in den Matches generische Namen enthalten
        if "Gew" not in str(t1) and "Verl" not in str(t1) and t1 != "TBD":
            assert "Team" in str(t1) or t1 == "—"

def test_gesamtrangliste(turnier_daten):
    """Testet die finale Rangliste 1 bis 12."""
    final_ranks = get_final_ranking_list(turnier_daten)
    
    # Genau 12 Plätze
    assert len(final_ranks) == 12
    
    # Platz 1 bis 12 Formatierung (inklusive Emojis wie 🥇)
    assert final_ranks[0][0].startswith("1. Platz")
    assert final_ranks[-1][0].startswith("12. Platz")
    
    # Sicherstellen, dass die Ränge 5-8 keine echten Namen enthalten
    for rank_str, team_name in final_ranks:
        if team_name and team_name != "—" and "Gew" not in team_name:
            assert "Team" in team_name
