# tbo/services/ranking.py
import pandas as pd
import functools
from typing import Dict, List

# ----------------------------------------------------------------------
# Hilfs‑Funktion: Direkter Begegnungs‑Gewinner (für Tie‑Breaker)
# ----------------------------------------------------------------------
def _direct_winner(match: dict, results: dict, team_a: str, team_b: str) -> str | None:
    """Gibt zurück, welches Team (team_a oder team_b) das direkte Duell gewonnen hat."""
    res = results.get(match["id"])
    if not res or not res.get("played"):
        return None

    # Wer ist Team A im Match?
    if match["t1"] == team_a and match["t2"] == team_b:
        s_a, s_b = res["score1"], res["score2"]
    elif match["t1"] == team_b and match["t2"] == team_a:
        s_a, s_b = res["score2"], res["score1"]
    else:
        return None

    if s_a > s_b:
        return team_a
    if s_b > s_a:
        return team_b
    return None


# ----------------------------------------------------------------------
# 1️⃣  Ranking‑Berechnung für eine Gruppe
# ----------------------------------------------------------------------
def calculate_ranking(
    group_name: str,
    teams: Dict[str, str],
    results: Dict[str, dict],
    schedule: List[dict],
) -> pd.DataFrame:
    """
    Ermittelt die Rangliste einer Gruppe.

    Parameters
    ----------
    group_name
        Name der Gruppe (z. B. "A").
    teams
        Mapping Team‑ID → Team‑Name für diese Gruppe.
    results
        Ergebnis‑Dict, Schlüssel = Match‑ID, Wert = {"score1":…, "score2":…, "played": True/False}
    schedule
        Liste von Match‑Dictionaries, wie sie ``schedule.generate_schedule`` zurückgibt.
    """
    # --------------------------------------------------------------
    # 1️⃣  Basis‑Statistik initialisieren
    # --------------------------------------------------------------
    stats = {
        t_id: {
            "Spiele": 0,
            "Satzpunkte": 0,
            "Punkte Diff": 0,
            "Erzielt": 0,
            "Erhalten": 0,
        }
        for t_id in teams
    }

    # --------------------------------------------------------------
    # 2️⃣  Durch alle Matches der Gruppe iterieren
    # --------------------------------------------------------------
    for m in schedule:
        if m["group"] != group_name:
            continue

        res = results.get(m["id"])
        if not res or not res.get("played"):
            continue

        t1, t2 = m["t1"], m["t2"]
        s1, s2 = res["score1"], res["score2"]

        # Spiele‑Zähler
        stats[t1]["Spiele"] += 1
        stats[t2]["Spiele"] += 1

        # Punkte‑Statistik
        stats[t1]["Erzielt"]   += s1
        stats[t1]["Erhalten"] += s2
        stats[t1]["Punkte Diff"] += s1 - s2

        stats[t2]["Erzielt"]   += s2
        stats[t2]["Erhalten"] += s1
        stats[t2]["Punkte Diff"] += s2 - s1

        # Satzpunkte (Gewinn‑Satz)
        if s1 > s2:
            stats[t1]["Satzpunkte"] += 1
        elif s2 > s1:
            stats[t2]["Satzpunkte"] += 1

    # --------------------------------------------------------------
    # 3️⃣  DataFrame aus den Stats bauen
    # --------------------------------------------------------------
    rows = []
    for t_id, d in stats.items():
        rows.append(
            {
                "Team ID": t_id,
                "Name": teams[t_id],
                "Spiele": d["Spiele"],
                "Satzpunkte": d["Satzpunkte"],
                "Punkte Diff": d["Punkte Diff"],
                "Punkte +": d["Erzielt"],
                "Punkte -": d["Erhalten"],
            }
        )
    df = pd.DataFrame(rows)

    # --------------------------------------------------------------
    # 4️⃣  Eigener Comparator (wie im Original‑Skript)
    # --------------------------------------------------------------
    def compare(a: dict, b: dict) -> int:
        # 1. Satzpunkte
        if a["Satzpunkte"] != b["Satzpunkte"]:
            return b["Satzpunkte"] - a["Satzpunkte"]

        # 2. Direktes Duell
        winner = None
        for m in schedule:
            if {m["t1"], m["t2"]} == {a["Team ID"], b["Team ID"]}:
                winner = _direct_winner(m, results, a["Team ID"], b["Team ID"])
                break
        if winner == a["Team ID"]:
            return -1
        if winner == b["Team ID"]:
            return 1

        # 3. Punkte‑Differenz
        return b["Punkte Diff"] - a["Punkte Diff"]

    # --------------------------------------------------------------
    # 5️⃣  Python‑seitiges Sortieren (statt pandas‑key‑Sortierung)
    # --------------------------------------------------------------
    #   * Wir wandeln das DataFrame in eine Liste von Dictionaries um,
    #   * sortieren diese Liste mit unserem Comparator,
    #   * bauen anschließend ein neues DataFrame aus der sortierten Liste.
    records = df.to_dict("records")
    records_sorted = sorted(records, key=functools.cmp_to_key(compare))
    df = pd.DataFrame(records_sorted)

    # --------------------------------------------------------------
    # 6️⃣  Rang‑Spalte ergänzen
    # --------------------------------------------------------------
    df["Rang"] = range(1, len(df) + 1)
    df["Tie‑Breaker"] = ""   # (kann später befüllt werden)

    # --------------------------------------------------------------
    # 7️⃣  Rückgabe – nur die Spalten, die das UI braucht
    # --------------------------------------------------------------
    return df[
        [
            "Rang",
            "Team ID",
            "Name",
            "Spiele",
            "Satzpunkte",
            "Punkte Diff",
            "Punkte +",
            "Punkte -",
            "Tie‑Breaker",
        ]
    ]


