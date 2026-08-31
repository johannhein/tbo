import datetime
import math
import random
from pathlib import Path
from typing import List, Dict
import streamlit as st
import pandas as pd

from config.constants import IMPORT_DIR, MAX_COURT_NUM, DEFAULT_TIEBREAK, DEFAULT_POINTS, DEFAULT_GROUP_SIZE
from db import save_tournament
from db.court_store import get_used_courts, set_courts
from db.days_store import get_courts_for_type
from config import MATCH_MODE_TO_UI, UI_TO_MATCH_MODE, settings_to_ui_values
from persistence.persistence import list_csv_files, load_csv
from core.models import Group, Tournament, StageType, MatchSettings, Stage


# ----------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------
def get_text_msg_for_groups(num_teams, num_groups):
    """Berechnet die Anzahl der Teams für jede Gruppe und gibt es aus."""
    if num_groups <= 0:
        return "Fehler: Anzahl der Gruppen muss größer als 0 sein."
    if num_teams <= 0:
        return "Fehler: Anzahl der Teams muss größer als 0 sein."

    base = num_teams // num_groups
    remainder = num_teams % num_groups

    # Anzahl der Gruppen mit einem zusätzlichen Team
    groups_with_extra = remainder
    groups_with_base = num_groups - remainder

    # Erstelle die Ausgabe
    lines = []
    if groups_with_base > 0:
        lines.append(f"{groups_with_base} Gruppe{'n' if groups_with_base > 1 else ''} mit {base} Team{'s' if base > 1 else ''}")
    if groups_with_extra > 0:
        lines.append(f"und {groups_with_extra} Gruppe{'n' if groups_with_extra > 1 else ''} mit {base + 1} Team{'s' if base + 1 > 1 else ''}")

    return "\n".join(lines)


def get_default_court_assignments(groups: Dict[str, Group], available_courts: List[int]) -> Dict[str, List[int]]:
    """
    Gibt die Standard-Zuweisung zurück:
    - Gruppe 1 → kleinstes Feld
    - Gruppe 2 → nächstes
    - usw.

    :param groups: Dict[str, Group] – Gruppen mit Namen (z. B. "1", "2", "A", "B")
    :param available_courts: Liste der verfügbaren Felder (z. B. [1, 2, 3, 4])
    :return: Dict mit Gruppenname → zugewiesene Felder
    """
    if not available_courts:
        return {name: [] for name in groups.keys()}

    def sort_key(name: str) -> int | str:
        try:
            return int(name)
        except ValueError:
            return name

    sorted_group_names = sorted(groups.keys(), key=sort_key)

    # Sortiere Felder
    sorted_courts = sorted(available_courts)

    # Zuweisung: 1 → 1. Feld, 2 → 2. Feld, usw.
    assignment = {}
    for i, name in enumerate(sorted_group_names):
        if i < len(sorted_courts):
            assignment[name] = [sorted_courts[i]]
        else:
            assignment[name] = []
            st.warning(f"⚠️ Es gibt nicht genug Felder für Gruppe {name}.")

    return assignment


def _rebuild_df_from_team_edit(original_df: pd.DataFrame, edited_df: pd.DataFrame, tournament_type: str,) -> pd.DataFrame:
    """
    Verschneidet die beiden DataFrames nach der Spalte 'Team'.
    - Alle Zeilen aus `edited_df` sind im Ergebnis enthalten.
    - Wenn ein Team aus `edited_df` nicht in `original_df` ist → andere Spalten = NaN.
    """
    # Kopie von edited_df, damit wir die Spalte 'Team' als Index verwenden können
    edited = edited_df.copy()
    edited = edited.set_index("team")  # → Team als Index

    # Kopie von original_df, mit 'Team' als Index
    original = original_df.copy()
    original = original.set_index("team")  # → Team als Index

    # Linker Join: alle Zeilen aus edited_df, mit Daten aus original_df
    merged = edited.merge(
        original,
        left_index=True,
        right_index=True,
        how="left",  # ← nur die Zeilen aus edited_df bleiben
        suffixes=("", "_original"),  # → um Spalten zu unterscheiden
    )

    # Wir setzen `Turnier` nur für neue Zeilen
    if "turnier" in merged.columns:
        # Wenn `Turnier_original` NaN ist → es war kein Match → neues Team
        mask = merged["turnier"].isna()
        merged.loc[mask, "turnier"] = tournament_type

    # Index zurücksetzen
    final_df = merged.reset_index().rename(columns={"index": "team"})

    return final_df


