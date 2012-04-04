import logging
import urlparse
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from globalsettings import get_setting
from django.core.urlresolvers import reverse

def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    this verifies the user is logged in and superuser. else it will redirect to login_url.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_staff ,
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
