# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import json
from datetime import date
from itertools import chain

from django import forms
from django.forms.formsets import BaseFormSet
from django.forms.formsets import formset_factory
from django.forms.util import ErrorList
from django.db.models import Q
from django.utils.encoding import force_text
from django.utils.encoding import force_unicode
from django.utils.encoding import python_2_unicode_compatible
from django.utils.html import conditional_escape
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from barcodes.models import Barcode
from common.constants import TARGET_MARKET_TYPES
from common.constants import USERS_ROLE
from common.utils import get_currency
from sales.models import DISCOUNT_TYPE
from sales.models import ExternalRef
from sales.models import GENDERS
from sales.models import OrderConfirmSetting
from sales.models import Product
from sales.models import ProductBrand
from sales.models import ProductCategory
from sales.models import ProductCurrency
from sales.models import WeightUnit
from shippings.models import CustomShippingRate
from shippings.models import CustomShippingRateInShipping
from shippings.models import SHIPPING_CALCULATION
from shippings.models import Service
from shippings.models import ServiceInShipping
from shops.models import Shop


TARGET_MARKET = (
    (TARGET_MARKET_TYPES.GLOBAL, _("Global")),
    (TARGET_MARKET_TYPES.LOCAL, _("Local"))
)

@python_2_unicode_compatible
class NoEmptyBaseFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        BaseFormSet.__init__(self, *args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False

def get_formset_extra(data, prefix):
    if not data or prefix + '-INITIAL_FORMS' not in data:
        return 0
    init_forms_count = data[prefix + '-INITIAL_FORMS']
    init_forms_count = init_forms_count[0] if type(init_forms_count) is list \
                                           else init_forms_count
    init_forms_count = int(init_forms_count)
    total_forms_count = data[prefix + '-TOTAL_FORMS']
    total_forms_count = total_forms_count[0] if type(total_forms_count) is list \
                                             else total_forms_count
    total_forms_count = int(total_forms_count)
    extra = total_forms_count - init_forms_count
    if extra > 0 and len([one for one in data
            if one.startswith("%s-%s" % (prefix, total_forms_count-1))]) == 0:
        extra = 0
    return extra

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
        extra_field = self.render_attrs.get('extra_field', None)

        final_attrs = self.build_attrs(attrs, name=name)
        output = ul_id and [u'<ul id="%s">' % ul_id] or [u'<ul>']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        group_name = ""
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            group_by_obj_name = None
            if '__' in group_by:
                group_by_obj_name, _group_by = group_by.split('__')
            else:
                _group_by = group_by

            group_by_obj = self._group_by_obj(self.choices.queryset[i],
                                                group_by_obj_name)
            if group_name != group_by_obj.__dict__[_group_by]:
                group_name = group_by_obj.__dict__[_group_by]
                output.append(u'<li><label><input class="folder" type="checkbox"/>%s</label><ul>'
                              % (self._get_folder_label(group_by_obj, _group_by)))

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
            if extra_field:
                extra_field_value = getattr(self.choices.queryset[i], extra_field, '')
                option_label = "<span %s='%s'>%s</span>" % (
                        extra_field, extra_field_value, option_label)
            output.append(u'<li><label%s>%s %s</label></li>' % (label_for, rendered_cb, option_label))

            if i + 1 < self.choices.queryset.count():
                next_group_by_obj = self._group_by_obj(
                    self.choices.queryset[i+1], group_by_obj_name)
                if group_name != next_group_by_obj.__dict__[_group_by]:
                    output.append('</ul></li>')
            else:
                output.append('</ul>')
        output.append(u'</ul>')
        return mark_safe(u'\n'.join(output))

    def _group_by_obj(self, obj, group_by_obj_name=None):
        if group_by_obj_name is None:
            return obj
        else:
            return getattr(obj, group_by_obj_name)


class ShippingServicesGroupedCheckboxSelectMultiple(GroupedCheckboxSelectMultiple):

    def _get_folder_label(self, queryset, attr_name):
        carrier = getattr(queryset, 'carrier', None)
        return carrier and carrier.name or ''

    def _rende_checkboxinput(self, final_attrs, str_values):
        service_ids = [obj.service_id for obj in
                       ServiceInShipping.objects.filter(pk__in=str_values)]
        return forms.CheckboxInput(
            final_attrs,
            check_test=lambda value: value in map(str, service_ids))


class ShippingCustomRuleCheckboxSelectMultiple(forms.CheckboxSelectMultiple):

    def _rende_checkboxinput(self, final_attrs, str_values):
        custom_rate_ids = [obj.custom_shipping_rate_id for obj in
                           CustomShippingRateInShipping.objects.filter(
                               pk__in=str_values)]
        return forms.CheckboxInput(
            final_attrs,
            check_test=lambda value: value in map(str, custom_rate_ids))

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
            output.append(format_html(u'<li><label{0}>{1} {2}</label></li>',
                                      label_for, rendered_cb, option_label))
        output.append('</ul>')
        return mark_safe('\n'.join(output))


class ShopForm(forms.Form):

    def __init__(self, mother_brand=None, request=None, *args, **kwargs):
        super(ShopForm, self).__init__(*args, **kwargs)
        self.request = request
        search_arguments = {"mother_brand": mother_brand}

        if (not request.user.is_superuser and
            request.user.get_profile().role == USERS_ROLE.MANAGER): # shop manager.
            search_arguments.update({"pk__in": request.user.get_profile().shops.all(),})

        self.fields['shops'] = forms.ModelMultipleChoiceField(
            label=_("Participating shops"),
            queryset=Shop.objects.filter(**search_arguments).order_by('address__city'),
            widget=GroupedCheckboxSelectMultiple(
                render_attrs={'group_by': 'address__city',
                              'ul_id': 'shopfolders',
                              'extra_field': 'default_currency'}),
            required=False,
            initial=kwargs['initial'].get('shops')
        )

        self.fields['target_market'] = forms.ChoiceField(
            label=_("Target market"),
            choices=self.get_target_market_choices(request),
            required=False)

        self.initial['shops'] = kwargs['initial'].get('shops') or []
        self.initial['target_market'] = kwargs['initial'].get('target_market')


    def get_target_market_choices(self, request):
        if request.user.is_superuser:
            return TARGET_MARKET

        req_u_profile = request.user.get_profile()
        if req_u_profile.role == USERS_ROLE.ADMIN:
            return TARGET_MARKET
        elif req_u_profile.role == USERS_ROLE.MANAGER:
            shops = req_u_profile.shops.all()
            if len(shops) and req_u_profile.allow_internet_operate:
                return TARGET_MARKET
            elif req_u_profile.allow_internet_operate:
                return (TARGET_MARKET[0],)
            else:
                return (TARGET_MARKET[1],)
        else:
            return ()

    def clean_target_market(self):
        if self.request.user.is_superuser:
            return self.cleaned_data['target_market']

        u_profile = self.request.user.get_profile()
        if (u_profile.role == USERS_ROLE.ADMIN or
            (u_profile.role == USERS_ROLE.MANAGER and
             u_profile.allow_internet_operate)):
            return self.cleaned_data['target_market']
        else:
            return 'L'

    def clean(self):
        data = self.cleaned_data
        target_market = data.get('target_market', '')
        # Only super user and global sales manager could set sales market
        # to global.
        if (target_market == TARGET_MARKET_TYPES.GLOBAL and
            (self.request.user.is_superuser or
             self.request.user.get_profile().role == USERS_ROLE.ADMIN or
             self.request.user.get_profile().allow_internet_operate)):
            data['shops'] = []
        else:
            if len(data['shops']) == 0:
                raise forms.ValidationError(_("You must select at least one shop."))

            # check if selected shops in the same currency
            first_currency = get_currency(self.request.user, data['shops'][0])
            for s in data['shops'][1:]:
                if get_currency(self.request.user, s) != first_currency:
                    raise forms.ValidationError(
                            _("Please select shops within the same currency area."))
        return data

class BrandAttributePreviewForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    url = forms.CharField(widget=forms.HiddenInput(), required=False)
    sort_order = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, data=None, files=None,
                 auto_id='id_%s', prefix=None, initial=None,
                 error_class=ErrorList, label_suffix=':',
                 empty_permitted=False):
        super(BrandAttributePreviewForm, self).__init__(data, files, auto_id, prefix,
                                          initial, error_class, label_suffix,
                                          empty_permitted)