def get_group_size_dict(num_groups: int, group_size: int, group_names: List[str], num_teams: int) -> Dict[str, int]:
    """Gibt ein Dict mit den Gruppennamen un der Anzahl an Teams wider."""
    max_num_teams = num_groups * group_size

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

    return group_size_dict


def split_clubs(verein: str) -> List[str]:
    """
    Trennt einen Verein mit '/' und normalisiert (lower, strip).
    Gibt eine Liste von Vereinen zurück.
    """
    if pd.isna(verein) or not str(verein).strip():
        return []
    return [club.strip().lower() for club in str(verein).split("/") if club.strip()]


def create_groups(group_df: pd.DataFrame,  selected_names: List[str], num_groups: int,
                  group_size: int,) -> Dict[str, Group]:
    """
    Erstellt Gruppen mit gleichmäßiger Verteilung und berücksichtigt:
    - Vereinsschutz (Groß-/Kleinschreibung wird ignoriert)
    - Teams mit mehreren Vereinen werden korrekt behandelt
    - Kopf-Teams werden zuerst zugewiesen
    - Teams mit Verein werden zuerst verteilt (mit Schutz)
    - Teams ohne Verein werden danach verteilt (ohne Schutz)
    - Keine Gruppe wird über die Zielgröße hinausgefüllt
    """
    # leere Gruppen erstellen
    group_names = [str(i + 1) for i in range(num_groups)]
    groups: Dict[str, Group] = {name: Group(name=name, teams=[], teams_target=group_size) for name in group_names}

    num_teams = len(group_df)

    # Zielgrößen berechnen: erste `remainder` Gruppen haben +1
    base_size = num_teams // num_groups
    remainder = num_teams % num_groups
    group_dict = {name: base_size + 1 if i < remainder else base_size for i, name in enumerate(group_names)}

    # Kopf-Teams zuweisen
    for i, name in enumerate(selected_names):
        grp_name = group_names[i]
        groups[grp_name].add_head(name)

    # Verein-Informationen extrahieren
    team_to_verein = {}
    for _, row in group_df.iterrows():
        team = row["team"]
        verein = row.get("verein")
        team_to_verein[team] = split_clubs(verein)

    assigned_teams = set(selected_names)

    # Teams mit Verein und ohne Verein trennen
    teams_with_club = [
        name for name in group_df["team"]
        if name not in assigned_teams and team_to_verein.get(name)
    ]
    teams_without_club = [
        name for name in group_df["team"]
        if name not in assigned_teams and not team_to_verein.get(name)
    ]

    # Zufällige Reihenfolge
    random.shuffle(teams_with_club)
    random.shuffle(teams_without_club)

    # Vereinsschutz: Für jede Gruppe speichern, welche Vereine bereits drin sind
    assigned_club_per_group = {name: set() for name in group_names}

    # Kopf-Teams in Schutz-Liste eintragen
    for i, name in enumerate(selected_names):
        grp_name = group_names[i]
        vereine = team_to_verein.get(name)
        if vereine:
            for verein in vereine:
                assigned_club_per_group[grp_name].add(verein)

    # Teams mit Verein verteilen (mit Schutz)
    for name in teams_with_club:
        vereine = team_to_verein.get(name)  # Liste von Vereinen

        # Verein vorhanden → Schutz aktiv
        possible_groups = [
            grp_name
            for grp_name in group_names
            if not any(verein in assigned_club_per_group[grp_name] for verein in vereine)
            and len(groups[grp_name].teams) < group_dict[grp_name]
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
        for verein in vereine:
            assigned_club_per_group[grp_name].add(verein)

    # Teams ohne Verein verteilen
    for name in teams_without_club:
        # Wähle eine Gruppe, die noch nicht voll ist
        available_non_full = [
            grp_name
            for grp_name in group_names
            if len(groups[grp_name].teams) < group_dict[grp_name]
        ]
        if not available_non_full:
            st.warning(f"⚠️ Keine Gruppe mehr verfügbar für Team ohne Verein: {name}")
            continue
        else:
            grp_name = random.choice(available_non_full)

        groups[grp_name].add_team(name)

    return groups


def get_tournament_types(df: pd.DataFrame) -> List[str]:
    """Alle eindeutigen Turnier‑Kategorien aus einem DataFrame."""
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

    if "last_selected_type" not in st.session_state or st.session_state["last_selected_type"] != selected:
        st.session_state["last_selected_type"] = selected
        st.session_state.setdefault("game_modes", {
            "complete": {"modus": "1 Satz", "points": DEFAULT_POINTS, "tiebreak": None},
            "incomplete": {"modus": "1 Satz", "points": DEFAULT_POINTS, "tiebreak": None},
        })
        st.session_state["court_assignments"] = {}

        reset_keys = [
            "teams",
            "df_table",
            "reset_df",
            "groups",
            "groups_created",
            "group_names",
            "group_size",
            "incomplete_groups",
            "max_court",
            "selected_courts",
        ]

        for key in reset_keys:
            if key in st.session_state:
                del st.session_state[key]

        st.session_state["selected_courts"] = get_courts_for_type(selected)

        st.rerun()

    return selected


def ui_edit_team_names(df_table: pd.DataFrame, tournament_type: str) -> None:
    """
    Zeigt einen Data‑Editor, in dem nur die Spalte 'Team' editierbar ist.
    Zusätzlich wird ein versteckter Index‑Wert (`orig_idx`) mitgeführt,
    damit wir nach dem Editieren exakt wissen, welche Zeile zu welchem
    Original‑Datensatz gehört.
    """
    edit_df = df_table[["team"]]

    column_cfg = {
        "team": st.column_config.Column(
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
            df_full_edit = _rebuild_df_from_team_edit(
                original_df=df_table,
                edited_df=edited,
                tournament_type=tournament_type,
            )
            st.session_state["df_table"] = df_full_edit
            st.session_state["teams"] = df_full_edit["team"]
            st.session_state["groups"] = {}
            st.success("✅ Änderungen wurden übernommen!")
            st.rerun()

    with cols[1]:
        if st.button("🔄 Änderungen zurücksetzen", key="reset_team_name_changes"):
            st.warning("🔄 Änderungen zurückgesetzt!")
            st.session_state["df_table"] = st.session_state["reset_df"]
            st.session_state["teams"] = st.session_state["reset_df"]["team"]
            st.session_state["groups"] = {}
            st.rerun()


def ui_basic_settings(num_teams: int) -> int:
    """Grundlegende Turnier-Einstellungen (Teams, Felder, Zeit, Gruppen)"""
    st.metric(label="Anzahl Teams", value=num_teams)

    cols = st.columns([15, 15, 70])

    with cols[0]:
        groups_size = st.number_input(
            "Wie viele Teams sollen in einer Gruppe sein?",
            min_value=3,
            max_value=6,
            value=DEFAULT_GROUP_SIZE,
            step=1,
            key="groups_max"
        )

        num_groups = math.ceil(num_teams / groups_size)

        num_courts = len(st.session_state["selected_courts"])

        if num_groups > num_courts:
            st.warning(f"Es soll {num_groups} Gruppen geben, aber es gibt nur {num_courts} Felder.")

        if "num_groups" not in st.session_state or st.session_state["num_groups"] != num_groups:
            st.session_state["num_groups"] = num_groups
            st.session_state["group_size"] = groups_size
            st.session_state["groups"] = {}
            if "court_assignments" in st.session_state:
                st.session_state["court_assignments"] = {}

    with cols[1]:
        start_time = st.time_input(
            "Startzeit", value=datetime.time(10, 0), key="start_time"
        )

    with cols[2]:
        if num_groups:
            st.markdown("")
            text = get_text_msg_for_groups(num_teams, num_groups)
            st.markdown(
                f"<div style='display:flex; align-items:flex-end; justify-content:flex-start; height:38px; padding-left:10px;'><strong>{text}</strong></div>",
                unsafe_allow_html=True)

    return num_groups


def _format_option(team: str, df: pd.DataFrame) -> str:
    """Gibt den Anzeigetext für ein Team zurück."""
    row = df[df["team"] == team].iloc[0]
    return f"{team} ({row['name']}, {row['verein']})"


def ui_select_group_heads(group_df: pd.DataFrame, max_selections: int,) -> List[str]:
    """
    UI für die Auswahl der Gruppenköpfe über den Team‑Namen (aus Spalte 'Team').
    """
    options = list(group_df["team"])

    # Lambda-Funktion, die group_df mitnimmt
    format_func = lambda team: _format_option(team, group_df)

    selected_teams = st.multiselect(
        "Gruppenköpfe auswählen",
        options=options,
        max_selections=max_selections,
        key="group_heads_select",
        placeholder="Bitte Köpfe auswählen …",
        format_func=format_func,
    )

    return selected_teams


def ui_show_groups(groups: Dict[str, Group], group_df: pd.DataFrame) -> None:
    """UI zur Anzeige der erstellten Gruppen (4 Spalten pro Zeile)"""
    group_names = list(groups.keys())
    for i in range(0, len(group_names), 4):
        cols = st.columns(4)
        for j, name in enumerate(group_names[i : i + 4]):
            with cols[j]:
                grp = groups[name]
                st.markdown(f"### 🟦 **Gruppe {name}**")
                for team in grp.teams:
                    try:
                        club = group_df[group_df["team"] == team].iloc[0]["verein"]
                        if pd.isna(club):
                            st.write(f"**{team.lstrip()}**")
                        else:
                            st.write(f"**{team.lstrip()}** - {club}")
                    except IndexError:
                        pass


def ui_game_modes(incomplete_groups: List[str]) -> None:
    """UI zum Einstellen der Spiel‑Modi für komplette und unvollständige Gruppen."""
    st.subheader("🗂️ Spielmodus")

    game_mode = st.session_state["game_modes"]
    for key in ("complete", "incomplete"):
        val = game_mode.get(key)
        if isinstance(val, dict):
            # Konvertiere das dict in ein MatchSettings‑Objekt
            modus_raw = val["modus"]
            if isinstance(modus_raw, str):
                modus = UI_TO_MATCH_MODE[modus_raw]  # String → Enum
            else:
                modus = modus_raw
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
        # Tiebreak‑Feld nur anzeigen, wenn der Modus 2 order 3 Gewinnsätze ist
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
            tiebreak_complete = None

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

    st.session_state.setdefault("game_modes", {
        "complete": {"modus": "1 Satz", "points": DEFAULT_POINTS, "tiebreak": None},
        "incomplete": {"modus": "1 Satz", "points": DEFAULT_POINTS, "tiebreak": None},
    })
    # CSV auswählen / laden
    csv_path = ui_select_csv()
    if not csv_path:
        st.info("Bitte wähle eine CSV‑Datei aus oder lade sie hoch.")
        return

    df_all = load_csv(csv_path)

    # Turnier‑Kategorie auswählen
    col1, col2 = st.columns(2)

    with col1:
        tournament_type = ui_select_tournament_type(df_all)
        if not tournament_type:
            return

    df_category = df_all[df_all["Turnier"] == tournament_type]
    df_category = df_category[["Team", "Turnier", "Name", "Verein / Gruppe", "City"]]
    df_category = df_category.rename(columns={
        "Team": "team",
        "Turnier": "turnier",
        "Name": "name",
        "Verein / Gruppe": "verein",
        "City": "city",
    })

    st.session_state["teams"] = df_category["team"]
    st.session_state["reset_df"] = df_category

    # Teamliste editieren
    st.markdown("### ✏️ Zum Editieren der Teamliste")
    if "df_table" in st.session_state:
        df_category = st.session_state["df_table"]
    ui_edit_team_names(df_category, tournament_type)

    num_teams = len(df_category)
    number_groups = ui_basic_settings(num_teams)

    # Gruppen definieren
    selected_names = ui_select_group_heads(df_category, max_selections=number_groups, )

    if st.button("🛠️ Gruppen erstellen", key="create_groups_button", type="primary"):
        if "df_table" in st.session_state:
            df_category = st.session_state["df_table"]
        st.session_state["group_size"] = math.ceil(num_teams / number_groups)
        groups = create_groups(
            group_df=df_category,
            selected_names=selected_names,
            num_groups=number_groups,
            group_size=st.session_state["group_size"],
        )
        st.session_state["groups"] = groups
        st.session_state["group_names"] = list(groups.keys())
        st.success("✅ Gruppen wurden erstellt!")
        st.session_state["court_assignments"] = get_default_court_assignments(groups, st.session_state["selected_courts"])
        st.rerun()

    # Wenn bereits erstellt → Anzeige + weitere Optionen
    if "groups" in st.session_state:
        if st.session_state["groups"]:
            groups: Dict[str, Group] = st.session_state["groups"]
            ui_show_groups(groups, df_category)
        elif "groups_final" in st.session_state:
            groups: Dict[str, Group] = st.session_state["groups_final"]
            ui_show_groups(groups, df_category)
        else:
            groups = {}
    else:
        st.session_state["groups"] = {}
        groups = {}

    if groups:
        st.subheader("🔧 Konkrete Felder pro Gruppe zuweisen")

        selected_courts = st.session_state.get("selected_courts", [])
        max_total_courts = len(selected_courts)

        if max_total_courts == 0:
            st.warning("⚠️ Keine Felder verfügbar. Bitte wähle mindestens ein Feld aus.")
            st.stop()

        court_assignments = st.session_state.get("court_assignments", {})

        # Gruppen in Blöcken zu je 4 pro Zeile anzeigen
        group_names = list(groups.keys())
        for i in range(0, len(group_names), 4):
            group_block = group_names[i: i + 4]
            cols = st.columns(4)

            for j, name in enumerate(group_block):
                with cols[j]:
                    # Filtere ungültige Felder aus default
                    current_courts = court_assignments.get(name, [])
                    valid_courts = [c for c in current_courts if c in selected_courts]
                    if len(valid_courts) != len(current_courts):
                        st.warning(f"⚠️ Ungültige Felder entfernt: {set(current_courts) - set(selected_courts)}")

                    new_courts = st.multiselect(
                        f"Gruppe {name} – Felder",
                        options=selected_courts,
                        default=valid_courts,
                        key=f"assign_courts_{name}",
                        placeholder="Felder auswählen …",
                    )

                    st.session_state["court_assignments"][name] = new_courts

        total_assigned = sum(len(courts) for courts in st.session_state["court_assignments"].values())

        if total_assigned > max_total_courts:
            st.warning(f"⚠️ Du hast {total_assigned} Felder zugewiesen, aber nur {max_total_courts} verfügbar!")

        st.session_state["max_court"] = max_total_courts
        st.session_state["groups"] = groups

        # Ermittlung unvollständiger Gruppen
        incomplete = [name for name, grp in groups.items() if not grp.complete]
        st.session_state["incomplete_groups"] = incomplete

    # Spielmodi
        ui_game_modes(incomplete)
        groups = st.session_state["groups"]

        # Zuweisung der Spielmodus
        for name, grp in groups.items():
            if grp.complete:
                grp.settings = st.session_state["game_modes"]["complete"]
            else:
                grp.settings = st.session_state["game_modes"]["incomplete"]

        st.session_state["groups_final"] = groups

    # Turnier erstellen
    if st.button("Turnier erstellen", key="create_tournament_button", type="primary",):
        # Feldbelegungen speichern
        total_assigned = sum(len(courts) for courts in st.session_state["court_assignments"].values())
        groups = st.session_state["groups_final"]
        if total_assigned > st.session_state["max_court"]:
            st.error(f"❌ Zu viele Felder zugewiesen! Nur {st.session_state["max_court"]} verfügbar.")
        else:
            for name, group in groups.items():
                group.assigned_courts = st.session_state["court_assignments"][name]
            assignments = st.session_state["court_assignments"]
            if assignments:
                # Erstelle eine Liste von Formatierungen: "Gruppe X: Feld Y,Z"
                parts = []
                for group_name, courts in assignments.items():
                    courts_str = ", ".join(map(str, courts))
                    parts.append(f"**Gruppe {group_name}:** Feld {courts_str}")

                line = " | ".join(parts)
                st.success(f"{line}")
            else:
                st.info("Keine Felder zugewiesen.")

        name = "TBO " + tournament_type + " " + str(datetime.datetime.now().year)
        tournament = Tournament(name=name, type=tournament_type, courts=st.session_state["selected_courts"], teams=st.session_state["teams"])
        group_list: List[Group] = list(groups.values())
        stage = Stage(id="Vorrunde", type=StageType.GROUP, teams=st.session_state["teams"],
                      groups=group_list)

        tournament.add_stage(stage)
        tournament.schedule_stage(stage.id)

        year = datetime.datetime.now().year
        name = f"{tournament.type} {str(year)}"
        save_tournament(tournament, name)

        st.success(f"✅ Das {tournament_type}-Turnier wurde erstellt!")

    # Aufräumen (temporäre Upload‑Datei)
    if csv_path.name.startswith("tmp_"):
        try:
            csv_path.unlink(missing_ok=True)
        except Exception as exc:
            st.warning(f"Konnte temporäre Datei nicht löschen: {exc}")
