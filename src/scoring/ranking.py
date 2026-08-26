import pandas as pd
import streamlit as st

from core import Group

def render_group_table(group: Group):
    """Zeigt die Gruppentabelle an."""
    if not group.match_list:
        st.info("Keine Spiele generiert.")
        return

    # Erstelle eine Liste für die Tabelle
    table_data = []

    # Zähle die Ergebnisse für jedes Team
    team_stats = {}

    for match in group.match_list:
        t1, t2 = match.t1, match.t2

        # Initialisiere Statistiken
        for team, name in [(t1, t1), (t2, t2)]:
            if name not in team_stats:
                team_stats[name] = {
                    "Spiele": 0,
                    "Siege": 0,
                    "Niederlagen": 0,
                    "Punkte": 0,
                    "Sätze": 0,
                    "Sätze-Verhältnis": tuple,
                    "Kleine-Punkte": 0,
                }

        # Prüfe, ob match.score existiert
        if match.score is None:
            # Keine Sätze gespielt → keine Punkte
            team_stats[t1]["Punkte"] += 0
            team_stats[t2]["Punkte"] += 0
        else:
            # Aktualisiere Statistiken
            team_stats[t1]["Spiele"] += 1
            team_stats[t2]["Spiele"] += 1
            team_stats[t1]["Kleine-Punkte"] += match.points[0] - match.points[1]
            team_stats[t2]["Kleine-Punkte"] += match.points[1] - match.points[0]
            # Es gibt Sätze → score ist (t1_won, t2_won)
            if match.score[0] > match.score[1]:
                team_stats[t1]["Siege"] += 1
                team_stats[t2]["Niederlagen"] += 1
            else:
                team_stats[t1]["Niederlagen"] += 1
                team_stats[t2]["Siege"] += 1

            # Punkte: 3 für Sieg, 1 für Niederlage
            if match.score[0] > match.score[1]:
                team_stats[t1]["Punkte"] += 2
            elif match.score[1] > match.score[0]:
                team_stats[t2]["Punkte"] += 2
            elif match.score[0] == match.score[1]:
                team_stats[t1]["Punkte"] += 1
                team_stats[t2]["Punkte"] += 1

        # Sätze
        if match.score is not None:
            team_stats[t1]["Sätze"] += match.score[0]
            team_stats[t2]["Sätze"] += match.score[1]

    # Berechne Sätze-Verhältnis
    for name in team_stats:
        sets_won = team_stats[name]["Sätze"]
        sets_lost = 0

        for match in group.match_list:
            if name not in (match.t1, match.t2):
                continue

            if match.score is None:
                continue

            if match.t1 == name:
                sets_lost += match.score[1]
            else:
                sets_lost += match.score[0]

        team_stats[name]["Sätze-Verhältnis"] = sets_won, sets_lost


    # Sortiere nach Punkten, dann nach Sätzen
    sorted_teams = sorted(
        team_stats.items(),
        key=lambda x: (x[1]["Punkte"], x[1]["Sätze-Verhältnis"][0] - x[1]["Sätze-Verhältnis"][1], x[1]["Kleine-Punkte"]),
        reverse=True,
    )

    # Erstelle Tabelle
    table_data = []
    for i, (name, stats) in enumerate(sorted_teams):
        table_data.append({
            "Rang": i + 1,
            "Team": name,
            "Spiele": stats["Spiele"],
            "Sätze": f"{stats['Sätze-Verhältnis'][0]}:{stats['Sätze-Verhältnis'][1]}",
            "Kleine Punkte": stats["Kleine-Punkte"],
            "Punkte": stats["Punkte"],
        })

    # Zeige Tabelle an
    st.subheader(f"📋 Gruppentabelle: {group.name}")
    st.dataframe(
        pd.DataFrame(table_data),
        hide_index=True,
        width='content',
    )
