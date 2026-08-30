import streamlit as st

from core import Stage
from core.models import StageType


# --- 2. Zustand initialisieren ---
def _init_session_state():
    """Initialisiert Session-State für die Rundenkonfiguration."""
    if "next_round_generated" not in st.session_state:
        st.session_state.next_round_generated = False
    if "next_round_matches" not in st.session_state:
        st.session_state.next_round_matches = []
    if "num_rounds" not in st.session_state:
        st.session_state.num_rounds = 1


# --- 3. Prüfe, ob Turnier geladen ist ---
def validate_tournament() -> bool:
    """Prüft, ob ein Turnier im Session-State vorhanden ist."""
    if "tournament" not in st.session_state:
        st.error("❌ Kein Turnier geladen! Bitte erst ein Turnier erstellen.")
        return False
    return True


# --- 4. Button: Weitere Runde hinzufügen ---
def render_round_controls():
    """Zeigt den Button zum Hinzufügen neuer Runden an."""
    if st.button("Weitere Runde einstellen", key="add_round"):
        st.session_state.num_rounds += 1


# --- 5. Zeige alle Runden-Configs an ---
def render_round_configs(tournament):
    """Erstellt dynamisch die Runden-Configs basierend auf num_rounds."""
    st.session_state.next_round_matches = []
    for i in range(st.session_state.num_rounds):
        config = render_round_config(i, tournament)
        st.session_state.next_round_matches.append(config)


# --- 6. Einzelne Runde rendern ---
def render_round_config(round_idx: int, tournament) -> dict:
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
        "stage_name": f"stage_name_{round_idx}",
    }

    # Zustand initialisieren
    for k in keys.values():
        if k not in st.session_state:
            st.session_state[k] = None

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
            options=tournament.courts,
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
            stage_direct = st.session_state[keys["stage_direct"]]
            place_direct = st.session_state[keys["place_direct"]]
        elif round_type == "Direkte Spiele":
            stage_direct = st.selectbox(
                "Aus welcher Runde sollen die Teams kommen?",
                options=list(tournament.stages.keys()),
                key=keys["stage_direct"]
            )
            place_direct = st.session_state[keys["place_direct"]]
        else:
            opponent_logic_choice = st.session_state[keys["opponent_logic_choice"]]
            stage_direct = st.session_state[keys["stage_direct"]]
            place_direct = st.session_state[keys["place_direct"]]

        stage_name = st.text_input(
            label="Name der Runde:",
            value="Zwischenrunde",  # ← Dieser Wert wird angezeigt
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
                    st.warning("Die ausgewählte Anzahl an Teams in ungerade.")
                st.session_state[keys["teams_list"]] = list_teams
                # st.success(list_teams)

        else:
            place_direct = None

        # Wenn "x. Plätze vs. y. Platz" ausgewählt ist
        if st.session_state[keys["opponent_logic_choice"]] == "x. Plätze vs. y. Platz":
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
            else:
                place_t1 = None

        # if st.button(f"✅ Stage Speichern"):
        #     stage_name = st.session_state[keys["stage_name"]]
        #     tournament.stages[stage_name] = Stage(id=stage_name, type=StageType.KNOCKOUT, teams=st.session_state[keys["teams_list"]])
        #     # st.success(tournament.stages[stage_name])

    with cols[3]:
        if st.session_state[keys["opponent_logic_choice"]] == "x. Plätze vs. y. Platz":
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
            else:
                place_t2 = None

    # Rückgabe der Konfiguration
    return {
        "type": round_type,
        "opponent_logic": st.session_state[keys["opponent_logic_choice"]],
        "stage_direct": st.session_state[keys["stage_direct"]],
        "place_direct": st.session_state[keys["place_direct"]],
        "stage_t1": st.session_state[keys["stage_t1"]],
        "place_t1": st.session_state[keys["place_t1"]],
        "stage_t2": st.session_state[keys["stage_t2"]],
        "place_t2": st.session_state[keys["place_t2"]],
        "teams_list": st.session_state[keys["teams_list"]],
        "courts": st.session_state[keys["courts"]],
        "stage_name": st.session_state[keys["stage_name"]],
    }


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
