from django import forms
from models import UserProfile
from globalsettings import get_setting

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        
    def __init__(self,*args,**kwargs):
        super(UserProfileForm,self).__init__(*args,**kwargs)
        if 'instance' not in kwargs.keys():
            self.fields['language'].initial = get_setting('default_language')
