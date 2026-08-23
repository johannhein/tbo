from core.models import MatchMode

# -------------------------------------------------
# Mapping
# -------------------------------------------------
MATCH_MODE_TO_UI = {
    MatchMode.SETS_1: "1 Satz",
    MatchMode.SETS_2: "2 Sätze",
    MatchMode.SETS_3: "3 Sätze",
    MatchMode.BEST_OF_3: "2 Gewinnsätze",
    MatchMode.BEST_OF_5: "3 Gewinnsätze",
}

UI_TO_MATCH_MODE = {v: k for k, v in MATCH_MODE_TO_UI.items()}

# Mapping für die Spielpläne
MATCH_MODE_TO_SETS = {
    MatchMode.SETS_1: ["1. Satz"],
    MatchMode.SETS_2: ["1. Satz", "2. Satz"],
    MatchMode.SETS_3: ["1. Satz", "2. Satz", "3. Satz"],
    MatchMode.BEST_OF_3: ["1. Satz", "2. Satz"],
    MatchMode.BEST_OF_5: ["1. Satz", "2. Satz", "3. Satz"],
}


def ui_modus(modus: MatchMode) -> str:
    """Übersetzt den MatchMode in String für die UI."""
    return MATCH_MODE_TO_UI.get(modus, str(modus))


def format_modus(modus_ui: str, pts: int, tiebreak: int | None = None) -> str:
    """Formatiert den Text für da Protokoll."""
    parts = [f"{modus_ui} bis {pts}"]
    if tiebreak is not None:
        parts.append(f"Tiebreak bis {tiebreak}")
    return " ".join(parts)