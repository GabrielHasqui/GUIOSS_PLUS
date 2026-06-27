from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from apps.evaluations.models import (
    Dimension,
    Evaluation,
    EvaluationFactor,
    EvaluationStatus,
    EvaluationSubfactor,
    Factor,
    FodaLevel,
    ImportanceLevel,
    Scope,
    Subfactor,
    SubfactorComplianceLevel,
)
from apps.evaluations.services import (
    calculate_mean_weight,
    calculate_relative_importance,
    classify_foda,
    initialize_relevant_subfactors,
    is_relevant,
    save_factor_decision_importance,
    save_single_subfactor_compliance,
    save_subfactor_compliance,
)


class OriginalGuiosCalculationTests(SimpleTestCase):
    def test_relative_importance_matches_original_guios_matrix(self):
        expected_matrix = [
            [1, 1, 2, 2],
            [1, 2, 2, 3],
            [2, 2, 3, 3],
            [2, 3, 3, 4],
        ]

        for suggested_importance in ImportanceLevel.values:
            for decision_maker_importance in ImportanceLevel.values:
                with self.subTest(
                    suggested_importance=suggested_importance,
                    decision_maker_importance=decision_maker_importance,
                ):
                    self.assertEqual(
                        calculate_relative_importance(
                            suggested_importance,
                            decision_maker_importance,
                        ),
                        expected_matrix[suggested_importance - 1][
                            decision_maker_importance - 1
                        ],
                    )

    def test_relevance_threshold_matches_original_guios(self):
        self.assertFalse(is_relevant(ImportanceLevel.IRRELEVANTE))
        self.assertTrue(is_relevant(ImportanceLevel.OPCIONAL))
        self.assertTrue(is_relevant(ImportanceLevel.IMPORTANTE))
        self.assertTrue(is_relevant(ImportanceLevel.FUNDAMENTAL))

    def test_mean_weight_and_foda_match_original_guios(self):
        self.assertEqual(calculate_mean_weight([1, 3, 4]), 8 / 3)
        self.assertEqual(classify_foda(2.9, Scope.INTERNO), FodaLevel.DEBILIDAD)
        self.assertEqual(classify_foda(3, Scope.INTERNO), FodaLevel.FORTALEZA)
        self.assertEqual(classify_foda(2.9, Scope.EXTERNO), FodaLevel.AMENAZA)
        self.assertEqual(classify_foda(3, Scope.EXTERNO), FodaLevel.OPORTUNIDAD)


class OriginalGuiosSubfactorWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="decision-maker")
        dimension = Dimension.objects.create(name="Tecnologica")
        factor = Factor.objects.create(
            name="Factor de prueba",
            dimension=dimension,
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.INTERNO,
        )
        Subfactor.objects.create(factor=factor, name="Subfactor uno")
        Subfactor.objects.create(factor=factor, name="Subfactor dos")
        evaluation = Evaluation.objects.create(
            software_name="Software",
            context="Educacion",
            created_by=self.user,
        )
        self.evaluation_factor = EvaluationFactor.objects.get(
            evaluation=evaluation,
            factor=factor,
        )
        self.evaluation_factor.is_relevant = True
        self.evaluation_factor.relative_importance = ImportanceLevel.IMPORTANTE
        self.evaluation_factor.save(
            update_fields=["is_relevant", "relative_importance"]
        )
        initialize_relevant_subfactors(self.evaluation_factor)

    def test_subfactors_start_at_one_without_calculating_mean(self):
        values = list(
            EvaluationSubfactor.objects.filter(
                evaluation_factor=self.evaluation_factor
            ).values_list("compliance", flat=True)
        )
        self.evaluation_factor.refresh_from_db()

        self.assertEqual(
            values,
            [SubfactorComplianceLevel.NO_CUMPLE] * 2,
        )
        self.assertIsNone(self.evaluation_factor.mean_weight)
        self.assertEqual(self.evaluation_factor.foda, "")

    def test_save_all_subfactors_calculates_original_mean_and_foda(self):
        subfactors = list(
            EvaluationSubfactor.objects.filter(
                evaluation_factor=self.evaluation_factor
            )
        )
        post_data = {
            f"compliance_{subfactors[0].pk}": "3",
            f"compliance_{subfactors[1].pk}": "4",
        }

        save_subfactor_compliance(
            self.evaluation_factor.evaluation,
            self.evaluation_factor,
            post_data,
        )
        self.evaluation_factor.refresh_from_db()

        self.assertEqual(self.evaluation_factor.mean_weight, 3.5)
        self.assertEqual(self.evaluation_factor.foda, FodaLevel.FORTALEZA)

    def test_save_single_subfactor_updates_factor_summary(self):
        subfactor = EvaluationSubfactor.objects.filter(
            evaluation_factor=self.evaluation_factor
        ).first()

        save_single_subfactor_compliance(
            self.evaluation_factor.evaluation,
            subfactor.pk,
            "4",
        )
        subfactor.refresh_from_db()
        self.evaluation_factor.refresh_from_db()

        self.assertEqual(subfactor.compliance, SubfactorComplianceLevel.CUMPLE)
        self.assertEqual(self.evaluation_factor.mean_weight, 2.5)
        self.assertEqual(self.evaluation_factor.foda, FodaLevel.DEBILIDAD)

    def test_partial_subfactor_submission_is_rejected(self):
        subfactor = EvaluationSubfactor.objects.filter(
            evaluation_factor=self.evaluation_factor
        ).first()

        with self.assertRaises(ValidationError):
            save_subfactor_compliance(
                self.evaluation_factor.evaluation,
                self.evaluation_factor,
                {f"compliance_{subfactor.pk}": "4"},
            )

        self.evaluation_factor.refresh_from_db()
        self.assertIsNone(self.evaluation_factor.mean_weight)

    def test_completed_evaluation_rejects_factor_and_subfactor_changes(self):
        self.evaluation_factor.evaluation.status = EvaluationStatus.COMPLETED
        self.evaluation_factor.evaluation.save(update_fields=["status", "updated_at"])
        subfactor = EvaluationSubfactor.objects.filter(
            evaluation_factor=self.evaluation_factor
        ).first()

        with self.assertRaises(ValidationError):
            save_factor_decision_importance(
                self.evaluation_factor.evaluation,
                {
                    f"decision_maker_importance_{self.evaluation_factor.pk}": str(
                        ImportanceLevel.FUNDAMENTAL
                    ),
                },
            )

        with self.assertRaises(ValidationError):
            save_single_subfactor_compliance(
                self.evaluation_factor.evaluation,
                subfactor.pk,
                "4",
            )

        self.evaluation_factor.refresh_from_db()
        subfactor.refresh_from_db()
        self.assertIsNone(self.evaluation_factor.decision_maker_importance)
        self.assertEqual(subfactor.compliance, SubfactorComplianceLevel.NO_CUMPLE)
