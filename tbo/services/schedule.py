"""
bvc_cup.services.schedule
~~~~~~~~~~~~~~~~~~~~~~~~~

Dieses Modul enthält die Logik, mit der der **Vorrunden‑Spielplan** und das
**K.O.-Schema** (Finale, Halbfinale, Platzierungsspiele …) generiert werden.

Die Funktionen sind bewusst klein gehalten, damit sie leicht unit‑getestet
und in anderen Kontexten (z. B. CLI‑Tool, automatisierte Tests) wiederverwendet
werden können.

Die wichtigsten Public‑APIs:

* ``generate_schedule`` – erstellt den Spielplan für die Vorrunde.
* ``get_final_schema`` – liefert das Roh‑Schema (nur die Beziehungen) für
  ein Turnier mit 8 / 12 / 16 Teams.
* ``generate_final_schedule`` – setzt das Roh‑Schema in einen konkreten
  Zeit‑/Feld‑Plan um (nach dem Vorrunden‑Ende).

Alle Funktionen arbeiten mit **Plain‑Python‑Datentypen** (``list``, ``dict``,
``str`` …) und benötigen keine externen Bibliotheken.
"""

from __future__ import annotations

import datetime as _dt
from typing import Dict, List, Tuple, Optional, Iterable

# ----------------------------------------------------------------------
# Hilfs‑Typen (nur für bessere Lesbarkeit)
# ----------------------------------------------------------------------
MatchID = str
GroupName = str
TeamID = str
CourtID = int
TimeStr = str  # z. B. "09:45"
Schedule = List[Dict]  # jedes Element entspricht einem Match‑Dict
Schema = List[Dict]   # Roh‑Schema für die Finalrunde


# ----------------------------------------------------------------------
# 1️⃣  Vorrunden‑Spielplan
# ----------------------------------------------------------------------
def _parse_time(t: str) -> _dt.datetime:
    """Wandelt ``"HH:MM"`` in ein ``datetime``‑Objekt (Datum = 1900‑01‑01)."""
    return _dt.datetime.strptime(t, "%H:%M")


def _format_time(dt: _dt.datetime) -> str:
    """Formatiert ein ``datetime``‑Objekt wieder zu ``"HH:MM"``."""
    return dt.strftime("%H:%M")


def generate_schedule(
    groups: Dict[GroupName, List[TeamID]],
    num_courts: int,
    start_time: str,
    match_duration_min: int,
) -> Tuple[Schedule, str]:
    """
    Erzeugt einen linearen Spielplan für die Vorrunde.

    Parameters
    ----------
    groups
        Mapping von Gruppennamen → Liste der Team‑IDs in dieser Gruppe.
        Beispiel: ``{"A": ["A1", "A2", "A3", "A4"], "B": ["B1", …]}``
    num_courts
        Wie viele Spielfelder gleichzeitig belegt werden können.
    start_time
        Startzeit der ersten Runde (``"HH:MM"``).
    match_duration_min
        Dauer eines einzelnen Spiels in Minuten (inkl. kurzer Pause zwischen
        den Spielen, falls du das separat einplanen willst, kannst du die
        Pause einfach zur Dauer addieren).


    Returns
    -------
    schedule
        Liste von Match‑Dictionaries. Jedes Dictionary hat die Schlüssel:

        ``id``      – eindeutige Match‑ID (z. B. ``"group_0"``)
        ``time``    – Startzeit (``"HH:MM"``)
        ``court``   – Feld‑Nummer (1‑basiert)
        ``t1`` / ``t2`` – Team‑IDs der Gegner
        ``group``   – Gruppen‑Name (``"A"``, ``"B"`` …)

    final_time_str
        Die Zeit, zu der das letzte Vorrunden‑Match endet (nach
        ``match_duration_min``).  Diese Angabe wird später für den
        Start der Finalrunde verwendet.
    """
    # ------------------------------------------------------------------
    # 1. Alle Paarungen pro Gruppe ermitteln (Round‑Robin)
    # ------------------------------------------------------------------
    raw_matches: List[Tuple[TeamID, TeamID, GroupName]] = []
    for grp_name, team_list in groups.items():
        n = len(team_list)
        for i in range(n):
            for j in range(i + 1, n):
                raw_matches.append((team_list[i], team_list[j], grp_name))

    # ------------------------------------------------------------------
    # 2. Sortieren, damit das Ergebnis reproduzierbar ist
    # ------------------------------------------------------------------
    raw_matches.sort(key=lambda x: (x[2], x[0], x[1]))

    # ------------------------------------------------------------------
    # 3. Zeitplan erzeugen – Match‑IDs, Feld‑Zuweisung, ggf. Mittagspause
    # ------------------------------------------------------------------
    schedule: Schedule = []
    current_time = _parse_time(start_time)
    lunch_start = _parse_time(lunch_start_str) if lunch_start_str else None

    for idx, (t1, t2, grp) in enumerate(raw_matches):
        # Wenn wir eine Mittagspause einlegen sollen und die aktuelle Zeit
        # den Pausen‑Start überschreitet, springen wir zur Pause.
        if lunch_start and current_time >= lunch_start:
            # Pause einlegen
            current_time += _dt.timedelta(minutes=lunch_duration_min)
            # Nach der Pause nicht erneut pausieren
            lunch_start = None

        match_id = f"group_{idx}"
        schedule.append(
            {
                "id": match_id,
                "time": _format_time(current_time),
                "court": (idx % num_courts) + 1,   # rotierendes Feld‑Schema
                "t1": t1,
                "t2": t2,
                "group": grp,
            }
        )
        # Nächstes Spiel starten
        current_time += _dt.timedelta(minutes=match_duration_min)

    final_time_str = _format_time(current_time)  # Zeit *nach* dem letzten Spiel
    return schedule, final_time_str


