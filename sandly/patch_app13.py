import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Init token
old_init = """if "team_tokens" not in data:
    import random, string
    tokens = {}
    if "teams" in data:
        for grp, grp_teams in data["teams"].items():
            for t_id in grp_teams.keys():
                tokens[t_id] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    data["team_tokens"] = tokens
    if "teams" in data: save_data(data)"""

new_init = """if "team_tokens" not in data or "admin_token" not in data:
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
    save_data(data)"""

content = content.replace(old_init, new_init)

# 2. Check token
old_check = """query_token = st.query_params.get("token")
if query_token:
    found_team = None
    for t_id, tk in data.get("team_tokens", {}).items():
        if tk == query_token:
            found_team = t_id
            break
    if found_team:
        st.session_state.role = 'team'
        st.session_state.team_id = found_team
elif 'role' not in st.session_state:
    st.session_state.role = 'guest'"""

new_check = """query_token = st.query_params.get("token")
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
    st.session_state.role = 'guest'"""

content = content.replace(old_check, new_check)

# 3. Add Admin to QR Code loop
old_qr = """                qr_cols = st.columns(3)
                idx = 0
                for grp in groups:
                    for t_id, t_name in data["teams"][grp].items():
                        token = data["team_tokens"].get(t_id, "FEHLER")"""

new_qr = """                qr_cols = st.columns(3)
                idx = 0
                
                items_to_generate = [("ADMIN", "Turnierleitung", data.get("admin_token", "FEHLER"))]
                for grp in groups:
                    for t_id, t_name in data["teams"][grp].items():
                        items_to_generate.append((t_id, t_name, data["team_tokens"].get(t_id, "FEHLER")))
                        
                for t_id, t_name, token in items_to_generate:"""

content = content.replace(old_qr, new_qr)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
