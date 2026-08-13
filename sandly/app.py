import streamlit as st
import pandas as pd
import json
import os
import io

# --- Constants & Data ---
DATA_FILE = "results.json"

# The match schedule according to the PDF (Group stage only for now)
# Format: Runde, Zeit, Feld, Team1, Team2, Gruppe
GROUP_MATCHES = [
    (1, "09:45-10:00", 1, "A1", "A6", "A"),
    (1, "09:45-10:00", 2, "A2", "A5", "A"),
    (1, "09:45-10:00", 3, "B1", "B6", "B"),
    
    (2, "10:00-10:15", 1, "A3", "A4", "A"),
    (2, "10:00-10:15", 2, "B2", "B5", "B"),
    (2, "10:00-10:15", 3, "B3", "B4", "B"),
    
    (3, "10:15-10:30", 1, "A2", "A6", "A"),
    (3, "10:15-10:30", 2, "A1", "A3", "A"),
    (3, "10:15-10:30", 3, "B2", "B6", "B"),
    
    (4, "10:30-10:45", 1, "A4", "A5", "A"),
    (4, "10:30-10:45", 2, "B1", "B3", "B"),
    (4, "10:30-10:45", 3, "B4", "B5", "B"),
    
    (5, "10:45-11:00", 1, "A3", "A6", "A"),
    (5, "10:45-11:00", 2, "A2", "A4", "A"),
    (5, "10:45-11:00", 3, "B3", "B6", "B"),
    
    (6, "11:00-11:30", 1, "A1", "A5", "A"),
    (6, "11:00-11:30", 2, "B2", "B4", "B"),
    (6, "11:00-11:30", 3, "B1", "B5", "B"),
    
    (7, "11:30-11:45", 1, "A4", "A6", "A"),
    (7, "11:30-11:45", 2, "A3", "A5", "A"),
    (7, "11:30-11:45", 3, "B4", "B6", "B"),
    
    (8, "11:45-12:00", 1, "A1", "A2", "A"),
    (8, "11:45-12:00", 2, "B3", "B5", "B"),
    (8, "11:45-12:00", 3, "B1", "B2", "B"),
    
    (9, "12:00-12:15", 1, "A5", "A6", "A"),
    (9, "12:00-12:15", 2, "A1", "A4", "A"),
    (9, "12:00-12:15", 3, "B5", "B6", "B"),
    
    (10, "12:15-12:30", 1, "A2", "A3", "A"),
    (10, "12:15-12:30", 2, "B1", "B4", "B"),
    (10, "12:15-12:30", 3, "B2", "B3", "B"),
]

# --- Helper Functions ---
def load_data():
    default_data = {
        "tournament_config": None,
        "group_matches": {}, 
        "final_matches": {},
        "teams": {},
        "paid_status": {}
    }
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Migration alter Daten (12-Teams Bündner Cup Format) auf das neue Format
            if "tournament_config" not in data:
                from scheduler import get_final_schema
                
                # Wir bauen den alten GROUP_MATCHES manuell nach (aus den hardcoded tuples)
                # Da GROUP_MATCHES hier noch in app.py hartkodiert ist (Zeile 13-52), nutzen wir es.
                schedule = []
                for i, m in enumerate(GROUP_MATCHES):
                    schedule.append({"id": f"group_{i}", "time": m[1], "court": m[2], "t1": m[3], "t2": m[4], "group": m[5]})
                    
                data["tournament_config"] = {
                    "num_teams": 12,
                    "num_groups": 2,
                    "num_courts": 3,
                    "groups": ["A", "B"],
                    "schedule": schedule,
                    "final_matches_schema": get_final_schema(12)
                }
                
                # Teams migrieren
                data["teams"] = {}
                if "teams_a" in data:
                    data["teams"]["A"] = data["teams_a"]
                if "teams_b" in data:
                    data["teams"]["B"] = data["teams_b"]
                    
            if "paid_status" not in data:
                data["paid_status"] = {}
            return data
            
    return default_data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def calculate_ranking(group_name, teams, results, schedule):
    # Initialize stats
    stats = {t: {"Spiele": 0, "Punkte": 0, "Diff": 0, "Erzielt": 0, "Erhalten": 0, "Satzpunkte": 0} for t in teams.keys()}
    
    # Calculate base stats
    for match in schedule:
        grp = match["group"]
        if grp != group_name:
            continue
        
        t1, t2 = match["t1"], match["t2"]
        match_id = match["id"]
        res = results.get(match_id)
        if res and res.get("played"):
            s1 = res["score1"]
            s2 = res["score2"]
            
            stats[t1]["Spiele"] += 1
            stats[t2]["Spiele"] += 1
            
            stats[t1]["Erzielt"] += s1
            stats[t1]["Erhalten"] += s2
            stats[t1]["Diff"] += (s1 - s2)
            
            stats[t2]["Erzielt"] += s2
            stats[t2]["Erhalten"] += s1
            stats[t2]["Diff"] += (s2 - s1)
            
            if s1 > s2:
                stats[t1]["Satzpunkte"] += 1
            elif s2 > s1:
                stats[t2]["Satzpunkte"] += 1

    # Convert to list for sorting
    ranking = []
    for t_id, d in stats.items():
        ranking.append({
            "Team ID": t_id,
            "Name": teams[t_id],
            "Spiele": d["Spiele"],
            "Satzpunkte": d["Satzpunkte"],
            "Punkte Diff": d["Diff"],
            "Punkte +": d["Erzielt"],
            "Punkte -": d["Erhalten"],
        })
    
    def get_direct_encounter_winner(t_a, t_b):
        for match in schedule:
            t1, t2 = match["t1"], match["t2"]
            if (t1 == t_a and t2 == t_b) or (t1 == t_b and t2 == t_a):
                match_id = match["id"]
                res = results.get(match_id)
                if res and res.get("played"):
                    s1 = res["score1"] if t1 == t_a else res["score2"]
                    s2 = res["score2"] if t1 == t_a else res["score1"]
                    if s1 > s2: return t_a
                    if s2 > s1: return t_b
        return None

    import functools
    def compare(a, b):
        if a["Satzpunkte"] != b["Satzpunkte"]:
            return b["Satzpunkte"] - a["Satzpunkte"]
        
        winner = get_direct_encounter_winner(a["Team ID"], b["Team ID"])
        if winner == a["Team ID"]:
            return -1
        elif winner == b["Team ID"]:
            return 1
            
        if a["Punkte Diff"] != b["Punkte Diff"]:
            return b["Punkte Diff"] - a["Punkte Diff"]
            
        return 0

    ranking.sort(key=functools.cmp_to_key(compare))
    
    for r in ranking:
        r["Tie-Breaker"] = ""

    for i in range(len(ranking) - 1):
        a = ranking[i]
        b = ranking[i+1]
        
        if a["Satzpunkte"] == b["Satzpunkte"]:
            winner = get_direct_encounter_winner(a["Team ID"], b["Team ID"])
            if winner == a["Team ID"]:
                ranking[i]["Tie-Breaker"] = f"Direktduell Sieg vs {b['Team ID']}"
            elif winner is None:
                if a["Punkte Diff"] > b["Punkte Diff"]:
                    ranking[i]["Tie-Breaker"] = f"Bessere Punktdiff. vs {b['Team ID']}"
            
    for i, r in enumerate(ranking):
        r["Rang"] = i + 1
        
    df = pd.DataFrame(ranking)
    df = df[["Rang", "Team ID", "Name", "Spiele", "Satzpunkte", "Punkte Diff", "Punkte +", "Punkte -", "Tie-Breaker"]]
    return df

def save_score_group(match_id):
    s1 = st.session_state[f"{match_id}_1"]
    s2 = st.session_state[f"{match_id}_2"]
    data = st.session_state.data
    data["group_matches"][match_id] = {"score1": s1, "score2": s2, "played": True}
    save_data(data)
    st.session_state.data = data
    st.session_state[f"feld_{match_id}_1"] = s1
    st.session_state[f"feld_{match_id}_2"] = s2

