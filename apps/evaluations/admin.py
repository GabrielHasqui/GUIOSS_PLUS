from django.contrib import admin

from apps.literature.services import (
    calculate_openalex_suggested_importance_for_evaluation,
    calculate_scopus_suggested_importance_for_evaluation,
)

from .models import (
    Dimension,
    Evaluation,
    EvaluationFactor,
    EvaluationSubfactor,
    Factor,
    FactorKeyword,
    Recommendation,
    Subfactor,
)
from .services import update_recommendation


class SubfactorInline(admin.TabularInline):
    model = Subfactor
    extra = 0


class FactorKeywordInline(admin.TabularInline):
    model = FactorKeyword
    extra = 0


@admin.register(Dimension)
class DimensionAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Factor)
class FactorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "dimension",
        "default_suggested_importance",
        "scope",
    ]
    list_filter = ["dimension", "scope", "default_suggested_importance"]
    search_fields = ["name"]
    inlines = [SubfactorInline, FactorKeywordInline]


@admin.register(Subfactor)
class SubfactorAdmin(admin.ModelAdmin):
    list_display = ["name", "factor"]
    list_filter = ["factor__dimension", "factor"]
    search_fields = ["name", "factor__name"]


@admin.register(FactorKeyword)
class FactorKeywordAdmin(admin.ModelAdmin):
    list_display = ["keyword", "factor"]
    list_filter = ["factor"]
    search_fields = ["keyword", "factor__name"]
    
class EvaluationFactorInline(admin.TabularInline):
    model = EvaluationFactor
    extra = 0
    fields = [
        "factor",
        "literature_importance",
        "expert_importance",
        "suggested_importance",
        "decision_maker_importance",
        "relative_importance",
        "is_relevant",
        "selected_scope",
        "mean_weight",
        "foda",
    ]


class EvaluationSubfactorInline(admin.TabularInline):
    model = EvaluationSubfactor
    extra = 0


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = [
        "software_name",
        "context",
        "status",
        "created_by",
        "created_at",
    ]
    list_filter = ["status", "context", "created_at"]
    search_fields = ["software_name", "context", "description"]
    inlines = [EvaluationFactorInline]
    actions = [
        "calculate_openalex_suggested_importance",
        "calculate_scopus_suggested_importance",
        "generate_recommendations",
    ]
    
    @admin.action(description="Calcular importancia sugerida con OpenAlex")
    def calculate_openalex_suggested_importance(self, request, queryset):
        total = 0

        for evaluation in queryset:
            total += calculate_openalex_suggested_importance_for_evaluation(
                evaluation,
                per_factor=5,
            )

        self.message_user(
            request,
            f"OpenAlex procesó {total} documento(s).",
        )

    @admin.action(description="Calcular importancia sugerida con Scopus")
    def calculate_scopus_suggested_importance(self, request, queryset):
        total = 0

        for evaluation in queryset:
            total += calculate_scopus_suggested_importance_for_evaluation(
                evaluation,
                per_factor=5,
            )

        self.message_user(
            request,
            f"Scopus procesó {total} documento(s).",
        )
    
    @admin.action(description="Generar recomendación GUIOS")
    def generate_recommendations(self, request, queryset):
        for evaluation in queryset:
            update_recommendation(evaluation)

        self.message_user(
            request,
            f"Se generaron {queryset.count()} recomendación(es).",
        )

@admin.register(EvaluationFactor)
class EvaluationFactorAdmin(admin.ModelAdmin):
    list_display = [
        "evaluation",
        "factor",
        "suggested_importance",
        "decision_maker_importance",
        "relative_importance",
        "is_relevant",
        "selected_scope",
        "mean_weight",
        "foda",
    ]
    list_filter = [
        "is_relevant",
        "selected_scope",
        "foda",
        "suggested_importance",
        "relative_importance",
    ]
    search_fields = ["evaluation__software_name", "factor__name"]
    inlines = [EvaluationSubfactorInline]


@admin.register(EvaluationSubfactor)
class EvaluationSubfactorAdmin(admin.ModelAdmin):
    list_display = [
        "evaluation_factor",
        "subfactor",
        "compliance",
    ]
    list_filter = ["compliance"]
    search_fields = [
        "evaluation_factor__evaluation__software_name",
        "subfactor__name",
    ]


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ["evaluation", "code", "created_at"]
    search_fields = ["evaluation__software_name", "text"]