# ----------------------------------------------------------------------
# 2️⃣  Gewinner eines Final‑Matches (beste von 3 Sätzen)
# ----------------------------------------------------------------------
def get_final_winner(res: dict) -> int | None:
    if not res.get("played"):
        return None

    sets1, sets2 = 0, 0
    for s in (1, 2, 3):
        s1 = res.get(f"set{s}_1", 0)
        s2 = res.get(f"set{s}_2", 0)
        if s1 > s2:
            sets1 += 1
        elif s2 > s1:
            sets2 += 1

    if sets1 >= 2:
        return 1
    if sets2 >= 2:
        return 2
    return None


# ----------------------------------------------------------------------
# 3️⃣  Alle Final‑Matches (inkl. Auflösung von Referenzen)
# ----------------------------------------------------------------------
def get_all_final_matches(data: dict) -> List[tuple]:
    """
    Liefert eine Liste von Tupeln:
    (title, info, team1, team2, match_id)

    Die Referenzen (z. B. ``rank_A_1``) werden in echte Team‑IDs
    aufgelöst – wenn die Vorrunde noch nicht abgeschlossen ist,
    wird ``"Noch offen"`` zurückgegeben.
    """
    if not data.get("tournament_config"):
        return []

    schema = data["tournament_config"]["final_matches_schema"]
    schedule = data["tournament_config"]["schedule"]

    # ---- Wie viele Vorrunden‑Spiele wurden bereits gespielt? ----
    played_cnt = sum(1 for m in data["group_matches"].values() if m.get("played"))
    all_played = played_cnt == len(schedule)

    # ---- Rankings pro Gruppe berechnen (nur nötig, wenn alles gespielt) ----
    rankings: Dict[str, pd.DataFrame] = {}
    for grp in data["tournament_config"]["groups"]:
        rankings[grp] = calculate_ranking(
            grp,
            data["teams"][grp],
            data["group_matches"],
            data["tournament_config"]["schedule"],
        )

    # ---- Hilfs‑Funktion: Team‑Name aus Referenz ermitteln ----
    def resolve_ref(ref: str) -> str:
        # 1️⃣  Rang‑Referenz (z. B. "rank_A_1")
        if ref.startswith("rank_"):
            _, grp, rank_str = ref.split("_")
            rank = int(rank_str)
            if not all_played:
                return "Noch offen"
            df = rankings[grp]
            if rank <= len(df):
                row = df.iloc[rank - 1]
                return f"{row['Team ID']} ({row['Name']})"
            return "TBD"

        # 2️⃣  Gewinner‑/Verlierer‑Referenz (z. B. "m_qf_1_winner")
        if ref.endswith("_winner") or ref.endswith("_loser"):
            match_id, typ = ref.rsplit("_", 1)   # typ = "winner" oder "loser"
            res = data["final_matches"].get(match_id, {})
            win_idx = get_final_winner(res)

            # Noch kein Ergebnis → Platzhalter zurückgeben
            if win_idx is None:
                return f"{typ.title()} noch offen"

            # Original‑Match aus dem Schema holen, um die beiden Teams zu kennen
            for m in schema:
                if m["id"] == match_id:
                    t1_ref, t2_ref = m["t1_ref"], m["t2_ref"]
                    t1 = resolve_ref(t1_ref)
                    t2 = resolve_ref(t2_ref)
                    if win_idx == 1:
                        return t1 if typ == "winner" else t2
                    else:
                        return t2 if typ == "winner" else t1
            return "Unbekannt"

        # 3️⃣  Direkter Team‑Name (z. B. "A1")
        return ref

    # ---- Endgültige Liste bauen ----
    matches = []
    for m in schema:
        t1 = resolve_ref(m["t1_ref"])
        t2 = resolve_ref(m["t2_ref"])
        time_str = m.get("time", "TBD")
        court = m.get("court", "?")
        info = f"{time_str} | 🏟️ FELD {court} | {m['info']}"
        matches.append((m["title"], info, t1, t2, m["id"]))

    return matches