def save_score_feld(match_id):
    s1 = st.session_state[f"feld_{match_id}_1"]
    s2 = st.session_state[f"feld_{match_id}_2"]
    data = st.session_state.data
    data["group_matches"][match_id] = {"score1": s1, "score2": s2, "played": True}
    save_data(data)
    st.session_state.data = data
    st.session_state[f"{match_id}_1"] = s1
    st.session_state[f"{match_id}_2"] = s2

def get_expander_title(time, feld, t1_name, t2_name, res, show_feld=True):
    prefix = f"{time}"
    if show_feld:
        prefix += f" | Feld {feld}"
        
    if not res.get("played"):
        return f"{prefix}: {t1_name} vs {t2_name}"
        
    s1 = res["score1"]
    s2 = res["score2"]
    if s1 > s2:
        return f"{prefix}: 🏆 {t1_name} vs {t2_name} ({s1} : {s2}) ✅"
    elif s2 > s1:
        return f"{prefix}: {t1_name} vs 🏆 {t2_name} ({s1} : {s2}) ✅"
    else:
        return f"{prefix}: {t1_name} vs {t2_name} ({s1} : {s2}) ✅"


def reset_tournament():
    data = st.session_state.data
    for k in list(data["group_matches"].keys()):
        data["group_matches"][k] = {"score1": 0, "score2": 0, "played": False}
    for k in list(data["final_matches"].keys()):
        data["final_matches"][k] = {
            "set1_1": 0, "set1_2": 0,
            "set2_1": 0, "set2_2": 0,
            "set3_1": 0, "set3_2": 0,
            "played": False
        }
        
    save_data(data)
    st.session_state.data = data
    
    # Delete instead of setting to 0 to avoid any widget state issues
    for key in list(st.session_state.keys()):
        if key.startswith("btn_"):
            continue
        if key.endswith("_1") or key.endswith("_2") or "_set" in key:
            st.session_state[key] = 0

def get_final_winner(res):
    if not res.get("played"): return None
    sets1 = 0
    sets2 = 0
    if res.get("set1_1", 0) > res.get("set1_2", 0): sets1 += 1
    elif res.get("set1_2", 0) > res.get("set1_1", 0): sets2 += 1
    
    if res.get("set2_1", 0) > res.get("set2_2", 0): sets1 += 1
    elif res.get("set2_2", 0) > res.get("set2_1", 0): sets2 += 1
    
    if res.get("set3_1", 0) > res.get("set3_2", 0): sets1 += 1
    elif res.get("set3_2", 0) > res.get("set3_1", 0): sets2 += 1
    
    if sets1 >= 2: return 1
    if sets2 >= 2: return 2
    return None

def save_score_final(m_id):
    data = st.session_state.data
    s = {}
    for k in ["set1_1", "set1_2", "set2_1", "set2_2", "set3_1", "set3_2"]:
        s[k] = st.session_state[f"{m_id}_{k}"]
        
    played = any(v != 0 for v in s.values())
    s["played"] = played
    data["final_matches"][m_id] = s
    save_data(data)
    st.session_state.data = data
    
def get_all_final_matches(data):
    if not data.get("tournament_config"): return []
    schema = data["tournament_config"]["final_matches_schema"]
    schedule = data["tournament_config"]["schedule"]
    
    played_count = sum(1 for m in data["group_matches"].values() if m.get("played"))
    all_played = (played_count == len(schedule))
    
    # Calculate all rankings
    rankings = {}
    groups = data["tournament_config"]["groups"]
    for grp in groups:
        rankings[grp] = calculate_ranking(grp, data["teams"][grp], data["group_matches"], data["tournament_config"]["schedule"])
        
    def get_team_by_rank(grp, rank):
        if not all_played: return "Noch offen"
        df = rankings[grp]
        if len(df) >= rank:
            row = df[df["Rang"] == rank].iloc[0]
            return f"{row['Team ID']} ({row['Name']})"
        return "TBD"
        
    def resolve_ref(ref):
        if ref.startswith("rank_"):
            # e.g., rank_A_1
            parts = ref.split("_")
            grp = parts[1]
            rank = int(parts[2])
            return get_team_by_rank(grp, rank)
        elif ref.endswith("_winner") or ref.endswith("_loser"):
            parts = ref.rsplit("_", 1)
            m_id = parts[0]
            type_ = parts[1] # winner or loser
            res = data["final_matches"].get(m_id, {})
            win_idx = get_final_winner(res)
            
            if not win_idx:
                return f"Gew. {m_id}" if type_ == "winner" else f"Verl. {m_id}"
            
            # Find the match from schema to get the resolved teams
            for m in schema:
                if m["id"] == m_id:
                    t1_resolved = resolve_ref(m["t1_ref"])
                    t2_resolved = resolve_ref(m["t2_ref"])
                    if win_idx == 1:
                        return t1_resolved if type_ == "winner" else t2_resolved
                    elif win_idx == 2:
                        return t2_resolved if type_ == "winner" else t1_resolved
            return "TBD"
            
        return ref
        
    matches = []
    for m in schema:
        t1 = resolve_ref(m["t1_ref"])
        t2 = resolve_ref(m["t2_ref"])
        time_str = m.get("time", "TBD")
        court_idx = m.get("court", "?")
        info = f"{time_str} | 🏟️ FELD {court_idx} | {m['info']}"
        matches.append((m["title"], info, t1, t2, m["id"]))
        
    return matches

def render_final_match(title, info, t1, t2, m_id):
    res = data["final_matches"].get(m_id, {})
    
    for k in ["set1_1", "set1_2", "set2_1", "set2_2", "set3_1", "set3_2"]:
        if f"{m_id}_{k}" not in st.session_state:
            st.session_state[f"{m_id}_{k}"] = res.get(k, 0)
            
    winner_idx = get_final_winner(res)
    t1_disp = f"🏆 {t1}" if winner_idx == 1 else t1
    t2_disp = f"🏆 {t2}" if winner_idx == 2 else t2
    played_mark = " ✅" if res.get("played") else ""
            
    with st.expander(f"{title} | {info} | {t1_disp} vs {t2_disp}{played_mark}", expanded=not res.get("played")):
        col_hdr, col_btn = st.columns([5, 1])
        # Parse info "Time | Field" to highlight the field
        try:
            time_part, feld_part = info.split("|")
            col_hdr.markdown(f"#### <span style='color:#087650;'>{feld_part.strip()}</span> &nbsp;&nbsp; ⏰ {time_part.strip()}", unsafe_allow_html=True)
        except:
            col_hdr.markdown(f"#### {info}")
            
        col_hdr.write(f"**{t1}** vs **{t2}**")
        col_btn.button("Speichern", key=f"btn_{m_id}", on_click=save_score_final, args=(m_id,))
        
        disabled = not can_edit_match(t1, t2)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Satz 1**")
            c_a, c_b = st.columns(2)
            c_a.number_input(f"T1_1_{m_id}", step=1, min_value=0, key=f"{m_id}_set1_1", label_visibility="collapsed", disabled=disabled)
            c_b.number_input(f"T2_1_{m_id}", step=1, min_value=0, key=f"{m_id}_set1_2", label_visibility="collapsed", disabled=disabled)
        with col2:
            st.markdown("**Satz 2**")
            c_a, c_b = st.columns(2)
            c_a.number_input(f"T1_2_{m_id}", step=1, min_value=0, key=f"{m_id}_set2_1", label_visibility="collapsed", disabled=disabled)
            c_b.number_input(f"T2_2_{m_id}", step=1, min_value=0, key=f"{m_id}_set2_2", label_visibility="collapsed", disabled=disabled)
        with col3:
            st.markdown("**Satz 3**")
            c_a, c_b = st.columns(2)
            c_a.number_input(f"T1_3_{m_id}", step=1, min_value=0, key=f"{m_id}_set3_1", label_visibility="collapsed", disabled=disabled)
            c_b.number_input(f"T2_3_{m_id}", step=1, min_value=0, key=f"{m_id}_set3_2", label_visibility="collapsed", disabled=disabled)

