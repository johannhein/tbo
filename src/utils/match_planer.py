from math import gcd
from typing import List, Dict

from core import Match, MatchID, MatchSettings, Group


def match_making_direct(teams: List[str], courts: List[int], settings: MatchSettings,
                        start_match_id: MatchID = 1) -> List[Match]:
    num_courts = len(courts)

    matches: List[Match] = []
    for idx, court in enumerate(courts):
        for i in range(2 * idx, len(teams), 2 * num_courts):
            match_id = i // 2 + start_match_id
            if i < len(teams) - 1:
                if i + 2 * len(courts) < len(teams):
                    match: Match = Match.create(match_id=match_id, court=court, t1=teams[i], t2=teams[i + 1],
                                                ref=teams[i + 2 * len(courts)], settings_match=settings)
                    matches.append(match)
                elif i - 2 * len(courts) >= 0:
                    match: Match = Match.create(match_id=match_id, court=court, t1=teams[i], t2=teams[i + 1],
                                                ref=teams[i - 2 * len(courts)], settings_match=settings)
                    matches.append(match)
                else:
                    match: Match = Match.create(match_id=match_id, court=court, t1=teams[i], t2=teams[i + 1],
                                                settings_match=settings)
                    matches.append(match)
                match_id += 1

    return matches


def match_making_ranking(teams: List[str], groups: List[str], courts: List[int], settings: MatchSettings,
                         start_match_id: MatchID = 1) -> List[Match]:
    """
    Erstellt Match-Paarungen nach Rang (erster gegen letzten, etc.),
    aber vermeidet Paarungen zwischen Teams aus derselben Gruppe.
    """
    assert len(teams) == len(groups), "Anzahl der Teams muss gleich Anzahl der Gruppen sein"
    assert len(teams) % 2 == 0, "Anzahl der Teams muss gerade sein"

    num_courts = len(courts)
    n = len(teams)
    mid = n // 2

    teams_high = teams[:mid]
    teams_low = teams[mid:]

    # Gruppenzuordnung als Dict: team -> group
    team_to_group: Dict[str, str] = dict(zip(teams, groups))

    matches: List[Match] = []

    low_teams_rotated = teams_low[:]

    found = False
    for rot in range(len(teams_low)):
        low_teams_rotated = teams_low[rot:] + teams_low[:rot]
        valid = True
        for i in range(mid):
            team1 = teams_high[i]
            team2 = low_teams_rotated[i]
            if team_to_group[team1] == team_to_group[team2]:
                valid = False
                break
        if valid:
            found = True
            break

    if not found:
        raise ValueError("Konnte keine gültige Paarung finden, ohne dass Teams aus derselben Gruppe gegeneinander spielen.")

    for idx, team in enumerate(teams_high):
        match_id = start_match_id + idx
        court_idx = idx % num_courts
        court = courts[court_idx]

        opponent = low_teams_rotated[idx]

        if team_to_group[team] == team_to_group[opponent]:
            raise RuntimeError(f"Paarung fehlerhaft: {team} und {opponent} aus derselben Gruppe!")

        if num_courts == len(teams_high):
            match = Match.create(match_id=match_id, court=court, t1=team, t2=opponent, settings_match=settings)
        else:
            if idx + num_courts < len(low_teams_rotated):
                id_ref = idx + num_courts
            else:
                id_ref = idx - num_courts
            ref = low_teams_rotated[id_ref]
            match = Match.create(match_id=match_id, court=court, t1=team, t2=opponent, ref=ref, settings_match=settings)

        matches.append(match)

    return matches


def match_making_x_vs_y(teams_1: List[str], teams_2: List[str], courts: List[int], settings: MatchSettings,
                        start_match_id: MatchID = 1) -> List[Match]:
    matches: List[Match] = []
    for i in range(len(teams_1)):
        match_id = i + start_match_id
        index = i % len(courts)
        j = i + len(teams_1) // 2
        if j >= len(teams_1):
            j = j - len(teams_1)
        if len(courts) < len(teams_1):
            match: Match = Match.create(match_id=match_id, court=courts[index], t1=teams_1[i], t2=teams_2[j],
                                        ref=teams_2[i], settings_match=settings)
            matches.append(match)
        else:
            match: Match = Match.create(match_id=match_id, court=courts[index], t1=teams_1[i], t2=teams_2[j],
                                        settings_match=settings)
            matches.append(match)

    return matches


def build_groups(teams_1: List[str], teams_2: List[str], groups_size: int, courts: List,
                 group_1: List = None, group_2: List = None) -> List[Group]:
    """
    Erzeugt Gruppen aus teams_1 und einer verschobenen teams_2-Liste.
    Dabei wird automatisch ein k gesucht, sodass kein Team gegen ein Team aus seiner vorherigen Gruppe spielt.
    """

    if group_1 and group_2:
        k = find_k(group_1, group_2, groups_size)
    else:
        list_1 = [str(i) for i in range(len(teams_1))]
        list_2 = [str(i) for i in range(len(teams_2))]
        k = find_k(list_1, list_2, groups_size)

    list_total = teams_1 + shift_list(teams_2, k)

    num_teams = len(list_total)
    num_groups = (num_teams + groups_size - 1) // groups_size

    groups: List[List[str]] = [[] for _ in range(num_groups)]

    for i in range(num_groups):
        for j in range(groups_size):
            idx = i + j * num_groups
            if idx < len(list_total):
                groups[i].append(list_total[idx])

    stage_groups = []
    for idx, teams in enumerate(groups):
        group = Group( name=str(idx + 1), teams=teams, teams_target=groups_size)
        group.assign_courts([courts[idx]])
        group.build_matches_from_schema()
        stage_groups.append(group)

    return stage_groups


def find_k( teams_1: List, teams_2: List, groups_size: int) -> int:
    """Findet ein k, sodass kein gemeinsames Team aus teams_1 und teams_2 in derselben Gruppe landet."""

    if not teams_2:
        return 0

    num_teams = len(teams_1) + len(teams_2)
    num_groups = (num_teams + groups_size - 1) // groups_size

    # Alle möglichen Verschiebungen ausprobieren
    for k in range(0, len(teams_2)):
        teams_2_shifted = shift_list(teams_2, k)
        list_total = teams_1 + teams_2_shifted

        groups_from_the_teams = {}

        # Ermitteln, in welcher Gruppe jedes Team landet
        for idx, team in enumerate(list_total):
            group_index = idx % num_groups

            if team in groups_from_the_teams:
                if groups_from_the_teams[team] == group_index:
                    break
            else:
                groups_from_the_teams[team] = group_index
        else:
            return k

    raise ValueError(
        "Es wurde kein k gefunden, bei dem alle doppelten Teams in unterschiedlichen Gruppen landen."
    )


def shift_list(lst: List, k: int) -> List:
    if not lst:
        return []

    k = k % len(lst)

    if k == 0:
        return lst.copy()

    return lst[-k:] + lst[:-k]
