# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


# Create your views here.
import logging
from common.utils import is_shop_manager_upper
from django import http
from django.utils.translation import check_for_language
import settings
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.template import RequestContext
from fouillis.views import ShopManagerUpperLoginRequiredMixin
from models import Brand, UserProfile
from django.contrib.auth.models import User
import json
from globalsettings import get_setting
import forms
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from common.constants import USERS_ROLE

from shops.models import Shop

def home_page(request):
    """
    returns index.html to non-super-admin
    returns sa_index.html to super admin.
    """
    if request.user.is_superuser: #== super admin
        return render_to_response('sa_index.html', context_instance=RequestContext(request))
    elif is_shop_manager_upper(request.user.get_profile().pk): #non super admin
        context = RequestContext(request)
        return render_to_response('new_index.html', context_instance=context)
    else:
        # TODO: operator directly redirect to order page.
        context = RequestContext(request)
        return render_to_response('index.html', context_instance=context)

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

def set_page_size(request):
    _next = request.REQUEST.get('next', None)
    if not _next:
        _next = request.META.get('HTTP_REFERER', None)
    if not _next:
        _next = '/'
    response = http.HttpResponseRedirect(_next)
    if request.method == 'POST':
        page_size = int(request.POST.get('pageSize', settings.DEFAULT_PAGE_SIZE))
        request.session['page_size'] = page_size
    return response

class BaseOperatorView(ShopManagerUpperLoginRequiredMixin):
    """
    User is different from other models since it has User + UserProfile model.
    system uses create form and edit form and save method is overridden in the form.   
    """
    template_name = "operator.html"

    def get_users(self):
        # super admin could operate all users.
        if self.request.user.is_superuser:
            return User.objects.filter(
                userprofile__role__gt=USERS_ROLE.ADMIN)

        # brand administrator could operate all brand users.
        req_u_profile = self.request.user.get_profile()
        if req_u_profile.role == USERS_ROLE.ADMIN:
            return User.objects.filter(
                userprofile__work_for=req_u_profile.work_for,
                userprofile__role__gt=USERS_ROLE.ADMIN)

        users = User.objects.filter(
            userprofile__work_for=req_u_profile.work_for,
            userprofile__role__gt=USERS_ROLE.MANAGER)

        req_u_shops = req_u_profile.shops.all()
        operate_users = []
        for user in users:
            u_shops = user.get_profile().shops.all()
            if not u_shops:
                continue
            if u_shops[0].pk in req_u_shops:
                operate_users.append(user.pk)
        users.filter(pk__in=operate_users)
        return users




    def get_context_data(self, **kwargs):

        if 'users' not in self.__dict__:
            self.users = self.get_users()

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
        if self.object:
            access_check = self._priority_check(self.request.user, self.object)
            if access_check:
                logging.error(
                    "hack_error? user %s trying to edit user %s"
                    % (self.request.user.pk, self.object.user_id))
                kwargs.update(access_check)

        return kwargs

    def _priority_check(self, user, user_profile):
        access_error = _("You have no priority to access this user")

        if user.is_superuser:
            return

        manager_profile = user.get_profile()

        # check manager have higher level than user.
        if manager_profile.role >= user_profile.role:
            return {"access_error": access_error}

        # check user's shops is shopkeeper owns.
        if manager_profile.role == USERS_ROLE.MANAGER:
            managed_shops = [s.pk for s in manager_profile.shops.all()]
            user_shops = [s.pk for s in user_profile.shops.all()]
            if len(set(user_shops).intersection(set(managed_shops))) == 0:
                return {"access_error": access_error}

    def get_form_kwargs(self):
        """
        overriding this for avoid any form binding during search post.
        """
        if 'is_search' in self.__dict__ and self.is_search:
            kwargs = {'initial': self.get_initial(), 'request': self.request,} 
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
            try:
                self.current_page = int(request.POST.get('page','1'))
            except:
                self.current_page = 1
            try:
                request.session['page_size'] = int(request.POST.get('page_size',settings.get_page_size(request)))
            except:
                pass
            self.users=User.objects.filter(
                username__contains=self.search_username,
                userprofile__work_for=self.request.user.get_profile().work_for)
            return self.get(request, *args, **kwargs)
        else:
            return super(BaseOperatorView,self).post(request, *args, **kwargs)
 
class CreateOperatorView(BaseOperatorView, CreateView):
    form_class = forms.CreateOperatorForm
    
    def get_success_url(self):
        return reverse('edit_operator',args=[self.object.user.pk])
    
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


    def __get_context_data(self, **kwargs):
        if self.object:
            request_user_role = self.request.user.get_profile().role
            access_error = _("You have no priority to access this user")
            if self.object.role >= request_user_role:
                return {"access_error": access_error}
        else:
            return super(EditOperatorView, self).get_context_data(**kwargs)

    def get_object(self):
        user = super(EditOperatorView,self).get_object()
        self.object, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"language": get_setting('default_language')})
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
        request_user_role = self.request.user.get_profile().role
        if request_user_role >= self.object.role:
            return http.HttpResponse(
                content=json.dumps({"access_error": "AUTHENTICATIOIN error"}),
                mimetype="application/json")
        else:
            user = self.object.user
            self.shops_owner_delete(user)
            self.object.delete()
            user.delete()
            return http.HttpResponse(
                content=json.dumps({"user_pk": self.kwargs.get('pk', None)}),
                mimetype="application/json")

    def shops_owner_delete(self, user):
        owned_shops = Shop.objects.filter(owner=user)
        for shop in owned_shops:
            shop.owner_id = None
            shop.save()

class OperatorShopsView(ShopManagerUpperLoginRequiredMixin, CreateView):
    form_class = forms.AjaxShopsForm
    template_name = "_ajax_shops.html"
    def get_initial(self):
        initials = super(OperatorShopsView,self).get_initial()
        initials['request'] = self.request
        return initials
