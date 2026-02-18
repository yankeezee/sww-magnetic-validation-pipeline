from __future__ import annotations
import json
import shutil
from pathlib import Path
from ..types import StructureItem, ValidationResult


def write_validated(item: StructureItem, out_dir: Path) -> Path:
    dst = out_dir / "validated_structures" / item.rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(item.path, dst)
    return dst


def write_rejected(
    item: StructureItem, out_dir: Path, result: ValidationResult
) -> Path:
    dst = out_dir / "rejected_structures" / item.rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(item.path, dst)

    reason_path = dst.with_suffix(".reason.json")
    payload = {
        "structure_id": item.structure_id,
        "reason": result.rejection.reason if result.rejection else "unknown",
        "details": result.rejection.details if result.rejection else {},
    }
    reason_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return dst
