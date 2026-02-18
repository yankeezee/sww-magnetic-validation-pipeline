from __future__ import annotations

from enum import Enum

MAGNETIC_ELEMENTS_DEFAULT = {"Fe", "Co", "Ni", "Mn", "Cr", "V"}


class ValidationStatus(str, Enum):
    VALIDATED = "validated"
    REJECTED = "rejected"


class GeometryQuality(str, Enum):
    OK = "ok"
    SUSPICIOUS = "suspicious"


class RejectionReason(str, Enum):
    CIF_PARSE_ERROR = "cif_parse_error"
    CIF_SANITY_ERROR = "cif_sanity_error"

    TOO_MANY_ATOMS = "too_many_atoms"
    PHYS_IMPOSSIBLE_DISTANCE = "physically_impossible_distance"
    UNREALISTIC_DENSITY = "unrealistic_density"
    NON_STANDARD_VPA = "non_standard_vpa"

    DUPLICATE = "duplicate"
    NOT_NOVEL = "not_novel"

    INTERNAL_ERROR = "internal_error"
