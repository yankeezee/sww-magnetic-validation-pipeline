from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
from pymatgen.core import Structure

from ..config import PipelineConfig
from ..constants import RejectionReason, ValidationStatus


@dataclass(frozen=True)
class GeometryOutcome:
    status: ValidationStatus
    is_suspicious: bool
    reason: RejectionReason | None
    details: dict[str, Any]


def geometry_validate(struct: Structure, cfg: PipelineConfig) -> GeometryOutcome:
    n_atoms = len(struct)
    if n_atoms > cfg.max_n_atoms:
        return GeometryOutcome(
            status=ValidationStatus.REJECTED,
            is_suspicious=False,
            reason=RejectionReason.TOO_MANY_ATOMS,
            details={"n_atoms": n_atoms, "max_n_atoms": cfg.max_n_atoms},
        )

    dens = float(struct.density)
    vpa = struct.volume / n_atoms if n_atoms else 0.0

    dm = struct.distance_matrix
    np.fill_diagonal(dm, 1e9)
    dmin = float(np.min(dm))

    details = {
        "n_atoms": n_atoms,
        "density": round(dens, 6),
        "volume_per_atom": round(vpa, 6),
        "min_distance": round(dmin, 6),
    }

    if dmin < cfg.d_min_reject:
        return GeometryOutcome(
            status=ValidationStatus.REJECTED,
            is_suspicious=False,
            reason=RejectionReason.PHYS_IMPOSSIBLE_DISTANCE,
            details={**details, "d_min_reject": cfg.d_min_reject},
        )

    if dens < cfg.density_min or dens > cfg.density_max:
        return GeometryOutcome(
            status=ValidationStatus.REJECTED,
            is_suspicious=False,
            reason=RejectionReason.UNREALISTIC_DENSITY,
            details={
                **details,
                "density_min": cfg.density_min,
                "density_max": cfg.density_max,
            },
        )

    suspicious = (
        (dmin < cfg.d_max_suspicious) or (vpa < cfg.vpa_min) or (vpa > cfg.vpa_max)
    )

    # Причину suspicious можно положить в details
    if suspicious and dmin < cfg.d_max_suspicious:
        details["suspicious_reason"] = "low_interatomic_distance"
    elif suspicious:
        details["suspicious_reason"] = "non_standard_vpa"

    return GeometryOutcome(
        status=ValidationStatus.VALIDATED,
        is_suspicious=suspicious,
        reason=None,
        details=details,
    )
