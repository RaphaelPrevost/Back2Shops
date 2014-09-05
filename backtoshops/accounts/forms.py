import logging
from django import forms
from models import UserProfile
from globalsettings import get_setting
import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from common.constants import USERS_ROLE
from shops.models import Shop

ADM_CHOICES = (
    ("", _("Please select user's role")),
    (USERS_ROLE.MANAGER, _('Manager')),
    (USERS_ROLE.OPERATOR, _('Operator')),
)

OP_CHOICES = (
    (USERS_ROLE.OPERATOR, _('Operator')),
)

def get_role_field(request):
    profile = request.user.get_profile()
    if profile.role == USERS_ROLE.ADMIN:
        choices = ADM_CHOICES
    else:
        choices = OP_CHOICES

    return forms.ChoiceField(
            label=_("Role"),
            required=True,
            choices=choices
        )

def get_manager_shops(request=None, user=None):
    own_shops = None
    if user is None:
        shops = Shop.objects.filter(
            Q(mother_brand = request.user.get_profile().work_for,
              owner__isnull=True))
    else:
        own_shops =  user.get_profile().shops.all()
        shops = Shop.objects.filter(
            Q(mother_brand = user.get_profile().work_for,
              owner__isnull=True) |
            Q(pk__in=own_shops))

    field = forms.ModelMultipleChoiceField(
        label = _("Shops"),
        required=False,
        queryset=shops,
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'checkbox'}))

    return field,  own_shops or None

def get_operator_shops(request, user=None,):
    own_shops = None
    req_u_profile = request.user.get_profile()
    if req_u_profile.role == USERS_ROLE.ADMIN:
        shops = Shop.objects.filter(
            Q(mother_brand = req_u_profile.work_for))
    elif req_u_profile.role == USERS_ROLE.MANAGER:
        shops = req_u_profile.shops.all()
    else:
        shops = []

    if user is not None:
        own_shops =  user.get_profile().shops.all()

    # Admin user could add global market operator.
    # ShopKeeper can only add his own shop's operator.
    if request.user.get_profile().role == USERS_ROLE.ADMIN:
        empty_label = "None"
    else:
        empty_label = None

    field = forms.ModelChoiceField(
        label = _("Shops"),
        required=False,
        queryset=shops,
        empty_label=empty_label,
        widget=forms.RadioSelect(
            attrs={'class': 'radiobox'}))
    return field, own_shops and own_shops[0].pk or (shops and shops[0].pk)


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
    language = forms.ChoiceField(label=_("language"),
                                 choices=settings.LANGUAGES_2)
    
    class Meta:
        model = UserProfile
        exclude=('user','work_for',)
        
    def __init__(self, request=None, *args, **kwargs):
        super(BaseOperatorForm,self).__init__(*args, **kwargs)
        self.request = request
        self.fields['role'] = get_role_field(request)
        self.fields['allow_internet_operate'] = forms.BooleanField(
            label=_("This Manager can add and edit Global sales"),
            required=False
        )

    def _new_role_is_manager(self):
        return (self.data['role'] and
                int(self.data['role'][0]) == USERS_ROLE.MANAGER)

    def _shops_owner_update(self):
        if not self._new_role_is_manager():
            return
        cur_own_shops = self.cleaned_data['shops']
        for shop in cur_own_shops:
            shop.owner = self.instance.user
            shop.save()

    def clean_allow_internet_operate(self):
        if not self._new_role_is_manager():
            return False
        return self.cleaned_data['allow_internet_operate']

    def _priority_check(self, shops):
        shops_id = [s.pk for s in shops]
        req_u_profile = self.request.user.get_profile()

        # shops' brand check
        for shop in shops:
            if shop.mother_brand != req_u_profile.work_for:
                logging.error("hack_error ? user %s trying to add "
                              "operator for other brand shop %s"
                              % (req_u_profile.user_id, shop.pk),
                              exc_info=True)
                raise forms.ValidationError(
                    _("The shops is not in your brands"))

        # Shopkeeper must owns the shops.
        if req_u_profile.role == USERS_ROLE.MANAGER:
            managed_shops = [s.pk for s in req_u_profile.shops.all()]
            not_owned_shops = set(shops_id) - set(managed_shops)
            if not_owned_shops:
                logging.error("hack_error ? user %s trying to add "
                              "operator for shops %s"
                              % (req_u_profile.user_id, not_owned_shops),
                              exc_info=True)
                raise forms.ValidationError(
                    _("You have no priority for access the shops"))

        # shopkeeper cannot add operator linked to no shops.
        if (req_u_profile.role == USERS_ROLE.MANAGER and
            len(shops_id) == 0):
            raise forms.ValidationError(
                _("You must link a shops for the user"))

    def clean_role(self):
        role = self.cleaned_data['role']
        user_profile = self.request.user.get_profile()
        if (role == USERS_ROLE.MANAGER and
            user_profile.role > USERS_ROLE.ADMIN):
            raise ValueError(_("You have no priority to create manager user"))
        return role

