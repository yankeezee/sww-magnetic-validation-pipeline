from pymatgen.core import Structure
from ..config import PipelineConfig


def has_magnetic_elements(struct: Structure, config: PipelineConfig) -> bool:
    """Проверяет, содержит ли структура элементы из списка магнитных."""
    elements = {site.specie.symbol for site in struct}
    return not elements.isdisjoint(config.magnetic_elements)
