from __future__ import annotations
from pathlib import Path
from pymatgen.core import Structure


def read_structure(path: Path) -> Structure:
    return Structure.from_file(path)
