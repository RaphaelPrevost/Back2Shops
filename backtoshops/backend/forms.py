'''
Created on 2012. 3. 28.

@author: Julian
'''
from django import forms
from accounts.models import Brand, UserProfile
from sales.models import ProductCategory, ProductType
from brandings.models import Branding
from sales.models import ProductCurrency
from globalsettings.models import GlobalSettings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
import settings
from widgets import AdvancedFileInput

class SABrandForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    
    logo = forms.ImageField(widget=AdvancedFileInput)
    
    class Meta:
        model = Brand
        
class BaseUserForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    username = forms.CharField(label=_("Username"))
    email = forms.EmailField(label=_("E-mail"))
    language = forms.ChoiceField(label=_("language"), choices=[(k, _(v)) for k, v in settings.LANGUAGES])
#    is_superuser = forms.BooleanField(label=_("Super admin"), required=False)
    
    class Meta:
        model = UserProfile
        exclude=('user',)

#    def clean(self):
#        cleaned_data = super(BaseUserForm,self).clean()
#        is_superuser = cleaned_data.get('is_superuser')
#        work_for = cleaned_data.get('work_for')
#        if is_superuser:
#            cleaned_data['work_for'] = None
#        else:
#            if work_for is None:
#                self._errors['work_for'] = self.error_class([_('Normal admin must select a brand.')])
#                del cleaned_data['work_for']
#        return cleaned_data

class SACreateUserForm(BaseUserForm):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Confirm password"), widget=forms.PasswordInput)
    
    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_("A user with that username already exists."))
        
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2
    
    def save(self, commit=True):
        user_profile = super(SACreateUserForm,self).save(commit=False)
        user = User.objects.create_user(self.cleaned_data["username"], self.cleaned_data["email"], self.cleaned_data["password1"])
        user.is_staff = True
#        user.is_superuser = self.cleaned_data['is_superuser']
        user.is_superuser = False
        user.save()
        user_profile.user = user
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
        if commit:
            self.instance.save()
        return self.instance
    
class SACategoryForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    
    class Meta:
        model = ProductCategory
            
class SAAttributeForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    
    class Meta:
        model = ProductType

class SABrandingForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    
    class Meta:
        model = Branding
        
class SASettingsForm(forms.Form):
    error_css_class = 'error'
    required_css_class = 'required'
    
    default_language = forms.ChoiceField(choices=[(k, _(v)) for k, v in settings.LANGUAGES], label=_('Default language'))
    default_currency = forms.ChoiceField(choices=[(s,s) for s in ProductCurrency.objects.all().values_list('code',flat=True)], label=_('Default currency'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    username = forms.CharField(label=_('Administrator login'))
    email = forms.EmailField(label=_('Administrator e-mail'))
    new_password1 = forms.CharField(label=_('New administrative password'), widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label=_('Confirm new password'), widget=forms.PasswordInput, required=False)
    
    def __init__(self, user=None, *args, **kwargs):
        initial = kwargs.get('initial', {})
        global_settings = GlobalSettings.objects.all()
        for global_setting in global_settings: 
            initial[global_setting.key] = global_setting.value
        if user is not None:
            initial['username'] = user.__dict__.get('username','')
            initial['email'] = user.__dict__.get('email','')
        super(SASettingsForm,self).__init__(initial=initial, *args, **kwargs)

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1", "")
        new_password2 = self.cleaned_data["new_password2"]
        if new_password1 != new_password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return new_password2
