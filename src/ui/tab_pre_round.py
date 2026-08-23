from pathlib import Path
from typing import List
import streamlit as st
import pandas as pd

from config.constants import HIGHLIGHT_COLOR, PICKLE_DIR, EXPORT_DIR, NAME_PREROUND
from core.models import Group, Tournament
from utils.export_schedule import export_stage
from utils.mapping import ui_modus, format_modus
from utils.path import list_files_with_suffix
from utils.persistence import load_pickle


def _match_to_simple_row(match):
    """Erzeugt ein dict mit den drei gewünschten Spalten."""
    return {
        "Nr.": match.id,
        "Team 1": match.t1,
        "Team 2": match.t2,
        "Schiedsrichter": match.ref or "-",
    }

def display_name(p: Path) -> str:
    """ Wandelt den Pickle Pfad in den lesbaren Namen um."""
    stem = p.stem.capitalize()
    return stem.replace("_", " ")

def highlight_team(selected_team, group: Group) -> None:
    """ Highlight the selected team in the text."""
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
        st.markdown(f"**Teams:** {', '.join(str(t) for t in group.teams)}")

def highlight_team_in_schedule(row):
    """ Highlight the selected team in the table."""
    selected_team = st.session_state.get("selected_team")
    if selected_team is None:
        return [""] * len(row)

    styles = []

    for col_name, value in row.items():
        # Prüfen, ob die aktuelle Zelle das gesuchte Team enthält
        if value == selected_team and col_name in ["Team 1", "Team 2"]:
            styles.append(f"background-color: {HIGHLIGHT_COLOR}; color: #000000; font-weight: bold")
        else:
            styles.append("")
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

def load_savestates(saved_tournament: Tournament, selected_pkl: str):
    """Lädt die Pickle-Datei und legt die Savestates an."""
    groups_list = next(iter(saved_tournament.stages.values())).groups
    st.session_state["groups"] = {g.name: g for g in groups_list}
    st.session_state["tournament"] = saved_tournament
    st.session_state["tournament_loaded"] = True
    st.session_state["last_selected_pkl"] = selected_pkl  # Speichere letzte Auswahl

def initialize_tournament():
    """Lädt das ausgewählte Turnier, nur wenn sich die Auswahl geändert hat."""
    selected_pkl = st.session_state.get("selected_pkl")

    # Wenn bereits geladen und die Auswahl gleich bleibt → überspringen
    if st.session_state.get("tournament_loaded") and st.session_state.get("last_selected_pkl") == selected_pkl:
        return

    # Wenn keine Auswahl → zurück
    if selected_pkl is None or selected_pkl == "-- keine Auswahl --":
        st.session_state["tournament_loaded"] = False
        st.session_state["groups"] = {}
        st.session_state["tournament"] = None
        return

    # Lade die Datei
    options = list_files_with_suffix(folder=PICKLE_DIR, suffix=".pkl")
    if selected_pkl not in options:
        st.session_state["tournament_loaded"] = False
        st.session_state["groups"] = {}
        st.session_state["tournament"] = None
        return

    saved_tournament = load_pickle(selected_pkl)

    if saved_tournament is None:
        st.error("❗ Das Turnier konnte nicht geladen werden. Bitte prüfe die Datei.")
        st.session_state["tournament_loaded"] = False
        st.session_state["groups"] = {}
        st.session_state["tournament"] = None
        return

    load_savestates(saved_tournament, selected_pkl)


def trade_teams(team_a: str, team_b: str):
    """Vertauscht die Positionen von 2 Teams."""
    group_a = group_b = None
    group_a_name = group_b_name = None

    for name, grp in st.session_state["groups"].items():
        team_strs = [str(t) for t in grp.teams]
        if team_a in team_strs:
            group_a, group_a_name = grp, name
        if team_b in team_strs:
            group_b, group_b_name = grp, name

    if not group_a or not group_b:
        st.error("Eines der Teams wurde in keiner Gruppe gefunden.")
        st.stop()

    idx_a = [str(t) for t in group_a.teams].index(team_a)
    idx_b = [str(t) for t in group_b.teams].index(team_b)

    group_a.teams[idx_a], group_b.teams[idx_b] = group_b.teams[idx_b], group_a.teams[idx_a]

    for grp in (group_a, group_b):
        if grp.match_list:
            first_id = grp.match_list[0].id
            grp.match_list = None
            grp.build_matches_from_schema(first_id)

    st.session_state["groups"][group_a_name] = group_a
    st.session_state["groups"][group_b_name] = group_b


def delay_teams(delayed_teams: List[str]):
    """Gibt verspäteten Teams den spätesten Zeitslots."""
    for group_name, group in st.session_state["groups"].items():
        team_list = [str(t) for t in group.teams]
        team_set = set(team_list)

        for team in delayed_teams:
            if team in team_set:
                last_pos = len(team_list) - 1
                if team_list[last_pos] != team:
                    team_idx = team_list.index(team)
                    team_list[team_idx], team_list[last_pos] = team_list[last_pos], team_list[team_idx]
                    group.teams = [int(t) if t.isdigit() else t for t in team_list]
                    match_id = group.match_list[0].id
                    group.match_list = None
                    group.build_matches_from_schema(match_id)
                    st.session_state["groups"][group_name] = group
                else:
                    st.info(f"✅ Team '{team}' ist bereits an letzter Position in Gruppe '{group_name}'.")


