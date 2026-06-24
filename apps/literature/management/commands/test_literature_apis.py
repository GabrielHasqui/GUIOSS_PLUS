import json

from django.core.management.base import BaseCommand

from apps.literature.clients.openalex import search_openalex_works
from apps.literature.clients.scopus import search_scopus_works


class Command(BaseCommand):
    help = "Muestra por consola una muestra cruda de datos recibidos desde Scopus y OpenAlex."

    def add_arguments(self, parser):
        parser.add_argument(
            "--query",
            default='Moodle education open source software adoption usability',
            help="Texto de busqueda para consultar ambas APIs.",
        )
        parser.add_argument(
            "--count",
            default=2,
            type=int,
            help="Cantidad de resultados a mostrar por API.",
        )
        parser.add_argument(
            "--source",
            choices=["all", "scopus", "openalex"],
            default="all",
            help="API a consultar.",
        )

    def handle(self, *args, **options):
        query = options["query"]
        count = options["count"]
        source = options["source"]

        self.stdout.write(self.style.WARNING("Consulta usada:"))
        self.stdout.write(query)

        if source in ["all", "scopus"]:
            self._print_scopus_results(query, count)

        if source in ["all", "openalex"]:
            self._print_openalex_results(query, count)

    def _print_scopus_results(self, query, count):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== SCOPUS ==="))

        try:
            entries = search_scopus_works(query, per_page=count)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error consultando Scopus: {exc}"))
            return

        self.stdout.write(f"Resultados recibidos: {len(entries)}")

        for index, entry in enumerate(entries, start=1):
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"--- Scopus resultado {index} ---"))
            self.stdout.write(json.dumps(entry, indent=2, ensure_ascii=False))

    def _print_openalex_results(self, query, count):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== OPENALEX ==="))

        try:
            works = search_openalex_works(query, per_page=count)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error consultando OpenAlex: {exc}"))
            return

        self.stdout.write(f"Resultados recibidos: {len(works)}")

        for index, work in enumerate(works, start=1):
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"--- OpenAlex resultado {index} ---"))
            self.stdout.write(json.dumps(work, indent=2, ensure_ascii=False))
