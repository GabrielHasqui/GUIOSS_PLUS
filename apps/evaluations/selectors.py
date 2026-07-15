from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.literature.models import FactorEvidence, LiteratureDocument, LiteratureQuery, QueryResult
from apps.users.permissions import is_guios_admin

from .models import Evaluation,EvaluationFactor,EvaluationSubfactor,EvaluationStatus,Factor,FodaLevel,ImportanceLevel,Recommendation,SubfactorComplianceLevel



def get_visible_evaluations_queryset(user=None):
    evaluations = Evaluation.objects.all()

    if user is None or not getattr(user, "is_authenticated", False):
        return evaluations

    if is_guios_admin(user):
        return evaluations

    return evaluations.filter(created_by=user)


def get_active_evaluation(user=None):
    return get_visible_evaluations_queryset(user).order_by("-updated_at", "-created_at").first()


def get_blocking_evaluation(user=None):
    return (
        get_visible_evaluations_queryset(user)
        .exclude(status=EvaluationStatus.COMPLETED)
        .order_by("-updated_at", "-created_at")
        .first()
    )


def get_evaluation(evaluation_id, user=None):
    return get_object_or_404(
        get_visible_evaluations_queryset(user),
        pk=evaluation_id,
    )


def get_continue_route(evaluation):
    if evaluation.status == EvaluationStatus.SUBFACTORS_READY:
        return "result"
    if evaluation.status == EvaluationStatus.FACTORS_READY:
        return "subfactors"
    return "factors"


def get_active_evaluation_progress_summary(evaluation):
    if not evaluation:
        return []

    evaluation_factors = EvaluationFactor.objects.filter(evaluation=evaluation)
    total_factors = evaluation_factors.count()
    relevant_factors = evaluation_factors.filter(is_relevant=True)
    relevant_factor_count = relevant_factors.count()

    suggested_ready_count = evaluation_factors.exclude(
        suggested_importance__isnull=True,
    ).count()
    factors_reviewed_count = evaluation_factors.exclude(
        decision_maker_importance__isnull=True,
    ).count()
    relevant_classified_count = relevant_factors.exclude(
        mean_weight__isnull=True,
    ).count()
    result_ready_count = 1 if evaluation.status == EvaluationStatus.COMPLETED else 0

    progress_items = [
        {
            "label": "Importancia sugerida disponible",
            "count": suggested_ready_count,
            "total": total_factors,
        },
        {
            "label": "Factores revisados por el decisor",
            "count": factors_reviewed_count,
            "total": total_factors,
        },
        {
            "label": "Factores relevantes clasificados",
            "count": relevant_classified_count,
            "total": relevant_factor_count,
        },
        {
            "label": "Resultado final generado",
            "count": result_ready_count,
            "total": 1,
        },
    ]

    for item in progress_items:
        item["percent"] = round((item["count"] / item["total"]) * 100) if item["total"] else 0

    return progress_items


def get_dashboard_context_data(user=None):
    visible_evaluations = get_visible_evaluations_queryset(user)
    latest_evaluation = get_active_evaluation(user)
    blocking_evaluation = get_blocking_evaluation(user)
    evaluation = blocking_evaluation or latest_evaluation
    evaluations = visible_evaluations
    total_evaluations = evaluations.count()
    evaluated_factors = EvaluationFactor.objects.none()

    if evaluation:
        evaluated_factors = (
            EvaluationFactor.objects.filter(evaluation=evaluation)
            .select_related("factor", "factor__dimension")
        )

    return {
        "active_nav": "dashboard",
        "evaluation": evaluation,
        "total_factors": Factor.objects.count(),
        "total_evaluations": total_evaluations,
        "completed_evaluations": evaluations.filter(
            status=EvaluationStatus.COMPLETED,
        ).count(),
        "unique_software_count": (
            evaluations.exclude(software_name="")
            .values("software_name")
            .distinct()
            .count()
        ),
        "literature_document_count": LiteratureDocument.objects.count(),
        "factors_with_decision": evaluated_factors.exclude(
            decision_maker_importance__isnull=True
        ).count(),
        "relevant_count": evaluated_factors.filter(is_relevant=True).count(),
        "evaluation_status_display": (
            EvaluationStatus(evaluation.status).label if evaluation else None
        ),
        "evaluation_progress_summary": get_active_evaluation_progress_summary(evaluation),
        "blocking_evaluation": blocking_evaluation,
        "can_create_evaluation": blocking_evaluation is None,
        "continue_route": get_continue_route(evaluation) if evaluation else "factors",
        "recent_evaluations": (
            evaluations.select_related("recommendation", "created_by")
            .order_by("-updated_at", "-created_at")[:2]
        ),
    }


