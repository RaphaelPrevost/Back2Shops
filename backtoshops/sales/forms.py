# coding:UTF-8
from datetime import date
from itertools import chain

from django import forms
from django.forms.formsets import formset_factory
from django.forms.util import ErrorList
from django.utils.encoding import force_text
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from barcodes.models import Barcode
from sales.models import DISCOUNT_TYPE
from sales.models import GENDERS
from sales.models import Product
from sales.models import ProductBrand
from sales.models import ProductCategory
from sales.models import ProductCurrency
from sales.models import SHIPPING_CALCULATION
from sales.models import ShippingCarrierService
from sales.models import ShippingCustomRule
from shippings.models import CustomShippingRate
from shippings.models import Service
from shops.models import Shop


TARGET_MARKET = (
    ('N', _("Global")),
    ('L', _("Local"))
)


class GroupedCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def __init__(self, attrs=None, choices=(), render_attrs=None):
        super(GroupedCheckboxSelectMultiple, self).__init__(attrs, choices)
        self.render_attrs = render_attrs or {}

    def _get_folder_label(self, queryset, attr_name):
        return getattr(queryset, attr_name, '')

    def _rende_checkboxinput(self, final_attrs, str_values):
        return forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        group_by = self.render_attrs.get('group_by', None) or 'id'
        ul_id = self.render_attrs.get('ul_id', None)

        final_attrs = self.build_attrs(attrs, name=name)
        output = ul_id and [u'<ul id="%s">' % ul_id] or [u'<ul>']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        group_name = ""
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            if group_name != self.choices.queryset[i].__dict__[group_by]:
                group_name = self.choices.queryset[i].__dict__[group_by]
                output.append(u'<li><label><input class="folder" type="checkbox"/>%s</label><ul>'
                              % (self._get_folder_label(self.choices.queryset[i], group_by)))

            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = self._rende_checkboxinput(final_attrs, str_values)
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


class ShippingServicesGroupedCheckboxSelectMultiple(GroupedCheckboxSelectMultiple):

    def _get_folder_label(self, queryset, attr_name):
        carrier = getattr(queryset, 'carrier', None)
        return carrier and carrier.name or ''

    def _rende_checkboxinput(self, final_attrs, str_values):
        service_ids = [obj.service_id for obj in ShippingCarrierService.objects.filter(pk__in=str_values)]
        return forms.CheckboxInput(final_attrs, check_test=lambda value: value in map(str, service_ids))