def get_final_ranking_list(data):
    if not data.get("tournament_config"): return []
    num_teams = data["tournament_config"]["num_teams"]
    
    # We map matches to ranks based on their title/id
    # A generic approach for top 4
    ranks = {i: "—" for i in range(1, num_teams + 1)}
    
    # helper
    def get_final_teams(m_id):
        res = data["final_matches"].get(m_id, {})
        win = get_final_winner(res)
        all_m = get_all_final_matches(data)
        for title, info, t1, t2, mid in all_m:
            if mid == m_id:
                if win == 1: return t1, t2
                if win == 2: return t2, t1
        return None, None

    # Top 4 are always the same IDs
    p1, p2 = get_final_teams("m_fin_gr")
    p3, p4 = get_final_teams("m_fin_kl")
    if p1: ranks[1] = p1
    if p2: ranks[2] = p2
    if p3: ranks[3] = p3
    if p4: ranks[4] = p4
    
    if num_teams == 8:
        p5, p6 = get_final_teams("m_5_6")
        p7, p8 = get_final_teams("m_7_8")
        if p5: ranks[5] = p5
        if p6: ranks[6] = p6
        if p7: ranks[7] = p7
        if p8: ranks[8] = p8
        
    elif num_teams == 12:
        # Original 12 teams logic
        p11, p12 = get_final_teams("m_11_12")
        p9, p10 = get_final_teams("m_9_10")
        if p11: ranks[11] = p11
        if p12: ranks[12] = p12
        if p9: ranks[9] = p9
        if p10: ranks[10] = p10
        
        # 5-8 logic from original
        _, p5_w = get_final_teams("m_w")
        _, p5_x = get_final_teams("m_x")
        _, p5_y = get_final_teams("m_y")
        _, p5_z = get_final_teams("m_z")
        
        all_m = get_all_final_matches(data)
        m_w = next((m for m in all_m if m[4] == "m_w"), None)
        m_x = next((m for m in all_m if m[4] == "m_x"), None)
        m_y = next((m for m in all_m if m[4] == "m_y"), None)
        m_z = next((m for m in all_m if m[4] == "m_z"), None)
        
        # simplified 5-8 sorting (would require direct_encounter_overall, we skip deep diff for now)
        # we just list them if they exist
        losers = [p5_w, p5_x, p5_y, p5_z]
        valid_losers = [l for l in losers if l and l != "—" and not l.startswith("Verl.")]
        for i, l in enumerate(valid_losers):
            ranks[5+i] = l
            
    elif num_teams == 16:
        # Just simple assignment for now
        pass
        
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

def generate_tournament_plan_html(data, info_text):
    if not data.get("tournament_config"): return ""
    groups = data["tournament_config"]["groups"]
    teams = data["teams"]
    schedule = data["tournament_config"]["schedule"]
    num_courts = data["tournament_config"]["num_courts"]
    modes = data["tournament_config"].get("game_modes", {
        "group": {"sets": 1, "points": 21},
        "intermediate": {"sets": 2, "points": 15},
        "final": {"sets": 2, "points": 15}
    })
    
    html = '''
    <html>
    <head>
        <meta charset="utf-8">
        <title>Turnierplan</title>
        <style>
            @media print {
                .page-break { page-break-after: always; }
                body { font-size: 14pt; }
                .no-print { display: none; }
            }
            body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; color: #000; }
            h1 { color: #087650; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; page-break-inside: avoid; }
            th, td { border: 1px solid #000; padding: 10px; text-align: center; }
            th { font-weight: bold; }
            .team-col { text-align: left; }
            .score-matrix td { width: 50px; height: 50px; }
            .diagonal { background-color: #ddd !important; }
            .info-box { padding: 15px; margin-top: 20px; font-size: 16px; line-height: 1.6; border: 1px solid #000; }
        </style>
    </head>
    <body>
    '''
    
    colors = ["#fce4ec", "#e8f5e9", "#e3f2fd", "#fff3e0", "#f3e5f5"]
    
    # PAGE 1: Gruppeneinteilung
    html += "<h1>Gruppeneinteilung</h1>"
    for idx, grp in enumerate(groups):
        color = colors[idx % len(colors)]
        html += f'''
        <table style="width: 60%; margin-bottom: 30px; border: 2px solid #000;">
            <tr><th colspan="2" style="background-color: {color}; font-size: 1.2em;">Gruppe {grp}</th></tr>
        '''
        for t_id, t_name in teams[grp].items():
            html += f'<tr><td style="font-weight: bold; width: 100px; background-color: {color};">{t_id}</td><td class="team-col">{t_name}</td></tr>'
        html += "</table>"
        
    html += '<div class="page-break"></div>'
    
    # PAGE 2: Spielplan
    html += "<h1>Spielplan</h1>"
    html += "<table><tr><th style='background-color: #f0f0f0;'>Zeit</th>"
    for c in range(1, num_courts + 1):
        html += f"<th style='background-color: #f0f0f0;'>Feld {c}</th>"
    html += "</tr>"
    
    from collections import defaultdict
    matches_by_time = defaultdict(list)
    for m in schedule:
        matches_by_time[m["time"]].append(m)
        
    sorted_times = sorted(list(matches_by_time.keys()))
    
    for t in sorted_times:
        ms = matches_by_time[t]
        html += f"<tr><td style='background-color: #f0f0f0;'><b>{t}</b></td>"
        
        court_dict = {m["court"]: m for m in ms}
        for c in range(1, num_courts + 1):
            if c in court_dict:
                m = court_dict[c]
                t1 = m["t1"]
                t2 = m["t2"]
                try:
                    grp_idx = groups.index(m["group"])
                    bg = colors[grp_idx % len(colors)]
                except:
                    bg = "#fff"
                html += f'<td style="background-color: {bg};">{t1} - {t2}</td>'
            else:
                html += "<td>—</td>"
        html += "</tr>"
        
    html += f'<tr><td colspan="{num_courts + 1}" style="background-color: #ffcc80; font-weight: bold; text-align: center;">Mittagspause / Zeitpuffer</td></tr>'
    
    finals = get_all_final_matches(data)
    f_by_time = defaultdict(list)
    for f in finals:
        info_parts = f[1].split("|")
        t_str = info_parts[0].strip()
        feld_str = info_parts[1].strip() if len(info_parts) > 1 else ""
        feld_idx = 1
        import re
        m_f = re.search(r'\d+', feld_str)
        if m_f: feld_idx = int(m_f.group())
        
        f_by_time[t_str].append((feld_idx, f[0], f[2], f[3]))
        
    for t in sorted(list(f_by_time.keys())):
        ms = f_by_time[t]
        html += f"<tr><td style='background-color: #f0f0f0;'><b>{t}</b></td>"
        court_dict = {m[0]: m for m in ms}
        for c in range(1, num_courts + 1):
            if c in court_dict:
                m = court_dict[c]
                html += f'<td style="background-color: #b2ebf2;"><b>{m[1]}</b><br><small>{m[2]} vs {m[3]}</small></td>'
            else:
                html += "<td>—</td>"
        html += "</tr>"
        
    html += "</table>"
    html += '<div class="page-break"></div>'
    
    # PAGE 3: Infos/Ablauf
    html += "<h1>Infos / Ablauf</h1>"
    html += "<div class='info-box'>"
    html += f"<b>Vorrunde:</b> {modes['group']['sets']} Gewinnsatz bis {modes['group']['points']} Punkte (2 Punkte Differenz)<br><br>"
    
    html += f"<b>Zwischenrunde & Halbfinals:</b> {modes['intermediate']['sets']} Sätze bis {modes['intermediate']['points']} Punkte<br><br>"
    html += f"<b>Finalspiele:</b> {modes['final']['sets']} Sätze bis {modes['final']['points']} Punkte<br><br>"
    
    html += "Der Gewinner schreibt das Resultat ein (Punkteresultat).<br>"
    html += "Pro Satzgewinn wird ein Punkt verteilt. Bei Punktegleichheit entscheidet:<br>"
    html += "1. die direkte Begegnung<br>2. die Punktedifferenz aller Begegnungen<br><br>"
    
    html += "Das Verliererteam täfelet (schiedst) das nächste Spiel auf demselben Feld.<br><br>"
    
    html += info_text.replace('\n', '<br>')
    html += "</div>"
    
    html += '<div class="page-break"></div>'
    
    # PAGE 4+: Leere Punkte Matrizen
    for idx, grp in enumerate(groups):
        color = colors[idx % len(colors)]
        html += f"<h1>Punkte Gruppe {grp}</h1>"
        html += '<table class="score-matrix">'
        team_ids = list(teams[grp].keys())
        
        html += "<tr><th style='background-color: #fff;'></th>"
        for t in team_ids:
            html += f"<th style='background-color: {color};'>{t}</th>"
        html += "<th style='background-color: #fff;'>Punkte</th></tr>"
        
        for row_t in team_ids:
            html += f"<tr><td style='font-weight: bold; background-color: {color};'>{row_t}</td>"
            for col_t in team_ids:
                if row_t == col_t:
                    html += '<td class="diagonal"></td>'
                else:
                    html += "<td></td>"
            html += "<td></td></tr>"
            
        html += "</table>"
        if idx < len(groups) - 1:
            html += '<div class="page-break"></div>'
            
    html += "</body></html>"
    return html

