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
from brandings.models import Branding
from common.constants import USERS_ROLE
from globalsettings import get_setting
from globalsettings.models import GlobalSettings
from sales.models import ProductCategory
from sales.models import ProductCurrency
from sales.models import ProductType
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
        choices=[(k, _(v)) for k, v in settings.LANGUAGES])
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


class SACategoryForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    thumbnail = forms.ImageField(widget=AdvancedFileInput)
    picture = forms.ImageField(widget=AdvancedFileInput)

    def __init__(self, *args, **kwargs):
        super(SACategoryForm, self).__init__(*args, **kwargs)
        cat = kwargs.get('instance', None)
        if cat:
            if not cat.valid:
                for field in self.fields.iterkeys():
                    self.fields[field].widget.attrs.update(DISABLED_WIDGET_ATTRS)

    class Meta:
        model = ProductCategory
        exclude = ['valid', ]


class SAAttributeForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        super(SAAttributeForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = ProductCategory.objects.filter(valid=True)
        sa_attr = kwargs.get('instance', None)
        if sa_attr:
            if not sa_attr.valid:
                for field in self.fields.iterkeys():
                    self.fields[field].widget.attrs.update(DISABLED_WIDGET_ATTRS)


    class Meta:
        model = ProductType
        exclude = ['valid', ]

class SACommonAttributeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SACommonAttributeForm, self).__init__(*args, **kwargs)
        common_attr = kwargs.get('instance', None)
        if common_attr:
            if not common_attr.valid:
                for field in self.fields.iterkeys():
                    self.fields[field].widget.attrs.update(DISABLED_WIDGET_ATTRS)

    class Meta:
        from attributes.models import CommonAttribute
        model = CommonAttribute
        exclude = ['valid', ]

class SACarrierForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

    class Meta:
        model = Carrier


class SABrandingForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    
    class Meta:
        model = Branding


class SASettingsForm(forms.Form):
    error_css_class = 'error'
    required_css_class = 'required'
    
    default_language = forms.ChoiceField(
        choices=[(k, _(v)) for k, v in settings.LANGUAGES],
        label=_('Default language'))
    default_currency = forms.ChoiceField(
        choices=[(s, s) for s in
                 ProductCurrency.objects.all().values_list('code', flat=True)],
        label=_('Default currency'))
    default_weight_unit = forms.ChoiceField(
        choices=[(s, s) for s in
                 WeightUnit.objects.all().values_list('key', flat=True)],
        label=_('Default weight unit'))
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
            initial[global_setting.key] = global_setting.value
        if user is not None:
            initial['username'] = user.__dict__.get('username', '')
            initial['email'] = user.__dict__.get('email', '')
        super(SASettingsForm, self).__init__(initial=initial, *args, **kwargs)

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1", "")
        new_password2 = self.cleaned_data["new_password2"]
        if new_password1 != new_password2:
            raise forms.ValidationError(
                _("The two password fields didn't match."))
        return new_password2

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

    def __init__(self, user=None, *args, **kwargs):
        initial = kwargs.get('initial', {})
        if user is not None:
            initial = get_ba_settings(user).copy()
            initial['default_currency'] = initial.get('default_currency') \
                                       or get_setting('default_currency')
            initial['starting_invoice_number'] = initial.get('starting_invoice_number') \
                                       or get_setting('starting_invoice_number')
        super(SABrandSettingsForm, self).__init__(initial=initial, *args, **kwargs)

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
        }

    def __init__(self, *args, **kwargs):
        super(SATaxForm, self).__init__(*args, **kwargs)
        self.fields['applies_to'].empty_label = _('Everything')
        self.fields['shipping_to_region'].empty_label = _('Worldwide')

    def clean(self):
        if self.cleaned_data['shipping_to_region']:
            self.cleaned_data['display_on_front'] = None
        if self.cleaned_data['applies_to']:
            self.cleaned_data['taxable'] = None
        return self.cleaned_data
