#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit‑App: editierbare Tabelle `tournament_days`.
- Daten werden nur einmal pro 5 Minuten gecached.
- Änderungen (Insert/Update/Delete) werden sofort in SQLite geschrieben.
- Die Tabelle ist zentriert und hat eine maximale Breite von 720 px.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from config.constants import MAX_COURT_NUM
from db.court_store import get_connection
from db.days_store import load_table, delete_row, upsert_row

# ----------------------------------------------------------------------
# 0️⃣  Streamlit‑Konfiguration (muss ganz oben stehen!)
# ----------------------------------------------------------------------
st.set_page_config(page_title="Tournament Days Editor", layout="wide")

# ----------------------------------------------------------------------
# 1️⃣  Pfad zur SQLite‑Datei (anpassen, falls nötig)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# 3️⃣  Cache‑Wrapper – **einmal** definiert, keine freie Variable mehr
# ----------------------------------------------------------------------
@st.cache_data(ttl=300)   # 5 Minuten Cache
def get_cached_data() -> pd.DataFrame:
    """Lädt die Daten (cached) – kümmert sich selbst um die Connection."""
    with get_connection() as conn:
        return load_table(conn)


def find_day_court_conflicts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gibt einen DataFrame zurück, der alle Zeilen enthält,
    deren *einzelne* Courts an dem jeweiligen Tag bereits von
    einem anderen Turnier belegt sind.
    """
    # Jede Court‑ID in eine eigene Zeile bringen
    exploded = df.explode("courts")

    # Gruppen, die mehr als einmal vorkommen → Konflikt
    dup = (
        exploded.groupby(["day", "courts"])
        .filter(lambda g: len(g) > 1)          # >1 = mindestens 2 Turniere nutzen das Feld
        .reset_index(drop=True)
    )

    # Alle betroffenen Turnier‑Typen zurückgeben (Original‑Zeilen)
    conflict_types = dup["type"].unique()
    return df[df["type"].isin(conflict_types)]


# ----------------------------------------------------------------------
# 4️⃣  UI‑Funktion (Tab‑Inhalt)
# ----------------------------------------------------------------------
def tab_presets() -> None:
    st.header("Voreinstellungen")

    # --------------------------------------------------------------
    # 2.1  CSS‑Block (max‑width)
    # --------------------------------------------------------------
    st.markdown(
        """
        <style>
        .centered-table {
            max-width: 720px;
            margin: 0 auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------
    # 2.2  Container
    # --------------------------------------------------------------
    with st.container():
        st.markdown('<div class="centered-table">', unsafe_allow_html=True)

        # ----------------------------------------------------------
        # 2.3  Daten holen (cached)
        # ----------------------------------------------------------
        df_original = get_cached_data()

        # ----------------------------------------------------------
        # 2.4  Data‑Editor (Breite = content, nicht full‑width)
        # ----------------------------------------------------------
        st.subheader("📋 Allgemeine Daten")

        cols = st.columns(2)
        with cols[0]:
            edited_df = st.data_editor(
                df_original,
                num_rows="dynamic",
                width='content',
                hide_index=True,
                column_config={
                    "type": st.column_config.TextColumn(
                        "Turnier", required=True
                    ),
                    "day": st.column_config.SelectboxColumn(
                        "Tag",
                        options=[
                            "Montag", "Dienstag", "Mittwoch", "Donnerstag",
                            "Freitag", "Samstag", "Sonntag"
                        ],
                        required=True,
                    ),
                    "height": st.column_config.SelectboxColumn(
                        "Netzhöhe",
                        options=["Damen", "Herren", "Mixed"],
                        required=True,
                    ),
                    # --------------------------------------------------
                    #  Multiselect – jetzt mit **String‑Optionen**
                    # --------------------------------------------------
                    "courts": st.column_config.MultiselectColumn(
                        "Felder",
                        options=[str(i) for i in range(1, MAX_COURT_NUM + 1)],   # "1" … "16"
                        required=True,
                        help="Mehrere Plätze auswählen – wird als JSON‑String gespeichert",
                    ),
                },
            )

        with cols[1]:
            st.caption(
                """
                • **Primärschlüssel**: `type` muss eindeutig sein.  
                • **Zeilen hinzufügen / entfernen**: Plus‑/Minus‑Symbol unten im Editor.  
                • **Änderungen erst wirksam** nach Klick auf **„Änderungen speichern“**.  
                """
            )

        conflict_df = find_day_court_conflicts(edited_df)  # ← NEW

        if not conflict_df.empty:  # ← NEW
            # Wir bauen für jede betroffene Zeile eine lesbare Meldung:
            for _, row in conflict_df.iterrows():
                day = row["day"]
                # Welche Courts dieser Zeile kollidieren?
                selected = set(row["courts"])
                # Courts, die an diesem Tag von *anderen* Zeilen gewählt wurden:
                other = (
                    edited_df[edited_df["type"] != row["type"]]
                    .explode("courts")
                    .loc[lambda d: d["day"] == day, "courts"]
                    .astype(str)
                    .unique()
                )
                overlap = selected.intersection(other)
                if overlap:
                    st.warning(
                        f"⚠️ **{row['type']}** am **{day}** verwendet Feld(e) "
                        f"{sorted(overlap)} – bereits von einem anderen Turnier belegt."
                    )

        # ----------------------------------------------------------
        # 2.5  Änderungen erkennen
        # ----------------------------------------------------------
        def detect_changes(
            original: pd.DataFrame, edited: pd.DataFrame
        ) -> tuple[list[pd.Series], list[str]]:
            merged = edited.merge(original[["type"]], on="type", how="left", indicator=True)
            to_upsert = edited[merged["_merge"] != "right_only"]
            to_delete = original[~original["type"].isin(edited["type"])]["type"].tolist()
            return list(to_upsert.itertuples(index=False, name=None)), to_delete

        to_upsert, to_delete = detect_changes(df_original, edited_df)

        # ----------------------------------------------------------
        # 2.6  Änderungen speichern
        # ----------------------------------------------------------
        if st.button("💾  Änderungen speichern", type="primary"):
            # 1️⃣  Löschungen
            for typ in to_delete:
                try:
                    delete_row(typ)
                    st.success(f"✅ Gelöscht: `{typ}`")
                except sqlite3.Error as e:
                    st.error(f"❌ Fehler beim Löschen von `{typ}`: {e}")

            # 2️⃣  Inserts / Updates
            for row in to_upsert:
                # row ist ein Tupel (type, day, height, courts) – courts ist bereits List[str]
                try:
                    series = pd.Series(row, index=["type", "day", "height", "courts"])
                    upsert_row(series)          # konvertiert intern zu JSON‑String
                    st.success(f"✅ Gespeichert: `{row[0]}`")
                except sqlite3.Error as e:
                    st.error(f"❌ Fehler beim Speichern von `{row[0]}`: {e}")

            # Cache leeren und UI neu laden
            st.cache_data.clear()
            st.rerun()                         # <-- neuer Aufruf (statt experimental_rerun)

        # ----------------------------------------------------------
        # 2.7  Container schließen
        # ----------------------------------------------------------
        st.markdown("</div>", unsafe_allow_html=True)

