from __future__ import annotations
from pymatgen.core import Structure
from ..types import Descriptors
from typing import Optional


def compute_basic_descriptors(
    struct: Structure, spacegroup: Optional[int]
) -> Descriptors:
    n_atoms = len(struct)
    vpa = struct.volume / n_atoms if n_atoms else 0.0
    dens = float(struct.density)
    formula = struct.composition.reduced_formula
    return Descriptors(
        n_atoms=n_atoms,
        density=dens,
        volume_per_atom=vpa,
        reduced_formula=formula,
        spacegroup=spacegroup,
    )
