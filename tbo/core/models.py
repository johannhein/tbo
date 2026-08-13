# bvc_cup/models/tournament.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Literal, Optional, Any

MatchID = str


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


@dataclass
class Match:
    id: MatchID
    court: int
    t1: str
    t2: str
    ref: str | None
    group: str | None = None
    time: str | None = None  # z.B. "14:00"
    winner: str | None = None  # nach Spiel
    score: Dict[str, int] | None = None  # z.B. {"t1": 2, "t2": 3} für 2:3
    sets: Dict[int, List[int, int]] | None = None
    stage_id: str | None = None  # auf welcher Runde das Spiel stattfindet

    def set_result(self, winner: str, score: Dict[str, int]):
        self.winner = winner
        self.score = score
        self.time = self.time or "played"  # oder aktuelle Zeit

@dataclass
class Tournament:
    name: str
    type: str  # z. B. "Damen", "Herren" "Quattro"
    courts: List[int]
    stages: Dict[str, Stage] = field(default_factory=dict)
    current_stage_id: Optional[str] = None
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
    id: str  # z. B. "round_1", "group_a", "quarterfinals"
    type: StageType
    modus: MatchMode
    settings: Dict[str, Any] = field(default_factory=dict)
    matches: List[Match] = field(default_factory=list)
    teams: List[str] = field(default_factory=list)
    next_stages: List[str] = field(default_factory=list)  # IDs der nächsten Runden
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

    def get_next_stages(self) -> List["Stage"]:
        # Diese Methode wird später von Tournament verwaltet
        return []

    def __repr__(self):
        return f"Stage(id={self.id}, type={self.type}, teams={len(self.teams)}, matches={len(self.matches)})"


@dataclass
class Group:
    name: str
    teams: List[str]
    settings: GroupSettings | None = None

    def __init__(self, name: str, teams: List[str] = None):
        self.name = name
        self.teams = teams or []
        self.settings = None

    def add_head(self, team_name: str):
        self.teams.append(team_name)

    def add_member(self, team_name: str):
        self.teams.append(team_name)

@dataclass
class GroupSettings:
    sets: str
    points: int
    tiebreak: int | None = None

    def to_dict(self) -> dict:
        return {
            "sets": self.sets,
            "points": self.points,
            "tiebreak": self.tiebreak
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupSettings":
        return cls(
            sets=data["sets"],
            points=data["points"],
            tiebreak=data.get("tiebreak")
        )

@dataclass
class Team:
    id: str
    name: str
    verein: str