def generate_report_html(data):
    if not data.get("tournament_config"): return ""
    html = '''
    <html>
    <head>
        <meta charset="utf-8">
        <title>Bündener Cup 2026 - Turnierbericht</title>
        <style>
            body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #333; line-height: 1.6; padding: 20px; max-width: 900px; margin: 0 auto; }
            h1 { color: #087650; border-bottom: 2px solid #087650; padding-bottom: 10px; }
            h2 { color: #087650; margin-top: 30px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .rank-123 { background-color: #e8f5e9; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🏆 Offizieller Turnierbericht - Bündener Cup 2026</h1>
        
        <h2>Gesamtrangliste</h2>
        <table>
            <tr><th>Rang</th><th>Team</th></tr>
    '''
    
    final_ranks = get_final_ranking_list(data)
    for rank_str, team in final_ranks:
        cls = "rank-123" if rank_str.startswith("1. Platz") or rank_str.startswith("2. Platz") or rank_str.startswith("3. Platz") else ""
        html += f'<tr class="{cls}"><td>{rank_str}</td><td>{team}</td></tr>'
        
    html += '''
        </table>
    '''
    groups = data["tournament_config"]["groups"]
    for grp in groups:
        html += f'<h2>Vorrunde - Endstand Gruppe {grp}</h2><table><tr><th>Rang</th><th>Team</th><th>Sätze</th><th>Diff</th></tr>'
        df_g = calculate_ranking(grp, data["teams"][grp], data["group_matches"], data["tournament_config"]["schedule"])
        for _, r in df_g.iterrows():
            html += f'<tr><td>{r["Rang"]}</td><td>{r["Name"]}</td><td>{r["Satzpunkte"]}</td><td>{r["Punkte Diff"]}</td></tr>'
        html += '</table>'
        
    html += '''
        <h2>🏐 Alle Vorrundenspiele</h2>
        <table>
            <tr><th>Zeit</th><th>Feld</th><th>Grp</th><th>Team 1</th><th>Team 2</th><th>Punkte</th></tr>
    '''
    schedule = data["tournament_config"]["schedule"]
    for match in schedule:
        m_id = match["id"]
        time, feld, grp, t1, t2 = match["time"], match["court"], match["group"], match["t1"], match["t2"]
        res = data["group_matches"].get(m_id, {})
        t1_name = data["teams"][grp].get(t1, t1)
        t2_name = data["teams"][grp].get(t2, t2)
        played = res.get("played", False)
        pts = f"{res.get('score1',0)} : {res.get('score2',0)}" if played else "—"
        html += f'<tr><td>{time}</td><td>Feld {feld}</td><td>{grp}</td><td>{t1_name}</td><td>{t2_name}</td><td><b>{pts}</b></td></tr>'
        
    html += '''
        </table>
        
        <h2>🥇 Alle Final- & Platzierungsspiele</h2>
        <table>
            <tr><th>Phase</th><th>Team 1</th><th>Team 2</th><th>Sätze (Punkte)</th></tr>
    '''
    all_final_matches = get_all_final_matches(data)
    for title, info, t1, t2, m_id in all_final_matches:
        res = data["final_matches"].get(m_id, {})
        played = res.get("played", False)
        
        if not played:
            pts = "—"
        else:
            sets_str = []
            for s in [1, 2, 3]:
                s1 = res.get(f"set{s}_1", 0)
                s2 = res.get(f"set{s}_2", 0)
                if s1 > 0 or s2 > 0:
                    sets_str.append(f"S{s}: {s1}:{s2}")
            pts = " | ".join(sets_str)
            if not pts: pts = "—"
            
        html += f'<tr><td><b>{title}</b><br><small style="color:#666;">{info.replace("|", " | ")}</small></td><td>{t1}</td><td>{t2}</td><td><b>{pts}</b></td></tr>'
        
    html += '''
        </table>
    </body>
    </html>
    '''
    return html


# --- Streamlit App ---
st.set_page_config(page_title="Bündener Cup 2026", layout="wide", page_icon="🏐")

# Custom CSS for BVC Calanda style
st.markdown("""
    <style>
    /* Optionale CSS-Anpassungen für den BVC Calanda Look */
    .stApp {
        background-color: #ffffff;
    }
    h1, h2, h3 {
        color: #087650 !important;
    }
    </style>
""", unsafe_allow_html=True)

# BVC Calanda Header Image
st.image("https://www.bvc-calanda.ch/static/bilder/Header.jpg", width="stretch")

st.title("🏐 Bündener Cup 2026 - Turnierauswertung")

if 'data' not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

if "logged_startup" not in st.session_state:
    print("\n" + "="*60)
    print(" 🔐 BVC TURNIER - ADMIN ZUGANG ")
    print("    Passwort für Seitenleiste: volley2026")
    if "admin_token" in data:
        print(f"    Admin Token URL: http://localhost:8501/?token={data['admin_token']}")
    print("="*60 + "\n")
    st.session_state.logged_startup = True

# -- ROLE & TOKEN SYSTEM --
if "team_tokens" not in data or "admin_token" not in data:
    import random, string
    tokens = data.get("team_tokens", {})
    if "teams" in data:
        for grp, grp_teams in data["teams"].items():
            for t_id in grp_teams.keys():
                if t_id not in tokens:
                    tokens[t_id] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    data["team_tokens"] = tokens
    if "admin_token" not in data:
        data["admin_token"] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    save_data(data)

query_token = st.query_params.get("token")
if query_token:
    if query_token == data.get("admin_token"):
        st.session_state.role = 'admin'
    else:
        found_team = None
        for t_id, tk in data.get("team_tokens", {}).items():
            if tk == query_token:
                found_team = t_id
                break
        if found_team:
            st.session_state.role = 'team'
            st.session_state.team_id = found_team
elif 'role' not in st.session_state:
    st.session_state.role = 'guest'

with st.sidebar:
    st.header("Zugriff")
    current_role = st.session_state.get("role", "guest")
    if current_role == "admin":
        st.success("Admin-Modus aktiv 🔓")
        if st.button("Logout"):
            st.session_state.role = "guest"
            st.rerun()
    elif current_role == "team":
        my_team = st.session_state.get("team_id")
        st.info(f"Team-Modus aktiv 🏐\nDu bearbeitest Ergebnisse für: **{my_team}**")
        if st.button("Als Zuschauer fortfahren"):
            st.session_state.role = "guest"
            st.session_state.team_id = None
            st.query_params.clear()
            st.rerun()
    else:
        st.write("Zuschauer-Modus 👁️")
        pwd = st.text_input("Admin Login", type="password")
        if st.button("Login"):
            if pwd == "volley2026":
                st.session_state.role = "admin"
                st.rerun()
            else:
                st.error("Falsches Passwort")

def can_edit_match(t1, t2):
    r = st.session_state.get("role")
    if r == "admin": return True
    if r == "team":
        my_team = st.session_state.get("team_id", "")
        return my_team and (my_team in str(t1) or my_team in str(t2))
    return False
