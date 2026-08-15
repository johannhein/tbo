from pathlib import Path
from typing import Union


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
        angelegt – entspricht ``mkdir -p``.
    exist_ok : bool, optional
        Wenn True (Standard) wird kein Fehler ausgelöst, wenn das Verzeichnis
        bereits existiert.

    """
    path = Path(folder).expanduser().resolve()

    path.mkdir(mode=0o777, parents=parents, exist_ok=exist_ok)

    return path