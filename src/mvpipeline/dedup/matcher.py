from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Structure


class SimilarityChecker:
    def __init__(self):
        # Допуски можно подкрутить под ваши нужды
        self.matcher = StructureMatcher(ltol=0.2, stol=0.3, angle_tol=5)
        # Группируем структуры по бакетам: {(formula, sg): [list_of_structures]}
        self._buckets = {}

    def is_duplicate(self, struct: Structure, formula: str, sg: int) -> bool:
        """
        Сравнивает структуру только с теми, у кого такая же формула и SG.
        """
        key = (formula, sg)

        # Если такого сочетания еще не было, это точно не дубликат
        if key not in self._buckets:
            return False

        # Сравниваем только внутри бакета (ТЗ: сравнение по формуле и SG)
        for existing in self._buckets[key]:
            if self.matcher.fit(struct, existing):
                return True
        return False

    def add_to_accepted(self, struct: Structure, formula: str, sg: int):
        """Добавляет структуру в соответствующий бакет."""
        key = (formula, sg)
        if key not in self._buckets:
            self._buckets[key] = []
        self._buckets[key].append(struct)
