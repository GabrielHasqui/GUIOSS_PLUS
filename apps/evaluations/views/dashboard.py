from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import EvaluationCreateForm
from ..selectors import get_dashboard_context_data
from ..services import create_evaluation_with_sources


@login_required
def dashboard(request):
    context = get_dashboard_context_data(request.user)
    context["evaluation_form"] = EvaluationCreateForm()
    return render(request, "evaluations/dashboard/dashboard.html", context)


@login_required
@require_POST
def create_evaluation(request):
    form = EvaluationCreateForm(request.POST)

    if not form.is_valid():
        context = get_dashboard_context_data(request.user)
        context.update(
            {
                "evaluation_form": form,
                "open_evaluation_modal": True,
            }
        )
        return render(
            request,
            "evaluations/dashboard/dashboard.html",
            context,
            status=400,
        )

    creation_lock_key = f"guios:evaluation-create:{request.user.pk}"
    if not cache.add(creation_lock_key, True, timeout=120):
        messages.warning(
            request,
            "Ya se esta procesando una evaluacion para tu cuenta.",
        )
        return redirect("dashboard")

    try:
        result = create_evaluation_with_sources(
            user=request.user,
            software_name=form.cleaned_data["software_name"],
            context=form.cleaned_data["context"],
            description=form.cleaned_data["description"],
            selected_sources=form.cleaned_data["sources"],
        )
    finally:
        cache.delete(creation_lock_key)
    evaluation = result["evaluation"]

    if result["blocked"]:
        messages.warning(
            request,
            "Completa la evaluacion activa antes de iniciar una nueva.",
        )
        return redirect("factors", evaluation_id=evaluation.pk)

    if form.cleaned_data["sources"]:
        messages.success(
            request,
            f"Se procesaron {result['processed_documents']} documento(s) para calcular la importancia sugerida.",
        )
    else:
        messages.success(request, "Evaluacion creada correctamente.")

    return redirect("factors", evaluation_id=evaluation.pk)
