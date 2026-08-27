import streamlit as st


def tab_new_round():
    st.header("Nächste Runde Konfigurator")

    # --- Zustand initialisieren ---
    if "next_round_generated" not in st.session_state:
        st.session_state.next_round_generated = False
    if "next_round_matches" not in st.session_state:
        st.session_state.next_round_matches = []  # Liste von dicts: { "type": "...", "stage1": "...", ... }

    # --- Dynamische Runden-Liste: Speichere Anzahl Runden im Session-State ---
    if "num_rounds" not in st.session_state:
        st.session_state.num_rounds = 1  # Start mit einer Runde

    # --- Button: Weitere Runde hinzufügen ---
    if st.button("Weitere Runde einstellen", key="add_round"):
        st.session_state.num_rounds += 1

    # --- Funktion: Erstelle ein einzelnes Runden-Setup mit dynamischen Keys ---
    def create_round_config(round_idx):
        st.subheader(f"Runde {round_idx + 1}")

        # Dynamische Keys für jedes Widget
        keys = {
            "round_type": f"round_{round_idx}_type",
            "opponent_logic_choice": f"round_{round_idx}_opponent_logic",
            "stage_direct": f"round_{round_idx}_stage_direct",
            "place_direct": f"round_{round_idx}_place_direct",
            "stage_t1": f"round_{round_idx}_stage_t1",
            "place_t1": f"round_{round_idx}_place_t1",
            "stage_t2": f"round_{round_idx}_stage_t2",
            "place_t2": f"round_{round_idx}_place_t2",
        }

        # --- Zustand für diese Runde initialisieren ---
        for k in keys.values():
            if k not in st.session_state:
                st.session_state[k] = None

        # --- Rundenarten und Logik ---
        round_types = {
            "Überkreuzspiele": "cross",
            "Direkte Spiele": "direct",
            "Platzierungsspiele": "ranking",
            "Gruppenphase": "group",
        }

        cross_logic = {
            "x. Plätze vs. y. Platz": "place",
            "Platz x bis y aus Gesamtranking": "rank",
        }



        # --- UI: Auswahl für diese Runde ---
        cols = st.columns(5)

        with cols[0]:
            round_type = st.selectbox(
                "Modus",
                options=list(round_types.keys()),
                key=keys["round_type"]
            )

        with cols[1]:
            if round_type == "Überkreuzspiele":
                opponent_logic_choice = st.selectbox(
                    "Gegner-Auswahl",
                    options=list(cross_logic.keys()),
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

        with cols[2]:
            if stage_direct is not None and stage_direct in tournament.stages:
                place_keys = list(tournament.stages[stage_direct].placement_tables.keys())
                place_direct = st.selectbox(
                    "Welche Plätze sollen gegeneinander spielen",
                    options=place_keys,
                    key=keys["place_direct"]
                )
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

        # --- Rückgabe der Konfiguration für diese Runde ---
        return {
            "type": round_type,
            "opponent_logic": st.session_state[keys["opponent_logic_choice"]],
            "stage_direct": st.session_state[keys["stage_direct"]],
            "place_direct": st.session_state[keys["place_direct"]],
            "stage_t1": st.session_state[keys["stage_t1"]],
            "place_t1": st.session_state[keys["place_t1"]],
            "stage_t2": st.session_state[keys["stage_t2"]],
            "place_t2": st.session_state[keys["place_t2"]],
        }

    # --- 🚨 Wichtig: Tournament laden, UNABHÄNGIG von Rundenart ---
    if "tournament" not in st.session_state:
        st.error("❌ Kein Turnier geladen! Bitte erst ein Turnier erstellen.")
        return  # Beende die Funktion, wenn kein Turnier da ist

    tournament = st.session_state["tournament"]

    # --- Erstelle dynamisch so viele Runden-Configs wie num_rounds ---
    st.session_state.next_round_matches = []
    for i in range(st.session_state.num_rounds):
        config = create_round_config(i)
        st.session_state.next_round_matches.append(config)

    # --- Optional: Button zum Generieren der Runden (z. B. für "Erstellen") ---
    if st.button("Runden generieren", key="generate_rounds"):
        st.session_state.next_round_generated = True
        st.success(f"✅ {len(st.session_state.next_round_matches)} Runden wurden konfiguriert.")