# -- END ROLE SYSTEM --

import datetime
if data.get("tournament_config") is None:
    st.header("⚙️ Turnier einrichten")
    st.info("Bitte konfiguriere die Eckdaten für das neue Turnier. Das System generiert automatisch den passenden Spielplan und K.O.-Baum.")
    col1, col2 = st.columns(2)
    with col1:
        num_teams = st.selectbox("Anzahl der Teams", [8, 12, 16], index=1)
        num_courts = st.selectbox("Anzahl der Spielfelder", [2, 3, 4, 5, 6], index=1)
    with col2:
        start_time = st.time_input("Startzeit", datetime.time(9, 45))
        lunch_duration = st.number_input("Dauer Mittagspause (nach Vorrunde, in Min)", min_value=0, max_value=120, value=45)

    st.markdown("### Spiel-Modi pro Phase")
    def calc_dur(sm, pt):
        if "1 Satz" in sm: return 15 if "15" in pt else 20
        return 35 if "15" in pt else 45

    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("**Vorrunde**")
        vr_sets = st.selectbox("Sätze", ["1 Satz", "2 Gewinnsätze"], index=0, key="vr_s")
        vr_pts = st.selectbox("Punkte", ["15 Punkte", "21 Punkte"], index=1, key="vr_p")
        dur_vr = calc_dur(vr_sets, vr_pts)
        st.info(f"Berechnete Dauer: ~{dur_vr} Min")
    with c2:
        st.write("**Zwischenrunde**")
        zr_sets = st.selectbox("Sätze", ["1 Satz", "2 Gewinnsätze"], index=0, key="zr_s")
        zr_pts = st.selectbox("Punkte", ["15 Punkte", "21 Punkte"], index=1, key="zr_p")
        dur_zr = calc_dur(zr_sets, zr_pts)
        st.info(f"Berechnete Dauer: ~{dur_zr} Min")
    with c3:
        st.write("**Finale (ab Halbfinale)**")
        fi_sets = st.selectbox("Sätze", ["1 Satz", "2 Gewinnsätze"], index=1, key="fi_s")
        fi_pts = st.selectbox("Punkte", ["15 Punkte", "21 Punkte"], index=0, key="fi_p")
        dur_fi = calc_dur(fi_sets, fi_pts)
        st.info(f"Berechnete Dauer: ~{dur_fi} Min")
        
    if st.button("Turnier generieren", type="primary"):
        groups = []
        teams = {}
        if num_teams == 8:
            groups = ["A", "B"]
            teams = {"A": {f"A{i}": f"Team A{i}" for i in range(1, 5)},
                     "B": {f"B{i}": f"Team B{i}" for i in range(1, 5)}}
        elif num_teams == 12:
            groups = ["A", "B"]
            teams = {"A": {f"A{i}": f"Team A{i}" for i in range(1, 7)},
                     "B": {f"B{i}": f"Team B{i}" for i in range(1, 7)}}
        elif num_teams == 16:
            groups = ["A", "B", "C", "D"]
            teams = {g: {f"{g}{i}": f"Team {g}{i}" for i in range(1, 5)} for g in groups}
            
        from scheduler import generate_schedule, get_final_schema, generate_final_schedule
        import datetime
        groups_list = {g: list(teams[g].keys()) for g in groups}
        
        # Vorrunde
        schedule, final_time = generate_schedule(groups_list, num_courts, start_time.strftime("%H:%M"), dur_vr, lunch_start_str=None)
        
        # Pause nach der Vorrunde
        ft = datetime.datetime.strptime(final_time, "%H:%M")
        finals_start_time = (ft + datetime.timedelta(minutes=lunch_duration)).strftime("%H:%M")
        
        raw_schema = get_final_schema(num_teams)
        schema = generate_final_schedule(raw_schema, num_courts, finals_start_time, dur_zr, dur_fi, lunch_start_str=None)
        
        data["tournament_config"] = {
            "num_teams": num_teams,
            "num_groups": len(groups),
            "num_courts": num_courts,
            "groups": groups,
            "schedule": schedule,
            "final_matches_schema": schema,
            "modes": {
                "vorrunde": {"sets": vr_sets, "points": vr_pts, "duration": dur_vr},
                "zwischenrunde": {"sets": zr_sets, "points": zr_pts, "duration": dur_zr},
                "finale": {"sets": fi_sets, "points": fi_pts, "duration": dur_fi}
            }
        }
        data["teams"] = teams
        data["group_matches"] = {}
        data["final_matches"] = {}
        save_data(data)
        st.session_state.data = data
        st.rerun()
        
    st.stop()

tabs = st.tabs(["📋 Vorrunde", "🏟️ Felder", "📊 Gruppen-Ranglisten", "🥇 Finalrunde", "🏅 Turnier-Endstand", "👤 Team-Ansicht", "⚙️ Teams & Daten"])

with tabs[0]:
    st.header("📋 Spielplan Vorrunde")
    
    played_count = sum(1 for m in data["group_matches"].values() if m.get("played"))
    schedule = data["tournament_config"]["schedule"]
    all_played = (played_count == len(schedule))
    st.progress(played_count / max(1, len(schedule)), text=f"Fortschritt Vorrunde: {played_count} von {len(schedule)} Spielen absolviert")
    
    if not all_played:
        st.warning(f"Die Vorrunde ist noch nicht abgeschlossen ({played_count}/{len(schedule)} Spiele beendet). Die Finalisten stehen erst fest, wenn alle Ergebnisse eingetragen wurden.")
    else:
        st.success("Die Vorrunde ist abgeschlossen! Alle Finalisten stehen fest. Gehe zum Tab 'Finalrunde'.")

    groups = data["tournament_config"]["groups"]
    group_cols = st.columns(len(groups))
    
    for i, grp in enumerate(groups):
        with group_cols[i]:
            st.subheader(f"Gruppe {grp}")
            for match in schedule:
                if match["group"] == grp:
                    m_id = match["id"]
                    time, feld, t1, t2 = match["time"], match["court"], match["t1"], match["t2"]
                    res = data["group_matches"].get(m_id, {})
                    t1_name = data["teams"][grp].get(t1, t1)
                    t2_name = data["teams"][grp].get(t2, t2)
                    title = get_expander_title(time, feld, t1_name, t2_name, res, show_feld=True)
                    with st.expander(title, expanded=not res.get("played")):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        disabled = not can_edit_match(t1, t2)
                        if f"{m_id}_1" not in st.session_state: st.session_state[f"{m_id}_1"] = res.get("score1", 0)
                        if f"{m_id}_2" not in st.session_state: st.session_state[f"{m_id}_2"] = res.get("score2", 0)
                        c2.number_input(t1_name, step=1, min_value=0, key=f"{m_id}_1", label_visibility="collapsed", disabled=disabled)
                        c3.number_input(t2_name, step=1, min_value=0, key=f"{m_id}_2", label_visibility="collapsed", disabled=disabled)
                        st.button("Speichern", key=f"btn_{m_id}", on_click=save_score_group, args=(m_id,))

with tabs[1]:
    st.header("🏟️ Spiele nach Feld (Schiedsrichter Ansicht)")
    
    num_courts = data["tournament_config"]["num_courts"]
    courts = [i for i in range(1, num_courts + 1)]
    court_cols = st.columns(len(courts))
    
    schedule = data["tournament_config"]["schedule"]
    
    for idx, court in enumerate(courts):
        with court_cols[idx]:
            st.subheader(f"Feld {court}")
            for match in schedule:
                if match["court"] == court:
                    m_id = match["id"]
                    time, grp, t1, t2 = match["time"], match["group"], match["t1"], match["t2"]
                    res = data["group_matches"].get(m_id, {})
                    t1_name = data["teams"][grp].get(t1, t1)
                    t2_name = data["teams"][grp].get(t2, t2)
                    title = get_expander_title(time, court, t1_name, t2_name, res, show_feld=False)
                    with st.expander(title, expanded=not res.get("played")):
                        st.markdown(f"**Gruppe {grp}**")
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        disabled = not can_edit_match(t1, t2)
                        if f"feld_{m_id}_1" not in st.session_state: st.session_state[f"feld_{m_id}_1"] = res.get("score1", 0)
                        if f"feld_{m_id}_2" not in st.session_state: st.session_state[f"feld_{m_id}_2"] = res.get("score2", 0)
                        c2.number_input(t1_name, step=1, min_value=0, key=f"feld_{m_id}_1", label_visibility="collapsed", disabled=disabled)
                        c3.number_input(t2_name, step=1, min_value=0, key=f"feld_{m_id}_2", label_visibility="collapsed", disabled=disabled)
                        st.button("Speichern", key=f"btn_feld_{m_id}", on_click=save_score_feld, args=(m_id,))

