from django import forms
from sales.models import ProductType


DISABLED_WIDGET_ATTRS = {'class': 'disabled', 'disabled': True}
class ProductTypeForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        self.brand = kwargs['initial'].get('brand')
        super(ProductTypeForm, self).__init__(*args, **kwargs)
        sa_attr = kwargs.get('instance', None)
        if sa_attr:
            if not sa_attr.valid:
                for field in self.fields.iterkeys():
                    self.fields[field].widget.attrs.update(DISABLED_WIDGET_ATTRS)


    class Meta:
        model = ProductType
        exclude = ['valid', ]

    def save(self, commit=True):
        self.instance = super(ProductTypeForm, self).save(commit=False)
        self.instance.brand_id = self.brand.pk
        self.instance.save()
        return self.instance
