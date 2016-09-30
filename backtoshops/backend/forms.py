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


"""
Created on 2012. 3. 28.

@author: Julian
"""
import settings
from django import forms
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.forms.models import fields_for_model
from django.utils.translation import ugettext_lazy as _

from address.models import Address
from accounts.models import Brand
from accounts.models import UserProfile
from brandsettings import get_ba_settings
from brandsettings import save_ba_settings
from common.constants import USERS_ROLE
from globalsettings import get_setting
from globalsettings.models import GlobalSettings
from sales.models import ProductCurrency
from sales.models import WeightUnit
from shippings.models import Carrier
from taxes.models import Rate
from widgets import AdvancedFileInput


DISABLED_WIDGET_ATTRS = {'class': 'disabled', 'disabled': True}
class CountryField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return _(obj.printable_name)

class SABrandForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    
    logo = forms.ImageField(widget=AdvancedFileInput)

    class Meta:
        model = Brand
        exclude = ('address', )

    def __init__(self, instance=None, *args, **kwargs):
        _fields = ('address', 'zipcode', 'city', 'country', 'province_code')
        _initial = model_to_dict(instance.address, _fields) if instance is not None else {}

        widgets = {
            'zipcode': forms.TextInput(attrs={'class': 'inputXS'}),
            'city': forms.TextInput(attrs={'class': 'inputM'}),
            #'country': CountryField(queryset=Country.objects.all(), empty_label=_('Select a country'), to_field_name='country'),
            'province_code': forms.HiddenInput(),
            'business_reg_number': forms.TextInput(attrs={'class': 'inputM'}),
            'tax_reg_number': forms.TextInput(attrs={'class': 'inputM'}),
        }
        kwargs['initial'].update(_initial)
        super(SABrandForm, self).__init__(instance=instance, *args, **kwargs)
        self.fields.update(fields_for_model(Address, _fields, widgets=widgets))

    def save(self, *args, **kwargs):
        if self.instance.address_id:
            addr = self.instance.address
        else:
            addr = Address()
        addr.address = self.cleaned_data['address']
        addr.zipcode = self.cleaned_data['zipcode']
        addr.city = self.cleaned_data['city']
        addr.country = self.cleaned_data['country']
        addr.province_code = self.cleaned_data['province_code']
        addr.save()

        self.instance.address = addr
        brand = super(SABrandForm, self).save(*args, **kwargs)
        return brand

class BaseUserForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    username = forms.CharField(label=_("Username"))
    email = forms.EmailField(label=_("E-mail"))
    role = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    language = forms.ChoiceField(
        label=_("language"),
        choices=[(k, _(v)) for k, v in settings.LANGUAGES_2])
#    is_superuser = forms.BooleanField(label=_("Super admin"), required=False)

    class Meta:
        model = UserProfile
        exclude = ('user',)

   # def clean(self):
   #     cleaned_data = super(BaseUserForm,self).clean()
   #     is_superuser = cleaned_data.get('is_superuser')
   #     work_for = cleaned_data.get('work_for')
   #     if is_superuser:
   #         cleaned_data['work_for'] = None
   #     else:
   #         if work_for is None:
   #             self._errors['work_for'] = self.error_class(
   #                 [_('Normal admin must select a brand.')])
   #             del cleaned_data['work_for']
   #     return cleaned_data


