from pathlib import Path

DATA_FILE = Path("results.json")

IMG_PATH = Path("tbo/assets/header.jpg")

DATA_DIR = Path("tbo/data")
IMPORT_DIR = Path("tbo/import")

TOURNAMENT_NAME = "19. Travemünder Beach Open  07./ 08. August 2027"

# Hard‑coded Group‑Matches – kann später in JSON ausgelagert werden
GROUP_MATCHES = [
    (1, "09:45-10:00", 1, "A1", "A6", "A"),
    (1, "09:45-10:00", 2, "A2", "A5", "A"),
    # … (alle übrigen Zeilen) …
]