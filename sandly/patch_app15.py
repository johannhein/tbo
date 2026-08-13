import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Insert generate_tournament_plan_html before generate_report_html
new_func = """def generate_tournament_plan_html(data, info_text):
    if not data.get("tournament_config"): return ""
    groups = data["tournament_config"]["groups"]
    teams = data["teams"]
    schedule = data["tournament_config"]["schedule"]
    num_courts = data["tournament_config"]["num_courts"]
    modes = data["tournament_config"]["game_modes"]
    
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
        m_f = re.search(r'\\d+', feld_str)
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
    
    html += info_text.replace('\\n', '<br>')
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

def generate_report_html(data):"""

content = content.replace("def generate_report_html(data):", new_func)

# 2. Add UI for Tournament Plan
old_ui = """        st.markdown("---")
        st.subheader("Turnier-Bericht (für PDF Druck)")"""

new_ui = """        st.markdown("---")
        st.subheader("🖨️ Turnierplan & Infoheft (für PDF Druck)")
        st.info("Hier generierst du das fertige Turnier-Heft (Spielplan, Gruppen, leere Schiri-Tabellen) für den Start des Turniers.")
        
        default_info = "Garderoben, WCs und Duschen stehen im Gebäude des Tennisclubs Chur bereit (Eingang via Tennis In),\\nund wie gewohnt gibt es vor Ort auch einen kleinen Kiosk mit Getränken, Kuchen, Salat und Snacks vom Grill."
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
        st.subheader("Turnier-Bericht (Endstand)")"""

content = content.replace(old_ui, new_ui)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
