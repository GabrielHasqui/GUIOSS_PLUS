from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Evaluation, EvaluationFactor,Recommendation,Scope,Subfactor,EvaluationSubfactor,EvaluationStatus,ImportanceLevel,FodaLevel,Factor,SubfactorComplianceLevel

from .selectors import get_blocking_evaluation, has_incomplete_relevant_subfactors

from apps.literature.services import calculate_openalex_suggested_importance_for_evaluation,calculate_scopus_suggested_importance_for_evaluation,recalculate_suggested_importance_from_evidence

def calculate_relative_importance(suggested_importance, decision_maker_importance):
    if suggested_importance is None or decision_maker_importance is None:
        return None

    suggested_index = int(suggested_importance) - 1
    decision_index = int(decision_maker_importance) - 1
    result_index = (suggested_index + decision_index) // 2

    return result_index + 1


def is_relevant(relative_importance):
    if relative_importance is None:
        return False

    return int(relative_importance) > ImportanceLevel.IRRELEVANTE


def calculate_mean_weight(compliances):
    if not compliances:
        return None

    return sum(int(value) for value in compliances) / len(compliances)


def classify_foda(mean_weight, scope):
    if mean_weight is None:
        return ""

    if scope == Scope.INTERNO:
        if mean_weight >= 3:
            return FodaLevel.FORTALEZA
        return FodaLevel.DEBILIDAD

    if scope == Scope.EXTERNO:
        if mean_weight >= 3:
            return FodaLevel.OPORTUNIDAD
        return FodaLevel.AMENAZA

    return ""


def generate_recommendation_text(evaluation):
    evaluated_factors = evaluation.evaluation_factors.exclude(foda="")

    if not evaluated_factors.exists():
        return (
            "",
            "No hay factores relevantes evaluados para generar una recomendación.",
        )

    has_critical_negative = evaluated_factors.filter(
        foda__in=[FodaLevel.AMENAZA, FodaLevel.DEBILIDAD],
        relative_importance__in=[
            ImportanceLevel.IMPORTANTE,
            ImportanceLevel.FUNDAMENTAL,
        ],
    ).exists()

    has_optional_negative = evaluated_factors.filter(
        foda__in=[FodaLevel.AMENAZA, FodaLevel.DEBILIDAD],
        relative_importance=ImportanceLevel.OPCIONAL,
    ).exists()

    if has_critical_negative:
        return (
            "C",
            "Recomendación C: La organización debe proporcionar los recursos "
            "necesarios que garanticen una adopción satisfactoria. Si se trata "
            "de factores internos, deben ser aspectos a mejorar dentro de la "
            "organización; si son factores externos, se recomienda dedicar "
            "recursos de ingeniería para mejorar el software.",
        )

    if has_optional_negative:
        return (
            "B",
            "Recomendación B: Es posible adoptar. A pesar de que se han "
            "detectado amenazas y/o debilidades en factores cuya importancia "
            "relativa es opcional, se sugiere revisar los criterios que no "
            "cumplen con lo mínimo requerido para adoptar.",
        )

    return (
        "A",
        "Recomendación A: Adoptar. Todos los factores han sido identificados "
        "como oportunidades y/o fortalezas. Esto quiere decir que la organización "
        "cumple satisfactoriamente con la mayoría de requisitos para adoptar la "
        "solución FLOSS.",
    )


def initialize_evaluation_factors(evaluation):
    """
    Crea los 18 factores evaluados para una evaluación.
    Usa la importancia sugerida base mientras no exista cálculo automático.
    """
    for factor in Factor.objects.all():
        EvaluationFactor.objects.get_or_create(
            evaluation=evaluation,
            factor=factor,
            defaults={
                "suggested_importance": factor.default_suggested_importance,
                "selected_scope": (
                    Scope.INTERNO if factor.scope == Scope.AMBOS else factor.scope
                ),
            },
        )


def create_evaluation_with_sources(user, software_name, context, description, selected_sources):
    
    blocking_evaluation = get_blocking_evaluation(user)

    if blocking_evaluation:
        return {
            "evaluation": blocking_evaluation,
            "blocked": True,
            "processed_documents": 0,
        }

    evaluation = Evaluation.objects.create(
        software_name=software_name.strip(),
        context=context.strip(),
        description=description.strip(),
        created_by=user,
    )

    total = 0

    if "openalex" in selected_sources:
        total = calculate_openalex_suggested_importance_for_evaluation(evaluation)

    if "scopus" in selected_sources:
        total += calculate_scopus_suggested_importance_for_evaluation(evaluation)

    if selected_sources:
        total = recalculate_suggested_importance_from_evidence(evaluation)

    return {
        "evaluation": evaluation,
        "blocked": False,
        "processed_documents": total,
    }


def reopen_completed_evaluation(evaluation, reopened_by):
    if evaluation.status != EvaluationStatus.COMPLETED:
        raise ValidationError("Solo se pueden reabrir evaluaciones completadas.")

    Recommendation.objects.filter(evaluation=evaluation).delete()
    evaluation.status = EvaluationStatus.FACTORS_READY
    evaluation.reopened_by = reopened_by
    evaluation.reopened_at = timezone.now()
    evaluation.reopen_reason = ""
    evaluation.save(
        update_fields=[
            "status",
            "reopened_by",
            "reopened_at",
            "reopen_reason",
            "updated_at",
        ]
    )


def update_evaluation_factor_relative_importance(evaluation_factor):
    relative_importance = calculate_relative_importance(
        evaluation_factor.suggested_importance,
        evaluation_factor.decision_maker_importance,
    )

    evaluation_factor.relative_importance = relative_importance
    evaluation_factor.is_relevant = is_relevant(relative_importance)
    evaluation_factor.save(
        update_fields=[
            "relative_importance",
            "is_relevant",
        ]
    )


