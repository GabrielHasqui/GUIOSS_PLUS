from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..selectors import get_evaluation,get_factor_name_for_evaluation_factor,get_factors_context_data,get_relevant_factors,get_result_context_data,get_selected_relevant_factor,get_subfactors_context_data,has_incomplete_relevant_subfactors
from ..services import evaluation_has_relevant_factors,initialize_relevant_subfactors,save_factor_decision_importance,save_subfactor_compliance,update_recommendation

@login_required
def factors(request, evaluation_id):
    evaluation = get_evaluation(evaluation_id, request.user)

    if request.method == "POST":
        try:
            save_factor_decision_importance(evaluation, request.POST)
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
            return redirect("factors", evaluation_id=evaluation.pk)

        if request.POST.get("action") == "continue":
            if evaluation_has_relevant_factors(evaluation):
                messages.success(
                    request,
                    "Importancia del decisor actualizada. Continua con subfactores.",
                )
                return redirect("subfactors", evaluation_id=evaluation.pk)

            messages.warning(
                request,
                "Debe definir la importancia del decisor para generar factores relevantes antes de continuar.",
            )
            return redirect("factors", evaluation_id=evaluation.pk)

        messages.success(request, "Importancia del decisor actualizada.")
        return redirect("factors", evaluation_id=evaluation.pk)

    return render(
        request,
        "evaluations/workflow/factors.html",
        get_factors_context_data(evaluation),
    )


@login_required
def subfactors(request, evaluation_id):
    evaluation = get_evaluation(evaluation_id, request.user)
    relevant_factors = get_relevant_factors(evaluation)

    if not relevant_factors.exists():
        messages.warning(
            request,
            "No hay factores relevantes. Primero completa la importancia del decisor.",
        )
        return redirect("factors", evaluation_id=evaluation.pk)

    selected_factor = get_selected_relevant_factor(
        relevant_factors,
        request.GET.get("factor"),
    )
    initialize_relevant_subfactors(selected_factor)
    selected_factor_pk = getattr(selected_factor, "pk")
    selected_factor_name = get_factor_name_for_evaluation_factor(selected_factor)

    if request.method == "POST":
        try:
            save_subfactor_compliance(evaluation, selected_factor, request.POST)
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
            return redirect(f"{request.path}?factor={selected_factor_pk}")
        messages.success(
            request,
            f"Subfactores de {selected_factor_name} guardados.",
        )
        return redirect(f"{request.path}?factor={selected_factor_pk}")

    return render(
        request,
        "evaluations/workflow/subfactors.html",
        get_subfactors_context_data(evaluation, selected_factor),
    )


@login_required
def result(request, evaluation_id):
    evaluation = get_evaluation(evaluation_id, request.user)
    relevant_factors = get_relevant_factors(evaluation)

    if not relevant_factors.exists():
        messages.warning(
            request,
            "No hay factores relevantes evaluados. Primero completa la importancia del decisor.",
        )
        return redirect("factors", evaluation_id=evaluation.pk)

    if has_incomplete_relevant_subfactors(evaluation):
        messages.warning(
            request,
            "Debes guardar los subfactores de todos los factores relevantes antes de ver el resultado.",
        )
        return redirect("subfactors", evaluation_id=evaluation.pk)

    recommendation = getattr(evaluation, "recommendation", None)

    if request.method == "POST":
        if update_recommendation(evaluation) is None:
            messages.warning(
                request,
                "La evaluacion aun no tiene datos suficientes para generar el resultado.",
            )
            return redirect("factors", evaluation_id=evaluation.pk)
        return redirect("result", evaluation_id=evaluation.pk)

    if recommendation is None:
        messages.warning(
            request,
            "Genera el resultado desde el ultimo paso de subfactores.",
        )
        return redirect("subfactors", evaluation_id=evaluation.pk)

    return render(
        request,
        "evaluations/workflow/result.html",
        get_result_context_data(evaluation),
    )
