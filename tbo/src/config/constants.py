from pathlib import Path

ASSETS_DIR: Path = Path("tbo/assets")
IMG_PATH: Path = ASSETS_DIR / "images/header.jpg"

DATA_DIR: Path = Path("tbo/data")
PICKLE_DIR = DATA_DIR / "pickle"
IMPORT_DIR: Path = DATA_DIR /"import"
TEMPLATE_DIR: Path = ASSETS_DIR / "templates"
EXPORT_DIR: Path = DATA_DIR / "export"

TOURNAMENT_NAME = "19. Travemünder Beach Open  07./ 08. August 2027"

HIGHLIGHT_COLOR = "#00ab17"

# Hard‑coded Group‑Matches –kann später in JSON ausgelagert werden
GROUP_MATCHES = [
    (1, "09:45-10:00", 1, "A1", "A6", "A"),
    (1, "09:45-10:00", 2, "A2", "A5", "A"),
    # … (alle übrigen Zeilen) …
]