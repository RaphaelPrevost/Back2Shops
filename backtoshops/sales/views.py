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


import settings
import json
import logging
from datetime import date

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.core.paginator import EmptyPage
from django.core.paginator import InvalidPage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template import loader
from django.template.context import Context
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.base import View
from formwizard.views import NamedUrlSessionWizardView
from sorl.thumbnail import get_thumbnail

from B2SProtocol.settings import SHIPPING_WEIGHT_UNIT
from attributes.models import BrandAttribute
from attributes.models import BrandAttributePreview
from attributes.models import CommonAttribute
from attributes.models import VariableAttribute
from barcodes.models import Barcode
from brandsettings import get_ba_settings
from common.assets_utils import get_asset_name
from common.cache_invalidation import send_cache_invalidation
from common.constants import TARGET_MARKET_TYPES
from common.constants import USERS_ROLE
from common.coupons import create_item_specific_coupon
from common.coupons import delete_coupon
from common.coupons import update_item_specific_coupon
from common.coupons import get_item_specific_discount_coupon
from common.error import InvalidRequestError
from common.utils import get_currency
from common.utils import get_default_setting
from common.utils import get_valid_sort_fields
from fouillis.views import ManagerUpperLoginRequiredMixin
from fouillis.views import OperatorUpperLoginRequiredMixin
from fouillis.views import ShopManagerUpperLoginRequiredMixin
from fouillis.views import manager_upper_required
from globalsettings import get_setting
from promotion.utils import save_sale_promotion_handler
from sales.forms import BrandAttributeForm
from sales.forms import ListSalesForm
from sales.forms import ProductBrandFormModel
from sales.forms import ProductForm
from sales.forms import ShippingForm
from sales.forms import ShopForm
from sales.models import ExternalRef
from sales.models import OrderConfirmSetting
from sales.models import Product
from sales.models import ProductBrand
from sales.models import ProductCategory
from sales.models import ProductCurrency
from sales.models import ProductPicture
from sales.models import ProductType
from sales.models import ProductTypeVarAttr
from sales.models import CategoryTypeMap
from sales.models import STOCK_TYPE_DETAILED
from sales.models import STOCK_TYPE_GLOBAL
from sales.models import Sale
from sales.models import ShippingInSale
from sales.models import ShopsInSale
from sales.models import TypeAttributePrice
from sales.models import TypeAttributeWeight
from sales.models import WeightUnit
from shippings.forms import CustomShippingRateFormModel
from shippings.models import FlatRateInShipping
from shippings.models import SC_CARRIER_SHIPPING_RATE
from shippings.models import SC_CUSTOM_SHIPPING_RATE
from shippings.models import SC_FLAT_RATE
from shippings.models import Shipping
from shops.models import DefaultShipping
from shops.models import Shop
from stocks.models import ProductStock
from taxes.models import Rate

def get_sale_currency(request, shop_data):
    target_market = shop_data['target_market']
    shops = shop_data['shops']
    if target_market == TARGET_MARKET_TYPES.LOCAL and shops:
        return get_currency(request.user, shops[0])
    return get_currency(request.user)

def filter_sales_by_role(request, sales):
    if request.user.is_superuser:
        return sales

    req_u_profile = request.user.get_profile()
    if req_u_profile.role == USERS_ROLE.ADMIN:
        sales = sales
    elif req_u_profile.role == USERS_ROLE.MANAGER:
        if req_u_profile.allow_internet_operate:
            sales = sales.filter(
                Q(shops__in=req_u_profile.shops.all()) |
                Q(type_stock=STOCK_TYPE_GLOBAL))
        else:
            sales = sales.filter(
                Q(shops__in=req_u_profile.shops.all()))
    else:
        if len(req_u_profile.shops.all()):
            sales = sales.filter(
                Q(shops__in=req_u_profile.shops.all()))
        else:
            sales = sales.filter(
                Q(type_stock=STOCK_TYPE_GLOBAL))
    return sales

class UploadProductPictureView(View, TemplateResponseMixin):
    template_name = ""

    def post(self, request):
        if request.FILES:
            new_img = request.FILES[u'files[]']
            if new_img.size > settings.SALE_IMG_UPLOAD_MAX_SIZE:
                content = {'status': 'max_limit_error'}
                return HttpResponse(json.dumps(content), mimetype='application/json')

            is_cover = request.POST.get('is_cover', False)
            is_brand_attribute = request.POST.get('is_brand_attribute', False)
            new_media = ProductPicture(picture=request.FILES[u'files[]'])
            new_media.is_brand_attribute = is_brand_attribute
            if is_cover:
                new_media.sort_order = -1
            new_media.save()
            thumb = get_thumbnail(new_media.picture, '187x187')
            t = loader.get_template('_product_preview_thumbnail.html')
            c = Context({"picture": new_media.picture })
            preview_html = t.render(c)
            to_ret = {'status': 'ok', 'url': new_media.picture.url, 'thumb_url': thumb.url,
                      'pk': new_media.pk, 'preview_html': preview_html}
            return HttpResponse(json.dumps(to_ret), mimetype="application/json")
        raise HttpResponseBadRequest(_("Please upload a picture."))

