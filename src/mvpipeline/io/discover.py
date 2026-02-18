from __future__ import annotations
from pathlib import Path
from typing import List
from ..types import StructureItem


def discover_cifs(input_dir: Path) -> List[StructureItem]:
    files = sorted(input_dir.rglob("*.cif"))
    items: List[StructureItem] = []
    for f in files:
        rel = f.relative_to(input_dir)
        structure_id = str(rel).replace("\\", "/")
        items.append(StructureItem(structure_id=structure_id, path=f, rel_path=rel))
    return items
