import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

old_code = """        st.info(f"Berechnete Dauer: ~{dur_fi} Min")
        
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
            teams = {
                "A": {f"A{i}": f"Team A{i}" for i in range(1, 5)},
                "B": {f"B{i}": f"Team B{i}" for i in range(1, 5)},
                "C": {f"C{i}": f"Team C{i}" for i in range(1, 5)},
                "D": {f"D{i}": f"Team D{i}" for i in range(1, 5)}
            }
            
        from scheduler import generate_schedule"""

new_code = """        st.info(f"Berechnete Dauer: ~{dur_fi} Min")
        
    st.markdown("### Teams eingeben (Optional)")
    st.info("Gib hier die Namen der Teams ein (einer pro Zeile oder kommagetrennt). Die Teams werden dann zufällig in die Gruppen verteilt.")
    team_input = st.text_area("Team-Namen", height=100, placeholder="Team 1, Team 2\\nTeam 3...")
        
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
            teams = {
                "A": {f"A{i}": f"Team A{i}" for i in range(1, 5)},
                "B": {f"B{i}": f"Team B{i}" for i in range(1, 5)},
                "C": {f"C{i}": f"Team C{i}" for i in range(1, 5)},
                "D": {f"D{i}": f"Team D{i}" for i in range(1, 5)}
            }
            
        # Parse and assign input teams
        input_teams = [t.strip() for t in team_input.replace(',', '\\n').split('\\n') if t.strip()]
        if input_teams:
            import random
            random.shuffle(input_teams)
            for grp, grp_dict in teams.items():
                for k in grp_dict.keys():
                    if input_teams:
                        grp_dict[k] = input_teams.pop(0)
            
        from scheduler import generate_schedule"""

content = content.replace(old_code, new_code)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
