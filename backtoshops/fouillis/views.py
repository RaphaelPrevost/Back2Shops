import logging
import urlparse
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from globalsettings import get_setting

from common.constants import USERS_ROLE


DEFAULT_LOGIN_URL = "/"

def super_admin_required(function=None,
                         redirect_field_name=REDIRECT_FIELD_NAME,
                         login_url="/"):
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

def admin_required(function=None,
                   redirect_field_name=REDIRECT_FIELD_NAME,
                   login_url=DEFAULT_LOGIN_URL):
    """
    this verifies the user is logged in as brand admin,
    else it will redirect to login_url.
    """
    def __test_func(u):
        if not u.is_authenticated():
            return False

        if u.is_superuser:
            return False

        return u.get_profile().role == USERS_ROLE.ADMIN

    actual_decorator = user_passes_test(
        __test_func,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def admin_upper_required(function=None,
                         redirect_field_name=REDIRECT_FIELD_NAME,
                         login_url=DEFAULT_LOGIN_URL,
                         super_allowed=True):
    """
    this verifies the user is logged in as brand admin or upper level,
    else it will redirect to login_url.
    """

    def __test_func(u):
        if not u.is_authenticated():
            return False

        if u.is_superuser:
            return super_allowed

        return u.get_profile().role <= USERS_ROLE.ADMIN

    actual_decorator = user_passes_test(
        __test_func,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def manager_required(function=None,
                     redirect_field_name=REDIRECT_FIELD_NAME,
                     login_url=DEFAULT_LOGIN_URL):
    """
    this verifies the user is logged in as manager,
    else it will redirect to login_url.
    """
    def __test_func(u):
        if not u.is_authenticated():
            return False

        if u.is_superuser:
            return False

        return u.get_profile().role == USERS_ROLE.MANAGER

    actual_decorator = user_passes_test(
        __test_func,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def manager_upper_required(function=None,
                           redirect_field_name=REDIRECT_FIELD_NAME,
                           login_url=DEFAULT_LOGIN_URL,
                           super_allowed=True):
    """
    this verifies the user is logged in as manager or upper level,
    else it will redirect to login_url.
    """
    def __test_func(u):
        if not u.is_authenticated():
            return False

        if u.is_superuser:
            return super_allowed

        return u.get_profile().role <= USERS_ROLE.MANAGER

    actual_decorator = user_passes_test(
        __test_func,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def shop_manager_upper_required(function=None,
                                redirect_field_name=REDIRECT_FIELD_NAME,
                                login_url=DEFAULT_LOGIN_URL,
                                super_allowed=True):
    """
    this verifies the user is logged in as shop manager or upper level,
    else it will redirect to login_url.
    """

    def __test_func(u):
        if not u.is_authenticated():
            return False

        if u.is_superuser:
            return super_allowed

        if u.get_profile().role < USERS_ROLE.MANAGER:
            return True

        return (u.get_profile().role == USERS_ROLE.MANAGER and
                len(u.get_profile().shops.all()) > 0)

    actual_decorator = user_passes_test(
        __test_func,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def operator_required(function=None,
                      redirect_field_name=REDIRECT_FIELD_NAME,
                      login_url=DEFAULT_LOGIN_URL):
    def __test_func(u):
        if not u.is_authenticated():
            return False

        if u.is_superuser:
            return False

        return u.get_profile().role == USERS_ROLE.OPERATOR

    actual_decorator = user_passes_test(
        __test_func,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def operator_upper_required(function=None,
                            redirect_field_name=REDIRECT_FIELD_NAME,
                            login_url=DEFAULT_LOGIN_URL,
                            super_allowed=True):
    def __test_func(u):
        if not u.is_authenticated():
            return False

        if u.is_superuser:
            return super_allowed

        return u.get_profile().role <= USERS_ROLE.OPERATOR

    actual_decorator = user_passes_test(
        __test_func,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


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
