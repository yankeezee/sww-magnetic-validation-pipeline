from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import RejectionReason, ValidationStatus


@dataclass(frozen=True)
class StructureItem:
    structure_id: str
    path: Path
    rel_path: Path


@dataclass(frozen=True)
class Descriptors:
    n_atoms: int
    density: float
    volume_per_atom: float
    reduced_formula: str
    spacegroup: int | None


@dataclass(frozen=True)
class Rejection:
    reason: RejectionReason
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationResult:
    status: ValidationStatus
    descriptors: Descriptors | None = None
    rejection: Rejection | None = None

    is_magnetic: bool = False
    is_novel: bool | None = None
    is_duplicate: bool = False
    is_suspicious: bool = False