with tabs[2]:
    st.header("Aktuelle Ranglisten")
    groups = data["tournament_config"]["groups"]
    
    # 2 groups per row
    for row_idx in range(0, len(groups), 2):
        cols = st.columns(2)
        for i, grp in enumerate(groups[row_idx:row_idx+2]):
            with cols[i]:
                st.subheader(f"Gruppe {grp}")
                df_g = calculate_ranking(grp, data["teams"][grp], data["group_matches"], data["tournament_config"]["schedule"])
                st.dataframe(df_g, hide_index=True)

with tabs[3]:
    st.header("Finalrunde & Platzierungsspiele")
    
    played_count = sum(1 for m in data["group_matches"].values() if m.get("played"))
    all_played = (played_count == len(data["tournament_config"]["schedule"]))
    
    if not all_played:
        st.warning(f"Die Vorrunde ist noch nicht abgeschlossen ({played_count}/{len(data['tournament_config']['schedule'])} Spiele beendet). Die Finalisten stehen erst fest, wenn alle Ergebnisse eingetragen wurden.")
    else:
        st.success("Die Vorrunde ist abgeschlossen! Die Paarungen für die Finalrunde stehen fest.")
    
    all_matches = get_all_final_matches(data)
    
    st.subheader("Platzierungsspiele & Zwischenrunde")
    for m in all_matches[:6]:
        render_final_match(*m)
        
    st.markdown("---")
    st.subheader("Halbfinals")
    for m in all_matches[6:8]:
        render_final_match(*m)
        
    st.markdown("---")
    st.subheader("Finals")
    for m in all_matches[8:]:
        render_final_match(*m)

with tabs[4]:
    st.header("🏆 Gesamtrangliste (Endstand)")
    st.info("Hier wird der finale Turnier-Endstand basierend auf den Finalspielen generiert.")
    
    # We need to compute the ranks based on final matches
    final_ranks = get_final_ranking_list(data)
    
    st.markdown("### Endergebnis")
    
    all_finished = True
    if not final_ranks:
        all_finished = False
    else:
        for rank_str, team in final_ranks:
            if team is None or "Gew" in str(team) or "Verl" in str(team) or "TBD" in str(team) or "offen" in str(team):
                all_finished = False
                break
            
    if not all_finished:
        st.warning("Die Gesamtrangliste steht erst fest, wenn alle Platzierungs- und Finalspiele abgeschlossen sind.")
        
    # Render table anyway
    html = "<table style='width:100%; text-align:left; font-size:1.1em;'>"
    html += "<tr style='border-bottom: 2px solid #087650;'><th>Rang</th><th>Team</th></tr>"
    for rank_str, team in final_ranks:
        display_team = team if team and "Gew" not in str(team) and "Verl" not in str(team) and "TBD" not in str(team) and "offen" not in str(team) else "—"
        
        row_style = "background-color: #f8f9fa;" if rank_str.startswith("1. Platz") or rank_str.startswith("2. Platz") or rank_str.startswith("3. Platz") else ""
        rank_display = rank_str
            
        html += f"<tr style='border-bottom: 1px solid #eee; {row_style}'><td style='padding: 8px;'><b>{rank_display}</b></td><td style='padding: 8px;'>{display_team}</td></tr>"
    html += "</table>"
    
    st.markdown(html, unsafe_allow_html=True)

