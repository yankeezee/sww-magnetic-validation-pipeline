from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any
import numpy as np
from pymatgen.core import Structure

@dataclass(frozen=True)
class GeometryThresholds:
    """
    Пороги из ТЗ (PDF). 
    Программист 1 позже может вынести это в загрузку из YAML.
    """
    # Расстояния
    dist_impossible: float = 0.7      # < 0.7 Å — физически невозможно (Reject)
    dist_overlap: float = 1.0         # < 1.0 Å — почти всегда перекрытие (Reject)
    dist_suspicious: float = 1.2      # < 1.2 Å — подозрительно (Suspicious)
    
    # Объемы (Å³/atom)
    vpa_too_small: float = 5.0        # < 5 — вырожденная решетка (Reject)
    vpa_min: float = 8.0              # 8-40 — норма (PDF стр. 3)
    vpa_max: float = 40.0             
    vpa_impossible: float = 80.0      # > 80 — нестабильная (Reject)

    # Плотность (g/cm³)
    density_min: float = 0.5          # < 0.5 — нереалистично
    density_max: float = 30.0         # > 30 — нереалистично


def min_distance(struct: Structure) -> float:
    """Расчет мин. расстояния с учетом периодических условий (PBC)."""
    if len(struct) < 2: return float("inf")
    # distance_matrix в pymatgen уже учитывает PBC
    dm = struct.distance_matrix
    dm = dm + np.eye(dm.shape[0]) * 1e9
    return float(np.min(dm))

def geometry_validate(struct: Structure, thr: GeometryThresholds) -> Tuple[str, Dict[str, Any]]:
    """
    Основная логика валидации 1-го дня.
    Возвращает: (status, info)
    Status: 'validated', 'rejected', 'suspicious'
    """
    n_atoms = len(struct)
    vol = float(struct.volume)
    vpa = vol / n_atoms if n_atoms > 0 else 0
    dens = float(struct.density)
    dmin = min_distance(struct)

    info = {
        "n_atoms": n_atoms,
        "volume_per_atom": round(vpa, 3),
        "density": round(dens, 3),
        "min_distance": round(dmin, 3),
        "formula": struct.composition.reduced_formula
    }

    # 1. Проверка на пустую структуру
    if n_atoms == 0:
        return "rejected", {**info, "reason": "empty_structure"}

    # 2. Валидация расстояний (PDF стр. 1)
    if dmin < thr.dist_impossible:
        return "rejected", {**info, "reason": f"physically_impossible_distance (<{thr.dist_impossible})"}
    if dmin < thr.dist_overlap:
        return "rejected", {**info, "reason": f"atomic_overlap (<{thr.dist_overlap})"}
    
    # 3. Валидация объема (PDF стр. 2)
    if vpa < thr.vpa_too_small:
        return "rejected", {**info, "reason": "degenerate_lattice_volume"}
    if vpa > thr.vpa_impossible:
        return "rejected", {**info, "reason": "too_large_unstable_volume"}

    # 4. Категория Suspicious (Подозрительно)
    if dmin < thr.dist_suspicious:
        return "suspicious", {**info, "reason": "low_interatomic_distance"}
    if vpa < thr.vpa_min or vpa > thr.vpa_max:
        return "suspicious", {**info, "reason": "non_standard_vpa"}

    return "validated", info