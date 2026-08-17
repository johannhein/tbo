from pathlib import Path
from typing import Union, List, Iterable


def ensure_dir(folder: Union[str, Path], *, parents: bool = True, exist_ok: bool = True,):
    """
    Lege den angegebenen Ordner an, falls er noch nicht existiert.

    Parameters
    ----------
    folder : str | pathlib.Path
        Der zu erstellende Pfad (kann ein String, ein Path‑Objekt oder ein
        beliebiges os‑Path‑Like‑Objekt sein).
    parents : bool, optional
        Wenn True (Standard) werden fehlende Eltern‑Verzeichnisse rekursiv
        angelegt – entspricht mkdir -p.
    exist_ok : bool, optional
        Wenn True (Standard) wird kein Fehler ausgelöst, wenn das Verzeichnis
        bereits existiert.

    """
    path = Path(folder).expanduser().resolve()

    path.mkdir(mode=0o777, parents=parents, exist_ok=exist_ok)

    return path


def list_files_with_suffix(folder: Union[str, Path], suffix: str, *, recursive: bool = False, 
                           case_insensitive: bool = True,  as_strings: bool = False,) -> List[Union[Path, str]]:
    """
    Durchsucht folder nach Dateien, deren Name mit suffix endet.

    Parameters
    ----------
    folder : str | Path
        Pfad zum zu durchsuchenden Verzeichnis.
    suffix : str
        Gesuchte Dateiendung (z. B. ".csv", ".txt" oder "json").
        Das führende „. ist optional – die Funktion fügt es bei Bedarf ein.
    recursive : bool, default=False
        Wenn True, wird das Verzeichnis **rekursiv** (also inklusive Unterordner)
        durchsucht. Ansonsten nur die direkte Ebene.
    case_insensitive : bool, default=True
        Ignoriert Groß‑/Kleinschreibung bei der Suffix-Prüfung.
        (Unter Windows ist das ohnehin der Standard, unter Linux nicht.)
    as_strings : bool, default=False
        Gibt entweder Path‑Objekte (False) oder deren string‑Repräsentation
        (True) zurück.
    """
    folder_path = Path(folder).expanduser().resolve()
    if not folder_path.is_dir():
        raise NotADirectoryError(f"'{folder_path}' ist kein gültiges Verzeichnis.")

    suffix = suffix if suffix.startswith(".") else f".{suffix}"

    # rglob liefert rekursiv, glob nur die aktuelle Ebene.
    iterator: Iterable[Path] = (
        folder_path.rglob(f"*{suffix}") if recursive else folder_path.glob(f"*{suffix}")
    )

    # case‑insensitive Vergleich
    if case_insensitive:
        suffix = suffix.lower()
        files = [
            p for p in iterator
            if p.is_file() and p.suffix.lower() == suffix
        ]
    else:
        files = [p for p in iterator if p.is_file() and p.suffix == suffix]

    files.sort()

    return [str(p) for p in files] if as_strings else files
