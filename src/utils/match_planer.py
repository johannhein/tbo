from typing import List

from core import Match, MatchID, MatchSettings


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


def match_making_ranking(teams: List[str], courts: List[int], settings: MatchSettings,
                         start_match_id: MatchID = 1) -> List[Match]:
    num_courts = len(courts)
    teams_high = teams[:len(teams) // 2]
    teams_low = teams[len(teams) // 2:]

    matches: List[Match] = []
    for idx, team in enumerate(teams_high):
        match_id = idx + start_match_id
        index = idx % len(courts)
        if num_courts == len(teams_high):
            match: Match = Match.create(match_id=match_id, court=courts[index], t1=team, t2=teams_low[-(idx + 1)],
                                        settings_match=settings)
            matches.append(match)
        else:
            match: Match = Match.create(match_id=match_id, court=courts[index], t1=team, t2=teams_low[-(idx + 1)],
                                        ref=teams_low[idx], settings_match=settings)
            matches.append(match)

        match_id += 1

    return matches


def match_making_cross(teams_1: List[str], teams_2: List[str], courts: List[int], settings: MatchSettings,
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