class SACreateUserForm(BaseUserForm):
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Confirm password"),
                                widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            _("A user with that username already exists."))

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(
                _("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        user_profile = super(SACreateUserForm, self).save(commit=False)
        user = User.objects.create_user(self.cleaned_data["username"],
                                        self.cleaned_data["email"],
                                        self.cleaned_data["password1"])
        user.is_staff = True
#        user.is_superuser = self.cleaned_data['is_superuser']
        user.is_superuser = False
        user.save()
        user_profile.user = user
        user_profile.role = USERS_ROLE.ADMIN
        if commit:
            user_profile.save()
        return user_profile


class SAUserForm(BaseUserForm):
    is_active = forms.BooleanField(label=_("Active"), required=False)

    def __init__(self, *args, **kwargs):
        super(SAUserForm, self).__init__(*args, **kwargs)
        self.fields['username'].initial = self.instance.user.username
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['email'].initial = self.instance.user.email
#        self.fields['is_superuser'].initial = self.instance.user.is_superuser
        self.fields['is_active'].initial = self.instance.user.is_active

    def save(self, commit=True):
        self.instance = super(SAUserForm, self).save(commit=False)
        self.instance.user.email = self.cleaned_data['email']
#        self.instance.user.is_superuser = self.cleaned_data['is_superuser']
        self.instance.user.is_active = self.cleaned_data['is_active']
        self.instance.user.save()
        self.instance.role = USERS_ROLE.ADMIN
        if commit:
            self.instance.save()
        return self.instance


class CategoryTypeForm(forms.ModelForm):
    class Meta:
        from sales.models import CategoryTypeMap
        model = CategoryTypeMap


class SACarrierForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

    class Meta:
        model = Carrier


class SASettingsForm(forms.Form):
    error_css_class = 'error'
    required_css_class = 'required'

    default_language = forms.ChoiceField(
        choices=[(k, _(v)) for k, v in settings.LANGUAGES_2],
        label=_('Default language'))
    default_currency = forms.ChoiceField(
        choices=[(s, s) for s in
                 ProductCurrency.objects.all().values_list('code', flat=True)],
        label=_('Default currency'))
    default_weight_unit = forms.ChoiceField(
        choices=[(s, s) for s in
                 WeightUnit.objects.all().values_list('key', flat=True)],
        label=_('Default weight unit'))
    front_business_account_allowed = forms.CharField(
        label=_("Allow front users to register Business Accounts"),
        widget=forms.CheckboxInput(),
        required=True)
    front_personal_account_allowed = forms.CharField(
        label=_("Allow front users to register Personal Accounts"),
        widget=forms.CheckboxInput(),
        required=True)

    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    username = forms.CharField(label=_('Administrator login'))
    email = forms.EmailField(label=_('Administrator e-mail'))
    new_password1 = forms.CharField(
        label=_('New administrative password'),
        widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(
        label=_('Confirm new password'),
        widget=forms.PasswordInput,
        required=False)

    def __init__(self, user=None, *args, **kwargs):
        initial = kwargs.get('initial', {})
        global_settings = GlobalSettings.objects.all()
        for global_setting in global_settings:
            key = global_setting.key
            initial[key] = global_setting.value
            if key in ('front_personal_account_allowed',
                       'front_business_account_allowed'):
                initial[key] = initial.get(key) == 'True'
        if user is not None:
            initial['username'] = getattr(user, 'username', '')
            initial['email'] = getattr(user, 'email', '')
        super(SASettingsForm, self).__init__(initial=initial, *args, **kwargs)

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1", "")
        new_password2 = self.cleaned_data["new_password2"]
        if new_password1 != new_password2:
            raise forms.ValidationError(
                _("The two password fields didn't match."))
        return new_password2

    def clean_front_personal_account_allowed(self):
        data = super(SASettingsForm, self).clean()
        p_account_allowed = data.get('front_personal_account_allowed')
        b_account_allowed = data.get('front_business_account_allowed')
        if p_account_allowed != 'True' and b_account_allowed != 'True':
            raise forms.ValidationError(
                    {'front_personal_account_allowed':
                        [_("At least one of user account should be allowed.")]})
        return p_account_allowed


class SABrandSettingsForm(forms.Form):
    error_css_class = 'error'
    required_css_class = 'required'

    default_currency = forms.ChoiceField(
        choices=[(s, s) for s in
                 ProductCurrency.objects.all().values_list('code', flat=True)],
        label=_('Default Currency'),
        required=False)
    default_payment_period = forms.IntegerField(
        label=_('Default Payment Period'),
        widget=forms.TextInput(attrs={'class': 'inputXS'}),
        required=False)
    default_shipment_period = forms.IntegerField(
        label=_('Default Shipment Period'),
        widget=forms.TextInput(attrs={'class': 'inputXS'}),
        required=False)
    starting_invoice_number = forms.IntegerField(
        label=_('Starting Invoice Number'),
        required=False)
    use_after_tax_price = forms.CharField(
        widget=forms.CheckboxInput(),
        label=_('Use After-Tax retail prices'))
    order_require_confirmation = forms.CharField(
        widget=forms.CheckboxInput(),
        label=_('Order Require Confirmation'))
    unique_items = forms.CharField(
        widget=forms.CheckboxInput(),
        label=_('Unique Items'))

    def __init__(self, user=None, having_orders=False, *args, **kwargs):
        initial = kwargs.get('initial', {})
        if user is not None:
            initial = get_ba_settings(user).copy()
            initial['default_currency'] = initial.get('default_currency') \
                                       or get_setting('default_currency')
            initial['starting_invoice_number'] = initial.get('starting_invoice_number') \
                                       or get_setting('starting_invoice_number')
            initial['use_after_tax_price'] = initial.get('use_after_tax_price') \
                                       or get_setting('use_after_tax_price')
            initial['use_after_tax_price'] = initial['use_after_tax_price'] == 'True'
            initial['order_require_confirmation'] = initial.get('order_require_confirmation') == 'True'
            initial['unique_items'] = initial.get('unique_items') == 'True'

        super(SABrandSettingsForm, self).__init__(initial=initial, *args, **kwargs)
        if having_orders:
            self.fields['use_after_tax_price'].widget = \
                    forms.CheckboxInput({'disabled': 'true'})

    def clean_default_payment_period(self):
        data = self.cleaned_data
        value = data.get('default_payment_period')
        if value and value < 0:
            raise forms.ValidationError(
                    {'default_payment_period':
                        [_("Please input positive integer.")]})
        return value

    def clean_default_shipment_period(self):
        data = self.cleaned_data
        value = data.get('default_shipment_period')
        if value and value < 0:
            raise forms.ValidationError(
                    {'default_shipment_period':
                        [_("Please input positive integer.")]})
        return value

    def clean_starting_invoice_number(self):
        data = self.cleaned_data
        value = data.get('starting_invoice_number')
        if value and value < 0:
            raise forms.ValidationError(
                    {'starting_invoice_number':
                        [_("Please input positive integer.")]})
        return value

    def save(self, user):
        save_ba_settings(user, self.cleaned_data)

class SATaxForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

    class Meta:
        model = Rate
        widgets = {
            'province': forms.Select,
            'shipping_to_province': forms.Select,
            'apply_after': forms.Select,
            'display_on_front': forms.CheckboxInput,
            'taxable': forms.CheckboxInput,
            'applies_to_personal_accounts': forms.CheckboxInput,
            'applies_to_business_accounts': forms.CheckboxInput,
        }

    def __init__(self, *args, **kwargs):
        super(SATaxForm, self).__init__(*args, **kwargs)
        self.fields['applies_to'].empty_label = _('Everything')
        self.fields['shipping_to_region'].empty_label = _('Worldwide')
        if get_setting('front_personal_account_allowed') != 'True':
            self.fields['applies_to_personal_accounts'].widget = forms.HiddenInput()
        if get_setting('front_business_account_allowed') != 'True':
            self.fields['applies_to_business_accounts'].widget = forms.HiddenInput()

    def clean(self):
        if self.cleaned_data['shipping_to_region']:
            self.cleaned_data['display_on_front'] = None
        if self.cleaned_data['applies_to']:
            self.cleaned_data['taxable'] = None
        return self.cleaned_data