def get_factors_context_data(evaluation):
    evidence_queryset = FactorEvidence.objects.select_related("document")
    evaluation_factors = (
        EvaluationFactor.objects.filter(evaluation=evaluation)
        .select_related("factor", "factor__dimension")
        .prefetch_related(Prefetch("evidence_items", queryset=evidence_queryset))
    )
    dimensions = sorted(
        {
            evaluation_factor.factor.dimension.name
            for evaluation_factor in evaluation_factors
        }
    )

    return {
        "active_nav": "factors",
        "evaluation": evaluation,
        "evaluation_factors": evaluation_factors,
        "dimensions": dimensions,
        "importance_levels": ImportanceLevel.choices,
    }


def get_relevant_factors(evaluation):
    return (
        EvaluationFactor.objects.filter(evaluation=evaluation, is_relevant=True)
        .select_related("factor", "factor__dimension")
    )


def get_selected_relevant_factor(relevant_factors, selected_factor_id):
    if selected_factor_id:
        selected_factor = relevant_factors.filter(pk=selected_factor_id).first()
        if selected_factor is not None:
            return selected_factor

    return relevant_factors.first()


def get_factor_name_for_evaluation_factor(evaluation_factor):
    return Factor.objects.only("name").get(pk=evaluation_factor.factor_id).name


def has_incomplete_relevant_subfactors(evaluation):
    return EvaluationFactor.objects.filter(
        evaluation=evaluation,
        is_relevant=True,
        mean_weight__isnull=True,
    ).exists()


def get_subfactors_context_data(evaluation, selected_factor):
    return {
        "active_nav": "subfactors",
        "evaluation": evaluation,
        "relevant_factors": get_relevant_factors(evaluation),
        "selected_factor": selected_factor,
        "selected_subfactors": (
            EvaluationSubfactor.objects.filter(evaluation_factor=selected_factor)
            .select_related("subfactor")
        ),
        "compliance_levels": SubfactorComplianceLevel.choices,
        "all_subfactors_complete": not has_incomplete_relevant_subfactors(evaluation),
    }


def get_result_factors(evaluation):
    return (
        EvaluationFactor.objects.filter(evaluation=evaluation, is_relevant=True)
        .select_related("factor", "factor__dimension")
        .prefetch_related("evaluation_subfactors__subfactor")
        .order_by("factor__dimension__name", "factor__name")
    )


def get_foda_counts(evaluation_factors):
    return {
        "fortalezas": evaluation_factors.filter(foda="Fortaleza").count(),
        "oportunidades": evaluation_factors.filter(foda="Oportunidad").count(),
        "debilidades": evaluation_factors.filter(foda="Debilidad").count(),
        "amenazas": evaluation_factors.filter(foda="Amenaza").count(),
    }


def get_result_explanation_rule(evaluation_factor):
    if evaluation_factor.selected_scope == "Interno":
        if evaluation_factor.mean_weight >= 3:
            return "Factor interno con PM mayor o igual a 3, por lo tanto se clasifica como Fortaleza."
        return "Factor interno con PM menor a 3, por lo tanto se clasifica como Debilidad."

    if evaluation_factor.selected_scope == "Externo":
        if evaluation_factor.mean_weight >= 3:
            return "Factor externo con PM mayor o igual a 3, por lo tanto se clasifica como Oportunidad."
        return "Factor externo con PM menor a 3, por lo tanto se clasifica como Amenaza."

    return "El alcance del factor no permite explicar la clasificacion."