# ----------------------------------------------------------------------
# 2️⃣  Roh‑Schema für die Finalrunde (abhängig von der Team‑Anzahl)
# ----------------------------------------------------------------------
def get_final_schema(num_teams: int) -> Schema:
    """
    Liefert das **Roh‑Schema** (nur Beziehungen) für die K.O.-Phase.

    Das zurückgegebene Schema ist eine Liste von Dictionaries mit den
    Schlüsseln:

    * ``id``          – interne Match‑ID (z. B. ``"m_fin_gr"``)
    * ``title``       – Anzeige‑Titel (z. B. ``"Finale"``)
    * ``info``        – Kurzinfo (Zeit/Feld wird später ergänzt)
    * ``t1_ref`` / ``t2_ref`` – Referenz auf das Ergebnis einer vorherigen
      Runde oder auf einen Rang‑Platz (z. B. ``"rank_A_1"``).

    Für die gängigsten Turniergrößen (8, 12, 16) ist ein vordefiniertes
    Schema enthalten.  Wenn du ein anderes Format brauchst, kannst du das
    Dictionary einfach erweitern oder anpassen.
    """
    if num_teams == 8:
        # 2 Gruppen à 4 Teams → 4 Viertelfinals → 2 Halbfinals → Finale
        return [
            # Viertelfinale
            {
                "id": "m_qf_1",
                "title": "Viertelfinale 1",
                "info": "",
                "t1_ref": "rank_A_1",
                "t2_ref": "rank_B_4",
            },
            {
                "id": "m_qf_2",
                "title": "Viertelfinale 2",
                "info": "",
                "t1_ref": "rank_A_2",
                "t2_ref": "rank_B_3",
            },
            {
                "id": "m_qf_3",
                "title": "Viertelfinale 3",
                "info": "",
                "t1_ref": "rank_B_1",
                "t2_ref": "rank_A_4",
            },
            {
                "id": "m_qf_4",
                "title": "Viertelfinale 4",
                "info": "",
                "t1_ref": "rank_B_2",
                "t2_ref": "rank_A_3",
            },
            # Halbfinale
            {
                "id": "m_sf_1",
                "title": "Halbfinale 1",
                "info": "",
                "t1_ref": "m_qf_1_winner",
                "t2_ref": "m_qf_2_winner",
            },
            {
                "id": "m_sf_2",
                "title": "Halbfinale 2",
                "info": "",
                "t1_ref": "m_qf_3_winner",
                "t2_ref": "m_qf_4_winner",
            },
            # Finale & Spiel um Platz 3
            {
                "id": "m_fin_gr",
                "title": "Finale",
                "info": "",
                "t1_ref": "m_sf_1_winner",
                "t2_ref": "m_sf_2_winner",
            },
            {
                "id": "m_fin_kl",
                "title": "Spiel um Platz 3",
                "info": "",
                "t1_ref": "m_sf_1_loser",
                "t2_ref": "m_sf_2_loser",
            },
        ]

    if num_teams == 12:
        # Das 12‑Team‑Schema ist etwas komplexer, weil nach der Vorrunde
        # ein „Zwischenspiel‑Rund“ (Platz 5‑8) stattfindet.
        return [
            # Direkt‑Finale (Platz 1‑2)
            {
                "id": "m_fin_gr",
                "title": "Finale",
                "info": "",
                "t1_ref": "rank_A_1",
                "t2_ref": "rank_B_1",
            },
            # Spiel um Platz 3
            {
                "id": "m_fin_kl",
                "title": "Spiel um Platz 3",
                "info": "",
                "t1_ref": "rank_A_2",
                "t2_ref": "rank_B_2",
            },
            # Platz 5‑8 (vier Spiele, danach weitere Platz‑Spiele)
            {
                "id": "m_w",
                "title": "Platz 5‑8 – Spiel 1",
                "info": "",
                "t1_ref": "rank_A_3",
                "t2_ref": "rank_B_4",
            },
            {
                "id": "m_x",
                "title": "Platz 5‑8 – Spiel 2",
                "info": "",
                "t1_ref": "rank_A_4",
                "t2_ref": "rank_B_3",
            },
            {
                "id": "m_y",
                "title": "Platz 5‑8 – Spiel 3",
                "info": "",
                "t1_ref": "m_w_loser",
                "t2_ref": "m_x_loser",
            },
            {
                "id": "m_z",
                "title": "Platz 5‑8 – Spiel 4",
                "info": "",
                "t1_ref": "m_w_winner",
                "t2_ref": "m_x_winner",
            },
            # Platz 9‑12 (nur für 12‑Team‑Turniere)
            {
                "id": "m_9_10",
                "title": "Platz 9‑10",
                "info": "",
                "t1_ref": "rank_A_5",
                "t2_ref": "rank_B_6",
            },
            {
                "id": "m_11_12",
                "title": "Platz 11‑12",
                "info": "",
                "t1_ref": "rank_A_6",
                "t2_ref": "rank_B_5",
            },
        ]

    if num_teams == 16:
        # 4 Gruppen à 4 Teams → 8 Viertelfinals → 4 Halbfinals → Finale
        # (Das Schema lässt sich leicht aus dem 8‑Team‑Schema ableiten.)
        # Für die Kürze hier nur ein stark vereinfachtes Beispiel:
        return [
            # Viertelfinale (8 Matches)
            *[
                {
                    "id": f"m_qf_{i+1}",
                    "title": f"Viertelfinale {i+1}",
                    "info": "",
                    "t1_ref": f"rank_{chr(65 + i//2)}_{(i%2)*2 + 1}",
                    "t2_ref": f"rank_{chr(66 + i//2)}_{(i%2)*2 + 2}",
                }
                for i in range(8)
            ],
            # Halbfinale (4 Matches)
            *[
                {
                    "id": f"m_sf_{i+1}",
                    "title": f"Halbfinale {i+1}",
                    "info": "",
                    "t1_ref": f"m_qf_{2*i+1}_winner",
                    "t2_ref": f"m_qf_{2*i+2}_winner",
                }
                for i in range(4)
            ],
            # Finale & Platz‑3‑Spiel
            {
                "id": "m_fin_gr",
                "title": "Finale",
                "info": "",
                "t1_ref": "m_sf_1_winner",
                "t2_ref": "m_sf_2_winner",
            },
            {
                "id": "m_fin_kl",
                "title": "Spiel um Platz 3",
                "info": "",
                "t1_ref": "m_sf_1_loser",
                "t2_ref": "m_sf_2_loser",
            },
        ]

    raise ValueError(f"Unsupported number of teams: {num_teams}")


