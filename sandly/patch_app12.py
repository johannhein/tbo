import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix Tab 0 Group Matches
old_group = """                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        c2.number_input(t1_name, step=1, key=f"{m_id}_1", value=res.get("score1", 0), label_visibility="collapsed")
                        c3.number_input(t2_name, step=1, key=f"{m_id}_2", value=res.get("score2", 0), label_visibility="collapsed")"""

new_group = """                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        disabled = not can_edit_match(t1, t2)
                        c2.number_input(t1_name, step=1, min_value=0, key=f"{m_id}_1", value=res.get("score1", 0), label_visibility="collapsed", disabled=disabled)
                        c3.number_input(t2_name, step=1, min_value=0, key=f"{m_id}_2", value=res.get("score2", 0), label_visibility="collapsed", disabled=disabled)"""

content = content.replace(old_group, new_group)

# Fix Tab 1 Field View
old_feld = """                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        c2.number_input(t1_name, step=1, key=f"feld_{m_id}_1", value=res.get("score1", 0), label_visibility="collapsed")
                        c3.number_input(t2_name, step=1, key=f"feld_{m_id}_2", value=res.get("score2", 0), label_visibility="collapsed")"""

new_feld = """                        c1.write(f"**{t1_name}** vs **{t2_name}**")
                        disabled = not can_edit_match(t1, t2)
                        c2.number_input(t1_name, step=1, min_value=0, key=f"feld_{m_id}_1", value=res.get("score1", 0), label_visibility="collapsed", disabled=disabled)
                        c3.number_input(t2_name, step=1, min_value=0, key=f"feld_{m_id}_2", value=res.get("score2", 0), label_visibility="collapsed", disabled=disabled)"""

content = content.replace(old_feld, new_feld)

# Fix Finals
old_finals = """        col_btn.button("Speichern", key=f"btn_{m_id}", on_click=save_score_final, args=(m_id,))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Satz 1**")
            c_a, c_b = st.columns(2)
            c_a.number_input(f"T1_1_{m_id}", step=1, key=f"{m_id}_set1_1", label_visibility="collapsed")
            c_b.number_input(f"T2_1_{m_id}", step=1, key=f"{m_id}_set1_2", label_visibility="collapsed")
        with col2:
            st.markdown("**Satz 2**")
            c_a, c_b = st.columns(2)
            c_a.number_input(f"T1_2_{m_id}", step=1, key=f"{m_id}_set2_1", label_visibility="collapsed")
            c_b.number_input(f"T2_2_{m_id}", step=1, key=f"{m_id}_set2_2", label_visibility="collapsed")
        with col3:
            st.markdown("**Satz 3**")
            c_a, c_b = st.columns(2)
            c_a.number_input(f"T1_3_{m_id}", step=1, key=f"{m_id}_set3_1", label_visibility="collapsed")
            c_b.number_input(f"T2_3_{m_id}", step=1, key=f"{m_id}_set3_2", label_visibility="collapsed")"""

new_finals = """        col_btn.button("Speichern", key=f"btn_{m_id}", on_click=save_score_final, args=(m_id,))
        
        disabled = not can_edit_match(t1, t2)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Satz 1**")
            c_a, c_b = st.columns(2)
            c_a.number_input(f"T1_1_{m_id}", step=1, min_value=0, value=st.session_state.get(f"{m_id}_set1_1", 0), key=f"{m_id}_set1_1", label_visibility="collapsed", disabled=disabled)
            c_b.number_input(f"T2_1_{m_id}", step=1, min_value=0, value=st.session_state.get(f"{m_id}_set1_2", 0), key=f"{m_id}_set1_2", label_visibility="collapsed", disabled=disabled)
        with col2:
            st.markdown("**Satz 2**")
            c_a, c_b = st.columns(2)
            c_a.number_input(f"T1_2_{m_id}", step=1, min_value=0, value=st.session_state.get(f"{m_id}_set2_1", 0), key=f"{m_id}_set2_1", label_visibility="collapsed", disabled=disabled)
            c_b.number_input(f"T2_2_{m_id}", step=1, min_value=0, value=st.session_state.get(f"{m_id}_set2_2", 0), key=f"{m_id}_set2_2", label_visibility="collapsed", disabled=disabled)
        with col3:
            st.markdown("**Satz 3**")
            c_a, c_b = st.columns(2)
            c_a.number_input(f"T1_3_{m_id}", step=1, min_value=0, value=st.session_state.get(f"{m_id}_set3_1", 0), key=f"{m_id}_set3_1", label_visibility="collapsed", disabled=disabled)
            c_b.number_input(f"T2_3_{m_id}", step=1, min_value=0, value=st.session_state.get(f"{m_id}_set3_2", 0), key=f"{m_id}_set3_2", label_visibility="collapsed", disabled=disabled)"""

content = content.replace(old_finals, new_finals)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
