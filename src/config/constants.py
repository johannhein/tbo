from pathlib import Path

ASSETS_DIR: Path = Path("assets")
IMG_PATH: Path = ASSETS_DIR / "images/header.jpg"

DATA_DIR: Path = Path("data")
PICKLE_DIR = DATA_DIR / "pickle"
IMPORT_DIR: Path = DATA_DIR / "import"
TEMPLATE_DIR: Path = ASSETS_DIR / "templates"
EXPORT_DIR: Path = DATA_DIR / "export"
DB_PATH: Path = DATA_DIR / "tournament_db.db"

SQL_SCHEMA_PATH: Path = Path("src/config/schema.sql")

TOURNAMENT_NAME = "19. Travemünder Beach Open  07./ 08. August 2027"

HIGHLIGHT_COLOR = "#00ab17"

MAX_COURT_NUM = 16

TOURNAMENT_DAYS = [
    ("Damen", "Sonntag", "Damen", "[2, 3, 4, 5]"),
    ("Herren", "Sonntag", "Herren", "[1, 6, 7, 10, 11, 12, 13, 14]"),
    ("Quattro", "Sonntag", "Mixed", "[8, 9, 15, 16]"),
    ("Duo Mixed Hobby", "Samstag", "Mixed",
     "[5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]"),
    ("Duo Mixed Leistung", "Samstag", "Mixed", "[1, 2, 3, 4]"),
]

DEFAULT_TIEBREAK = 11
DEFAULT_POINTS = 15
DEFAULT_GROUP_SIZE = 4

MIN_DIFF = True
