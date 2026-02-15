# src/mvpipeline/validation/geometry_checks.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any, List

import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.local_env import CrystalNN


@dataclass(frozen=True)
class GeometryThresholds:
    """
    Пороги можно подобрать позже. Сейчас — безопасные дефолты для первичной фильтрации.
    """
    min_interatomic_distance: float = 1.0   # Å: грубый фильтр перекрытий
    min_volume_per_atom: float = 5.0        # Å^3/atom: слишком маленький объём на атом обычно подозрителен
    max_volume_per_atom: float = 60.0       # Å^3/atom: слишком большой объём на атом тоже подозрителен
    min_density: float = 0.5                # g/cm^3
    max_density: float = 30.0               # g/cm^3
    max_n_atoms: int = 500                  # чтобы не взрывать время/память на странных огромных ячейках


def basic_stats(struct: Structure) -> Dict[str, float]:
    """
    Базовые геометрические/физические величины, которые почти всегда нужны в отчёте.
    """
    n_atoms = len(struct)
    vol = float(struct.volume)
    vpa = float(vol / n_atoms) if n_atoms > 0 else float("nan")

    # pymatgen.Structure.density -> g/cm^3 (в большинстве версий pymatgen)
    try:
        density = float(struct.density)
    except Exception:
        density = float("nan")

    lattice = struct.lattice
    return {
        "n_atoms": float(n_atoms),
        "volume": vol,
        "volume_per_atom": vpa,
        "density": density,
        "a": float(lattice.a),
        "b": float(lattice.b),
        "c": float(lattice.c),
        "alpha": float(lattice.alpha),
        "beta": float(lattice.beta),
        "gamma": float(lattice.gamma),
    }


def min_distance(struct: Structure) -> float:
    """
    Минимальная межатомная дистанция в ячейке (учитывая PBC).
    Для n_atoms>~500 это может быть тяжело, но для ваших 200–1000 CIF нормально.
    """
    if len(struct) < 2:
        return float("inf")

    dm = struct.distance_matrix  # NxN
    # исключаем диагональ
    dm = dm + np.eye(dm.shape[0]) * 1e9
    return float(np.min(dm))


def check_lattice_sanity(struct: Structure, thr: GeometryThresholds) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Быстрые проверки: число атомов, объём/атом, плотность.
    """
    info = basic_stats(struct)

    n_atoms = int(info["n_atoms"])
    if n_atoms <= 0:
        return False, "empty_structure", info
    if n_atoms > thr.max_n_atoms:
        return False, "too_many_atoms", info

    vpa = info["volume_per_atom"]
    if not np.isfinite(vpa) or vpa < thr.min_volume_per_atom:
        return False, "too_small_volume_per_atom", info
    if vpa > thr.max_volume_per_atom:
        return False, "too_large_volume_per_atom", info

    dens = info["density"]
    if np.isfinite(dens):
        if dens < thr.min_density:
            return False, "too_low_density", info
        if dens > thr.max_density:
            return False, "too_high_density", info

    return True, None, info


def check_overlaps(struct: Structure, thr: GeometryThresholds) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Грубая проверка перекрытий: минимальная дистанция.
    """
    dmin = min_distance(struct)
    info = {"min_distance": dmin}

    if not np.isfinite(dmin):
        return False, "distance_nan", info
    if dmin < thr.min_interatomic_distance:
        return False, "overlap", info

    return True, None, info


def geometry_validate(struct: Structure, thr: GeometryThresholds) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Единая точка входа: возвращает (ok, reason, details).
    reason заполняется только если ok=False.
    """
    ok, reason, info1 = check_lattice_sanity(struct, thr)
    if not ok:
        return False, reason, info1

    ok, reason, info2 = check_overlaps(struct, thr)
    if not ok:
        details = {**info1, **info2}
        return False, reason, details

    # Объединяем детали успешных чеков
    details = {**info1, **info2}
    return True, None, details
