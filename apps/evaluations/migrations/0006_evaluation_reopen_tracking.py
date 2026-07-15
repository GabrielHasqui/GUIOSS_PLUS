from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("evaluations", "0005_load_guios_csv_data"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="evaluation",
            name="reopen_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="evaluation",
            name="reopened_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="evaluation",
            name="reopened_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reopened_evaluations",
                to="auth.user",
            ),
        ),
    ]
