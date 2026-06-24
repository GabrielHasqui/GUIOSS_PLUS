from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("evaluations", "0003_alter_evaluationfactor_unique_together_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evaluationsubfactor",
            name="compliance",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "No cumple el requisito"),
                    (2, "Desconozco si cumple requisito"),
                    (3, "Cumple parcialmente el requisito"),
                    (4, "Cumple el requisito"),
                ],
                default=1,
            ),
        ),
    ]
