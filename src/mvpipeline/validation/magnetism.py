from pymatgen.core import Structure

MAGNETIC_ELEMENTS = {"Fe", "Co", "Ni", "Mn", "Cr", "V"}

def has_magnetic_elements(struct: Structure) -> bool:
    """Проверяет, содержит ли структура элементы из списка магнитных."""
    elements = {site.specie.symbol for site in struct}
    return not elements.isdisjoint(MAGNETIC_ELEMENTS)