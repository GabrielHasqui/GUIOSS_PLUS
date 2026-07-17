from django.db import migrations


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


def load_factor_keywords(apps, schema_editor):
    Factor = apps.get_model("evaluations", "Factor")
    FactorKeyword = apps.get_model("evaluations", "FactorKeyword")

    database = schema_editor.connection.alias
    missing_factors = []

    for factor_name, keywords in KEYWORDS.items():
        factor = Factor.objects.using(database).filter(name=factor_name).first()
        if factor is None:
            missing_factors.append(factor_name)
            continue

        for keyword in keywords:
            FactorKeyword.objects.using(database).get_or_create(
                factor=factor,
                keyword=keyword,
            )

    if missing_factors:
        missing = ", ".join(missing_factors)
        raise RuntimeError(
            f"No se encontraron factores para cargar palabras clave: {missing}"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("evaluations", "0006_evaluation_reopen_tracking"),
    ]

    operations = [
        migrations.RunPython(
            load_factor_keywords,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
