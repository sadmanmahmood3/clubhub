from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class BootstrapFormMixin:
    """Adds Bootstrap CSS classes to every field, so all ClubHub forms look the same.
    Other apps can reuse it:  class MyForm(BootstrapFormMixin, forms.ModelForm)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    student_id = forms.CharField(max_length=10, help_text="Your 7-digit IUB student ID.")
    department = forms.CharField(max_length=100, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "student_id", "department")

    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"].strip()
        if not student_id.isdigit() or len(student_id) != 7:
            raise forms.ValidationError("Student ID must be exactly 7 digits.")
        if User.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError("An account with this student ID already exists.")
        return student_id
