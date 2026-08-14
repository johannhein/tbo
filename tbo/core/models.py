from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple

MatchID = str
StageID = str


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
    # set_num: int
    t1: str
    t2: str
    ref: str | None
    group: str | None = None
    time: str | None = None  # z.B. "14:00"
    sets: List[Tuple[int, int]] | None = None
    stage_id: str | None = None  # auf welcher Runde das Spiel stattfindet

    @property
    def score(self) -> Tuple[int, int] | None:
        """
        Gibt die Satz‑Bilanz als String zurück, z.B. "2:0".
        Wenn noch keine Sätze gespeichert sind, wird "–" zurückgegeben.
        """
        if not self.sets:
            return None  # kein Ergebnis vorhanden

        t1_won = 0
        t2_won = 0

        for idx, (p1, p2) in enumerate(self.sets, start=1):
            if p1 > p2:
                t1_won += 1
            elif p2 > p1:
                t2_won += 1
            else:
                pass

        return t1_won,t2_won


    @property
    def winner(self) -> str | None:
        if self.score[0] > self.score[1]:
            return self.t1
        elif self.score[0] < self.score[1]:
            return self.t2
        else:
            return None

    @property
    def loser(self) -> str | None:
        if self.score[0] < self.score[1]:
            return self.t1
        elif self.score[0] > self.score[1]:
            return self.t2
        else:
            return None


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

    def start_tournament(self):
        if not self.stages:
            raise ValueError("No stages defined!")
        self.status = "running"
        # Starte mit erster Runde
        first_stage_id = next(iter(self.stages))
        self.current_stage_id = first_stage_id

    def advance_to_next_stage(self, stage_id: str) -> bool:
        stage = self.get_stage(stage_id)
        if not stage or stage.is_completed:
            return False

        # Prüfe, ob alle Matches abgeschlossen sind
        if not stage.is_ready_for_next():
            return False

        # Entscheide, welche Runden als nächstes kommen
        # → Hier wird die Logik für überkreuzspiele, K.O. etc. implementiert
        next_stages = self._determine_next_stages(stage)
        for next_stage_id in next_stages:
            self.stages[next_stage_id].is_completed = False
            self.stages[next_stage_id].results = {}

        self.current_stage_id = next_stages[0] if next_stages else None
        return True

    def _determine_next_stages(self, current_stage: Stage) -> List[str]:
        """
        Dynamische Entscheidung: Was kommt nach dieser Runde?
        Beispiel: Nach Gruppenphase → überkreuzspiele oder K.O.
        """
        if current_stage.type == StageType.GROUP:
            # Nach Gruppenphase: überkreuzspiele oder K.O.?
            # Beispiel: 1. und 2. aus jeder Gruppe → Viertelfinale
            return self._create_knockout_from_groups(current_stage)

        elif current_stage.type == StageType.KNOCKOUT:
            # Nach Viertelfinale → Halbfinale → Finale
            if len(current_stage.teams) == 8:
                return ["semifinal_1", "semifinal_2"]
            elif len(current_stage.teams) == 4:
                return ["final"]
            else:
                return []

        elif current_stage.type == StageType.CROSSOVER:
            # Überkreuzspiele → K.O.?
            return self._create_knockout_from_crossover(current_stage)

        return []

    def _create_knockout_from_groups(self, group_stage: Stage) -> List[str]:
        # Beispiel: 4 Gruppen, 2 Teams pro Gruppe → 8 Teams → Viertelfinale
        # Hier: Logik, wie Teams aus Gruppen ausgewählt werden
        # z. B. 1. und 2. aus jeder Gruppe
        teams = []
        for group_id, group in self.stages.items():
            if group.type == StageType.GROUP:
                # Annahme: Gruppen haben Platzierungen in results
                # z. B. group.results["rankings"] = ["team_a", "team_b", ...]
                if "rankings" in group.results:
                    teams.extend(group.results["rankings"][:2])  # Top 2

        # Erstelle Viertelfinale
        knockout_stages = []
        for i in range(0, len(teams), 2):
            if i + 1 < len(teams):
                stage_id = f"quarterfinal_{i//2 + 1}"
                stage = Stage(
                    id=stage_id,
                    type=StageType.KNOCKOUT,
                    modus=MatchMode.BEST_OF_3,
                    settings={"sets": "3", "points": 25, "tiebreak": 15},
                    teams=[teams[i], teams[i+1]],
                    next_stages=[f"semifinal_{i//4 + 1}"]
                )
                self.add_stage(stage)
                knockout_stages.append(stage_id)

        return knockout_stages

    def _create_knockout_from_crossover(self, crossover_stage: Stage) -> List[str]:
        # Beispiel: überkreuzspiele → K.O. mit 4 Teams → Halbfinale
        # Hier: Logik, wie Teams aus überkreuzspiele kommen
        # z. B. Gewinner der überkreuzspiele → Halbfinale
        teams = [match.winner for match in crossover_stage.matches if match.winner]
        # Erstelle Halbfinale
        semifinal_stages = []
        for i in range(0, len(teams), 2):
            if i + 1 < len(teams):
                stage_id = f"semifinal_{i//2 + 1}"
                stage = Stage(
                    id=stage_id,
                    type=StageType.KNOCKOUT,
                    modus=MatchMode.BEST_OF_3,
                    settings={"sets": "3", "points": 25, "tiebreak": 15},
                    teams=[teams[i], teams[i+1]],
                    next_stages=["final"]
                )
                self.add_stage(stage)
                semifinal_stages.append(stage_id)
        return semifinal_stages


@dataclass
class Stage:
    id: StageID
    type: StageType
    teams: List[str]
    groups: List[Group] | None = None
    matches: List[Match] | None = None
    prev_stage: StageID = None
    next_stages: List[StageID] = field(default_factory=list)  # IDs der nächsten Runden
    is_completed: bool = False
    results: Dict[str, Any] = field(default_factory=dict)  # z. B. Platzierungen, Gewinner

    def add_team(self, team_name: str):
        if team_name not in self.teams:
            self.teams.append(team_name)

    def add_match(self, match: Match):
        self.matches.append(match)

    def is_ready_for_next(self) -> bool:
        # Prüft, ob alle Matches abgeschlossen sind
        return all(match.time is not None for match in self.matches) and len(self.matches) > 0

    def __repr__(self):
        return f"Stage(id={self.id}, type={self.type}, teams={self.teams}, matches={self.matches}, groups={self.groups})"


@dataclass
class Group:
    name: str
    teams: List[str]
    teams_target: int
    assigned_courts: List[int] = field(default_factory=list)
    settings: MatchSettings | None = None

    @property
    def num_teams(self) -> int:
        return len(self.teams)

    @property
    def complete(self) -> bool:
        if self.teams_target == self.num_teams:
            return True
        else:
            return False

    def __init__(self, name: str, teams: List[str], teams_target: int):
        self.name = name
        self.teams = teams or []
        self.teams_target = teams_target

    def add_head(self, team_name: str):
        self.teams.append(team_name)

    def add_member(self, team_name: str):
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
