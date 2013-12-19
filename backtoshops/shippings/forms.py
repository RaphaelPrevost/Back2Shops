from django import forms
from shippings.models import CustomShippingRate


class CustomShippingRateFormModel(forms.ModelForm):
    class Meta:
        model = CustomShippingRate
        exclude = ("seller",)
