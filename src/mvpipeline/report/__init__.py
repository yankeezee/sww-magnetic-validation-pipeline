"""
Report module: формирование артефактов анализа.

Отвечает за:
    - запись общего CSV по всем CIF (all_structures.csv)

Публичный API:
    write_records_csv
"""

from .records import write_records_csv

__all__ = [
    "write_records_csv",
]
