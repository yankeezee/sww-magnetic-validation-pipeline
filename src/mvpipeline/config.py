from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set
import yaml

from .constants import MAGNETIC_ELEMENTS_DEFAULT


@dataclass(frozen=True)
class DedupConfig:
    ltol: float = 0.2
    stol: float = 0.3
    angle_tol: float = 5.0


@dataclass(frozen=True)
class PipelineConfig:
    # geometry
    d_min_reject: float = 0.7
    d_max_suspicious: float = 1.2
    vpa_min: float = 8.0
    vpa_max: float = 40.0

    # physical
    density_min: float = 0.5
    density_max: float = 30.0

    # system
    max_n_atoms: int = 500

    # magnetism
    magnetic_elements: Set[str] = frozenset(MAGNETIC_ELEMENTS_DEFAULT)

    # behavior flags
    reject_suspicious: bool = False  # if True: suspicious -> rejected
    reject_non_novel: bool = False  # if True: not novel -> rejected (optional)

    # dedup config
    dedup: DedupConfig = DedupConfig()


def load_config(path: Optional[str | Path]) -> PipelineConfig:
    if not path:
        return PipelineConfig()

    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    geo = cfg.get("geometry", {})
    phys = cfg.get("physical_properties", {})
    sys_lim = cfg.get("system_limits", {})
    ded = cfg.get("dedup", {})
    mag = cfg.get("magnetism", {})

    return PipelineConfig(
        d_min_reject=float(geo.get("d_min_reject", 0.7)),
        d_max_suspicious=float(geo.get("d_max_suspicious", 1.2)),
        vpa_min=float(geo.get("vol_min", 8.0)),
        vpa_max=float(geo.get("vol_max", 40.0)),
        density_min=float(phys.get("min_density", 0.5)),
        density_max=float(phys.get("max_density", 30.0)),
        max_n_atoms=int(sys_lim.get("max_n_atoms", 500)),
        magnetic_elements=frozenset(
            mag.get("elements", list(MAGNETIC_ELEMENTS_DEFAULT))
        ),
        reject_suspicious=bool(cfg.get("reject_suspicious", False)),
        reject_non_novel=bool(cfg.get("reject_non_novel", False)),
        dedup=DedupConfig(
            ltol=float(ded.get("ltol", 0.2)),
            stol=float(ded.get("stol", 0.3)),
            angle_tol=float(ded.get("angle_tol", 5.0)),
        ),
    )
