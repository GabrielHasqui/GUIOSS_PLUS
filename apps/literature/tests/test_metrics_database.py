from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.evaluations.models import (
    Dimension,
    Evaluation,
    EvaluationFactor,
    Factor,
    ImportanceLevel,
    Scope,
    Subfactor,
)
from apps.literature.models import (
    FactorEvidence,
    LiteratureDocument,
    LiteratureQuery,
    LiteratureQueryStatus,
    LiteratureSource,
)
from apps.literature.services import recalculate_suggested_importance_from_evidence


class SuggestedImportanceEvidenceTests(TestCase):
    def setUp(self):
        Factor.objects.all().delete()
        Dimension.objects.all().delete()

        user = User.objects.create_user(username="literature-user")
        dimension = Dimension.objects.create(name="Tecnologica")
        self.factor = Factor.objects.create(
            name="Compatibilidad de prueba",
            dimension=dimension,
            default_suggested_importance=ImportanceLevel.IMPORTANTE,
            scope=Scope.EXTERNO,
        )
        Subfactor.objects.create(factor=self.factor, name="Subfactor")
        self.evaluation = Evaluation.objects.create(
            software_name="Software",
            context="Educacion",
            created_by=user,
        )
        self.evaluation_factor = EvaluationFactor.objects.get(
            evaluation=self.evaluation,
            factor=self.factor,
        )

    def test_failed_query_preserves_original_suggested_importance(self):
        LiteratureQuery.objects.create(
            evaluation_factor=self.evaluation_factor,
            source=LiteratureSource.OPENALEX,
            query_text="failed query",
            status=LiteratureQueryStatus.FAILED,
            error_message="External service failed.",
            completed_at=timezone.now(),
        )
        EvaluationFactor.objects.filter(pk=self.evaluation_factor.pk).update(
            literature_importance=ImportanceLevel.IRRELEVANTE,
            expert_importance=ImportanceLevel.IMPORTANTE,
            suggested_importance=ImportanceLevel.OPCIONAL,
        )

        result = recalculate_suggested_importance_from_evidence(self.evaluation)
        self.evaluation_factor.refresh_from_db()

        self.assertEqual(result, 0)
        self.assertIsNone(self.evaluation_factor.literature_importance)
        self.assertIsNone(self.evaluation_factor.expert_importance)
        self.assertEqual(
            self.evaluation_factor.suggested_importance,
            self.factor.default_suggested_importance,
        )

    def test_same_doi_from_two_sources_counts_as_one_reference(self):
        LiteratureQuery.objects.create(
            evaluation_factor=self.evaluation_factor,
            source=LiteratureSource.OPENALEX,
            query_text="completed query",
            status=LiteratureQueryStatus.COMPLETED,
            completed_at=timezone.now(),
        )
        for source, identifier in [
            (LiteratureSource.OPENALEX, "W1"),
            (LiteratureSource.SCOPUS, "S1"),
        ]:
            document = LiteratureDocument.objects.create(
                source=source,
                source_identifier=identifier,
                title="The same reference",
                doi="10.1000/same-reference",
                year=2020,
                citation_count=999,
            )
            FactorEvidence.objects.create(
                evaluation_factor=self.evaluation_factor,
                document=document,
                relevance_score=8,
            )

        result = recalculate_suggested_importance_from_evidence(self.evaluation)

        self.assertEqual(result, 1)
