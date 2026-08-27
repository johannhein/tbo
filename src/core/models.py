from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Any, Tuple

import pandas as pd

from config import SCHEMA_MAP
from config.constants import MIN_DIFF

MatchID = int
StageID = str

# -------------------------------------------------
# Enums
# -------------------------------------------------
class MatchStatus(Enum):
    """Zustand eines Matches im Turnier."""
    PENDING   = auto()   # noch nicht gestartet / keine Sätze
    FINISHED  = auto()   # Sieger ermittelt
    CANCELLED = auto()   # abgesagt (z. B. wegen Verletzung)


class StageType(Enum):
    GROUP = "group"
    KNOCKOUT = "knockout"
    CROSSOVER = "crossover"
    FINAL = "final"
    PLAYOFF = "playoff"

class MatchMode(Enum):
    BEST_OF_3 = "2 Gewinnsätze"
    BEST_OF_5 = "3 Gewinnsätze"
    SETS_3 = "3 Sätze"
    SETS_2 = "2 Sätze"
    SETS_1 = "1 Satz"

# Mapping für die Spielpläne
MATCH_MODE_TO_SETS = {
    MatchMode.SETS_1: ["1. Satz"],
    MatchMode.SETS_2: ["1. Satz", "2. Satz"],
    MatchMode.SETS_3: ["1. Satz", "2. Satz", "3. Satz"],
    MatchMode.BEST_OF_3: ["1. Satz", "2. Satz", "3. Satz"],
    MatchMode.BEST_OF_5: ["1. Satz", "2. Satz", "3. Satz", "4. Satz", "5. Satz"],
}

# -------------------------------------------------
# Dataclasses
# -------------------------------------------------
@dataclass
class Match:
    id: MatchID
    court: int
    t1: str
    t2: str
    ref: Optional[str] = None
    settings: Optional[MatchSettings] = None
    sets: Dict[int, Tuple[int, int]] = field(default_factory=dict)
    status: MatchStatus = MatchStatus.PENDING

    @property
    def score(self) -> Tuple[int, int] | None:
        """
        Gibt die Satz‑Bilanz als String zurück, z.B. "2,0".
        Wenn noch keine Sätze gespeichert sind, wird "–" zurückgegeben.
        """
        if not self.sets:
            return None
        t1_won = sum(1 for p1, p2 in self.sets.values() if p1 > p2)
        t2_won = sum(1 for p1, p2 in self.sets.values() if p2 > p1)
        return t1_won, t2_won

    @property
    def score_str(self) -> str:
        """Mensch‑lesbare Darstellung, z.B. "2:1" oder "–"."""
        s = self.score
        return f"{s[0]}:{s[1]}" if s else "–"

    @property
    def winner(self) -> Optional[str]:
        """Name des Gewinners, falls das Match bereits beendet ist."""
        s = self.score
        if s is None:
            return None
        if s[0] > s[1]:
            return self.t1
        if s[1] > s[0]:
            return self.t2
        if s[1] == s[0]:
            return "unentschieden"
        return None

    @property
    def loser(self) -> Optional[str]:
        """Name des Verlierers, falls das Match bereits beendet ist."""
        s = self.score
        if s is None:
            return None
        if s[0] < s[1]:
            return self.t1
        if s[1] < s[0]:
            return self.t2
        if s[1] == s[0]:
            return "unentschieden"
        return None

    @property
    def points(self) -> Tuple[int, int] | None:
        """
        Gibt die Satz‑Bilanz als String zurück, z.B. "2,0".
        Wenn noch keine Sätze gespeichert sind, wird "–" zurückgegeben.
        """
        if not self.sets:
            return None

        team1 = 0
        team2 = 0

        for p1, p2 in self.sets.values():
            team1 += p1
            team2 += p2
        return team1, team2

    def _validate_set(self, set_num: int, p1: int, p2: int) -> None:
        """Prüft, ob ein einzelner Satz plausibel ist."""
        num_sets = len(MATCH_MODE_TO_SETS.get(self.settings.modus))
        if MIN_DIFF:
            min_advantage = 2
        else:
            min_advantage = 1
        if abs(p1 - p2) < min_advantage:
            raise ValueError( f"Ein Satz muss mindestens {min_advantage} Punkt/Punkte Vorsprung haben. Ergebnis: {p1}:{p2}")
        if set_num > num_sets:
            raise ValueError(f"Das Match hat maximal nur {str(num_sets)} Satz/Sätze.")
        if not self.settings.tiebreak or num_sets > set_num:
            if not (p1 >= self.settings.points or p2 >= self.settings.points):
                raise ValueError(f"Kein Team hat die erforderlichen {self.settings.points} Punkte im {set_num}. Satz erreicht. Ergebnis: {p1}:{p2}")
        if self.settings.tiebreak and num_sets == set_num:
            if not (p1 >= self.settings.tiebreak or p2 >= self.settings.tiebreak):
                raise ValueError(f"Kein Team hat die erforderlichen {self.settings.tiebreak} Punkte im {set_num}. Satz erreicht. Ergebnis: {p1}:{p2}")


    @classmethod
    def create(cls, match_id: int, court: int, t1: str, t2: str, ref: Optional[str] = None,
               settings_match: Optional[MatchSettings] = None) -> Match:
        """Factory‑Methode – gibt automatisch die nächste globale Match‑ID zurück."""
        return cls(id=match_id, court=court, t1=t1, t2=t2, ref=ref, settings=settings_match)

    def add_set(self, set_num: int, p1: int, p2: int) -> None:
        """Fügt einen neuen Satz zum Match hinzu und aktualisiert den Status."""
        self._validate_set(set_num, p1, p2)
        self.sets[set_num] = p1, p2

        # Status‑Logik
        if self.winner is not None:
            self.status = MatchStatus.FINISHED

    def add_result(self, result: Dict[int, Tuple[int:int]]) -> None:
        """Fügt einen neuen Satz zum Match hinzu und aktualisiert den Status."""
        for set_number, (player1_score, player2_score) in result.items():
            self._validate_set(set_number, player1_score, player2_score)
            self.sets[set_number] = (player1_score, player2_score)

        self.status = MatchStatus.FINISHED

    def to_dict(self) -> dict:
        """Serialisiert das Match für JSON‑Export o. Ä."""
        return {
            "id": str(self.id),
            "court": self.court,
            "t1": self.t1,
            "t2": self.t2,
            "referee": self.ref if self.ref else None,
            "sets": self.sets,
            "status": self.status.name,
        }


