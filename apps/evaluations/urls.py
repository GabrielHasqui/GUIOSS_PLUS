from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('history/', views.history_index, name='history_index'),
    path('evaluations/new/', views.create_evaluation, name='evaluation_create'),
    path('evaluations/<int:evaluation_id>/report.pdf', views.export_evaluation_pdf, name='evaluation_report_pdf'),
    path('evaluations/<int:evaluation_id>/factors/', views.factors, name='factors'),
    path('evaluations/<int:evaluation_id>/subfactors/', views.subfactors, name='subfactors'),
    path('evaluations/<int:evaluation_id>/subfactors/save/', views.save_subfactor, name='subfactor_save'),
    path('evaluations/<int:evaluation_id>/result/', views.result, name='result'),
    path('evaluations/<int:evaluation_id>/history/', views.history, name='history'),
]
