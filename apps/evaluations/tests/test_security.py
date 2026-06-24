from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.evaluations.models import (
    Dimension,
    Evaluation,
    EvaluationFactor,
    Factor,
    FodaLevel,
    ImportanceLevel,
    Recommendation,
    Scope,
)


class EvaluationInputSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="secure.input",
            email="secure-input@example.com",
            password="SecurePassword123!",
        )
        self.client.force_login(self.user)

    def test_create_evaluation_rejects_unknown_source(self):
        response = self.client.post(
            reverse("evaluation_create"),
            data={
                "software_name": "Moodle",
                "context": "Educacion",
                "description": "Prueba",
                "sources": ["internal-network"],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Evaluation.objects.filter(created_by=self.user).exists())

    def test_create_evaluation_rejects_oversized_name(self):
        response = self.client.post(
            reverse("evaluation_create"),
            data={
                "software_name": "x" * 181,
                "context": "Educacion",
                "description": "Prueba",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Evaluation.objects.filter(created_by=self.user).exists())

    def test_result_get_does_not_write_recommendation(self):
        dimension = Dimension.objects.create(name="Security dimension")
        factor = Factor.objects.create(
            dimension=dimension,
            name="Security factor",
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )
        evaluation = Evaluation.objects.create(
            software_name="Secure result",
            context="Test",
            created_by=self.user,
        )
        EvaluationFactor.objects.filter(
            evaluation=evaluation,
            factor=factor,
        ).update(
            decision_maker_importance=ImportanceLevel.IMPORTANTE,
            relative_importance=ImportanceLevel.IMPORTANTE,
            is_relevant=True,
            mean_weight=3,
            foda=FodaLevel.FORTALEZA,
        )

        response = self.client.get(reverse("result", args=[evaluation.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Recommendation.objects.filter(evaluation=evaluation).exists())