@dataclass
class Tournament:
    name: str
    type: str  # z. B. "Damen", "Herren" "Quattro"
    courts: List[int]
    teams: List[str]
    stages: Dict[StageID, Stage] = field(default_factory=dict)
    current_stage_id: str | None = None
    status: str = "planning"  # planning, running, finished

    def add_stage(self, stage: Stage) -> None:
        """Fügt eine neue Stage hinzu – wirft bei doppelter ID."""
        if stage.id in self.stages:
            raise ValueError(f"Stage‑ID {stage.id!r} existiert bereits.")
        self.stages[stage.id] = stage

    def get_stage(self, stage_id: StageID) -> Stage:
        """Liefert die Stage oder wirft KeyError."""
        return self.stages[stage_id]

    def remove_stage(self, stage_id: StageID) -> None:
        """Entfernt eine Stage (falls vorhanden)."""
        self.stages.pop(stage_id, None)

    def all_stages(self) -> List[Stage]:
        """Gibt alle Stages in Einfüge‑Reihenfolge zurück."""
        return list(self.stages.values())

    def ids_stages(self) -> List[StageID]:
        """Liste aller IDs (ebenfalls in Einfüge‑Reihenfolge)."""
        return list(self.stages.keys())

    def schedule_stage(self, stage_id: StageID):
        stage = self.get_stage(stage_id)

        match_id = 1
        for group in stage.groups:
            match_id = group.build_matches_from_schema(match_id)