class ShippingCustomRuleCheckboxSelectMultiple(forms.CheckboxSelectMultiple):

    def _rende_checkboxinput(self, final_attrs, str_values):
        custom_rate_ids = [obj.custom_shipping_rate_id for obj in ShippingCustomRule.objects.filter(pk__in=str_values)]
        return forms.CheckboxInput(final_attrs, check_test=lambda value: value in map(str, custom_rate_ids))

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = ['<ul>']
        # Normalize to strings
        str_values = set([force_text(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = format_html(' for="{0}"', final_attrs['id'])
            else:
                label_for = ''

            cb = self._rende_checkboxinput(final_attrs, str_values)
            option_value = force_text(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = force_text(option_label)
            output.append(format_html('<li><label{0}>{1} {2}</label></li>',
                                      label_for, rendered_cb, option_label))
        output.append('</ul>')
        return mark_safe('\n'.join(output))


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
            widget=GroupedCheckboxSelectMultiple(
                render_attrs={'group_by': 'city',
                              'ul_id': 'shopfolders'}),
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
    premium_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    premium_amount = forms.FloatField(widget=forms.HiddenInput(), required=False)
    premium_price = forms.FloatField(widget=forms.HiddenInput(), required=False)
    texture = forms.CharField(widget=forms.HiddenInput(), required=False)
    # texture_thumb = forms.CharField(widget=forms.HiddenInput())
    # preview_pk = forms.IntegerField(widget=forms.HiddenInput())
    preview = forms.CharField(widget=forms.HiddenInput(), required=False)
    preview_pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    # preview_thumb = forms.CharField(widget=forms.HiddenInput())


class TypeAttributePriceForm(forms.Form):
    tap_id = forms.IntegerField(widget=forms.HiddenInput())
    type_attribute = forms.IntegerField(widget=forms.HiddenInput())
    type_attribute_price = forms.FloatField(widget=forms.HiddenInput())


class ProductPictureForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput())
    url = forms.CharField(widget=forms.HiddenInput())
    thumb_url = forms.CharField(widget=forms.HiddenInput())


class ProductForm(forms.Form):
    category = forms.ModelChoiceField(
        widget=forms.Select(attrs={'onChange': 'getTypeOptions(this.value)'}),
        label=_("Product category"),
        queryset=ProductCategory.objects.all())
    type = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(label=_("Product name"), show_hidden_initial=True)
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea())
    normal_price = forms.FloatField(
        widget=forms.HiddenInput(),
        error_messages={'required': _(u'The Unified price is required')})
    currency = forms.ModelChoiceField(
        label=_("Currency"),
        queryset=ProductCurrency.objects.all())
    discount_price = forms.FloatField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'inputXS', 'style': 'display: none;'}))
    discount_type = forms.ChoiceField(required=False, choices=DISCOUNT_TYPE)
    discount = forms.FloatField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'inputXS'}))
    valid_from = forms.DateField(
        required=False,
        label=_("From"),
        widget=forms.TextInput(attrs={'class': 'inputS'}),
        localize=True)
    valid_to = forms.DateField(
        required=False,
        label=_("To"),
        widget=forms.TextInput(attrs={'class': 'inputS'}),
        localize=True)

    def __init__(self, mother_brand=None, data=None, files=None,
                 auto_id='id_%s', prefix=None, initial=None,
                 error_class=ErrorList, label_suffix=':',
                 empty_permitted=False):
        super(ProductForm, self).__init__(data, files, auto_id, prefix,
                                          initial, error_class, label_suffix,
                                          empty_permitted)
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

        TypeAttributePriceFormSet = formset_factory(TypeAttributePriceForm,
                                                    extra=0, can_delete=True)
        if initial:
            self.type_attribute_prices = TypeAttributePriceFormSet(
                data=data, initial=initial.get('type_attribute_prices', None),
                prefix="type_attribute_prices")
        else:
            self.type_attribute_prices = TypeAttributePriceFormSet(
                data=data, prefix="type_attribute_prices")

    def clean_valid_to(self):
        valid_to = self.cleaned_data['valid_to']
        valid_from = self.cleaned_data['valid_from']
        if valid_to and valid_to < valid_from:
            raise forms.ValidationError(
                _("Starting date can not be set past this sale's "
                  "expiration date."))
        elif valid_to and valid_to < date.today():
            raise forms.ValidationError(
                _("Expiration date can not be set before today."))
        return valid_to


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
        self._clean_barcodes()
        return super(StockStepForm, self).clean()

    def _clean_barcodes(self):
        shops = []
        for stock in self.stocks:
            if stock.cleaned_data['shop']:
                shops.append(stock.cleaned_data['shop'])

        # In one shop, cannot have 2 same product barcode for two sale items.
        upcs = []
        for barcode in self.barcodes:
            barcode.full_clean()
            new_upc = barcode.cleaned_data['upc']
            old_upc = barcode.initial.get('upc')
            upcs.append(new_upc)
            # skip valid check if upc didn't change when edit sale.
            if old_upc and old_upc == new_upc:
                continue
            brs_with_same_upc = Barcode.objects.filter(upc=new_upc)
            for br in brs_with_same_upc:
                pro = Product.objects.get(sale=br.sale)
                if pro.valid_to and pro.valid_to < date.today():
                    continue
                br_shops = br.sale.shops.all()
                # check: 1. the same upc is in global shop when current sale in global shop.
                #        2. the same upc is in same shop.
                br_shops_id = [s.id for s in br_shops]
                if len(br_shops_id) == 0 and len(shops) == 0:
                    raise forms.ValidationError(_("product barcode %s already used in global market." % new_upc))
                elif len(set(br_shops_id).intersection(set(shops))):
                    raise forms.ValidationError(_("product barcode %s already used in your shop." % new_upc))

        if len(upcs) > len(set(upcs)):
            # barcodes are now optional for global sales, so empty upcs are OK.
            if not (shops == [] and set(upcs) == set([''])):
                raise forms.ValidationError(_("You cannot use two same product barcodes."))

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


class ShippingForm(forms.Form):
    handling_fee = forms.FloatField(
        label='Handling fee',
        widget=forms.TextInput(attrs={'class': 'handling_fee_input'}))
    allow_group_shipment = forms.BooleanField(
        label='Allow group shipment',
        required=False)
    allow_pickup = forms.BooleanField(
        label='Allow pick-up at the store',
        required=False)
    pickup_voids_handling_fee = forms.BooleanField(
        label='Pickup voids handling fees',
        required=False)
    shipping_calculation = forms.ChoiceField(
        label='Shipping calculation',
        widget=forms.RadioSelect(attrs={'class': 'shipping-radio'}),
        choices=SHIPPING_CALCULATION)
    service = forms.ModelMultipleChoiceField(
        label=_('Service'),
        queryset=Service.objects.all(),
        widget=ShippingServicesGroupedCheckboxSelectMultiple(
            render_attrs={'group_by': 'carrier_id',
                          'ul_id': 'service-folders'}),
        required=False
    )
    set_as_default_shop_shipping = forms.BooleanField(required=False)

    def __init__(self, mother_brand=None, request=None, *args, **kwargs):
        super(ShippingForm, self).__init__(*args, **kwargs)

        self.fields['custom_shipping_rate'] = forms.ModelMultipleChoiceField(
            required=False,
            queryset=CustomShippingRate.objects.filter(seller=mother_brand),
            widget=ShippingCustomRuleCheckboxSelectMultiple()
        )
