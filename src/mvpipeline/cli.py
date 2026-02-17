import json
import shutil
from pathlib import Path
from typing import Dict, Any

import typer
from rich.progress import track
from rich import print
from pymatgen.core import Structure

# Импортируем твою логику
from mvpipeline.validation.geometry_checks import geometry_validate, GeometryThresholds

app = typer.Typer()

@app.command()
def validate(
    input_dir: Path = typer.Option(Path("samples"), help="Folder with CIF files"),
    out_dir: Path = typer.Option(Path("outputs"), help="Output folder"),
    train_reference: Path = typer.Option(None, help="CSV with train references (Day 2)"),
):
    """Пайплайн валидации кристаллических структур."""
    
    # Создаем структуру папок (ТЗ PDF 2, стр. 5)
    out_dir.mkdir(parents=True, exist_ok=True)
    valid_dir = out_dir / "validated_structures"
    reject_dir = out_dir / "rejected_structures"
    valid_dir.mkdir(exist_ok=True)
    reject_dir.mkdir(exist_ok=True)

    cif_files = list(input_dir.rglob("*.cif"))
    print(f"Найдено [bold blue]{len(cif_files)}[/bold blue] CIF файлов.")

    results = []
    stats = {"validated": 0, "rejected": 0, "suspicious": 0, "errors": 0}
    reasons_count = {}

    thr = GeometryThresholds()

    for cif_path in track(cif_files, description="Validating..."):
        # ID как относительный путь (ТЗ PDF 2, стр. 1)
        rel_id = str(cif_path.relative_to(input_dir))
        
        try:
            struct = Structure.from_file(cif_path)
            status, info = geometry_validate(struct, thr)
        except Exception as e:
            status, info = "rejected", {"reason": f"cif_parse_error: {str(e)}"}
            stats["errors"] += 1

        # Собираем данные для отчета
        entry = {
            "id": rel_id,
            "file_name": cif_path.name,
            "status": status,
            **info
        }
        results.append(entry)
        stats[status] += 1
        
        # Считаем причины отказов для статистики
        if status == "rejected":
            r = info.get("reason", "unknown")
            reasons_count[r] = reasons_count.get(r, 0) + 1

        # Копируем файлы (чтобы Химик мог их посмотреть)
        target_folder = valid_dir if status != "rejected" else reject_dir
        shutil.copy(cif_path, target_folder / cif_path.name)

    # Формируем финальный отчет (ТЗ PDF 2, стр. 5)
    report = {
        "model_name": input_dir.name,
        "n_total": len(cif_files),
        "n_validated": stats["validated"],
        "n_rejected": stats["rejected"],
        "n_suspicious": stats["suspicious"],
        "validity_ratio": round(stats["validated"] / len(cif_files), 2) if cif_files else 0,
        "rejection_reasons": reasons_count,
        "items": results # Детальный список для каждого файла
    }

    report_path = out_dir / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"\n[bold green]Валидация завершена![/bold green]")
    print(f"Отчет: {report_path}")
    print(f"Статистика: {stats}")

if __name__ == "__main__":
    app()