from typing import List, Tuple
import pandas as pd
import streamlit as st

from core.models import StageType, Stage


def nongroup_rankings(stage: Stage, rankings: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
    if len(stage.teams) == 2:
        winner = stage.winner[0] if stage.winner else None
        loser = stage.loser[0] if stage.loser else None

        if winner:
            rankings.append((stage.standing, winner))
        if loser:
            rankings.append((stage.standing + 1, loser))
    else:
        place = stage.standing
        for match in stage.match_list:
            rankings.append((place, match.winner))
            rankings.append((place + 1, match.loser))
            place = place + 2

    return rankings


def group_rankings(stage: Stage, rankings: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
    place = stage.standing
    for group in stage.groups:
        if group.is_ready:
            for team in group.table["Team"]:
                rankings.append((place, team))
                place = place + 1
        else:
            place = place + len(group.teams)

    return rankings


def tab_standings():
    st.header("🏅 Endplatzierungen")

    if "tournament" not in st.session_state or not st.session_state["tournament_loaded"]:
        st.info("Bitte lade ein Turnier im Tab „Übersicht“.")
        return

    tournament = st.session_state["tournament"]
    n_teams = len(tournament.teams)

    rankings = []

    for stage in tournament.stages.values():
        if not stage.standing:
            continue
        if stage.type == StageType.GROUP:
            rankings = group_rankings(stage=stage, rankings=rankings)
        elif not stage.is_ready:
            continue
        else:
            rankings = nongroup_rankings(stage=stage, rankings=rankings)

    rankings.sort(key=lambda x: x[0])

    standings = {}
    for place, team in rankings:
        if place not in standings:
            standings[place] = team
        # else:
        #     st.warning(f"⚠️ Platz {place} bereits belegt: {standings[place]}")

    # # Fülle Lücken
    # for place in range(1, n_teams + 1):
    #     if place not in standings:
    #         standings[place] = ""

    # Erstelle DataFrame
    data = []
    for place in range(1, n_teams + 1):
        team = standings.get(place, "")
        data.append({"Platzierung": place, "Team": team})

    df = pd.DataFrame(data)

    df["Teilnahme"] = False
    df["Urkunde"] = False

    # Spalten‑Konfiguration für den Editor
    columns_config = {
        "Platzierung": st.column_config.NumberColumn(
            label="Platzierung",
            width="small",
            format="%d",
            disabled=True,
        ),
        "Team": st.column_config.TextColumn(
            "Team",
            width="large",
            disabled=True,
        ),
        "Teilnahme": st.column_config.CheckboxColumn(
            label="Weg?",
            help="Ist das Team schon weg?",
            width="small",
        ),
        "Urkunde": st.column_config.CheckboxColumn(
            label="Urkunde",
            help="Wurde die Urkunde schon ausgegeben?",
            width="small",
        ),
    }

    # Editierbare Tabelle anzeigen
    df_edited = st.data_editor(
        df,
        column_config=columns_config,
        width='content',
        height="content",
        hide_index=True,
        key="ranking_table_editor",
    )

    # if st.button("Änderungen übernehmen"):
    #     # Zeige nur die Zeilen, bei denen sich etwas geändert hat
    #     changed = df_edited[
    #         (df_edited["Teilnahme"] != df["Teilnahme"]) |
    #         (df_edited["Urkunde"] != df["Urkunde"])
    #         ]
    #     st.write("Geänderte Zeilen:", changed)
