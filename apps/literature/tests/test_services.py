from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.evaluations.models import ImportanceLevel
from apps.literature.services import THESIS_BASE_EXPERT_IMPORTANCE,assign_quartile_importance,calculate_factor_importance_metrics,calculate_literature_ratio,calculate_quartile_thresholds,calculate_suggested_importance,scopus_entry_url
from apps.literature.services.matching import (
    is_usable_literature_result,
    normalize_context_for_search,
)
from apps.literature.clients.openalex import search_openalex_works


class SuggestedImportanceCalculationTests(SimpleTestCase):
    @override_settings(OPENALEX_EMAIL="", OPENALEX_API_KEY="")
    @patch("apps.literature.clients.openalex.requests.get")
    def test_openalex_request_filters_publications_from_2020(self, request_get):
        response = request_get.return_value
        response.json.return_value = {"results": []}

        search_openalex_works("open source adoption")

        self.assertEqual(
            request_get.call_args.kwargs["params"]["filter"],
            "from_publication_date:2020-01-01",
        )

    def test_scopus_entry_url_prefers_public_scopus_link(self):
        entry = {
            "prism:url": "https://api.elsevier.com/content/abstract/scopus_id/85021627634",
            "link": [
                {
                    "@ref": "self",
                    "@href": "https://api.elsevier.com/content/abstract/scopus_id/85021627634",
                },
                {
                    "@ref": "scopus",
                    "@href": "https://www.scopus.com/inward/record.uri?partnerID=HzOxMe3b&scp=85021627634&origin=inward",
                },
            ],
        }

        self.assertEqual(
            scopus_entry_url(entry),
            "https://www.scopus.com/inward/record.uri?partnerID=HzOxMe3b&scp=85021627634&origin=inward",
        )

    def test_scopus_entry_url_supports_xml_style_link_keys(self):
        entry = {
            "prism:url": "https://api.elsevier.com/content/abstract/scopus_id/85021627634",
            "link": [
                {
                    "rel": "self",
                    "href": "https://api.elsevier.com/content/abstract/scopus_id/85021627634",
                },
                {
                    "rel": "scopus",
                    "href": "https://www.scopus.com/inward/record.uri?partnerID=HzOxMe3b&scp=85021627634&origin=inward",
                },
            ],
        }

        self.assertEqual(
            scopus_entry_url(entry),
            "https://www.scopus.com/inward/record.uri?partnerID=HzOxMe3b&scp=85021627634&origin=inward",
        )

    def test_literature_result_requires_title_identifier_and_relevance(self):
        self.assertFalse(is_usable_literature_result("", "2-s2.0-1", 8))
        self.assertFalse(
            is_usable_literature_result("Untitled Scopus work", "2-s2.0-1", 8)
        )
        self.assertFalse(is_usable_literature_result("Valid title", "", 8))
        self.assertFalse(is_usable_literature_result("Valid title", "2-s2.0-1", 3))
        self.assertTrue(is_usable_literature_result("Valid title", "2-s2.0-1", 5))

    def test_library_context_is_normalized_for_literature_search(self):
        self.assertEqual(
            normalize_context_for_search("Bibliotecas universitarias"),
            "academic libraries",
        )

    def test_suggested_importance_uses_guios_assignment_matrix(self):
        expected_matrix = [
            [1, 1, 2, 2],
            [1, 2, 2, 3],
            [2, 2, 3, 3],
            [2, 3, 3, 4],
        ]

        for literature_importance in ImportanceLevel.values:
            for expert_importance in ImportanceLevel.values:
                with self.subTest(
                    literature_importance=literature_importance,
                    expert_importance=expert_importance,
                ):
                    self.assertEqual(
                        calculate_suggested_importance(
                            literature_importance,
                            expert_importance,
                        ),
                        expected_matrix[literature_importance - 1][expert_importance - 1],
                    )

    def test_literature_ratio_matches_thesis_formula(self):
        self.assertEqual(calculate_literature_ratio(33, 8), 33 / 8)
        self.assertEqual(calculate_literature_ratio(10, 0), 0)

    def test_quartile_importance_assigns_four_levels(self):
        thresholds = calculate_quartile_thresholds([1, 2, 3, 4])

        self.assertEqual(thresholds, [1, 2, 3])
        self.assertEqual(
            assign_quartile_importance(1, thresholds),
            ImportanceLevel.IRRELEVANTE,
        )
        self.assertEqual(
            assign_quartile_importance(2, thresholds),
            ImportanceLevel.OPCIONAL,
        )
        self.assertEqual(
            assign_quartile_importance(3, thresholds),
            ImportanceLevel.IMPORTANTE,
        )
        self.assertEqual(
            assign_quartile_importance(4, thresholds),
            ImportanceLevel.FUNDAMENTAL,
        )

    def test_factor_metrics_use_api_documents_for_literature_and_thesis_expert_baseline(self):
        factor_metrics = [
            {
                "citation_count": 400,
                "document_count": 1,
                "subfactor_count": 1,
            },
            {
                "citation_count": 300,
                "document_count": 2,
                "subfactor_count": 1,
            },
            {
                "citation_count": 200,
                "document_count": 3,
                "subfactor_count": 1,
            },
            {
                "citation_count": 100,
                "document_count": 4,
                "subfactor_count": 1,
            },
        ]

        result = calculate_factor_importance_metrics(factor_metrics)

        self.assertEqual(result[0]["literature_importance"], ImportanceLevel.IRRELEVANTE)
        self.assertEqual(result[1]["literature_importance"], ImportanceLevel.OPCIONAL)
        self.assertEqual(result[2]["literature_importance"], ImportanceLevel.IMPORTANTE)
        self.assertEqual(result[3]["literature_importance"], ImportanceLevel.FUNDAMENTAL)
        self.assertEqual(result[3]["expert_importance"], THESIS_BASE_EXPERT_IMPORTANCE)
        self.assertEqual(result[3]["suggested_importance"], ImportanceLevel.IMPORTANTE)

    def test_literature_importance_matches_thesis_table_5_3(self):
        thesis_data = [
            ("Compatibilidad", 33, 8, ImportanceLevel.IMPORTANTE),
            ("Fiabilidad", 19, 5, ImportanceLevel.IMPORTANTE),
            ("Mantenibilidad", 4, 1, ImportanceLevel.IMPORTANTE),
            ("Personalizacion", 30, 6, ImportanceLevel.FUNDAMENTAL),
            ("Prueba", 4, 1, ImportanceLevel.IMPORTANTE),
            ("Documentacion", 20, 11, ImportanceLevel.IRRELEVANTE),
            ("Portabilidad", 4, 2, ImportanceLevel.OPCIONAL),
            ("Reusabilidad", 5, 2, ImportanceLevel.OPCIONAL),
            ("Usabilidad", 14, 4, ImportanceLevel.OPCIONAL),
            ("Apoyo", 5, 1, ImportanceLevel.FUNDAMENTAL),
            ("Formacion", 27, 4, ImportanceLevel.FUNDAMENTAL),
            ("Soporte", 43, 6, ImportanceLevel.FUNDAMENTAL),
            ("Actitud", 3, 2, ImportanceLevel.IRRELEVANTE),
            ("Bloqueo", 3, 1, ImportanceLevel.OPCIONAL),
            ("Casos", 1, 1, ImportanceLevel.IRRELEVANTE),
            ("Centralidad", 2, 2, ImportanceLevel.IRRELEVANTE),
            ("Tiempo", 2, 2, ImportanceLevel.IRRELEVANTE),
            ("TCO", 24, 2, ImportanceLevel.FUNDAMENTAL),
        ]
        ratios = [
            calculate_literature_ratio(citation_count, subfactor_count)
            for _, citation_count, subfactor_count, _ in thesis_data
        ]
        thresholds = calculate_quartile_thresholds(ratios)

        for name, citation_count, subfactor_count, expected in thesis_data:
            with self.subTest(name=name):
                self.assertEqual(
                    assign_quartile_importance(
                        calculate_literature_ratio(citation_count, subfactor_count),
                        thresholds,
                    ),
                    expected,
                )

    def test_suggested_importance_matches_thesis_table_5_3_with_expert_baseline(self):
        thesis_data = [
            ("Compatibilidad", ImportanceLevel.IMPORTANTE, ImportanceLevel.IMPORTANTE),
            ("Fiabilidad", ImportanceLevel.IMPORTANTE, ImportanceLevel.IMPORTANTE),
            ("Mantenibilidad", ImportanceLevel.IMPORTANTE, ImportanceLevel.IMPORTANTE),
            ("Personalizacion", ImportanceLevel.FUNDAMENTAL, ImportanceLevel.IMPORTANTE),
            ("Prueba", ImportanceLevel.IMPORTANTE, ImportanceLevel.IMPORTANTE),
            ("Documentacion", ImportanceLevel.IRRELEVANTE, ImportanceLevel.OPCIONAL),
            ("Portabilidad", ImportanceLevel.OPCIONAL, ImportanceLevel.OPCIONAL),
            ("Reusabilidad", ImportanceLevel.OPCIONAL, ImportanceLevel.OPCIONAL),
            ("Usabilidad", ImportanceLevel.OPCIONAL, ImportanceLevel.OPCIONAL),
            ("Apoyo", ImportanceLevel.FUNDAMENTAL, ImportanceLevel.IMPORTANTE),
            ("Formacion", ImportanceLevel.FUNDAMENTAL, ImportanceLevel.IMPORTANTE),
            ("Soporte", ImportanceLevel.FUNDAMENTAL, ImportanceLevel.IMPORTANTE),
            ("Actitud", ImportanceLevel.IRRELEVANTE, ImportanceLevel.OPCIONAL),
            ("Bloqueo", ImportanceLevel.OPCIONAL, ImportanceLevel.OPCIONAL),
            ("Casos", ImportanceLevel.IRRELEVANTE, ImportanceLevel.OPCIONAL),
            ("Centralidad", ImportanceLevel.IRRELEVANTE, ImportanceLevel.OPCIONAL),
            ("Tiempo", ImportanceLevel.IRRELEVANTE, ImportanceLevel.OPCIONAL),
            ("TCO", ImportanceLevel.FUNDAMENTAL, ImportanceLevel.IMPORTANTE),
        ]

        for name, literature_importance, expected in thesis_data:
            with self.subTest(name=name):
                self.assertEqual(
                    calculate_suggested_importance(
                        literature_importance,
                        THESIS_BASE_EXPERT_IMPORTANCE,
                    ),
                    expected,
                )
