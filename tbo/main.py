import streamlit as st
from pathlib import Path

from config.constants import TOURNAMENT_NAME, IMG_PATH
from services import tournament_manager, auth
from ui import style, pages
from ui.page_new_tournament import tab_new_tournament

# ----------------------------------------------------------------------
# 1️⃣  Page‑Config & Header‑Bild
# ----------------------------------------------------------------------
st.set_page_config(page_title=TOURNAMENT_NAME, layout="wide", page_icon="🏐")
style.inject_css()

if IMG_PATH.is_file():
    st.image(str(IMG_PATH), width="stretch")
else:
    st.warning("Header‑Bild nicht gefunden – bitte prüfe assets/header.jpg")

st.title("🏐 " + TOURNAMENT_NAME)

# ----------------------------------------------------------------------
# 2️⃣  Session‑State: Turnier‑Liste & aktuelles Turnier
# ----------------------------------------------------------------------
if "tournament_list" not in st.session_state:
    st.session_state.tournament_list = tournament_manager.get_all_tournaments()

if "current_tournament" not in st.session_state:
    st.session_state.current_tournament = None

# ----------------------------------------------------------------------
# 3️⃣  Sidebar – Login + Turnier‑Auswahl (ohne extra Hinweis)
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("🔐 Zugriff & Turnier‑Auswahl")

    # ---- Turnier auswählen (Dropdown) ----
    if st.session_state.tournament_list:
        names = [t["name"] for t in st.session_state.tournament_list]
        selected_name = st.selectbox("Wähle ein Turnier", options=names, index=0)
        selected_file = next(t["file"] for t in st.session_state.tournament_list
                             if t["name"] == selected_name)

        # Wenn ein anderes Turnier gewählt wurde → laden
        if st.session_state.current_tournament != selected_file:
            st.session_state.current_tournament = selected_file
            st.session_state.data = tournament_manager.load_tournament_data(selected_file)
            st.success(f"Turnier **{selected_name}** geladen.")
    else:
        st.info("Keine Turniere vorhanden – erstelle eines über den Tab „🆕 Neues Turnier“.")

    st.markdown("---")

    # ---- Login‑Logik (Admin / Team / Guest) ----
    if st.session_state.get("role") == "admin":
        st.success("✅ Admin‑Modus aktiv")
        if st.button("Logout"):
            st.session_state.role = "guest"
            st.session_state.team_id = None
            st.rerun()
    elif st.session_state.get("role") == "team":
        my_team = st.session_state.get("team_id", "")
        st.info(f"👥 Team‑Modus aktiv – du bearbeitest **{my_team}**")
        if st.button("Als Zuschauer fortfahren"):
            st.session_state.role = "guest"
            st.session_state.team_id = None
            st.query_params.clear()
            st.rerun()
    else:
        st.write("👁️ Zuschauer‑Modus")
        pwd = st.text_input("Admin‑Passwort", type="password")
        if st.button("Login"):
            if pwd == "volley2026":
                st.session_state.role = "admin"
                st.rerun()
            else:
                st.error("❌ Falsches Passwort")

    # ---- Optional: Turnier löschen (falls gewünscht) ----
    st.markdown("---")
    if st.button("Aktuelles Turnier löschen"):
        if st.session_state.current_tournament:
            tournament_manager.delete_tournament(st.session_state.current_tournament)
            st.session_state.tournament_list = tournament_manager.get_all_tournaments()
            st.session_state.current_tournament = None
            st.session_state.data = {}
            st.success("Turnier wurde gelöscht.")
            st.rerun()
        else:
            st.warning("Kein Turnier zum Löschen ausgewählt.")

# ----------------------------------------------------------------------
# 4️⃣  Daten‑Laden (falls noch nicht im Session‑State)
# ----------------------------------------------------------------------
if "data" not in st.session_state:
    # Noch kein Turnier gewählt → leeres Dict, damit die Tabs
    # ihre internen „Bitte erst ein Turnier anlegen“‑Meldungen zeigen können.
    st.session_state.data = {}

# ----------------------------------------------------------------------
# 5️⃣  Tabs – inkl. „🆕 Neues Turnier“ (immer sichtbar)
# ----------------------------------------------------------------------
tab_names = [
    "🆕 Neues Turnier",   # <-- jetzt Teil der regulären Tab‑Leiste
    "📋 Vorrunde",
    "🏟️ Felder",
    "📊 Gruppen‑Ranglisten",
    "🥇 Finalrunde",
    "🏅 Endstand",
    "👤 Team‑Ansicht",
    "⚙️ Admin",
]
tabs = st.tabs(tab_names)

# Reihenfolge muss zu den Tab‑Namen passen
with tabs[0]:
    tab_new_tournament()          # <-- dein bereits vorhandener Tab
with tabs[1]:
    pages.tab_group_stage()
with tabs[2]:
    pages.tab_courts()
with tabs[3]:
    pages.tab_rankings()
with tabs[4]:
    pages.tab_finals()
with tabs[5]:
    pages.tab_overview()
with tabs[6]:
    pages.tab_team_view()
with tabs[7]:
    pages.tab_admin()