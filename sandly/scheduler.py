import datetime

def generate_round_robin(teams):
    """Generates a list of rounds, where each round is a list of pairings (t1, t2)."""
    if len(teams) % 2 != 0:
        teams = teams + [None]
    
    n = len(teams)
    matchs = []
    
    for round_idx in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            t1 = teams[i]
            t2 = teams[n - 1 - i]
            if t1 is not None and t2 is not None:
                round_matches.append((t1, t2))
        teams.insert(1, teams.pop())
        matchs.append(round_matches)
        
    return matchs

def generate_schedule(groups_dict, num_courts, start_time_str, duration_minutes, lunch_start_str="12:00", lunch_duration_minutes=45):
    """
    groups_dict: {"A": ["A1", "A2", "A3", "A4"], "B": ["B1", ...]}
    Returns: (scheduled_matches, final_end_time_str)
    """
    # 1. Generate all rounds for all groups
    all_group_rounds = {}
    max_rounds = 0
    for grp_name, teams in groups_dict.items():
        rounds = generate_round_robin(teams)
        all_group_rounds[grp_name] = rounds
        if len(rounds) > max_rounds:
            max_rounds = len(rounds)
            
    # 2. Flatten matches, interleaving groups round by round
    flat_matches = []
    for r in range(max_rounds):
        for grp_name in groups_dict.keys():
            if r < len(all_group_rounds[grp_name]):
                for pairing in all_group_rounds[grp_name][r]:
                    flat_matches.append({
                        "t1": pairing[0],
                        "t2": pairing[1],
                        "group": grp_name
                    })
                    
    # 3. Assign times and courts
    try:
        current_time = datetime.datetime.strptime(start_time_str, "%H:%M")
    except ValueError:
        current_time = datetime.datetime.strptime("09:00", "%H:%M")
        
    try:
        lunch_start_time = datetime.datetime.strptime(lunch_start_str, "%H:%M") if lunch_start_str else None
    except (ValueError, TypeError):
        lunch_start_time = None
        
    delta = datetime.timedelta(minutes=duration_minutes)
    
    scheduled_matches = []
    court_idx = 1
    lunch_taken = False
    
    for idx, match in enumerate(flat_matches):
        match_id = f"group_{idx}"
        
        # Check for lunch break before starting a new round of games
        # We only apply lunch break when starting at court 1 so all courts break together
        if court_idx == 1 and not lunch_taken and lunch_start_time and current_time >= lunch_start_time:
            current_time += datetime.timedelta(minutes=lunch_duration_minutes)
            lunch_taken = True
            
        end_time = current_time + delta
        time_str = f"{current_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
        
        scheduled_matches.append({
            "id": match_id,
            "time": time_str,
            "court": court_idx,
            "t1": match["t1"],
            "t2": match["t2"],
            "group": match["group"]
        })
        
        court_idx += 1
        if court_idx > num_courts:
            court_idx = 1
            current_time = end_time
            
    # If the last round didn't fill all courts, current_time is still the start of the round
    # So end time is current_time + delta
    final_time = current_time if court_idx == 1 else current_time + delta
    return scheduled_matches, final_time.strftime("%H:%M")

