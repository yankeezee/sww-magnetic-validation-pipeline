from __future__ import annotations
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Tuple, Any
import numpy as np
from pymatgen.core import Structure

@dataclass(frozen=True)
class GeometryThresholds:
    # Из секции geometry
    dist_impossible: float    # d_min_reject
    dist_suspicious: float    # d_max_suspicious
    
    # Из секции geometry (объемы)
    vpa_min: float            # vol_min
    vpa_max: float            # vol_max
    
    # Из секции physical_properties
    density_min: float        # min_density
    density_max: float        # max_density

    # Из секции system_limits
    max_atoms: int            # max_n_atoms

    @classmethod
    def from_yaml(cls, path: str | Path) -> GeometryThresholds:
        with open(path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        
        geo = cfg.get('geometry', {})
        phys = cfg.get('physical_properties', {})
        sys_lim = cfg.get('system_limits', {})

        return cls(
            dist_impossible=geo.get('d_min_reject', 0.7),
            dist_suspicious=geo.get('d_max_suspicious', 1.2),
            vpa_min=geo.get('vol_min', 8.0),
            vpa_max=geo.get('vol_max', 40.0),
            density_min=phys.get('min_density', 0.5),
            density_max=phys.get('max_density', 30.0),
            max_atoms=sys_lim.get('max_n_atoms', 500)
        )

def geometry_validate(struct: Structure, thr: GeometryThresholds) -> Tuple[str, Dict[str, Any]]:
    """
    Валидация на основе загруженных порогов.
    """
    n_atoms = len(struct)
    vol = struct.volume
    vpa = vol / n_atoms if n_atoms > 0 else 0
    dens = struct.density
    
    # Расчет dmin
    dm = struct.distance_matrix
    np.fill_diagonal(dm, 1e9)
    dmin = float(np.min(dm))

    info = {
        "n_atoms": n_atoms,
        "volume_per_atom": round(vpa, 3),
        "density": round(dens, 3),
        "min_distance": round(dmin, 3),
        "formula": struct.composition.reduced_formula,
        "spacegroup": struct.get_space_group_info()[1]
    }

    # 1. Системные ограничения (max_n_atoms)
    if n_atoms > thr.max_atoms:
        return "rejected", {**info, "reason": "too_many_atoms"}

    # 2. Валидация расстояний (d_min_reject)
    if dmin < thr.dist_impossible:
        return "rejected", {**info, "reason": "physically_impossible_distance"}
    
    # 3. Плотность (min_density / max_density)
    if dens < thr.density_min or dens > thr.density_max:
        return "rejected", {**info, "reason": "unrealistic_density"}
    
    # 4. Проверка на "Подозрительно" (Suspicious)
    # Если расстояние в диапазоне между d_min_reject и d_max_suspicious
    if dmin < thr.dist_suspicious:
        return "suspicious", {**info, "reason": "low_interatomic_distance"}
    
    # Если объем вне рамок "нормы" (vol_min - vol_max)
    if vpa < thr.vpa_min or vpa > thr.vpa_max:
        return "suspicious", {**info, "reason": "non_standard_vpa"}

    return "validated", info