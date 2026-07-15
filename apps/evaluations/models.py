from django.db import models
from django.db.models.functions import Lower


class ImportanceLevel(models.IntegerChoices):
    IRRELEVANTE = 1, "Irrelevante"
    OPCIONAL = 2, "Opcional"
    IMPORTANTE = 3, "Importante"
    FUNDAMENTAL = 4, "Fundamental"


class Scope(models.TextChoices):
    INTERNO = "Interno", "Interno"
    EXTERNO = "Externo", "Externo"
    AMBOS = "Ambos", "Ambos"


class Dimension(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Dimensión"
        verbose_name_plural = "Dimensiones"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(name=""), name="evaluation_dimension_name_not_empty"),
            models.UniqueConstraint(Lower("name"), name="evaluation_dimension_name_ci_unique"),
        ]

    def __str__(self):
        return self.name


class Factor(models.Model):
    dimension = models.ForeignKey(
        Dimension,
        on_delete=models.PROTECT,
        related_name="factors",
    )
    name = models.CharField(max_length=180, unique=True)
    default_suggested_importance = models.PositiveSmallIntegerField(
        choices=ImportanceLevel.choices,
        default=ImportanceLevel.OPCIONAL,
    )
    scope = models.CharField(
        max_length=20,
        choices=Scope.choices,
        default=Scope.INTERNO,
    )

    class Meta:
        verbose_name = "Factor"
        verbose_name_plural = "Factores"
        ordering = ["dimension__name", "name"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(name=""), name="evaluation_factor_name_not_empty"),
            models.CheckConstraint(condition=models.Q(default_suggested_importance__range=(1, 4)), name="evaluation_factor_default_importance_valid"),
            models.CheckConstraint(condition=models.Q(scope__in=Scope.values), name="evaluation_factor_scope_valid"),
            models.UniqueConstraint(Lower("name"), name="evaluation_factor_name_ci_unique"),
        ]

    def __str__(self):
        return self.name


class Subfactor(models.Model):
    factor = models.ForeignKey(
        Factor,
        on_delete=models.CASCADE,
        related_name="subfactors",
    )
    name = models.TextField()

    class Meta:
        verbose_name = "Subfactor"
        verbose_name_plural = "Subfactores"
        ordering = ["factor__name", "id"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(name=""), name="evaluation_subfactor_name_not_empty"),
            models.UniqueConstraint(models.F("factor"), Lower("name"), name="evaluation_subfactor_factor_name_ci_unique"),
        ]

    def __str__(self):
        return self.name


class FactorKeyword(models.Model):
    factor = models.ForeignKey(
        Factor,
        on_delete=models.CASCADE,
        related_name="keywords",
    )
    keyword = models.CharField(max_length=120)

    class Meta:
        verbose_name = "Palabra clave de factor"
        verbose_name_plural = "Palabras clave de factores"
        ordering = ["factor__name", "keyword"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(keyword=""), name="evaluation_keyword_not_empty"),
            models.UniqueConstraint(models.F("factor"), Lower("keyword"), name="evaluation_keyword_factor_value_ci_unique"),
        ]

    def __str__(self):
        return f"{self.factor.name}: {self.keyword}"
    
class EvaluationStatus(models.TextChoices):
    DRAFT = "draft", "Borrador"
    SUGGESTED_READY = "suggested_ready", "Importancia sugerida calculada"
    FACTORS_READY = "factors_ready", "Factores evaluados"
    SUBFACTORS_READY = "subfactors_ready", "Subfactores evaluados"
    COMPLETED = "completed", "Completada"


class FodaLevel(models.TextChoices):
    FORTALEZA = "Fortaleza", "Fortaleza"
    OPORTUNIDAD = "Oportunidad", "Oportunidad"
    DEBILIDAD = "Debilidad", "Debilidad"
    AMENAZA = "Amenaza", "Amenaza"


class SubfactorComplianceLevel(models.IntegerChoices):
    NO_CUMPLE = 1, "No cumple el requisito"
    DESCONOCE = 2, "Desconozco si cumple requisito"
    CUMPLE_PARCIAL = 3, "Cumple parcialmente el requisito"
    CUMPLE = 4, "Cumple el requisito"


class Evaluation(models.Model):
    software_name = models.CharField(max_length=180)
    context = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=40,
        choices=EvaluationStatus.choices,
        default=EvaluationStatus.DRAFT,
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="evaluations",
    )
    reopened_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="reopened_evaluations",
        null=True,
        blank=True,
    )
    reopened_at = models.DateTimeField(null=True, blank=True)
    reopen_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(software_name=""), name="evaluation_software_name_not_empty"),
            models.CheckConstraint(condition=~models.Q(context=""), name="evaluation_context_not_empty"),
            models.CheckConstraint(condition=models.Q(status__in=EvaluationStatus.values), name="evaluation_status_valid"),
        ]

    def __str__(self):
        return f"{self.software_name} - {self.context}"


