# import streamlit as st
# from utils import ranking, auth, tournament_manager, persistence, schedule as sched_mod
# from ui import helpers
# import json
# import datetime
#
#
# # ----------------------------------------------------------------------
# # Hilfs‑Callback für das „Speichern“-Button (Vorrunde)
# # ----------------------------------------------------------------------
# def _save_group_score(match_id: str):
#     """Speichert das Ergebnis eines Vorrunden‑Matches."""
#     s1 = st.session_state[f"{match_id}_1"]
#     s2 = st.session_state[f"{match_id}_2"]
#     data = st.session_state.data
#     data["group_matches"][match_id] = {"score1": s1, "score2": s2, "played": True}
#     persistence.save_data(data)
#     st.session_state.data = data
#
#
# # ----------------------------------------------------------------------
# # 1️⃣  Turnier‑Einrichtungs‑Formular (wird angezeigt, solange kein Config existiert)
# # ----------------------------------------------------------------------
# def setup_tournament():
#     """Formular zum Erstellen eines neuen Turniers."""
#     st.header("⚙️ Turnier einrichten")
#     st.info(
#         "Bitte konfiguriere die Eckdaten für das neue Turnier. "
#         "Das System generiert automatisch den passenden Spielplan und K.O.-Baum."
#     )
#
#     col1, col2 = st.columns(2)
#     with col1:
#         num_teams = st.selectbox("Anzahl der Teams", [8, 12, 16], index=1)
#         num_courts = st.selectbox("Anzahl der Spielfelder", [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], index=1)
#     with col2:
#         start_time = st.time_input("Startzeit", value=datetime.time(10, 00))
#
#
#     # ---- Spiel-Modi -------------------------------------------------
#     c1, c2, c3 = st.columns(3)
#     with c1:
#         vr_sets = st.selectbox("Vorrunde – Sätze", ["1 Satz", "2 Sätze", "2 Gewinnsätze"], index=0, key="vr_s")
#         vr_pts = st.number_input(label="Zwischenrunde – Punkte", min_value=1, max_value=99,  value=15, step=1,)
#     with c2:
#         zr_sets = st.selectbox("Zwischenrunde – Sätze", ["1 Satz", "2 Sätze", "2 Gewinnsätze"], index=0, key="zr_s")
#         zr_pts = st.number_input(label="Zwischenrunde – Punkte", min_value=1, max_value=99,  value=15, step=1,)
#     with c3:
#         fi_sets = st.selectbox("Finale – Sätze", ["1 Satz", "2 Sätze", "2 Gewinnsätze"], index=1, key="fi_s")
#         fi_pts = st.number_input(label="Zwischenrunde – Punkte", min_value=1, max_value=99,  value=15, step=1,)
#
#     # ---- Hilfsfunktion: Spieldauer aus Set-/Punkte-Auswahl ----------
#     def _calc_duration(sets: str, pts: int) -> int:
#         if "1 Satz" in sets:
#             return 15 if "15" in pts else 20
#         return 35 if "15" in pts else 45
#
#     if st.button("Turnier generieren", type="primary"):
#         # ---- Teams & Gruppen -----------------------------------------
#         if num_teams == 8:
#             groups = ["A", "B"]
#             teams = {
#                 "A": {f"A{i}": f"Team A{i}" for i in range(1, 5)},
#                 "B": {f"B{i}": f"Team B{i}" for i in range(1, 5)},
#             }
#         elif num_teams == 12:
#             groups = ["A", "B"]
#             teams = {
#                 "A": {f"A{i}": f"Team A{i}" for i in range(1, 7)},
#                 "B": {f"B{i}": f"Team B{i}" for i in range(1, 7)},
#             }
#         else:
#             groups = ["A", "B", "C", "D"]
#             teams = {
#                 g: {f"{g}{i}": f"Team {g}{i}" for i in range(1, 5)} for g in groups
#             }
#
#         # ---- Vorrunden-Plan -----------------------------------------
#         groups_dict = {g: list(teams[g].keys()) for g in groups}
#         schedule, final_start = sched_mod.generate_schedule(
#             groups=groups_dict,
#             num_courts=num_courts,
#             start_time=start_time.strftime("%H:%M"),
#             match_duration_min=_calc_duration(vr_sets, vr_pts),
#         )
#
#         # ---- K.O.-Schema --------------------------------------------
#         raw_schema = sched_mod.get_final_schema(num_teams)
#         final_schema = sched_mod.generate_final_schedule(
#             raw_schema=raw_schema,
#             num_courts=num_courts,
#             start_time=final_start,
#             inter_duration_min=_calc_duration(zr_sets, zr_pts),
#             final_duration_min=_calc_duration(fi_sets, fi_pts),
#         )
#
#         # ---- Daten-Dictionary zusammenbauen -------------------------
#         data = st.session_state.data
#         data["tournament_config"] = {
#             "num_teams": num_teams,
#             "num_groups": len(groups),
#             "num_courts": num_courts,
#             "groups": groups,
#             "schedule": schedule,
#             "final_matches_schema": final_schema,
#             "modes": {
#                 "vorrunde": {"sets": vr_sets, "points": vr_pts},
#                 "zwischenrunde": {"sets": zr_sets, "points": zr_pts},
#                 "finale": {"sets": fi_sets, "points": fi_pts},
#             },
#         }
#         data["teams"] = teams
#         data["group_matches"] = {}
#         data["final_matches"] = {}
#         data["team_tokens"] = {}
#         data["paid_status"] = {}
#         data["admin_token"] = ""
#
#         # ---- Speichern in der aktuellen Datei -----------------------
#         tournament_manager.save_tournament_data(st.session_state.current_tournament, data)
#         st.session_state.data = data
#         st.session_state.tournament_list = tournament_manager.get_all_tournaments()
#         st.success("Turnier wurde erfolgreich angelegt!")
#         st.rerun()
#
#
# # ----------------------------------------------------------------------
# # 2️⃣  Tab‑Funktionen (Vorrunde, Felder, Rankings, …)
# # ----------------------------------------------------------------------
# # def tab_group_stage():
# #     """Vorrunden‑Tab – Spielplan + Eingabefelder."""
# #     data = st.session_state.data
# #
# #     # ---- Wenn noch kein Turnier existiert, nichts rendern ----
# #     if not data.get("tournament_config"):
# #         st.info("Bitte erst ein Turnier anlegen (Tab „⚙️ Turnier einrichten“).")
# #         return
# #
# #     schedule = data["tournament_config"]["schedule"]
# #     groups   = data["tournament_config"]["groups"]
# #
# #     # Fortschritts‑Bar
# #     played = sum(1 for m in data["group_matches"].values() if m.get("played"))
# #     st.progress(
# #         played / max(1, len(schedule)),
# #         text=f"Vorrunde: {played}/{len(schedule)} Spiele"
# #     )
# #
# #     # Anzeige pro Gruppe
# #     cols = st.columns(len(groups))
# #     for i, grp in enumerate(groups):
# #         with cols[i]:
# #             st.subheader(f"Gruppe {grp}")
# #             for m in schedule:
# #                 if m["group"] != grp:
# #                     continue
# #                 m_id = m["id"]
# #                 res  = data["group_matches"].get(m_id, {})
# #                 title = helpers.get_expander_title(
# #                     m["time"], m["court"],
# #                     data["teams"][grp][m["t1"]],
# #                     data["teams"][grp][m["t2"]],
# #                     res,
# #                 )
# #                 with st.expander(title, expanded=not res.get("played")):
# #                     c1, c2, c3 = st.columns([2, 1, 1])
# #                     c1.write(
# #                         f"**{data['teams'][grp][m['t1']]}** vs "
# #                         f"**{data['teams'][grp][m['t2']]}**"
# #                     )
# #                     # Berechtigung prüfen
# #                     disabled = not auth.can_edit_match(m["t1"], m["t2"])
# #
# #                     # Session‑State‑Initialisierung (falls noch nicht vorhanden)
# #                     if f"{m_id}_1" not in st.session_state:
# #                         st.session_state[f"{m_id}_1"] = res.get("score1", 0)
# #                     if f"{m_id}_2" not in st.session_state:
# #                         st.session_state[f"{m_id}_2"] = res.get("score2", 0)
# #
# #                     # ---- Number‑Inputs mit nicht‑leeren Labels ----
# #                     c2.number_input(
# #                         label=f"Punkte {data['teams'][grp][m['t1']]}",
# #                         step=1, min_value=0,
# #                         key=f"{m_id}_1",
# #                         label_visibility="collapsed",   # Label verstecken, aber nicht leer
# #                         disabled=disabled,
# #                     )
# #                     c3.number_input(
# #                         label=f"Punkte {data['teams'][grp][m['t2']]}",
# #                         step=1, min_value=0,
# #                         key=f"{m_id}_2",
# #                         label_visibility="collapsed",
# #                         disabled=disabled,
# #                     )
# #                     st.button(
# #                         "Speichern",
# #                         key=f"btn_{m_id}",
# #                         on_click=_save_group_score,
# #                         args=(m_id,),
# #                     )
#
#
# def tab_courts():
#     """Tab „Felder“ – Übersicht nach Spielfeld sortiert."""
#     data = st.session_state.data
#     if not data.get("tournament_config"):
#         st.info("Bitte erst ein Turnier anlegen.")
#         return
#
#     schedule = data["tournament_config"]["schedule"]
#     num_courts = data["tournament_config"]["num_courts"]
#     court_cols = st.columns(num_courts)
#
#     for idx, court in enumerate(range(1, num_courts + 1)):
#         with court_cols[idx]:
#             st.subheader(f"Feld {court}")
#             for m in schedule:
#                 if m["court"] != court:
#                     continue
#                 m_id = m["id"]
#                 grp  = m["group"]
#                 res  = data["group_matches"].get(m_id, {})
#                 title = helpers.get_expander_title(
#                     m["time"], court,
#                     data["teams"][grp][m["t1"]],
#                     data["teams"][grp][m["t2"]],
#                     res,
#                     show_court=False,
#                 )
#                 with st.expander(title, expanded=not res.get("played")):
#                     st.markdown(f"**Gruppe {grp}**")
#                     c1, c2, c3 = st.columns([2, 1, 1])
#                     c1.write(
#                         f"**{data['teams'][grp][m['t1']]}** vs "
#                         f"**{data['teams'][grp][m['t2']]}**"
#                     )
#                     disabled = not auth.can_edit_match(m["t1"], m["t2"])
#
#                     if f"feld_{m_id}_1" not in st.session_state:
#                         st.session_state[f"feld_{m_id}_1"] = res.get("score1", 0)
#                     if f"feld_{m_id}_2" not in st.session_state:
#                         st.session_state[f"feld_{m_id}_2"] = res.get("score2", 0)
#
#                     c2.number_input(
#                         label=f"Punkte {data['teams'][grp][m['t1']]}",
#                         step=1, min_value=0,
#                         key=f"feld_{m_id}_1",
#                         label_visibility="collapsed",
#                         disabled=disabled,
#                     )
#                     c3.number_input(
#                         label=f"Punkte {data['teams'][grp][m['t2']]}",
#                         step=1, min_value=0,
#                         key=f"feld_{m_id}_2",
#                         label_visibility="collapsed",
#                         disabled=disabled,
#                     )
#                     st.button(
#                         "Speichern",
#                         key=f"btn_feld_{m_id}",
#                         on_click=_save_group_score,   # gleiche Callback wie oben
#                         args=(m_id,),
#                     )
#
#
# def tab_rankings():
#     """Tab „Gruppen‑Ranglisten“."""
#     data = st.session_state.data
#     if not data.get("tournament_config"):
#         st.info("Bitte erst ein Turnier anlegen.")
#         return
#
#     groups = data["tournament_config"]["groups"]
#     # 2 Gruppen pro Zeile → 2 Spalten
#     for row_idx in range(0, len(groups), 2):
#         cols = st.columns(2)
#         for i, grp in enumerate(groups[row_idx:row_idx + 2]):
#             with cols[i]:
#                 st.subheader(f"Gruppe {grp}")
#                 df = ranking.calculate_ranking(
#                     grp,
#                     data["teams"][grp],
#                     data["group_matches"],
#                     data["tournament_config"]["schedule"],
#                 )
#                 st.dataframe(df, hide_index=True)
#
#
# def tab_finals():
#     """Tab „Finalrunde & Platzierungsspiele“."""
#     data = st.session_state.data
#     if not data.get("tournament_config"):
#         st.info("Bitte erst ein Turnier anlegen.")
#         return
#
#     # Prüfen, ob die Vorrunde abgeschlossen ist
#     schedule = data["tournament_config"]["schedule"]
#     played = sum(1 for m in data["group_matches"].values() if m.get("played"))
#     all_played = (played == len(schedule))
#
#     if not all_played:
#         st.warning(
#             f"Vorrunde noch nicht fertig ({played}/{len(schedule)} Spiele). "
#             "Die Finalpaarungen werden erst angezeigt, wenn alle Vorrundenspiele eingetragen sind."
#         )
#         return
#
#     all_matches = sched_mod.get_all_final_matches(data)
#
#     # ---- Platzierungsspiele & Zwischenrunde ----
#     st.subheader("Platzierungsspiele & Zwischenrunde")
#     for m in all_matches[:6]:
#         helpers.render_final_match(*m)
#
#     st.markdown("---")
#     st.subheader("Halbfinals")
#     for m in all_matches[6:8]:
#         helpers.render_final_match(*m)
#
#     st.markdown("---")
#     st.subheader("Finals")
#     for m in all_matches[8:]:
#         helpers.render_final_match(*m)
#
#
# def tab_overview():
#     """Tab „Turnier‑Endstand“ – Gesamtrangliste."""
#     data = st.session_state.data
#     if not data.get("tournament_config"):
#         st.info("Bitte erst ein Turnier anlegen.")
#         return
#
#     final_ranks = ranking.get_final_ranking_list(data)
#
#     # Prüfen, ob alle Final‑/Platz‑Spiele abgeschlossen sind
#     all_finished = all(
#         r[1] and not any(word in str(r[1]) for word in ["Gew", "Verl", "TBD", "offen"])
#         for r in final_ranks
#     )
#     if not all_finished:
#         st.warning("Die Gesamtrangliste ist erst fest, wenn alle Final‑Spiele abgeschlossen sind.")
#
#     # HTML‑Tabelle (wie im Original)
#     html = "<table style='width:100%; text-align:left; font-size:1.1em;'>"
#     html += "<tr style='border-bottom: 2px solid #087650;'><th>Rang</th><th>Team</th></tr>"
#     for rank_str, team in final_ranks:
#         display = team if team and "Gew" not in str(team) and "Verl" not in str(team) else "—"
#         row_style = "background-color: #f8f9fa;" if rank_str.startswith("1. Platz") else ""
#         html += f"<tr style='{row_style}'><td><b>{rank_str}</b></td><td>{display}</td></tr>"
#     html += "</table>"
#     st.markdown(html, unsafe_allow_html=True)
#
#
# def tab_team_view():
#     """Tab „Team‑Ansicht“ – persönliche Übersicht für das eingeloggte Team."""
#     # Wenn kein Team‑Login, einfach Hinweis zeigen
#     if st.session_state.get("role") != "team":
#         st.info("Bitte logge dich als Team‑Nutzer ein (Token‑Link).")
#         return
#
#     data = st.session_state.data
#     my_team_id = st.session_state.get("team_id")
#     # Ermitteln, zu welcher Gruppe das Team gehört
#     my_group = next(
#         grp for grp, teams in data["teams"].items() if my_team_id in teams
#     )
#     my_name = data["teams"][my_group][my_team_id]
#
#     st.subheader(f"🏐 Dein Team: {my_team_id} – {my_name}")
#
#     # ---- Vorrundenspiele des Teams ----
#     schedule = data["tournament_config"]["schedule"]
#     my_matches = [m for m in schedule if m["t1"] == my_team_id or m["t2"] == my_team_id]
#
#     st.markdown("### 📋 Deine Vorrundenspiele")
#     for m in my_matches:
#         m_id = m["id"]
#         res = data["group_matches"].get(m_id, {})
#         opponent_id = m["t2"] if m["t1"] == my_team_id else m["t1"]
#         opponent_name = data["teams"][m["group"]][opponent_id]
#         time_str = m["time"]
#         court = m["court"]
#         if res.get("played"):
#             my_score = res["score1"] if m["t1"] == my_team_id else res["score2"]
#             opp_score = res["score2"] if m["t1"] == my_team_id else res["score1"]
#             result = "SIEG" if my_score > opp_score else "NIEDERLAGE"
#             badge = f"<span style='color:green;'>{result} ({my_score}:{opp_score})</span>"
#         else:
#             badge = "<span style='color:gray;'>Noch offen</span>"
#         st.markdown(
#             f"**{time_str} | Feld {court}** – Gegner: {opponent_id} ({opponent_name})  \n"
#             f"**Ergebnis:** {badge}",
#             unsafe_allow_html=True,
#         )
#         st.markdown("<hr>", unsafe_allow_html=True)
#
#     # ---- Aktuelle Gruppen‑Rangliste ----
#     st.markdown("### 📊 Aktuelle Rangliste deiner Gruppe")
#     df = ranking.calculate_ranking(
#         my_group,
#         data["teams"][my_group],
#         data["group_matches"],
#         data["tournament_config"]["schedule"],
#     )
#     # Zeile hervorheben, die das eigene Team enthält
#     def highlight(row):
#         return ["background-color: #d1ecf1" if row["Team ID"] == my_team_id else "" for _ in row]
#
#     st.dataframe(df.style.apply(highlight, axis=1), hide_index=True)
#
#
# def tab_admin():
#     """Admin‑Bereich – nur sichtbar, wenn ein Turnier geladen ist."""
#     st.header("⚙️ Admin‑Bereich")
#
#     # ---- 1️⃣  Guard‑Clause -------------------------------------------------
#     if not st.session_state.data.get("tournament_config"):
#         st.info("🔎 Bitte wähle ein vorhandenes Turnier aus oder erstelle ein neues, "
#                 "damit du den Admin‑Bereich nutzen kannst.")
#         return   # ← beendet die Funktion, bevor ein KeyError entstehen kann
#
#     # ----------------------------------------------------------------------
#     # 2️⃣  Teams bearbeiten
#     # ----------------------------------------------------------------------
#     st.subheader("Teams bearbeiten")
#     st.info("Hier kannst du die Namen der Teams anpassen und markieren, ob sie "
#             "ihre Teilnahmegebühr bezahlt haben.")
#     groups = st.session_state.data["tournament_config"]["groups"]
#     cols = st.columns(len(groups))
#     for i, grp in enumerate(groups):
#         with cols[i]:
#             st.subheader(f"Gruppe {grp}")
#             for k in list(st.session_state.data["teams"][grp].keys()):
#                 col_name, col_paid = st.columns([3, 1])
#                 # ---- Name ändern ------------------------------------------------
#                 new_name = col_name.text_input(
#                     f"Team {k}",
#                     value=st.session_state.data["teams"][grp][k],
#                     key=f"edit_{k}",
#                     label_visibility="collapsed",
#                 )
#                 # ---- Zahlungsstatus ------------------------------------------------
#                 paid = col_paid.checkbox(
#                     "Bezahlt",
#                     value=st.session_state.data["paid_status"].get(k, False),
#                     key=f"paid_{k}",
#                 )
#                 # Update im Session‑State
#                 st.session_state.data["teams"][grp][k] = new_name
#                 st.session_state.data["paid_status"][k] = paid
#
#     # ---- Änderungen speichern ------------------------------------------------
#     if st.button("Änderungen speichern"):
#         persistence.save_data(st.session_state.data)
#         st.session_state.data = st.session_state.data  # refresh
#         st.success("Teams und Zahlungsstatus wurden gespeichert!")
#         st.rerun()
#
#     # ----------------------------------------------------------------------
#     # 3️⃣  QR‑Codes für Teams drucken
#     # ----------------------------------------------------------------------
#     st.markdown("---")
#     st.subheader("📱 QR‑Codes für Teams")
#     st.info("Jedes Team hat einen einzigartigen Token‑Link. Drucke diese Codes aus, "
#             "damit Teams ihre eigenen Ergebnisse live eintragen können.")
#     base_url = st.text_input(
#         "Basis‑URL der App (ohne abschließenden Slash)",
#         value="http://localhost:8501"
#     )
#     if st.button("QR‑Codes generieren & Download"):
#         try:
#             import qrcode, base64
#             from io import BytesIO
#
#             html = """<html><head><meta charset="utf-8"><title>Team QR‑Codes</title>
#             <style>
#                 body{font-family:Arial; margin:2cm;}
#                 .card{border:2px dashed #ccc; padding:30px; margin-bottom:30px; text-align:center;}
#                 .team{font-size:24px; font-weight:bold; margin-bottom:10px;}
#                 img{width:350px;height:350px;}
#             </style></head><body>"""
#
#             # ---- Admin‑Token (falls vorhanden) ----
#             admin_token = st.session_state.data.get("admin_token", "")
#             if admin_token:
#                 admin_url = f"{base_url}/?token={admin_token}"
#                 html += f"""
#                 <div class="card">
#                     <div class="team">ADMIN – Turnierleitung</div>
#                     <img src="data:image/png;base64,{_qr_base64(admin_url)}">
#                     <div>{admin_token}</div>
#                 </div>
#                 """
#
#             # ---- Team‑Tokens ----
#             for grp in groups:
#                 for t_id, t_name in st.session_state.data["teams"][grp].items():
#                     token = st.session_state.data["team_tokens"].get(t_id, "")
#                     url = f"{base_url}/?token={token}"
#                     html += f"""
#                     <div class="card">
#                         <div class="team">{t_id} – {t_name}</div>
#                         <img src="data:image/png;base64,{_qr_base64(url)}">
#                         <div>{token}</div>
#                     </div>
#                     """
#
#             html += "</body></html>"
#             st.download_button(
#                 label="📄 QR‑Codes als HTML‑Datei herunterladen",
#                 data=html,
#                 file_name="team_qrcodes.html",
#                 mime="text/html",
#                 type="primary"
#             )
#         except ImportError:
#             st.error("Bitte installiere `qrcode` und `Pillow` (pip install qrcode Pillow).")
#
#     # ----------------------------------------------------------------------
#     # 4️⃣  Export / Import
#     # ----------------------------------------------------------------------
#     st.markdown("---")
#     st.subheader("Daten‑Export & Import")
#     st.info("Exportiere das komplette Turnier als JSON/CSV/Excel oder importiere "
#             "ein Backup, um Daten wiederherzustellen.")
#     # ---- Export (JSON) ----
#     json_str = json.dumps(st.session_state.data, indent=4)
#     st.download_button(
#         label="💾 JSON‑Backup herunterladen",
#         data=json_str,
#         file_name="bvc_backup.json",
#         mime="application/json"
#     )
#     # ---- CSV‑Export (Beispiel) ----
#     # (Hier könntest du deine eigene Export‑Logik einbauen)
#
#     # ---- Import ----
#     uploaded = st.file_uploader("JSON‑Backup importieren", type=["json"])
#     if uploaded and st.button("Importieren"):
#         try:
#             imported = json.load(uploaded)
#             persistence.save_data(imported)
#             st.session_state.data = imported
#             st.success("Daten erfolgreich importiert!")
#             st.rerun()
#         except Exception as e:
#             st.error(f"Import‑Fehler: {e}")
#
#     # ----------------------------------------------------------------------
#     # 5️⃣  Reset‑Funktionen
#     # ----------------------------------------------------------------------
#     st.markdown("---")
#     st.subheader("⚠️ Reset / Daten löschen")
#     if st.button("Alle Ergebnisse zurücksetzen"):
#         for m in st.session_state.data["group_matches"].values():
#             m["score1"] = 0
#             m["score2"] = 0
#             m["played"] = False
#         for m in st.session_state.data["final_matches"].values():
#             for k in list(m.keys()):
#                 if k.startswith("set"):
#                     m[k] = 0
#             m["played"] = False
#         persistence.save_data(st.session_state.data)
#         st.success("Alle Ergebnisse wurden zurückgesetzt.")
#         st.rerun()
#
#     if st.button("Komplettes Turnier löschen (Achtung!)"):
#         st.session_state.data = {
#             "tournament_config": None,
#             "teams": {},
#             "group_matches": {},
#             "final_matches": {},
#             "team_tokens": {},
#             "paid_status": {},
#             "admin_token": ""
#         }
#         persistence.save_data(st.session_state.data)
#         st.success("Alle Turnier‑Daten wurden gelöscht.")
#         st.rerun()
#
#
# # ----------------------------------------------------------------------
# # Hilfs‑Funktion: QR‑Code → Base64‑String (für den HTML‑Export)
# # ----------------------------------------------------------------------
# def _qr_base64(url: str) -> str:
#     """Erzeugt einen Base64‑String für einen QR‑Code zu `url`."""
#     import qrcode
#     from io import BytesIO
#     import base64
#
#     qr = qrcode.QRCode(box_size=10, border=4)
#     qr.add_data(url)
#     qr.make(fit=True)
#     img = qr.make_image(fill_color="black", back_color="white")
#     buf = BytesIO()
#     img.save(buf, format="PNG")
#     return base64.b64encode(buf.getvalue()).decode()