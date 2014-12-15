from django import forms
from sales.models import ProductCategory
from backend.widgets import AdvancedFileInput

DISABLED_WIDGET_ATTRS = {'class': 'disabled', 'disabled': True}
class CategoryForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    thumbnail = forms.ImageField(widget=AdvancedFileInput, required=False)
    picture = forms.ImageField(widget=AdvancedFileInput, required=False)

    def __init__(self, *args, **kwargs):
        self.brand = kwargs['initial'].get('brand')
        super(CategoryForm, self).__init__(*args, **kwargs)
        cat = kwargs.get('instance', None)
        if cat:
            if not cat.valid:
                for field in self.fields.iterkeys():
                    self.fields[field].widget.attrs.update(DISABLED_WIDGET_ATTRS)

    class Meta:
        model = ProductCategory
        exclude = ['valid', ]

    def save(self, commit=True):
        self.instance = super(CategoryForm, self).save(commit=False)
        self.instance.brand_id = self.brand.pk
        self.instance.save()
        return self.instance
