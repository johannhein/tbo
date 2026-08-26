from pathlib import Path
from typing import List
import streamlit as st
import pandas as pd

from config import ui_modus, format_modus, MATCH_MODE_TO_SETS
from config.constants import HIGHLIGHT_COLOR, EXPORT_DIR, NAME_PREROUND
from core.models import Group, Tournament, MatchStatus, Match
from db import load_tournament, get_all_tournament_names
from scoring import process_match_scores
from scoring.ranking import render_group_table
from utils import export_stage


def create_score_input(col: st.delta_generator.DeltaGenerator, default_pts: int | None, key: str, label: str = "", ) -> int:
    """
    Erstellt ein st.number_input für einen Punktestand.
    Gibt den Wert zurück.
    """
    with col:
        if default_pts is not None:
            value = default_pts
        else:
            value = 0

        return st.number_input(
            label,
            min_value=0,
            max_value=99,
            value=value,
            step=1,
            key=key,
            label_visibility="collapsed",
            format="%d",
        )


def render_match_header(num_sets: int):
    """Zeigt die Satz-Header an."""
    cols = st.columns([20, 5, 20, 55])
    with cols[3]:
        widths = []
        for _ in range(num_sets):
            widths.extend([1.5, 0.2, 0.5])
        hdr_cols = st.columns(widths)

        for j in range(num_sets):
            left = hdr_cols[j * 3]
            left.markdown(f"**Satz {j + 1}**", unsafe_allow_html=True)


def render_match_row(match: Match, num_sets: int, group: Group):
    """Zeigt ein einzelnes Match mit Teams und Sätzen an."""
    # Platzverhältnisse
    col1, col2, col3, col4 = st.columns([20, 5, 20, 55])

    with col1:
        st.markdown(f"<div style='display:flex; align-items:center; height:38px;'><strong>{match.t1}</strong></div>",
                    unsafe_allow_html=True,)
    with col2:
        st.markdown("<div style='display:flex; align-items:center; height:38px;'>vs.</div>", unsafe_allow_html=True,)
    with col3:
        st.markdown(f"<div style='display:flex; align-items:center; height:38px;'><strong>{match.t2}</strong></div>",
                    unsafe_allow_html=True,)
    with col4:
        widths = []
        for _ in range(num_sets):
            widths.extend([1, 0.2, 1])
        set_cols = st.columns(widths)

        scores = {}
        for j in range(num_sets):
            key_a = f"set_{match.id}_a{j}"
            key_b = f"set_{match.id}_b{j}"

            default_pts = None
            if match.sets and j in match.sets:
                default_pts = match.sets[j][0]

            p1 = create_score_input(col=set_cols[j * 3], default_pts=default_pts, key=key_a, label=f"Satz {j + 1}")
            with set_cols[j * 3 + 1]:
                st.markdown("<div style='display:flex; align-items:center; height:38px;'><strong>:</strong></div>",
                            unsafe_allow_html=True, )
            p2 = create_score_input(col=set_cols[j * 3 + 2], default_pts=default_pts, key=key_b, label=f"Satz {j + 1}")

            scores[j + 1] = (p1, p2)

        process_match_scores(match=match, scores=scores,)


def render_group_expander(group: Group):
    """Zeigt die Gruppe mit Matches und Tabelle an."""
    if not group.match_list:
        st.info("Keine Spiele generiert.")
        return

    sets = MATCH_MODE_TO_SETS.get(group.settings.modus, ["1. Satz"])
    num_sets = len(sets)

    with st.expander(f"🟦 Gruppe {group.name}", expanded=False):
        render_match_header(num_sets)

        for match in group.match_list:
            render_match_row(match=match, num_sets=num_sets, group=group)

        # Button: Ergebnisse speichern
        if st.button(f"✅ Ergebnisse für Gruppe {group.name} speichern", key=f"save_group_{group.name}"):
            for match in group.match_list:
                if match.status != MatchStatus.FINISHED:
                    match.status = MatchStatus.FINISHED
            st.success(f"✅ Ergebnisse für Gruppe {group.name} wurden gespeichert.")
            st.rerun()


def _match_to_simple_row(match):
    """Erzeugt ein dict mit den drei gewünschten Spalten."""
    return {
        "Nr.": match.id,
        "Team 1": match.t1,
        "Team 2": match.t2,
        "Schiedsrichter": match.ref or "-",
    }


def display_name(p: Path) -> str:
    """Wandelt den Pickle-Pfad in den lesbaren Namen um."""
    stem = p.stem.capitalize()
    return stem.replace("_", " ")


def highlight_team(selected_team, group: Group) -> None:
    """Highlight das ausgewählte Team in der Liste."""
    if selected_team:
        team_list = [str(t) for t in group.teams]
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
    """Highlight das ausgewählte Team in der Tabelle."""
    selected_team = st.session_state.get("selected_team")
    if selected_team is None:
        return [""] * len(row)

    styles = []
    for col_name, value in row.items():
        if value == selected_team and col_name in ["Team 1", "Team 2"]:
            styles.append(f"background-color: {HIGHLIGHT_COLOR}; color: #000000; font-weight: bold")
        else:
            styles.append("")
    return styles


def _display_group_info(group, col):
    """Zeigt Modus, Punkte und Tiebreak in einer Zeile an."""
    modus_ui = ui_modus(group.settings.modus)
    modus = format_modus(
        modus_ui=modus_ui,
        pts=group.settings.points,
        tiebreak=group.settings.tiebreak
    )
    st.markdown(f"**Modus: {modus}**")


