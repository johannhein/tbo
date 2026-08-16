import streamlit as st
import pandas as pd

from config.constants import HIGHLIGHT_COLOR
from core.models import Group
from services.mapping import ui_modus, format_modus
from services.persistence import load_tournament


def _match_to_simple_row(match):
    """Erzeugt ein dict mit den drei gewünschten Spalten."""
    return {
        "Nr.": match.id,
        "Team 1": match.t1,
        "Team 2": match.t2,
        "Schiedsrichter": match.ref or "-",
    }

def highlight_team(selected_team, group: Group) -> None:
    if selected_team:
        # Liste der Teams als Strings
        team_list = [str(t) for t in group.teams]
        # Markiere das ausgewählte Team
        highlighted_teams = [
            f'<span style="background-color: {HIGHLIGHT_COLOR}; padding: 0.1em 0.3em; border-radius: 4px; font-weight: bold;">{t}</span>'
            if t == selected_team else t
            for t in team_list
        ]
        teams_html = ", ".join(highlighted_teams)
        st.markdown(f"**Teams:** {teams_html}", unsafe_allow_html=True)
    else:
        # Standard: keine Hervorhebung
        st.markdown(f"**Teams:** {', '.join(str(t) for t in group.teams)}")

def highlight_team_in_schedule(row):
    selected_team = st.session_state.get("selected_team")
    if selected_team is None:
        return [""] * len(row)

    styles = []

    for col_name, value in row.items():
        # Prüfen, ob die aktuelle Zelle das gesuchte Team enthält
        if value == selected_team and col_name in ["Team 1", "Team 2"]:
            styles.append(f"background-color: {HIGHLIGHT_COLOR}; color: #000000; font-weight: bold")
        else:
            styles.append("")  # keine Formatierung
    return styles


def _display_group_info(group, col):
    """
    Zeigt in der übergebenen Streamlit-Spalte (col) die Basis-Infos einer Gruppe an.
    Modus, Punkte und Tiebreak werden in einer Zeile nebeneinander angezeigt.
    """
    modus_ui = ui_modus(group.settings.modus)

    modus = format_modus(
        modus_ui=modus_ui,
        pts=group.settings.points,
        tiebreak=group.settings.tiebreak
    )

    st.markdown(f"**Modus: {modus}**")


def tab_group_stage() -> None:
    st.header("🆕 Überblick Vorrunde")

    if not st.session_state["tournament_created"]:
        saved_tournament = load_tournament()
        if saved_tournament is not None:
            st.info("🔍 Ein gespeichertes Turnier wurde gefunden – wird automatisch geladen.")
            groups_list = next(iter(saved_tournament.stages.values())).groups
            st.session_state["groups"] = {group.name: group for group in groups_list}
            st.session_state["tournament_created"] = True
            st.session_state["test_tournament"] = saved_tournament
            st.rerun()
        else:
            st.info("Bitte erst ein Turnier anlegen (Tab „⚙️ Turnier einrichten“).")
        return

    groups = st.session_state["groups"]
    group_names = list(groups.keys())

    # 🔍 Alle Teams sammeln
    all_teams = set()
    for group in groups.values():
        for team in group.teams:
            all_teams.add(str(team))

    # 🎯 Auswahlbox
    selected_team = st.selectbox(
        "Team auswählen (für Hervorhebung)",
        options=["-- keine Auswahl --"] + sorted(all_teams),
        index=0,
        key="team_selector"
    )

    if selected_team != "-- keine Auswahl --":
        st.session_state["selected_team"] = selected_team
    else:
        st.session_state["selected_team"] = None

    # Loop über die Gruppen
    for i in range(0, len(group_names), 2):
        cols = st.columns(2)

        grp_name_1 = group_names[i]
        grp_1 = groups[grp_name_1]

        with cols[0]:
            if grp_1.assigned_courts:
                st.subheader(f"🟦 Gruppe {grp_name_1} Feld {', '.join(map(str, grp_1.assigned_courts))}")
            else:
                st.markdown(f"🟦 Gruppe {grp_name_1} noch kein Feld zugewiesen")

            _display_group_info(grp_1, cols[0])

            highlight_team(selected_team, grp_1)

            if grp_1.match_list:
                rows = [_match_to_simple_row(m) for m in grp_1.match_list]
                df = pd.DataFrame(rows, columns=["Nr.", "Team 1", "Team 2", "Schiedsrichter"])


                styled_df = df.style.apply(highlight_team_in_schedule, axis=1)
                st.dataframe(styled_df, width="content", hide_index=True)
            else:
                st.info("Noch keine Spielpaarungen erzeugt.")

        if i + 1 < len(group_names):
            grp_name_2 = group_names[i + 1]
            grp_2 = groups[grp_name_2]

            with cols[1]:
                if grp_2.assigned_courts:
                    st.subheader(f"🟦 Gruppe {grp_name_2} Feld {', '.join(map(str, grp_2.assigned_courts))}")
                else:
                    st.markdown(f"🟦 Gruppe {grp_name_2} noch kein Feld zugewiesen")

                _display_group_info(grp_2, cols[1])

                highlight_team(selected_team, grp_2)

                if grp_2.match_list:
                    rows = [_match_to_simple_row(m) for m in grp_2.match_list]
                    df = pd.DataFrame(rows, columns=["Nr.", "Team 1", "Team 2", "Schiedsrichter"])

                    styled_df = df.style.apply(highlight_team_in_schedule, axis=1)
                    st.dataframe(styled_df, width="content", hide_index=True)
                else:
                    st.info("Noch keine Spielpaarungen erzeugt.")
        else:
            with cols[1]:
                st.empty()