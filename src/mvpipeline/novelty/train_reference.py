import pandas as pd
from pymatgen.core import Structure


def is_novel(struct: Structure, reference_df: pd.DataFrame) -> bool:
    """Проверяет новизну относительно train_reference.csv."""
    if reference_df is None or reference_df.empty:
        return True

    formula = struct.composition.reduced_formula
    sg_number = struct.get_space_group_info()[1]

    # Ищем совпадение по формуле и spacegroup
    match = reference_df[
        (reference_df["reduced_formula"] == formula)
        & (reference_df["spacegroup"].astype(str) == str(sg_number))
    ]
    return match.empty
