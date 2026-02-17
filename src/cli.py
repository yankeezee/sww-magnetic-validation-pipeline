from pathlib import Path
import json
import typer
from rich import print

app = typer.Typer()

@app.command()
def validate(
    input_dir: Path = typer.Option(..., help="Folder with CIF files"),
    out_dir: Path = typer.Option(Path("outputs"), help="Output folder"),
    train_reference: Path = typer.Option(None, help="CSV with train references for novelty"),
):
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "validation_report.json"

    # Заглушка: потом ребята заменят на реальную логику
    report = {
        "input_dir": str(input_dir),
        "n_total": 0,
        "n_validated": 0,
        "n_rejected": 0,
        "rejection_reasons": {},
        "notes": "stub report; implement validation pipeline",
    }

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[green]Saved report:[/green] {report_path}")

if __name__ == "__main__":
    app()
