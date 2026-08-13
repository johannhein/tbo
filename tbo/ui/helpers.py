# bvc_cup/ui/helpers.py
import streamlit as st
from typing import Dict

def get_expander_title(
    time: str,
    court: int,
    t1_name: str,
    t2_name: str,
    res: Dict,
    show_court: bool = True,
) -> str:
    prefix = f"{time}"
    if show_court:
        prefix += f" | Feld {court}"
    if not res.get("played"):
        return f"{prefix}: {t1_name} vs {t2_name}"
    s1, s2 = res["score1"], res["score2"]
    if s1 > s2:
        return f"{prefix}: 🏆 {t1_name} vs {t2_name} ({s1} : {s2}) ✅"
    if s2 > s1:
        return f"{prefix}: {t1_name} vs 🏆 {t2_name} ({s1} : {s2}) ✅"
    return f"{prefix}: {t1_name} vs {t2_name} ({s1} : {s2}) ✅"