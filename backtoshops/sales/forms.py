# coding:UTF-8
from datetime import date
from itertools import chain
from django import forms
from django.forms.formsets import formset_factory
from django.forms.util import ErrorList
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from sales.models import DISCOUNT_TYPE, ProductBrand, ProductType, ProductCategory, GENDERS, ProductCurrency
from shops.models import Shop


TARGET_MARKET = (
    ('N', _("Global")),
    ('L', _("Local"))
)

class GroupedCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        group_by = 'city'
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<ul id="shopfolders">']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        group_name = ""
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            if group_name != self.choices.queryset[i].__dict__[group_by]:
                group_name = self.choices.queryset[i].__dict__[group_by]
                output.append(u'<li><label><input class="folder" type="checkbox"/>%s</label><ul>' % (group_name))

            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<li><label%s>%s %s</label></li>' % (label_for, rendered_cb, option_label))
            if i + 1 < self.choices.queryset.count():
                if group_name != self.choices.queryset[i+1].__dict__[group_by]:
                    output.append('</ul></li>')
            else:
                output.append('</ul>')
        output.append(u'</ul>')
        return mark_safe(u'\n'.join(output))


class ShopForm(forms.Form):
    target_market = forms.ChoiceField(label=_("Target market"), choices=TARGET_MARKET, required=False)
    
    def __init__(self, mother_brand=None, request=None, *args, **kwargs):
        super(ShopForm, self).__init__(*args, **kwargs)
        self.request = request
        search_arguments = {"mother_brand": mother_brand}
        
        if not request.user.is_staff: #operator.
            search_arguments.update({"pk__in": request.user.get_profile().shops.all(),})
            
        self.fields['shops'] = forms.ModelMultipleChoiceField(
            label=_("Participating shops"),
            queryset=Shop.objects.filter(**search_arguments).order_by('city'),
            widget=GroupedCheckboxSelectMultiple(),
            required=False
        )
        
    def clean_target_market(self):
        if self.request.user.is_staff:
            return self.cleaned_data['target_market']
        else:
            return 'L'

    def clean(self):
        data = self.cleaned_data
        target_market = data.get('target_market','')
        if target_market == 'N' and self.request.user.is_staff:
            data['shops'] = []
        else:
            if len(data['shops']) == 0:
                raise forms.ValidationError(_("You must select at least one shop."))
        return data

class BrandAttributeForm(forms.Form):
    ba_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(widget=forms.HiddenInput())
    premium_type = forms.CharField(widget=forms.HiddenInput(),required=False)
    premium_amount = forms.FloatField(widget=forms.HiddenInput(), required=False)
    premium_price = forms.FloatField(widget=forms.HiddenInput(), required=False)
    texture = forms.CharField(widget=forms.HiddenInput(), required=False)
    # texture_thumb = forms.CharField(widget=forms.HiddenInput())
    # preview_pk = forms.IntegerField(widget=forms.HiddenInput())
    preview = forms.CharField(widget=forms.HiddenInput(), required=False)
    preview_pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    # preview_thumb = forms.CharField(widget=forms.HiddenInput())

class ProductPictureForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput())
    url = forms.CharField(widget=forms.HiddenInput())
    thumb_url = forms.CharField(widget=forms.HiddenInput())

