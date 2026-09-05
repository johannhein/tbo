from typing import List
import streamlit as st

from config import MATCH_MODE_TO_SETS
from core.models import StageType, Group, MatchStatus, Match
from scoring.results import simulate_random_results, process_match_scores


def create_score_input(col: st.delta_generator.DeltaGenerator, default_pts: int | None, key: str, label: str = "") -> int:
    """
    Erstellt ein st.number_input für einen Punktestand.
    Gibt den Wert zurück.
    """
    with col:
        return st.number_input(
            label,
            min_value=0,
            max_value=99,
            # value=value
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


def render_match_row(match: Match, num_sets: int, stage_name: str):
    """Zeigt ein einzelnes Match mit Teams und Sätzen an."""
    # todo problem wenn ein Satz zu 0 endet fixen
    # siehe create_score_input mit einbeziehen
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
            key_a = f"{stage_name}_set_{match.id}_a{j}"
            key_b = f"{stage_name}_set_{match.id}_b{j}"

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


def render_group_expander(group: Group, stage_name: str):
    """Zeigt die Gruppe mit Matches und Tabelle an."""
    if not group.match_list:
        st.info("Keine Spiele generiert.")
        return

    sets = MATCH_MODE_TO_SETS.get(group.settings.modus, ["1. Satz"])
    num_sets = len(sets)

    with st.expander(f"🟦 Gruppe {group.name}", expanded=True):
        render_match_header(num_sets)

        for match in group.match_list:
            render_match_row(match=match, num_sets=num_sets, stage_name=stage_name)

        if st.button(f"✅ Ergebnisse für Gruppe {group.name} speichern", key=f"save_group_{stage_name}_{group.name}"):
            for match in group.match_list:
                if match.status != MatchStatus.FINISHED:
                    match.status = MatchStatus.FINISHED
            st.success(f"✅ Ergebnisse für Gruppe {group.name} wurden gespeichert.")
            st.rerun()


def render_matches(matches: List[Match], stage_name: str):

    sets = MATCH_MODE_TO_SETS.get(matches[0].settings.modus, ["1. Satz"])
    num_sets = len(sets)

    render_match_header(num_sets)
    for match in matches:
        render_match_row(match=match, num_sets=num_sets, stage_name=stage_name)

    if st.button("✅ Ergebnisse für Gruppe die Runde speichern", key=f"save_round_{stage_name}"):
        for match in matches:
            if match.status != MatchStatus.FINISHED:
                match.status = MatchStatus.FINISHED
        st.success("✅ Ergebnisse für die Runde wurden gespeichert.")
        st.rerun()


def render_groups(groups: List[Group], stage_name: str):
    for i in range(len(groups)):
        cols = st.columns(2)
        if i < len(groups):
            with cols[0]:
                group = groups[i]
                render_group_expander(group=group, stage_name=stage_name)
            with cols[1]:
                st.subheader(f"📋 Gruppentabelle: {group.name}")
                st.dataframe(group.table, hide_index=True, width='content')
        st.markdown("---")


def tab_results(stage_name: str):
    if "tournament" not in st.session_state or not st.session_state["tournament_loaded"]:
        st.info("Bitte lade ein Turnier im Tab „Übersicht“.")
        return

    st.header("📊 Ergebnisse eingeben")
    tournament = st.session_state["tournament"]

    if st.button("🎲 Zufällige Ergebnisse simulieren", key=f"simulate_results_{stage_name}", type="secondary"):
        st.info("🎲 Simuliere zufällige Ergebnisse für alle Gruppen...")

        simulate_random_results(tournament)
        st.rerun()

    if stage_name in tournament.stages:
        stage = tournament.stages[stage_name]
        if stage.type == StageType.GROUP:
            render_groups(stage.groups, stage_name)
        else:
            render_matches(stage.match_list, stage_name)
