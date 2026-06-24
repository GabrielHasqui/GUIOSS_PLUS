from django.contrib import admin

from .models import FactorEvidence, LiteratureDocument, LiteratureQuery, QueryResult


@admin.register(LiteratureQuery)
class LiteratureQueryAdmin(admin.ModelAdmin):
    list_display = [
        "evaluation_factor",
        "source",
        "status",
        "total_results",
        "created_at",
        "completed_at",
    ]
    list_filter = ["source", "status", "created_at"]
    search_fields = [
        "evaluation_factor__evaluation__software_name",
        "evaluation_factor__factor__name",
        "query_text",
    ]


@admin.register(LiteratureDocument)
class LiteratureDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "source",
        "source_identifier",
        "year",
        "citation_count",
        "doi",
    ]
    list_filter = ["source", "year"]
    search_fields = ["title", "abstract", "authors", "doi"]


@admin.register(QueryResult)
class QueryResultAdmin(admin.ModelAdmin):
    list_display = [
        "query",
        "document",
        "relevance_score",
        "position",
    ]
    list_filter = ["query__source", "query__status"]
    search_fields = [
        "query__evaluation_factor__evaluation__software_name",
        "query__query_text",
        "document__title",
        "document__doi",
    ]


@admin.register(FactorEvidence)
class FactorEvidenceAdmin(admin.ModelAdmin):
    list_display = [
        "evaluation_factor",
        "document",
        "relevance_score",
    ]
    search_fields = [
        "evaluation_factor__evaluation__software_name",
        "evaluation_factor__factor__name",
        "document__title",
    ]
