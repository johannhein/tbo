from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from config.constants import EXPORT_DIR, TEMPLATE_DIR, TOURNAMENT_NAME
from core.models import Group, Match, Tournament, StageID, MatchMode
from services.mapping import MATCH_MODE_TO_SETS, format_modus, ui_modus
from services.path import ensure_dir


def get_match_table_data(matches: list[Match], mode: MatchMode) -> dict:
    """Liefert ein Dictionary, das das Template leicht verarbeiten kann."""
    max_set_count = 0
    rows = []

    for i, m in enumerate(matches, start=1):
        set_headers = MATCH_MODE_TO_SETS.get(mode, [])
        max_set_count = max(max_set_count, len(set_headers))

        scores: dict[int, tuple[int, int]] = {
            idx + 1: tup for idx, tup in enumerate(m.sets)
        }

        rows.append(
            {
                "nr": i,
                "court": m.court,
                "t1": m.t1,
                "t2": m.t2,
                "ref": m.ref or "-",
                "mode": mode,
                "set_headers": set_headers,
                "scores": scores,
            }
        )
    return {"max_set_count": max_set_count, "rows": rows}


def render_group_schedule_html(group: Group, stage_id: StageID, tournament: Tournament, *,
                               template_dir: str = TEMPLATE_DIR, header: str = TOURNAMENT_NAME,) -> Path:
    """Rendert eine HTML-Datei für das Spielprotokoll einer Gruppe."""
    t_type = tournament.type or ""
    stage_name = f"{stage_id} {t_type}"
    modus_ui = ui_modus(group.settings.modus)

    modus = format_modus(modus_ui=modus_ui, pts=group.settings.points, tiebreak=group.settings.tiebreak)

    table_data = get_match_table_data(group.match_list, group.settings.modus)

    env = Environment(
        loader=FileSystemLoader(Path(template_dir).absolute()),
        autoescape=True,
    )
    template = env.get_template("group_match_report.html")

    rendered = template.render(
        header=header,
        stage_name=stage_name,
        modus_ui=modus_ui,
        modus=modus,
        group=group,
        max_set_count=table_data["max_set_count"],
        rows=table_data["rows"],
        MatchMode=MatchMode,
    )

    export_dir = Path(EXPORT_DIR / (tournament.type.lower() if tournament.type else ""))
    ensure_dir(export_dir)

    out_file = export_dir / f"Spielplan_Gruppe_{group.name}.html"
    out_file.write_text(rendered, encoding="utf-8")
    print(f"✅ HTML-Datei geschrieben: {out_file.resolve()}")
    return out_file


def export_stage(tournament: Tournament, stage_id: StageID):
    stage = tournament.get_stage(stage_id)

    for group in stage.groups:
        render_group_schedule_html(group=group, stage_id=stage_id, tournament=tournament)