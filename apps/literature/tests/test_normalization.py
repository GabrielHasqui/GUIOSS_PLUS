from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.evaluations.models import Dimension, Evaluation, Factor, FactorKeyword, Scope, Subfactor

from apps.literature.models import FactorEvidence, LiteratureDocument, LiteratureQuery, LiteratureQueryStatus, LiteratureSource, QueryResult

from apps.literature.services import calculate_scopus_suggested_importance_for_evaluation


class LiteratureNormalizationTests(TestCase):
    def setUp(self):
        Factor.objects.all().delete()
        Dimension.objects.all().delete()

        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="secret",
        )

        dimension = Dimension.objects.create(name="Tecnologica")

        self.factor = Factor.objects.create(
            dimension=dimension,
            name="Usabilidad",
            default_suggested_importance=3,
            scope=Scope.EXTERNO,
        )

        FactorKeyword.objects.create(
            factor=self.factor,
            keyword="usability",
        )

        Subfactor.objects.create(
            factor=self.factor,
            name="El software es facil de usar",
        )

        self.evaluation = Evaluation.objects.create(
            software_name="Moodle",
            context="Educacion",
            description="Caso de prueba",
            created_by=self.user,
        )

    @patch("apps.literature.services.scopus.search_scopus_works")
    def test_scopus_repeated_query_reuses_document_without_duplicating_evidence(
        self,
        search_scopus_works,
    ):
        search_scopus_works.return_value = [
            {
                "eid": "2-s2.0-123",
                "dc:title": "Moodle usability adoption",
                "dc:creator": "Autor A.",
                "prism:coverDate": "2024-01-01",
                "prism:doi": "10.1000/test",
                "citedby-count": "10",
                "link": [
                    {
                        "@ref": "scopus",
                        "@href": "https://www.scopus.com/inward/record.uri?scp=123",
                    }
                ],
            }
        ]

        calculate_scopus_suggested_importance_for_evaluation(self.evaluation)
        calculate_scopus_suggested_importance_for_evaluation(self.evaluation)

        self.assertIn("PUBYEAR > 2019", search_scopus_works.call_args.args[0])
        self.assertEqual(LiteratureQuery.objects.count(), 2)
        self.assertFalse(
            LiteratureQuery.objects.exclude(
                evaluation_factor__evaluation=self.evaluation,
                evaluation_factor__factor=self.factor,
            ).exists()
        )
        self.assertEqual(LiteratureDocument.objects.count(), 1)
        self.assertEqual(QueryResult.objects.count(), 2)
        self.assertEqual(FactorEvidence.objects.count(), 1)

    @patch("apps.literature.services.scopus.search_scopus_works")
    def test_scopus_only_uses_documents_from_2020(self, search_scopus_works):
        search_scopus_works.return_value = [
            {
                "eid": "old-document",
                "dc:title": "Moodle usability adoption before 2020",
                "prism:coverDate": "2019-12-31",
                "citedby-count": "1000",
            },
            {
                "eid": "allowed-document",
                "dc:title": "Moodle usability adoption from 2020",
                "prism:coverDate": "2020-01-01",
                "citedby-count": "1",
            },
        ]

        calculate_scopus_suggested_importance_for_evaluation(self.evaluation)

        self.assertEqual(
            list(LiteratureDocument.objects.values_list("source_identifier", flat=True)),
            ["allowed-document"],
        )

    @patch("apps.literature.services.openalex.search_openalex_works")
    def test_openalex_only_uses_documents_from_2020(self, search_openalex_works):
        search_openalex_works.return_value = [
            {
                "id": "https://openalex.org/old-document",
                "display_name": "Moodle usability adoption before 2020",
                "publication_year": 2019,
                "cited_by_count": 1000,
            },
            {
                "id": "https://openalex.org/allowed-document",
                "display_name": "Moodle usability adoption from 2020",
                "publication_year": 2020,
                "cited_by_count": 1,
            },
        ]

        from apps.literature.services import (
            calculate_openalex_suggested_importance_for_evaluation,
        )

        calculate_openalex_suggested_importance_for_evaluation(self.evaluation)

        self.assertEqual(
            list(LiteratureDocument.objects.values_list("source_identifier", flat=True)),
            ["https://openalex.org/allowed-document"],
        )

    @patch("apps.literature.services.openalex.search_openalex_works")
    def test_external_api_error_does_not_persist_credentials(self, search_works):
        search_works.side_effect = RuntimeError(
            "https://api.openalex.org/works?api_key=SECRET-VALUE"
        )

        from apps.literature.services import (
            calculate_openalex_suggested_importance_for_evaluation,
        )

        calculate_openalex_suggested_importance_for_evaluation(self.evaluation)
        query = LiteratureQuery.objects.get()

        self.assertEqual(query.status, LiteratureQueryStatus.FAILED)
        self.assertNotIn("SECRET-VALUE", query.error_message)
        self.assertNotIn("api_key", query.error_message)
