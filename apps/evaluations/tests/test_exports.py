from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from apps.evaluations.models import (
    Dimension,
    Evaluation,
    EvaluationFactor,
    EvaluationStatus,
    Factor,
    FodaLevel,
    ImportanceLevel,
    Recommendation,
    Scope,
)


class EvaluationPdfExportTests(TestCase):
    def setUp(self):
        Factor.objects.all().delete()
        Dimension.objects.all().delete()

        self.user = User.objects.create_user(
            username="gabri",
            email="gabri@example.com",
            password="testpass123",
        )
        self.client.force_login(self.user)

        dimension = Dimension.objects.create(name="Tecnica")
        factor = Factor.objects.create(
            dimension=dimension,
            name="Usabilidad",
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )
        self.evaluation = Evaluation.objects.create(
            software_name="Koha",
            context="Educacion",
            description="Evaluacion de prueba",
            status=EvaluationStatus.COMPLETED,
            created_by=self.user,
        )
        evaluation_factor = EvaluationFactor.objects.get(
            evaluation=self.evaluation,
            factor=factor,
        )
        evaluation_factor.literature_importance = ImportanceLevel.IMPORTANTE
        evaluation_factor.expert_importance = ImportanceLevel.IMPORTANTE
        evaluation_factor.suggested_importance = ImportanceLevel.IMPORTANTE
        evaluation_factor.decision_maker_importance = ImportanceLevel.IMPORTANTE
        evaluation_factor.relative_importance = ImportanceLevel.IMPORTANTE
        evaluation_factor.is_relevant = True
        evaluation_factor.selected_scope = Scope.INTERNO
        evaluation_factor.mean_weight = 3.5
        evaluation_factor.foda = FodaLevel.FORTALEZA
        evaluation_factor.save()
        Recommendation.objects.create(
            evaluation=self.evaluation,
            code="A",
            text="Recomendacion de prueba.",
        )

    def test_export_evaluation_pdf_returns_pdf_response(self):
        response = self.client.get(
            reverse("evaluation_report_pdf", args=[self.evaluation.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_export_escapes_reportlab_markup_from_user_input(self):
        self.evaluation.software_name = '<img src="http://127.0.0.1/private"/>'
        self.evaluation.context = "<b>Injected context</b>"
        self.evaluation.save(update_fields=["software_name", "context", "updated_at"])

        with patch("reportlab.platypus.paraparser.ImageReader") as image_reader:
            response = self.client.get(
                reverse("evaluation_report_pdf", args=[self.evaluation.pk])
            )

        self.assertEqual(response.status_code, 200)
        image_reader.assert_not_called()
