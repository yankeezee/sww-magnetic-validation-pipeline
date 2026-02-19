from __future__ import annotations

"""
records.py — формирование “общей таблицы” по всем CIF.

Задача:
    - собрать все результаты в один CSV, где одна строка = один CIF
    - сохранить поля, нужные для дальнейшего анализа
    - не терять детали (кладём details_json)

Публичный API:
    write_records_csv
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# Единый порядок колонок (чтобы CSV был стабильный и удобный)
_COLUMNS = [
    "structure_id",
    "input_path",
    "status",
    "rejection_reason",
    "is_suspicious",
    "is_duplicate",
    "is_novel",
    "is_magnetic",
    "n_atoms",
    "density",
    "volume_per_atom",
    "min_distance",
    "reduced_formula",
    "spacegroup",
    "charge_solution_json",
    "details_json",
]


def _normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Приводит record к стабильному виду:
      - гарантируем наличие всех колонок
      - лишние поля оставляем (pandas их тоже запишет), но базовые фиксируем
    """
    out: Dict[str, Any] = {}
    for col in _COLUMNS:
        out[col] = rec.get(col, "")

    # если появились новые поля — тоже добавим, чтобы ничего не потерять
    for k, v in rec.items():
        if k not in out:
            out[k] = v

    return out


def write_records_csv(out_dir: Path, records: List[Dict[str, Any]]) -> Optional[Path]:
    """
    Записывает общий CSV со всеми структурами.

    Путь:
        <out_dir>/all_structures.csv

    Возвращает:
        Path до CSV или None, если records пустой.
    """
    if not records:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)

    normalized = [_normalize_record(r) for r in records]
    df = pd.DataFrame(normalized)

    # Пытаемся сохранить базовый порядок колонок, но не ломаемся, если есть новые.
    cols = [c for c in _COLUMNS if c in df.columns] + [
        c for c in df.columns if c not in _COLUMNS
    ]
    df = df[cols]

    path = out_dir / "all_structures.csv"
    df.to_csv(path, index=False)

    return path
