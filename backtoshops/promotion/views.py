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


import json
import logging
import settings
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from common.constants import USERS_ROLE
from common.error import ServerError
from common.error import InvalidRequestError
from fouillis.views import manager_upper_required
from fouillis.views import ManagerUpperLoginRequiredMixin
from promotion.forms import GroupForm
from promotion.models import Group, TypesInGroup, SalesInGroup
from sales.models import Sale, ProductType
from shops.models import Shop


class BasePromotionView(ManagerUpperLoginRequiredMixin):
    template_name = "promotion_group.html"
    form_class = GroupForm
    model = Group

    def get_success_url(self):
        return reverse("page_promotion")

    def _get_groups_by_user(self):
        if self.request.user.is_superuser:
            return Group.objects.all()

        req_u_profile = self.request.user.get_profile()
        if req_u_profile.role == USERS_ROLE.ADMIN:
            return Group.objects.filter(brand=req_u_profile.work_for)

        if req_u_profile.role == USERS_ROLE.MANAGER:
            if req_u_profile.allow_internet_operate:
                return Group.objects.filter(
                    Q(shop__in=req_u_profile.shops.all()) |
                    Q(shop__isnull=True)).filter(
                        brand=req_u_profile.work_for)
            else:
                return Group.objects.filter(
                    shop__in=req_u_profile.shops.all())

        raise ServerError("Shouldn't be here!!")

    def _get_shops(self, brand):
        shops = Shop.objects.filter(mother_brand=brand)
        if self.request.user.is_superuser:
            return shops

        req_u_profile = self.request.user.get_profile()
        if req_u_profile.role == USERS_ROLE.ADMIN:
            return shops

        return req_u_profile.shops.all()

    def _get_sales(self, brand, shops):
        sales = Sale.objects.filter(mother_brand=brand)
        if self.request.user.is_superuser:
            return sales

        req_u_profile = self.request.user.get_profile()
        if req_u_profile.role == USERS_ROLE.ADMIN:
            return sales

        user_shops = req_u_profile.shops.all()
        sales.filter(shopsinsale__shop__in=user_shops)
        return sales

    def global_priority(self):
        if self.request.user.is_superuser:
            return True

        req_u_profile = self.request.user.get_profile()
        if req_u_profile.role == USERS_ROLE.ADMIN:
            return True

        return req_u_profile.allow_internet_operate

    def get_initial(self):
        types = ProductType.objects.all()

        return {
            "types": types,
            "global_priority": self.global_priority()
        }

    def get_context_data(self, **kwargs):
        groups = self._get_groups_by_user()
        try:
            p_size = int(self.request.GET.get('page_size',settings.get_page_size(self.request)))
            p_size = p_size if p_size in settings.CHOICE_PAGE_SIZE else settings.DEFAULT_PAGE_SIZE
            self.request.session['page_size'] = p_size
        except:
            pass
        self.current_page = int(self.kwargs.get('page','1'))
        paginator = Paginator(groups,settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages
        self.range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)    
        kwargs.update({
            'promotion_pk': self.kwargs.get('pk', None),
            'groups': self.page,
            'request': self.request,
            'media_url': settings.MEDIA_URL,
            'choice_page_size': settings.CHOICE_PAGE_SIZE,
            'current_page_size': settings.get_page_size(self.request),
            'page': self.page,
            'prev_10': self.current_page-settings.PAGE_NAV_SIZE if self.current_page-settings.PAGE_NAV_SIZE > 1 else 1,
            'next_10': self.current_page+settings.PAGE_NAV_SIZE if self.current_page+settings.PAGE_NAV_SIZE <= self.page.paginator.num_pages else self.page.paginator.num_pages,
            'page_nav': self.page.paginator.page_range[self.range_start:self.range_start+settings.PAGE_NAV_SIZE],       
        })
        return kwargs

    def _get_promotion_types(self, brand):
        pass

    def priority_check(self, obj):
        if self.request.user.is_superuser:
            return

        req_u_profile = self.request.user.get_profile()
        if obj.brand != req_u_profile.work_for:
            raise InvalidRequestError("Priority Error")

        if req_u_profile.role == USERS_ROLE.ADMIN:
            return

        if obj.shop is None:
            if not req_u_profile.allow_internet_operate:
                raise InvalidRequestError("Priority Error")
        elif len(req_u_profile.shops.all().filter(pk=obj.shop.pk)) == 0:
            raise InvalidRequestError("Priority Error")


class CreatePromotionView(BasePromotionView, CreateView):
    def get_initial(self):
        initial = super(CreatePromotionView, self).get_initial()
        if self.request.user.is_superuser:
            return initial

        brand = self.request.user.get_profile().work_for
        shops = self._get_shops(brand)
        sales = self._get_sales(brand, shops)
        initial.update({
            "brand": brand,
            "shops": shops,
            "sales": sales.all(),
            })
        return initial

    def get_success_url(self):
        return reverse('page_promotion')

    def post(self, request, *args, **kwargs):
        return manager_upper_required(
            super(CreatePromotionView, self).post,
            redirect_field_name="/",
            super_allowed=False)(request, *args, **kwargs)


class EditPromotionView(BasePromotionView, UpdateView):
    def get_initial(self):
        initial = super(EditPromotionView, self).get_initial()
        pk = self.kwargs.get('pk')
        obj = Group.objects.get(pk=pk)

        shops = self._get_shops(obj.brand)
        sales = self._get_sales(obj.brand, shops)

        type_choices = [
            tig.type for tig in TypesInGroup.objects.filter(group_id=pk)]

        sales_choices = [
            sig.sale for sig in SalesInGroup.objects.filter(group_id=pk)]


        group = Group.objects.get(pk=pk)
        initial.update({
            "brand": obj.brand,
            "shops": shops,
            "sales": sales,
            "type_choices": type_choices,
            "sales_choices": sales_choices,
            "pk": pk,
            'name': group.name,
            'shop': group.shop
            })
        return initial

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            self.priority_check(obj)
            return super(EditPromotionView,self).get(request, *args, **kwargs)
        except InvalidRequestError, e:
            logging.error("promotion_edit_request_error: %s",
                          str(e),
                          exc_info=True)
            return HttpResponseRedirect('/')
        except Exception, e:
            logging.error("promotion_edit_server_error: %s",
                          str(e),
                          exc_info=True)
            return HttpResponseRedirect('/')

    def post(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            self.priority_check(obj)
            return super(EditPromotionView,self).post(request, *args, **kwargs)
        except InvalidRequestError, e:
            logging.error("promotion_update_request_error: %s",
                          str(e),
                          exc_info=True)
            return HttpResponseRedirect('/')
        except Exception, e:
            logging.error("promotion_update_server_error: %s",
                          str(e),
                          exc_info=True)
            return HttpResponseRedirect('/')
        
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("edit_promotion",args=[pk])


class DeletePromotionView(BasePromotionView, DeleteView):
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.priority_check(self.object)
            self.object.delete()
            return HttpResponse(
                content=json.dumps(
                    {"group_pk": self.kwargs.get('pk', None)}),
                mimetype="application/json")
        except InvalidRequestError, e:
            logging.error("promotion_delete_error: %s",
                          str(e),
                          exc_info=True)
            return HttpResponse(
                content=json.dumps({"error": str(e)}),
                mimetype="application/json")
        except Exception, e:
            logging.error("promotion_delete_error: %s",
                          str(e),
                          exc_info=True)
            return HttpResponse(
                content=json.dumps({"error": "Server Error"}),
                mimetype="application/json")