def load_savestates(saved_tournament: Tournament, selected_tournament: str):
    """Lädt die Savestates."""
    groups_list = next(iter(saved_tournament.stages.values())).groups
    st.session_state["groups"] = {g.name: g for g in groups_list}
    st.session_state["tournament"] = saved_tournament
    st.session_state["tournament_loaded"] = True
    st.session_state["last_selected_tournament"] = selected_tournament


def initialize_tournament():
    """Lädt das ausgewählte Turnier, nur wenn sich die Auswahl geändert hat."""
    selected_tournament = st.session_state.get("selected_tournament")

    if st.session_state.get("tournament_loaded") and st.session_state.get("last_selected_tournament") == selected_tournament:
        return

    if selected_tournament is None or selected_tournament == "-- keine Auswahl --":
        st.session_state["tournament_loaded"] = False
        st.session_state["groups"] = {}
        st.session_state["tournament"] = None
        return

    options = get_all_tournament_names()
    if selected_tournament not in options:
        st.session_state["tournament_loaded"] = False
        st.session_state["groups"] = {}
        st.session_state["tournament"] = None
        return

    saved_tournament = load_tournament(selected_tournament)

    if saved_tournament is None:
        st.error("❗ Das Turnier konnte nicht geladen werden. Bitte prüfe die Datei.")
        st.session_state["tournament_loaded"] = False
        st.session_state["groups"] = {}
        st.session_state["tournament"] = None
        return

    load_savestates(saved_tournament, selected_tournament)


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
    """Plottet den Spielplan für die UI."""
    highlight_team(selected_team, group)

    if group.match_list:
        rows = [_match_to_simple_row(m) for m in group.match_list]
        df = pd.DataFrame(rows, columns=["Nr.", "Team 1", "Team 2", "Schiedsrichter"])

        styled_df = df.style.apply(highlight_team_in_schedule, axis=1)
        st.dataframe(styled_df, width="content", hide_index=True)
    else:
        st.info("Noch keine Spielpaarungen erzeugt.")


def tab_group_stage():
    st.header("🆕 Vorrunde")

    # ✅ Neue Tabs innerhalb von "Vorrunde"
    tabs = st.tabs(["📋 Übersicht", "📊 Ergebnisse", "📋 Zusammenfassung"])

    with tabs[0]:
        # --- Übersicht ---
        options = get_all_tournament_names()

        if not options:
            st.info("Bitte erst ein Turnier anlegen (Tab „⚙️ Neues Turnier“).")
            return

        cols = st.columns(4)

        with cols[0]:
            selected_tournament = st.selectbox(
                "Turnier auswählen",
                options=["-- keine Auswahl --"] + options,
                index=0,
                key="select_tournament"
            )
            st.session_state["selected_tournament"] = selected_tournament

        with cols[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Zurücksetzen", key="reset_button"):
                selected_tournament = st.session_state["selected_tournament"]
                saved_tournament = load_tournament(selected_tournament)

                if saved_tournament is None:
                    st.error("❌ Fehler beim Neuladen der Datei.")
                else:
                    load_savestates(saved_tournament, selected_tournament)

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

    with tabs[1]:
        st.header("📊 Ergebnisse eingeben")
        st.markdown("Noch nicht fertig. Geduldet euch.")

        if "tournament" not in st.session_state or not st.session_state["tournament_loaded"]:
            st.info("Bitte lade ein Turnier im Tab „Übersicht“.")
            st.stop()

        tournament = st.session_state["tournament"]
        stage = next(iter(tournament.stages.values()))
        groups = stage.groups

        # Gruppen paarweise nebeneinander darstellen
        for i in range(len(groups)):
            cols = st.columns(2)
            if i < len(groups):
                with cols[0]:
                    render_group_expander(group=groups[i])
                with cols[1]:
                    st.subheader(f"📋 Gruppentabelle: {groups[i].name}")
                    st.dataframe(groups[i].table, hide_index=True, width='content')
            st.markdown("---")

    with tabs[2]:
        # --- Zusammenfassung ---
        st.header("📋 Zusammenfassung")

        st.markdown("Geduldet euch ist doch schon in Arbeit.")

        # if "tournament" not in st.session_state or not st.session_state["tournament_loaded"]:
        #     st.info("Bitte lade ein Turnier im Tab „Übersicht“.")
        #     return
        #
        # tournament = st.session_state["tournament"]
        # stage = next(iter(tournament.stages.values()))
        # groups = stage.groups
        #
        # # Rangliste berechnen
        # ranking = calculate_ranking(groups)
        #
        # st.subheader("🏆 Rangliste")
        # df = pd.DataFrame(ranking)
        # st.dataframe(df, hide_index=True)
        #
        # st.subheader("📊 Statistiken")
        # total_matches = sum(len(group.match_list) for group in groups.values())
        # st.metric("Gesamtanzahl Spiele", total_matches)
        #
        # # Teams mit den meisten Sätzen
        # max_sets = max(r["Sätze"] for r in ranking)
        # top_teams = [r["Team"] for r in ranking if r["Sätze"] == max_sets]
        # st.metric("Team mit meisten Sätzen", ", ".join(top_teams))
        #
        # # Teams mit besten Punktdifferenz
        # max_diff = max(r["Punktdifferenz"] for r in ranking)
        # top_diff = [r["Team"] for r in ranking if r["Punktdifferenz"] == max_diff]
        # st.metric("Beste Punktdifferenz", ", ".join(top_diff))