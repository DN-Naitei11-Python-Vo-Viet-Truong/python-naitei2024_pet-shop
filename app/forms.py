import re
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .constants import MAX_LENGTH_NAME, MAX_LENGTH_PASSWORD


class SignInForm(forms.Form):
    username = forms.CharField(max_length=MAX_LENGTH_NAME)
    password = forms.CharField(
        max_length=MAX_LENGTH_PASSWORD, widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.search(r"^\w+$", username):
            raise forms.ValidationError(
                _("Username can only contain alphanumeric characters and the underscore."))
        return username
