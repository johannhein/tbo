import sqlite3
import pandas as pd
import streamlit as st

from db.court_store import get_connection
from db.days_store import load_table, delete_row, upsert_row

# Streamlit‑Konfiguration
st.set_page_config(page_title="Tournament Days Editor", layout="wide")


# Cache‑Wrapper
@st.cache_data(ttl=300)
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
        .filter(lambda g: len(g) > 1)
        .reset_index(drop=True)
    )

    # Alle betroffenen Turnier‑Typen zurückgeben (Original‑Zeilen)
    conflict_types = dup["type"].unique()
    return df[df["type"].isin(conflict_types)]


def detect_changes(original: pd.DataFrame, edited: pd.DataFrame) -> tuple[list[pd.Series], list[str]]:
    merged = edited.merge(original[["type"]], on="type", how="left", indicator=True)
    to_upsert = edited[merged["_merge"] != "right_only"]
    to_delete = original[~original["type"].isin(edited["type"])]["type"].tolist()
    return list(to_upsert.itertuples(index=False, name=None)), to_delete


def tab_presets() -> None:
    st.header("Voreinstellungen")

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

    cols = st.columns(5)

    with cols[0]:
        st.selectbox(
            "Anzahl der verfügbaren Felder",
            options=range(1, 20),
            index=15,
            key="max_courts_num"
        )

    # Container
    with st.container():
        st.markdown('<div class="centered-table">', unsafe_allow_html=True)

        df_original = get_cached_data()

        # Data‑Editor
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
                    "courts": st.column_config.MultiselectColumn(
                        "Felder",
                        options=[str(i) for i in range(1, st.session_state["max_courts_num"] + 1)],
                        required=True,
                        help="Mehrere Plätze auswählen – wird als JSON‑String gespeichert",
                    ),
                },
            )

        with cols[1]:
            st.caption(
                """
                • **Turnier**: `Tunier` muss eindeutig sein und den Turnieren in der Anmeldung entsprechen.
                • **Zeilen hinzufügen / entfernen**: Plus‑/Minus‑Symbol unten im Editor.
                • **Felder**: Zum Zuweisen zwei Mal in die Zelle klicken.
                • **Änderungen erst wirksam** nach Klick auf **„Änderungen speichern“**.
                """
            )

        conflict_df = find_day_court_conflicts(edited_df)

        if not conflict_df.empty:
            for _, row in conflict_df.iterrows():
                day = row["day"]
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
                if len(overlap) == 1:
                    field = next(iter(overlap))
                    st.warning(f"⚠️ Das Feld {field} ist schon vom {row['type']} Turnier belegt.")
                if len(overlap) > 1:
                    st.warning(f"⚠️ Die Felder {", ".join(sorted(overlap))} sind schon vom {row['type']} Turnier belegt.")

        # Änderungen erkennen
        to_upsert, to_delete = detect_changes(df_original, edited_df)

        # Änderungen speichern
        if st.button("💾  Änderungen speichern", type="primary"):
            for typ in to_delete:
                try:
                    delete_row(typ)
                    st.success(f"✅ Gelöscht: `{typ}`")
                except sqlite3.Error as e:
                    st.error(f"❌ Fehler beim Löschen von `{typ}`: {e}")

            for row in to_upsert:
                # row ist ein Tupel (type, day, height, courts) – courts ist bereits List[str]
                try:
                    series = pd.Series(row, index=["type", "day", "height", "courts"])
                    upsert_row(series)          # konvertiert intern zu JSON‑String
                    st.success(f"✅ Gespeichert: `{row[0]}`")
                except sqlite3.Error as e:
                    st.error(f"❌ Fehler beim Speichern von `{row[0]}`: {e}")

            st.cache_data.clear()
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