def get_result_summaries(result_factors):
    summaries = []

    for evaluation_factor in result_factors:
        subfactors = list(evaluation_factor.evaluation_subfactors.all())
        values = [subfactor.compliance for subfactor in subfactors]
        formula = " + ".join(str(value) for value in values)
        factor_label = evaluation_factor.factor.name

        if evaluation_factor.foda == FodaLevel.FORTALEZA:
            explanation = (
                f"{factor_label} se clasifica como Fortaleza porque su alcance es "
                f"{evaluation_factor.selected_scope.lower()} y su PM es "
                f"{evaluation_factor.mean_weight:.1f}."
            )
        elif evaluation_factor.foda == FodaLevel.OPORTUNIDAD:
            explanation = (
                f"{factor_label} se clasifica como Oportunidad porque su alcance es "
                f"{evaluation_factor.selected_scope.lower()} y su PM es "
                f"{evaluation_factor.mean_weight:.1f}."
            )
        elif evaluation_factor.foda == FodaLevel.DEBILIDAD:
            explanation = (
                f"{factor_label} se clasifica como Debilidad porque su alcance es "
                f"{evaluation_factor.selected_scope.lower()} y su PM es "
                f"{evaluation_factor.mean_weight:.1f}."
            )
        else:
            explanation = (
                f"{factor_label} se clasifica como Amenaza porque su alcance es "
                f"{evaluation_factor.selected_scope.lower()} y su PM es "
                f"{evaluation_factor.mean_weight:.1f}."
            )

        summaries.append(
            {
                "evaluation_factor": evaluation_factor,
                "subfactors": subfactors,
                "formula": formula,
                "subfactor_count": len(subfactors),
                "explanation": explanation,
                "rule_text": get_result_explanation_rule(evaluation_factor),
            }
        )

    return summaries


def get_recommendation_reason(result_factors, recommendation):
    if recommendation.code == "C":
        critical_negative = [
            evaluation_factor.factor.name
            for evaluation_factor in result_factors
            if evaluation_factor.foda in [FodaLevel.DEBILIDAD, FodaLevel.AMENAZA]
            and evaluation_factor.relative_importance in [
                ImportanceLevel.IMPORTANTE,
                ImportanceLevel.FUNDAMENTAL,
            ]
        ]
        return (
            "La recomendacion C se genera porque existen debilidades o amenazas en "
            "factores importantes o fundamentales: "
            + ", ".join(critical_negative)
            + "."
        )

    if recommendation.code == "B":
        optional_negative = [
            evaluation_factor.factor.name
            for evaluation_factor in result_factors
            if evaluation_factor.foda in [FodaLevel.DEBILIDAD, FodaLevel.AMENAZA]
            and evaluation_factor.relative_importance == ImportanceLevel.OPCIONAL
        ]
        return (
            "La recomendacion B se genera porque existen debilidades o amenazas en "
            "factores cuya importancia relativa es opcional: "
            + ", ".join(optional_negative)
            + "."
        )

    return (
        "La recomendacion A se genera porque todos los factores relevantes "
        "evaluados quedaron clasificados como fortalezas u oportunidades."
    )


def get_result_context_data(evaluation):
    result_factors_queryset = get_result_factors(evaluation)
    result_factors = list(result_factors_queryset)
    recommendation = Recommendation.objects.get(evaluation=evaluation)

    return {
        "active_nav": "result",
        "evaluation": evaluation,
        "result_factors": result_factors,
        "recommendation": recommendation,
        "result_summaries": get_result_summaries(result_factors),
        "recommendation_reason": get_recommendation_reason(result_factors, recommendation),
        **get_foda_counts(result_factors_queryset),
    }


def get_software_history_data(user=None):
    evaluations = get_visible_evaluations_queryset(user).order_by("-updated_at", "-created_at")
    history_items = []

    for evaluation in evaluations:
        relevant_factors = EvaluationFactor.objects.filter(
            evaluation=evaluation,
            is_relevant=True,
        )
        recommendation = Recommendation.objects.filter(evaluation=evaluation).first()
        history_items.append(
            {
                "evaluation": evaluation,
                "status_display": EvaluationStatus(evaluation.status).label,
                "recommendation": recommendation,
                "created_by_display": (
                    evaluation.created_by.get_full_name().strip()
                    or evaluation.created_by.email
                    or evaluation.created_by.username
                ),
                "fortalezas": relevant_factors.filter(foda="Fortaleza").count(),
                "oportunidades": relevant_factors.filter(foda="Oportunidad").count(),
                "debilidades": relevant_factors.filter(foda="Debilidad").count(),
                "amenazas": relevant_factors.filter(foda="Amenaza").count(),
            }
        )

    contexts = sorted(
        {
            item["evaluation"].context
            for item in history_items
            if item["evaluation"].context
        }
    )

    return {
        "history_items": history_items,
        "contexts": contexts,
    }


