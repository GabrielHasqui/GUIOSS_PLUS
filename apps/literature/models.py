from django.db import models


class LiteratureSource(models.TextChoices):
    SCOPUS = "scopus", "Scopus"
    OPENALEX = "openalex", "OpenAlex"
    SEMANTIC_SCHOLAR = "semantic_scholar", "Semantic Scholar"


class LiteratureQueryStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    RUNNING = "running", "En ejecución"
    COMPLETED = "completed", "Completada"
    FAILED = "failed", "Fallida"


class LiteratureQuery(models.Model):
    evaluation_factor = models.ForeignKey(
        "evaluations.EvaluationFactor",
        on_delete=models.CASCADE,
        related_name="literature_queries",
    )
    source = models.CharField(
        max_length=40,
        choices=LiteratureSource.choices,
    )
    query_text = models.TextField()
    status = models.CharField(
        max_length=40,
        choices=LiteratureQueryStatus.choices,
        default=LiteratureQueryStatus.PENDING,
    )
    total_results = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Consulta bibliográfica"
        verbose_name_plural = "Consultas bibliográficas"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(source__in=LiteratureSource.values), name="literature_query_source_valid"),
            models.CheckConstraint(condition=~models.Q(query_text=""), name="literature_query_text_not_empty"),
            models.CheckConstraint(condition=models.Q(status__in=LiteratureQueryStatus.values), name="literature_query_status_valid"),
            models.CheckConstraint(
                condition=(
                    models.Q(status__in=[LiteratureQueryStatus.COMPLETED, LiteratureQueryStatus.FAILED], completed_at__isnull=False)
                    | models.Q(status__in=[LiteratureQueryStatus.PENDING, LiteratureQueryStatus.RUNNING], completed_at__isnull=True)
                ),
                name="literature_query_completion_consistent",
            ),
            models.CheckConstraint(
                condition=models.Q(status=LiteratureQueryStatus.FAILED) | models.Q(error_message=""),
                name="literature_query_error_only_when_failed",
            ),
        ]

    def __str__(self):
        return f"{self.evaluation_factor} - {self.source}"


class LiteratureDocument(models.Model):
    source = models.CharField(
        max_length=40,
        choices=LiteratureSource.choices,
    )
    source_identifier = models.CharField(max_length=255)
    title = models.TextField()
    abstract = models.TextField(blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    authors = models.TextField(blank=True)
    doi = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    citation_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Documento bibliográfico"
        verbose_name_plural = "Documentos bibliográficos"
        ordering = ["-citation_count", "-year"]
        constraints = [
            models.UniqueConstraint(fields=["source", "source_identifier"], name="literature_document_source_identifier_unique"),
            models.CheckConstraint(condition=models.Q(source__in=LiteratureSource.values), name="literature_document_source_valid"),
            models.CheckConstraint(condition=~models.Q(source_identifier=""), name="literature_document_identifier_not_empty"),
            models.CheckConstraint(condition=~models.Q(title=""), name="literature_document_title_not_empty"),
            models.CheckConstraint(condition=models.Q(year__isnull=True) | models.Q(year__range=(1900, 2100)), name="literature_document_year_valid"),
        ]

    def __str__(self):
        return self.title[:120]


class QueryResult(models.Model):
    query = models.ForeignKey(
        LiteratureQuery,
        on_delete=models.CASCADE,
        related_name="results",
    )
    document = models.ForeignKey(
        LiteratureDocument,
        on_delete=models.CASCADE,
        related_name="query_results",
    )
    relevance_score = models.FloatField(default=0)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Resultado de consulta"
        verbose_name_plural = "Resultados de consulta"
        ordering = ["position", "-relevance_score"]
        constraints = [
            models.UniqueConstraint(fields=["query", "document"], name="literature_query_document_unique"),
            models.UniqueConstraint(fields=["query", "position"], name="literature_query_position_unique"),
            models.CheckConstraint(condition=models.Q(position__gte=1), name="literature_query_position_positive"),
            models.CheckConstraint(condition=models.Q(relevance_score__range=(0, 12)), name="literature_query_relevance_score_valid"),
        ]

    def __str__(self):
        return f"{self.query} - {self.document}"


class FactorEvidence(models.Model):
    evaluation_factor = models.ForeignKey(
        "evaluations.EvaluationFactor",
        on_delete=models.CASCADE,
        related_name="evidence_items",
    )
    document = models.ForeignKey(
        LiteratureDocument,
        on_delete=models.CASCADE,
        related_name="factor_evidence",
    )
    matched_keywords = models.TextField(blank=True)
    relevance_score = models.FloatField(default=0)

    class Meta:
        verbose_name = "Evidencia por factor"
        verbose_name_plural = "Evidencias por factor"
        ordering = ["-relevance_score"]
        constraints = [
            models.UniqueConstraint(fields=["evaluation_factor", "document"], name="literature_evidence_factor_document_unique"),
            models.CheckConstraint(condition=models.Q(relevance_score__range=(0, 12)), name="literature_evidence_relevance_score_valid"),
        ]

    def __str__(self):
        return f"{self.evaluation_factor} - {self.document}"