# ----------------------------------------------------------------------
# 4️⃣  Gesamtrangliste (Endstand) – Ergebnis nach Final‑ und Platzierungsspielen
# ----------------------------------------------------------------------
def get_final_ranking_list(data: dict) -> List[tuple]:
    """
    Liefert eine Liste von Tupeln ``(Rang‑Bezeichnung, Team‑Anzeige)``,
    die im Tab „Endstand“ angezeigt wird.

    Die Rangfolge wird aus den Final‑ und Platzierungsspielen abgeleitet.
    Für 8, 12 und 16 Teams werden die Plätze 1–12 (bzw. 1–16) ermittelt.

    Parameters
    ----------
    data
        Das vollständige Turnier‑Datenobjekt (aus `st.session_state.data`).

    Returns
    -------
    List[tuple]
        Liste von Tupeln: (Rang‑Text, Team‑Name)
        Beispiel: [("1. Platz 🥇", "A1 (Team A1)"), ("2. Platz 🥈", "B1 (Team B1)"), ...]
    """
    if not data.get("tournament_config"):
        return []

    num_teams = data["tournament_config"]["num_teams"]
    schema = data["tournament_config"]["final_matches_schema"]

    # ---- Alle Final‑Matches auflösen (mit echten Team‑Namen) ----
    all_matches = get_all_final_matches(data)

    # ---- Rangliste initialisieren (alle Plätze mit "—" füllen) ----
    ranks = {i: "—" for i in range(1, num_teams + 1)}

    # ---- Hilfsfunktion: Gewinner eines Matches ermitteln ----
    def get_winner(match_id: str) -> int | None:
        res = data["final_matches"].get(match_id, {})
        return get_final_winner(res)

    # ---- 1. Platz (Finale) ----
    # Finale ist immer das letzte Match in der Schema‑Liste
    final_match = next((m for m in schema if m["id"] == "m_fin_gr"), None)
    if final_match:
        win_idx = get_winner("m_fin_gr")
        if win_idx == 1:
            ranks[1] = all_matches[-1][2]  # Team 1
        elif win_idx == 2:
            ranks[1] = all_matches[-1][3]  # Team 2

    # ---- 2. Platz (Finale) ----
    if final_match:
        win_idx = get_winner("m_fin_gr")
        if win_idx == 1:
            ranks[2] = all_matches[-1][3]  # Team 2
        elif win_idx == 2:
            ranks[2] = all_matches[-1][2]  # Team 1

    # ---- 3. Platz (Spiel um Platz 3) ----
    kl_match = next((m for m in schema if m["id"] == "m_fin_kl"), None)
    if kl_match:
        win_idx = get_winner("m_fin_kl")
        if win_idx == 1:
            ranks[3] = all_matches[-2][2]  # Team 1
        elif win_idx == 2:
            ranks[3] = all_matches[-2][3]  # Team 2

    # ---- 4. Platz (Spiel um Platz 3) ----
    if kl_match:
        win_idx = get_winner("m_fin_kl")
        if win_idx == 1:
            ranks[4] = all_matches[-2][3]  # Team 2
        elif win_idx == 2:
            ranks[4] = all_matches[-2][2]  # Team 1

    # ---- 5–8 Platz (12‑Team‑Turnier) ----
    if num_teams == 12:
        # Platz 5–8: aus den Viertelfinal‑Verlierern
        # m_w, m_x, m_y, m_z
        m_w = next((m for m in schema if m["id"] == "m_w"), None)
        m_x = next((m for m in schema if m["id"] == "m_x"), None)
        m_y = next((m for m in schema if m["id"] == "m_y"), None)
        m_z = next((m for m in schema if m["id"] == "m_z"), None)

        # Gewinner der Viertelfinal‑Verlierer‑Spiele
        winners = []
        if m_w:
            win_idx = get_winner("m_w")
            if win_idx == 1:
                winners.append(all_matches[4][2])
            elif win_idx == 2:
                winners.append(all_matches[4][3])
        if m_x:
            win_idx = get_winner("m_x")
            if win_idx == 1:
                winners.append(all_matches[5][2])
            elif win_idx == 2:
                winners.append(all_matches[5][3])
        if m_y:
            win_idx = get_winner("m_y")
            if win_idx == 1:
                winners.append(all_matches[6][2])
            elif win_idx == 2:
                winners.append(all_matches[6][3])
        if m_z:
            win_idx = get_winner("m_z")
            if win_idx == 1:
                winners.append(all_matches[7][2])
            elif win_idx == 2:
                winners.append(all_matches[7][3])

        # Platz 5–8: die 4 Gewinner
        for i, w in enumerate(winners):
            ranks[5 + i] = w

    # ---- 5–8 Platz (8‑Team‑Turnier) ----
    elif num_teams == 8:
        # Platz 5–8: aus den Viertelfinal‑Verlierern
        # m_qf_1, m_qf_2, m_qf_3, m_qf_4
        m_qf_1 = next((m for m in schema if m["id"] == "m_qf_1"), None)
        m_qf_2 = next((m for m in schema if m["id"] == "m_qf_2"), None)
        m_qf_3 = next((m for m in schema if m["id"] == "m_qf_3"), None)
        m_qf_4 = next((m for m in schema if m["id"] == "m_qf_4"), None)

        winners = []
        if m_qf_1:
            win_idx = get_winner("m_qf_1")
            if win_idx == 1:
                winners.append(all_matches[0][2])
            elif win_idx == 2:
                winners.append(all_matches[0][3])
        if m_qf_2:
            win_idx = get_winner("m_qf_2")
            if win_idx == 1:
                winners.append(all_matches[1][2])
            elif win_idx == 2:
                winners.append(all_matches[1][3])
        if m_qf_3:
            win_idx = get_winner("m_qf_3")
            if win_idx == 1:
                winners.append(all_matches[2][2])
            elif win_idx == 2:
                winners.append(all_matches[2][3])
        if m_qf_4:
            win_idx = get_winner("m_qf_4")
            if win_idx == 1:
                winners.append(all_matches[3][2])
            elif win_idx == 2:
                winners.append(all_matches[3][3])

        for i, w in enumerate(winners):
            ranks[5 + i] = w

    # ---- 9–12 Platz (12‑Team‑Turnier) ----
    if num_teams == 12:
        m_9_10 = next((m for m in schema if m["id"] == "m_9_10"), None)
        m_11_12 = next((m for m in schema if m["id"] == "m_11_12"), None)

        if m_9_10:
            win_idx = get_winner("m_9_10")
            if win_idx == 1:
                ranks[9] = all_matches[8][2]
            elif win_idx == 2:
                ranks[9] = all_matches[8][3]
        if m_11_12:
            win_idx = get_winner("m_11_12")
            if win_idx == 1:
                ranks[11] = all_matches[9][2]
            elif win_idx == 2:
                ranks[11] = all_matches[9][3]

        # Platz 10 und 12: Verlierer
        if m_9_10:
            win_idx = get_winner("m_9_10")
            if win_idx == 1:
                ranks[10] = all_matches[8][3]
            elif win_idx == 2:
                ranks[10] = all_matches[8][2]
        if m_11_12:
            win_idx = get_winner("m_11_12")
            if win_idx == 1:
                ranks[12] = all_matches[9][3]
            elif win_idx == 2:
                ranks[12] = all_matches[9][2]

    # ---- 13–16 Platz (16‑Team‑Turnier) ----
    elif num_teams == 16:
        # Für 16 Teams: Platz 13–16 aus den Halbfinal‑Verlierern
        # m_sf_1, m_sf_2
        m_sf_1 = next((m for m in schema if m["id"] == "m_sf_1"), None)
        m_sf_2 = next((m for m in schema if m["id"] == "m_sf_2"), None)

        if m_sf_1:
            win_idx = get_winner("m_sf_1")
            if win_idx == 1:
                ranks[13] = all_matches[10][2]
                ranks[14] = all_matches[10][3]
            elif win_idx == 2:
                ranks[13] = all_matches[10][3]
                ranks[14] = all_matches[10][2]
        if m_sf_2:
            win_idx = get_winner("m_sf_2")
            if win_idx == 1:
                ranks[15] = all_matches[11][2]
                ranks[16] = all_matches[11][3]
            elif win_idx == 2:
                ranks[15] = all_matches[11][3]
                ranks[16] = all_matches[11][2]

    # ---- Rückgabe: Liste von (Rang, Team) Tupeln ----
    final_list = []
    for i in range(1, num_teams + 1):
        if i == 1:
            final_list.append((f"{i}. Platz 🥇", ranks[i]))
        elif i == 2:
            final_list.append((f"{i}. Platz 🥈", ranks[i]))
        elif i == 3:
            final_list.append((f"{i}. Platz 🥉", ranks[i]))
        else:
            final_list.append((f"{i}. Platz", ranks[i]))

    return final_list