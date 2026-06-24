from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.evaluations.models import Dimension, Evaluation, EvaluationFactor, EvaluationStatus, Factor, ImportanceLevel, Scope
from apps.evaluations.selectors import (
    get_active_evaluation,
    get_active_evaluation_progress_summary,
    get_blocking_evaluation,
    get_visible_evaluations_queryset,
)
from apps.users.models import UserRole


class EvaluationVisibilitySelectorTests(TestCase):
    def setUp(self):
        Factor.objects.all().delete()
        Dimension.objects.all().delete()

        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
        )
        self.admin.profile.role = UserRole.ADMIN
        self.admin.profile.save(update_fields=["role", "updated_at"])

        self.user_one = User.objects.create_user(
            username="user.one",
            email="user.one@example.com",
            password="pass12345",
        )
        self.user_two = User.objects.create_user(
            username="user.two",
            email="user.two@example.com",
            password="pass12345",
        )

        self.evaluation_one = Evaluation.objects.create(
            software_name="Open edX",
            context="Educacion",
            created_by=self.user_one,
        )
        self.evaluation_two = Evaluation.objects.create(
            software_name="Koha",
            context="Bibliotecas",
            created_by=self.user_two,
        )

    def test_evaluator_only_sees_their_own_evaluations(self):
        visible_ids = list(
            get_visible_evaluations_queryset(self.user_two).values_list("id", flat=True)
        )

        self.assertEqual(visible_ids, [self.evaluation_two.id])
        self.assertEqual(get_active_evaluation(self.user_two), self.evaluation_two)
        self.assertEqual(get_blocking_evaluation(self.user_two), self.evaluation_two)

    def test_admin_sees_all_evaluations(self):
        visible_ids = list(
            get_visible_evaluations_queryset(self.admin).values_list("id", flat=True)
        )

        self.assertCountEqual(visible_ids, [self.evaluation_one.id, self.evaluation_two.id])

    def test_active_evaluation_progress_summary_uses_real_workflow_progress(self):
        dimension = Dimension.objects.create(name="Dimension test dashboard")
        factor_one = Factor.objects.create(
            name="Factor uno test",
            dimension=dimension,
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )
        factor_two = Factor.objects.create(
            name="Factor dos test",
            dimension=dimension,
            default_suggested_importance=ImportanceLevel.OPCIONAL,
            scope=Scope.EXTERNO,
        )

        evaluation = Evaluation.objects.create(
            software_name="Moodle",
            context="Educacion",
            created_by=self.user_one,
            status=EvaluationStatus.FACTORS_READY,
        )

        EvaluationFactor.objects.filter(
            evaluation=evaluation,
            factor=factor_one,
        ).update(
            suggested_importance=ImportanceLevel.FUNDAMENTAL,
            decision_maker_importance=ImportanceLevel.IMPORTANTE,
            relative_importance=ImportanceLevel.IMPORTANTE,
            is_relevant=True,
            selected_scope=Scope.INTERNO,
            mean_weight=3.5,
        )
        EvaluationFactor.objects.filter(
            evaluation=evaluation,
            factor=factor_two,
        ).update(
            suggested_importance=ImportanceLevel.OPCIONAL,
            selected_scope=Scope.EXTERNO,
        )

        summary = get_active_evaluation_progress_summary(evaluation)

        self.assertEqual(summary[0]["count"], 2)
        self.assertEqual(summary[0]["total"], 2)
        self.assertEqual(summary[1]["count"], 1)
        self.assertEqual(summary[1]["total"], 2)
        self.assertEqual(summary[2]["count"], 1)
        self.assertEqual(summary[2]["total"], 1)
        self.assertEqual(summary[3]["count"], 0)
        self.assertEqual(summary[3]["total"], 1)