# ----------------------------------------------------------------------
# 3️⃣  Final‑Spielplan (Zeit + Feld) aus dem Roh‑Schema erzeugen
# ----------------------------------------------------------------------
def generate_final_schedule(
    raw_schema: Schema,
    num_courts: int,
    start_time: str,
    inter_duration_min: int,
    final_duration_min: int,
    lunch_start_str: Optional[str] = None,
    lunch_duration_min: int = 45,
) -> Schema:
    """
    Setzt das Roh‑Schema (aus ``get_final_schema``) in einen konkreten
    Zeit‑/Feld‑Plan um.

    Der Ablauf ist:

    1. **Zwischenrunde** (falls vorhanden) – Dauer ``inter_duration_min``.
    2. **Finale** – Dauer ``final_duration_min``.
    3. Optional: Mittagspause zwischen den beiden Phasen.

    Die Rückgabe ist das gleiche Schema‑Objekt, jedoch mit den Feldern
    ``time`` und ``court`` befüllt.

    Parameters
    ----------
    raw_schema
        Das unveränderte K.O.-Schema (Liste von Dictionaries).
    num_courts
        Wie viele Felder gleichzeitig belegt werden können.
    start_time
        Startzeit der ersten Final‑Runde (``"HH:MM"``).
    inter_duration_min
        Dauer einer „Zwischenrunde“ (z. B. Viertelfinale) in Minuten.
    final_duration_min
        Dauer einer Final‑Runde (Halbfinale, Finale, Platz‑3‑Spiel) in Minuten.
    lunch_start_str
        Optionaler Zeitpunkt, zu dem eine Mittagspause beginnt.
    lunch_duration_min
        Länge der Pause (Standard = 45 min).

    Returns
    -------
    schema
        Das überarbeitete Schema‑Objekt (mit ``time`` und ``court``).
    """
    # ------------------------------------------------------------------
    # 1. Aufteilen in „Zwischenrunde“ und „Finalrunde“
    # ------------------------------------------------------------------
    # Wir gehen davon aus, dass das Roh‑Schema bereits in der richtigen
    # Reihenfolge steht: zuerst alle Zwischenrunden‑Matches, danach die
    # Final‑Matches.  Das ist bei den vordefinierten Schemas der Fall.
    inter_matches = [m for m in raw_schema if "winner" not in m["id"] and "loser" not in m["id"]]
    final_matches = [m for m in raw_schema if "winner" in m["id"] or "loser" in m["id"] or m["id"] in {"m_fin_gr", "m_fin_kl"}]

    # ------------------------------------------------------------------
    # 2. Zeitplan für die Zwischenrunde
    # ------------------------------------------------------------------
    schedule: List[Dict] = []
    current_time = _parse_time(start_time)

    # (a) Zwischenrunde
    for idx, match in enumerate(inter_matches):
        # Mittagspause einlegen, falls definiert und wir die Schwelle überschreiten
        if lunch_start_str:
            lunch_start = _parse_time(lunch_start_str)
            if current_time >= lunch_start:
                current_time += _dt.timedelta(minutes=lunch_duration_min)
                lunch_start_str = None  # nur einmal pausieren

        match_copy = match.copy()
        match_copy["time"] = _format_time(current_time)
        match_copy["court"] = (idx % num_courts) + 1
        schedule.append(match_copy)

        current_time += _dt.timedelta(minutes=inter_duration_min)

    # ------------------------------------------------------------------
    # 3. (Optional) Mittagspause zwischen den Phasen
    # ------------------------------------------------------------------
    if lunch_start_str:
        # Wenn die Pause noch nicht stattgefunden hat, jetzt einlegen
        current_time += _dt.timedelta(minutes=lunch_duration_min)

    # ------------------------------------------------------------------
    # 4. Zeitplan für die Finalrunde
    # ------------------------------------------------------------------
    for idx, match in enumerate(final_matches):
        match_copy = match.copy()
        match_copy["time"] = _format_time(current_time)
        match_copy["court"] = (idx % num_courts) + 1
        schedule.append(match_copy)

        current_time += _dt.timedelta(minutes=final_duration_min)

    return schedule


