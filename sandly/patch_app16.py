import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

old_code = """    schedule = data["tournament_config"]["schedule"]
    num_courts = data["tournament_config"]["num_courts"]
    modes = data["tournament_config"]["game_modes"]
    
    html = '''"""

new_code = """    schedule = data["tournament_config"]["schedule"]
    num_courts = data["tournament_config"]["num_courts"]
    modes = data["tournament_config"].get("game_modes", {
        "group": {"sets": 1, "points": 21},
        "intermediate": {"sets": 2, "points": 15},
        "final": {"sets": 2, "points": 15}
    })
    
    html = '''"""

content = content.replace(old_code, new_code)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
