from brandings.models import Branding
from django import forms

class BrandingForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

    class Meta:
        model = Branding

    def __init__(self, *args, **kwargs):
        self.brand = kwargs['initial'].get('brand')
        return super(BrandingForm, self).__init__(*args, **kwargs)

    def clean_for_brand_id(self):
        brand = self.cleaned_data.get('for_brand')
        if brand and int(brand) != self.brand:
            raise forms.ValidationError('auth failed')

    def save(self, commit=True):
        self.instance = super(BrandingForm, self).save(commit=False)
        self.instance.for_brand_id = self.brand.pk
        self.instance.save()
        return self.instance

