import pandas as pd
import streamlit as st


def tab_standings():
    st.header("🏅 Endplatzierungen")

    if "tournament" not in st.session_state or not st.session_state["tournament_loaded"]:
        st.info("Bitte lade ein Turnier im Tab „Übersicht“.")
        return

    tournament = st.session_state["tournament"]
    n_teams = len(tournament.teams)


    standings = tournament.standings

    data = []
    for place in range(1, n_teams + 1):
        team = standings.get(place, "Nicht zugewiesen")
        data.append({"Platzierung": place, "Team": team})

    df = pd.DataFrame(data)

    column_config = {
        "Platzierung": st.column_config.NumberColumn(
            "Platzierung",
            width="compact",  # ✅ Nur so breit wie nötig
            format="%d"
        ),
        "Team": st.column_config.TextColumn(
            "Team",
            width="compact"  # ✅ Nimmt den Rest
        )
    }

    # st.dataframe(df, width='stretch', hide_index=True, column_config=column_config)
    st.dataframe(
        df,
        column_config={
            "Platzierung": st.column_config.NumberColumn(
                "Platzierung",
                width="small",  # ✅ Nur so breit wie nötig
                format="%d"
            ),
            "Team": st.column_config.TextColumn(
                "Team",
                width="large"  # ✅ Nimmt den Rest
            )
        },
        width='content',
        height="content",
        hide_index=True
    )
