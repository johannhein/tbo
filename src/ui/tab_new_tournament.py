import datetime
import math
import random
from pathlib import Path
from typing import List, Dict
import streamlit as st
import pandas as pd

from config.constants import IMPORT_DIR, MAX_COURT_NUM, DEFAULT_TIEBREAK, DEFAULT_POINTS, DEFAULT_GROUPS, NAME_PREROUND
from db.court_store import get_used_courts, set_courts
from db.days_store import get_courts_for_type
from utils.mapping import MATCH_MODE_TO_UI, UI_TO_MATCH_MODE
from utils.persistence import list_csv_files, save_tournament, load_csv
from core.models import Team, Group, Tournament, StageType, MatchSettings, MatchMode, Stage


# ----------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------
def settings_to_ui_values(settings: MatchSettings) -> dict:
    """
    Wandelt ein MatchSettings‑Objekt in ein Dictionary um,
    das von den Streamlit‑Widgets verwendet werden kann.
    """
    return {
        "modus": MATCH_MODE_TO_UI[settings.modus],
        "points": settings.points,
        "tiebreak": settings.tiebreak if settings.tiebreak is not None else DEFAULT_TIEBREAK,
    }


def get_incomplete_groups(groups: Dict[str, Group], num_groups: int, total_teams: int,) -> List[str]:
    """
    Gibt die Namen aller Gruppen zurück, die **weniger** Teams besitzen
    als die größte mögliche Gruppe.

    - `max_size = ceil(total_teams / num_groups)` → Größe der größten Gruppe
    - Jede Gruppe, deren aktuelle Größe < max_size, ist „unvollständig“.
    """
    max_size = math.ceil(total_teams / num_groups)   # z. B. 10 Teams / 3 Gruppen → 4
    incomplete = [
        name for name, grp in groups.items()
        if len(grp.teams) < max_size
    ]
    return incomplete


def get_default_court_assignments(groups: Dict[str, Group], available_courts: List[int]) -> Dict[str, List[int]]:
    """
    Gibt die Standard-Zuweisung zurück:
    - Gruppe A → kleinstes Feld
    - Gruppe B → nächstes
    - usw.

    :param groups: Dict[str, Group] – Gruppen mit Namen (A, B, C, ...)
    :param available_courts: Liste der verfügbaren Felder (z. B. [1, 2, 3, 4])
    :return: Dict mit Gruppenname → zugewiesene Felder
    """
    if not available_courts:
        return {name: [] for name in groups.keys()}

    # Sortiere Gruppen nach Namen (A, B, C, ...)
    sorted_group_names = sorted(groups.keys())

    # Sortiere Felder
    sorted_courts = sorted(available_courts)

    # Zuweisung: A → 1. Feld, B → 2. Feld, usw.
    assignment = {}
    for i, name in enumerate(sorted_group_names):
        if i < len(sorted_courts):
            assignment[name] = [sorted_courts[i]]
        else:
            assignment[name] = []  # Kein Feld mehr

    return assignment


def calculate_group_size(total_teams: int, num_groups: int) -> int:
    """
    Berechnet die minimale Gruppengröße (aufgerundet) aus Anzahl der Teams und Anzahl der Gruppen.
    """
    if num_groups <= 0:
        raise ValueError("Anzahl der Gruppen muss größer als 0 sein.")
    if total_teams < 0:
        raise ValueError("Anzahl der Teams darf nicht negativ sein.")

    # Berechnung der minimalen Gruppengröße damit jedes Team einen Platz in einer Gruppe hat
    min_size = (total_teams + num_groups - 1) // num_groups
    return min_size


