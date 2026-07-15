import re

from django import forms

from .models import Evaluation


SOURCE_CHOICES = (
    ("openalex", "OpenAlex"),
    ("scopus", "Scopus"),
)

CONTEXT_CHOICES = (
    ("Educacion", "Educación"),
    ("Salud", "Salud"),
    ("Gobierno", "Gobierno"),
    ("Empresa", "Empresa"),
    ("Biblioteca", "Biblioteca"),
    ("Organizacion", "Organización"),
)


class EvaluationCreateForm(forms.ModelForm):
    context_choices = CONTEXT_CHOICES
    context = forms.CharField(max_length=120)
    context_mode = forms.ChoiceField(
        choices=(("choice", "Selector"), ("other", "Otro")),
        required=False,
    )
    description = forms.CharField(required=False, max_length=2000)
    sources = forms.MultipleChoiceField(
        required=False,
        choices=SOURCE_CHOICES,
    )

    class Meta:
        model = Evaluation
        fields = ["software_name", "context", "description"]

    def clean(self):
        cleaned_data = super().clean()
        context = (cleaned_data.get("context") or "").strip()
        context_mode = cleaned_data.get("context_mode") or "choice"
        controlled_contexts = {value for value, _label in CONTEXT_CHOICES}

        if context_mode == "choice" and context not in controlled_contexts:
            self.add_error("context", "Selecciona un area o contexto valido.")

        if context_mode == "other" and context == "":
            self.add_error("context", "Indica el area o contexto.")

        cleaned_data["context"] = context

        for field_name in ("software_name", "context", "description"):
            value = cleaned_data.get(field_name, "")
            if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", value):
                self.add_error(
                    field_name,
                    "El texto contiene caracteres de control no permitidos.",
                )

        return cleaned_data
