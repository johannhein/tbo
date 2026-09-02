from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from config.constants import TEMPLATE_DIR, TOURNAMENT_NAME, EXPORT_DIR
from core import Tournament
from persistence import ensure_dir


def export_overview(tournament: Tournament, stage_id: str, *, template_dir: str = TEMPLATE_DIR,
                    header: str = TOURNAMENT_NAME, export_dir: Path = EXPORT_DIR) -> Path:
    """Rendert eine HTML-Datei mit einer Übersicht über alle Gruppen des Turniers."""
    tournament_type = tournament.type.lower()
    export_path = Path(export_dir) / tournament_type
    ensure_dir(export_path)

    groups_data = []
    for group in tournament.stages[stage_id].groups:
        print(group.assigned_courts)
        groups_data.append({
            "name": group.name,
            "courts": group.assigned_courts or [],
            "teams": group.teams
        })

    env = Environment(
        loader=FileSystemLoader(Path(template_dir).absolute()),
        autoescape=True,
    )
    template = env.get_template("tournament_overview.html")

    rendered = template.render(
        tournament_name=header,
        tournament_type=tournament.type,
        groups=groups_data,
    )

    out_file = export_path / "Turnierübersicht.html"
    out_file.write_text(rendered, encoding="utf-8")
    print(f"✅ Turnierübersicht HTML geschrieben: {out_file.resolve()}")
    return out_file
