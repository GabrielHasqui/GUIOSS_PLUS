from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..selectors import get_active_evaluation,get_evaluation,get_history_detail_context_data,get_software_history_data


@login_required
def history_index(request):
    context = {
        "active_nav": "history",
        "evaluation": get_active_evaluation(request.user),
        **get_software_history_data(request.user),
    }
    return render(request, "evaluations/history/list.html", context)


@login_required
def history(request, evaluation_id):
    evaluation = get_evaluation(evaluation_id, request.user)
    return render(
        request,
        "evaluations/history/detail.html",
        get_history_detail_context_data(evaluation),
    )
