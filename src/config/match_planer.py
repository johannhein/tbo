from typing import Dict, Tuple, List

group_size_3 = [
    {"Round": 1, "Matches": [{"Match": 1, "Team1": 1, "Team2": 2, "Ref": 3}]},
    {"Round": 2, "Matches": [{"Match": 2, "Team1": 1, "Team2": 3, "Ref": 2}]},
    {"Round": 3, "Matches": [{"Match": 3, "Team1": 2, "Team2": 3, "Ref": 1}]}
]

group_size_4 = [
    {"Round": 1, "Matches": [{"Match": 1, "Team1": 1, "Team2": 2, "Ref": 3}]},
    {"Round": 2, "Matches": [{"Match": 2, "Team1": 3, "Team2": 4, "Ref": 1}]},
    {"Round": 3, "Matches": [{"Match": 3, "Team1": 1, "Team2": 3, "Ref": 4}]},
    {"Round": 4, "Matches": [{"Match": 4, "Team1": 2, "Team2": 4, "Ref": 1}]},
    {"Round": 5, "Matches": [{"Match": 5, "Team1": 1, "Team2": 4, "Ref": 2}]},
    {"Round": 6, "Matches": [{"Match": 6, "Team1": 2, "Team2": 3, "Ref": 4}]}
]

group_size_5 = [
    {"Round": 1, "Matches": [{"Match": 1, "Team1": 1, "Team2": 2, "Ref": 3}]},
    {"Round": 2, "Matches": [{"Match": 2, "Team1": 1, "Team2": 3, "Ref": 4}]},
    {"Round": 3, "Matches": [{"Match": 3, "Team1": 1, "Team2": 4, "Ref": 5}]},
    {"Round": 4, "Matches": [{"Match": 4, "Team1": 1, "Team2": 5, "Ref": 2}]},
    {"Round": 5, "Matches": [{"Match": 5, "Team1": 2, "Team2": 3, "Ref": 5}]},
    {"Round": 6, "Matches": [{"Match": 6, "Team1": 2, "Team2": 4, "Ref": 1}]},
    {"Round": 7, "Matches": [{"Match": 7, "Team1": 2, "Team2": 5, "Ref": 4}]},
    {"Round": 8, "Matches": [{"Match": 8, "Team1": 3, "Team2": 4, "Ref": 2}]},
    {"Round": 9, "Matches": [{"Match": 9, "Team1": 3, "Team2": 5, "Ref": 1}]},
    {"Round": 10, "Matches": [{"Match": 10, "Team1": 4, "Team2": 5, "Ref": 3}]}
]

group_size_6 = [
    {"Round": 1, "Matches": [{"Match": 1, "Team1": 1, "Team2": 2, "Ref": 3}]},
    {"Round": 2, "Matches": [{"Match": 2, "Team1": 4, "Team2": 5, "Ref": 6}]},
    {"Round": 3, "Matches": [{"Match": 3, "Team1": 1, "Team2": 3, "Ref": 4}]},
    {"Round": 4, "Matches": [{"Match": 4, "Team1": 2, "Team2": 6, "Ref": 5}]},
    {"Round": 5, "Matches": [{"Match": 5, "Team1": 1, "Team2": 4, "Ref": 2}]},
    {"Round": 6, "Matches": [{"Match": 6, "Team1": 3, "Team2": 5, "Ref": 6}]},
    {"Round": 7, "Matches": [{"Match": 7, "Team1": 1, "Team2": 5, "Ref": 3}]},
    {"Round": 8, "Matches": [{"Match": 8, "Team1": 2, "Team2": 4, "Ref": 6}]},
    {"Round": 9, "Matches": [{"Match": 9, "Team1": 1, "Team2": 6, "Ref": 2}]},
    {"Round": 10, "Matches": [{"Match": 10, "Team1": 3, "Team2": 4, "Ref": 5}]},
    {"Round": 11, "Matches": [{"Match": 11, "Team1": 2, "Team2": 5, "Ref": 1}]},
    {"Round": 12, "Matches": [{"Match": 12, "Team1": 3, "Team2": 6, "Ref": 4}]},
    {"Round": 13, "Matches": [{"Match": 13, "Team1": 4, "Team2": 6, "Ref": 1}]},
    {"Round": 14, "Matches": [{"Match": 14, "Team1": 2, "Team2": 3, "Ref": 5}]},
    {"Round": 15, "Matches": [{"Match": 15, "Team1": 5, "Team2": 6, "Ref": 1}]}
]

