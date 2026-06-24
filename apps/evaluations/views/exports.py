from django.contrib.auth.decorators import login_required

from ..reporting import build_evaluation_report_response
from ..selectors import get_evaluation, get_evaluation_report_context_data


@login_required
def export_evaluation_pdf(request, evaluation_id):
    evaluation = get_evaluation(evaluation_id, request.user)
    report_context = get_evaluation_report_context_data(evaluation)
    return build_evaluation_report_response(report_context)
