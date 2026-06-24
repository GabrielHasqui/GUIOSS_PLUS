import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.evaluations.models import Dimension, Factor, Subfactor


class Command(BaseCommand):
    help = "Importa dimensiones, factores y subfactores desde el proyecto GUIOS original."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            default=None,
            help="Ruta opcional donde estan factors.csv y guiosad_data.csv.",
        )

    def handle(self, *args, **options):
        source_dir = options["source_dir"]

        if source_dir:
            source_path = Path(source_dir)
        else:
            source_path = (
                Path(settings.BASE_DIR)
                / "apps"
                / "evaluations"
                / "data"
                / "guios_original"
            )

        guiosad_data_path = source_path / "guiosad_data.csv"
        factors_path = source_path / "factors.csv"

        if not guiosad_data_path.exists():
            raise CommandError(f"No existe: {guiosad_data_path}")

        if not factors_path.exists():
            raise CommandError(f"No existe: {factors_path}")

        factor_metadata = {}

        with factors_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                factor_metadata[row["Factor"].strip()] = {
                    "suggested": int(row["Sugerida"]),
                    "scope": row["Alcance"].strip(),
                }

        created_dimensions = 0
        created_factors = 0
        created_subfactors = 0

        with guiosad_data_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, delimiter="\t")

            for row in reader:
                dimension_name = row["Dimensión"].strip()
                factor_name = row["Factor"].strip()
                subfactor_name = row["Subfactor"].strip()

                dimension, dimension_created = Dimension.objects.get_or_create(
                    name=dimension_name
                )

                if dimension_created:
                    created_dimensions += 1

                metadata = factor_metadata.get(
                    factor_name,
                    {
                        "suggested": 2,
                        "scope": "Interno",
                    },
                )

                factor, factor_created = Factor.objects.get_or_create(
                    name=factor_name,
                    defaults={
                        "dimension": dimension,
                        "default_suggested_importance": metadata["suggested"],
                        "scope": metadata["scope"],
                    },
                )

                if factor_created:
                    created_factors += 1
                else:
                    factor.dimension = dimension
                    factor.default_suggested_importance = metadata["suggested"]
                    factor.scope = metadata["scope"]
                    factor.save()

                subfactor, subfactor_created = Subfactor.objects.get_or_create(
                    factor=factor,
                    name=subfactor_name,
                )

                if subfactor_created:
                    created_subfactors += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Importación completada: "
                f"{created_dimensions} dimensiones, "
                f"{created_factors} factores, "
                f"{created_subfactors} subfactores creados."
            )
        )