class BrandAttributeForm(forms.Form):
    ba_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(widget=forms.HiddenInput())
    premium_type = forms.ChoiceField(choices=DISCOUNT_TYPE, required=False)
    premium_amount = forms.FloatField(widget=forms.TextInput(attrs={'class': 'inputXS'}),
                                      required=False)
    texture = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, data=None, files=None,
                 auto_id='id_%s', prefix=None, initial=None,
                 error_class=ErrorList, label_suffix=':',
                 empty_permitted=False):
        super(BrandAttributeForm, self).__init__(data, files, auto_id, prefix,
                                          initial, error_class, label_suffix,
                                          empty_permitted)
        preview_prefix = "%s-previews" % prefix
        formset = formset_factory(BrandAttributePreviewForm,
                                  formset=NoEmptyBaseFormSet,
                                  extra=get_formset_extra(data, preview_prefix),
                                  can_delete=True)
        if data and self.is_empty_ba(data, preview_prefix):
            data.update({
                '%s-TOTAL_FORMS' % preview_prefix: 0,
                '%s-INITIAL_FORMS' % preview_prefix: 0,
                '%s-MAX_NUM_FORMS' % preview_prefix: 1000,
            })
        if initial:
            self.previews = formset(data=data,
                                    initial=initial.get('previews', None),
                                    prefix=preview_prefix)
        else:
            self.previews = formset(data=data, prefix=preview_prefix)

    def is_empty_ba(self, data, preview_prefix):
        return len([k for k in data if k.startswith(preview_prefix)]) == 0


