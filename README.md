# magnetic-validation-pipeline

CPU validation pipeline for generated crystal structures  
(MatterGen / Con-CDVAE).

---

## Описание

Этот репозиторий предназначен для автоматической проверки CIF-файлов,
сгенерированных генеративными моделями.

Pipeline выполняет:

- Проверку корректности CIF
- Проверку межатомных расстояний
- Проверку charge neutrality
- Расчёт базовых физических дескрипторов (density, volume per atom, number of atoms)
- Проверку наличия магнитных элементов
- Удаление дубликатов
- Проверку новизны относительно train-dataset
- Формирование итогового отчёта

---

## 1. Установка

Создание окружения:

conda env create -f environment.yml

Активация окружения:

conda activate mvpipeline

Установка проекта:

pip install -e .

---

## 2. Структура данных

Ожидаемая структура проекта:

samples/
    mattergen_cifs/        # CIF-файлы MatterGen
    concdvae_cifs/         # CIF-файлы Con-CDVAE

train_reference.csv        # Данные train-набора для проверки новизны

---

## 3. Формат train_reference.csv

Минимально обязательные столбцы:

| column          | описание                           |
|-----------------|------------------------------------|
| id              | уникальный идентификатор структуры |
| reduced_formula | приведённая химическая формула     |
| spacegroup      | (опционально) номер или символ SG  |

Пример:

id,reduced_formula,spacegroup
mp-1234,Fe2O3,167
mp-5678,NiO,225

---

## 4. Запуск валидации

Пример запуска:

mvp validate \
  --input-dir samples/mattergen_cifs \
  --out-dir outputs/mattergen \
  --train-reference train_reference.csv

---

## 5. Ожидаемый результат

После запуска создаётся:

outputs/
    mattergen/
        validation_report.json
        validated_structures/
        rejected_structures/

---

## 6. Формат validation_report.json

Пример структуры отчёта:

{
  "model_name": "mattergen",
  "n_total": 1000,
  "n_validated": 820,
  "n_rejected": 180,
  "validity_ratio": 0.82,
  "magnetic_ratio": 0.47,
  "novelty_ratio": 0.63,
  "duplicate_ratio": 0.12,
  "avg_density": 5.34,
  "avg_volume_per_atom": 13.2,
  "rejection_reasons": {
    "cif_parse_error": 10,
    "overlap": 95,
    "charge_imbalance": 50,
    "duplicate": 25
  }
}

---

## 7. Правила разработки

- Использовать единое окружение
- Не менять формат отчёта без обсуждения
- Логировать все причины отклонения структуры
- Все новые метрики добавлять в validation_report.json
- Не выполнять ручную фильтрацию структур
- Код писать модульно (validation / evaluation / utils)

---

## 8. Цель проекта

Создать воспроизводимый validation pipeline,
который можно применять к любому генератору кристаллических структур
и использовать для корректного сравнения моделей.