def get_final_schema(num_teams):
    """
    Returns the raw schema structure for knockout phase.
    """
    schema = []
    if num_teams == 8:
        schema = [
            {"id": "m_hf1", "title": "Halbfinale 1", "info": "1. Grp A - 2. Grp B", "t1_ref": "rank_A_1", "t2_ref": "rank_B_2"},
            {"id": "m_hf2", "title": "Halbfinale 2", "info": "1. Grp B - 2. Grp A", "t1_ref": "rank_B_1", "t2_ref": "rank_A_2"},
            {"id": "m_5_8_1", "title": "Spiel um Platz 5-8", "info": "3. Grp A - 4. Grp B", "t1_ref": "rank_A_3", "t2_ref": "rank_B_4"},
            {"id": "m_5_8_2", "title": "Spiel um Platz 5-8", "info": "3. Grp B - 4. Grp A", "t1_ref": "rank_B_3", "t2_ref": "rank_A_4"},
            {"id": "m_7_8", "title": "Spiel um Platz 7", "info": "Verl. 5-8", "t1_ref": "m_5_8_1_loser", "t2_ref": "m_5_8_2_loser"},
            {"id": "m_5_6", "title": "Spiel um Platz 5", "info": "Gew. 5-8", "t1_ref": "m_5_8_1_winner", "t2_ref": "m_5_8_2_winner"},
            {"id": "m_fin_kl", "title": "Kleines Finale", "info": "Verl. HF", "t1_ref": "m_hf1_loser", "t2_ref": "m_hf2_loser"},
            {"id": "m_fin_gr", "title": "Großes Finale", "info": "Gew. HF", "t1_ref": "m_hf1_winner", "t2_ref": "m_hf2_winner"}
        ]
    elif num_teams == 12:
        schema = [
            {"id": "m_y", "title": "Zwischenrunde (Y)", "info": "2. Grp A - 3. Grp B", "t1_ref": "rank_A_2", "t2_ref": "rank_B_3"},
            {"id": "m_z", "title": "Zwischenrunde (Z)", "info": "2. Grp B - 3. Grp A", "t1_ref": "rank_B_2", "t2_ref": "rank_A_3"},
            {"id": "m_11_12", "title": "Spiel um Platz 11", "info": "6. Grp A - 6. Grp B", "t1_ref": "rank_A_6", "t2_ref": "rank_B_6"},
            {"id": "m_w", "title": "Zwischenrunde (W)", "info": "1. Grp A - 4. Grp B", "t1_ref": "rank_A_1", "t2_ref": "rank_B_4"},
            {"id": "m_x", "title": "Zwischenrunde (X)", "info": "1. Grp B - 4. Grp A", "t1_ref": "rank_B_1", "t2_ref": "rank_A_4"},
            {"id": "m_9_10", "title": "Spiel um Platz 9", "info": "5. Grp A - 5. Grp B", "t1_ref": "rank_A_5", "t2_ref": "rank_B_5"},
            {"id": "m_hf1", "title": "Halbfinale 1", "info": "Gew. W - Gew. Z", "t1_ref": "m_w_winner", "t2_ref": "m_z_winner"},
            {"id": "m_hf2", "title": "Halbfinale 2", "info": "Gew. X - Gew. Y", "t1_ref": "m_x_winner", "t2_ref": "m_y_winner"},
            {"id": "m_fin_kl", "title": "Kleines Finale", "info": "Verl. HF", "t1_ref": "m_hf1_loser", "t2_ref": "m_hf2_loser"},
            {"id": "m_fin_gr", "title": "Großes Finale", "info": "Gew. HF", "t1_ref": "m_hf1_winner", "t2_ref": "m_hf2_winner"}
        ]
    elif num_teams == 16:
        schema = [
            {"id": "m_vf1", "title": "Viertelfinale 1", "info": "1. Grp A - 2. Grp B", "t1_ref": "rank_A_1", "t2_ref": "rank_B_2"},
            {"id": "m_vf2", "title": "Viertelfinale 2", "info": "1. Grp C - 2. Grp D", "t1_ref": "rank_C_1", "t2_ref": "rank_D_2"},
            {"id": "m_vf3", "title": "Viertelfinale 3", "info": "1. Grp B - 2. Grp A", "t1_ref": "rank_B_1", "t2_ref": "rank_A_2"},
            {"id": "m_vf4", "title": "Viertelfinale 4", "info": "1. Grp D - 2. Grp C", "t1_ref": "rank_D_1", "t2_ref": "rank_C_2"},
            {"id": "m_hf1", "title": "Halbfinale 1", "info": "Gew. VF1 - Gew. VF2", "t1_ref": "m_vf1_winner", "t2_ref": "m_vf2_winner"},
            {"id": "m_hf2", "title": "Halbfinale 2", "info": "Gew. VF3 - Gew. VF4", "t1_ref": "m_vf3_winner", "t2_ref": "m_vf4_winner"},
            {"id": "m_fin_kl", "title": "Kleines Finale", "info": "Verl. HF", "t1_ref": "m_hf1_loser", "t2_ref": "m_hf2_loser"},
            {"id": "m_fin_gr", "title": "Großes Finale", "info": "Gew. HF", "t1_ref": "m_hf1_winner", "t2_ref": "m_hf2_winner"}
        ]
    return schema

def generate_final_schedule(schema, num_courts, start_time_str, duration_zwischenrunde, duration_finals, lunch_start_str=None, lunch_duration_minutes=45):
    try:
        current_time = datetime.datetime.strptime(start_time_str, "%H:%M")
    except ValueError:
        current_time = datetime.datetime.strptime("13:00", "%H:%M")
        
    try:
        lunch_start = datetime.datetime.strptime(lunch_start_str, "%H:%M") if lunch_start_str else None
    except (ValueError, TypeError):
        lunch_start = None
        
    depths = {}
    def get_depth(m_id):
        if m_id in depths: return depths[m_id]
        match = next((m for m in schema if m["id"] == m_id), None)
        if not match: return 0
        t1_ref = match.get("t1_ref", "")
        t2_ref = match.get("t2_ref", "")
        
        d1 = 0
        if t1_ref.endswith("_winner") or t1_ref.endswith("_loser"):
            ref_id = t1_ref.rsplit("_", 1)[0]
            d1 = get_depth(ref_id) + 1
            
        d2 = 0
        if t2_ref.endswith("_winner") or t2_ref.endswith("_loser"):
            ref_id = t2_ref.rsplit("_", 1)[0]
            d2 = get_depth(ref_id) + 1
            
        depths[m_id] = max(d1, d2)
        return depths[m_id]
        
    for m in schema: get_depth(m["id"])
        
    matches_by_depth = {}
    for m in schema:
        d = depths[m["id"]]
        if d not in matches_by_depth: matches_by_depth[d] = []
        matches_by_depth[d].append(m)
        
    lunch_taken = False
    if lunch_start and current_time >= lunch_start + datetime.timedelta(minutes=1):
        lunch_taken = True
        
    def get_duration_for_match(m):
        if "hf" in m["id"] or "fin" in m["id"]:
            return duration_finals
        return duration_zwischenrunde
        
    max_depth = max(depths.values()) if depths else 0
    for d in range(max_depth + 1):
        if d not in matches_by_depth: continue
        
        court_idx = 1
        
        # Calculate max duration for this depth level
        max_duration_in_round = max(get_duration_for_match(m) for m in matches_by_depth[d])
        delta = datetime.timedelta(minutes=max_duration_in_round)
        
        for m in matches_by_depth[d]:
            if court_idx == 1 and lunch_start and not lunch_taken and current_time >= lunch_start:
                current_time += datetime.timedelta(minutes=lunch_duration_minutes)
                lunch_taken = True
                
            m_duration = get_duration_for_match(m)
            m_delta = datetime.timedelta(minutes=m_duration)
            end_time = current_time + m_delta
            
            m["time"] = f"{current_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
            m["court"] = court_idx
            
            court_idx += 1
            if court_idx > num_courts:
                court_idx = 1
                current_time = current_time + delta
                
        if court_idx != 1:
            current_time = current_time + delta
            
    return schema