class EvaluationFactor(models.Model):
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="evaluation_factors",
    )
    factor = models.ForeignKey(
        Factor,
        on_delete=models.PROTECT,
        related_name="evaluation_factors",
    )

    literature_importance = models.PositiveSmallIntegerField(
        choices=ImportanceLevel.choices,
        null=True,
        blank=True,
    )
    expert_importance = models.PositiveSmallIntegerField(
        choices=ImportanceLevel.choices,
        null=True,
        blank=True,
    )
    suggested_importance = models.PositiveSmallIntegerField(
        choices=ImportanceLevel.choices,
        default=ImportanceLevel.OPCIONAL,
    )
    decision_maker_importance = models.PositiveSmallIntegerField(
        choices=ImportanceLevel.choices,
        null=True,
        blank=True,
    )
    relative_importance = models.PositiveSmallIntegerField(
        choices=ImportanceLevel.choices,
        null=True,
        blank=True,
    )
    is_relevant = models.BooleanField(default=False)

    selected_scope = models.CharField(
        max_length=20,
        choices=Scope.choices,
    )
    mean_weight = models.FloatField(null=True, blank=True)
    foda = models.CharField(
        max_length=20,
        choices=FodaLevel.choices,
        blank=True,
    )

    class Meta:
        verbose_name = "Factor evaluado"
        verbose_name_plural = "Factores evaluados"
        ordering = ["factor__dimension__name", "factor__name"]
        constraints = [
            models.UniqueConstraint(fields=["evaluation", "factor"], name="evaluation_factor_pair_unique"),
            models.CheckConstraint(condition=models.Q(literature_importance__isnull=True) | models.Q(literature_importance__range=(1, 4)), name="evaluation_literature_importance_valid"),
            models.CheckConstraint(condition=models.Q(expert_importance__isnull=True) | models.Q(expert_importance__range=(1, 4)), name="evaluation_expert_importance_valid"),
            models.CheckConstraint(condition=models.Q(suggested_importance__range=(1, 4)), name="evaluation_suggested_importance_valid"),
            models.CheckConstraint(condition=models.Q(decision_maker_importance__isnull=True) | models.Q(decision_maker_importance__range=(1, 4)), name="evaluation_decision_importance_valid"),
            models.CheckConstraint(condition=models.Q(relative_importance__isnull=True) | models.Q(relative_importance__range=(1, 4)), name="evaluation_relative_importance_valid"),
            models.CheckConstraint(condition=models.Q(selected_scope__in=[Scope.INTERNO, Scope.EXTERNO]), name="evaluation_selected_scope_valid"),
            models.CheckConstraint(condition=models.Q(mean_weight__isnull=True) | models.Q(mean_weight__range=(1, 4)), name="evaluation_mean_weight_valid"),
            models.CheckConstraint(condition=models.Q(foda__in=["", *FodaLevel.values]), name="evaluation_foda_valid"),
            models.CheckConstraint(
                condition=(
                    models.Q(relative_importance__isnull=True, is_relevant=False)
                    | models.Q(relative_importance=ImportanceLevel.IRRELEVANTE, is_relevant=False)
                    | models.Q(relative_importance__gte=ImportanceLevel.OPCIONAL, is_relevant=True)
                ),
                name="evaluation_relevance_consistent",
            ),
        ]

    def __str__(self):
        return f"{self.evaluation} - {self.factor}"


class EvaluationSubfactor(models.Model):
    evaluation_factor = models.ForeignKey(
        EvaluationFactor,
        on_delete=models.CASCADE,
        related_name="evaluation_subfactors",
    )
    subfactor = models.ForeignKey(
        Subfactor,
        on_delete=models.PROTECT,
        related_name="evaluation_subfactors",
    )
    compliance = models.PositiveSmallIntegerField(
        choices=SubfactorComplianceLevel.choices,
        default=SubfactorComplianceLevel.NO_CUMPLE,
    )

    class Meta:
        verbose_name = "Subfactor evaluado"
        verbose_name_plural = "Subfactores evaluados"
        ordering = ["subfactor__id"]
        constraints = [
            models.UniqueConstraint(fields=["evaluation_factor", "subfactor"], name="evaluation_subfactor_pair_unique"),
            models.CheckConstraint(condition=models.Q(compliance__range=(1, 4)), name="evaluation_subfactor_compliance_valid"),
        ]

    def __str__(self):
        return f"{self.evaluation_factor} - {self.subfactor}"


class Recommendation(models.Model):
    evaluation = models.OneToOneField(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="recommendation",
    )
    code = models.CharField(max_length=10, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recomendación"
        verbose_name_plural = "Recomendaciones"
        constraints = [
            models.CheckConstraint(condition=models.Q(code__in=["", "A", "B", "C"]), name="evaluation_recommendation_code_valid"),
            models.CheckConstraint(condition=~models.Q(text=""), name="evaluation_recommendation_text_not_empty"),
        ]

    def __str__(self):
        return f"{self.evaluation} - {self.code}"
