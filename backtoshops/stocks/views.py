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

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.db.models.aggregates import Sum
from django import forms
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View, TemplateResponseMixin
from fouillis.views import OperatorUpperLoginRequiredMixin

from attributes.models import BrandAttribute
from attributes.models import CommonAttribute
from barcodes.models import Barcode
from brandsettings import get_ba_settings
from common.cache_invalidation import send_cache_invalidation
from common.error import UsersServerError
from common.error import ParamsValidCheckError
from orders.views import _get_req_user_shops
from sales.models import ExternalRef
from sales.models import OrderConfirmSetting
from sales.models import Product
from sales.models import Sale
from shops.models import Shop
from sales.models import ShopsInSale
from sales.models import STOCK_TYPE_GLOBAL
from stocks.models import ProductStock
from stocks.forms import StockForm
from stocks.forms import StockListForm


class OutOfStockError(Exception):
    pass

def need_invalidate_cache(old_stock, new_stock):
    old_stock = old_stock or 0
    new_stock = new_stock or 0
    return old_stock <= 0 and new_stock > 0 \
        or old_stock > 0 and new_stock <= 0

def update_stock(sale_id, ba_id, ca_id, shop_id,
                 input_stock=None, delta_stock=None, alert=None):
    sale = Sale.objects.get(pk=sale_id)

    if shop_id and ShopsInSale.objects.get(shop_id=shop_id, sale=sale).is_freezed:
        raise Exception('this shop is frozen, can\'t update stocks')

    stock, created = ProductStock.objects.get_or_create(sale=sale,
        shop=Shop.objects.get(pk=shop_id) if shop_id else None,
        common_attribute=CommonAttribute.objects.get(pk=ca_id) if ca_id else None,
        brand_attribute=BrandAttribute.objects.get(pk=ba_id) if ba_id else None,
        )

    if input_stock is not None and stock.rest_stock == input_stock:
        invalid_cache = False
    else:
        if input_stock is None:
            input_stock = stock.rest_stock + delta_stock
            if input_stock < 0:
                raise OutOfStockError({'id_sale': sale_id, 'id_variant': ba_id,
                                       'id_type': ca_id, 'id_shop': shop_id,
                                       'quantity': stock.rest_stock})
        invalid_cache = need_invalidate_cache(stock.rest_stock, input_stock)
        stock.rest_stock = input_stock or 0
        if stock.rest_stock < 0:
            stock.rest_stock = 0
        if stock.stock < stock.rest_stock:
            stock.stock = stock.rest_stock
    if alert is not None and stock.alert != alert:
        stock.alert = alert
    stock.save()

    sale_stock_sum = sale.detailed_stock.aggregate(stock_sum=Sum('stock'),
                                                   rest_stock_sum=Sum('rest_stock'))
    invalid_cache = invalid_cache or \
                    need_invalidate_cache(sale.total_rest_stock,
                                          sale_stock_sum['rest_stock_sum'])
    sale.total_stock = sale_stock_sum['stock_sum'] or 0
    sale.total_rest_stock = sale_stock_sum['rest_stock_sum'] or 0
    if sale.total_rest_stock < 0:
        sale.total_rest_stock = 0
    if sale.total_stock < sale.total_rest_stock:
        sale.total_stock = sale.total_rest_stock
    sale.save()

    if invalid_cache:
        send_cache_invalidation("PUT", 'sale', sale.id)
    return sale