def save_factor_decision_importance(evaluation, post_data):
    if evaluation.status == EvaluationStatus.COMPLETED:
        raise ValidationError("La evaluacion ya fue completada y no puede modificarse.")

    for evaluation_factor in EvaluationFactor.objects.filter(evaluation=evaluation):
        field_name = f"decision_maker_importance_{evaluation_factor.pk}"
        value = post_data.get(field_name)

        if not value:
            continue

        try:
            importance = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("La importancia seleccionada no es valida.") from exc

        if importance not in ImportanceLevel.values:
            raise ValidationError("La importancia seleccionada no es valida.")

        evaluation_factor.decision_maker_importance = importance
        evaluation_factor.save(update_fields=["decision_maker_importance"])
        update_evaluation_factor_relative_importance(evaluation_factor)
        initialize_relevant_subfactors(evaluation_factor)

    Evaluation.objects.filter(pk=evaluation.pk).update(updated_at=timezone.now())


def evaluation_has_relevant_factors(evaluation):
    return EvaluationFactor.objects.filter(
        evaluation=evaluation,
        is_relevant=True,
    ).exists()


def initialize_relevant_subfactors(evaluation_factor):
    if not evaluation_factor.is_relevant:
        EvaluationSubfactor.objects.filter(evaluation_factor=evaluation_factor).delete()
        return

    for subfactor in Subfactor.objects.filter(factor_id=evaluation_factor.factor_id):
        EvaluationSubfactor.objects.get_or_create(
            evaluation_factor=evaluation_factor,
            subfactor=subfactor,
        )


def update_factor_mean_weight_and_foda(evaluation_factor):
    compliances = list(
        EvaluationSubfactor.objects.filter(evaluation_factor=evaluation_factor).values_list(
            "compliance",
            flat=True,
        )
    )

    mean_weight = calculate_mean_weight(compliances)
    foda = classify_foda(mean_weight, evaluation_factor.selected_scope)

    evaluation_factor.mean_weight = mean_weight
    evaluation_factor.foda = foda
    evaluation_factor.save(
        update_fields=[
            "mean_weight",
            "foda",
        ]
    )


def save_subfactor_compliance(evaluation, selected_factor, post_data):
    if evaluation.status == EvaluationStatus.COMPLETED:
        raise ValidationError("La evaluacion ya fue completada y no puede modificarse.")

    evaluation_subfactors = list(EvaluationSubfactor.objects.filter(
        evaluation_factor=selected_factor,
    ))
    values_to_save = []

    for evaluation_subfactor in evaluation_subfactors:
        field_name = f"compliance_{evaluation_subfactor.pk}"
        value = post_data.get(field_name)

        if value is None:
            raise ValidationError("Debe evaluar todos los subfactores del factor.")

        try:
            compliance = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("El nivel de cumplimiento no es valido.") from exc

        if compliance not in SubfactorComplianceLevel.values:
            raise ValidationError("El nivel de cumplimiento no es valido.")

        values_to_save.append((evaluation_subfactor.pk, compliance))

    for evaluation_subfactor_id, compliance in values_to_save:
        EvaluationSubfactor.objects.filter(pk=evaluation_subfactor_id).update(
            compliance=compliance
        )

    update_factor_mean_weight_and_foda(selected_factor)

    if not has_incomplete_relevant_subfactors(evaluation):
        evaluation.status = EvaluationStatus.SUBFACTORS_READY
        evaluation.save(update_fields=["status", "updated_at"])
    else:
        Evaluation.objects.filter(pk=evaluation.pk).update(updated_at=timezone.now())


def save_single_subfactor_compliance(evaluation, evaluation_subfactor_id, compliance_value):
    if evaluation.status == EvaluationStatus.COMPLETED:
        raise ValidationError("La evaluacion ya fue completada y no puede modificarse.")

    try:
        compliance = int(compliance_value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("El nivel de cumplimiento no es valido.") from exc

    if compliance not in SubfactorComplianceLevel.values:
        raise ValidationError("El nivel de cumplimiento no es valido.")

    evaluation_subfactor = (
        EvaluationSubfactor.objects.select_related("evaluation_factor")
        .filter(
            pk=evaluation_subfactor_id,
            evaluation_factor__evaluation=evaluation,
            evaluation_factor__is_relevant=True,
        )
        .first()
    )
    if evaluation_subfactor is None:
        raise ValidationError("El subfactor no pertenece a esta evaluacion.")

    EvaluationSubfactor.objects.filter(pk=evaluation_subfactor.pk).update(
        compliance=compliance
    )
    update_factor_mean_weight_and_foda(evaluation_subfactor.evaluation_factor)
    evaluation_subfactor.evaluation_factor.refresh_from_db(
        fields=["mean_weight", "foda"]
    )

    if not has_incomplete_relevant_subfactors(evaluation):
        evaluation.status = EvaluationStatus.SUBFACTORS_READY
        evaluation.save(update_fields=["status", "updated_at"])
    else:
        Evaluation.objects.filter(pk=evaluation.pk).update(updated_at=timezone.now())

    return evaluation_subfactor.evaluation_factor


def update_recommendation(evaluation):
    relevant_factors = evaluation.evaluation_factors.filter(is_relevant=True)

    if (
        not relevant_factors.exists()
        or relevant_factors.filter(mean_weight__isnull=True).exists()
    ):
        return None

    code, text = generate_recommendation_text(evaluation)

    Recommendation.objects.update_or_create(
        evaluation=evaluation,
        defaults={
            "code": code,
            "text": text,
        },
    )

    evaluation.status = EvaluationStatus.COMPLETED
    evaluation.save(update_fields=["status", "updated_at"])

    return code, text
