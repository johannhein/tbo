from typing import Dict, List
import streamlit as st

from config import UI_TO_MATCH_MODE, MATCH_MODE_TO_UI, format_modus, ui_modus
from config.constants import DEFAULT_TIEBREAK, DEFAULT_POINTS, DEFAULT_GROUP_SIZE
from core import Stage, Tournament
from core.models import StageType, MatchSettings, Group
from utils import match_making_direct, match_making_x_vs_y, match_making_ranking, build_groups


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
            if k in {keys["teams_list"], keys["group_list"], keys["courts"]}:
                st.session_state[k] = []
            elif k in {keys["tiebreak_complete"], keys["tiebreak_incomplete"]}:
                st.session_state[k] = DEFAULT_TIEBREAK
            elif k in {keys["points_complete"], keys["points_incomplete"]}:
                st.session_state[k] = DEFAULT_POINTS
            elif k == keys["placing_bool"]:
                st.session_state[k] = False
            elif k in {keys["modus_complete"], keys["modus_incomplete"]}:
                st.session_state[k] = "2 Sätze"
            elif k == keys["groups_max"]:
                st.session_state[k] = DEFAULT_GROUP_SIZE
            else:
                st.session_state[k] = None


def render_stage_preview(stage: Stage):
    """Zeigt eine aufklappbare Vorschau der aktuellen Runde an."""
    stage_name = stage.id

    modus = format_modus(
        modus_ui=ui_modus(stage.match_list[0].settings.modus),
        pts=stage.match_list[0].settings.points,
        tiebreak=stage.match_list[0].settings.tiebreak
    )

    with st.expander(f"📋 Vorschau: {stage_name}"):
        st.write(f"**`{stage.id}`**")
        match_count = len(stage.match_list) if stage.match_list else 0
        st.write(f"**Anzahl an Spielen:** {match_count}")

        st.markdown(f"**Modus: {modus}**")

        if stage.match_list:
            st.write("### Spiele:")
            for match in stage.match_list:
                st.markdown(f"""
                - **Spiel {match.id}** auf Feld {match.court} **{match.t1}** vs **{match.t2}**
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


def set_group_settings(groups: List[Group], settings: MatchSettings, keys: Dict) -> List[Group]:
    for group in groups:
        if group.complete:
            group.settings = settings
        else:
            group.settings = MatchSettings(modus=UI_TO_MATCH_MODE[st.session_state[keys["modus_incomplete"]]],
                                           points=st.session_state[keys["points_incomplete"]],
                                           tiebreak=st.session_state[keys["tiebreak_incomplete"]])
            group.build_matches_from_schema()

    return groups


def confirm_round(tournament: Tournament, keys: Dict) -> Stage:
    courts = st.session_state[keys["courts"]]
    if not courts:
        st.warning("Es wurden keine Felder gesetzt.")
        st.stop()
    stage_name = st.session_state[keys["stage_name_from"]]
    round_type = st.session_state[keys["round_type"]]
    match_settings_complete = MatchSettings(modus=UI_TO_MATCH_MODE[st.session_state[keys["modus_complete"]]],
                                            points=st.session_state[keys["points_complete"]],
                                            tiebreak=st.session_state[keys["tiebreak_complete"]])

    teams = st.session_state[keys["teams_list"]]

    stage_typ: StageType = StageType.NONGROUP
    if round_type == "Gruppenphase":
        stage_typ: StageType = StageType.GROUP
        teams_1 = teams[:len(teams) // 2]
        teams_2 = teams[len(teams) // 2:]
        # todo felder zuweisung
        if len(courts) < len(teams) / st.session_state[keys["groups_max"]]:
            st.warning("Es gibt zu wenige Felder für jede Gruppe.")
            st.stop()
        if st.session_state[keys["opponent_logic_choice"]] == "x. Plätze vs. y. Platz":
            groups = build_groups(teams_1, teams_2, st.session_state[keys["groups_max"]], courts)
            groups = set_group_settings(groups=groups, settings=match_settings_complete, keys=keys)
        # elif st.session_state[keys["opponent_logic_choice"]] == "Platz x bis y aus Gesamtranking":
        else:
            groups_list = st.session_state[keys["group_list"]]
            group_1 = groups_list[:len(groups_list) // 2]
            group_2 = groups_list[len(groups_list) // 2:]
            groups = build_groups(teams_1, teams_2, st.session_state[keys["groups_max"]], courts, group_1, group_2)
            groups = set_group_settings(groups=groups, settings=match_settings_complete, keys=keys)
        stage = Stage(id=stage_name, type=stage_typ, teams=teams, groups=groups)
    elif round_type == "Direkte Spiele":
        match_list = match_making_direct(teams=teams, courts=courts, settings=match_settings_complete)
        stage = Stage(id=stage_name, type=stage_typ, teams=teams, match_list=match_list)
    # elif round_type == "Überkreuzspiele"
    else:
        if st.session_state[keys["opponent_logic_choice"]] == "x. Plätze vs. y. Platz":
            teams_1 = teams[:len(teams) // 2]
            teams_2 = teams[len(teams) // 2:]
            match_list = match_making_x_vs_y(teams_1=teams_1, teams_2=teams_2, courts=courts,
                                             settings=match_settings_complete)
        # elif st.session_state[keys["opponent_logic_choice"]] == "Platz x bis y aus Gesamtranking":
        else:
            groups = st.session_state[keys["group_list"]]
            match_list = match_making_ranking(teams=teams, groups=groups, courts=courts, settings=match_settings_complete)

        stage = Stage(id=stage_name, type=stage_typ, teams=teams, match_list=match_list)

    st.session_state[keys["stage"]] = stage
    st.session_state[keys["stage_ready"]] = True
    tournament.stages[stage_name] = Stage(id=stage_name, type=stage_typ, teams=teams)

    # st.success(f"✅ Runde '{stage_name}' wurde erstellt.")
    return stage


def render_match_settings(keys: Dict, complete: bool = True):
    cols = st.columns(5)
    if complete:
        modus = "complete"
    else:
        modus = "incomplete"
        st.write("Modus für unvollständige Gruppen")

    with cols[0]:
        st.selectbox(
            label="Welcher Modus soll gespielt werden",
            options=list(MATCH_MODE_TO_UI.values()),
            key=keys[f"modus_{modus}"],
        )

    with cols[1]:
        st.number_input(
            label="Punkte",
            min_value=1,
            max_value=99,
            step=1,
            key=keys[f"points_{modus}"],
        )

    with cols[2]:
        if st.session_state[keys[f"modus_{modus}"]] in ["2 Gewinnsätze", "3 Gewinnsätze"]:
            st.number_input(
                label="Tiebreak‑Punkte",
                min_value=1,
                max_value=99,
                step=1,
                key=keys[f"tiebreak_{modus}"],
            )
        else:
            st.session_state[keys[f"tiebreak_{modus}"]] = None


def render_slider(tournament: Tournament, keys: Dict):
    if st.session_state[keys["teams_list"]]:
        num_teams = len(st.session_state[keys["teams_list"]])
    else:
        # todo hier noch mal drüber schauen, welche fälle das betreffen könnte
        num_teams = 0

    if not st.session_state[keys["placing_slider"]]:
        st.session_state[keys["placing_slider"]] = (1, num_teams)

    placing = st.slider(
        f"Welche Plätze sollen für die {num_teams} Teams ausgespielt werden?",
        min_value=1,
        max_value=len(tournament.teams),
        value=st.session_state[keys["placing_slider"]],
        step=1,
        key=keys["placing_slider"]
    )

    if placing:
        start, end = placing
        num_placing = end - start + 1

        if num_placing < num_teams:
            st.warning("Es sind weniger Platzierungen als Teams in der Runde.")
        elif num_placing > num_teams:
            st.warning("Es sind mehr Platzierungen als Teams in der Runde.")


def render_direct_stage(tournament: Tournament, keys: Dict):
    stage = tournament.stages[st.session_state[keys["stage_direct"]]]
    if stage.type == StageType.GROUP:
        place_keys = list(stage.placement_tables.keys())
        place_direct = st.selectbox(
            label="Welche Plätze sollen gegeneinander spielen",
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

    elif stage.type == StageType.NONGROUP:
        place_direct = st.selectbox(
            label="Verlierer oder Gewinner",
            options=["Verlierer", "Gewinner"],
            key=keys["place_direct"]
        )

        if place_direct == "Verlierer":
            list_teams = stage.loser
        else:
            list_teams = stage.winner

        if not list_teams and place_direct:
            st.warning(f"Es sind keine {place_direct} in der ausgewählten Runde enthalten.")
        elif len(list_teams) % 2 != 0:
            st.warning("Die ausgewählte Anzahl an Teams ist ungerade.")
        else:
            st.session_state[keys["teams_list"]] = list_teams


def ui_first_selection_line(tournament: Tournament, keys: Dict):
    cols = st.columns(5)

    with cols[0]:
        st.text_input(
            label="Name der Runde:",
            placeholder="Gib einen Namen für die Runde ein ...",
            key=keys["stage_name_from"]
        )

    with cols[1]:
        st.multiselect(
            label="Verfügbare Felder",
            options=tournament.courts or [1, 2],
            key=keys["courts"],
            placeholder="Verfügbare Felder für die Runde wählen …"
        )

    with cols[2]:
        st.selectbox(
            label="Modus",
            options=["Überkreuzspiele", "Direkte Spiele", "Gruppenphase"],
            key=keys["round_type"]
        )

    with cols[3]:
        if st.session_state[keys["round_type"]] in ["Überkreuzspiele", "Gruppenphase"]:
            st.selectbox(
                label="Gegner-Auswahl",
                options=["x. Plätze vs. y. Platz", "Platz x bis y aus Gesamtranking"],
                key=keys["opponent_logic_choice"]
            )
        elif st.session_state[keys["round_type"]] == "Direkte Spiele":
            st.selectbox(
                label="Aus welcher Runde sollen die Teams kommen?",
                options=list(tournament.stages.keys()),
                key=keys["stage_direct"]
            )

    with cols[4]:
        if st.session_state[keys["stage_direct"]] is not None and st.session_state[keys["stage_direct"]] in tournament.stages:
            render_direct_stage(tournament=tournament, keys=keys)
        else:
            st.session_state[keys["teams_list"]] = []

        if st.session_state[keys["round_type"]] == "Gruppenphase":
            st.number_input(
                label="Wie viele Teams sollen in einer Gruppe sein?",
                min_value=3,
                max_value=6,
                step=1,
                key=keys["groups_max"]
            )


def render_stage_selection(tournament: Tournament, keys: Dict, team: int):
    st.selectbox(
        label=f"Aus welcher Runde kommt Team {team}",
        options=list(tournament.stages.keys()),
        key=keys[f"stage_t{team}"]
    )


def render_team_selection(tournament: Tournament, keys: Dict, team: int):
    stage_name = st.session_state[keys[f"stage_t{team}"]]
    if stage_name is not None and stage_name in tournament.stages:
        stage = tournament.stages[stage_name]
        if stage.type == StageType.GROUP:
            place_keys = list(stage.placement_tables.keys())
            place = st.selectbox(
                label=f"Platz Team {team}",
                options=place_keys,
                key=keys[f"place_t{team}"]
            )
            if place in place_keys:
                stage = tournament.stages[stage_name]
                list_teams = stage.placement_tables[place].sort_values(by=["Gruppe"])["Team"].tolist()
                if team == 1:
                    st.session_state[keys["teams_list"]] = list_teams
                else:
                    st.session_state[keys["teams_list"]] = st.session_state[keys["teams_list"]] + list_teams
        elif stage.type == StageType.NONGROUP:
            place_direct = st.selectbox(
                label="Verlierer oder Gewinner",
                options=["Verlierer", "Gewinner"],
                key=keys[f"place_t{team}"]
            )

            if place_direct == "Verlierer":
                # todo fix loser/winner in model?
                list_teams = stage.loser
            else:
                list_teams = stage.winner

            if not list_teams and place_direct:
                st.warning(f"Es sind keine {place_direct} in der ausgewählten Runde enthalten.")
            elif len(list_teams) % 2 != 0:
                st.warning("Die ausgewählte Anzahl an Teams ist ungerade.")
            else:
                if team == 1:
                    st.session_state[keys["teams_list"]] = list_teams
                else:
                    st.session_state[keys["teams_list"]] = st.session_state[keys["teams_list"]] + list_teams


def render_x_vs_y(tournament: Tournament, keys: Dict):
    cols = st.columns(5)
    with cols[0]:
        render_stage_selection(tournament=tournament, keys=keys, team=1)

    with cols[1]:
        render_team_selection(tournament=tournament, keys=keys, team=1)

    with cols[2]:
        render_stage_selection(tournament=tournament, keys=keys, team=2)

    with cols[3]:
        render_team_selection(tournament=tournament, keys=keys, team=2)

    if st.session_state[keys["place_t1"]] and st.session_state[keys["place_t2"]]:
        place_t1 = st.session_state.get(keys["place_t1"])
        place_t2 = st.session_state.get(keys["place_t2"])
        stage_t1 = tournament.stages[st.session_state.get(keys["stage_t1"])]
        stage_t2 = tournament.stages[st.session_state.get(keys["stage_t2"])]
        if place_t1 is not None and place_t1 == place_t2 and stage_t1 is not None and stage_t1 == stage_t2:
            st.warning("Du hast die gleichen Platzierungen ausgewählt")

        teams_1 = stage_t1.placement_tables[place_t1].sort_values(by=["Gruppe"])["Team"].tolist()
        teams_2 = stage_t2.placement_tables[place_t2].sort_values(by=["Gruppe"])["Team"].tolist()

        teams_doubled = [team for team in teams_1 if team in teams_2]

        if teams_doubled:
            if len(teams_doubled) == 1:
                st.warning(f"Das Team {teams_doubled[0]} kommt in beiden Teamlisten vor")
            elif len(teams_doubled) > 1:
                st.warning(f"Die Teams {teams_doubled} kommen in beiden Teamlisten vor")


def render_from_x_until_y(tournament: Tournament, keys: Dict):
    cols = st.columns(5)
    with cols[0]:
        render_stage_selection(tournament=tournament, keys=keys, team=1)

    if st.session_state[keys["stage_t1"]]:
        stage_name = st.session_state[keys["stage_t1"]]
        if tournament.stages[stage_name].type != StageType.GROUP:
            st.warning("Die gewählte Runde hat keine Gruppenphase, daher ist kein Gesamtranking vorhanden.")
            st.stop()
        stage = tournament.stages[stage_name]
        num_teams = len(stage.teams)
        places = list(range(1, num_teams + 1))
        if stage_name is not None and stage_name in tournament.stages:
            with cols[1]:
                r_from = st.selectbox(
                    label="Platz von:",
                    options=places,
                    key=keys["place_from"]
                )

            with cols[2]:
                r_until = st.selectbox(
                    label="Platz bis:",
                    options=places,
                    key=keys["place_until"]
                )

            if st.session_state[keys["place_from"]] and st.session_state[keys["place_until"]]:
                if st.session_state[keys["round_type"]] == "Überkreuzspiele" and (r_until - (r_from - 1)) % 2 != 0:
                    st.warning("Anzahl der Teams muss gerade sein")
                table = stage.table

                table_from_until = table[(table["Rang"] >= r_from) & (table["Rang"] <= r_until)]

                teams = table_from_until["Team"].tolist()
                groups = table_from_until["Gruppe"].tolist()

                st.session_state[keys["teams_list"]] = teams
                st.session_state[keys["group_list"]] = groups


def ui_second_selection_line(tournament: Tournament, keys: Dict):
    if st.session_state.get(keys["opponent_logic_choice"]) == "x. Plätze vs. y. Platz":
        render_x_vs_y(tournament=tournament, keys=keys)
    elif st.session_state.get(keys["opponent_logic_choice"]) == "Platz x bis y aus Gesamtranking":
        render_from_x_until_y(tournament=tournament, keys=keys)


def render_groups_review(stage: Stage) -> None:
    """UI zur Anzeige der erstellten Gruppen (4 Spalten pro Zeile)"""
    with st.expander(f"📋 Vorschau: {stage.id}"):
        groups = stage.groups
        for i in range(0, len(groups), 4):
            cols = st.columns(4)
            for idx, group in enumerate(groups[i:i + 4]):
                with cols[idx]:
                    modus = format_modus(
                        modus_ui=ui_modus(group.settings.modus),
                        pts=group.settings.points,
                        tiebreak=group.settings.tiebreak
                    )
                    st.markdown(f"### 🟦 **Gruppe {group.name}**")
                    st.markdown(f"**Modus: {modus}**")
                    st.markdown(f"**Feld: {", ".join(map(str, group.assigned_courts))}**")
                    for team in group.teams:
                        st.write(f"**{team.lstrip()}**")


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
        "stage_name_from": f"stage_name_from_{round_idx}",
        "points_complete": f"points_complete_{round_idx}",
        "modus_complete": f"modus_complete_{round_idx}",
        "tiebreak_complete": f"tiebreak_complete_{round_idx}",
        "points_incomplete": f"points_incomplete_{round_idx}",
        "modus_incomplete": f"modus_incomplete_{round_idx}",
        "tiebreak_incomplete": f"tiebreak_incomplete_{round_idx}",
        "stage": f"stage_{round_idx}",
        "stage_ready": f"stage_ready_{round_idx}",
        "groups_max": f"groups_max_{round_idx}",
        "placing_slider": f"placing_slider_{round_idx}",
        "place_from": f"place_from_{round_idx}",
        "place_until": f"place_until_{round_idx}",
        "placing_bool": f"placing_bool_{round_idx}",
        "confirm_round": f"confirm_round_{round_idx}",
        "group_list": f"group_list_{round_idx}",
    }

    init_session_state_keys(keys=keys)

    ui_first_selection_line(tournament=tournament, keys=keys)

    ui_second_selection_line(tournament=tournament, keys=keys)

    render_match_settings(keys=keys)

    if st.session_state[keys["round_type"]] == "Gruppenphase" and st.session_state[keys["teams_list"]] and st.session_state[keys["groups_max"]]:
        if len(st.session_state[keys["teams_list"]]) % st.session_state[keys["groups_max"]]:
            render_match_settings(keys=keys, complete=False)

    checkbox = st.checkbox(
        label="Platzierungsrunde",
        key=keys["placing_bool"]
    )

    if checkbox:
        render_slider(tournament=tournament, keys=keys)

    if st.button(label=f"✅ Runde {round_idx + 1} bestätigen"):
        new_stage = confirm_round(tournament=tournament, keys=keys)
        if not new_stage.id:
            st.warning("Kein Rundenname gesetzt.")
            return

        if not new_stage:
            st.warning("Keine Runde vorhanden.")
            return

    if keys["stage_ready"] not in st.session_state:
        st.session_state[keys["stage_ready"]] = False
    if st.session_state[keys["stage_ready"]]:
        stage_render = st.session_state[keys["stage"]]
        if stage_render.type == StageType.NONGROUP:
            render_stage_preview(stage=stage_render)
        else:
            render_groups_review(stage=stage_render)


def render_round_generation(tournament):
    """Zeigt den Button zum Generieren der Runden an."""
    if st.button("Runden generieren", key="generate_rounds"):
        st.session_state.next_round_generated = True
        st.success(f"✅ {len(st.session_state.next_round_matches)} Runden wurden konfiguriert.")
        print(tournament.stages.keys())


def tab_new_round():
    if "tournament" not in st.session_state or not st.session_state["tournament_loaded"]:
        st.info("Bitte lade ein Turnier im Tab „Übersicht“.")
        return

    st.header("Nächste Runde Konfigurator")

    _init_session_state()

    if not validate_tournament():
        return

    tournament = st.session_state["tournament"]

    # Steuere Runden-UI
    render_round_configs(tournament)
    render_round_controls()
    render_round_generation(tournament)