class ListStocksView(OperatorUpperLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = 'stock_list.html'

    def get(self, request, *args, **kwargs):
        req_params = request.GET
        return self._handle_req(req_params, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        req_params = request.POST
        for f in StockListForm(data=req_params).stocks:
            if f.is_valid():
                self._save_row(f)
        return self._handle_req(req_params, *args, **kwargs)

    def _save_row(self, stock_form):
        self._save_stock(stock_form)
        self._save_order_confirm_setting(stock_form)

    def _save_stock(self, stock_form):
        sale_id = stock_form.cleaned_data['sale_id']
        ba_id = stock_form.cleaned_data['ba_id']
        ca_id = stock_form.cleaned_data['ca_id']
        shop_id = stock_form.cleaned_data['shop_id']
        input_stock = stock_form.cleaned_data['stock']
        alert = stock_form.cleaned_data['alert'] == 'True'
        try:
            update_stock(sale_id, ba_id, ca_id, shop_id,
                         input_stock=input_stock, alert=alert)
        except Exception:
            pass

    def _save_order_confirm_setting(self, stock_form):
        sale = Sale.objects.get(pk=stock_form.cleaned_data['sale_id'])
        ba_id = stock_form.cleaned_data['ba_id']
        ca_id = stock_form.cleaned_data['ca_id']
        order_require_confirm = stock_form.cleaned_data['order_require_confirm'] == 'True'

        ocs, created = OrderConfirmSetting.objects.get_or_create(sale=sale,
            common_attribute=CommonAttribute.objects.get(pk=ca_id) if ca_id else None,
            brand_attribute=BrandAttribute.objects.get(pk=ba_id) if ba_id else None,
            )
        ocs.require_confirm = order_require_confirm
        ocs.save()

    def _handle_req(self, req_params, *args, **kwargs):
        sale_id = self.kwargs.get('sale')
        search = req_params.get('search') or ''
        if sale_id:
            sale = Sale.objects.get(pk=sale_id)
            sales_list = [sale]
            if sale.shops.count() == 0:
                shops_id = [0]
            else:
                shops_id = [s.id for s in sale.shops.all()]
            shop_id = self.kwargs.get('shop') or shops_id[0]
            shop_id = int(shop_id)
        else:
            shops_id = _get_req_user_shops(self.request.user)
            shops_id.reverse()
            shop_id = self.kwargs.get('shop') or shops_id[0]
            shop_id = int(shop_id)
            sales_list = self.get_sales_list(shop_id, search)

        shop_tabs = self.get_tabs(shops_id)
        stocks_list = self.get_stocks_list(shop_id, sales_list)
        paginator, page_obj, object_list, is_paginated = self.make_page(stocks_list)

        data = {
            'shop_tabs': shop_tabs,
            'current_tab': shop_id,
            'search': search,
            'stocks_form': StockListForm(initial=object_list),
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': is_paginated,
            'sale_id': sale_id,
            'request': self.request,
        }
        return self.render_to_response(data)

    def get_tabs(self, shops_id):
        shop_tabs = []
        for _shop_id in shops_id:
            if _shop_id:
                shop_tabs.append({'name': Shop.objects.get(pk=_shop_id).name,
                                  'shop_id': _shop_id})
            else:
                shop_tabs.append({'name': _("Global"),
                                  'shop_id': 0})
        return shop_tabs

    def get_sales_list(self, shop_id, search):
        if shop_id in (0, '0'):
            shop_id = None

        if self.request.user.is_superuser:
            sales = Sale.objects.all()
        else:
            brand = self.request.user.get_profile().work_for
            sales = Sale.objects.filter(mother_brand=brand)

        if shop_id:
            sales = sales.filter(Q(shops__in=Shop.objects.filter(pk=shop_id)))
        else:
            sales = sales.filter(Q(type_stock=STOCK_TYPE_GLOBAL))
        if search:
            sales = sales.filter(
                Q(product__name__icontains=search)|
                Q(product__description__icontains=search)|
                Q(product__short_description__icontains=search)|
                Q(barcodes__upc__contains=search) |
                Q(externalrefs__external_id__contains=search)
            ).distinct()
        return sales.order_by('id')

    def get_stocks_list(self, shop_id, sales):
        if shop_id in (0, '0'):
            shop_id = None

        stocks_list = []
        for sale in sales:
            br_attrs = sale.product.brand_attributes.all().distinct()
            co_attrs = CommonAttribute.objects.filter(for_type=sale.product.type)
            if br_attrs:
                for ba in br_attrs:
                    if co_attrs:
                        for ca in co_attrs:
                            stocks_list.append(
                                    self._get_row(shop_id, sale, ba, ca))
                    else:
                        stocks_list.append(
                                self._get_row(shop_id, sale, ba, None))
            else:
                if co_attrs:
                    for ca in co_attrs:
                        stocks_list.append(
                                self._get_row(shop_id, sale, None, ca))
                else:
                    stocks_list.append(
                            self._get_row(shop_id, sale, None, None))
        return stocks_list

    def _get_row(self, shop_id, sale, ba, ca):
        try:
            stock_obj = ProductStock.objects.get(sale=sale, shop_id=shop_id,
                                             brand_attribute=ba,
                                             common_attribute=ca)
            stock = stock_obj.rest_stock
            alert = stock_obj.alert
        except ProductStock.DoesNotExist:
            stock = 0
            alert = False

        try:
            barcode = Barcode.objects.get(sale=sale,
                                          brand_attribute=ba,
                                          common_attribute=ca).upc
        except Barcode.DoesNotExist:
            barcode = ''

        try:
            sku = ExternalRef.objects.get(sale=sale,
                                          brand_attribute=ba,
                                          common_attribute=ca).external_id
        except ExternalRef.DoesNotExist:
            sku = ''

        try:
            require_confirm = OrderConfirmSetting.objects.get(sale=sale,
                                          brand_attribute=ba,
                                          common_attribute=ca).require_confirm
        except OrderConfirmSetting.DoesNotExist:
            require_confirm = get_ba_settings(self.request.user).get('order_require_confirmation') == 'True'

        sale_cover = None
        if sale.product.pictures.count() > 0:
            sale_cover = sale.product.pictures.order_by('sort_order', 'id')[0].picture

        row_data = {
            'sale_id': sale.id,
            'shop_id': shop_id,
            'ba_id': ba.pk if ba else None,
            'ca_id': ca.pk if ca else None,
            'ba_name': ba.name if ba else '',
            'ca_name': ca.name if ca else '',
            'sale_cover': sale_cover.url if sale_cover else '',
            'product_name': sale.product.name or '',
            'stock': stock,
            'barcode': barcode,
            'sku': sku,
            'alert': alert,
            'order_require_confirm': require_confirm,
        }
        return row_data

    def make_page(self, stocks_list):
        current_page = self.kwargs.get('page') or 1
        paginator = Paginator(stocks_list, settings.DEFAULT_PAGE_SIZE)
        try:
            page = paginator.page(current_page)
        except(EmptyPage, InvalidPage):
            page = paginator.page(paginator.num_pages)
            current_page = paginator.num_pages
        return (paginator, page, page.object_list, page.has_other_pages())


class UpdateSkuAjaxView(View):
    def post(self, request):
        result = {}
        try:
            params = request.POST
            for field in ('sale_id', 'ba_id', 'ca_id', 'shop_id', 'sku'):
                if field not in params:
                    raise forms.ValidationError(_('missing paramater %s' % field))

            sale = Sale.objects.get(pk=params['sale_id'])
            ba_id = params['ba_id']
            ca_id = params['ca_id']
            shop_id = params['shop_id']
            new_sku = params['sku']

            ext_ref, created = ExternalRef.objects.get_or_create(sale=sale,
                common_attribute=CommonAttribute.objects.get(pk=ca_id) if ca_id else None,
                brand_attribute=BrandAttribute.objects.get(pk=ba_id) if ba_id else None,
                )
            if ext_ref.external_id != new_sku:
                self._valid(new_sku, shop_id)
                ext_ref.external_id = new_sku
                ext_ref.save()
            result['success'] = True
            result['value'] = ext_ref.external_id
        except forms.ValidationError, e:
            result['err'] = e.messages[0]
        except Exception, e:
            logging.error('Got exception: %s', e, exc_info=True)

        return HttpResponse(json.dumps(result), mimetype="application/json")

    def _valid(self, new_exid, shop_id):
        if isinstance(shop_id, str) and shop_id.isdigit():
            shop_id = int(shop_id)
        # In one shop, cannot have 2 same external id for two sale items.
        refs_with_same_exid = ExternalRef.objects.filter(external_id=new_exid)
        for ref in refs_with_same_exid:
            pro = Product.objects.get(sale=ref.sale)
            if pro.valid_to and pro.valid_to < date.today():
                continue
            # check: 1. the same external_id is in global shop when current sale in global shop.
            #        2. the same external_id is in same shop.
            shops_id = [s.id for s in ref.sale.shops.all()]
            if not shop_id and len(shops_id) == 0:
                raise forms.ValidationError(_("external refs %s already used in global market." % new_exid))
            elif shop_id and shop_id in shops_id:
                raise forms.ValidationError(_("external refs %s already used in your shop." % new_exid))


class UpdateBarcodeAjaxView(View):
    def post(self, request):
        result = {}
        try:
            params = request.POST
            for field in ('sale_id', 'ba_id', 'ca_id', 'shop_id', 'barcode'):
                if field not in params:
                    raise forms.ValidationError(_('missing paramater %s' % field))

            sale = Sale.objects.get(pk=params['sale_id'])
            ba_id = params['ba_id']
            ca_id = params['ca_id']
            shop_id = params['shop_id']
            new_upc = params['barcode']

            barcode, created = Barcode.objects.get_or_create(sale=sale,
                common_attribute=CommonAttribute.objects.get(pk=ca_id) if ca_id else None,
                brand_attribute=BrandAttribute.objects.get(pk=ba_id) if ba_id else None,
                )
            if barcode.upc != new_upc:
                self._valid(new_upc, shop_id)
                barcode.upc = new_upc
                barcode.save()
            result['success'] = True
            result['value'] = barcode.upc
        except forms.ValidationError, e:
            result['err'] = e.messages[0]
        except Exception, e:
            result['err'] = str(e)
            logging.error('Got exception: %s', e, exc_info=True)

        return HttpResponse(json.dumps(result), mimetype="application/json")

    def _valid(self, new_upc, shop_id):
        if isinstance(shop_id, str) and shop_id.isdigit():
            shop_id = int(shop_id)
        # In one shop, cannot have 2 same product barcode for two sale items.
        brs_with_same_upc = Barcode.objects.filter(upc=new_upc)
        for br in brs_with_same_upc:
            pro = Product.objects.get(sale=br.sale)
            if pro.valid_to and pro.valid_to < date.today():
                continue
            # check: 1. the same upc is in global shop when current sale in global shop.
            #        2. the same upc is in same shop.
            br_shops = br.sale.shops.all()
            br_shops_id = [s.id for s in br_shops]
            if not shop_id and len(br_shops_id) == 0:
                raise forms.ValidationError(_("product barcode %s already used in global market." % new_upc))
            elif shop_id and shop_id in br_shops_id:
                raise forms.ValidationError(_("product barcode %s already used in your shop." % new_upc))

