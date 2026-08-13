import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Print Log on Startup
old_data_load = """data = st.session_state.data

# -- ROLE & TOKEN SYSTEM --"""

new_data_load = """data = st.session_state.data

if "logged_startup" not in st.session_state:
    print("\\n" + "="*60)
    print(" 🔐 BVC TURNIER - ADMIN ZUGANG ")
    print("    Passwort für Seitenleiste: volley2026")
    if "admin_token" in data:
        print(f"    Admin Token URL: http://localhost:8501/?token={data['admin_token']}")
    print("="*60 + "\\n")
    st.session_state.logged_startup = True

# -- ROLE & TOKEN SYSTEM --"""

content = content.replace(old_data_load, new_data_load)

# 2. Fix number_input in Tab 0
old_tab0 = """                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        disabled = not can_edit_match(t1, t2)
                        c2.number_input(t1_name, step=1, min_value=0, key=f"{m_id}_1", value=res.get("score1", 0), label_visibility="collapsed", disabled=disabled)
                        c3.number_input(t2_name, step=1, min_value=0, key=f"{m_id}_2", value=res.get("score2", 0), label_visibility="collapsed", disabled=disabled)"""

new_tab0 = """                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        disabled = not can_edit_match(t1, t2)
                        if f"{m_id}_1" not in st.session_state: st.session_state[f"{m_id}_1"] = res.get("score1", 0)
                        if f"{m_id}_2" not in st.session_state: st.session_state[f"{m_id}_2"] = res.get("score2", 0)
                        c2.number_input(t1_name, step=1, min_value=0, key=f"{m_id}_1", label_visibility="collapsed", disabled=disabled)
                        c3.number_input(t2_name, step=1, min_value=0, key=f"{m_id}_2", label_visibility="collapsed", disabled=disabled)"""

content = content.replace(old_tab0, new_tab0)

# 3. Fix number_input in Tab 1
old_tab1 = """                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        disabled = not can_edit_match(t1, t2)
                        c2.number_input(t1_name, step=1, min_value=0, key=f"feld_{m_id}_1", value=res.get("score1", 0), label_visibility="collapsed", disabled=disabled)
                        c3.number_input(t2_name, step=1, min_value=0, key=f"feld_{m_id}_2", value=res.get("score2", 0), label_visibility="collapsed", disabled=disabled)"""

new_tab1 = """                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        disabled = not can_edit_match(t1, t2)
                        if f"feld_{m_id}_1" not in st.session_state: st.session_state[f"feld_{m_id}_1"] = res.get("score1", 0)
                        if f"feld_{m_id}_2" not in st.session_state: st.session_state[f"feld_{m_id}_2"] = res.get("score2", 0)
                        c2.number_input(t1_name, step=1, min_value=0, key=f"feld_{m_id}_1", label_visibility="collapsed", disabled=disabled)
                        c3.number_input(t2_name, step=1, min_value=0, key=f"feld_{m_id}_2", label_visibility="collapsed", disabled=disabled)"""

content = content.replace(old_tab1, new_tab1)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
