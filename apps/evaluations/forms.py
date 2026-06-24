import re

from django import forms

from .models import Evaluation


SOURCE_CHOICES = (
    ("openalex", "OpenAlex"),
    ("scopus", "Scopus"),
)


class EvaluationCreateForm(forms.ModelForm):
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

        for field_name in ("software_name", "context", "description"):
            value = cleaned_data.get(field_name, "")
            if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", value):
                self.add_error(
                    field_name,
                    "El texto contiene caracteres de control no permitidos.",
                )

        return cleaned_data
