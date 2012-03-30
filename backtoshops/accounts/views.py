# Create your views here.
from django import http
from django.utils.translation import check_for_language
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

def home_page(request):
    """
    returns index.html to non-super-admin
    returns sa_index.html to super admin.
    """
    if request.user.is_superuser: #== super admin
        return render_to_response('sa_index.html', context_instance=RequestContext(request))
    else: #non super admin
        return render_to_response('index.html', context_instance=RequestContext(request))

def set_language(request):
    """
    Redirect to a given url while setting the chosen language in the
    session or cookie. The url and the language code need to be
    specified in the request parameters.

    Since this view changes how the user will see the rest of the site, it must
    only be accessed as a POST request. If called as a GET request, it will
    redirect to the page in the request (the 'next' parameter) without changing
    any state.
    """
    _next = request.REQUEST.get('next', None)
    if not _next:
        _next = request.META.get('HTTP_REFERER', None)
    if not _next:
        _next = '/'
    response = http.HttpResponseRedirect(_next)
    if request.method == 'POST':
        lang_code = request.POST.get('language', None)
        if lang_code and check_for_language(lang_code):
            try:
                p = request.user.get_profile()
                p.language = lang_code
                p.save()
            except: #super admin doesn't have profile.
                pass
            if hasattr(request, 'session'):
                request.session['django_language'] = lang_code
            else:
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
    return response