# ----------------------------------------------------------------------
# 5️⃣  Kleine Hilfs‑Funktion für Debug‑Ausgaben (optional)
# ----------------------------------------------------------------------
def pretty_print_schedule(schedule: Iterable[Dict]) -> None:
    """
    Gibt einen lesbaren Überblick über einen Spielplan auf der Konsole aus.
    Praktisch beim Entwickeln oder beim Schreiben von Unit‑Tests.
    """
    print("-" * 60)
    print(f"{'ID':<12} {'Zeit':<6} {'Feld':<4} {'Team 1':<6} {'Team 2':<6} {'Grp':<3}")
    print("-" * 60)
    for m in schedule:
        print(
            f"{m['id']:<12} {m['time']:<6} {m['court']:<4} {m['t1']:<6} {m['t2']:<6} {m.get('group',''):<3}"
        )
    print("-" * 60)


# ----------------------------------------------------------------------
# Beispiel‑Aufruf (nur zum Testen, wird nicht beim Import ausgeführt)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Beispiel‑Daten für ein 12‑Team‑Turnier
    groups_example = {
        "A": [f"A{i}" for i in range(1, 7)],
        "B": [f"B{i}" for i in range(1, 7)],
    }

    # 1️⃣ Vorrunden‑Plan
    schedule, final_start = generate_schedule(
        groups=groups_example,
        num_courts=3,
        start_time="09:45",
        match_duration_min=15,
        lunch_start_str="11:30",
        lunch_duration_min=45,
    )
    print("\n=== Vorrunden‑Plan ===")
    pretty_print_schedule(schedule)

    # 2️⃣ K.O.-Schema + Final‑Plan
    raw_schema = get_final_schema(num_teams=12)
    final_schedule = generate_final_schedule(
        raw_schema=raw_schema,
        num_courts=3,
        start_time=final_start,
        inter_duration_min=35,
        final_duration_min=45,
        lunch_start_str=None,
    )
    print("\n=== Final‑Plan ===")
    pretty_print_schedule(final_schedule)