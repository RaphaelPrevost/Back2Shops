# Create your views here.
import settings
import json
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage
from django.core.paginator import InvalidPage
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView

from accounts.models import Brand
from accounts.models import UserProfile
from attributes.models import CommonAttribute
from backend import forms
from brandings.models import Branding
from common.constants import USERS_ROLE
from fouillis.views import super_admin_required
from fouillis.views import admin_required
from globalsettings import get_setting
from globalsettings.models import GlobalSettings
from sales.models import ProductCategory
from sales.models import ProductType
from shippings.models import Carrier
from shippings.models import Service
from taxes.models import Rate


class SARequiredMixin(object):
    """
    this will be a basis mixin view for super admin pages.
    this utilizes super_admin_required decorator function.
    """
    def dispatch(self, *args, **kwargs):
        bound_dispatch = super(SARequiredMixin, self).dispatch
        return super_admin_required(bound_dispatch, login_url="/")(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        # general pagination handling.
        try:
            p_size = int(self.request.GET.get('page_size',settings.get_page_size(self.request)))
            p_size = p_size if p_size in settings.CHOICE_PAGE_SIZE else settings.DEFAULT_PAGE_SIZE
            self.request.session['page_size'] = p_size
        except:
            pass
        self.current_page = int(self.kwargs.get('page','1'))
        paginator = Paginator(self.get_queryset(),settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages
        self.range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)   
        # fill some required fields.
        kwargs.update({
            'choice_page_size': settings.CHOICE_PAGE_SIZE,
            'current_page_size': settings.get_page_size(self.request),
            'page': self.page,
            'prev_10': self.current_page-settings.PAGE_NAV_SIZE if self.current_page-settings.PAGE_NAV_SIZE > 1 else 1,
            'next_10': self.current_page+settings.PAGE_NAV_SIZE if self.current_page+settings.PAGE_NAV_SIZE <= self.page.paginator.num_pages else self.page.paginator.num_pages,
            'page_nav': self.page.paginator.page_range[self.range_start:self.range_start+settings.PAGE_NAV_SIZE],
            'request': self.request,
            'pk': self.kwargs.get('pk', None),
        })
        return kwargs
     
class BaseBrandView(SARequiredMixin):
    template_name = "sa_brand.html"
    form_class = forms.SABrandForm
    model = Brand
    
class CreateBrandView(BaseBrandView, CreateView):
    def get_success_url(self):
        return reverse('sa_edit_brand',args=[self.object.id])
    
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
        if 'users' not in self.__dict__:
            self.users = User.objects.filter(
                is_staff=True,
                is_superuser=False,
                userprofile__role=USERS_ROLE.ADMIN)
        if 'current_page' not in self.__dict__:
            self.current_page = 1
        users = None
        paginator = Paginator(self.users,settings.get_page_size(self.request))
        try:
            users = Paginator(self.users,settings.get_page_size(self.request)).page(self.current_page)
        except(EmptyPage, InvalidPage):
            users = Paginator(self.users,settings.get_page_size(self.request)).page(paginator.num_pages)
            self.current_page = paginator.num_pages
        range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)   
        kwargs.update({
            'user_pk': self.kwargs.get('pk', None),
            'choice_page_size': settings.CHOICE_PAGE_SIZE,
            'current_page_size': settings.get_page_size(self.request),
            'users': users,
            'prev_10': self.current_page-settings.PAGE_NAV_SIZE if self.current_page-settings.PAGE_NAV_SIZE > 1 else 1,
            'next_10': self.current_page+settings.PAGE_NAV_SIZE if self.current_page+settings.PAGE_NAV_SIZE <= users.paginator.num_pages else users.paginator.num_pages,
            'page_nav': users.paginator.page_range[range_start:range_start+settings.PAGE_NAV_SIZE],
            'companies': Brand.objects.all(),
            'request': self.request,
        })
        if 'is_search' in self.__dict__ and self.is_search:
            kwargs.update({
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
            try:
                self.current_page = int(request.POST.get('page','1'))
            except:
                self.current_page = 1
            try:
                request.session['page_size'] = int(request.POST.get('page_size',settings.get_page_size(request)))
            except:
                pass
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
        return reverse('sa_edit_user',args=[self.object.user.pk])
    
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
        return reverse("sa_edit_user",args=[self.object.user.pk])


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

@super_admin_required
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

class CreateCategoryView(BaseCategoryView, CreateView):
    def get_success_url(self):
        return reverse('sa_categories')
    
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


class BaseCarrierView(SARequiredMixin):
    template_name = "sa_carrier.html"
    form_class = forms.SACarrierForm
    model = Carrier
    formset = inlineformset_factory(Carrier, Service, extra=0)

    def get_context_data(self, **kwargs):
        kwargs.update({"formset": self.formset,})
        return super(BaseCarrierView, self).get_context_data(**kwargs)

class CreateCarrierView(BaseCarrierView, CreateView):
    def get_success_url(self):
        return reverse('sa_carriers')

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            carrier=form.save(commit=False)
            formset = self.formset(data=self.request.POST, instance=carrier)
            if formset.is_valid():
                form.save(commit=True)
                formset.save()
                return self.form_valid(form)
        return self.form_invalid(form)

class EditCarrierView(BaseCarrierView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("sa_edit_carrier",args=[pk])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = inlineformset_factory(Carrier, Service, extra=0)
        self.formset = formset(instance = self.get_object())
        return super(BaseCarrierView,self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            carrier=form.save(commit=False)
            formset = self.formset(data=self.request.POST, instance=carrier)
            if formset.is_valid():
                form.save(commit=True)
                formset.save()
                return self.form_valid(form)
        return self.form_invalid(form)

class DeleteCarrierView(BaseCarrierView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({"carrier_pk": self.kwargs.get('pk', None)}),
                            mimetype="application/json")

class BaseAttributeView(SARequiredMixin):
    template_name = "sa_attribute.html"
    form_class = forms.SAAttributeForm
    model = ProductType
    formset = inlineformset_factory(ProductType, CommonAttribute, extra=0)
    
    def get_context_data(self, **kwargs):
        kwargs.update({"formset": self.formset,})
        return super(BaseAttributeView,self).get_context_data(**kwargs)
    
class CreateAttributeView(BaseAttributeView, CreateView):
    def get_success_url(self):
        return reverse('sa_edit_attribute',args=[self.object.id])
        
    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            product_type=form.save(commit=False)
            formset = self.formset(data=self.request.POST, instance=product_type)
            if formset.is_valid():
                form.save(commit=True)
                formset.save()
                return self.form_valid(form)
        return self.form_invalid(form)
    
class EditAttributeView(BaseAttributeView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("sa_edit_attribute",args=[pk])
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = inlineformset_factory(ProductType, CommonAttribute,extra=0)
        self.formset = formset(instance = self.get_object())
        return super(BaseAttributeView,self).get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            product_type=form.save(commit=False)
            formset = self.formset(data=self.request.POST, instance=product_type)
            if formset.is_valid():
                form.save(commit=True)
                formset.save()
                return self.form_valid(form)
        return self.form_invalid(form)

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
    
class CreateBrandingView(BaseBrandingView, CreateView):
    def get_success_url(self):
        return reverse('sa_edit_branding',args=[self.object.id])
    
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


def settings_view(request):
    if request.user.is_superuser:
        return sa_settings(request)
    return brand_settings(request)

@super_admin_required
def sa_settings(request):
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
    return render_to_response('sa_settings.html',
                {'form':form, 'is_saved':is_saved, 'request':request, },
                context_instance=RequestContext(request))

@admin_required
def brand_settings(request):
    is_saved = False
    if request.method == 'POST':
        form = forms.SABrandSettingsForm(data=request.POST, user=request.user)
        if form.is_valid():
            brand = request.user.get_profile().work_for
            brand.default_currency = form.cleaned_data['default_currency']
            brand.save()
            is_saved = True
    else:
        form = forms.SABrandSettingsForm(user=request.user)
    return render_to_response('brand_settings.html',
                {'form':form, 'is_saved':is_saved, 'request':request, },
                context_instance=RequestContext(request))


class BaseTaxView(SARequiredMixin):
    template_name = "sa_tax.html"
    form_class = forms.SATaxForm
    model = Rate


class CreateTaxView(BaseTaxView, CreateView):
    def get_success_url(self):
        return reverse('sa_edit_tax', args=[self.object.pk])


class EditTaxView(BaseTaxView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("sa_edit_tax", args=[pk])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(BaseTaxView, self).get(request, *args, **kwargs)


class DeleteTaxView(BaseTaxView, DeleteView):
    def post(self, *args, **kwargs):

        self.object = self.get_object()
        if self.request.GET.get('double_confirm', None):
            return self.delete(*args, **kwargs)

        applied_after = Rate.objects.filter(apply_after=self.object.pk)
        if applied_after:
            note = ('Note! Another ates %s apply after this rate! '
                    'Are you sure you want to delete it?!' % applied_after)
            return HttpResponse(
                content=json.dumps({'note': note}),
                mimetype="application/json")
        else:
            return self.delete(*args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object.delete()
        return HttpResponse(
            content=json.dumps({"rate_pk": self.kwargs.get('pk', None)}),
            mimetype="application/json")
