from typing import Dict
import streamlit as st

from config import UI_TO_MATCH_MODE, MATCH_MODE_TO_UI
from config.constants import DEFAULT_TIEBREAK, DEFAULT_POINTS
from core import Stage
from core.models import StageType, MatchSettings
from utils import match_making_direct, match_making_cross


def _init_session_state():
    """Initialisiert Session-State für die Rundenkonfiguration."""
    if "next_round_generated" not in st.session_state:
        st.session_state.next_round_generated = False
    if "next_round_matches" not in st.session_state:
        st.session_state.next_round_matches = []
    if "num_rounds" not in st.session_state:
        st.session_state.num_rounds = 1

    if "tournament" not in st.session_state:
        st.session_state.tournament = None


def init_session_state_keys(keys: Dict):
    """Initialisiert alle session_state-Keys."""
    for k in keys.values():
        if k not in st.session_state:
            if k == keys["game_modes"]:
                st.session_state[k] = {}
            elif k == keys["teams_list"] or k == keys["teams1_list"] or k == keys["teams2_list"]:
                st.session_state[k] = []
            elif k == keys["courts"]:
                st.session_state[k] = []
            elif k == keys["stage_name"]:
                st.session_state[k] = "Zwischenrunde"
            elif k in keys["tiebreak_complete"]:
                st.session_state[k] = DEFAULT_TIEBREAK
            elif k in keys["points_complete"]:
                st.session_state[k] = DEFAULT_POINTS
            elif k in keys["stage_ready"]:
                st.session_state[k] = False
            else:
                st.session_state[k] = None


def render_stage_preview(stage: Stage):
    """
    Zeigt eine aufklappbare Vorschau der aktuellen Runde an.

    """
    stage_name = stage.id
    if not stage_name:
        st.warning("Kein Rundenname gesetzt.")
        return

    if not stage:
        st.warning("Keine Runde vorhanden.")
        return

    with st.expander(f"📋 Vorschau: Runde {stage_name}"):
        st.write(f"**`{stage.id}`**")
        match_count = len(stage.match_list) if stage.match_list else 0
        st.write(f"**Anzahl an Spielen:** {match_count}")

        if stage.match_list:
            st.write("### Spiele:")
            for match in stage.match_list:
                st.markdown(f"""
                - **Spiel {match.id}**  auf Feld {match.court} **{match.t1}** vs **{match.t2}** 
                Schiedsrichter: {match.ref or '—'}
                """)
        else:
            st.write("Keine Matches erstellt.")


def validate_tournament() -> bool:
    """Prüft, ob ein Turnier im Session-State vorhanden ist."""
    if "tournament" not in st.session_state or st.session_state.tournament is None:
        st.error("❌ Kein Turnier geladen! Bitte erst ein Turnier erstellen.")
        return False
    return True


def render_round_controls():
    """Zeigt den Button zum Hinzufügen neuer Runden an."""
    if st.button("Weitere Runde einstellen", key="add_round"):
        st.session_state.num_rounds += 1


def render_round_configs(tournament):
    """Erstellt dynamisch die Runden-Configs basierend auf num_rounds."""
    st.session_state.next_round_matches = []
    for i in range(st.session_state.num_rounds):
        render_round_config(i, tournament)