class TypeAttributePriceForm(forms.Form):
    tap_id = forms.IntegerField(widget=forms.HiddenInput())
    type_attribute = forms.IntegerField(widget=forms.HiddenInput())
    type_attribute_price = forms.FloatField(widget=forms.HiddenInput())


class TypeAttributeWeightForm(forms.Form):
    taw_id = forms.IntegerField(widget=forms.HiddenInput())
    type_attribute = forms.IntegerField(widget=forms.HiddenInput())
    type_attribute_weight = forms.FloatField(widget=forms.HiddenInput())


class ProductPictureForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput())
    url = forms.CharField(widget=forms.HiddenInput())
    thumb_url = forms.CharField(widget=forms.HiddenInput())
    sort_order = forms.CharField(widget=forms.HiddenInput(), required=False)


class ProductForm(forms.Form):
    category = forms.ModelChoiceField(
        widget=forms.Select(attrs={'onChange': 'getTypeOptions(this.value)'}),
        label=_("Product category"),
        queryset=ProductCategory.objects.all())
    type = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(
        label=_("Product name"),
        max_length=50,
        show_hidden_initial=True)
    short_description = forms.CharField(
        label=_("Short Description"),
        required=False,
        max_length=240)
    cover_pk = forms.IntegerField(widget=forms.HiddenInput())
    cover_url = forms.CharField(
        label=_("Cover picture"),
        widget=forms.HiddenInput())
    description = forms.CharField(
        label=_("Full description"),
        widget=forms.Textarea())
    weight_unit = forms.ModelChoiceField(
        label=_("Weight Unit"),
        queryset=WeightUnit.objects.all())
    standard_weight = forms.FloatField(
        required=False,
        widget=forms.HiddenInput())
    normal_price = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False)
    currency = forms.ModelChoiceField(
        label=_("Currency"),
        queryset=ProductCurrency.objects.all(),
        widget=forms.Select(attrs={'disabled':'disabled'}))
    discount_type = forms.ChoiceField(
        required=False,
        choices=(('percentage', 'Percentage'),))
    coupon_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'display: none;'}))
    discount = forms.FloatField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'inputXS'}))
    preview_discount_price_str = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'inputXS', 'style': 'display: none;'}))
    preview_base_price = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'inputXS', 'style': 'display: none;'}))
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
    gender = forms.ChoiceField(choices=GENDERS, label=_("Target gender"))
    available_from = forms.DateField(
        required=False,
        label=_("From"),
        widget=forms.TextInput(attrs={'class': 'inputS'}),
        localize=True)
    available_to = forms.DateField(
        required=False,
        label=_("To"),
        widget=forms.TextInput(attrs={'class': 'inputS'}),
        localize=True)

    def __init__(self, mother_brand=None, data=None, files=None,
                 auto_id='id_%s', prefix=None, initial=None,
                 error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, add_new=False):
        super(ProductForm, self).__init__(data, files, auto_id, prefix,
                                          initial, error_class, label_suffix,
                                          empty_permitted)
        self.fields['brand'] = forms.ModelChoiceField(
            queryset=ProductBrand.objects.filter(seller=mother_brand)
        )
        cat_queryset = ProductCategory.objects.filter(
                Q(brand=mother_brand) & Q(valid=True))
        if initial.get('category'):
            selected_category = ProductCategory.objects.get(pk=initial['category'])
            if not (selected_category.is_default or selected_category.valid):
                cat_queryset = ProductCategory.objects.filter(
                        Q(brand=mother_brand))
        if not cat_queryset:
            cat_queryset = ProductCategory.objects.filter(
                Q(is_default=True) & Q(valid=True))
            self.fields['category'].empty_label = None
        self.fields['category'].queryset = cat_queryset

        b_attrs_prefix = "brand_attributes"
        formset = formset_factory(BrandAttributeForm,
                                  formset=NoEmptyBaseFormSet,
                                  extra=get_formset_extra(data, b_attrs_prefix),
                                  can_delete=True)
        if initial:
            self.brand_attributes = formset(data=data,
                                            initial=initial.get('brand_attributes', None),
                                            prefix=b_attrs_prefix)
        else:
            self.brand_attributes = formset(data=data, prefix=b_attrs_prefix)

        pictures_prefix = "product_pictures"
        pictures_formset = formset_factory(ProductPictureForm,
                                           formset=NoEmptyBaseFormSet,
                                           extra=get_formset_extra(data, pictures_prefix),
                                           can_delete=True)
        if initial:
            self.pictures = pictures_formset(data=data,
                                             initial=initial.get('pictures', None),
                                             prefix=pictures_prefix)
        else:
            self.pictures = pictures_formset(data=data, prefix=pictures_prefix)

        type_attr_prices_prefix = "type_attribute_prices"
        TypeAttributePriceFormSet = formset_factory(TypeAttributePriceForm,
                                                    formset=NoEmptyBaseFormSet,
                                                    extra=get_formset_extra(data, type_attr_prices_prefix),
                                                    can_delete=True)
        if initial:
            self.type_attribute_prices = TypeAttributePriceFormSet(
                data=data, initial=initial.get('type_attribute_prices', None),
                prefix=type_attr_prices_prefix)
        else:
            self.type_attribute_prices = TypeAttributePriceFormSet(
                data=data, prefix=type_attr_prices_prefix)

        type_attr_weights_prefix = "type_attribute_weights"
        TypeAttributeWeightFormSet = formset_factory(TypeAttributeWeightForm,
                                                     formset=NoEmptyBaseFormSet,
                                                     extra=get_formset_extra(data, type_attr_weights_prefix),
                                                     can_delete=True)
        if initial:
            self.type_attribute_weights = TypeAttributeWeightFormSet(
                data=data, initial=initial.get('type_attribute_weights', None),
                prefix=type_attr_weights_prefix)
        else:
            self.type_attribute_weights = TypeAttributeWeightFormSet(
                data=data, prefix=type_attr_weights_prefix)

        varattr_prefix = "varattrs"
        VarattrFormset = formset_factory(ProductTypeVarAttrForm,
                                         formset=NoEmptyBaseFormSet,
                                         extra=get_formset_extra(data, varattr_prefix),
                                         can_delete=True)
        if initial.get('varattrs_initials', None):
            self.varattrs = VarattrFormset(data=data, prefix=varattr_prefix,
                                initial=initial.get('varattrs_initials', None))
        else:
            self.varattrs = VarattrFormset(data=data, prefix=varattr_prefix)

        barcodes_prefix = "barcodes"
        BarcodeFormset = formset_factory(BarcodeForm,
                                         formset=NoEmptyBaseFormSet,
                                         extra=get_formset_extra(data, barcodes_prefix),
                                         can_delete=True)
        if initial.get('barcodes_initials', None):
            self.barcodes = BarcodeFormset(data=data, prefix=barcodes_prefix,
                                initial=initial.get('barcodes_initials', None))
        else:
            self.barcodes = BarcodeFormset(data=data, prefix=barcodes_prefix)

        extrefs_prefix = "externalrefs"
        ExternalRefFormset = formset_factory(ExternalRefForm,
                                             formset=NoEmptyBaseFormSet,
                                             extra=get_formset_extra(data, extrefs_prefix),
                                             can_delete=True)
        if initial.get('externalrefs_initials', None):
            self.externalrefs = ExternalRefFormset(data=data, prefix=extrefs_prefix,
                                initial=initial.get('externalrefs_initials', None))
        else:
            self.externalrefs = ExternalRefFormset(data=data, prefix=extrefs_prefix)

        _prefix = "ordersettings"
        OrderSettingFormset = formset_factory(OrderSettingForm,
                                             formset=NoEmptyBaseFormSet,
                                             extra=get_formset_extra(data, _prefix),
                                             can_delete=True)
        if initial.get('ordersettings_initials', None):
            self.ordersettings = OrderSettingFormset(data=data, prefix=_prefix,
                                initial=initial.get('ordersettings_initials', None))
        else:
            self.ordersettings = OrderSettingFormset(data=data, prefix=_prefix)

        self.fields['shop_ids'] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=initial.get('shop_ids'),
            required=False,
        )

    def clean(self):
        self._clean_barcodes()
        self._clean_externalrefs()
        return super(ProductForm, self).clean()

    def clean_valid_to(self):
        valid_from = self.cleaned_data['valid_from']
        valid_to = self.cleaned_data['valid_to']

        if valid_from and valid_to and valid_to < valid_from:
            raise forms.ValidationError(
                _("Starting date can not be set past this sale's "
                  "expiration date."))
        elif valid_to and valid_to < date.today():
            raise forms.ValidationError(
                _("Expiration date can not be set before today."))
        return valid_to

    def clean_available_to(self):
        available_from = self.cleaned_data['available_from']
        available_to = self.cleaned_data['available_to']

        if available_from and available_to and available_to < available_from:
            raise forms.ValidationError(
                _("Starting date can not be set past this sale's "
                  "expiration date."))
        elif available_to and available_to < date.today():
            raise forms.ValidationError(
                _("Expiration date can not be set before today."))
        return available_to

    def clean_standard_weight(self):
        valid_taws = [taw for taw in self.type_attribute_weights.cleaned_data
                      if not taw['DELETE']]
        standard_weight = self.cleaned_data.get('standard_weight', None)
        if not valid_taws and not standard_weight:
            raise forms.ValidationError(_(
                'You must enter a Standard Weight, or enter a weight for at '
                'least one type of item.'))
        return standard_weight

    def clean_normal_price(self):
        valid_taps = [tap for tap in self.type_attribute_prices.cleaned_data
                      if not tap['DELETE']]
        normal_price = self.cleaned_data.get('normal_price', None)
        if not valid_taps and not normal_price:
            raise forms.ValidationError(_(
                'You must enter a Unified price, or enter a price for at '
                'least one type of item.'))
        return normal_price

    def _clean_barcodes(self):
        shops = json.loads(self.cleaned_data['shop_ids'])

        # In one shop, cannot have 2 same product barcode for two sale items.
        upcs = []
        for barcode in self.barcodes:
            barcode.full_clean()
            if not barcode.cleaned_data \
                    or not barcode.cleaned_data['upc'] \
                    or barcode.cleaned_data['DELETE']:
                continue
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

        if shops == []:
            # barcodes are now optional for global sales, so empty upcs are OK.
            filled_upcs = [_id for _id in upcs if _id]
            if len(filled_upcs) > len(set(filled_upcs)):
                raise forms.ValidationError(_("You cannot use two same product barcodes."))
        else:
            if len(upcs) > len(set(upcs)):
                raise forms.ValidationError(_("You cannot use two same product barcodes."))

    def _clean_externalrefs(self):
        shops = json.loads(self.cleaned_data['shop_ids'])

        # In one shop, cannot have 2 same external id for two sale items.
        exids = []
        for externalref in self.externalrefs:
            externalref.full_clean()
            if not externalref.cleaned_data \
                    or not externalref.cleaned_data['external_id'] \
                    or externalref.cleaned_data['DELETE']:
                continue
            new_exid = externalref.cleaned_data['external_id']
            old_exid = externalref.initial.get('external_id')
            exids.append(new_exid)
            if old_exid and old_exid == new_exid:
                continue
            refs_with_same_exid = ExternalRef.objects.filter(external_id=new_exid)
            for ref in refs_with_same_exid:
                pro = Product.objects.get(sale=ref.sale)
                if pro.valid_to and pro.valid_to < date.today():
                    continue
                # check: 1. the same external_id is in global shop when current sale in global shop.
                #        2. the same external_id is in same shop.
                shops_id = [s.id for s in ref.sale.shops.all()]
                if len(shops_id) == 0 and len(shops) == 0:
                    raise forms.ValidationError(_("external refs %s already used in global market." % new_exid))
                elif len(set(shops_id).intersection(set(shops))):
                    raise forms.ValidationError(_("external refs %s already used in your shop." % new_exid))

        if shops == []:
            # optional for global sales, so empty are OK.
            filled_exids = [_id for _id in exids if _id]
            if len(filled_exids) > len(set(filled_exids)):
                raise forms.ValidationError(_("You cannot use two same external refs."))
        else:
            if len(exids) > len(set(exids)):
                raise forms.ValidationError(_("You cannot use two same external refs."))

