from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.evaluations.models import (
    Dimension,
    Evaluation,
    EvaluationFactor,
    EvaluationStatus,
    EvaluationSubfactor,
    Factor,
    FodaLevel,
    ImportanceLevel,
    Recommendation,
    Scope,
    Subfactor,
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

    def test_ajax_subfactor_save_rejects_other_user_evaluation(self):
        other_user = get_user_model().objects.create_user(
            username="other.user",
            email="other@example.com",
            password="SecurePassword123!",
        )
        dimension = Dimension.objects.create(name="Private dimension")
        factor = Factor.objects.create(
            dimension=dimension,
            name="Private factor",
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )
        subfactor = Subfactor.objects.create(
            factor=factor,
            name="Private subfactor",
        )
        evaluation = Evaluation.objects.create(
            software_name="Private app",
            context="Test",
            created_by=other_user,
        )
        evaluation_factor = EvaluationFactor.objects.get(
            evaluation=evaluation,
            factor=factor,
        )
        evaluation_factor.is_relevant = True
        evaluation_factor.relative_importance = ImportanceLevel.IMPORTANTE
        evaluation_factor.save(update_fields=["is_relevant", "relative_importance"])
        evaluation_subfactor = EvaluationSubfactor.objects.create(
            evaluation_factor=evaluation_factor,
            subfactor=subfactor,
        )

        response = self.client.post(
            reverse("subfactor_save", args=[evaluation.pk]),
            data={
                "subfactor_id": evaluation_subfactor.pk,
                "compliance": "4",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        evaluation_subfactor.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(evaluation_subfactor.compliance, 1)

    def test_ajax_subfactor_save_updates_owned_evaluation(self):
        dimension = Dimension.objects.create(name="Owned dimension")
        factor = Factor.objects.create(
            dimension=dimension,
            name="Owned factor",
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )
        subfactor = Subfactor.objects.create(
            factor=factor,
            name="Owned subfactor",
        )
        evaluation = Evaluation.objects.create(
            software_name="Owned app",
            context="Test",
            created_by=self.user,
        )
        evaluation_factor = EvaluationFactor.objects.get(
            evaluation=evaluation,
            factor=factor,
        )
        evaluation_factor.is_relevant = True
        evaluation_factor.relative_importance = ImportanceLevel.IMPORTANTE
        evaluation_factor.save(update_fields=["is_relevant", "relative_importance"])
        evaluation_subfactor = EvaluationSubfactor.objects.create(
            evaluation_factor=evaluation_factor,
            subfactor=subfactor,
        )

        response = self.client.post(
            reverse("subfactor_save", args=[evaluation.pk]),
            data={
                "subfactor_id": evaluation_subfactor.pk,
                "compliance": "4",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        evaluation_subfactor.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mean_weight"], 4)
        self.assertEqual(response.json()["foda"], FodaLevel.FORTALEZA)
        self.assertTrue(response.json()["all_subfactors_complete"])
        self.assertEqual(evaluation_subfactor.compliance, 4)

    def test_completed_evaluation_rejects_factor_post(self):
        dimension = Dimension.objects.create(name="Closed factors dimension")
        factor = Factor.objects.create(
            dimension=dimension,
            name="Closed factors factor",
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )
        evaluation = Evaluation.objects.create(
            software_name="Closed app",
            context="Test",
            created_by=self.user,
            status=EvaluationStatus.COMPLETED,
        )
        evaluation_factor = EvaluationFactor.objects.get(
            evaluation=evaluation,
            factor=factor,
        )

        response = self.client.post(
            reverse("factors", args=[evaluation.pk]),
            data={
                f"decision_maker_importance_{evaluation_factor.pk}": str(
                    ImportanceLevel.FUNDAMENTAL
                ),
                "action": "continue",
            },
        )

        evaluation_factor.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(evaluation_factor.decision_maker_importance)

    def test_completed_evaluation_rejects_ajax_subfactor_save(self):
        dimension = Dimension.objects.create(name="Closed subfactor dimension")
        factor = Factor.objects.create(
            dimension=dimension,
            name="Closed subfactor factor",
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )
        subfactor = Subfactor.objects.create(
            factor=factor,
            name="Closed subfactor",
        )
        evaluation = Evaluation.objects.create(
            software_name="Closed subfactor app",
            context="Test",
            created_by=self.user,
            status=EvaluationStatus.COMPLETED,
        )
        evaluation_factor = EvaluationFactor.objects.get(
            evaluation=evaluation,
            factor=factor,
        )
        evaluation_factor.is_relevant = True
        evaluation_factor.relative_importance = ImportanceLevel.IMPORTANTE
        evaluation_factor.save(update_fields=["is_relevant", "relative_importance"])
        evaluation_subfactor = EvaluationSubfactor.objects.create(
            evaluation_factor=evaluation_factor,
            subfactor=subfactor,
        )

        response = self.client.post(
            reverse("subfactor_save", args=[evaluation.pk]),
            data={
                "subfactor_id": evaluation_subfactor.pk,
                "compliance": "4",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        evaluation_subfactor.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(evaluation_subfactor.compliance, 1)