@dataclass
class Stage:
    id: StageID
    type: StageType
    teams: List[str]
    groups: List[Group] | None = None
    match_list: List[Match] | None = None
    prev_stage: StageID = None
    next_stages: List[StageID] = field(default_factory=list)  # IDs der nächsten Runden
    is_completed: bool = False
    results: Dict[str, Any] = field(default_factory=dict)  # z. B. Platzierungen, Gewinner

    @property
    def table(self) -> pd.DataFrame:
        """
        Erstellt eine Gesamttabelle für die Stage, sortiert nach:
        1. Platzierung in der Gruppe
        2. Punkte
        3. Sätze-Differenz
        4. Kleine Punkte
        """
        team_data = self._collect_team_data()
        if not team_data:
            return pd.DataFrame(columns=["Rang", "Team", "Gruppe", "Platzierung", "Punkte", "Sätze", "Kleine Punkte"])

        df = pd.DataFrame(team_data)

        def parse_sets(sets_str: str) -> int:
            try:
                won, lost = map(int, sets_str.split(":"))
                return won - lost
            except:
                return 0

        df["Sätze-Diff"] = df["Sätze"].apply(parse_sets)

        # Sortieren: Platzierung → Punkte → Sätze-Diff → Kleine Punkte
        df = df.sort_values(
            by=["Platzierung", "Punkte", "Sätze-Diff", "Kleine Punkte"],
            ascending=[True, False, False, False]
        ).reset_index(drop=True)

        # Rang neu setzen
        df["Rang"] = range(1, len(df) + 1)

        # Spaltenreihenfolge
        return df[["Rang", "Team", "Gruppe", "Platzierung", "Punkte", "Sätze", "Kleine Punkte"]]

    @property
    def placement_tables(self) -> Dict[int, pd.DataFrame]:
        """
        Gibt ein Dictionary mit Tabellen für jede Platzierung zurück:
        - key: Platzierung (1, 2, 3, ...)
        - value: pd.DataFrame mit allen Teams, die diese Platzierung in ihrer Gruppe erreicht haben
        """
        team_data = self._collect_team_data()
        if not team_data:
            return {}

        df = pd.DataFrame(team_data)

        # Sortiere nach Platzierung
        df = df.sort_values("Platzierung")

        placement_tables = {}

        # Für jede Platzierung
        for rank in df["Platzierung"].unique():
            subset = df[df["Platzierung"] == rank].copy()
            subset = subset.sort_values(
                by=["Punkte", "Sätze", "Kleine Punkte"],
                ascending=[False, False, False]
            ).reset_index(drop=True)

            # Rang innerhalb der Platzierung neu setzen
            subset["Rang"] = range(1, len(subset) + 1)

            # Spaltenreihenfolge
            subset = subset[["Rang", "Team", "Gruppe", "Punkte", "Sätze", "Kleine Punkte"]]

            placement_tables[rank] = subset

        return placement_tables

    def _collect_team_data(self) -> List[Dict[str, Any]]:
        """Sammelt alle Teams aus allen Gruppen mit ihren Statistiken."""
        if not self.groups:
            return []

        all_teams = []

        for group in self.groups:
            group_table = group.table

            for _, row in group_table.iterrows():
                all_teams.append({
                    "Team": row["Team"],
                    "Gruppe": group.name,
                    "Platzierung": row["Rang"],
                    "Punkte": row["Punkte"],
                    "Sätze": row["Sätze"],
                    "Kleine Punkte": row["Kleine Punkte"],
                })

        return all_teams

    def add_team(self, team_name: str):
        if team_name not in self.teams:
            self.teams.append(team_name)

    def add_match(self, match: Match):
        self.match_list.append(match)

    def is_ready_for_next(self) -> bool:
        # Prüft, ob alle Matches abgeschlossen sind
        return all(match.time is not None for match in self.match_list) and len(self.match_list) > 0

    def __repr__(self):
        return f"Stage(id={self.id}, type={self.type}, teams={self.teams}, match_list={self.match_list}, groups={self.groups})"


