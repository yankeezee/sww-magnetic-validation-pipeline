from __future__ import annotations

import pandas as pd
from pymatgen.core import Structure


def is_novel(struct: Structure, reference_df: pd.DataFrame) -> bool:
    """
    Проверяет, является ли структура новой относительно train_reference.csv.

    Структура считается НЕ новой (not novel), если в train_reference.csv уже
    существует структура с той же:
        - reduced_formula
        - spacegroup

    Это используется для оценки способности генеративной модели создавать
    новые структуры, а не просто воспроизводить train dataset.

    Почему используется именно (formula, spacegroup):
        reduced_formula
            Нормализованный химический состав (например Fe4O6 → Fe2O3)

        spacegroup
            Определяет симметрию структуры. Одинаковая формула может иметь
            разные структуры, поэтому spacegroup необходим для различения.

    Пример:

        train_reference.csv:
            Fe2O3,167

        generated:
            Fe2O3,167  → not novel
            Fe2O3,62   → novel
            NiO,225    → novel

    Parameters
    ----------
    struct : Structure
        Структура pymatgen, которую нужно проверить.

    reference_df : pd.DataFrame
        DataFrame, загруженный из train_reference.csv.
        Должен содержать столбцы:
            - reduced_formula
            - spacegroup

        Если None или пустой → все структуры считаются новыми.

    Returns
    -------
    bool
        True  → структура новая (novel)
        False → структура уже есть в train dataset (not novel)
    """

    # Если reference dataset не предоставлен — считаем всё новым
    if reference_df is None or reference_df.empty:
        return True

    # Получаем нормализованную формулу
    formula = struct.composition.reduced_formula

    # Получаем номер spacegroup
    sg_number = struct.get_space_group_info()[1]

    # Ищем совпадение в reference dataset
    match = reference_df[
        (reference_df["reduced_formula"] == formula)
        & (reference_df["spacegroup"].astype(str) == str(sg_number))
    ]

    # Если совпадений нет → структура новая
    return match.empty
