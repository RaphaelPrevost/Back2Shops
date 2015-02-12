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

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View, TemplateResponseMixin
from fouillis.views import OperatorUpperLoginRequiredMixin

from attributes.models import BrandAttribute
from attributes.models import CommonAttribute
from barcodes.models import Barcode
from common.error import UsersServerError
from orders.views import _get_req_user_shops
from sales.models import ExternalRef
from sales.models import Sale
from shops.models import Shop
from sales.models import STOCK_TYPE_GLOBAL
from stocks.models import ProductStock
from stocks.forms import StockForm
from stocks.forms import StockListForm


class ListStocksView(OperatorUpperLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = 'stock_list.html'

    def get(self, request, *args, **kwargs):
        req_params = request.GET
        return self._handle_req(req_params, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        req_params = request.POST
        for f in StockListForm(data=req_params).stocks:
            if f.is_valid():
                self._save_stock(f)
        return self._handle_req(req_params, *args, **kwargs)

    def _save_stock(self, stock_form):
        sale = Sale.objects.get(pk=stock_form.cleaned_data['sale_id'])
        ba_id = stock_form.cleaned_data['ba_id']
        ca_id = stock_form.cleaned_data['ca_id']
        shop_id = stock_form.cleaned_data['shop_id']
        #TODO add alert
        alert = stock_form.cleaned_data['alert']

        stock, created = ProductStock.objects.get_or_create(sale=sale,
            shop=Shop.objects.get(pk=shop_id) if shop_id else None,
            common_attribute=CommonAttribute.objects.get(pk=ca_id) if ca_id else None,
            brand_attribute=BrandAttribute.objects.get(pk=ba_id) if ba_id else None,
            )
        if stock.rest_stock == stock_form.cleaned_data['stock']:
            return
        stock.rest_stock = stock_form.cleaned_data['stock'] or 0
        if stock.stock < stock.rest_stock:
            stock.stock = stock.rest_stock
        stock.save()

        sale_stock_sum = sale.detailed_stock.aggregate(stock_sum=Sum('stock'),
                                                       rest_stock_sum=Sum('rest_stock'))
        sale.total_stock = sale_stock_sum['stock_sum'] or 0
        sale.total_rest_stock = sale_stock_sum['rest_stock_sum'] or 0
        if sale.total_stock < sale.total_rest_stock:
            sale.total_stock = sale.total_rest_stock
        sale.save()

    def _handle_req(self, req_params, *args, **kwargs):
        shops_id = _get_req_user_shops(self.request.user)
        shops_id.reverse()
        shop_id = self.kwargs.get('shop') or shops_id[0]
        shop_id = int(shop_id)
        search = req_params.get('search') or ''

        shop_tabs = []
        for _shop_id in shops_id:
            if _shop_id:
                shop_tabs.append({'name': Shop.objects.get(pk=_shop_id).name,
                                  'shop_id': _shop_id})
            else:
                shop_tabs.append({'name': _("Global"),
                                  'shop_id': 0})

        stocks_list = self.get_stocks_list(shop_id, search)
        paginator, page_obj, object_list, is_paginated = self.make_page(stocks_list)
        data = {
            'shop_tabs': shop_tabs,
            'current_tab': shop_id,
            'search': search,
            'stocks_form': StockListForm(initial=object_list),
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': is_paginated,
        }
        return self.render_to_response(data)

    def _get_sales(self, shop_id, search):
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
        return sales

    def get_stocks_list(self, shop_id, search):
        if shop_id in (0, '0'):
            shop_id = None

        sales = self._get_sales(shop_id, search)
        stocks_list = []
        for sale in sales:
            br_attrs = sale.product.brand_attributes.all()
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
            stock = ProductStock.objects.get(sale=sale, shop_id=shop_id,
                                             brand_attribute=ba,
                                             common_attribute=ca).rest_stock
        except ProductStock.DoesNotExist:
            stock = 0

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
            'alert': False, #TODO get alert status
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

