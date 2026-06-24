from django.core.management.base import BaseCommand

from apps.evaluations.models import Factor, FactorKeyword


KEYWORDS = {
    "Compatibilidad": [
        "compatibility",
        "interoperability",
        "integration",
        "migration",
        "standards",
    ],
    "Personalización": [
        "customization",
        "configuration",
        "extension",
        "plugin",
        "modularity",
    ],
    "Prueba": [
        "testing",
        "deployment",
        "trial",
        "pilot",
    ],
    "Fiabilidad": [
        "reliability",
        "stability",
        "security",
        "trust",
    ],
    "Reusabilidad": [
        "reuse",
        "library",
        "framework",
        "license",
    ],
    "Usabilidad": [
        "usability",
        "user experience",
        "ease of use",
        "learning curve",
    ],
    "Mantenibilidad": [
        "maintainability",
        "maintenance",
        "active development",
        "updates",
    ],
    "Portabilidad": [
        "portability",
        "cross platform",
        "mobile",
        "database independent",
    ],
    "Documentación": [
        "documentation",
        "manual",
        "tutorial",
        "community documentation",
    ],
    "Formación": [
        "training",
        "learning",
        "skills",
        "capacity building",
    ],
    "Tiempo de adopción": [
        "adoption time",
        "implementation time",
        "migration time",
    ],
    "Casos de estudio de adopción FLOSS": [
        "case study",
        "success story",
        "adoption case",
    ],
    "Centralidad de la tecnología de la información": [
        "IT centrality",
        "IT infrastructure",
        "information technology",
    ],
    "Apoyo de la alta dirección": [
        "top management support",
        "management support",
        "organizational support",
    ],
    "Bloqueo de proveedores": [
        "vendor lock-in",
        "lock in",
        "proprietary dependency",
    ],
    "Soporte": [
        "support",
        "technical support",
        "community support",
        "help desk",
    ],
    "Actitud hacia el cambio": [
        "attitude to change",
        "change management",
        "resistance to change",
    ],
    "Coste total de propiedad": [
        "total cost of ownership",
        "TCO",
        "cost",
        "licensing cost",
        "migration cost",
    ],
}


class Command(BaseCommand):
    help = "Carga palabras clave iniciales para relacionar literatura con factores GUIOS."

    def handle(self, *args, **options):
        created_count = 0

        for factor_name, keywords in KEYWORDS.items():
            try:
                factor = Factor.objects.get(name=factor_name)
            except Factor.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"No existe el factor: {factor_name}")
                )
                continue

            for keyword in keywords:
                _, created = FactorKeyword.objects.get_or_create(
                    factor=factor,
                    keyword=keyword,
                )
                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Palabras clave cargadas: {created_count}"
            )
        )