def get_history_detail_context_data(evaluation):
    factor_queryset = (
        EvaluationFactor.objects.filter(evaluation=evaluation)
        .select_related("factor", "factor__dimension")
        .prefetch_related(
            Prefetch(
                "evidence_items",
                queryset=FactorEvidence.objects.select_related("document"),
            )
        )
        .order_by("factor__dimension__name", "factor__name")
    )
    factor_summaries = []

    for evaluation_factor in factor_queryset:
        evidence_items = FactorEvidence.objects.filter(
            evaluation_factor=evaluation_factor,
        ).select_related("document")
        documents = {
            evidence.document.pk: evidence.document
            for evidence in evidence_items
        }
        citation_count = sum(document.citation_count for document in documents.values())

        factor_summaries.append(
            {
                "evaluation_factor": evaluation_factor,
                "evidence_items": evidence_items,
                "document_count": len(documents),
                "citation_count": citation_count,
            }
        )

    relevant_factors = factor_queryset.filter(is_relevant=True)

    return {
        "active_nav": "history",
        "evaluation": evaluation,
        "evaluation_status_display": EvaluationStatus(evaluation.status).label,
        "created_by_display": (
            evaluation.created_by.get_full_name().strip()
            or evaluation.created_by.email
            or evaluation.created_by.username
        ),
        "factor_summaries": factor_summaries,
        "dimensions": sorted(
            {
                summary["evaluation_factor"].factor.dimension.name
                for summary in factor_summaries
            }
        ),
        "recommendation": getattr(evaluation, "recommendation", None),
        "relevant_count": relevant_factors.count(),
        **get_foda_counts(relevant_factors),
        "query_count": LiteratureQuery.objects.filter(
            evaluation_factor__evaluation=evaluation,
        ).count(),
        "document_count": QueryResult.objects.filter(
            query__evaluation_factor__evaluation=evaluation,
        ).values("document_id").distinct().count(),
    }


def get_report_code(evaluation):
    return f"GUIOS-{timezone.localtime(evaluation.updated_at).year}-{evaluation.pk:04d}"


def get_recommendation_title(code):
    recommendation_titles = {
        "A": "Adopcion recomendada",
        "B": "Adopcion con observaciones",
        "C": "Adopcion condicionada",
    }
    return recommendation_titles.get(code, "Resultado de evaluacion")


def get_evaluation_report_context_data(evaluation):
    history_context = get_history_detail_context_data(evaluation)
    factor_summaries = history_context["factor_summaries"]
    relevant_summaries = [
        summary
        for summary in factor_summaries
        if summary["evaluation_factor"].is_relevant
    ]
    recommendation = history_context["recommendation"]

    foda_groups = {
        "Fortaleza": [],
        "Oportunidad": [],
        "Debilidad": [],
        "Amenaza": [],
    }

    for summary in relevant_summaries:
        evaluation_factor = summary["evaluation_factor"]
        if evaluation_factor.foda in foda_groups:
            foda_groups[evaluation_factor.foda].append(summary)

    return {
        "evaluation": evaluation,
        "evaluation_status_display": history_context["evaluation_status_display"],
        "recommendation": recommendation,
        "recommendation_title": (
            get_recommendation_title(recommendation.code)
            if recommendation
            else "Resultado pendiente"
        ),
        "report_code": get_report_code(evaluation),
        "issued_at": timezone.localtime(evaluation.updated_at),
        "factor_summaries": factor_summaries,
        "relevant_summaries": relevant_summaries,
        "relevant_factor_count": history_context["relevant_count"],
        "evaluated_factor_count": len(relevant_summaries),
        "query_count": history_context["query_count"],
        "document_count": history_context["document_count"],
        "fortalezas": history_context["fortalezas"],
        "oportunidades": history_context["oportunidades"],
        "debilidades": history_context["debilidades"],
        "amenazas": history_context["amenazas"],
        "foda_groups": foda_groups,
    }
