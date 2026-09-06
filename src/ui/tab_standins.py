import pandas as pd
import streamlit as st

from core.models import StageType


def tab_standings():
    st.header("🏅 Endplatzierungen")

    if "tournament" not in st.session_state or not st.session_state["tournament_loaded"]:
        st.info("Bitte lade ein Turnier im Tab „Übersicht“.")
        return

    tournament = st.session_state["tournament"]
    n_teams = len(tournament.teams)

    rankings = []

    for stage in tournament.stages.values():
        if not stage.is_complete or not stage.standing:
            continue

        if stage.type == StageType.GROUP:
            for idx, team in enumerate(stage.table["Team"]):
                place = idx + stage.standing
                rankings.append((place, team))
        elif len(stage.teams) == 2:
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

    rankings.sort(key=lambda x: x[0])

    standings = {}
    for place, team in rankings:
        if place not in standings:
            standings[place] = team
        # else:
        #     st.warning(f"⚠️ Platz {place} bereits belegt: {standings[place]}")

    # Fülle Lücken
    for place in range(1, n_teams + 1):
        if place not in standings:
            standings[place] = "Nicht zugewiesen"

    # Erstelle DataFrame
    data = []
    for place in range(1, n_teams + 1):
        team = standings.get(place, "Nicht zugewiesen")
        data.append({"Platzierung": place, "Team": team})

    df = pd.DataFrame(data)

    # Zeige Tabelle
    st.dataframe(
        df,
        column_config={
            "Platzierung": st.column_config.NumberColumn(
                "Platzierung",
                width="small",
                format="%d"
            ),
            "Team": st.column_config.TextColumn(
                "Team",
                width="large"
            )
        },
        width='content',
        height="content",
        hide_index=True
    )