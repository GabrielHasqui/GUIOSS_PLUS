from django.utils import timezone

from apps.evaluations.models import EvaluationStatus
from apps.literature.clients.openalex import search_openalex_works
from apps.literature.constants import MIN_PUBLICATION_YEAR
from apps.literature.models import FactorEvidence, LiteratureDocument, LiteratureQuery, LiteratureQueryStatus, LiteratureSource, QueryResult

from apps.literature.services.matching import (
    build_openalex_query,
    calculate_document_relevance_score,
    is_usable_literature_result,
)
from apps.literature.services.metrics import calculate_factor_importance_metrics, update_evaluation_factors_from_importance_metrics

def openalex_authors_to_text(work):
    authorships = work.get("authorships", [])
    names = []

    for authorship in authorships:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            names.append(name)

    return ", ".join(names)


def openalex_work_url(work):
    primary_location = work.get("primary_location") or {}
    landing_page_url = primary_location.get("landing_page_url")

    if landing_page_url:
        return landing_page_url

    return work.get("id", "")


def openalex_work_doi(work):
    doi = work.get("doi") or ""
    return doi.replace("https://doi.org/", "")


def openalex_work_identifier(work):
    return (
        work.get("id")
        or openalex_work_doi(work)
        or openalex_work_url(work)
        or work.get("display_name", "")
    )


def calculate_openalex_suggested_importance_for_evaluation(evaluation, per_factor=5):
    """
    Consulta OpenAlex y alimenta la IL con evidencia bibliografica.
    La IE se conserva como base de expertos definida en la tesis.
    """
    total_documents = 0
    factor_metrics = []

    for evaluation_factor in evaluation.evaluation_factors.select_related("factor"):
        factor = evaluation_factor.factor
        query_text = build_openalex_query(evaluation, factor)

        query = LiteratureQuery.objects.create(
            evaluation_factor=evaluation_factor,
            source=LiteratureSource.OPENALEX,
            query_text=query_text,
            status=LiteratureQueryStatus.RUNNING,
        )

        try:
            works = search_openalex_works(query_text, per_page=per_factor)
        except Exception:
            query.status = LiteratureQueryStatus.FAILED
            query.error_message = "OpenAlex no pudo completar la consulta."
            query.completed_at = timezone.now()
            query.save(
                update_fields=[
                    "status",
                    "error_message",
                    "completed_at",
                ]
            )
            continue

        citation_count = 0
        document_count = 0
        relevance_score = 0

        for position, work in enumerate(works, start=1):
            title = work.get("display_name") or "Untitled OpenAlex work"
            source_identifier = openalex_work_identifier(work)
            citations = work.get("cited_by_count") or 0
            year = work.get("publication_year")

            if not isinstance(year, int) or year < MIN_PUBLICATION_YEAR:
                continue

            document_score = calculate_document_relevance_score(
                work,
                evaluation,
                factor,
            )

            if not is_usable_literature_result(
                title,
                source_identifier,
                document_score,
            ):
                continue

            document, created = LiteratureDocument.objects.get_or_create(
                source=LiteratureSource.OPENALEX,
                source_identifier=source_identifier,
                defaults={
                    "title": title,
                    "abstract": "",
                    "year": year,
                    "authors": openalex_authors_to_text(work),
                    "doi": openalex_work_doi(work),
                    "url": openalex_work_url(work),
                    "citation_count": citations,
                },
            )

            if not created and citations > document.citation_count:
                document.citation_count = citations
                document.save(update_fields=["citation_count"])

            QueryResult.objects.update_or_create(
                query=query,
                document=document,
                defaults={
                    "relevance_score": float(document_score),
                    "position": position,
                },
            )

            evidence, created = FactorEvidence.objects.get_or_create(
                evaluation_factor=evaluation_factor,
                document=document,
                defaults={
                    "matched_keywords": ", ".join(
                        factor.keywords.values_list("keyword", flat=True)[:5]
                    ),
                    "relevance_score": float(document_score),
                },
            )

            if not created and document_score > evidence.relevance_score:
                evidence.relevance_score = float(document_score)
                evidence.save(update_fields=["relevance_score"])

            citation_count += citations
            document_count += 1
            relevance_score += document_score
            total_documents += 1

        factor_metrics.append(
            {
                "evaluation_factor": evaluation_factor,
                "citation_count": citation_count,
                "document_count": document_count,
                "relevance_score": relevance_score,
                "subfactor_count": factor.subfactors.count(),
            }
        )

        query.status = LiteratureQueryStatus.COMPLETED
        query.total_results = document_count
        query.completed_at = timezone.now()
        query.save(
            update_fields=[
                "status",
                "total_results",
                "completed_at",
            ]
        )

    calculate_factor_importance_metrics(factor_metrics)
    update_evaluation_factors_from_importance_metrics(factor_metrics)

    evaluation.status = EvaluationStatus.SUGGESTED_READY
    evaluation.save(update_fields=["status", "updated_at"])

    return total_documents