with tabs[5]:
    st.header("👤 Deine Team-Ansicht")
    st.info("Wähle hier dein Team aus, um deinen persönlichen Turnierverlauf und deine nächsten Spiele zu sehen.")
    
    all_teams = []
    groups = data["tournament_config"]["groups"]
    for grp in groups:
        for t_id, t_name in data["teams"][grp].items():
            all_teams.append((t_id, f"{t_id} ({t_name})", grp))
            
    options = [t[0] for t in all_teams]
    default_idx = 0
    disabled = False
    
    if st.session_state.get("role") == "team" and st.session_state.get("team_id") in options:
        default_idx = options.index(st.session_state.get("team_id"))
        disabled = True
        
    selected_team_id = st.selectbox("Team auswählen", options=options, index=default_idx, disabled=disabled, format_func=lambda x: next(t[1] for t in all_teams if t[0] == x))
    selected_grp = next(t[2] for t in all_teams if t[0] == selected_team_id)
    selected_team_name = data["teams"][selected_grp][selected_team_id]
    
    st.markdown("---")
    st.subheader("📋 Deine Vorrunden-Spiele")
    
    schedule = data["tournament_config"]["schedule"]
    team_matches = [m for m in schedule if m["t1"] == selected_team_id or m["t2"] == selected_team_id]
    
    if not team_matches:
        st.write("Keine Spiele gefunden.")
    else:
        for m in team_matches:
            m_id = m["id"]
            res = data["group_matches"].get(m_id, {})
            played = res.get("played", False)
            
            is_t1 = (m["t1"] == selected_team_id)
            opponent_id = m["t2"] if is_t1 else m["t1"]
            opponent_name = data["teams"][m["group"]][opponent_id]
            
            time_str = m.get("time", "TBD")
            court_idx = m.get("court", "?")
            
            score_own = res.get("score1", 0) if is_t1 else res.get("score2", 0)
            score_opp = res.get("score2", 0) if is_t1 else res.get("score1", 0)
            
            if played:
                if score_own > score_opp:
                    result_badge = f"<span style='color:green; font-weight:bold;'>SIEG ({score_own}:{score_opp})</span>"
                elif score_own < score_opp:
                    result_badge = f"<span style='color:red; font-weight:bold;'>NIEDERLAGE ({score_own}:{score_opp})</span>"
                else:
                    result_badge = f"<span style='color:orange; font-weight:bold;'>UNENTSCHIEDEN ({score_own}:{score_opp})</span>"
            else:
                result_badge = "<span style='color:gray;'>Noch offen</span>"
                
            st.markdown(f"**{time_str} | 🏟️ FELD {court_idx}**  \n**Gegner:** {opponent_id} ({opponent_name})  \n**Ergebnis:** {result_badge}", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 0.5em 0;'>", unsafe_allow_html=True)
            
    st.markdown("---")
    st.subheader("📊 Aktueller Stand")
    
    df_g = calculate_ranking(selected_grp, data["teams"][selected_grp], data["group_matches"], data["tournament_config"]["schedule"])
    
    played_count = sum(1 for m in data["group_matches"].values() if m.get("played"))
    all_played = (played_count == len(schedule))
    
    def highlight_row(row):
        return ['background-color: #d1ecf1' if row['Team ID'] == selected_team_id else '' for _ in row]
    
    st.dataframe(df_g.style.apply(highlight_row, axis=1), hide_index=True)
    
    if not all_played:
        st.info("Die Vorrunde läuft noch. Dein finaler Platz in der Gruppe steht erst fest, wenn alle Ergebnisse eingetragen wurden.")
        
    st.markdown("---")
    st.subheader("🥇 Dein Turnierverlauf (Finalrunde)")
    
    schema = data["tournament_config"]["final_matches_schema"]
    
    def get_team_by_rank(grp, rank):
        if not all_played: return "Noch offen"
        if len(df_g) >= rank:
            row = df_g[df_g["Rang"] == rank].iloc[0]
            return row["Team ID"]
        return "TBD"

    all_finals = get_all_final_matches(data)
    
    if not all_played:
        num_teams_in_grp = len(data["teams"][selected_grp])
        st.write("Da die Vorrunde noch läuft, hier deine möglichen nächsten Spiele je nach Platzierung:")
        for r in range(1, num_teams_in_grp + 1):
            ref_str = f"rank_{selected_grp}_{r}"
            found = False
            for m in schema:
                if m["t1_ref"] == ref_str or m["t2_ref"] == ref_str:
                    time_str = m.get("time", "TBD")
                    court_idx = m.get("court", "?")
                    st.markdown(f"- **Als {r}. Platz:** {m['title']} ({time_str} | 🏟️ FELD {court_idx})")
                    found = True
            if not found:
                st.markdown(f"- **Als {r}. Platz:** Turnier beendet.")
    else:
        my_matches = []
        for title, info, t1, t2, m_id in all_finals:
            if selected_team_id in str(t1) or selected_team_name in str(t1) or selected_team_id in str(t2) or selected_team_name in str(t2):
                my_matches.append((title, info, t1, t2, m_id))
                
        if not my_matches:
            st.write("Dein Team hat leider keine weiteren Spiele in der Finalrunde.")
        else:
            for title, info, t1, t2, m_id in my_matches:
                res = data["final_matches"].get(m_id, {})
                played = res.get("played", False)
                
                win_idx = get_final_winner(res)
                
                next_winner = None
                next_loser = None
                for sm in schema:
                    if sm["t1_ref"] == f"{m_id}_winner" or sm["t2_ref"] == f"{m_id}_winner":
                        next_winner = f"{sm['title']} ({sm.get('time', 'TBD')} | Feld {sm.get('court', '?')})"
                    if sm["t1_ref"] == f"{m_id}_loser" or sm["t2_ref"] == f"{m_id}_loser":
                        next_loser = f"{sm['title']} ({sm.get('time', 'TBD')} | Feld {sm.get('court', '?')})"
                        
                st.markdown(f"**Nächstes Spiel:** {title}")
                st.markdown(f"**Wann:** {info}")
                
                display_t1 = str(t1)
                display_t2 = str(t2)
                if selected_team_id in display_t1 or selected_team_name in display_t1:
                    gegner = display_t2
                else:
                    gegner = display_t1
                st.markdown(f"**Gegner:** {gegner}")
                
                if played:
                    is_t1 = (selected_team_id in display_t1 or selected_team_name in display_t1)
                    won = (win_idx == 1 and is_t1) or (win_idx == 2 and not is_t1)
                    badge = "<span style='color:green; font-weight:bold;'>GEWONNEN 🎉</span>" if won else "<span style='color:red; font-weight:bold;'>VERLOREN</span>"
                    st.markdown(f"**Status:** {badge}", unsafe_allow_html=True)
                else:
                    if next_winner: st.markdown(f"- *Bei Sieg:* ➡️ {next_winner}")
                    if next_loser: st.markdown(f"- *Bei Niederlage:* ➡️ {next_loser}")
                    if not next_winner and not next_loser:
                        st.markdown(f"- *Dieses Spiel entscheidet eure finale Platzierung im Turnier!*")
                
                st.markdown("<hr style='margin: 0.5em 0;'>", unsafe_allow_html=True)

with tabs[6]:
    if st.session_state.get("role") != "admin":
        st.warning("Dieser Bereich ist geschützt. Bitte logge dich als Admin in der Seitenleiste ein.")
    else:
        st.header("Teams bearbeiten")
        st.info("Hier kannst du die Namen der Teams anpassen und markieren, ob sie ihre Teilnahmegebühr bezahlt haben.")
        
        groups = data["tournament_config"]["groups"]
        cols = st.columns(len(groups))
        for i, grp in enumerate(groups):
            with cols[i]:
                st.subheader(f"Gruppe {grp}")
                for k in list(data["teams"][grp].keys()):
                    col_n, col_p = st.columns([3, 1])
                    data["teams"][grp][k] = col_n.text_input(f"Team {k}", value=data["teams"][grp][k], key=f"edit_{k}", label_visibility="collapsed")
                    data["paid_status"][k] = col_p.checkbox("Bezahlt", value=data["paid_status"].get(k, False), key=f"paid_{k}")
                
        if st.button("Änderungen speichern"):
            save_data(data)
            st.session_state.data = data
            st.success("Teams und Zahlungsstatus wurden erfolgreich gespeichert!")
            st.rerun()

        st.markdown("---")
        st.subheader("📱 QR-Codes für Teams drucken")
        st.info("Jedes Team hat einen einzigartigen Token-Link. Drucke diese Codes aus, damit Teams ihre eigenen Ergebnisse live eintragen können.")
        base_url = st.text_input("Basis-URL der App (ohne abschließenden Slash)", value="http://localhost:8501")
        if st.button("QR-Codes generieren & Druckversion erstellen"):
            try:
                import qrcode
                import base64
                from io import BytesIO
                
                html_content = """<html>
                <head>
                    <meta charset="utf-8">
                    <title>Team QR Codes</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 2cm; }
                        .card { border: 2px dashed #ccc; padding: 30px; margin-bottom: 30px; text-align: center; page-break-inside: avoid; break-inside: avoid; }
                        .team-name { font-size: 28px; font-weight: bold; margin-bottom: 10px; }
                        .instruction { font-size: 18px; color: #555; margin-bottom: 20px; }
                        img { width: 350px; height: 350px; }
                        .url-text { font-family: monospace; margin-top: 15px; font-size: 14px; color: #777; }
                        @media print {
                            .card { border: 1px solid #000; page-break-inside: avoid; break-inside: avoid; }
                        }
                    </style>
                </head>
                <body>
                    <h1 style="text-align: center;">BVC Turnier - Team Logins</h1>
                """
                
                st.success("QR-Codes wurden erfolgreich generiert! Du kannst sie hier betrachten und als druckfertige Datei herunterladen.")
                
                qr_cols = st.columns(3)
                idx = 0
                
                items_to_generate = [("ADMIN", "Turnierleitung", data.get("admin_token", "FEHLER"))]
                for grp in groups:
                    for t_id, t_name in data["teams"][grp].items():
                        items_to_generate.append((t_id, t_name, data["team_tokens"].get(t_id, "FEHLER")))
                        
                for t_id, t_name, token in items_to_generate:
                        url = f"{base_url}/?token={token}"
                        
                        qr = qrcode.QRCode(version=1, box_size=10, border=4)
                        qr.add_data(url)
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        img_bytes = buf.getvalue()
                        
                        # Generate HTML
                        b64 = base64.b64encode(img_bytes).decode()
                        img_src = f"data:image/png;base64,{b64}"
                        html_content += f"""
                        <div class="card">
                            <div class="team-name">{t_id} - {t_name}</div>
                            <div class="instruction">Scannt diesen Code, um eure Ergebnisse live einzutragen!</div>
                            <img src="{img_src}" alt="QR Code für {t_name}">
                            <div class="url-text">{url}</div>
                        </div>
                        """
                        
                        with qr_cols[idx % 3]:
                            st.write(f"**{t_id} ({t_name})**")
                            st.image(img_bytes, width=150)
                            st.write(f"`{token}`")
                            st.markdown("---")
                        idx += 1
                        
                html_content += "</body></html>"
                
                st.download_button(
                    label="📄 QR-Codes als Druck-Version (.html) herunterladen",
                    data=html_content,
                    file_name="team_qrcodes.html",
                    mime="text/html",
                    type="primary"
                )
            except ImportError:
                st.error("Bitte installiere qrcode und Pillow (pip install qrcode Pillow)")

        st.markdown("---")
        st.subheader("🖨️ Turnierplan & Infoheft (für PDF Druck)")
        st.info("Hier generierst du das fertige Turnier-Heft (Spielplan, Gruppen, leere Schiri-Tabellen) für den Start des Turniers.")
        
        default_info = "Garderoben, WCs und Duschen stehen im Gebäude des Tennisclubs Chur bereit (Eingang via Tennis In),\nund wie gewohnt gibt es vor Ort auch einen kleinen Kiosk mit Getränken, Kuchen, Salat und Snacks vom Grill."
        custom_info = st.text_area("Zusätzliche Infos / Ort / Sponsor (wird auf Seite 3 gedruckt)", value=default_info, height=100)
        
        plan_html = generate_tournament_plan_html(data, custom_info)
        st.download_button(
            label="📄 Turnierplan generieren & herunterladen (.html)",
            data=plan_html,
            file_name="turnierplan.html",
            mime="text/html",
            type="primary"
        )
            
        st.markdown("---")
        st.subheader("Turnier-Bericht (Endstand)")
        st.info("Hier kannst du den kompletten Turnier-Endstand und die Vorrunden-Ergebnisse als saubere HTML-Datei herunterladen. Öffne die Datei danach einfach in deinem Browser und drücke `Strg+P` (oder `Cmd+P` auf dem Mac), um sie als PDF zu drucken.")
        
        report_html = generate_report_html(data)
        st.download_button(
            label="📄 Turnierbericht herunterladen (.html)",
            data=report_html,
            file_name="turnierbericht.html",
            mime="text/html",
            type="primary"
        )
        
        st.markdown("---")
        st.subheader("Datenverwaltung & Export")
        st.info("Hier kannst du das komplette Turnier sichern, wiederherstellen oder zurücksetzen.")

        col_exp, col_imp, col_rst = st.columns(3)
        
        with col_exp:
            st.subheader("Export (Backup)")
            import json
            import pandas as pd
            import io
            json_str = json.dumps(data, indent=4)
            st.download_button(
                label="💾 Als JSON (System) herunterladen",
                data=json_str,
                file_name="bvc_turnier_backup.json",
                mime="application/json"
            )
            
            # Build Export Dataframe
            export_rows = []
            schedule = data["tournament_config"]["schedule"]
            for match in schedule:
                m_id = match["id"]
                time, feld, t1, t2, grp = match["time"], match["court"], match["t1"], match["t2"], match["group"]
                res = data["group_matches"].get(m_id, {"score1": 0, "score2": 0})
                export_rows.append({
                    "Match_ID": m_id,
                    "Phase": f"Vorrunde Grp {grp}",
                    "Team1": data["teams"][grp].get(t1, t1),
                    "Team2": data["teams"][grp].get(t2, t2),
                    "Punkte_Team1": res.get("score1", 0),
                    "Punkte_Team2": res.get("score2", 0)
                })
                
            all_final_matches = get_all_final_matches(data)
            for title, info, t1, t2, m_id in all_final_matches:
                res = data["final_matches"].get(m_id, {})
                export_rows.append({
                    "Match_ID": m_id,
                    "Phase": title,
                    "Team1": "TBD" if "Gew" in str(t1) or "Verl" in str(t1) or "offen" in str(t1) else str(t1),
                    "Team2": "TBD" if "Gew" in str(t2) or "Verl" in str(t2) or "offen" in str(t2) else str(t2),
                    "Punkte_Team1": f"{res.get('set1_1',0)}, {res.get('set2_1',0)}, {res.get('set3_1',0)}",
                    "Punkte_Team2": f"{res.get('set1_2',0)}, {res.get('set2_2',0)}, {res.get('set3_2',0)}"
                })
                
            df_export = pd.DataFrame(export_rows)
            
            csv_buf = io.StringIO()
            df_export.to_csv(csv_buf, index=False, sep=";")
            st.download_button(
                label="📊 Als CSV herunterladen",
                data=csv_buf.getvalue(),
                file_name="bvc_turnier_export.csv",
                mime="text/csv"
            )
            
            # Optional: Excel Export if openpyxl is installed
            try:
                excel_buf = io.BytesIO()
                df_export.to_excel(excel_buf, index=False, engine='openpyxl')
                st.download_button(
                    label="📊 Als Excel herunterladen",
                    data=excel_buf.getvalue(),
                    file_name="bvc_turnier_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except ImportError:
                st.caption("Excel Export benötigt 'openpyxl' (pip install openpyxl)")
                
        with col_imp:
            st.subheader("Import")
            uploaded_file = st.file_uploader("Backup/Ergebnisse hochladen", type=["json", "csv", "xlsx"])
            if uploaded_file is not None:
                if st.button("Daten importieren"):
                    try:
                        if uploaded_file.name.endswith(".json"):
                            imported_data = json.load(uploaded_file)
                            save_data(imported_data)
                            st.session_state.data = imported_data
                            
                            if imported_data.get("tournament_config"):
                                for match in imported_data["tournament_config"]["schedule"]:
                                    m_id = match["id"]
                                    res = imported_data["group_matches"].get(m_id, {})
                                    st.session_state[f"{m_id}_1"] = res.get("score1", 0)
                                    st.session_state[f"{m_id}_2"] = res.get("score2", 0)
                                    st.session_state[f"feld_{m_id}_1"] = res.get("score1", 0)
                                    st.session_state[f"feld_{m_id}_2"] = res.get("score2", 0)
                                
                        elif uploaded_file.name.endswith(".csv") or uploaded_file.name.endswith(".xlsx"):
                            if uploaded_file.name.endswith(".csv"):
                                df_in = pd.read_csv(uploaded_file, sep=";")
                            else:
                                df_in = pd.read_excel(uploaded_file)
                                
                            curr_data = st.session_state.data
                            for _, row in df_in.iterrows():
                                m_id = row["Match_ID"]
                                
                                if str(m_id).startswith("group_"):
                                    s1 = int(row["Punkte_Team1"])
                                    s2 = int(row["Punkte_Team2"])
                                    played = (s1 != 0 or s2 != 0)
                                    curr_data["group_matches"][m_id] = {"score1": s1, "score2": s2, "played": played}
                                    st.session_state[f"{m_id}_1"] = s1
                                    st.session_state[f"{m_id}_2"] = s2
                                    st.session_state[f"feld_{m_id}_1"] = s1
                                    st.session_state[f"feld_{m_id}_2"] = s2
                                else:
                                    try:
                                        sets1 = str(row["Punkte_Team1"]).split(',')
                                        sets2 = str(row["Punkte_Team2"]).split(',')
                                        sets1 = [int(s.strip()) if s.strip().isdigit() else 0 for s in sets1] + [0,0,0]
                                        sets2 = [int(s.strip()) if s.strip().isdigit() else 0 for s in sets2] + [0,0,0]
                                    except:
                                        sets1 = [0,0,0]
                                        sets2 = [0,0,0]
                                        
                                    s_dict = {
                                        "set1_1": sets1[0], "set1_2": sets2[0],
                                        "set2_1": sets1[1], "set2_2": sets2[1],
                                        "set3_1": sets1[2], "set3_2": sets2[2],
                                    }
                                    played = any(v != 0 for v in s_dict.values())
                                    s_dict["played"] = played
                                    curr_data["final_matches"][m_id] = s_dict
                                    
                                    for k, v in s_dict.items():
                                        if k != "played":
                                            st.session_state[f"{m_id}_{k}"] = v
                                    
                            save_data(curr_data)
                            st.session_state.data = curr_data
                            
                        st.success("Daten erfolgreich importiert!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Import: {e}")
                        
        with col_rst:
            st.subheader("Turnier Reset")
            st.warning("Achtung: Dies löscht ALLE Ergebnisse.")
            if st.button("Alle Ergebnisse löschen"):
                for m in data["group_matches"].values():
                    m["score1"] = 0
                    m["score2"] = 0
                    m["played"] = False
                for m in data["final_matches"].values():
                    for k in list(m.keys()):
                        if k.startswith("set"): m[k] = 0
                    m["played"] = False
                save_data(data)
                st.success("Alle Ergebnisse wurden zurückgesetzt!")
                st.rerun()
                
            st.markdown("---")
            st.error("Gefahrenzone: Komplettes Turnier löschen")
            if st.button("⚠️ Komplettes Turnier verwerfen"):
                data["tournament_config"] = None
                data["teams"] = {}
                data["group_matches"] = {}
                data["final_matches"] = {}
                data["team_tokens"] = {}
                save_data(data)
                st.session_state.data = data
                st.session_state.clear()
                st.rerun()
