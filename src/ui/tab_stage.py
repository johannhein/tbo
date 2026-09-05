import streamlit as st

from ui.tab_new_round import tab_new_round
from ui.tab_results import tab_results


def tab_next_stage(stage_name, stage_data):
    st.header(stage_name)

    tabs = st.tabs(["📋 Übersicht", "📊 Ergebnisse", "📋 Zusammenfassung", "⏩ Nächste Runde"])

    with tabs[0]:
        st.header("test")
    with tabs[1]:
        tab_results(stage_name)
    with tabs[2]:
        st.header("test")
    with tabs[3]:
        tab_new_round(stage_name)