class CreateOperatorForm(BaseOperatorForm):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(CreateOperatorForm, self).__init__(*args, **kwargs)
        init_role = (self.request.POST and
                     self.request.POST.get('role') and
                     int(self.request.POST.get('role'))) or None
        if (init_role == USERS_ROLE.OPERATOR or
            self.request.user.get_profile().role == USERS_ROLE.MANAGER):
            shops_field, sel_shops = get_operator_shops(self.request)
        else:
            shops_field, sel_shops = get_manager_shops(request=self.request)
        self.fields['shops'] = shops_field
        if sel_shops is not None:
            self.initial['shops'] = sel_shops

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
        user = User.objects.create_user(self.cleaned_data["username"],
                                        self.cleaned_data["email"],
                                        self.cleaned_data["password1"])
        user.save()
        user_profile.user = user
        user_profile.work_for = self.request.user.get_profile().work_for
        if commit:
            user_profile.save()
            self._shops_owner_update()
            self.save_m2m()

        return user_profile

    def clean_shops(self):
        shops_id = [int(s) for s in self.data.getlist('shops')
                    if s.isdigit()]
        shops = Shop.objects.filter(pk__in=shops_id)
        if set([s.pk for s in shops]) - set(shops_id):
            logging.error("hack_error? user %s trying to add operator for "
                          "some not exist shops: %s"
                          % (self.request.user.pk,
                             set([s.pk for s in shops]) - set(shops_id)),
                          exc_info=True)
            raise forms.ValidationError(
                _("Operate shops not exist"))

        self._priority_check(shops)
        self.cleaned_data['shops'] = shops

        if not self._new_role_is_manager():
            return self.cleaned_data['shops']

        for shop in self.cleaned_data['shops']:
            if shop.owner is not None:
                raise forms.ValidationError(
                    _("Shop(%s)'s owner have already been set") % shop.name)
        return self.cleaned_data['shops']


class OperatorForm(BaseOperatorForm):
    is_active = forms.BooleanField(label=_("Active"), required=False)
    
    def __init__(self, *args, **kwargs):
        super(OperatorForm, self).__init__(*args, **kwargs)
        user = self.instance.user

        if user.get_profile().role == USERS_ROLE.MANAGER:
            shops_field, own_shops = get_manager_shops(self.request, user)
        else:
            shops_field, own_shops = get_operator_shops(self.request, user)

        self.fields['shops'] = shops_field
        self.fields['username'].initial = self.instance.user.username
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['email'].initial = self.instance.user.email
        self.fields['is_active'].initial = self.instance.user.is_active
        if own_shops is not None:
            self.initial['shops'] = own_shops

    def _shops_owner_update(self):
        super(OperatorForm, self)._shops_owner_update()
        user = self.instance.user

        if not self._new_role_is_manager():
            # Check whether the user owned some shops.
            reduce_shops = Shop.objects.filter(owner=user)
        else:
            # Check whether user's owned shops reduced.
            cur_own_shops = [s.pk for s in self.cleaned_data['shops']]
            reduce_shops = user.get_profile().shops.all().exclude(
                pk__in=cur_own_shops)
        for shop in reduce_shops:
            shop.owner_id = None
            shop.save()


    def clean_shops(self):
        shops_id = [int(s) for s in self.data.getlist('shops')
                    if s.isdigit()]
        shops = Shop.objects.filter(pk__in=shops_id)
        if set([s.pk for s in shops]) - set(shops_id):
            logging.error("hack_error? user %s trying to add operator for "
                          "some not exist shops: %s"
                          % (self.request.user.pk,
                             set([s.pk for s in shops]) - set(shops_id)),
                          exc_info=True)
            raise forms.ValidationError(
                _("Operate shops not exist"))

        self._priority_check(shops)
        self.cleaned_data['shops'] = shops

        if not self._new_role_is_manager():
            return self.cleaned_data['shops']

        for shop in self.cleaned_data['shops']:
            if (shop.owner is not None and
                shop.owner_id != self.instance.user.pk):
                raise forms.ValidationError(
                    _("Shop(%s)'s owner have already been set") % shop.name)
        return self.cleaned_data['shops']

    def save(self, commit=True):
        self.instance = super(OperatorForm, self).save(commit=False)
        self.instance.user.email = self.cleaned_data['email']
        self.instance.user.is_active = self.cleaned_data['is_active']
        self.instance.user.save()

        if commit:
            self.instance.save()
            self._shops_owner_update()
            self.save_m2m()

        return self.instance

class AjaxShopsForm(forms.Form):
    def __init__(self, instance=None, *args, **kwargs):
        super(AjaxShopsForm, self).__init__(*args, **kwargs)
        request = kwargs['initial'].get('request')
        users_id = request.GET.get('users_id')
        role_type = request.GET.get('role_type')

        user = None
        if users_id and int(users_id):
            user = User.objects.get(pk=users_id)

        if role_type and int(role_type) == USERS_ROLE.MANAGER:
            shops_field, own_shops = get_manager_shops(request, user)
        else:
            shops_field, own_shops = get_operator_shops(request, user)

        self.fields['shops'] =shops_field
        if own_shops is not None:
            self.initial['shops'] = own_shops
