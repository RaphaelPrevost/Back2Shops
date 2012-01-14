import logging
import urlparse
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

class LoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(LoginRequiredMixin, self).dispatch
        return login_required(bound_dispatch)(*args, **kwargs)

class BOLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(BOLoginRequiredMixin, self).dispatch
        return login_required(bound_dispatch, login_url="bo_login")(*args, **kwargs)


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
                if user.is_active and user.is_staff:
                    login(request, user)
                    request.session['django_language'] = user.get_profile().language
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
