import json
import shutil
import pandas as pd
from pathlib import Path
import typer
from rich.progress import track
from rich import print
from pymatgen.core import Structure

from mvpipeline.validation.geometry_checks import geometry_validate, GeometryThresholds
from mvpipeline.validation.chemistry import has_magnetic_elements
from mvpipeline.validation.duplicates import SimilarityChecker, is_novel
from mvpipeline.validation.geometry_checks import GeometryThresholds, geometry_validate

app = typer.Typer()

@app.command()
def validate(
    input_dir: Path = typer.Option(..., help="Folder with CIF files"),
    out_dir: Path = typer.Option(..., help="Output folder"),
    train_reference: Path = typer.Option(None, help="CSV with train references"),
):
    out_dir.mkdir(parents=True, exist_ok=True)
    valid_dir = out_dir / "validated_structures"
    reject_dir = out_dir / "rejected_structures"
    
    ref_df = pd.read_csv(train_reference) if train_reference and train_reference.exists() else None
    
    cif_files = list(input_dir.rglob("*.cif"))
    config_path = Path("src/mvpipeline/config/thresholds.yaml")
    thr = GeometryThresholds.from_yaml(config_path)
    sim_checker = SimilarityChecker()
    
    # Список для формирования csv_progress
    progress_records = []
    
    results = []
    stats = {"total": len(cif_files), "validated": 0, "rejected": 0, "magnetic_count": 0, "novel_count": 0}
    reasons_count = {}
    valid_densities = []
    valid_vpas = []

    for cif_path in track(cif_files, description="Processing..."):
        rel_path = cif_path.relative_to(input_dir)
        status = "validated"
        info = {}

        try:
            struct = Structure.from_file(cif_path)
            formula = struct.composition.reduced_formula
            sg_number = struct.get_space_group_info()[1]
            
            # 1. Геометрия
            # Затем используем как обычно в цикле
            status, info = geometry_validate(struct, thr)
            # Дополним инфо для логов
            info["formula"] = formula
            info["spacegroup"] = sg_number
            
            # 2. Если геометрия ОК, проверяем на новизну (по референсу)
            if status != "rejected":
                if not is_novel(struct, ref_df):
                    status, info["reason"] = "rejected", "not_novel"
                
                # 3. Проверка на дубликаты (внутри текущего запуска)
                # Теперь передаем формулу и SG для быстрого поиска по бакетам
                elif sim_checker.is_duplicate(struct, formula, sg_number):
                    status, info["reason"] = "rejected", "duplicate"
            
            if status != "rejected":
                # Добавляем в бакеты для последующих сравнений
                sim_checker.add_to_accepted(struct, formula, sg_number)
                
                # Добавляем запись в прогресс-лист (валидные + подозрительные)
                progress_records.append({
                    "id": str(rel_path).replace("\\", "/"),
                    "reduced_formula": formula,
                    "spacegroup": sg_number
                })
                
                # Магнитные свойства
                info["is_magnetic"] = has_magnetic_elements(struct)
                if info["is_magnetic"]: stats["magnetic_count"] += 1
                stats["novel_count"] += 1
                valid_densities.append(info["density"])
                valid_vpas.append(info["volume_per_atom"])
            
        except Exception as e:
            status, info = "rejected", {"reason": "cif_parse_error", "details": str(e)}

        # Сохранение файлов
        target_folder = valid_dir if status != "rejected" else reject_dir
        target_path = target_folder / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(cif_path, target_path)

        if status == "rejected":
            reason_file = target_path.with_suffix(".reason.json")
            reason_data = {"structure_id": str(rel_path), "reason": info.get("reason"), "details": info}
            reason_file.write_text(json.dumps(reason_data, indent=2))
            
            stats["rejected"] += 1
            r = info.get("reason", "unknown")
            reasons_count[r] = reasons_count.get(r, 0) + 1
        else:
            stats["validated"] += 1

    # 1. Сохраняем csv_progress (только принятые структуры)
    if progress_records:
        progress_df = pd.DataFrame(progress_records)
        progress_path = out_dir / "validated_progress.csv"
        progress_df.to_csv(progress_path, index=False)
        print(f"Прогресс-файл сохранен: [bold blue]{progress_path}[/bold blue]")

    # 2. Сохраняем финальный JSON отчет
    report = {
        "model_name": input_dir.name,
        "n_total": stats["total"],
        "n_validated": stats["validated"],
        "n_rejected": stats["rejected"],
        "validity_ratio": round(stats["validated"] / stats["total"], 2) if stats["total"] else 0,
        "magnetic_ratio": round(stats["magnetic_count"] / stats["validated"], 2) if stats["validated"] else 0,
        "novelty_ratio": round(stats["novel_count"] / stats["validated"], 2) if stats["validated"] else 0,
        "duplicate_ratio": round(reasons_count.get("duplicate", 0) / stats["total"], 2) if stats["total"] else 0,
        "avg_density": round(sum(valid_densities)/len(valid_densities), 2) if valid_densities else 0,
        "avg_volume_per_atom": round(sum(valid_vpas)/len(valid_vpas), 2) if valid_vpas else 0,
        "rejection_reasons": reasons_count
    }

    (out_dir / "validation_report.json").write_text(json.dumps(report, indent=2))
    print(f"[bold green]Валидация завершена![/bold green] Успешно: {stats['validated']}")

if __name__ == "__main__":
    app()