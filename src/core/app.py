import streamlit as st

from config.constants import TOURNAMENT_NAME
from db import init_db, get_connection, table_exists, create_table_and_fill
from ui import style, tab_standings, tab_next_stage
from ui.tab_new_tournament import tab_new_tournament
from ui.tab_pre_round import tab_group_stage
from ui.tab_presets import tab_presets

con = get_connection()
init_db(con)

with con as conn:
    if not table_exists(conn, "tournament_days"):
        create_table_and_fill(conn)


# ----------------------------------------------------------------------
# Page‑Config & Header‑Bild
# ----------------------------------------------------------------------
st.set_page_config(page_title=TOURNAMENT_NAME, layout="wide", page_icon="🏐")
style.inject_css()

# if IMG_PATH.is_file():
#     st.image(str(IMG_PATH), width="stretch")
# else:
#     st.warning(f"Header‑Bild nicht gefunden – bitte prüfe {IMG_PATH}")

st.title("🏐 " + TOURNAMENT_NAME)

# # ----------------------------------------------------------------------
# # Session‑State: Turnier‑Liste & aktuelles Turnier
# # ----------------------------------------------------------------------
# if "tournament_list" not in st.session_state:
#     st.session_state.tournament_list = tournament_manager.get_all_tournaments()
#
# if "current_tournament" not in st.session_state:
#     st.session_state.current_tournament = None

# ----------------------------------------------------------------------
# Sidebar + Login + Turnier‑Auswahl
# ----------------------------------------------------------------------
with st.sidebar:
    # st.header("🔐 Zugriff & Turnier‑Auswahl")
    #
    # # ---- Turnier auswählen (Dropdown) ----
    # if st.session_state.tournament_list:
    #     names = [t["name"] for t in st.session_state.tournament_list]
    #     selected_name = st.selectbox("Wähle ein Turnier", options=names, index=0)
    #     selected_file = next(t["file"] for t in st.session_state.tournament_list
    #                          if t["name"] == selected_name)
    #
    #     # Wenn ein anderes Turnier gewählt wurde → laden
    #     if st.session_state.current_tournament != selected_file:
    #         st.session_state.current_tournament = selected_file
    #         st.session_state.data = tournament_manager.load_tournament_data(selected_file)
    #         st.success(f"Turnier **{selected_name}** geladen.")
    # else:
    #     st.info("Keine Turniere vorhanden – erstelle eines über den Tab „🆕 Neues Turnier“.")
    #
    # st.markdown("---")

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

    # # ---- Optional: Turnier löschen (falls gewünscht) ----
    # st.markdown("---")
    # if st.button("Aktuelles Turnier löschen"):
    #     if st.session_state.current_tournament:
    #         tournament_manager.delete_tournament(st.session_state.current_tournament)
    #         st.session_state.tournament_list = tournament_manager.get_all_tournaments()
    #         st.session_state.current_tournament = None
    #         st.session_state.data = {}
    #         st.success("Turnier wurde gelöscht.")
    #         st.rerun()
    #     else:
    #         st.warning("Kein Turnier zum Löschen ausgewählt.")

# ----------------------------------------------------------------------
# Daten‑Laden (falls noch nicht im Session‑State)
# ----------------------------------------------------------------------
if "data" not in st.session_state:
    # Noch kein Turnier gewählt → leeres Dict, damit die Tabs
    # ihre internen „Bitte erst ein Turnier anlegen“‑Meldungen zeigen können.
    st.session_state.data = {}

# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
# dummy
def render_stage(stage_name):
    st.header(stage_name)

stage_dict = st.session_state.get("stage_dict", {})

tabs_config = []

tabs_config.append({
    "name": "⚙️ Voreinstellungen",
    "func": tab_presets,
    "condition": True
})

tabs_config.append({
    "name": "⚙️ Neues Turnier",
    "func": tab_new_tournament,
    "condition": True
})

tabs_config.append({
    "name": "📋 Vorrunde",
    "func": tab_group_stage,
    "condition": True
})

if stage_dict:
    for stage_id, stage_data in stage_dict.items():
        tabs_config.append({
            "name": f"🎯 {stage_id}",
            "func": lambda stage_name=stage_id, data=stage_data: tab_next_stage(stage_name, data),
            "condition": True
        })

tabs_config.append({
    "name": "🏅 Platzierungen",
    "func": tab_standings,
    "condition": True
})

visible_tabs = [tab for tab in tabs_config if tab["condition"]]

if visible_tabs:
    tab_names = [tab["name"] for tab in visible_tabs]
    tabs = st.tabs(tab_names)

    for i, tab in enumerate(visible_tabs):
        with tabs[i]:
            tab["func"]()
else:
    st.info("Keine Tabs verfügbar. Bitte erstellen Sie ein Turnier.")