@dataclass
class Group:
    name: str
    teams: List[str]
    teams_target: int
    assigned_courts: Optional[List[int]] = None
    settings: Optional[MatchSettings] = None
    match_list: List[Match] | None = None
    _table_cache: Optional[pd.DataFrame] = None
    _last_match_list_hash: Optional[int] = None

    def __init__(self, name: str, teams: List[str], teams_target: int):
        self.name = name
        self.teams = teams or []
        self.teams_target = teams_target

    @property
    def num_teams(self) -> int:
        return len(self.teams)

    @property
    def complete(self) -> bool:
        if self.teams_target == self.num_teams:
            return True
        else:
            return False

    @property
    def num_courts(self) -> int:
        return len(self.assigned_courts or [])

    @property
    def schedule_schema(self) -> List[dict]:
        """Gibt das passende Schema Spielplan zurück, basierend auf Gruppengröße und verfügbaren Feldern."""
        key = (self.num_teams, self.num_courts)

        try:
            return SCHEMA_MAP[key]
        except KeyError as exc:
            raise ValueError(
                f"Kein vordefiniertes Schema für {self.num_teams} Teams "
                f"und {self.num_courts} Feld(er). "
                f"Verfügbare Kombinationen: {list(SCHEMA_MAP.keys())}"
            ) from exc

    @property
    def table(self) -> pd.DataFrame:
        """
        Berechnet die aktuelle Gruppentabelle aus den Match-Ergebnissen.
        Cache: Nur neu berechnet, wenn sich die match_list geändert hat.
        """
        # Hash der match_list für Änderungserkennung
        current_hash = hash(tuple((m.t1, m.t2, m.score, m.points) for m in (self.match_list or [])))

        if self._table_cache is not None and self._last_match_list_hash == current_hash:
            return self._table_cache

        # Wenn keine Matches vorhanden → leere Tabelle
        if not self.match_list:
            return pd.DataFrame(columns=["Rang", "Team", "Spiele", "Sätze", "Kleine Punkte", "Punkte"])

        # Statistiken berechnen (wie in deiner render_group_table-Funktion)
        team_stats = {}

        for match in self.match_list:
            t1, t2 = match.t1, match.t2
            for team, name in [(t1, t1), (t2, t2)]:
                if name not in team_stats:
                    team_stats[name] = {
                        "Spiele": 0,
                        "Siege": 0,
                        "Niederlagen": 0,
                        "Punkte": 0,
                        "Sätze": 0,
                        "Sätze-Verhältnis": (0, 0),
                        "Kleine-Punkte": 0,
                    }

            if match.score is None:
                continue

            # Spiele zählen
            team_stats[t1]["Spiele"] += 1
            team_stats[t2]["Spiele"] += 1

            # Punkte (2 für Sieg, 1 für unentschieden)
            if match.score[0] > match.score[1]:
                team_stats[t1]["Punkte"] += 2
            elif match.score[1] > match.score[0]:
                team_stats[t2]["Punkte"] += 2
            elif match.score[1] == match.score[0]:
                team_stats[t1]["Punkte"] += 1
                team_stats[t2]["Punkte"] += 1

            # Sätze
            team_stats[t1]["Sätze"] += match.score[0]
            team_stats[t2]["Sätze"] += match.score[1]

            # Kleine Punkte (Differenz)
            team_stats[t1]["Kleine-Punkte"] += match.points[0] - match.points[1]
            team_stats[t2]["Kleine-Punkte"] += match.points[1] - match.points[0]

        # Sätze-Verhältnis berechnen (gesamt gewonnen / verloren)
        for name in team_stats:
            sets_won = team_stats[name]["Sätze"]
            sets_lost = 0
            for match in self.match_list:
                if name not in (match.t1, match.t2):
                    continue
                if match.score is None:
                    continue
                if match.t1 == name:
                    sets_lost += match.score[1]
                else:
                    sets_lost += match.score[0]
            team_stats[name]["Sätze-Verhältnis"] = (sets_won, sets_lost)

        # Sortieren: Punkte → Sätze → Kleine Punkte
        sorted_teams = sorted(
            team_stats.items(),
            key=lambda x: (x[1]["Punkte"], x[1]["Sätze-Verhältnis"][0] - x[1]["Sätze-Verhältnis"][1],
                           x[1]["Kleine-Punkte"]),
            reverse=True,
        )

        # Tabelle erstellen
        table_data = []
        for i, (name, stats) in enumerate(sorted_teams):
            table_data.append({
                "Rang": i + 1,
                "Team": name,
                "Spiele": stats["Spiele"],
                "Sätze": f"{stats['Sätze-Verhältnis'][0]}:{stats['Sätze-Verhältnis'][1]}",
                "Kleine Punkte": stats["Kleine-Punkte"],
                "Punkte": stats["Punkte"],
            })

        df = pd.DataFrame(table_data)

        # Cache speichern
        self._table_cache = df
        self._last_match_list_hash = current_hash

        return df

    def add_head(self, team_name: str) -> None:
        """
        Fügt ein neues Team an die erste Position der Gruppe ein.
        """
        if team_name in self.teams:
            self.teams.remove(team_name)
        if self.complete:
            raise ValueError(
                f"Gruppe '{self.name}' ist bereits voll ({self.teams_target} Teams)."
            )
        self.teams.insert(0, team_name)

    def add_team(self, team_name: str):
        if self.complete:
            raise ValueError(f"Gruppe '{self.name}' ist bereits voll ({self.teams_target} Teams).")
        else:
            if team_name not in self.teams:
                self.teams.append(team_name)

    def swap_teams(self, index1: int, index2: int):
        """
        Tauscht zwei Teams in der Liste an den gegebenen Indizes.

        :param index1: Index des ersten Teams
        :param index2: Index des zweiten Teams
        :raises IndexError: Wenn ein Index ungültig ist
        :raises ValueError: Wenn die Indizes gleich sind
        """
        if not (0 <= index1 < len(self.teams)):
            raise IndexError(f"Index {index1} ist außerhalb des gültigen Bereichs (0 bis {len(self.teams) - 1})")
        if not (0 <= index2 < len(self.teams)):
            raise IndexError(f"Index {index2} ist außerhalb des gültigen Bereichs (0 bis {len(self.teams) - 1})")
        if index1 == index2:
            raise ValueError("Beide Indizes sind gleich – kein Tausch nötig.")

        self.teams[index1], self.teams[index2] = self.teams[index2], self.teams[index1]

    def swap_teams_by_name(self, team_name1: str, team_name2: str):
        """
        Tauscht zwei Teams in der Liste anhand ihres Namens.

        :param team_name1: Name des ersten Teams
        :param team_name2: Name des zweiten Teams
        :raises ValueError: Wenn eines der Teams nicht gefunden wird oder die Namen gleich sind
        """
        if team_name1 == team_name2:
            raise ValueError("Beide Team-Namen sind gleich – kein Tausch nötig.")

        try:
            index1 = self.teams.index(team_name1)
            index2 = self.teams.index(team_name2)
        except ValueError as e:
            raise ValueError(f"Ein Team wurde nicht gefunden: {e}")

        self.teams[index1], self.teams[index2] = self.teams[index2], self.teams[index1]

    def assign_courts(self, court_numbers: List[int]):
        """Weist konkrete Felder zu."""
        if not court_numbers:
            raise ValueError("Mindestens ein Feld muss zugewiesen werden.")
        self.assigned_courts = sorted(court_numbers)

    def build_matches_from_schema(self, match_index: int = 1) -> int:
        """
        Nutzt self.schedule_schema und füllt self.match_list mit echten
        Match‑Instanzen.

        * Die Feld‑Belegung rotiert über self.assigned_courts.
        * Team‑IDs aus dem Schema (1‑basiert) werden in die tatsächlichen
          Team‑Namen (Strings) übersetzt.
        """
        self.match_list = []

        # Mapping: 1‑basierte ID → Team‑Name (wie im Schema verwendet)
        id_to_name = {i + 1: name for i, name in enumerate(self.teams)}

        # Durch das Schema iterieren und Match‑Objekte bauen
        for round_dict in self.schedule_schema:
            for m in round_dict["Matches"]:
                # Team‑Namen holen
                t1_name = id_to_name[m["Team1"]]
                t2_name = id_to_name[m["Team2"]]
                ref_name = (
                    id_to_name[m["Ref"]] if m["Ref"] is not None else None
                )

                court_id = self.assigned_courts[
                    match_index % len(self.assigned_courts)
                ]

                new_match = Match.create(match_id=match_index, court=court_id, t1=t1_name, t2=t2_name, ref=ref_name,
                                         settings_match=self.settings)
                self.match_list.append(new_match)

                match_index += 1

        return match_index


@dataclass
class MatchSettings:
    modus: MatchMode
    points: int
    tiebreak: int | None = None

    def to_dict(self) -> dict:
        return {
            "modus": self.modus,
            "points": self.points,
            "tiebreak": self.tiebreak
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MatchSettings":
        return cls(
            modus=data["modus"],
            points=data["points"],
            tiebreak=data.get("tiebreak")
        )


@dataclass
class Team:
    id: str
    name: str
    verein: str

    def __str__(self):
        return self.name
