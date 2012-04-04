# Create your views here.
from django import http
from django.utils.translation import check_for_language
from django.conf import settings
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from fouillis.views import BOLoginRequiredMixin
from models import Brand, UserProfile
from django.contrib.auth.models import User
import json
from globalsettings import get_setting
import forms

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
            except: 
                pass
            if hasattr(request, 'session'):
                request.session['django_language'] = lang_code
            else:
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
    return response

class BaseOperatorView(BOLoginRequiredMixin):
    """
    User is different from other models since it has User + UserProfile model.
    system uses create form and edit form and save method is overridden in the form.   
    """
    template_name = "operator.html"
    
    def get_context_data(self, **kwargs):
        kwargs.update({
            'user_pk': self.kwargs.get('pk', None),
            'users': User.objects.filter(is_staff=False, userprofile__work_for=self.request.user.get_profile().work_for),  
            'companies': Brand.objects.all(),
            'request': self.request,
        })
        if 'is_search' in self.__dict__ and self.is_search:
            kwargs.update({'users':self.users,
                           'search_username': self.search_username,
                           })
        return kwargs
    
    def get_form_kwargs(self):
        """
        overriding this for avoid any form binding during search post.
        """
        if 'is_search' in self.__dict__ and self.is_search:
            kwargs = {'initial': self.get_initial(),} 
            if 'object' in self.__dict__:
                kwargs.update({'instance': self.object,})
            return kwargs
        else:
            kwargs = super(BaseOperatorView,self).get_form_kwargs() 
            kwargs.update({'request': self.request,})
            return kwargs 
    
    def post(self, request, *args, **kwargs):
        self.is_search = request.POST.get('search',False)
        if self.is_search: #search case
            self.search_username=request.POST.get('username','')
            self.users=User.objects.filter(username__contains=self.search_username, is_staff=False, userprofile__work_for=self.request.user.get_profile().work_for)
            return self.get(request, *args, **kwargs)
        else:
            return super(BaseOperatorView,self).post(request, *args, **kwargs)
 
class CreateOperatorView(BaseOperatorView, CreateView):
    form_class = forms.CreateOperatorForm
    
    def get_success_url(self):
        new_id = User.objects.all().count()
        return reverse('edit_operator',args=[new_id])
    
    def get_initial(self):
        initials = super(CreateOperatorView,self).get_initial()
        initials.update({"language": get_setting('default_language')})
        return initials
    
class EditOperatorView(BaseOperatorView, UpdateView):
    """
    this class uses get_object overriding to make a fail safe call of UserProfile.
    in other words, if there is a User but it doesn't have UserProfile, Edit View will make one for the User.
    """
    form_class = forms.OperatorForm
    queryset = User.objects.all()
    
    def get_object(self):
        user = super(EditOperatorView,self).get_object()
        self.object, created = UserProfile.objects.get_or_create(user=user, defaults={"language": get_setting('default_language')})
        return self.object
    
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("edit_operator",args=[pk])

class DeleteOperatorView(BaseOperatorView, DeleteView):
    """
    same as the EditView, it also uses get_object overriding. 
    when deleting, first it deletes UserProfile and then delete user.
    """
    queryset = User.objects.all()
    
    def get_object(self):
        user = super(DeleteOperatorView,self).get_object()
        self.object, created = UserProfile.objects.get_or_create(user=user, defaults={"language": get_setting('default_language')})
        return self.object
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        self.object.delete()
        user.delete()
        return http.HttpResponse(content=json.dumps({"user_pk": self.kwargs.get('pk', None)}),
                            mimetype="application/json")
