import re
from django import forms
from accounts.models import EndUser

import settings


email_pattern = re.compile(
    r"^([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@([-0-9a-zA-Z]+.)+[a-zA-Z]{2,6}$")

class UserCreationForm(forms.Form):

    action = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    password = forms.CharField(required=False)
    captcha = forms.CharField(required=False)

    def clean_action(self):
        action = self.cleaned_data.get("action", None)
        if action is None or action != 'create':
            raise forms.ValidationError("ERR_ACTION")
        return action

    def clean_email(self):
        email = self.cleaned_data.get("email", None)
        if email is None or not email_pattern.match(email):
            raise forms.ValidationError("ERR_EMAIL")

        try:
            EndUser.objects.get(email=email)
        except EndUser.DoesNotExist:
            return email
        raise forms.ValidationError("EXISTING_EMAIL")

    def clean_password(self):
        password = self.cleaned_data.get("password", None)
        if password is None or len(password) < 8:
            raise forms.ValidationError("ERR_PASSWORD")
        return password

    def clean_captcha(self):
        captcha = self.cleaned_data.get("captcha", None)
        if captcha and captcha != settings.USER_CREATION_CAPTCHA:
            raise forms.ValidationError("ERR_CAPTCHA")
        return captcha

    def get_response_error(self):
        for key in self.errors:
            return self.errors[key]
        return ""
