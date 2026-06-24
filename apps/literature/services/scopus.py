from django.utils import timezone

from apps.evaluations.models import EvaluationStatus
from apps.literature.clients.scopus import search_scopus_works
from apps.literature.constants import MIN_PUBLICATION_YEAR
from apps.literature.models import FactorEvidence, LiteratureDocument, LiteratureQuery, LiteratureQueryStatus, LiteratureSource, QueryResult

from apps.literature.services.matching import (
    build_scopus_query,
    calculate_scopus_document_relevance_score,
    is_usable_literature_result,
)

from apps.literature.services.metrics import calculate_factor_importance_metrics, update_evaluation_factors_from_importance_metrics

def scopus_entry_url(entry):
    links = entry.get("link") or []
    scopus_web_url = ""

    for link in links:
        relation = link.get("@ref") or link.get("rel")
        url = link.get("@href") or link.get("href")

        if relation == "scopus" and url:
            return url

        if url and "www.scopus.com" in url:
            scopus_web_url = url

    return scopus_web_url or entry.get("prism:url", "")


def scopus_entry_identifier(entry):
    return (
        entry.get("eid")
        or entry.get("dc:identifier")
        or entry.get("prism:doi")
        or scopus_entry_url(entry)
        or entry.get("dc:title", "")
    )


def calculate_scopus_suggested_importance_for_evaluation(evaluation, per_factor=5):
    """
    Consulta Scopus por cada factor y alimenta la IL con evidencia bibliografica.
    La IE se conserva como base de expertos definida en la tesis.
    """
    total_documents = 0
    factor_metrics = []

    for evaluation_factor in evaluation.evaluation_factors.select_related("factor"):
        factor = evaluation_factor.factor
        query_text = build_scopus_query(evaluation, factor)

        query = LiteratureQuery.objects.create(
            evaluation_factor=evaluation_factor,
            source=LiteratureSource.SCOPUS,
            query_text=query_text,
            status=LiteratureQueryStatus.RUNNING,
        )

        try:
            entries = search_scopus_works(query_text, per_page=per_factor)
        except Exception:
            query.status = LiteratureQueryStatus.FAILED
            query.error_message = "Scopus no pudo completar la consulta."
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

        for position, entry in enumerate(entries, start=1):
            title = entry.get("dc:title") or "Untitled Scopus work"
            source_identifier = scopus_entry_identifier(entry)
            citations = int(entry.get("citedby-count") or 0)
            year_text = (entry.get("prism:coverDate") or "")[:4]
            year = int(year_text) if year_text.isdigit() else None

            if year is None or year < MIN_PUBLICATION_YEAR:
                continue

            document_score = calculate_scopus_document_relevance_score(
                entry,
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
                source=LiteratureSource.SCOPUS,
                source_identifier=source_identifier,
                defaults={
                    "title": title,
                    "abstract": "",
                    "year": year,
                    "authors": entry.get("dc:creator", ""),
                    "doi": entry.get("prism:doi", ""),
                    "url": scopus_entry_url(entry),
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
