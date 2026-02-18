import pandas as pd
from pathlib import Path
from pymatgen.core import Structure
from tqdm import tqdm


def generate_reference_csv(root_dir: str, output_csv: str):
    root = Path(root_dir)
    data = []

    # Рекурсивно ищем все .cif файлы
    cif_files = list(root.rglob("*.cif"))
    print(f"Найдено файлов для обработки: {len(cif_files)}")

    for cif_path in tqdm(cif_files, desc="Парсинг структур"):
        try:
            # Читаем структуру
            struct = Structure.from_file(cif_path)

            # 1. Формируем ID.
            # Используем относительный путь, чтобы ID были уникальными,
            # если файлы с одинаковым именем лежат в разных подпапках.
            # Пример: mattergen_cifs/probe100.../structure_1.cif
            relative_id = str(cif_path.relative_to(root)).replace("\\", "/")

            # 2. Получаем формулу
            formula = struct.composition.reduced_formula

            # 3. Получаем номер пространственной группы (spacegroup)
            # симметрия вычисляется на лету
            sg_info = struct.get_space_group_info()
            sg_number = sg_info[1]

            data.append(
                {"id": relative_id, "reduced_formula": formula, "spacegroup": sg_number}
            )

        except Exception as e:
            # Если файл битый или не парсится - пропускаем
            continue

    # Создаем DataFrame
    df = pd.DataFrame(data)

    if not df.empty:
        # Сохраняем ровно 3 колонки, как в ТЗ
        df.to_csv(output_csv, index=False, encoding="utf-8")
        print(f"\nУспешно сохранено в {output_csv}")
        print(f"Пример данных:\n{df.head(3)}")
    else:
        print("Файлы не найдены или не удалось прочитать ни одного CIF.")


if __name__ == "__main__":
    # Запускаем сборку из папки samples
    generate_reference_csv(root_dir="samples", output_csv="train_reference.csv")
