from __future__ import annotations
import pathlib
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from config.constants import EXPORT_DIR, TEMPLATE_DIR
from core.models import Group, Match, Tournament, StageID
from services.path import ensure_dir


def render_group_schedule_html(group: Group, tournament_type: str = None, template_dir: str = TEMPLATE_DIR) -> pathlib.Path:
    """
    Rendert das Jinja2‑Template `schedule.html` mit den Daten aus `group`
    und schreibt das Ergebnis in `output_path`.
    """
    if tournament_type:
        export_dir = Path(EXPORT_DIR / tournament_type.lower())
    else:
        export_dir = Path(EXPORT_DIR)

    ensure_dir(export_dir)

    file_name =f"Spielplan_Gruppe_{group.name}.html"
    print(Path(template_dir).absolute())
    env = Environment(loader=FileSystemLoader(Path(template_dir).absolute()), autoescape=True)
    template = env.get_template("schedule.html")

    rendered = template.render(
        group=group,
        matches=group.match_list
    )

    out_file = Path(export_dir / file_name)
    out_file.write_text(rendered, encoding="utf-8")
    print(f"✅ HTML‑Datei wurde geschrieben: {out_file.resolve()}")
    return out_file


def export_stage(tournament: Tournament, stage_id: StageID):
    stage = tournament.get_stage(stage_id)

    for group in stage.groups:
        render_group_schedule_html(group= group, tournament_type=tournament.type)