group_size_4_fields_2 = [
    {"Round": 1, "Matches": [{"Match": 1, "Team1": 1, "Team2": 2, "Ref": None},
                           {"Match": 2, "Team1": 3, "Team2": 4, "Ref": None}]},
    {"Round": 2, "Matches": [{"Match": 3, "Team1": 1, "Team2": 3, "Ref": None},
                           {"Match": 4, "Team1": 2, "Team2": 4, "Ref": None}]},
    {"Round": 3, "Matches": [{"Match": 5, "Team1": 1, "Team2": 4, "Ref": None},
                           {"Match": 6, "Team1": 2, "Team2": 3, "Ref": None}]}
]

group_size_5_fields_2 = [
    {"Round": 1, "Matches": [
        {"Match": 1, "Team1": 1, "Team2": 2, "Ref": 5},
        {"Match": 2, "Team1": 3, "Team2": 4, "Ref": 5}
    ]},
    {"Round": 2, "Matches": [
        {"Match": 3, "Team1": 1, "Team2": 3, "Ref": 4},
        {"Match": 4, "Team1": 2, "Team2": 5, "Ref": 4}
    ]},
    {"Round": 3, "Matches": [
        {"Match": 5, "Team1": 1, "Team2": 4, "Ref": 2},
        {"Match": 6, "Team1": 3, "Team2": 5, "Ref": 2}
    ]},
    {"Round": 4, "Matches": [
        {"Match": 7, "Team1": 1, "Team2": 5, "Ref": 3},
        {"Match": 8, "Team1": 2, "Team2": 4, "Ref": 3}
    ]},
    {"Round": 5, "Matches": [
        {"Match": 9, "Team1": 2, "Team2": 3, "Ref": 1},
        {"Match": 10, "Team1": 4, "Team2": 5, "Ref": 1}
    ]}
]


group_size_6_fields_2 = [
    {"Round": 1, "Matches": [{"Match": 1, "Team1": 1, "Team2": 2, "Ref": 5},
                           {"Match": 2, "Team1": 3, "Team2": 4, "Ref": 6}]},
    {"Round": 2, "Matches": [{"Match": 3, "Team1": 1, "Team2": 5, "Ref": 3},
                           {"Match": 4, "Team1": 2, "Team2": 6, "Ref": 4}]},
    {"Round": 3, "Matches": [{"Match": 5, "Team1": 3, "Team2": 5, "Ref": 1},
                           {"Match": 6, "Team1": 4, "Team2": 6, "Ref": 2}]},
    {"Round": 4, "Matches": [{"Match": 7, "Team1": 1, "Team2": 4, "Ref": 5},
                           {"Match": 8, "Team1": 2, "Team2": 3, "Ref": 6}]},
    {"Round": 5, "Matches": [{"Match": 9, "Team1": 1, "Team2": 6, "Ref": 3},
                           {"Match": 10, "Team1": 2, "Team2": 5, "Ref": 4}]},
    {"Round": 6, "Matches": [{"Match": 11, "Team1": 3, "Team2": 6, "Ref": 1},
                           {"Match": 12, "Team1": 4, "Team2": 5, "Ref": 2}]},
    {"Round": 7, "Matches": [{"Match": 13, "Team1": 1, "Team2": 3, "Ref": 6},
                           {"Match": 14, "Team1": 2, "Team2": 4, "Ref": 5}]},
    {"Round": 8, "Matches": [{"Match": 15, "Team1": 5, "Team2": 6, "Ref": 2}]}
]


SCHEMA_MAP: Dict[Tuple[int, int], List[Dict]] = {
    (3, 1): group_size_3,
    (4, 1): group_size_4,
    (5, 1): group_size_5,
    (6, 1): group_size_6,
    (4, 2): group_size_4_fields_2,
    (5, 2): group_size_5_fields_2,
    (6, 2): group_size_6_fields_2,
}
