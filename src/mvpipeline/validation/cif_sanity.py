from __future__ import annotations
from pymatgen.core import Structure


def sanity_ok(struct: Structure) -> bool:
    if len(struct) <= 0:
        return False
    # volume must be > 0
    if not (struct.volume and struct.volume > 0):
        return False
    return True
