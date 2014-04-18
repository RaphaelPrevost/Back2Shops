import logging
import json
import settings
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from fouillis.views import admin_required
from fouillis.views import ManagerUpperLoginRequiredMixin
from common.constants import USERS_ROLE
from common.error import InvalidRequestError
from common.utils import get_currency
from countries.models import CountryXCurrency
from shops.models import Shop
from shops.forms import ShopForm

class ShopCoordinates(TemplateView):
    def get(self, request, *args, **kwargs):
        shop_id = request.GET.get("shop_id", None)
        toret = {}
        if shop_id:
            shop = Shop.objects.get(pk=shop_id)
            toret['latitude'] = shop.latitude
            toret['longitude'] = shop.longitude
        return HttpResponse(content=json.dumps(toret), mimetype="application/json")

class BaseShopView(ManagerUpperLoginRequiredMixin):
    template_name = "physical_shop.html"
    form_class = ShopForm
    model = Shop

    def get_success_url(self):
        return reverse("page_shops")

    def get_context_data(self, **kwargs):
        shops = self.get_shops()
            
        try:
            p_size = int(self.request.GET.get('page_size',settings.get_page_size(self.request)))
            p_size = p_size if p_size in settings.CHOICE_PAGE_SIZE else settings.DEFAULT_PAGE_SIZE
            self.request.session['page_size'] = p_size
        except:
            pass
        self.current_page = int(self.kwargs.get('page','1'))
        paginator = Paginator(shops,settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages
        self.range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)    
        kwargs.update({
            'shop_pk': self.kwargs.get('pk', None),
            'shops': self.page,
            'request': self.request,
            'geonames_username': settings.GEONAMES_USERNAME,
            'media_url': settings.MEDIA_URL,
            'choice_page_size': settings.CHOICE_PAGE_SIZE,
            'current_page_size': settings.get_page_size(self.request),
            'page': self.page,
            'prev_10': self.current_page-settings.PAGE_NAV_SIZE if self.current_page-settings.PAGE_NAV_SIZE > 1 else 1,
            'next_10': self.current_page+settings.PAGE_NAV_SIZE if self.current_page+settings.PAGE_NAV_SIZE <= self.page.paginator.num_pages else self.page.paginator.num_pages,
            'page_nav': self.page.paginator.page_range[self.range_start:self.range_start+settings.PAGE_NAV_SIZE],       
        })
        return kwargs

    def get_shops(self):
        if self.request.user.is_superuser:
            return Shop.objects.all()

        shops = Shop.objects.filter(
            mother_brand=self.request.user.get_profile().work_for)
        req_u_profile = self.request.user.get_profile()
        if req_u_profile.role == USERS_ROLE.MANAGER:
            shops = shops.filter(
                pk__in=self.request.user.get_profile().shops.all())
        return shops

    def _valid_shop_owner(self, pk):
        if self.request.user.is_superuser:
            return True

        return len(self.request.user.get_profile().shops.filter(pk=pk))>0

    def _valid_shop_brand(self, shop):
        if self.request.user.is_superuser:
            return True
        return shop.mother_brand == self.request.user.get_profile().work_for

class CreateShopView(BaseShopView, CreateView):
    def get_initial(self):
        if self.request.user.is_superuser:
            return {}

        return {
            "default_currency": get_currency(self.request.user),
            "mother_brand": self.request.user.get_profile().work_for
        }

    def post(self, request, *args, **kwargs):
        return admin_required(super(CreateShopView,self).post,
                              login_url="/")(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('edit_shop',args=[self.object.id])


class EditShopView(BaseShopView, UpdateView):
    queryset = Shop.objects.all()

    def _valid_shop(self, shop):
        if self.request.user.is_superuser:
            return True

        # shop's brand must same with request user brand.
        if not self._valid_shop_brand(shop):
            return False

        # If request user is a shopkeeper, the shopkeeper must
        # own the shop
        req_u_profile = self.request.user.get_profile()
        if (req_u_profile.role == USERS_ROLE.MANAGER and
            not self._valid_shop_owner(shop.pk)):
            return False

        return True

    def get_object(self, queryset=None):
        obj = super(EditShopView, self).get_object(queryset)
        if not self._valid_shop(obj):
            raise InvalidRequestError(
                "User %s trying to edit shop %s which is not owned to him",
                self.request.user.pk, obj.pk)
        return obj

    def get(self, request, *args, **kwargs):
        try:
            return super(EditShopView,self).get(request, *args, **kwargs)
        except InvalidRequestError, e:
            logging.error("user_get_edit_shop_error: %s",
                          str(e),
                          exc_info=True)
            return HttpResponseRedirect('/')
    
    def post(self, request, *args, **kwargs):
        try:
            return super(EditShopView,self).post(request, *args, **kwargs)
        except InvalidRequestError, e:
            logging.error("user_post_edit_shop_error: %s",
                          str(e),
                          exc_info=True)
            return HttpResponseRedirect('/')

    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("edit_shop",args=[pk])

class DeleteShopView(BaseShopView, DeleteView):
    def _valid_shop(self, shop):
        if self.request.user.is_superuser:
            return True

        # shop's brand must same with request user brand.
        if not self._valid_shop_brand(shop):
            raise InvalidRequestError(
                "User %s trying to delete shop %s which is not owned to him",
                self.request.user.pk, shop.pk)

        # If request user is a shopkeeper, the shopkeeper must
        # own the shop
        req_u_profile = self.request.user.get_profile()
        if req_u_profile.role != USERS_ROLE.ADMIN:
            raise InvalidRequestError(
                "User %s trying to delete shop %s who has no delete priority",
                self.request.user.pk, shop.pk)

        return True

    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self._valid_shop(self.object)
            self.object.delete()
            return HttpResponse(content=json.dumps({"shop_pk": self.kwargs.get('pk', None)}),
                                mimetype="application/json")
        except InvalidRequestError, e:
            logging.error("user_delete_shop_error: %s",
                          str(e), exc_info=True)
            return HttpResponse(content=json.dumps({"shop_pk": "N/A"}),
                                mimetype='application/json')
