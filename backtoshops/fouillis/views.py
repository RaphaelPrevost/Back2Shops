import logging
import urlparse
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from globalsettings import get_setting
from django.core.urlresolvers import reverse

from common.constants import USERS_ROLE


def super_admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    this verifies the user is logged in as superuser. else it will redirect to login_url.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    this verifies the user is logged in as brand admin,
    else it will redirect to login_url.
    """
    actual_decorator = user_passes_test(
        lambda u: not u.is_superuser and
                  (u.is_authenticated() and
                   u.is_staff and
                   u.get_profile().role == USERS_ROLE.ADMIN),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def admin_upper_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    this verifies the user is logged in as brand admin or upper level,
    else it will redirect to login_url.
    """

    actual_decorator = user_passes_test(
        lambda u: (u.is_authenticated() and u.is_superuser) or
                  (u.is_authenticated() and
                   u.is_staff and
                   not u.is_superuser and
                   u.get_profile().role <= USERS_ROLE.ADMIN),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def manager_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    this verifies the user is logged in as manager,
    else it will redirect to login_url.
    """
    actual_decorator = user_passes_test(
        lambda u: not u.is_superuser and
                  (u.is_authenticated() and
                   u.get_profile().role == USERS_ROLE.MANAGER),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def manager_upper_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    this verifies the user is logged in as manager or upper level,
    else it will redirect to login_url.
    """
    actual_decorator = user_passes_test(
        lambda u: (u.is_authenticated() and u.is_superuser) or
                  (u.is_authenticated() and
                   not u.is_superuser and
                   u.get_profile().role <= USERS_ROLE.MANAGER),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def shop_manager_upper_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    this verifies the user is logged in as shop manager or upper level,
    else it will redirect to login_url.
    """
    actual_decorator = user_passes_test(
        lambda u: (u.is_authenticated() and u.is_superuser) or
                  ((u.is_authenticated() and
                    not u.is_superuser and
                    u.get_profile().role < USERS_ROLE.MANAGER) or
                   (u.is_authenticated() and
                    u.get_profile().role == USERS_ROLE.MANAGER and
                    not u.is_superuser and
                    len(u.get_profile().shops.all()) > 0
                   )),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def operator_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    actual_decorator = user_passes_test(
        lambda u: not u.is_superuser and
                  (u.is_authenticated() and
                   u.get_profile().role == USERS_ROLE.OPERATOR),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def operator_upper_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    actual_decorator = user_passes_test(
        lambda u: (u.is_authenticated() and u.is_superuser) or
                  (u.is_authenticated() and
                   not u.is_superuser and
                   u.get_profile().role <= USERS_ROLE.OPERATOR),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

class LoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(LoginRequiredMixin, self).dispatch
        return login_required(bound_dispatch, login_url="/")(*args, **kwargs)

class BOLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(BOLoginRequiredMixin, self).dispatch
        return admin_required(bound_dispatch, login_url="/")(*args, **kwargs)

class SuperAdminLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(SuperAdminLoginRequiredMixin, self).dispatch
        return super_admin_required(bound_dispatch, login_url="/")(*args, **kwargs)

class AdminLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(AdminLoginRequiredMixin, self).dispatch
        return admin_required(bound_dispatch, login_url="/")(*args, **kwargs)

class AdminUpperLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(AdminUpperLoginRequiredMixin, self).dispatch
        return admin_upper_required(bound_dispatch, login_url="/")(*args, **kwargs)

class ManagerLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(ManagerLoginRequiredMixin, self).dispatch
        return manager_required(bound_dispatch, login_url="/")(*args, **kwargs)

class ManagerUpperLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(ManagerUpperLoginRequiredMixin, self).dispatch
        return manager_upper_required(bound_dispatch, login_url="/")(*args, **kwargs)

class ShopManagerUpperLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(ShopManagerUpperLoginRequiredMixin, self).dispatch
        return shop_manager_upper_required(bound_dispatch, login_url="/")(*args, **kwargs)

class OperatorLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(OperatorLoginRequiredMixin, self).dispatch
        return operator_required(bound_dispatch, login_url="/")(*args, **kwargs)

class OperatorUpperLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(OperatorUpperLoginRequiredMixin, self).dispatch
        return operator_upper_required(bound_dispatch, login_url="/")(*args, **kwargs)

logger = logging.getLogger('django')

def login_staff(request):
    if request.method == "POST":
        redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, '')
        print redirect_to
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    try:
                        request.session['django_language'] = user.get_profile().language
                    except:
                        request.session['django_language'] = get_setting('default_language')
                        
                    netloc = urlparse.urlparse(redirect_to)[1]

                    # Use default setting if redirect_to is empty
                    if not redirect_to:
                        redirect_to = '/'

                    # Security check -- don't allow redirection to a different
                    # host.
                    elif netloc and netloc != request.get_host():
                        redirect_to = '/'
                    return redirect(redirect_to)
    else:
        form = AuthenticationForm(request)
    return render(request, 'login.html', locals())