def _rebuild_df_from_team_edit(original_df: pd.DataFrame, edited_df: pd.DataFrame, tournament_type: str,) -> pd.DataFrame:
    """
    Verschneidet die beiden DataFrames nach der Spalte 'Team'.
    - Alle Zeilen aus `edited_df` sind im Ergebnis enthalten.
    - Wenn ein Team aus `edited_df` nicht in `original_df` ist → andere Spalten = NaN.
    """
    # Kopie von edited_df, damit wir die Spalte 'Team' als Index verwenden können
    edited = edited_df.copy()
    edited = edited.set_index("Team")  # → Team als Index

    # Kopie von original_df, mit 'Team' als Index
    original = original_df.copy()
    original = original.set_index("Team")  # → Team als Index

    # Linker Join: alle Zeilen aus edited_df, mit Daten aus original_df
    merged = edited.merge(
        original,
        left_index=True,
        right_index=True,
        how="left",  # ← nur die Zeilen aus edited_df bleiben
        suffixes=("", "_original"),  # → um Spalten zu unterscheiden
    )

    # → Wir setzen `Turnier` nur für neue Zeilen (wo `Turnier_original` NaN ist)
    if "Turnier" in merged.columns:
        # Wenn `Turnier_original` NaN ist → es war kein Match → neues Team
        mask = merged["Turnier"].isna()
        merged.loc[mask, "Turnier"] = tournament_type
    else:
        # Wenn `Turnier` nicht existiert, fügen wir es hinzu
        merged["Turnier"] = tournament_type

    # Index zurücksetzen
    final_df = merged.reset_index().rename(columns={"index": "Team"})

    return final_df


def build_teams(df_category: pd.DataFrame) -> tuple[List[Team], Dict[str, str]]:
    """
    Erzeugt Team‑Objekte und ein Mapping von Team‑Name → Team‑ID.
    """
    teams: List[Team] = []
    team_to_id: Dict[str, str] = {}

    for _, row in df_category.iterrows():
        team = Team(
            id=str(row["Team"]).strip(),
            name=str(row["Name"]).strip(),
            verein=str(row["Verein / Gruppe"]).strip(),
        )
        teams.append(team)
        team_to_id[team.id] = team.id  # → Team‑ID ist der Name

    return teams, team_to_id


def get_group_size_dict(num_groups: int, group_size: int, group_names: List[str], num_teams: int) -> Dict[str, int]:
    """Gibt ein Dict mit den Gruppennamen un der Anzahl an Teams wider."""
    max_num_teams = num_groups * group_size

    print(f"num_groups: {num_groups}, group_size: {group_size}, max_num_teams: {max_num_teams}, num_teams: {num_teams}")

    group_size_dict = {}
    if num_teams == max_num_teams:
        for name in group_names:
            group_size_dict[name] = group_size
    if num_teams < max_num_teams:
        full_groups = num_groups - (max_num_teams - num_teams)
        for i, name in enumerate(group_names):
            if i < full_groups:
                group_size_dict[name] = group_size
            else:
                group_size_dict[name] = group_size - 1

    print(group_size_dict)

    return group_size_dict


def create_groups(group_df: pd.DataFrame, selected_names: List[str], num_groups: int, group_size: int) -> Dict[str, Group]:
    """
    Erstellt Gruppen mit gleichmäßiger Verteilung und berücksichtigt:
    - Vereinsschutz (Groß-/Kleinschreibung wird ignoriert)
    - Teams ohne Verein werden ignoriert (kein Schutz)
    - Kopf-Teams werden zuerst zugewiesen
    - Restliche Teams werden verteilt, aber mit Vereinsschutz
    """
    group_names = [chr(ord("A") + i) for i in range(num_groups)]
    groups: Dict[str, Group] = {name: Group(name=name,  teams=[], teams_target=group_size) for name in group_names}

    num_teams = len(group_df)

    group_dict = get_group_size_dict(num_groups=num_groups, group_size=group_size, group_names=group_names, num_teams=num_teams)

    # Kopf-Teams zuweisen (in Reihenfolge)
    for i, name in enumerate(selected_names):
        grp_name = group_names[i]
        groups[grp_name].add_head(name)

    # Verein-Informationen extrahieren (case-insensitive, NaN ignoriert)
    # Erstelle Mapping: Team → Verein (in lower-case, NaN → None)
    team_to_verein = {}
    for _, row in group_df.iterrows():
        team = row["team"]
        verein = row.get("verein")
        if pd.isna(verein) or not str(verein).strip():
            team_to_verein[team] = None  # Kein Verein → ignoriert
        else:
            team_to_verein[team] = str(verein).strip().lower()  # Normalisieren

    assigned_teams = set(selected_names)

    # Restliche Teams (nicht als Kopf)
    remaining_teams = [name for name in group_df["team"] if name not in assigned_teams]

    random.shuffle(remaining_teams)

    # Vereinsschutz: Für jede Gruppe speichern, welche Vereine bereits drin sind
    assigned_club_per_group = {name: set() for name in group_names}

    # Kopf-Teams in Schutz-Liste eintragen
    for i, name in enumerate(selected_names):
        grp_name = group_names[i]
        club = team_to_verein.get(name)
        if club is not None:  # Nur wenn Verein vorhanden
            assigned_club_per_group[grp_name].add(club)

    teams_with_no_club = []
    # Restliche Teams verteilen (mit Vereinsschutz)
    for name in remaining_teams:
        verein = team_to_verein.get(name)
        if verein is None:  # Kein Verein → kein Schutz
            teams_with_no_club.append(name)
            continue
        else:
            # Verein vorhanden → Schutz aktiv
            possible_groups = [
                grp_name
                for grp_name in group_names
                if verein not in assigned_club_per_group[grp_name] and len(groups[grp_name].teams) < group_dict[grp_name]
            ]

            if not possible_groups:
                # Keine Gruppe mit Schutz → wähle eine nicht-volle Gruppe
                available_non_full = [
                    grp_name
                    for grp_name in group_names
                    if len(groups[grp_name].teams) < group_dict[grp_name]
                ]
                if not available_non_full:
                    st.warning(f"⚠️ Keine Gruppe mehr verfügbar für Team mit Verein: {name}")
                    continue
                else:
                    grp_name = random.choice(available_non_full)
            else:
                grp_name = random.choice(possible_groups)

        groups[grp_name].add_team(name)

    for name in teams_with_no_club:
        available_non_full = [
            grp_name
            for grp_name in group_names
            if len(groups[grp_name].teams) < group_dict[grp_name]
        ]
        if not available_non_full:
            st.warning(f"⚠️ Keine Gruppe mehr verfügbar für Team: {name}")
            continue
        else:
            grp_name = random.choice(available_non_full)


        groups[grp_name].add_team(name)

    return groups