class ProductForm(forms.Form):
    type = forms.ModelChoiceField(
        label=_("Product type"),
        queryset=ProductType.objects.all(),
        empty_label=None
    )
    category = forms.ModelChoiceField(
        label=_("Product category"),
        queryset=ProductCategory.objects.all(),
        empty_label=None
    )
    name = forms.CharField(label=_("Product name"), show_hidden_initial=True)
    description = forms.CharField(label=_("Description"), widget=forms.Textarea())
    normal_price = forms.FloatField(label=_("Price"),widget=forms.TextInput(attrs={'class': 'inputS'}))
    currency = forms.ModelChoiceField(queryset=ProductCurrency.objects.all())
    discount_price = forms.FloatField(widget=forms.TextInput(attrs={'class': 'inputXS', 'style': 'display: none;'}))
    discount_type = forms.ChoiceField(choices=DISCOUNT_TYPE)
    discount = forms.FloatField(widget=forms.TextInput(attrs={'class': 'inputXS'}))
    valid_from = forms.DateField(label=_("From"), widget=forms.TextInput(attrs={'class': 'inputS'}), localize=True)
    valid_to = forms.DateField(label=_("To"), widget=forms.TextInput(attrs={'class': 'inputS'}), localize=True)

    def __init__(self, mother_brand=None, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False):
        super(ProductForm, self).__init__(data, files, auto_id, prefix, initial,
                                          error_class, label_suffix, empty_permitted)
        self.fields['brand'] = forms.ModelChoiceField(
            queryset=ProductBrand.objects.filter(seller=mother_brand)
        )
        formset = formset_factory(BrandAttributeForm, extra=0, can_delete=True)
        if initial:
            self.brand_attributes = formset(data=data, initial=initial.get('brand_attributes', None), prefix="brand_attributes")
        else:
            self.brand_attributes = formset(data=data, prefix="brand_attributes")

        pictures_formset = formset_factory(ProductPictureForm, extra=0, can_delete=True)
        if initial:
            self.pictures = pictures_formset(data=data, initial=initial.get('pictures', None),
                                             prefix="product_pictures")
        else:
            self.pictures = pictures_formset(data=data, prefix="product_pictures")

    def clean_valid_to(self):
        if self.cleaned_data['valid_to'] < self.cleaned_data['valid_from']:
            raise forms.ValidationError(_("Starting date can not be set past this sale's expiration date."))
        elif self.cleaned_data['valid_to'] < date.today():
            raise forms.ValidationError(_("Expiration date can not be set before today."))
        return self.cleaned_data['valid_to']

class BarcodeForm(forms.Form):
    brand_attribute = forms.IntegerField(required=False)
    common_attribute = forms.IntegerField()
    upc = forms.CharField(label=_("Barcode"), required=False)
BarcodeFormset = formset_factory(BarcodeForm, can_delete=True, extra=0)

class StockForm(forms.Form):
    brand_attribute = forms.IntegerField(required=False)
    common_attribute = forms.IntegerField()
    shop = forms.IntegerField(required=False)
    stock = forms.IntegerField(label=_("Stock"), error_messages = {'required': _(u'This field is required.')})
    def clean_stock(self):
        data = self.cleaned_data['stock']
        try:
            int_data = int(data)
        except:
            raise forms.ValidationError(_('Invalid stock quantity.'))
        return int_data

StockFormset = formset_factory(StockForm, can_delete=True, extra=0)

class StockStepForm(forms.Form):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False):
        super(StockStepForm, self).__init__(data, files, auto_id, prefix, initial,
                                            error_class, label_suffix, empty_permitted)
        if initial.get('stocks_initials', None):
            self.stocks = StockFormset(data=data, prefix="stocks", initial=initial.get('stocks_initials', None))
        else:
            self.stocks = StockFormset(data=data, prefix="stocks")

        if initial.get('barcodes_initials', None):
            self.barcodes = BarcodeFormset(data=data, prefix="barcodes", initial=initial.get('barcodes_initials', None))
        else:
            self.barcodes = BarcodeFormset(data=data, prefix="barcodes")
            
    def clean(self):
        if self.stocks.errors:
            for form in self.stocks.forms:
                if form.errors:
                    raise forms.ValidationError(form.errors)

class TargetForm(forms.Form):
    gender = forms.ChoiceField(choices=GENDERS, label=_("Target gender"))

class ProductBrandFormModel(forms.ModelForm):
    class Meta:
        model = ProductBrand
        exclude = ("seller",)

class ListSalesForm(forms.Form):
    ORDER_BY_ITEMS = {
                      ('product__category',_("Product category")),
                      ('product__type',_("Product type")),
                      ('product__name',_("Product name")),
                      ('total_stock',_("Initial stock quantity")),
                      ('total_rest_stock',_("Available quantity")),
                      ('total_sold_stock',_("Sales")),
                      ('product__normal_price',_("Price")),
                      ('product__discount_price',_("Discounted price")),
                      ('product__valid_from',_("Starting date")),
                      ('product__valid_to',_("Expiration date")),
                     }
    order_by1 = forms.ChoiceField(required=False,choices=ORDER_BY_ITEMS)
    order_by2 = forms.ChoiceField(required=False,choices=ORDER_BY_ITEMS)
    
