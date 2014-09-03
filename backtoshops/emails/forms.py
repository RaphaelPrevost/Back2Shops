from django import forms
from django.forms.formsets import formset_factory
from emails.models import EmailTemplate

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate

    def __init__(self, *args, **kwargs):
        super(EmailTemplateForm, self).__init__(*args, **kwargs)

        self.fields['html_head'] = forms.CharField(
                widget=forms.Textarea(),
                required=False,
                initial=
            '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n'
            '<meta content="width=device-width"/>')
        self.fields['html_body'] = forms.CharField(
                widget=forms.Textarea(),
                required=False)

        formset = formset_factory(EmailTemplateImageForm, extra=0, can_delete=True)
        initial = kwargs.get('initial') or {}
        if initial:
            self.images = formset(data=kwargs.get('data'),
                                  initial=initial.get('images', None),
                                  prefix="email_images")
        else:
            self.images = formset(data=kwargs.get('data'),
                                  prefix="email_images")


class EmailTemplateImageForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput())
    url = forms.CharField(widget=forms.HiddenInput())
    thumb_url = forms.CharField(widget=forms.HiddenInput())

