# Create your views here.
import json
from django.http import HttpResponse
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.models import User
from accounts.models import Brand, UserProfile
from sales.models import ProductCategory, ProductType
from globalsettings.models import GlobalSettings
from brandings.models import Branding
from globalsettings import get_setting
import forms

def superadmin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    this verifies the user is logged in and superuser. else it will redirect to login_url.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_superuser ,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

class SARequiredMixin(object):
    """
    this will be a basis mixin view for super admin pages.
    this utilizes superadmin_required decorator function.
    """
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(SARequiredMixin, self).dispatch
        return superadmin_required(bound_dispatch, login_url="/")(*args, **kwargs)   
     
class BaseBrandView(SARequiredMixin):
    template_name = "sa_brand.html"
    form_class = forms.SABrandForm
    model = Brand

    def get_context_data(self, **kwargs):
        kwargs.update({
            'brand_pk': self.kwargs.get('pk', None),
            'brands': Brand.objects.all(),
            'request': self.request,
        })
        return kwargs
    
class CreateBrandView(BaseBrandView, CreateView):
    def get_success_url(self):
        new_id = Brand.objects.all().count()
        return reverse('sa_edit_brand',args=[new_id])
    
class EditBrandView(BaseBrandView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("sa_edit_brand",args=[pk])

class DeleteBrandView(BaseBrandView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({"brand_pk": self.kwargs.get('pk', None)}),
                            mimetype="application/json")

class BaseUserView(SARequiredMixin):
    """
    User is different from other models since it has User + UserProfile model.
    system uses create form and edit form and save method is overridden in the form.   
    """
    template_name = "sa_user.html"
    
    def get_context_data(self, **kwargs):
        kwargs.update({
            'user_pk': self.kwargs.get('pk', None),
            'users': User.objects.filter(is_staff=True, is_superuser=False),  
            'companies': Brand.objects.all(),
            'request': self.request,
        })
        if 'is_search' in self.__dict__ and self.is_search:
            kwargs.update({'users':self.users,
                           'search_username': self.search_username,
                           })
            if 'search_brand' in self.__dict__:
                kwargs.update({'search_brand': self.search_brand,})
        
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
            return super(BaseUserView,self).get_form_kwargs()
    
    def post(self, request, *args, **kwargs):
        self.is_search = request.POST.get('search',False)
        if self.is_search: #search case
            self.search_username=request.POST.get('username','')
            self.users=User.objects.filter(username__contains=self.search_username, is_staff=True, is_superuser=False)
            try:
                self.search_brand=int(request.POST['company'])
                self.users=self.users.filter(userprofile__work_for=self.search_brand)
            except:
                pass
            return self.get(request, *args, **kwargs)
        else:
            return super(BaseUserView,self).post(request, *args, **kwargs)
 
class CreateUserView(BaseUserView, CreateView):
    form_class = forms.SACreateUserForm
    
    def get_success_url(self):
        new_id = User.objects.all().count()
        return reverse('sa_edit_user',args=[new_id])
    
    def get_initial(self):
        initials = super(CreateUserView,self).get_initial()
        initials.update({"language": get_setting('default_language')})
        return initials
    
class EditUserView(BaseUserView, UpdateView):
    """
    this class uses get_object overriding to make a fail safe call of UserProfile.
    in other words, if there is a User but it doesn't have UserProfile, Edit View will make one for the User.
    """
    form_class = forms.SAUserForm
    queryset = User.objects.all()
    
    def get_object(self):
        user = super(EditUserView,self).get_object()
        self.object, created = UserProfile.objects.get_or_create(user=user, defaults={"language": get_setting('default_language')})
        return self.object
    
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("sa_edit_user",args=[pk])

class DeleteUserView(BaseUserView, DeleteView):
    """
    same as the EditView, it also uses get_object overriding. 
    when deleting, first it deletes UserProfile and then delete user.
    """
    queryset = User.objects.all()
    
    def get_object(self):
        user = super(DeleteUserView,self).get_object()
        self.object, created = UserProfile.objects.get_or_create(user=user, defaults={"language": get_setting('default_language')})
        return self.object
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        self.object.delete()
        user.delete()
        return HttpResponse(content=json.dumps({"user_pk": self.kwargs.get('pk', None)}),
                            mimetype="application/json")

@superadmin_required
def ajax_user_search(request):
    """
    returns the user search result. currently this is not used since search user feature changed to form post.
    """
    if request.method=='POST':
        username=request.POST.get('username','')
        users=User.objects.filter(username__contains=username)
        try:
            brand=int(request.POST['company'])
            users=users.filter(userprofile__work_for=brand)
        except:
            pass
        
    return render_to_response('ajax/user_search.html', {'users':users,}, mimetype='text/html')

class BaseCategoryView(SARequiredMixin):
    template_name = "sa_category.html"
    form_class = forms.SACategoryForm
    model = ProductCategory

    def get_context_data(self, **kwargs):
        kwargs.update({
            'category_pk': self.kwargs.get('pk', None),
            'categories': ProductCategory.objects.all(),
            'request': self.request,
        })
        return kwargs
    
class CreateCategoryView(BaseCategoryView, CreateView):
    def get_success_url(self):
        new_id = ProductCategory.objects.all().count()
        return reverse('sa_edit_category',args=[new_id])
    
class EditCategoryView(BaseCategoryView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("sa_edit_category",args=[pk])

class DeleteCategoryView(BaseCategoryView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({"category_pk": self.kwargs.get('pk', None)}),
                            mimetype="application/json")
        
class BaseAttributeView(SARequiredMixin):
    template_name = "sa_attribute.html"
    form_class = forms.SAAttributeForm
    model = ProductType

    def get_context_data(self, **kwargs):
        kwargs.update({
            'attribute_pk': self.kwargs.get('pk', None),
            'attributes': ProductType.objects.all(),
            'request': self.request,
        })
        return kwargs
    
class CreateAttributeView(BaseAttributeView, CreateView):
    def get_success_url(self):
        new_id = ProductType.objects.all().count()
        return reverse('sa_edit_attribute',args=[new_id])
    
class EditAttributeView(BaseAttributeView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("sa_edit_attribute",args=[pk])

class DeleteAttributeView(BaseAttributeView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({"attribute_pk": self.kwargs.get('pk', None)}),
                            mimetype="application/json")

class BaseBrandingView(SARequiredMixin):
    template_name = "sa_branding.html"
    form_class = forms.SABrandingForm
    model = Branding

    def get_context_data(self, **kwargs):
        kwargs.update({
            'branding_pk': self.kwargs.get('pk', None),
            'brandings': Branding.objects.all(),
            'request': self.request,
        })
        return kwargs
    
class CreateBrandingView(BaseBrandingView, CreateView):
    def get_success_url(self):
        new_id = Branding.objects.all().count()
        return reverse('sa_edit_branding',args=[new_id])
    
class EditBrandingView(BaseBrandingView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("sa_edit_branding",args=[pk])

class DeleteBrandingView(BaseBrandingView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({"branding_pk": self.kwargs.get('pk', None)}),
                            mimetype="application/json")

@superadmin_required
def settings_view(request):
    is_saved = False
    if request.method == 'POST':
        form = forms.SASettingsForm(data=request.POST, user=request.user)
        if form.is_valid():
            global_settings = GlobalSettings.objects.all()
            for global_setting in global_settings: 
                global_setting.value = form.cleaned_data[global_setting.key]
                global_setting.save()
            user = User.objects.get(pk=request.user.pk)
            user.username = form.cleaned_data['username']
            user.email = form.cleaned_data['email']
            if form.cleaned_data['new_password1'] != '':
                user.set_password(form.cleaned_data['new_password1'])
            user.save()
            is_saved = True
    else:
        form = forms.SASettingsForm(user=request.user)
        
    return render_to_response('sa_settings.html',{'form':form, 'is_saved':is_saved, 'request':request, }, context_instance=RequestContext(request))
