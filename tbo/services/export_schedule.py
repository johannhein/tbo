from __future__ import annotations
import pathlib
from jinja2 import Environment, FileSystemLoader

from core.models import Group, Match


def render_group_schedule_html(group: Group,
                         template_dir: str = "templates") -> pathlib.Path:
    """
    Rendert das Jinja2‑Template `schedule.html` mit den Daten aus `group`
    und schreibt das Ergebnis in `output_path`.
    """
    file_name = f"Spielplan_Gruppe_{group.name}.html"
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("schedule.html")

    rendered = template.render(
        group=group,
        matches=group.match_list
    )

    output_path = "tbo/export/" + file_name
    out_file = pathlib.Path(output_path)
    out_file.write_text(rendered, encoding="utf-8")
    print(f"✅ HTML‑Datei wurde geschrieben: {out_file.resolve()}")
    return out_file