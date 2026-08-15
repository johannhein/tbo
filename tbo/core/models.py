from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Any, Tuple

from services.schedule import SCHEMA_MAP

MatchID = int
StageID = str


class MatchStatus(Enum):
    """Zustand eines Matches im Turnier."""
    PENDING   = auto()   # noch nicht gestartet / keine Sätze
    FINISHED  = auto()   # Sieger ermittelt
    CANCELLED = auto()   # abgesagt (z. B. wegen Verletzung)



class StageType(Enum):
    GROUP = "group"
    KNOCKOUT = "knockout"
    CROSSOVER = "crossover"  # überkreuzspiele
    FINAL = "final"
    PLAYOFF = "playoff"     # z. B. 3. Platz, 5. Platz etc.


class MatchMode(Enum):
    BEST_OF_3 = "best_of_3"
    BEST_OF_5 = "best_of_5"
    SETS_3 = "3 Sätze"  # 3 Sätze, kein Tiebreak
    SETS_2 = "2 Sätze"  # 2 Sätze, kein Tiebreak
    SETS_1 = "1 Satz"   # 1 Satz, kein Tiebreak

# -------------------------------------------------
# Mapping von UI‑Text → MatchMode‑Enum
# -------------------------------------------------
SET_MODE_MAP: dict[str, MatchMode] = {
    "1 Satz":   MatchMode.SETS_1,
    "2 Sätze":  MatchMode.SETS_2,
    "3 Sätze":  MatchMode.SETS_3,
    "Best of 3": MatchMode.BEST_OF_3,
    "Best of 5": MatchMode.BEST_OF_5,
}


MATCH_MODE_TO_UI = {
    MatchMode.SETS_1: "1 Satz",
    MatchMode.SETS_2: "2 Sätze",
    MatchMode.SETS_3: "3 Sätze",
    MatchMode.BEST_OF_3: "Best of 3",
    MatchMode.BEST_OF_5: "Best of 5",
    # falls du noch weitere Modi hast, ergänze sie hier
}

# Und das Gegenstück (UI‑Text → Enum) – du hast das bereits als SET_MODE_MAP
UI_TO_MATCH_MODE = {v: k for k, v in MATCH_MODE_TO_UI.items()}


@dataclass
class Match:
    id: MatchID
    court: int
    t1: str
    t2: str
    ref: Optional[str] = None
    sets: List[Tuple[int, int]] = field(default_factory=list)
    status: MatchStatus = MatchStatus.PENDING

    @property
    def score(self) -> Tuple[int, int] | None:
        """
        Gibt die Satz‑Bilanz als String zurück, z.B. "2,0".
        Wenn noch keine Sätze gespeichert sind, wird "–" zurückgegeben.
        """
        if not self.sets:
            return None

        t1_won = sum(1 for p1, p2 in self.sets if p1 > p2)
        t2_won = sum(1 for p1, p2 in self.sets if p2 > p1)

        return t1_won,t2_won

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
        return None

    @staticmethod
    def _validate_set(p1: int, p2: int) -> None:
        """Prüft, ob ein einzelner Satz plausibel ist. Für Tennis (Best‑of‑3) gelten z.B.:
        - 0≤Punkte≤7
        - kein Unentschieden
        - ein Spieler muss mindestens 6 Punkte haben und mit mind. 2 Punkten Vorsprung gewinnen,
          außer bei 7‑6 (Tie‑Break).
        """
        if not (0 <= p1 <= 7 and 0 <= p2 <= 7):
            raise ValueError("Punkte müssen zwischen 0 und 7 liegen.")
        if p1 == p2:
            raise ValueError("Ein Satz darf nicht unentschieden enden.")
        # Minimal‑Gewinn‑Regel
        if max(p1, p2) < 6:
            raise ValueError("Ein Satz muss mit mindestens 6 Punkten gewonnen werden.")
        if abs(p1 - p2) < 2 and max(p1, p2) != 7:
            raise ValueError("Gewinner muss mit mindestens 2 Punkten Unterschied gewinnen "
                             "(außer 7‑6).")

    @classmethod
    def create(cls, id: int, court: int, t1: str, t2: str, ref: Optional[str] = None) -> Match:
        """Factory‑Methode – gibt automatisch die nächste globale Match‑ID zurück."""
        return cls(id=id, court=court, t1=t1, t2=t2, ref=ref)

    def add_set(self, p1: int, p2: int) -> None:
        """Fügt einen neuen Satz zum Match hinzu und aktualisiert den Status."""
        self._validate_set(p1, p2)
        self.sets.append((p1, p2))

        # Status‑Logik
        if self.winner is not None:
            self.status = MatchStatus.FINISHED

    def add_result(self, result: List[Tuple[int:int]]) -> None:
        """Fügt einen neuen Satz zum Match hinzu und aktualisiert den Status."""
        for set_score in result:
            self._validate_set(set_score[0], set_score[0])
            self.sets.append((set_score[0], set_score[0]))

        self.status = MatchStatus.FINISHED

    def to_dict(self) -> dict:
        """Serialisiert das Match für JSON‑Export o. Ä."""
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
    stages: Dict[str, Stage] = field(default_factory=dict)
    current_stage_id: str | None = None
    status: str = "planning"  # planning, running, finished

    def add_stage(self, stage: Stage):
        self.stages[stage.id] = stage

    def get_stage(self, stage_id: str) -> Optional[Stage]:
        return self.stages.get(stage_id)


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
    assigned_courts: List[int] = field(default_factory=list)
    settings: Optional[MatchSettings] = None
    match_list: List[Match] | None = None

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

    def __init__(self, name: str, teams: List[str], teams_target: int):
        self.name = name
        self.teams = teams or []
        self.teams_target = teams_target

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

    def build_matches_from_schema(self) -> None:
        """
        Nutzt self.schedule_schema und füllt self.match_list mit echten
        Match‑Instanzen.

        * Die Feld‑Belegung rotiert über self.assigned_courts.
        * Team‑IDs aus dem Schema (1‑basiert) werden in die tatsächlichen
          Team‑Namen (Strings) übersetzt.
        """
        if self.match_list:
            self.match_list.clear()

        # Mapping: 1‑basierte ID → Team‑Name (wie im Schema verwendet)
        id_to_name = {i + 1: name for i, name in enumerate(self.teams)}

        # Rotations‑Index für die Feld‑Belegung
        match_index = 1

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

                new_match = Match.create(id=match_index, court=court_id, t1=t1_name, t2=t2_name, ref=ref_name)
                self.match_list.append(new_match)

                match_index += 1



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