def get_tournament_types(df: pd.DataFrame) -> List[str]:
    """Alle eindeutigen Turnier‑Kategorien aus einer DataFrame."""
    if "Turnier" not in df.columns:
        st.error("❗Die CSV‑Datei enthält keine Spalte **Turnier**.")
        return []
    types = (
        df["Turnier"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    return sorted(types)


# ----------------------------------------------------------------------
# UI Funktionen
# ----------------------------------------------------------------------
def ui_select_csv() -> Path | None:
    """Liefert den Pfad zur zu verarbeitenden CSV‑Datei (oder None)."""
    st.info(
        f"Lege deine CSV‑Datei in den Ordner `{IMPORT_DIR}` ab oder lade sie hier hoch. "
        "Die Datei muss eine Spalte Turnier enthalten."
    )

    col1, col2 = st.columns(2)

    with col1:

        # Auswahlmenü für vorhandene CSV‑Dateien im Import‑Ordner
        csv_files = list_csv_files(IMPORT_DIR)
        selected_path: Path | None = None

        if csv_files:
            file_names = [p.name for p in csv_files]
            selected_name = st.selectbox(
                "Vorhandene CSV‑Datei auswählen",
                options=["-- keine Auswahl --"] + file_names,
                index=0,
            )
            if selected_name != "-- keine Auswahl --":
                selected_path = IMPORT_DIR / selected_name

    with col2:
        # manueller Upload
        upload = st.file_uploader(
            "Oder CSV‑Datei von deinem Rechner hochladen",
            type=["csv", "txt"],
            help="Wird verwendet, wenn die gewünschte Datei nicht im Standard‑Ordner liegt.",
        )
        if upload:
            # temporäre Datei im Daten‑Ordner des Managers anlegen
            tmp_path = IMPORT_DIR / f"tmp_{upload.name}"
            with open(tmp_path, "wb") as f:
                f.write(upload.getbuffer())
            selected_path = tmp_path

    return selected_path


def ui_select_courts(tournament_id: str, max_court_num: int = MAX_COURT_NUM,) -> List[int]:
    """
    Multiselect‑Widget für die Feld‑Auswahl.
    - Entfernt alte, nicht mehr gültige Werte aus dem Session‑State.
    - Gibt eine Warnung aus, wenn das ausgewählte Feld bereits von einem
      anderen Turnier belegt ist (siehe Abschnitt 2).
    """
    options = list(range(1, max_court_num + 1))

    key = f"assign_courts_{tournament_id}"

    stored = st.session_state.get(key, [])
    # Filtere alte Werte, die nicht mehr in den Optionen vorkommen
    valid_stored = [c for c in stored if c in options]
    if len(valid_stored) != len(stored):
        st.session_state[key] = valid_stored

    used_elsewhere = get_used_courts(exclude_tournament=tournament_id)

    selected = st.multiselect(
        f"Turnier {tournament_id} – Felder",
        options=options,
        max_selections=max_court_num,
        key=key,
        default=valid_stored,  # explizit den gefilterten Default setzen
        placeholder="Bitte verfügbare Felder wählen …",
    )

    conflicted = set(selected) & used_elsewhere
    if conflicted:
        st.warning(
            f"⚠️ Die Felder {sorted(conflicted)} sind bereits in einem anderen Turnier belegt. "
            "Bitte wähle andere Felder."
        )
    set_courts(tournament_id, selected)

    return selected


def ui_select_tournament_type(df):
    """UI zum Auswählen des Turniertyps"""
    types = get_tournament_types(df)
    if not types:
        st.warning("Keine Kategorien gefunden – bitte CSV prüfen.")
        return None

    col_select, col_empty = st.columns([1, 3])

    with col_select:
        selected = st.selectbox(
            "Welche Kategorie soll das Turnier haben?",
            options=types,
            key="selected_tournament_type",
        )

    return selected


def ui_edit_team_names(df_category: pd.DataFrame) -> None:
    """
    Zeigt einen Data‑Editor, in dem nur die Spalte 'Team' editierbar ist.
    Zusätzlich wird ein versteckter Index‑Wert (`orig_idx`) mitgeführt,
    damit wir nach dem Editieren exakt wissen, welche Zeile zu welchem
    Original‑Datensatz gehört.
    """
    edit_df = df_category[["Team"]]

    column_cfg = {
        "Team": st.column_config.Column(
            label="Team‑Name",
            width=300,
        ),
    }

    col1, col2 = st.columns(2)

    with col1:
        edited = st.data_editor(
            edit_df,
            num_rows="dynamic",          # Add‑ und Delete‑Buttons aktiv
            width="stretch",
            hide_index=False,            # Index‑Spalte (Müll‑Icon) bleibt sichtbar
            column_config=column_cfg,
            key="team_name_editor",
        )

    cols = st.columns(4)

    with cols[0]:
        if st.button("✅ Änderungen übernehmen", key="apply_team_name_changes"):
            st.session_state["edited_team_names"] = edited
            st.success("✅ Änderungen wurden übernommen!")

    with cols[1]:
        if st.button("🔄 Änderungen zurücksetzen", key="reset_team_name_changes"):
            st.warning("🔄 Änderungen zurückgesetzt!")
            st.session_state["edited_team_names"] = df_category
            st.rerun()


def ui_basic_settings(num_teams: int) -> int:
    """Grundlegende Turnier‑Einstellungen (Teams, Felder, Zeit, Gruppen)"""
    st.metric(label="Anzahl Teams", value=num_teams)

    col1, col2 = st.columns(2)

    with col1:
        num_groups = st.number_input(
            "Anzahl der Gruppen",
            min_value=1,
            max_value=max(DEFAULT_GROUPS, len(st.session_state["selected_courts"])),
            value=max(DEFAULT_GROUPS, len(st.session_state["selected_courts"])),
            step=1,
            key="num_groups"
        )

        st.session_state["group_size"] = math.ceil(num_teams / num_groups)

    with col2:
        start_time = st.time_input(
            "Startzeit", value=datetime.time(10, 0), key="start_time"
        )

    return  num_groups


def ui_select_group_heads(team_to_id: Dict[str, str], max_selections: int,) -> List[str]:
    """
    UI für die Auswahl der Gruppenköpfe über den Team‑Namen (aus Spalte 'Team').
    """
    # Nur die Team‑IDs anzeigen
    options = list(team_to_id.keys())

    selected_ids = st.multiselect(
        "Gruppenköpfe auswählen",
        options=options,
        max_selections=max_selections,
        key="group_heads_select",
        placeholder="Bitte Köpfe auswählen …",
    )

    return selected_ids


def ui_show_groups(groups: Dict[str, Group]) -> None:
    """UI zur Anzeige der erstellten Gruppen (4 Spalten pro Zeile)"""
    group_names = list(groups.keys())
    for i in range(0, len(group_names), 4):
        cols = st.columns(4)
        for j, name in enumerate(group_names[i : i + 4]):
            with cols[j]:
                grp = groups[name]
                st.markdown(f"### 🟦 **Gruppe {name}**")

                # Teams anzeigen
                for team in grp.teams:
                    st.write(team)


def ui_game_modes(incomplete_groups: List[str]) -> None:
    """UI zum Einstellen der Spiel‑Modi für komplette und unvollständige Gruppen."""
    st.subheader("🗂️ Spielmodus")

    game_mode = st.session_state["game_modes"]
    # Falls bereits ein Eintrag existiert, prüfen wir, ob er ein dict ist (z. B. nach einem Reload)
    for key in ("complete", "incomplete"):
        val = game_mode.get(key)
        if isinstance(val, dict):
            # Konvertiere das dict in ein MatchSettings‑Objekt
            # Erwartete Schlüssel: "modus" (Enum‑oder String), "points", "tiebreak"
            modus_raw = val["modus"]
            # Der Modus kann bereits ein Enum sein oder ein UI‑String
            if isinstance(modus_raw, str):
                modus = UI_TO_MATCH_MODE[modus_raw]  # String → Enum
            else:
                modus = modus_raw  # Enum → Enum
            game_mode[key] = MatchSettings(
                modus=modus,
                points=int(val["points"]),
                tiebreak=int(val["tiebreak"]) if val.get("tiebreak") else None,
            )

    # UI‑Werte (Strings, ints) für die Selectboxen / Number‑Inputs
    complete_ui   = settings_to_ui_values(game_mode["complete"])
    incomplete_ui = settings_to_ui_values(game_mode["incomplete"])

    # Einstellungen für vollständige Gruppen
    st.markdown("#### Vollständige Gruppen")

    col1, col2, col3 = st.columns(3)
    with col1:
        sets_complete = st.selectbox(
            "Sätze",
            options=list(MATCH_MODE_TO_UI.values()),
            index=list(MATCH_MODE_TO_UI.values()).index(complete_ui["modus"]),
            key="sets_complete",
        )
    with col2:
        points_complete = st.number_input(
            "Punkte",
            min_value=1,
            max_value=99,
            value=complete_ui["points"],
            step=1,
            key="points_complete",
        )
    with col3:
        # Tiebreak‑Feld nur anzeigen, wenn der Modus „2 Gewinnsätze“ ist
        if sets_complete == "2 Gewinnsätze" or sets_complete == "3 Gewinnsätze":
            tiebreak_complete = st.number_input(
                "Tiebreak‑Punkte",
                min_value=1,
                max_value=99,
                value=DEFAULT_TIEBREAK,
                step=1,
                key="tiebreak_complete",
            )
        else:
            tiebreak_complete = None  # Default‑Wert, wird nicht angezeigt

        # Session‑State aktualisieren
        st.session_state["game_modes"]["complete"] = MatchSettings(
            modus=UI_TO_MATCH_MODE[sets_complete],
            points=points_complete,
            tiebreak=tiebreak_complete,
        )

    # Einstellungen für unvollständige Gruppen (falls vorhanden)
    if incomplete_groups:
        group_names_str = ", ".join(incomplete_groups)
        st.markdown(f"#### Unvollständige Gruppen ({group_names_str})")

        col1, col2, col3 = st.columns(3)
        with col1:
            sets_incomplete = st.selectbox(
                "Sätze",
                options=list(MATCH_MODE_TO_UI.values()),
                index=list(MATCH_MODE_TO_UI.values()).index(incomplete_ui["modus"]),
                key="sets_incomplete",
            )
        with col2:
            points_incomplete = st.number_input(
                "Punkte",
                min_value=1,
                max_value=99,
                value=DEFAULT_POINTS,
                step=1,
                key="points_incomplete",
            )
        with col3:
            if sets_incomplete == "2 Gewinnsätze" or sets_incomplete == "3 Gewinnsätze":
                tiebreak_incomplete = st.number_input(
                    "Tiebreak‑Punkte",
                    min_value=1,
                    max_value=99,
                    value=DEFAULT_TIEBREAK,
                    step=1,
                    key="tiebreak_incomplete",
                )
            else:
                tiebreak_incomplete = None

            # Session‑State aktualisieren
            st.session_state["game_modes"]["incomplete"] = MatchSettings(
                modus=UI_TO_MATCH_MODE[sets_incomplete],
                points=points_incomplete,
                tiebreak=tiebreak_incomplete,
            )
    else:
        st.info("Alle Gruppen sind vollständig – ein einheitlicher Spielmodus wird verwendet.")


# ----------------------------------------------------------------------
# Zusammenbauen der Seite
# ----------------------------------------------------------------------
def tab_new_tournament() -> None:
    st.header("🆕 Neues Turnier erstellen")

    st.session_state.setdefault("groups_created", False)
    st.session_state.setdefault("group_names", None)
    st.session_state["tournament_created"] = False
    st.session_state.setdefault("assign_group_refs", True)  # ← Standard‑Wert
    st.session_state.setdefault("game_modes", {
        "complete": {"modus": "1 Satz", "points": DEFAULT_POINTS, "tiebreak": None},
        "incomplete": {"modus": "1 Satz", "points": DEFAULT_POINTS, "tiebreak": None},
    })

    # -------------------------------------------------
    # CSV auswählen / laden
    # -------------------------------------------------
    csv_path = ui_select_csv()
    if not csv_path:
        st.info("Bitte wähle eine CSV‑Datei aus oder lade sie hoch.")
        return

    df_all = load_csv(csv_path)

    # -------------------------------------------------
    # Turnier‑Kategorie auswählen
    # -------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        tournament_type = ui_select_tournament_type(df_all)
        if not tournament_type:
            return

    # tournament_id = f"{tournament_type} {datetime.datetime.now().year}"

    # with col2:
    #     new_selected = ui_select_courts(tournament_id=tournament_id)
    #
    #     st.session_state["selected_courts"] = new_selected
    st.session_state["selected_courts"] = get_courts_for_type(tournament_type)
    df_category = df_all[df_all["Turnier"] == tournament_type]
    st.session_state["teams"] = df_category["Team"]

    # -------------------------------------------------
    # Team‑Namen editieren
    # -------------------------------------------------
    st.markdown("### ✏️ Zum Editieren der Teamliste")
    ui_edit_team_names(df_category)

    if "edited_team_names" in st.session_state:
        edited = st.session_state["edited_team_names"]
        df_category = _rebuild_df_from_team_edit(
            original_df=df_category,
            edited_df=edited,
            tournament_type=tournament_type,
        )
        st.session_state["teams"] = df_category["Team"]

    num_teams = len(df_category)
    number_groups = ui_basic_settings(num_teams)

    # -------------------------------------------------
    # Gruppen definieren
    # -------------------------------------------------
    teams, display_to_name = build_teams(df_category)

    group_df = df_category[["Team", "Name", "Verein / Gruppe", "City"]]
    group_df = group_df.rename(columns={
        "Team": "team",
        "Name": "name",
        "Verein / Gruppe": "verein",
        "City": "city",
    })

    selected_names = ui_select_group_heads(display_to_name, max_selections=number_groups,)

    if st.button("🛠️ Gruppen erstellen", key="create_groups_button", type="primary"):
        team_names = [t.id for t in teams]
        groups = create_groups(group_df=group_df, selected_names=selected_names, num_groups=number_groups,
                               group_size=st.session_state["group_size"], )
        st.session_state["groups"] = groups
        st.session_state["group_names"] = list(groups.keys())
        st.session_state["groups_created"] = True
        st.success("✅ Gruppen wurden erstellt!")
        st.rerun()

    # Wenn bereits erstellt → Anzeige + weitere Optionen
    if st.session_state["groups"]:
        groups: Dict[str, Group] = st.session_state["groups"]
        ui_show_groups(groups)
    elif "groups_final" in st.session_state:
        groups: Dict[str, Group] = st.session_state["groups_final"]
        ui_show_groups(groups)
    else:
        groups = {}

    if groups:
        st.subheader("🔧 Konkrete Felder pro Gruppe zuweisen")

        selected_courts = st.session_state.get("selected_courts", [])
        max_total_courts = len(selected_courts)

        if max_total_courts == 0:
            st.warning("⚠️ Keine Felder verfügbar. Bitte wähle mindestens ein Feld aus.")
            st.stop()

        # Automatische Voreinstellung
        if "court_assignments" not in st.session_state:
            default_assignments = get_default_court_assignments(groups, selected_courts)
            st.session_state["court_assignments"] = default_assignments

        # Zeige Auswahl
        cols = st.columns(len(groups))
        for i, (name, group) in enumerate(groups.items()):
            with cols[i]:
                current_courts = st.session_state["court_assignments"].get(name, [])
                new_courts = st.multiselect(
                    f"Gruppe {name} – Felder",
                    options=selected_courts,
                    default=current_courts,
                    key=f"assign_courts_{name}"
                )
                st.session_state["court_assignments"][name] = new_courts

        # Summe der zugewiesenen Felder
        total_assigned = sum(len(courts) for courts in st.session_state["court_assignments"].values())

        # Warnung, wenn zu viele Felder zugewiesen
        if total_assigned > max_total_courts:
            st.warning(f"⚠️ Du hast {total_assigned} Felder zugewiesen, aber nur {max_total_courts} verfügbar!")

        st.session_state["max_court"] = max_total_courts
        st.session_state["groups"] = groups

        # Ermittlung unvollständiger Gruppen
        total_teams = sum(len(g.teams) for g in groups.values())
        incomplete = get_incomplete_groups(groups=groups, num_groups=number_groups, total_teams=total_teams,)
        st.session_state["incomplete_groups"] = incomplete

    # -------------------------------------------------
    # Spielmodi
    # -------------------------------------------------
        ui_game_modes(incomplete)
        groups = st.session_state["groups"]

        # Zuweisung der Spielmodus
        for name, grp in groups.items():
            if grp.complete:
                grp.settings = st.session_state["game_modes"]["complete"]
            else:
                grp.settings = st.session_state["game_modes"]["incomplete"]

        st.session_state["groups_final"] = groups
        # pickle_name = f"{tournament_type}_groups"
        # save_group(st.session_state["groups"], pickle_name)
        # st.session_state["pickle_saved"] = True

    # -------------------------------------------------
    # Turnier erstellen
    # -------------------------------------------------
    if st.button("Turnier erstellen", key="create_tournament_button", type="primary",):
        # Feldbelegungen speichern
        # pickle_name = f"groups/{tournament_type}_groups.pkl"
        # path: Path = PICKLE_DIR / pickle_name
        # if  not st.session_state["groups_final"]:
        #     st.session_state["groups_final"] = load_pickle(path)
        #     st.session_state["pickle_loaded"] = True
        #     print("loaded")
        #     st.rerun()
        total_assigned = sum(len(courts) for courts in st.session_state["court_assignments"].values())
        groups = st.session_state["groups_final"]
        if total_assigned > st.session_state["max_court"]:
            st.error(f"❌ Zu viele Felder zugewiesen! Nur {st.session_state["max_court"]} verfügbar.")
        else:
            for name, group in groups.items():
                group.assigned_courts = st.session_state["court_assignments"][name]
            st.success(f"✅ Felder wurden zugewiesen: {st.session_state['court_assignments']}")

        name = "TBO " + tournament_type + " " + str(datetime.datetime.now().year)
        tournament = Tournament(name=name, type=tournament_type, courts=st.session_state["selected_courts"], teams=st.session_state["teams"])
        group_list: List[Group] = list(groups.values())
        stage = Stage(id=NAME_PREROUND, type=StageType.GROUP, teams=st.session_state["teams"],
                      groups=group_list)

        tournament.add_stage(stage)
        tournament.schedule_stage(stage.id)

        year = datetime.datetime.now().year
        filename = f"{tournament.type.lower()}_{str(year)}"
        save_tournament(tournament, filename)

        # if "pickle_saved" in st.session_state:
        #     delete_folder_completely(path.parent)

        st.session_state["tournament_created"] = True
        st.success(f"✅ Das {tournament_type}-Turnier wurde erstellt!")

        # print(st.session_state["groups"])
        # print(group_list[0])


    # -------------------------------------------------
    # Aufräumen (temporäre Upload‑Datei)
    # -------------------------------------------------
    if csv_path.name.startswith("tmp_"):
        try:
            csv_path.unlink(missing_ok=True)
        except Exception as exc:
            st.warning(f"Konnte temporäre Datei nicht löschen: {exc}")