class ProductBrandView(ManagerUpperLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_ajax_brands.html"

    def post(self, request):
        try:
            form = ProductBrandFormModel(request.POST, request.FILES)
            if form.is_valid():
                self.new_brand = form.save(commit=False)
                self.new_brand.seller = request.user.get_profile().work_for
                self.new_brand.save()
                messages.success(request, _("The brand has been successfully created."))
                self.brands = ProductBrand.objects.filter(seller=request.user.get_profile().work_for)
        except Exception as e:
            self.errors = e
        return self.render_to_response(self.__dict__)

class BrandLogoView(ManagerUpperLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_brand_preview_thumbnail.html"

    def get(self, request, brand_id=None):
        if brand_id:
            brand = ProductBrand.objects.get(pk=brand_id)
            # bugfix: handle picture field is NULL
            if brand.picture == 'NULL': return HttpResponse(ugettext('Please upload a logo.'))
            self.picture = brand.picture
            return self.render_to_response(self.__dict__)
        return HttpResponseBadRequest()

class ListSalesView(OperatorUpperLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = 'list.html'
    list_current = True

    def set_sales_list(self, request, sales_type=None, contains=None):
        """
        this is just internal method to make the self.sales queryset.
        """
        if request.user.is_superuser:
            self.sales = Sale.objects.all()
        else:
            self.sales = Sale.objects.filter(
                mother_brand=request.user.get_profile().work_for
            )

        if contains is not None and contains != '':
            self.sales = self.sales.filter(
                Q(product__name__icontains=contains) |
                Q(product__description__icontains=contains) |
                Q(barcodes__upc__contains=contains) |
                Q(externalrefs__external_id__contains=contains)
            ).distinct()

        if sales_type == "old":
            self.sales = self.sales.filter(
                Q(product__available_to__isnull=False) &
                Q(product__available_to__lt=date.today())
            )
            self.page_title = _("History")
        else:
            self.sales = self.sales.filter(
                Q(product__available_to__isnull=True) |
                Q(product__available_to__gte=date.today())
            )
            self.page_title = _("Current Sales")

        self.sales = filter_sales_by_role(self.request, self.sales)

        #put extra fields
        self.sales = self.sales.extra(select={'total_sold_stock':'total_stock-total_rest_stock'})
        self.tax_flag = get_default_setting('use_after_tax_price', self.request.user) == 'True'
        self.tax_price_label = _("Before-tax price:") if self.tax_flag \
                          else _("After-tax price:")
        for sale in self.sales:
            type_attribute_prices = TypeAttributePrice.objects.filter(sale=sale)
            prices = [i.type_attribute_price for i in type_attribute_prices]
            if prices:
                sale.max_type_attribute_price = max(prices)
                sale.min_type_attribute_price = min(prices)
                base_price = min(prices)
            else:
                base_price = sale.product.normal_price

            if sale.product.discount_type == 'percentage':
                sale.product.discount_price = base_price * sale.product.discount / 100.0
            elif sale.product.discount_type == 'amount':
                sale.product.discount_price = base_price - sale.product.discount
            else:
                sale.product.discount_price = base_price

            if sale.shops.count() > 0:
                country_code = sale.shops.all()[0].address.country_id
                province_code = sale.shops.all()[0].address.province_code
            else:
                country_code = sale.mother_brand.address.country_id
                province_code = sale.mother_brand.address.province_code
            category_id = Product.objects.get(sale=sale).category_id
            taxes = Rate.objects.filter(
                Q(enabled=True) &
                Q(region_id=country_code) &
                Q(shipping_to_region_id=None) &
                Q(shipping_to_province='') &
                (Q(applies_to_id=None) | Q(applies_to_id=category_id))
            )
            if province_code:
                taxes = taxes.filter(Q(province="") | Q(province=province_code))
            else:
                taxes = taxes.filter(Q(province=""))
            if taxes.count() > 0:
                sale.product.tax_rate = taxes.all()[0].rate
            else:
                sale.product.tax_rate = 0

            if sale.product.pictures.count() > 0:
                sale.cover = sale.product.pictures.order_by('sort_order', 'id')[0].picture
        self.sales = list(self.sales)

        return

    def make_page(self):
        """
        make a pagination
        """
        try:
            self.current_page = int(self.request.GET.get('page','1'))
            p_size = int(self.request.GET.get('page_size',settings.get_page_size(self.request)))
            p_size = p_size if p_size in settings.CHOICE_PAGE_SIZE else settings.DEFAULT_PAGE_SIZE
            self.request.session['page_size'] = p_size
        except:
            self.current_page = 1
        paginator = Paginator(self.sales, settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages
        self.range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)
        self.choice_page_size = settings.CHOICE_PAGE_SIZE
        self.current_page_size = settings.get_page_size(self.request)
        self.prev_10 = self.current_page-settings.PAGE_NAV_SIZE if self.current_page-settings.PAGE_NAV_SIZE > 1 else 1
        self.next_10 = self.current_page+settings.PAGE_NAV_SIZE if self.current_page+settings.PAGE_NAV_SIZE <= self.page.paginator.num_pages else self.page.paginator.num_pages
        self.page_nav = self.page.paginator.page_range[self.range_start:self.range_start+settings.PAGE_NAV_SIZE]

    def get(self, request, sales_type=None):
        self.set_sales_list(request, sales_type)
        self.form = ListSalesForm()
        self.make_page()
        return self.render_to_response(self.__dict__)

    def post(self, request, sales_type=None):
        self.form = ListSalesForm(request.POST)
        if self.form.is_valid():
            if 'search_sale' in request.POST:
                search_by = self.form.cleaned_data['search_by']
                self.set_sales_list(request, sales_type, contains=search_by)
                self.search_sale = True
            else:
                self.set_sales_list(request, sales_type)
                order_by1 = self.form.cleaned_data['order_by1']
                order_by2 = self.form.cleaned_data['order_by2']
                sort_fields = get_valid_sort_fields(order_by1, order_by2)
                if sort_fields:
                    from common.utils import Sorter
                    sorter = Sorter(self.sales)
                    sorter.sort(sort_fields)
        self.make_page()
        return self.render_to_response(self.__dict__)

class DeleteSalesView(ShopManagerUpperLoginRequiredMixin, View):

    def priority_check(self, sale):
        if self.request.user.is_superuser:
            return
        req_u_profile = self.request.user.get_profile()

        if req_u_profile.role == USERS_ROLE.ADMIN:
            if sale.mother_brand != req_u_profile.work_for:
                raise InvalidRequestError("Priority Error")
        elif req_u_profile.role == USERS_ROLE.MANAGER:
            if sale.type_stock == TARGET_MARKET_TYPES.GLOBAL:
                raise InvalidRequestError("Priority Error")
            shops_in_sale = ShopsInSale.objects.filter(sale=sale)
            shops_in_sale.filter(shop__in=req_u_profile.shops.all())
            if len(shops_in_sale) == 0:
                raise InvalidRequestError("Priority Error")
        else:
            raise InvalidRequestError("Priority Error")

    def _delete(self, sale):
        if self.request.user.is_superuser:
            return sale.delete()

        req_u_profile = self.request.user.get_profile()
        shops_in_sale = ShopsInSale.objects.filter(sale=sale)
        exclude_shops = shops_in_sale.exclude(
            shop__in=req_u_profile.shops.all())

        if len(exclude_shops):
            user_shops = req_u_profile.shops.all()
            user_managed_shops = shops_in_sale.filter(shop__in=user_shops)
            # delete delete sale's stock info
            ProductStock.objects.filter(
                sale=sale, shop__in=user_shops).delete()
            user_managed_shops.delete()
        else:
            sale.delete()

    def post(self, request, sale_id):
        try:
            sale = Sale.objects.get(pk=sale_id)
            self.priority_check(sale)
            self._delete(sale)
        except InvalidRequestError, e:
            return HttpResponse(json.dumps({'success': False,
                                            'error': str(e)}),
                                mimetype='text/json')
        except:
            return HttpResponse(json.dumps({'success': False,
                                            'error': 'Server Error'}),
                                mimetype='text/json')
        return HttpResponse(json.dumps({'success': True}), mimetype='text/json')

class SaleDetails(OperatorUpperLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_sale_details.html"

    def _get_common_attributes(self, shop_id, ba):
        rows = []
        for common_attribute in self.common_attributes.all():
            if shop_id:
                results = ProductStock.objects.filter(brand_attribute=ba,
                                                      common_attribute=common_attribute,
                                                      sale=self.sale,
                                                      shop=shop_id)\
                                              .aggregate(stock_sum=Sum('stock'), rest_stock_sum=Sum('rest_stock'))
            else:
                results = ProductStock.objects.filter(brand_attribute=ba,
                                                      common_attribute=common_attribute,
                                                      sale=self.sale)\
                                              .aggregate(stock_sum=Sum('stock'), rest_stock_sum=Sum('rest_stock'))

            stock_sum = results and results['stock_sum'] or 0
            rest_stock_sum = results and results['rest_stock_sum'] or 0
            rows.append({
                'common_attribute': common_attribute.name,
                'base': stock_sum,
                'to_sell': rest_stock_sum,
                'sold': stock_sum - rest_stock_sum,
                'stock': rest_stock_sum
            })
            if shop_id:
                self.total_stock += stock_sum
                self.total_rest_stock += rest_stock_sum
        return rows

    def get(self, request, sale_id, shop_id=None):
        self.sale = Sale.objects.get(pk=sale_id)
        self.common_attributes = CommonAttribute.objects.filter(for_type=self.sale.product.type)
        self.stocks_table = []
        self.total_stock = self.sale.total_stock if not shop_id else 0
        self.total_rest_stock = self.sale.total_rest_stock if not shop_id else 0

        if self.sale.product.brand_attributes.all():
            for attribute in self.sale.product.brand_attributes.all():
                table = {}
                table['attribute'] = attribute.name
                table['rows'] = self._get_common_attributes(shop_id, attribute)
                self.stocks_table.append(table)
        else:
            table = {}
            table['attribute'] = None
            table['rows'] = self._get_common_attributes(shop_id, None)
            self.stocks_table.append(table)

        return self.render_to_response(self.__dict__)

class SaleDetailsShop(OperatorUpperLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_sale_details_shop.html"

    def filter_shops_by_role(self, request, shops):
        if request.user.is_superuser:
            return shops

        req_u_profile = self.request.user.get_profile()
        if req_u_profile.role == USERS_ROLE.ADMIN:
            shops = shops.filter(mother_brand=req_u_profile.work_for)
        else:
            shops = shops.filter(pk__in=req_u_profile.shops.all())
        return shops

    def get(self, request, sale_id=None):
        self.sale = Sale.objects.get(pk=sale_id)
        self.shops = Shop.objects.filter(shopsinsale__sale=self.sale)
        self.shops = self.filter_shops_by_role(request, self.shops)
        self.shops.filter(productstock__sale=self.sale).distinct()
        return self.render_to_response(self.__dict__)


def _has_valid_shop(mother_brand, user):
    if Shop.objects.filter(mother_brand=mother_brand):
        return True

    if (not user.is_superuser and
            user.get_profile().role in (USERS_ROLE.ADMIN, USERS_ROLE.MANAGER) and
            user.get_profile().allow_internet_operate and
            user.get_profile().shops.all()):
        return True

    return False


def show_step_shop(wizard):
    if wizard.get_form(SaleWizardNew.STEP_SHOP).initial.get('shops', []):
        return True

    shop_form_kws = wizard.get_form_kwargs(SaleWizardNew.STEP_SHOP)
    user = shop_form_kws.get('request').user
    mother_brand=shop_form_kws.get('mother_brand')
    if _has_valid_shop(mother_brand, user):
        return True

    return False


def add_sale(request, *args, **kwargs):
    forms = [
        (SaleWizardNew.STEP_SHOP, ShopForm),
        (SaleWizardNew.STEP_PRODUCT, ProductForm),
        (SaleWizardNew.STEP_SHIPPING, ShippingForm),
    ]

    initial_product = {
        'weight_unit': WeightUnit.objects.get(key=get_setting('default_weight_unit')),
        'category': None,
    }

    initials = {
        SaleWizardNew.STEP_PRODUCT: initial_product,
    }

    sale_wizard = manager_upper_required(
        SaleWizardNew.as_view(forms,
                              initial_dict=initials,
                              url_name="add_sale",
                              done_step_name="list_sales",
                              condition_dict={SaleWizardNew.STEP_SHOP: show_step_shop}
        ),
        login_url="/",
        super_allowed=False)
    return sale_wizard(request, *args, **kwargs)

def _is_edit_sales_owner(sale, user):
    if user.is_superuser:
        return True

    u_profile = user.get_profile()
    if u_profile.work_for != sale.mother_brand: #if brand is different
        return False

    if u_profile.role == USERS_ROLE.ADMIN: # if user is brand admin
        return True
    elif u_profile.role == USERS_ROLE.MANAGER: # if user is shop manager
        internet_priority = u_profile.allow_internet_operate
        owned_shops = u_profile.shops.all()
        is_owner = False
        if internet_priority and sale.type_stock == STOCK_TYPE_GLOBAL:
            is_owner = True
        elif len(sale.shops.all().filter(pk__in=owned_shops)):
            is_owner = True
        return is_owner

def _get_edit_sales_shops(sale, user):
    shops = ShopsInSale.objects.filter(sale=sale,is_freezed=False)

    if user.is_superuser or user.get_profile().role == USERS_ROLE.ADMIN: # if user is admin.
        return [s.shop_id for s in shops]
    else:  # if user is shop manager.
        shops = shops.filter(shop_id__in=user.get_profile().shops.all())
        return [s.shop_id for s in shops]

def edit_sale(request, *args, **kwargs):
    forms = [
        (SaleWizardNew.STEP_SHOP, ShopForm),
        (SaleWizardNew.STEP_PRODUCT, ProductForm),
        (SaleWizardNew.STEP_SHIPPING, ShippingForm),
    ]

    if not 'sale_id' in kwargs:
        return add_sale(request, *args, **kwargs)
    sale_id = kwargs['sale_id']
    sale = Sale.objects.get(pk=sale_id)

    user = request.user
    if not _is_edit_sales_owner(sale, user):
        return HttpResponseRedirect("/")

    # We use pk in initials so we can use has_changed() method on forms
    initial_shop = {
        'target_market': sale.type_stock,
        'shops': _get_edit_sales_shops(sale, user),
    }

    pictures = []
    cover_picture = None
    for pic in sale.product.pictures.exclude(is_brand_attribute=True).order_by('sort_order', 'id'):
        pp = {
            'pk': pic.pk,
            'url': pic.picture.url,
            'thumb_url': get_thumbnail(pic.picture, '187x187').url,
            'sort_order': pic.sort_order,
        }
        if pic.sort_order == -1:
            cover_picture = pp
        else:
            pictures.append(pp)

    brand_attributes = {}
    for i in sale.product.brand_attributes.all():
        if i.pk in brand_attributes:
            continue

        previews = BrandAttributePreview.objects.filter(brand_attribute=i,
                                                        product=sale.product)
        bap = [{'url': get_thumbnail(p.preview.picture, "187x187").url
                       if p.preview else None,
                'pk': p.preview.pk if p.preview else None,
                'sort_order': p.preview.sort_order if p.preview else None,
               } for p in previews]
        bap.sort(key=lambda i:i['sort_order'])
        brand_attributes.update({
            i.pk: {
                'name': i.name,
                'ba_id': i.pk,
                'texture': i.texture.url if i.texture else None,
                'premium_type': i.premium_type,
                'premium_amount': i.premium_amount,
                'previews': bap,
            }
        })
    brand_attributes = brand_attributes.values()

    type_attribute_prices = []
    for i in TypeAttributePrice.objects.filter(sale=sale):
        type_attribute_prices.append({
            'tap_id': i.pk,
            'type_attribute': i.type_attribute.id,
            'type_attribute_price': i.type_attribute_price
        })

    type_attribute_weights = []
    for i in TypeAttributeWeight.objects.filter(sale=sale):
        type_attribute_weights.append({
            'taw_id': i.pk,
            'type_attribute': i.type_attribute.id,
            'type_attribute_weight': i.type_attribute_weight,
        })

    initial_varattrs = []
    for i in ProductTypeVarAttr.objects.filter(sale=sale):
        initial_varattrs.append({
            'attr': i.attr.id,
            'value': i.value,
        })

    initial_barcodes = []
    for i in Barcode.objects.filter(sale=sale):
        initial_barcodes.append({
            'brand_attribute': i.brand_attribute.pk if i.brand_attribute else None,
            'common_attribute': i.common_attribute.pk if i.common_attribute else None,
            'upc': i.upc
        })

    initial_externalrefs = []
    for i in ExternalRef.objects.filter(sale=sale):
        initial_externalrefs.append({
            'brand_attribute': i.brand_attribute.pk if i.brand_attribute else None,
            'common_attribute': i.common_attribute.pk if i.common_attribute else None,
            'external_id': i.external_id,
        })

    initial_ordersettings = []
    for i in OrderConfirmSetting.objects.filter(sale=sale):
        initial_ordersettings.append({
            'brand_attribute': i.brand_attribute.pk if i.brand_attribute else None,
            'common_attribute': i.common_attribute.pk if i.common_attribute else None,
            'require_confirm': i.require_confirm,
        })

    initial_product = {
        'brand': sale.product.brand.pk,
        'type': sale.product.type.pk,
        'category': sale.product.category.pk,
        'name': sale.product.name,
        'description': sale.product.description,
        'weight_unit': sale.product.weight_unit,
        'standard_weight': sale.product.standard_weight,
        'available_from': sale.product.available_from,
        'available_to': sale.product.available_to,
        'normal_price': sale.product.normal_price,
        'currency': sale.product.currency,
        'brand_attributes': brand_attributes,
        'pictures': pictures,
        'type_attribute_prices': type_attribute_prices,
        'type_attribute_weights': type_attribute_weights,
        'short_description': sale.product.short_description,
        'cover_pk': cover_picture['pk'] if cover_picture else None,
        'cover_url': cover_picture['thumb_url'] if cover_picture else None,
        'gender': sale.gender,
        'barcodes_initials': initial_barcodes,
        'externalrefs_initials': initial_externalrefs,
        'ordersettings_initials': initial_ordersettings,
        'varattrs_initials': initial_varattrs,
    }

    coupon = get_item_specific_discount_coupon(sale.mother_brand.id,
                                               id_sale=sale.id)
    if coupon:
        initial_product.update({
            'coupon_id': coupon.id,
            'discount': coupon.reward.rebate.ratio,
            'valid_from': coupon.valid.from_[:10] if coupon.valid.from_ else None,
            'valid_to': coupon.valid.to_[:10] if coupon.valid.to_ else None,
        })

    initial_shipping = {}
    if hasattr(sale, 'shippinginsale') and sale.shippinginsale:
        shipping = sale.shippinginsale.shipping
        initial_shipping = {
            'handling_fee': shipping.handling_fee,
            'allow_group_shipment': shipping.allow_group_shipment,
            'allow_pickup': shipping.allow_pickup,
            'pickup_voids_handling_fee': shipping.pickup_voids_handling_fee,
            'shipping_calculation': shipping.shipping_calculation,
            'service': [],
            'custom_shipping_rate': [],
        }

        if shipping.shipping_calculation == SC_CARRIER_SHIPPING_RATE:
            initial_shipping.update({
                'service': shipping.serviceinshipping_set.all()
            })
        if shipping.shipping_calculation == SC_CUSTOM_SHIPPING_RATE:
            initial_shipping.update({
                'custom_shipping_rate':
                    shipping.customshippingrateinshipping_set.all()
            })
        if shipping.shipping_calculation == SC_FLAT_RATE:
            fr_shipping = FlatRateInShipping.objects.filter(shipping=shipping)
            if fr_shipping:
                initial_shipping.update({
                    'flat_rate': fr_shipping[0].flat_rate
                })

    initials = {
        SaleWizardNew.STEP_SHOP: initial_shop,
        SaleWizardNew.STEP_PRODUCT: initial_product,
        SaleWizardNew.STEP_SHIPPING: initial_shipping,
    }

    settings = {
        'base_template': 'edit_sale_base.html',
        'edit_mode': True,
        'sale': sale
    }
    sale_wizard = manager_upper_required(
        SaleWizardNew.as_view(forms, initial_dict=initials,
                              url_name="edit_sale",
                              done_step_name="list_sales",
                              condition_dict={SaleWizardNew.STEP_SHOP: show_step_shop},
                              **settings),
        login_url="bo_login")

    return sale_wizard(request, *args, **kwargs)

class StocksInfos(object):
    def __init__(self):
        self.__dict__['shops'] = None
        self.__dict__['product_type'] = None
        self.__dict__['brand_attributes'] = None
        self.__dict__['barcodes'] = None

    def __setattr__(self, key, value):
        self.__dict__[key] = value

class SaleWizardNew(NamedUrlSessionWizardView):
    STEP_SHOP = 'shop'
    STEP_PRODUCT = 'product'
    STEP_SHIPPING = 'shipping'
    file_storage = FileSystemStorage()
    base_template = "add_sale_base.html"
    edit_mode = False
    sale = None
    skip_shop_step = False

    @transaction.commit_on_success
    def done(self, form_list, **kwargs):
        if self.skip_shop_step:
            product_form, shipping_form = form_list
            shop_form = None
        else:
            shop_form, product_form, shipping_form = form_list

        if self.edit_mode:
            sale = self.sale
            product = sale.product
            if hasattr(sale, 'shippinginsale') and sale.shippinginsale:
                shipping = sale.shippinginsale.shipping
            else:
                shipping = Shipping()
        else:
            sale = Sale()
            product = Product()
            shipping = Shipping()
            sale.mother_brand = self.request.user.get_profile().work_for
        sale.type_stock = shop_form and shop_form.cleaned_data['target_market'] or STOCK_TYPE_GLOBAL
        sale.save()

        if sale.type_stock == STOCK_TYPE_DETAILED:
            ShopsInSale.objects.filter(sale=sale).update(is_freezed=True)
            if shop_form:
                for shop in shop_form.cleaned_data['shops']:
                    shops_in_sale, created = ShopsInSale.objects.get_or_create(sale=sale,shop=shop)
                    shops_in_sale.is_freezed = False
                    shops_in_sale.save()
            #if the rest stock is same as initial stock and it is frozen, delete.
            #also remove the stock record for these.
            #update sale's total stock and rest_stock
            shops_to_be_removed = ShopsInSale.objects.filter(is_freezed = True, shop__in = [p.shop for p in ProductStock.objects.filter(sale=self.sale,stock=F('rest_stock'))])
            stocks_to_be_removed = ProductStock.objects.filter(sale=sale,shop__in=[s.shop for s in shops_to_be_removed])
            stocks_to_be_removed.delete()
            shops_to_be_removed.delete()

        product_data = product_form.cleaned_data
        product.sale = sale
        product.brand = product_data['brand']
        product.type = ProductType.objects.get(pk=product_data['type'])
        product.category = product_data['category']
        product.name = product_data['name']
        product.description = product_data['description']
        product.weight_unit = product_data['weight_unit']
        product.standard_weight = product_data['standard_weight']
        product.available_from = product_data['available_from'] or date.today()
        product.available_to = product_data['available_to']
        product.normal_price = product_data['normal_price']
        product.currency = product_data['currency']
        product.short_description = product_data['short_description']
        product.save()

        if product_data['coupon_id']:
            if product_data['discount']:
                # update item-specific coupon
                update_item_specific_coupon(
                    product_data['coupon_id'],
                    product.brand.id, self.request.user.id, sale.id,
                    product_data['discount'],
                    product_data['valid_from'],
                    product_data['valid_to'],
                )

            else:
                # delete coupon
                delete_coupon(product.brand.id, self.request.user.id,
                              product_data['coupon_id'])
        else:
            if product_data['discount']:
                # create the item-specific coupon
                create_item_specific_coupon(
                    product.brand.id, self.request.user.id, sale.id,
                    product_data['discount'],
                    product_data['valid_from'],
                    product_data['valid_to'],
                )

        sale.gender = product_data['gender']
        sale.save()

        ca_ids = [c.id for c in CommonAttribute.objects.filter(for_type=product.type)]
        ba_ids = []
        brand_attributes = product_form.brand_attributes
        for ba_form, ba in zip(brand_attributes, brand_attributes.cleaned_data):
            if not ba: continue

            if ba['DELETE']:
                baps = BrandAttributePreview.objects.filter(
                    brand_attribute=BrandAttribute.objects.get(pk=ba['ba_id']),
                    product=product)
                [bap.delete() for bap in baps if bap]

            else:
                ba_obj = BrandAttribute.objects.get(pk=ba['ba_id'])
                ba_obj.name = ba['name']
                ba_obj.premium_type = ba['premium_type']
                ba_obj.premium_amount = ba['premium_amount']
                ba_obj.texture = get_asset_name(ba['texture'])
                ba_obj.save()
                ba_ids.append(ba_obj.id)

                if not ba_form.previews.cleaned_data:
                    self._save_ba_preview(ba['ba_id'], product, None, None)

                for preview_data in ba_form.previews.cleaned_data:
                    if not preview_data: continue

                    preview = None
                    preview_pk = preview_data['pk']
                    if preview_pk:
                        preview = ProductPicture.objects.get(pk=preview_pk)
                    if not preview_data['DELETE']:
                        self._save_ba_preview(ba['ba_id'], product, preview_pk, preview)
                    else:
                        try:
                            bap = BrandAttributePreview.objects.get(
                                brand_attribute=BrandAttribute.objects.get(pk=ba['ba_id']),
                                product=product,
                                preview=preview)
                        except BrandAttributePreview.DoesNotExist:
                            pass
                        else:
                            if bap: bap.delete()
        if ba_ids:
            ProductStock.objects.filter(sale=sale, brand_attribute=None).delete()
        self._update_sale_stock_sum(sale)

        for pp_data in product_form.pictures.cleaned_data:
            if pp_data and not pp_data['DELETE'] and pp_data['sort_order']:
                pp = ProductPicture.objects.get(pk=int(pp_data['pk']))
                pp.sort_order = pp_data['sort_order']
                pp.save()

        pp_pks = [int(pp['pk']) for pp in product_form.pictures.cleaned_data
                                if pp and not pp['DELETE']]
        if product_form.cleaned_data['cover_pk']:
            pp_pks.append(product_form.cleaned_data['cover_pk'])
        product.pictures = ProductPicture.objects.filter(pk__in=pp_pks)
        product.save()

        varattr_ids = []
        for i in product_form.varattrs:
            if not i.is_valid() or not i.cleaned_data \
                    or not i.cleaned_data['value'] or i.cleaned_data['DELETE']:
                continue
            varattr, created = ProductTypeVarAttr.objects.get_or_create(sale=sale,
                    attr=VariableAttribute.objects.get(pk=i.cleaned_data['attr']))
            varattr.value = i.cleaned_data['value']
            varattr.save()
            varattr_ids.append(varattr.id)
        if varattr_ids:
            ProductTypeVarAttr.objects.filter(sale=sale).extra(
                where=['id NOT IN (%s)' % ','.join(map(str, varattr_ids))]).delete()
        else:
            ProductTypeVarAttr.objects.filter(sale=sale).delete()

        bc_ids = []
        for i in product_form.barcodes:
            if not i.is_valid() or not i.cleaned_data \
                    or not i.cleaned_data['upc'] or i.cleaned_data['DELETE']:
                continue
            ba_pk = i.cleaned_data['brand_attribute']
            ca_pk = i.cleaned_data['common_attribute']
            barcode, created = Barcode.objects.get_or_create(sale=sale,
                common_attribute=CommonAttribute.objects.get(pk=ca_pk) if ca_pk else None,
                brand_attribute=BrandAttribute.objects.get(pk=ba_pk) if ba_pk else None,
                )
            barcode.upc = i.cleaned_data['upc']
            barcode.save()
            bc_ids.append(barcode.id)
        if bc_ids:
            Barcode.objects.filter(sale=sale).extra(
                where=['id NOT IN (%s)' % ','.join(map(str, bc_ids))]).delete()
        else:
            Barcode.objects.filter(sale=sale).delete()

        ext_ids = []
        for i in product_form.externalrefs:
            if not i.is_valid() or not i.cleaned_data \
                    or not i.cleaned_data['external_id'] or i.cleaned_data['DELETE']:
                continue
            ba_pk = i.cleaned_data['brand_attribute']
            ca_pk = i.cleaned_data['common_attribute']
            externalref, created = ExternalRef.objects.get_or_create(sale=sale,
                common_attribute=CommonAttribute.objects.get(pk=ca_pk) if ca_pk else None,
                brand_attribute=BrandAttribute.objects.get(pk=ba_pk) if ba_pk else None,
                )
            externalref.external_id = i.cleaned_data['external_id']
            externalref.save()
            ext_ids.append(externalref.id)
        if ext_ids:
            ExternalRef.objects.filter(sale=sale).extra(
                where=['id NOT IN (%s)' % ','.join(map(str, ext_ids))]).delete()
        else:
            ExternalRef.objects.filter(sale=sale).delete()

        os_ids = []
        for i in product_form.ordersettings:
            if not i.is_valid() or not i.cleaned_data \
                    or not i.cleaned_data['require_confirm'] or i.cleaned_data['DELETE']:
                continue
            ba_pk = i.cleaned_data['brand_attribute']
            ca_pk = i.cleaned_data['common_attribute']
            os, created = OrderConfirmSetting.objects.get_or_create(sale=sale,
                common_attribute=CommonAttribute.objects.get(pk=ca_pk) if ca_pk else None,
                brand_attribute=BrandAttribute.objects.get(pk=ba_pk) if ba_pk else None,
                )
            os.require_confirm = i.cleaned_data['require_confirm']
            os.save()
            os_ids.append(os.id)
        if os_ids:
            OrderConfirmSetting.objects.filter(sale=sale).extra(
                where=['id NOT IN (%s)' % ','.join(map(str, os_ids))]).delete()
        else:
            OrderConfirmSetting.objects.filter(sale=sale).delete()

        shipping_data = shipping_form.cleaned_data
        shipping.sale = sale
        shipping.handling_fee = shipping_data['handling_fee']
        shipping.allow_group_shipment = shipping_data['allow_group_shipment']
        shipping.allow_pickup = shipping_data['allow_pickup']
        shipping.pickup_voids_handling_fee = (
            shipping_data['allow_pickup'] and
            shipping_data['pickup_voids_handling_fee'])
        shipping.shipping_calculation = shipping_data['shipping_calculation']
        shipping.save()

        if shipping_data['set_as_default_shop_shipping']:
            if shop_form:
                for shop in shop_form.cleaned_data['shops']:
                    df_shipping, _ = DefaultShipping.objects.get_or_create(
                        shop=shop,
                        defaults={'shipping': shipping})
                    df_shipping.shipping = shipping
                    df_shipping.save()

        if self.edit_mode:
            # Remove useless records.
            if int(shipping.shipping_calculation) != int(SC_CARRIER_SHIPPING_RATE):
                shipping.serviceinshipping_set.all().delete()
            if int(shipping.shipping_calculation) != int(SC_CUSTOM_SHIPPING_RATE):
                shipping.customshippingrateinshipping_set.all().delete()
            if int(shipping.shipping_calculation) != int(SC_FLAT_RATE):
                FlatRateInShipping.objects.filter(shipping=shipping).delete()

            # Merge records:
            if int(shipping.shipping_calculation) == int(SC_CARRIER_SHIPPING_RATE):
                old_service_ids = set([scs.service.id for scs in
                                       shipping.serviceinshipping_set.all()])
                new_service_ids = set([service.id for service in
                                       shipping_data['service']])

                for s_id in old_service_ids - new_service_ids:
                    shipping.serviceinshipping_set.get(
                        shipping=shipping, service_id=s_id
                    ).delete()
                for s_id in new_service_ids - old_service_ids:
                    shipping.serviceinshipping_set.create(
                        shipping=shipping, service_id=s_id)

            if int(shipping.shipping_calculation) == int(SC_CUSTOM_SHIPPING_RATE):
                old_rate_ids = set([csr.custom_shipping_rate.id for csr in
                                    shipping.customshippingrateinshipping_set.all()])
                new_rate_ids = set([csr.id for csr in
                                    shipping_data['custom_shipping_rate']])

                for c_id in old_rate_ids - new_rate_ids:
                    shipping.customshippingrateinshipping_set.get(
                        shipping=shipping, custom_shipping_rate_id=c_id
                    ).delete()
                for c_id in new_rate_ids - old_rate_ids:
                    shipping.customshippingrateinshipping_set.create(
                        shipping=shipping, custom_shipping_rate_id=c_id)

            if int(shipping.shipping_calculation) == int(SC_FLAT_RATE):
                fr_shipping, _ = FlatRateInShipping.objects.get_or_create(shipping=shipping)
                fr_shipping.flat_rate = shipping_data['flat_rate']
                fr_shipping.save()

            if not hasattr(sale, 'shippinginsale') or not sale.shippinginsale:
                sale.shippinginsale = ShippingInSale.objects.create(
                    sale=sale, shipping=shipping)
        else:
            if int(shipping.shipping_calculation) == int(SC_CARRIER_SHIPPING_RATE):
                for service in shipping_data['service']:
                    shipping.serviceinshipping_set.create(
                        shipping=shipping, service=service)
            if int(shipping.shipping_calculation) == int(SC_CUSTOM_SHIPPING_RATE):
                for shipping_rate in shipping_data['custom_shipping_rate']:
                    shipping.customshippingrateinshipping_set.create(
                        shipping=shipping, custom_shipping_rate=shipping_rate)
            if int(shipping.shipping_calculation) == int(SC_FLAT_RATE):
                FlatRateInShipping.objects.create(
                    shipping=shipping, flat_rate=shipping_data['flat_rate'])
            sale.shippinginsale = ShippingInSale.objects.create(
                sale=sale, shipping=shipping)

        sale.complete = True
        sale.product = product
        sale.save()

        type_attribute_prices = product_form.type_attribute_prices
        for tap in type_attribute_prices.cleaned_data:
            if tap['DELETE']:
                if tap['tap_id'] < 0:
                    continue
                try:
                    tap_obj = TypeAttributePrice.objects.get(pk=tap['tap_id'])
                    tap_obj.delete()
                except ObjectDoesNotExist:
                    logging.error('No TypeAttributePrice Object found for '
                                  'id:%s' % tap['tap_id'])
            else:
                if tap['tap_id'] > 0:
                    continue
                ta = CommonAttribute.objects.get(pk=tap['type_attribute'])
                s_tap = TypeAttributePrice.objects.create(
                    sale=sale,
                    type_attribute=ta,
                    type_attribute_price=tap['type_attribute_price']
                )
                s_tap.save()

        type_attribute_weights = product_form.type_attribute_weights
        for taw in type_attribute_weights.cleaned_data:
            if taw['DELETE']:
                if taw['taw_id'] < 0:
                    continue
                try:
                    taw_obj = TypeAttributeWeight.objects.get(pk=taw['taw_id'])
                    taw_obj.delete()
                except ObjectDoesNotExist:
                    logging.error('No TypeAttributeWeight Object found for '
                                  'id:%s' % taw['taw_id'])
            else:
                if taw['taw_id'] > 0:
                    continue
                ta = CommonAttribute.objects.get(pk=taw['type_attribute'])
                s_taw = TypeAttributeWeight.objects.create(
                    sale=sale,
                    type_attribute=ta,
                    type_attribute_weight=taw['type_attribute_weight'])
                s_taw.save()

        if self.request.session.get('stocks_infos', None):
            del(self.request.session['stocks_infos'])
        if (not self.edit_mode and
                self.request.session.get('abandoned_sale', None)):
            del(self.request.session['abandoned_sale'])

        is_unique_items = get_ba_settings(self.request.user).get('unique_items') == 'True'
        if not self.edit_mode and is_unique_items:
            self._save_unique_item_stock(sale, ba_ids, ca_ids)

        send_cache_invalidation(self.edit_mode and "PUT" or "POST",
                                'sale', sale.id)
        save_sale_promotion_handler(sale)

        if not self.edit_mode and not is_unique_items:
            return redirect("sale_list_stocks", sale=sale.id)
        return redirect("list_sales")

    def _save_unique_item_stock(self, sale, ba_ids, ca_ids):
        if sale.shops.count() == 0:
            shop_ids = [None]
        else:
            shop_ids = [s.id for s in sale.shops.all()]

        for shop_id in shop_ids:
            for ba_id in ba_ids or [None]:
                for ca_id in ca_ids or [None]:
                    stock, created = ProductStock.objects.get_or_create(sale=sale,
                        shop_id=shop_id,
                        common_attribute_id=ca_id,
                        brand_attribute_id=ba_id,
                        stock=1,
                        rest_stock=1,
                        )
        self._update_sale_stock_sum(sale)

    def _update_sale_stock_sum(self, sale):
        sale_stock_sum = sale.detailed_stock.aggregate(stock_sum=Sum('stock'),
                                                       rest_stock_sum=Sum('rest_stock'))
        sale.total_stock = sale_stock_sum['stock_sum'] or 0
        sale.total_rest_stock = sale_stock_sum['rest_stock_sum'] or 0
        if sale.total_rest_stock < 0:
            sale.total_rest_stock = 0
        if sale.total_stock < sale.total_rest_stock:
            sale.total_stock = sale.total_rest_stock
        sale.save()

    def _save_ba_preview(self, ba_pk, product, preview_pk, preview):
        try:
            bap = BrandAttributePreview.objects.get(
                brand_attribute_id=ba_pk,
                product=product,
                preview=None)
        except BrandAttributePreview.DoesNotExist:
            pass
        else:
            if preview_pk and preview_pk != bap.preview_id:
                bap.preview = preview
                bap.save()

        (bap, created) = BrandAttributePreview.objects.get_or_create(
            brand_attribute=BrandAttribute.objects.get(pk=ba_pk),
            product=product,
            preview=preview
        )
        bap.save()

    def dispatch(self, request, *args, **kwargs):
        self.stocks_infos = request.session.get('stocks_infos', StocksInfos())
        return super(SaleWizardNew, self).dispatch(request, *args, **kwargs)

    def _reset_storage(self):
        self.storage.reset()
        self.storage.current_step = self.steps.first

    def get(self, request, *args, **kwargs):
        step_url = kwargs.get('step', None)
        if self.edit_mode:
            if step_url == self.steps.first:
                self._reset_storage()
        else:
            if step_url is None:
                self._reset_storage()
                if self.request.session.get('abandoned_sale', None):
                    self.storage.data = self.request.session['abandoned_sale']
        self.skip_shop_step = (self.steps.count == 2)  # hard code
        return super(NamedUrlSessionWizardView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Override post to catch cancel actions, else just call super
        """
        wizard_cancel = self.request.POST.get('wizard_cancel', None)
        if wizard_cancel:
            self.storage.reset()
            if self.request.session.get('stocks_infos', None):
                del(self.request.session['stocks_infos'])
            if (not self.edit_mode and
                    self.request.session.get('abandoned_sale', None)):
                del(self.request.session['abandoned_sale'])

            return redirect('/')
        if self.edit_mode:
            prev_step = self.request.POST.get('wizard_prev_step', None)
            if prev_step and prev_step in self.get_form_list():
                self.storage.current_step = prev_step
                return redirect(self.url_name, step=prev_step, sale_id=self.sale.pk)
        else:
            self.request.session['abandoned_sale'] = self.storage.data

        return super(SaleWizardNew, self).post(*args, **kwargs)

    def process_step(self, form):
        if self.steps.current == self.STEP_SHOP:
            self.stocks_infos.shops = form.cleaned_data
        elif self.steps.current == self.STEP_PRODUCT:
            self.stocks_infos.product_type = form.cleaned_data['type']
            self.stocks_infos.brand_attributes = form.brand_attributes.cleaned_data
        return super(SaleWizardNew, self).process_step(form)

    def render(self, form=None, **kwargs):
#        if self.request.session.get("edit_mode", False):
#            self.base_template = "edit_sale_base.html"
        self.template_name = "add_sale_"+str(self.steps.current)+".html"
        form = form or self.get_form()
        context = self.get_context_data(form, **kwargs)
        self.request.session['stocks_infos'] = self.stocks_infos
        return self.render_to_response(context)

    def render_next_step(self, form, **kwargs):
        if self.edit_mode:
            next_step = self.get_next_step()
            self.storage.current_step = next_step
            return redirect(self.url_name, step=next_step, sale_id=self.sale.pk)
        return super(SaleWizardNew, self).render_next_step(form, **kwargs)

    def render_revalidation_failure(self, failed_step, form, **kwargs):
        if self.edit_mode:
            self.storage.current_step = failed_step
            return redirect(self.url_name, step=failed_step, sale_id=self.sale.pk)
        return super(SaleWizardNew, self).render_revalidation_failure(failed_step, form, **kwargs)

    def render_done(self, form, **kwargs):
        if self.edit_mode:
            if kwargs.get('step', None) != self.done_step_name:
                return redirect(self.url_name, step=self.done_step_name, sale_id=self.sale.pk)
        return super(SaleWizardNew, self).render_done(form, **kwargs)

    def _render_preview(self, step):
        context = {
            'context': self.get_form(step, self.storage.get_step_data(step),
                                     self.storage.get_step_files(step))
        }
        t = loader.get_template("add_sale_preview_"+step+".html")
        c = Context(context)
        return t.render(c)

    def get_context_data(self, form, *args, **kwargs):
        context = super(SaleWizardNew, self).get_context_data(form, *args, **kwargs)
        if self.edit_mode:
            context.update({
                'sale_id': self.sale.pk
            })
        context.update({
            'request': self.request,
            'base_template': self.base_template
        })
        if self.steps.current == self.STEP_SHOP:
            context.update({
                'form_title': _("Shops Selection"),
                'brand_currency': get_currency(self.request.user),
                'preview_shop': "blank",
                'shops_cant_be_deleted': ','.join(list(set(
                   [str(p.shop.pk) for p in ProductStock.objects.filter(sale=self.sale).exclude(stock=F('rest_stock'))
                    if p.shop and p.shop.pk in ShopsInSale.objects.filter(sale=self.sale,is_freezed=False).values_list('shop_id',flat=True)]
                   ))),
                'freezed_shops': ','.join([str(s.shop.pk) for s in ShopsInSale.objects.filter(sale=self.sale,is_freezed=True)]),
            })
        elif self.steps.current == self.STEP_PRODUCT:
            context.update({
                'product_brand_form': ProductBrandFormModel,
                'sale_img_upload_max_size': settings.SALE_IMG_UPLOAD_MAX_SIZE,
                'common_attributes': getattr(self, 'common_attributes', []),
            })
        elif self.steps.current == self.STEP_SHIPPING:
            context.update({
                'form_title': _("Shipping"),
                'currency': self.currency,
                'shipping_weight_unit': SHIPPING_WEIGHT_UNIT,
                'shipping_currency': self.currency,
                'custom_shipping_rate_form': CustomShippingRateFormModel,
            })

        context.update({'price_label': _("(after tax)")
                if get_default_setting('use_after_tax_price',
                                       self.request.user) == 'True' else ""})
        return context

    def get_form_kwargs(self, step=None):
        if step in (self.STEP_SHOP, self.STEP_PRODUCT, self.STEP_SHIPPING):
            kwargs = {}
            if step == self.STEP_SHOP:
                kwargs.update({"request": self.request,})
            if self.edit_mode:
                kwargs.update({'mother_brand': self.sale.mother_brand,})
            else:
                kwargs.update(
                    {'mother_brand': self.request.user.get_profile().work_for,})
            if step == self.STEP_PRODUCT and not self.edit_mode:
                kwargs.update({'add_new': True,})

            return kwargs
        return super(SaleWizardNew, self).get_form_kwargs(step)

    def _get_varattr(self, attr_id):
        if self.edit_mode:
            for i in self.initial_dict.get(self.STEP_PRODUCT).get('varattrs_initials', []):
                if i['attr'] == attr_id:
                    return i['value']
        return None

    def _get_barcode(self, ba, ca):
        if self.edit_mode:
            for i in self.initial_dict.get(self.STEP_PRODUCT).get('barcodes_initials', []):
                if i['brand_attribute'] == ba:
                    if i['common_attribute'] == ca:
                        return i['upc']
        else:
            if self.stocks_infos.barcodes:
                for i in self.stocks_infos.barcodes:
                    if i:
                        if i['brand_attribute'] == ba:
                            if i['common_attribute'] == ca:
                                return i['upc']
        return None

    def _get_external_id(self, ba, ca):
        if self.edit_mode:
            for i in self.initial_dict.get(self.STEP_PRODUCT).get('externalrefs_initials', []):
                if i['brand_attribute'] == ba:
                    if i['common_attribute'] == ca:
                        return i['external_id']
        else:
            if getattr(self.stocks_infos, 'externalrefs', None):
                for i in self.stocks_infos.externalrefs:
                    if i:
                        if i['brand_attribute'] == ba:
                            if i['common_attribute'] == ca:
                                return i['external_id']
        return None

    def _get_require_confirm(self, ba, ca):
        if self.edit_mode:
            for i in self.initial_dict.get(self.STEP_PRODUCT).get('ordersettings_initials', []):
                if i['brand_attribute'] == ba:
                    if i['common_attribute'] == ca:
                        return i['require_confirm']
        else:
            if getattr(self.stocks_infos, 'ordersettings', None):
                for i in self.stocks_infos.ordersettings:
                    if i:
                        if i['brand_attribute'] == ba:
                            if i['common_attribute'] == ca:
                                return i['require_confirm']
        return get_ba_settings(self.request.user).get('order_require_confirmation') == 'True'

    def _get_stock_initial(self, ba, ca, sh, st):
        return {
            'brand_attribute': ba,
            'common_attribute': ca,
            'shop': sh,
            'stock': st,
        }

    def get_form_initial(self, step):
        if step is None:
            step = self.steps.current

        if step == self.STEP_PRODUCT:
            initial_product = super(SaleWizardNew, self).get_form_initial(step)
            # the shop step is skipped, set default value "global"
            if self.skip_shop_step is True:
                self.storage.set_step_data(self.STEP_SHOP,
                                           {'shop-target_market': STOCK_TYPE_GLOBAL})
            if not self.edit_mode:
                shop_obj = self.get_form(self.STEP_SHOP,
                    data=self.storage.get_step_data(self.STEP_SHOP))
                if not shop_obj.is_valid():
                    return {}
                currency = get_sale_currency(self.request, shop_obj.cleaned_data)
                initial_product.update({'currency':
                        ProductCurrency.objects.get(code=currency)})

            if self.stocks_infos.shops:
                initial_product['shop_ids'] = json.dumps(
                        [s.id for s in self.stocks_infos.shops.get('shops', [])])
            else:
                initial_product['shop_ids'] = json.dumps([])

            product_init_data = self.initial_dict.get(self.STEP_PRODUCT)
            if product_init_data.get('type'):
                initial_product.update(self._init_varattrs(product_init_data['type']))
                c_attrs = CommonAttribute.objects.filter(for_type=product_init_data['type'])
                c_attrs = [c for c in c_attrs]
            else:
                c_attrs = []
            self.common_attributes = c_attrs
            b_attrs = product_init_data.get('brand_attributes', [])
            initial_product.update(self._init_barcodes(b_attrs, c_attrs))
            initial_product.update(self._init_externalrefs(b_attrs, c_attrs))
            initial_product.update(self._init_ordersettings(b_attrs, c_attrs))
            return initial_product

        if step == self.STEP_SHIPPING:
            product_obj = self.get_form(self.STEP_PRODUCT,
                                        data=self.storage.get_step_data(self.STEP_PRODUCT),
                                        files=self.storage.get_step_files(self.STEP_PRODUCT)
            )
            if product_obj.is_valid():
                self.currency = product_obj.cleaned_data['currency']
        return super(SaleWizardNew, self).get_form_initial(step)

    def _init_varattrs(self, type_id):
        initials = []
        for v in VariableAttribute.objects.filter(for_type_id=type_id):
            initials.append({
                'type': type_id,
                'attr': v.id,
                'name': v.name,
                'value': self._get_varattr(v.id),
            })
        return {'varattrs_initials': initials}

    def _init_barcodes(self, brand_attributes, common_attributes):
        # Initializes the initials for barcodes form
        initials = []
        if common_attributes:
            for ca in common_attributes:
                initials.append({
                    'brand_attribute': None,
                    'common_attribute': ca.pk,
                    'upc': self._get_barcode(None, ca.pk),
                })
        else:
            initials.append({
                'brand_attribute': None,
                'common_attribute': None,
                'upc': self._get_barcode(None, None),
                })

        if brand_attributes:
            for ba in brand_attributes:
                if common_attributes:
                    for ca in common_attributes:
                        initials.append({
                            'brand_attribute': ba['ba_id'],
                            'common_attribute': ca.pk,
                            'upc': self._get_barcode(ba['ba_id'], ca.pk),
                        })
                else:
                    initials.append({
                        'brand_attribute': ba['ba_id'],
                        'common_attribute': None,
                        'upc': self._get_barcode(ba['ba_id'], None),
                        })
        return {'barcodes_initials': initials}

    def _init_externalrefs(self, brand_attributes, common_attributes):
        # Initializes the initials for externalrefs form
        initials = []
        if common_attributes:
            for ca in common_attributes:
                initials.append({
                    'brand_attribute': None,
                    'common_attribute': ca.pk,
                    'external_id': self._get_external_id(None, ca.pk),
                })
        else:
            initials.append({
                'brand_attribute': None,
                'common_attribute': None,
                'external_id': self._get_external_id(None, None),
                })

        if brand_attributes:
            for ba in brand_attributes:
                if common_attributes:
                    for ca in common_attributes:
                        initials.append({
                            'brand_attribute': ba['ba_id'],
                            'common_attribute': ca.pk,
                            'external_id': self._get_external_id(ba['ba_id'], ca.pk),
                        })
                else:
                    initials.append({
                        'brand_attribute': ba['ba_id'],
                        'common_attribute': None,
                        'external_id': self._get_external_id(ba['ba_id'], None),
                        })
        return {'externalrefs_initials': initials}

    def _init_ordersettings(self, brand_attributes, common_attributes):
        # Initializes the initials for ordersettings form
        initials = []
        if common_attributes:
            for ca in common_attributes:
                initials.append({
                    'brand_attribute': None,
                    'common_attribute': ca.pk,
                    'require_confirm': self._get_require_confirm(None, ca.pk),
                })
        else:
            initials.append({
                'brand_attribute': None,
                'common_attribute': None,
                'require_confirm': self._get_require_confirm(None, None),
                })

        if brand_attributes:
            for ba in brand_attributes:
                if common_attributes:
                    for ca in common_attributes:
                        initials.append({
                            'brand_attribute': ba['ba_id'],
                            'common_attribute': ca.pk,
                            'require_confirm': self._get_require_confirm(ba['ba_id'], ca.pk),
                        })
                else:
                    initials.append({
                        'brand_attribute': ba['ba_id'],
                        'common_attribute': None,
                        'require_confirm': self._get_require_confirm(ba['ba_id'], None),
                        })
        return {'ordersettings_initials': initials}


def get_product_types(request, *args, **kwargs):
    types = list(ProductType.objects.filter(Q(is_default=True) & Q(valid=True)))

    brand = request.user.get_profile().work_for
    cat_id = kwargs.get('cat_id')
    cat = ProductCategory.objects.filter(pk=cat_id).filter(brand=brand)
    if cat:
        cat_maps = CategoryTypeMap.objects\
            .filter(category_id=cat_id)\
            .filter(type__brand=brand)

        types.extend([map.type for map in cat_maps])
        map_types = CategoryTypeMap.objects\
            .order_by('type')\
            .values('type')\
            .distinct()
        orphan_types = ProductType.objects\
            .filter(brand=brand)\
            .exclude(id__in=map_types)

        orphan_types = list(orphan_types)
        types.extend(orphan_types)

    product_types_list = [{'label': t.name, 'value': t.id, 'valid': t.valid}
                          for t in types]
    return HttpResponse(json.dumps(product_types_list),
                        mimetype='application/json')


def get_item_varattr_values(request, *args, **kwargs):
    keyword = request.GET.get('term', '').strip()
    attrs = ProductTypeVarAttr.objects.filter(
        attr_id=kwargs.get('aid', None),
        value__contains=keyword)

    values = []
    for attr in attrs:
        if attr in values:
            continue
        values.append(attr.value)
    return HttpResponse(json.dumps(values),
                        mimetype='application/json')

