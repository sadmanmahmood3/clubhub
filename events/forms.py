from django import forms
from django.utils import timezone

from accounts.forms import BootstrapFormMixin

from .models import Event

DATETIME_INPUT = "%Y-%m-%dT%H:%M"  # format used by <input type="datetime-local">


class EventForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "venue", "start_time", "end_time", "capacity"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_INPUT),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_INPUT),
        }
        help_texts = {"capacity": "Maximum number of students who can register."}

    def clean_start_time(self):
        start_time = self.cleaned_data["start_time"]
        if start_time < timezone.now():
            raise forms.ValidationError("The event must start in the future.")
        return start_time