def plot_schedule(group: Group, selected_team: str):
    highlight_team(selected_team, group)

    if group.match_list:
        rows = [_match_to_simple_row(m) for m in group.match_list]
        df = pd.DataFrame(rows, columns=["Nr.", "Team 1", "Team 2", "Schiedsrichter"])

        styled_df = df.style.apply(highlight_team_in_schedule, axis=1)
        st.dataframe(styled_df, width="content", hide_index=True)
    else:
        st.info("Noch keine Spielpaarungen erzeugt.")


def tab_group_stage() -> None:
    st.header("🆕 Überblick Vorrunde")
    options = list_files_with_suffix(folder=PICKLE_DIR, suffix=".pkl")

    if not options:
        st.info("Bitte erst ein Turnier anlegen (Tab „⚙️ Turnier einrichten“).")
        return

    cols = st.columns(4)

    with cols[0]:
        selected_pkl = st.selectbox(
            "Turnier auswählen",
            options=["-- keine Auswahl --"] + options,
            index=0,
            format_func=lambda x: x if isinstance(x, str) else display_name(x),
            key="select_tournament"
        )

        st.session_state["selected_pkl"] = selected_pkl

    with cols[1]:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Zurücksetzen", key="reset_button"):
            selected_pkl = st.session_state["selected_pkl"]
            saved_tournament = load_pickle(selected_pkl)

            if saved_tournament is None:
                st.error("❌ Fehler beim Neuladen der Datei.")
            else:
                load_savestates(saved_tournament, selected_pkl)

    initialize_tournament()

    if not st.session_state.get("tournament_loaded"):
        st.info("Kein Turnier geladen.")
        return

    group_names = list(st.session_state["groups"].keys())
    all_teams = set()
    for group in st.session_state["groups"].values():
        for team in group.teams:
            all_teams.add(str(team))

    cols = st.columns(4)

    with cols[0]:
        team_a = st.selectbox(
            "Team A",
            options=["-- wähle Team A --"] + sorted(all_teams),
            key="team_a"
        )

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

    with cols[1]:
        team_b = st.selectbox(
            "Team B",
            options=["-- wähle Team B --"] + sorted(all_teams),
            key="team_b"
        )

        delayed_teams = st.multiselect(
            "Welche Teams kommen später?",
            options=sorted(all_teams),
            key="team_delayed",
            placeholder="Bitte verspätete Teams auswählen …"
        )

    with cols[2]:
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Teams tauschen", key="swap_button"):
            if team_a == "-- wähle Team A --" or team_b == "-- wähle Team B --":
                st.warning("Bitte wähle beide Teams aus.")
                st.stop()
            if team_a == team_b:
                st.warning("Beide Teams sind gleich. Kein Tausch möglich.")
                st.stop()

            trade_teams(team_a, team_b)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Verspätete Teams", key="delay_button"):
            if delayed_teams:
                delay_teams(delayed_teams)

    # Zeige Gruppen an
    for i in range(0, len(group_names), 2):
        cols = st.columns(2)

        grp_name_1 = group_names[i]
        grp_1 = st.session_state["groups"][grp_name_1]

        with cols[0]:
            if grp_1.assigned_courts:
                st.subheader(f"🟦 Gruppe {grp_name_1} Feld {', '.join(map(str, grp_1.assigned_courts))}")
            else:
                st.markdown(f"🟦 Gruppe {grp_name_1} noch kein Feld zugewiesen")

            _display_group_info(grp_1, cols[0])

            plot_schedule(grp_1, selected_team)

        if i + 1 < len(group_names):
            grp_name_2 = group_names[i + 1]
            grp_2 = st.session_state["groups"][grp_name_2]

            with cols[1]:
                if grp_2.assigned_courts:
                    st.subheader(f"🟦 Gruppe {grp_name_2} Feld {', '.join(map(str, grp_2.assigned_courts))}")
                else:
                    st.markdown(f"🟦 Gruppe {grp_name_2} noch kein Feld zugewiesen")

                _display_group_info(grp_2, cols[1])

                plot_schedule(grp_2, selected_team)
        else:
            with cols[1]:
                st.empty()

    if st.button("Spielprotokolle generieren", key="create_protocols", type="primary"):
        stage_name = NAME_PREROUND
        export_stage(tournament=st.session_state["tournament"], stage_id=stage_name)
        stage = stage_name.lower().replace(" ", "_")
        path = EXPORT_DIR.resolve() / st.session_state["tournament"].type.lower() / stage
        st.success(f"✅ Die Protokolle wurden in dem Ordner {path} gespeichert.")