def render_round_config(round_idx: int, tournament):
    """Zeigt ein einzelnes Runden-Setup mit dynamischen Keys an."""
    st.subheader(f"Runde {round_idx + 1}")

    # Dynamische Keys
    keys = {
        "round_type": f"round_{round_idx}_type",
        "opponent_logic_choice": f"round_{round_idx}_opponent_logic",
        "stage_direct": f"round_{round_idx}_stage_direct",
        "place_direct": f"round_{round_idx}_place_direct",
        "stage_t1": f"round_{round_idx}_stage_t1",
        "place_t1": f"round_{round_idx}_place_t1",
        "stage_t2": f"round_{round_idx}_stage_t2",
        "place_t2": f"round_{round_idx}_place_t2",
        "courts": f"courts_{round_idx}",
        "teams_list": f"teams_list_{round_idx}",
        "teams1_list": f"teams1_list{round_idx}",
        "teams2_list": f"teams2_list{round_idx}",
        "stage_name": f"stage_name_{round_idx}",
        "points_complete": f"points_complete_{round_idx}",
        "modus_complete": f"modus_complete_{round_idx}",
        "tiebreak_complete": f"tiebreak_complete_{round_idx}",
        "points_incomplete": f"points_incomplete_{round_idx}",
        "modus_incomplete": f"modus_incomplete_{round_idx}",
        "tiebreak_incomplete": f"tiebreak_incomplete_{round_idx}",
        "game_modes": f"game_modes_{round_idx}",
        "stage": f"stage{round_idx}",
        "stage_ready": f"stage_ready{round_idx}",
    }

    init_session_state_keys(keys=keys)

    # UI: Auswahl
    cols = st.columns(5)

    with cols[0]:
        round_type = st.selectbox(
            "Modus",
            options=["Überkreuzspiele", "Direkte Spiele", "Platzierungsspiele", "Gruppenphase"],
            key=keys["round_type"]
        )

        courts = st.multiselect(
            "Verfügbare Felder",
            options=tournament.courts or [1, 2],
            key=keys["courts"],
            placeholder="Verfügbare Felder für die Runde wählen …"
        )

    with cols[1]:
        if round_type == "Überkreuzspiele":
            opponent_logic_choice = st.selectbox(
                "Gegner-Auswahl",
                options=["x. Plätze vs. y. Platz", "Platz x bis y aus Gesamtranking"],
                key=keys["opponent_logic_choice"]
            )
            stage_direct = st.session_state.get(keys["stage_direct"], None)
            place_direct = st.session_state.get(keys["place_direct"], None)
        elif round_type == "Direkte Spiele":
            stage_direct = st.selectbox(
                "Aus welcher Runde sollen die Teams kommen?",
                options=list(tournament.stages.keys()),
                key=keys["stage_direct"]
            )
            place_direct = st.session_state.get(keys["place_direct"], None)
        else:
            opponent_logic_choice = st.session_state.get(keys["opponent_logic_choice"], None)
            stage_direct = st.session_state.get(keys["stage_direct"], None)
            place_direct = st.session_state.get(keys["place_direct"], None)

        stage_name = st.text_input(
            label="Name der Runde:",
            placeholder="Gib deinen Namen ein...",
            key=keys["stage_name"]
        )

    with cols[2]:
        if stage_direct is not None and stage_direct in tournament.stages:
            stage = tournament.stages[stage_direct]
            place_keys = list(stage.placement_tables.keys())
            place_direct = st.selectbox(
                "Welche Plätze sollen gegeneinander spielen",
                options=place_keys,
                key=keys["place_direct"]
            )

            if place_direct in place_keys:
                list_teams = stage.placement_tables[place_direct].sort_values(by=["Gruppe"])["Team"].tolist()
                if len(list_teams) % 2 != 0:
                    st.warning("Die ausgewählte Anzahl an Teams ist ungerade.")
                st.session_state[keys["teams_list"]] = list_teams
            else:
                st.session_state[keys["teams_list"]] = []
        else:
            st.session_state[keys["teams_list"]] = []

        if st.session_state.get(keys["opponent_logic_choice"]) == "x. Plätze vs. y. Platz":
            stage_t1 = st.selectbox(
                "Aus welcher Runde kommt Team 1",
                options=list(tournament.stages.keys()),
                key=keys["stage_t1"]
            )
            if stage_t1 is not None and stage_t1 in tournament.stages:
                place_keys = list(tournament.stages[stage_t1].placement_tables.keys())
                place_t1 = st.selectbox(
                    "Platz Team 1",
                    options=place_keys,
                    key=keys["place_t1"]
                )
                if place_t1 in place_keys:
                    list_teams1 = tournament.stages[stage_t1].placement_tables[place_t1].sort_values(by=["Gruppe"])["Team"].tolist()
                    st.session_state[keys["teams1_list"]] = list_teams1
            else:
                place_t1 = None

    with cols[3]:
        if st.session_state.get(keys["opponent_logic_choice"]) == "x. Plätze vs. y. Platz":
            stage_t2 = st.selectbox(
                "Aus welcher Runde kommt Team 2",
                options=list(tournament.stages.keys()),
                key=keys["stage_t2"]
            )
            if stage_t2 is not None and stage_t2 in tournament.stages:
                place_keys = list(tournament.stages[stage_t2].placement_tables.keys())
                place_t2 = st.selectbox(
                    "Platz Team 2",
                    options=place_keys,
                    key=keys["place_t2"]
                )
                if place_t2 in place_keys:
                    list_teams2 = tournament.stages[stage_t2].placement_tables[place_t2].sort_values(by=["Gruppe"])["Team"].tolist()
                    st.session_state[keys["teams2_list"]] = list_teams2
            else:
                place_t2 = None

    cols = st.columns(5)
    with cols[0]:
        sets_complete = st.selectbox(
            "Welcher Modus soll gespielt werden",
            options=list(MATCH_MODE_TO_UI.values()),
            key=keys["modus_complete"],
        )
    with cols[1]:
        points_complete = st.number_input(
            "Punkte",
            min_value=1,
            max_value=99,
            step=1,
            key=keys["points_complete"],
        )
    with cols[2]:
        if sets_complete in ["2 Gewinnsätze", "3 Gewinnsätze"]:
            tiebreak_complete = st.number_input(
                "Tiebreak‑Punkte",
                min_value=1,
                max_value=99,
                step=1,
                key=keys["tiebreak_complete"],
            )
        else:
            tiebreak_complete = None

        if keys["game_modes"] not in st.session_state:
            st.session_state[keys["game_modes"]] = {}

        if sets_complete:
            st.session_state[keys["game_modes"]]["complete"] = {
                "modus": UI_TO_MATCH_MODE[sets_complete],
                "points": points_complete,
                "tiebreak": tiebreak_complete,
            }

    with cols[4]:
        st.write("")
        if st.button(f"✅ Runde bestätigen"):
            stage_name = st.session_state[keys["stage_name"]]
            teams = st.session_state[keys["teams_list"]]
            if round_type == "Gruppenphase":
                stage_typ: StageType = StageType.GROUP
            else:
                stage_typ: StageType = StageType.NONGROUP
                match_settings: MatchSettings = st.session_state[keys["game_modes"]]["complete"]
            if round_type == "Direkte Spiele":
                match_list = match_making_direct(teams=teams, courts=courts, settings=match_settings)
            elif round_type == "Überkreuzspiele":
                match_list = match_making_cross(teams_1=list_teams1, teams_2=list_teams2, courts=courts, settings=match_settings)
            stage = Stage(id=stage_name, type=stage_typ, teams=teams, match_list=match_list)
            st.session_state[keys["stage"]] = stage
            st.session_state[keys["stage_ready"]] = True
            tournament.stages[stage_name] = Stage(id=stage_name, type=stage_typ, teams=teams)

            st.success(f"✅ Runde '{stage_name}' wurde erstellt.")

    if st.session_state[keys["stage_ready"]]:
        render_stage_preview(stage=stage)


# --- 7. Button: Runden generieren ---
def render_round_generation(tournament):
    """Zeigt den Button zum Generieren der Runden an."""
    if st.button("Runden generieren", key="generate_rounds"):
        st.session_state.next_round_generated = True
        st.success(f"✅ {len(st.session_state.next_round_matches)} Runden wurden konfiguriert.")
        print(tournament.stages.keys())


def tab_new_round():
    st.header("Nächste Runde Konfigurator")

    # Zustand initialisieren
    _init_session_state()

    # Prüfe, ob Turnier geladen ist
    if not validate_tournament():
        return

    tournament = st.session_state["tournament"]

    # Steuere Runden-UI
    render_round_configs(tournament)
    render_round_controls()
    render_round_generation(tournament)