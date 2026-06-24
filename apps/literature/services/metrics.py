from math import ceil, floor

from apps.evaluations.models import EvaluationFactor, EvaluationStatus, ImportanceLevel, Subfactor
from apps.literature.constants import MIN_PUBLICATION_YEAR
from apps.literature.models import FactorEvidence, LiteratureQueryStatus


THESIS_BASE_EXPERT_IMPORTANCE = ImportanceLevel.IMPORTANTE


def calculate_suggested_importance(literature_importance, expert_importance):
    """
    Mantiene la lógica de GUIOS:
    IS se obtiene combinando IL e IE con la matriz de la tesis.
    """
    literature_index = int(literature_importance) - 1
    expert_index = int(expert_importance) - 1
    result_index = (literature_index + expert_index) // 2

    return result_index + 1


def calculate_literature_ratio(reference_count, subfactor_count):
    """
    Formula 5.1 de la tesis: ri = ci / n.
    ci es la cantidad de referencias encontradas para el factor y n su numero
    de subfactores. No se usa el contador bibliometrico de citas de cada obra.
    """
    if subfactor_count <= 0:
        return 0

    return reference_count / subfactor_count


def get_thesis_base_expert_importance():
    """
    La IE real proviene de expertos, no de Scopus/OpenAlex.
    GUIOS+ usa como base el valor IE=3 de la Tabla 5.3 de la tesis.
    """
    return THESIS_BASE_EXPERT_IMPORTANCE


def calculate_quartile_thresholds(values):
    """
    Replica la asignacion por cuartiles descrita para IL en la tesis.
    Devuelve los valores maximos de cada cuartil: rq1, rq2 y rq3.
    """
    ordered_values = sorted(values)

    if not ordered_values:
        return []

    count = len(ordered_values)
    threshold_indexes = [
        max(ceil(count * 0.25) - 1, 0),
        max(floor(count * 0.50) - 1, 0),
        max(floor(count * 0.75) - 1, 0),
    ]

    return [ordered_values[index] for index in threshold_indexes]


def assign_quartile_importance(value, thresholds):
    if value <= 0 or not thresholds:
        return ImportanceLevel.IRRELEVANTE

    first, second, third = thresholds

    if value <= first:
        return ImportanceLevel.IRRELEVANTE

    if value <= second:
        return ImportanceLevel.OPCIONAL

    if value <= third:
        return ImportanceLevel.IMPORTANTE

    return ImportanceLevel.FUNDAMENTAL


def calculate_literature_importance_from_metrics(
    citation_count,
    subfactor_count,
    thresholds,
):
    ratio = calculate_literature_ratio(citation_count, subfactor_count)
    return assign_quartile_importance(ratio, thresholds)


def calculate_factor_importance_metrics(factor_metrics):
    """
    Las APIs alimentan la IL con documentos/citas. La IE no se infiere desde
    APIs; se conserva como base de expertos definida por la tesis.
    """
    literature_ratios = [
        calculate_literature_ratio(
            metrics["document_count"],
            metrics["subfactor_count"],
        )
        for metrics in factor_metrics
    ]
    literature_thresholds = calculate_quartile_thresholds(literature_ratios)

    for metrics in factor_metrics:
        literature_importance = calculate_literature_importance_from_metrics(
            metrics["document_count"],
            metrics["subfactor_count"],
            literature_thresholds,
        )
        expert_importance = metrics.get(
            "expert_importance",
            get_thesis_base_expert_importance(),
        )

        metrics["literature_importance"] = literature_importance
        metrics["expert_importance"] = expert_importance
        metrics["suggested_importance"] = calculate_suggested_importance(
            literature_importance,
            expert_importance,
        )

    return factor_metrics


def update_evaluation_factors_from_importance_metrics(factor_metrics):
    from apps.evaluations.services import (
        initialize_relevant_subfactors,
        update_evaluation_factor_relative_importance,
    )

    for metrics in factor_metrics:
        evaluation_factor = metrics["evaluation_factor"]
        evaluation_factor.literature_importance = metrics["literature_importance"]
        evaluation_factor.expert_importance = metrics["expert_importance"]
        evaluation_factor.suggested_importance = metrics["suggested_importance"]
        evaluation_factor.save(
            update_fields=[
                "literature_importance",
                "expert_importance",
                "suggested_importance",
            ]
        )

        if evaluation_factor.decision_maker_importance is not None:
            update_evaluation_factor_relative_importance(evaluation_factor)
            initialize_relevant_subfactors(evaluation_factor)


def recalculate_suggested_importance_from_evidence(evaluation):
    """
    Recalcula IL e IS con toda la evidencia guardada para la evaluacion.
    La IE se conserva como base de expertos de la tesis, porque no se obtiene
    desde las APIs bibliograficas.
    """
    evaluation_factors = list(
        EvaluationFactor.objects.filter(evaluation=evaluation)
        .select_related("factor")
        .prefetch_related("literature_queries")
    )

    # Si una consulta fallo no se debe convertir la ausencia tecnica de datos
    # en IL=1. En ese caso se conservan los valores sugeridos del GUIOS original.
    has_complete_coverage = all(
        any(
            query.status == LiteratureQueryStatus.COMPLETED
            for query in evaluation_factor.literature_queries.all()
        )
        for evaluation_factor in evaluation_factors
    )

    if not has_complete_coverage:
        for evaluation_factor in evaluation_factors:
            evaluation_factor.literature_importance = None
            evaluation_factor.expert_importance = None
            evaluation_factor.suggested_importance = (
                evaluation_factor.factor.default_suggested_importance
            )
            evaluation_factor.save(
                update_fields=[
                    "literature_importance",
                    "expert_importance",
                    "suggested_importance",
                ]
            )

        evaluation.status = EvaluationStatus.SUGGESTED_READY
        evaluation.save(update_fields=["status", "updated_at"])
        return 0

    factor_metrics = []

    for evaluation_factor in evaluation_factors:
        citation_count = 0
        relevance_score = 0
        reference_keys = set()

        for evidence in FactorEvidence.objects.filter(
            evaluation_factor=evaluation_factor,
        ).select_related("document"):
            if (
                evidence.document.year is None
                or evidence.document.year < MIN_PUBLICATION_YEAR
            ):
                continue

            citation_count += evidence.document.citation_count
            relevance_score += evidence.relevance_score
            normalized_doi = evidence.document.doi.strip().lower().removeprefix(
                "https://doi.org/"
            )
            if normalized_doi:
                reference_key = ("doi", normalized_doi)
            else:
                reference_key = (
                    "title",
                    " ".join(evidence.document.title.lower().split()),
                    evidence.document.year,
                )
            reference_keys.add(reference_key)

        factor_metrics.append(
            {
                "evaluation_factor": evaluation_factor,
                "citation_count": citation_count,
                "document_count": len(reference_keys),
                "relevance_score": relevance_score,
                "subfactor_count": Subfactor.objects.filter(
                    factor_id=evaluation_factor.factor.pk,
                ).count(),
            }
        )

    calculate_factor_importance_metrics(factor_metrics)
    update_evaluation_factors_from_importance_metrics(factor_metrics)

    evaluation.status = EvaluationStatus.SUGGESTED_READY
    evaluation.save(update_fields=["status", "updated_at"])

    return sum(metrics["document_count"] for metrics in factor_metrics)
