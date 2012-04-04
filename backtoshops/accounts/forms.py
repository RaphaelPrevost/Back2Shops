from django import forms
from models import UserProfile
from globalsettings import get_setting
import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from shops.models import Shop

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        
    def __init__(self,*args,**kwargs):
        super(UserProfileForm,self).__init__(*args,**kwargs)
        if 'instance' not in kwargs.keys():
            self.fields['language'].initial = get_setting('default_language')

class BaseOperatorForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    username = forms.CharField(label=_("Username"))
    email = forms.EmailField(label=_("E-mail"))
    language = forms.ChoiceField(label=_("language"), choices=settings.LANGUAGES)
    
    class Meta:
        model = UserProfile
        exclude=('user','work_for',)
        
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.base_fields['shops'].queryset = Shop.objects.filter(mother_brand = request.user.get_profile().work_for)
        super(BaseOperatorForm,self).__init__(*args, **kwargs)

class CreateOperatorForm(BaseOperatorForm):
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
        user_profile = super(CreateOperatorForm,self).save(commit=False)
        user = User.objects.create_user(self.cleaned_data["username"], self.cleaned_data["email"], self.cleaned_data["password1"])
        user.save()
        user_profile.user = user
        user_profile.work_for = self.request.user.get_profile().work_for
        if commit:
            user_profile.save()
            self.save_m2m()
        return user_profile
    
class OperatorForm(BaseOperatorForm):
    is_active = forms.BooleanField(label=_("Active"), required=False)
    
    def __init__(self, *args, **kwargs):
        super(OperatorForm, self).__init__(*args, **kwargs)
        self.fields['username'].initial = self.instance.user.username
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['email'].initial = self.instance.user.email
        self.fields['is_active'].initial = self.instance.user.is_active
        
    def save(self, commit=True):
        self.instance = super(OperatorForm, self).save(commit=False)
        self.instance.user.email = self.cleaned_data['email']
        self.instance.user.is_active = self.cleaned_data['is_active']
        self.instance.user.save()
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
    