import csv
from pathlib import Path

from django.db import migrations


def load_guios_csv_data(apps, schema_editor):
    Dimension = apps.get_model("evaluations", "Dimension")
    Factor = apps.get_model("evaluations", "Factor")
    Subfactor = apps.get_model("evaluations", "Subfactor")

    database = schema_editor.connection.alias
    source_dir = Path(__file__).resolve().parent.parent / "data" / "guios_original"
    factors_path = source_dir / "factors.csv"
    guios_data_path = source_dir / "guiosad_data.csv"

    if not factors_path.exists() or not guios_data_path.exists():
        raise RuntimeError(f"No se encontraron los CSV iniciales en {source_dir}")

    factor_metadata = {}
    with factors_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter="\t"):
            factor_metadata[row["Factor"].strip()] = {
                "default_suggested_importance": int(row["Sugerida"]),
                "scope": row["Alcance"].strip(),
            }

    with guios_data_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file, delimiter="\t"):
            dimension_name = row["Dimensión"].strip()
            factor_name = row["Factor"].strip()
            subfactor_name = row["Subfactor"].strip()

            dimension, _ = Dimension.objects.using(database).get_or_create(
                name=dimension_name,
            )

            metadata = factor_metadata.get(
                factor_name,
                {
                    "default_suggested_importance": 2,
                    "scope": "Interno",
                },
            )
            factor, _ = Factor.objects.using(database).update_or_create(
                name=factor_name,
                defaults={
                    "dimension": dimension,
                    **metadata,
                },
            )

            Subfactor.objects.using(database).get_or_create(
                factor=factor,
                name=subfactor_name,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("evaluations", "0004_alter_evaluationsubfactor_compliance"),
    ]

    operations = [
        migrations.RunPython(
            load_guios_csv_data,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
