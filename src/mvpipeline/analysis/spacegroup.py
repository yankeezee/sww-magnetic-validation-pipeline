from __future__ import annotations
from typing import Optional
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer


def get_spacegroup_number(struct: Structure, symprec: float) -> Optional[int]:
    try:
        sga = SpacegroupAnalyzer(struct, symprec=symprec)
        return int(sga.get_space_group_number())
    except Exception:
        return None