class ProductTypeVarAttrForm(forms.Form):
    type = forms.IntegerField(required=False)
    attr = forms.IntegerField(required=False)
    name = forms.CharField(required=False)
    value = forms.CharField(required=False)

class BarcodeForm(forms.Form):
    brand_attribute = forms.IntegerField(required=False)
    common_attribute = forms.IntegerField(required=False)
    upc = forms.CharField(label=_("Barcode"), required=False)

class ExternalRefForm(forms.Form):
    brand_attribute = forms.IntegerField(required=False)
    common_attribute = forms.IntegerField(required=False)
    external_id = forms.CharField(label=_("External Ref"), required=False)

class OrderSettingForm(forms.Form):
    brand_attribute = forms.IntegerField(required=False)
    common_attribute = forms.IntegerField(required=False)
    require_confirm = forms.BooleanField(label=_("Order require confirmation"))

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
                      ('product__available_from',_("Starting date")),
                      ('product__available_to',_("Expiration date")),
                     }
    order_by1 = forms.ChoiceField(required=False,choices=ORDER_BY_ITEMS)
    order_by2 = forms.ChoiceField(required=False,choices=ORDER_BY_ITEMS)
    search_by = forms.CharField(required=False)


class ShippingForm(forms.Form):
    handling_fee = forms.FloatField(
        label='Handling fee',
        widget=forms.TextInput(attrs={'class': 'handling_fee_input'}),
        required=False)
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

        self.fields['flat_rate'] = forms.FloatField(
            label=_('Flat rate'),
            widget=forms.TextInput(attrs={'class': 'inputM'}),
            required=False)
