# src/mvpipeline/pipeline/runner.py
from __future__ import annotations

"""
runner.py — главный файл, который запускает весь validation pipeline.

Это "оркестратор". Он ничего не проверяет сам, а вызывает другие модули
в правильном порядке.

Общий flow pipeline:

    1. Находим все CIF файлы (discover_cifs)
    2. Для каждого файла:
        - читаем CIF
        - sanity проверка
        - определяем spacegroup
        - считаем дескрипторы
        - проверяем геометрию
        - проверяем электронейтральность
        - проверяем новизну
        - проверяем дубликаты
        - проверяем магнитность
        - сохраняем validated или rejected
        - обновляем статистику

    3. После обработки всех структур:
        - считаем итоговые метрики
        - записываем validation_report.json
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from pymatgen.core import Structure

from ..analysis import compute_basic_descriptors, get_spacegroup_number
from ..dedup import SimilarityChecker
from ..io import discover_cifs, read_structure, write_rejected, write_validated
from ..novelty import is_novel
from ..utils import (
    PipelineConfig,
    Rejection,
    RejectionReason,
    ValidationResult,
    ValidationStatus,
)
from ..validation import (
    check_charge_neutrality,
    geometry_validate,
    has_magnetic_elements,
    sanity_ok,
)


# =============================================================================
# Класс для накопления статистики
# =============================================================================


@dataclass
class RunStats:
    """
    Этот класс хранит статистику по всем структурам.

    Мы постепенно обновляем эти значения во время работы pipeline,
    а в конце используем их для создания validation_report.json.
    """

    # сколько всего структур нашли
    total: int = 0

    # сколько приняли
    validated: int = 0

    # сколько отклонили
    rejected: int = 0

    # сколько валидных содержат магнитные элементы
    magnetic_count: int = 0

    # сколько валидных являются новыми
    novel_count: int = 0

    # плотности валидных структур (для среднего)
    densities: list[float] = field(default_factory=list)

    # объем на атом валидных структур (для среднего)
    vpas: list[float] = field(default_factory=list)

    # причины отклонения (словарь: причина -> сколько раз)
    rejection_reasons: Dict[str, int] = field(default_factory=dict)

    # строки для validated_progress.csv
    progress_rows: list[dict[str, Any]] = field(default_factory=list)

    def add_rejection_reason(self, reason: RejectionReason) -> None:
        """
        Увеличивает счетчик конкретной причины отклонения.

        Например:
            duplicate -> 15
            cif_parse_error -> 3
        """

        key = reason.value
        self.rejection_reasons[key] = self.rejection_reasons.get(key, 0) + 1


# =============================================================================
# Вспомогательная функция: загрузка train_reference.csv
# =============================================================================


def _load_train_reference(path: Optional[Path]) -> Optional[pd.DataFrame]:
    """
    Загружает train_reference.csv, если он существует.

    Этот файл нужен для проверки новизны структуры.
    """

    if path is None:
        return None

    if not path.exists():
        return None

    df = pd.read_csv(path)

    # приводим к строкам, чтобы сравнение работало корректно
    if "reduced_formula" in df.columns:
        df["reduced_formula"] = df["reduced_formula"].astype(str)

    if "spacegroup" in df.columns:
        df["spacegroup"] = df["spacegroup"].astype(str)

    return df


# =============================================================================
# Вспомогательная функция: безопасное среднее
# =============================================================================


def _avg(values: list[float]) -> float:
    """
    Возвращает среднее значение списка.

    Если список пустой — возвращает 0.
    """

    if not values:
        return 0.0

    return sum(values) / len(values)


# =============================================================================
# Главная функция pipeline
# =============================================================================


def run_validation(
    *,
    input_dir: Path,
    out_dir: Path,
    cfg: PipelineConfig,
    train_reference: Optional[Path] = None,
    model_name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Главная функция, которая запускает весь pipeline.

    input_dir:
        папка с CIF файлами

    out_dir:
        папка, куда сохраняем результаты

    cfg:
        конфигурация pipeline

    train_reference:
        CSV файл с train dataset (для novelty проверки)

    model_name:
        имя модели (если None — используем имя input_dir)
    """

    # создаем папку результатов
    out_dir.mkdir(parents=True, exist_ok=True)

    # находим все CIF файлы
    items = discover_cifs(input_dir)

    # загружаем train_reference.csv
    reference_df = _load_train_reference(train_reference)

    # создаем объект статистики
    stats = RunStats(total=len(items))

    # создаем checker дубликатов
    sim_checker = SimilarityChecker()

    # =========================================================================
    # Главный цикл — обрабатываем каждый CIF
    # =========================================================================

    for item in items:

        # ------------------------------------------------------------
        # 1. Читаем CIF
        # ------------------------------------------------------------

        try:
            struct: Structure = read_structure(item.path)

        except Exception as e:
            # если CIF не читается — отклоняем

            result = ValidationResult(
                status=ValidationStatus.REJECTED,
                rejection=Rejection(
                    reason=RejectionReason.CIF_PARSE_ERROR,
                    details={"error": str(e)},
                ),
            )

            write_rejected(item, out_dir, result)

            stats.rejected += 1
            stats.add_rejection_reason(RejectionReason.CIF_PARSE_ERROR)

            continue

        # ------------------------------------------------------------
        # 2. sanity проверка
        # ------------------------------------------------------------

        if not sanity_ok(struct):

            result = ValidationResult(
                status=ValidationStatus.REJECTED,
                rejection=Rejection(
                    reason=RejectionReason.CIF_SANITY_ERROR,
                    details={"error": "sanity_failed"},
                ),
            )

            write_rejected(item, out_dir, result)

            stats.rejected += 1
            stats.add_rejection_reason(RejectionReason.CIF_SANITY_ERROR)

            continue

        # ------------------------------------------------------------
        # 3. определяем spacegroup
        # ------------------------------------------------------------

        sg = get_spacegroup_number(struct, cfg.symprec)

        # ------------------------------------------------------------
        # 4. считаем дескрипторы
        # ------------------------------------------------------------

        desc = compute_basic_descriptors(struct, sg)

        # ------------------------------------------------------------
        # 5. проверяем геометрию
        # ------------------------------------------------------------

        geo = geometry_validate(struct, cfg)

        if geo.status == ValidationStatus.REJECTED:

            result = ValidationResult(
                status=ValidationStatus.REJECTED,
                descriptors=desc,
                rejection=Rejection(geo.reason, geo.details),
            )

            write_rejected(item, out_dir, result)

            stats.rejected += 1
            stats.add_rejection_reason(geo.reason)

            continue

        # ------------------------------------------------------------
        # 6. проверяем заряд
        # ------------------------------------------------------------

        charge = check_charge_neutrality(struct, cfg)

        if not charge.ok:

            result = ValidationResult(
                status=ValidationStatus.REJECTED,
                descriptors=desc,
                rejection=Rejection(charge.reason, charge.details),
            )

            write_rejected(item, out_dir, result)

            stats.rejected += 1
            stats.add_rejection_reason(charge.reason)

            continue

        # ------------------------------------------------------------
        # 7. проверяем новизну
        # ------------------------------------------------------------

        novel = is_novel(struct, reference_df) if reference_df is not None else None

        # ------------------------------------------------------------
        # 8. проверяем дубликаты
        # ------------------------------------------------------------

        formula = desc.reduced_formula
        sg_key = desc.spacegroup or -1

        if sim_checker.is_duplicate(struct, formula, sg_key):

            result = ValidationResult(
                status=ValidationStatus.REJECTED,
                descriptors=desc,
                rejection=Rejection(RejectionReason.DUPLICATE),
            )

            write_rejected(item, out_dir, result)

            stats.rejected += 1
            stats.add_rejection_reason(RejectionReason.DUPLICATE)

            continue

        sim_checker.add_to_accepted(struct, formula, sg_key)

        # ------------------------------------------------------------
        # 9. проверяем магнитность
        # ------------------------------------------------------------

        magnetic = has_magnetic_elements(struct, cfg)

        # ------------------------------------------------------------
        # 10. структура валидна — сохраняем
        # ------------------------------------------------------------

        result = ValidationResult(
            status=ValidationStatus.VALIDATED,
            descriptors=desc,
            is_magnetic=magnetic,
            is_novel=novel,
        )

        write_validated(item, out_dir)

        stats.validated += 1

        if magnetic:
            stats.magnetic_count += 1

        if novel:
            stats.novel_count += 1

        stats.densities.append(desc.density)
        stats.vpas.append(desc.volume_per_atom)

    # =========================================================================
    # Формируем итоговый отчет
    # =========================================================================

    report = {
        "model_name": model_name or input_dir.name,
        "n_total": stats.total,
        "n_validated": stats.validated,
        "n_rejected": stats.rejected,
        "validity_ratio": stats.validated / stats.total if stats.total else 0,
        "magnetic_ratio": (
            stats.magnetic_count / stats.validated if stats.validated else 0
        ),
        "novelty_ratio": stats.novel_count / stats.validated if stats.validated else 0,
        "duplicate_ratio": (
            stats.rejection_reasons.get("duplicate", 0) / stats.total
            if stats.total
            else 0
        ),
        "avg_density": _avg(stats.densities),
        "avg_volume_per_atom": _avg(stats.vpas),
        "rejection_reasons": stats.rejection_reasons,
    }

    report_path = out_dir / "validation_report.json"

    report_path.write_text(json.dumps(report, indent=2))

    return report
