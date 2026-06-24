from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.evaluations.models import (
    Dimension,
    Evaluation,
    EvaluationFactor,
    Factor,
    ImportanceLevel,
    Scope,
)


class EvaluationDatabaseIntegrityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="integrity.user",
            email="integrity@example.com",
            password="pass12345",
        )
        self.dimension = Dimension.objects.create(name="Integrity dimension")

    def test_factor_importance_must_be_between_one_and_four(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Factor.objects.create(
                dimension=self.dimension,
                name="Invalid importance factor",
                default_suggested_importance=9,
                scope=Scope.INTERNO,
            )

    def test_factor_names_are_unique_ignoring_case(self):
        Factor.objects.create(
            dimension=self.dimension,
            name="Usability integrity",
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Factor.objects.create(
                dimension=self.dimension,
                name="USABILITY INTEGRITY",
                default_suggested_importance=ImportanceLevel.OPCIONAL,
                scope=Scope.EXTERNO,
            )

    def test_relevance_flag_must_match_relative_importance(self):
        factor = Factor.objects.create(
            dimension=self.dimension,
            name="Relevant integrity factor",
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )
        evaluation = Evaluation.objects.create(
            software_name="Integrity software",
            context="Integrity context",
            created_by=self.user,
        )
        evaluation_factor = EvaluationFactor.objects.get(
            evaluation=evaluation,
            factor=factor,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            EvaluationFactor.objects.filter(pk=evaluation_factor.pk).update(
                relative_importance=ImportanceLevel.FUNDAMENTAL,
                is_relevant=False,
            )
