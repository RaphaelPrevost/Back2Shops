'''
Created on 2012. 3. 28.

@author: Julian
'''
from django import forms
from accounts.models import Brand, UserProfile
from sales.models import ProductCategory, ProductType
from brandings.models import Branding
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
import settings

class SABrandForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    
    class Meta:
        model = Brand
        
class BaseUserForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    username = forms.CharField(label=_("Username"))
    email = forms.EmailField(label=_("E-mail"))
    language = forms.ChoiceField(label=_("language"), choices=settings.LANGUAGES)
    is_superuser = forms.BooleanField(label=_("Super admin"), required=False)
    
    class Meta:
        model = UserProfile
        exclude=('user',)

    def clean(self):
        cleaned_data = super(BaseUserForm,self).clean()
        is_superuser = cleaned_data.get('is_superuser')
        work_for = cleaned_data.get('work_for')
        if is_superuser:
            cleaned_data['work_for'] = None
        else:
            if work_for is None:
                self._errors['work_for'] = self.error_class([_('Normal admin must select a brand.')])
                del cleaned_data['work_for']
        return cleaned_data

class SACreateUserForm(BaseUserForm):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)
    
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
        user.is_superuser = self.cleaned_data['is_superuser']
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
        self.fields['is_superuser'].initial = self.instance.user.is_superuser
        self.fields['is_active'].initial = self.instance.user.is_active
        
    def save(self, commit=True):
        self.instance = super(SAUserForm, self).save(commit=False)
        self.instance.user.email = self.cleaned_data['email']
        self.instance.user.is_superuser = self.cleaned_data['is_superuser']
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