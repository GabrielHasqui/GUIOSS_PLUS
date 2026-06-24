from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Evaluation, EvaluationFactor, EvaluationSubfactor
from .services import is_relevant, calculate_relative_importance, initialize_evaluation_factors, initialize_relevant_subfactors, update_factor_mean_weight_and_foda

@receiver(post_save, sender=Evaluation)
def create_evaluation_factors(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    if created:
        initialize_evaluation_factors(instance)


@receiver(post_save, sender=EvaluationFactor)
def update_factor_after_decision_importance(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    if created:
        return

    if instance.decision_maker_importance is None:
        return

    relative_importance = calculate_relative_importance(
        instance.suggested_importance,
        instance.decision_maker_importance,
    )
    relevant = is_relevant(relative_importance)

    EvaluationFactor.objects.filter(pk=instance.pk).update(
        relative_importance=relative_importance,
        is_relevant=relevant,
    )

    instance.relative_importance = relative_importance
    instance.is_relevant = relevant

    initialize_relevant_subfactors(instance)


@receiver(post_save, sender=EvaluationSubfactor)
def update_factor_after_subfactor_save(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    # El GUIOS original calcula la ponderacion solo cuando el decisor guarda
    # todos los valores del factor, no durante su inicializacion.
    if created:
        return
    update_factor_mean_weight_and_foda(instance.evaluation_factor)


@receiver(post_delete, sender=EvaluationSubfactor)
def update_factor_after_subfactor_delete(sender, instance, **kwargs):
    update_factor_mean_weight_and_foda(instance.evaluation_factor)
