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


import datetime
import logging
import settings
import ujson
import urlparse
import xmltodict

from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View, TemplateResponseMixin
from django.views.generic.edit import CreateView, UpdateView
from fouillis.views import OperatorUpperLoginRequiredMixin

from common.actors.shipping_list import ActorShipments
from common.constants import FAILURE
from common.constants import TARGET_MARKET_TYPES
from common.constants import USERS_ROLE

from common.error import UsersServerError
from common.error import InvalidRequestError
from common.fees import compute_fee
from common.utils import format_epoch_time
from common.utils import get_default_setting
from common.utils import get_valid_sort_fields
from common.utils import Sorter
from common.utils import weight_convert
from common.orders import get_order_detail
from common.orders import get_order_packing_list
from common.orders import remote_delete_order
from common.orders import remote_invoices
from common.orders import remote_send_invoices
from common.orders import get_order_list
from common.orders import send_shipping_fee
from common.orders import send_delete_shipment
from common.orders import send_new_shipment
from common.orders import send_update_shipment
from common.utils import get_merchant_address
from orders.forms import ListOrdersForm
from orders.forms import ShippingForm
from orders.models import Shipping
from shippings.models import Carrier
from shippings.models import Service
from shops.models import Shop
from B2SProtocol.constants import CUSTOM_SHIPPING_CARRIER
from B2SProtocol.constants import FREE_SHIPPING_CARRIER
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM

from B2SUtils.base_actor import actor_to_dict



def is_decimal(val):
    try:
        Decimal(val)
    except ValueError:
        return False
    return True

def get_shop(id_shop):
    if int(id_shop) == 0:
        return
    return Shop.objects.get(pk=id_shop)


class ShippingFee(OperatorUpperLoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        fee = compute_fee(request.GET)
        return HttpResponse(ujson.dumps(fee), mimetype="application/json")

class PackingFeeView(View):
    def get(self, request, *args, **kwargs):
        user_profile = request.user.get_profile()
        id_shop = request.GET.get('id_shop')
        addr_orig = get_merchant_address(user_profile, id_shop)
        addr_dest = request.GET.get('addr_dest')
        addr_dest = urlparse.parse_qs(addr_dest)

        for key, value in addr_dest.iteritems():
            if isinstance(value, list):
                addr_dest[key] = value[0]

        items = request.GET.getlist('item')
        if not isinstance(items, list):
            items = [items]
        sum_weight = 0
        for item in items:
            sail = urlparse.parse_qs(item)
            weight = sail.get('weight')[0]
            weight_unit = sail.get('weight_unit')[0]
            quantity = sail.get('quantity')[0]
            weight = weight_convert(weight_unit, weight)
            sum_weight += weight * int(quantity)

        data = {'addr_orig': {'address': addr_orig.address,
                              'zipcode': addr_orig.zipcode,
                              'city': addr_orig.city,
                              'country_id': addr_orig.country_id,
                              'province_code': addr_orig.province_code
                              },
                'addr_dest': addr_dest,
                'carrier': request.GET.get('shipping_carrier').strip(),
                'service': request.GET.get('shipping_service').strip(),
                'weight': sum_weight,
                }

        fee = compute_fee(data)
        return HttpResponse(ujson.dumps(fee), mimetype="application/json")


class BaseShippingView(OperatorUpperLoginRequiredMixin):
    template_name = "shipping_fee.html"
    form_class = ShippingForm
    model = Shipping

    def get_success_url(self):
        return reverse("shipment_status")

    def get_context_data(self, **kwargs):
        kwargs.update({
            'shipping_pk': self.kwargs.get('pk', None),
            'request': self.request,
            })
        return kwargs

    def _send_shipping_fee(self, request):
        id_shipment = request.POST.get('shipment')
        id_postage = request.POST.get('service')
        shipping_fee = request.POST.get('total_fee')
        try:
            assert is_decimal(id_shipment), 'shipment: %s should be a digit' % id_shipment
            assert is_decimal(id_postage), 'service: %s should be a digit' % id_postage
            assert is_decimal(shipping_fee), 'shipping fee: %s should be a digit' % shipping_fee
        except AssertionError, e:
            logging.error('send_shipping_fee args error: %s' % e,
                          exc_info=True)
            raise
        send_shipping_fee(id_shipment, id_postage, shipping_fee)

    def _compute_total_fee(self, request):
        total_fee = compute_fee(request.POST)
        request.POST.update({'total_fee': total_fee})
        return total_fee


class CreateShippingView(BaseShippingView, CreateView):
    def get_initial(self):
        initial = {"addr_orig": self.request.GET.get('addr_orig', 'orignal'),
                   "addr_dest": self.request.GET.get('addr_dest', 'dest'),
                   "shipment": self.request.GET.get('shipment', 0),
                   }
        return initial


    def post(self, request, *args, **kwargs):
        self._compute_total_fee(request)
        rst = super(CreateShippingView,self).post(request, *args, **kwargs)
        self._send_shipping_fee(request)
        return rst


class EditShippingView(BaseShippingView, UpdateView):
    shipping_id = None

    def get_initial(self):
        if self.shipping_id is None:
            return super(EditShippingView, self).get_initial()
        initial = super(EditShippingView, self).get_initial()
        shp = Shipping.objects.get(pk=self.shipping_id)
        initial['carrier'] = shp.carrier
        initial['service'] = shp.service
        return initial

    def get(self, request, shipping_id):
        self.shipping_id = shipping_id
        self.kwargs.update({'pk': shipping_id})
        return super(EditShippingView,self).get(request)

    def post(self, request, shipping_id):
        self.shipping_id = shipping_id
        self.kwargs.update({'pk': shipping_id})
        self._compute_total_fee(request)
        rst = super(EditShippingView,self).post(request)
        self._send_shipping_fee(request)
        return rst

class ShippingStatusView(OperatorUpperLoginRequiredMixin,
                         View,
                         TemplateResponseMixin):
    template_name = 'shipping_status.html'

    def get_shippings(self):
        self.shippings = Shipping.objects.all()

    def get(self, request, *args, **kwargs):
        self.get_shippings()
        return self.render_to_response(self.__dict__)


def _get_req_user_shops(user):
    # super user could read orders for all shops.
    if user.is_superuser:
        return

    # * brand admin could read orders for
    #   all brand shops and internet sales
    # * store manager could read orders for owned shops.
    #   If the store manager have internet sales priority, could also
    #   read orders for internet sales.
    # * shop operator could only read orders for owned shop.
    #   internet operator could only read orders brand internet sales.
    req_u_profile = user.get_profile()
    if req_u_profile.role == USERS_ROLE.ADMIN:
        shops = Shop.objects.filter(mother_brand=req_u_profile.work_for)
        shops_id = [s.id for s in shops]
        shops_id.append(0)
    elif req_u_profile.role == USERS_ROLE.MANAGER:
        shops_id = [s.id for s in req_u_profile.shops.all()]
        if req_u_profile.allow_internet_operate:
            shops_id.append(0)
    else:
        shops_id = [s.id for s in req_u_profile.shops.all()]
        if len(shops_id) == 0:
            shops_id = [0]

    return shops_id


class ListOrdersView(OperatorUpperLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = 'new_order_list.html'
    list_current = True

    def set_orders_list(self, request, params):
        orders = []
        if request.user.is_superuser:
            brand_id = 0
        else:
            brand_id = request.user.get_profile().work_for.pk

        try:
            shops_id = _get_req_user_shops(self.request.user)
            orders = get_order_list(brand_id, shops_id=shops_id)
        except UsersServerError, e:
            self.error_msg = (
                "Sorry, the system meets some issues, our engineers have been "
                "notified, please check back later.")

        orders_by_status = {
            ORDER_STATUS.PENDING: [],
            ORDER_STATUS.AWAITING_PAYMENT: [],
            ORDER_STATUS.AWAITING_SHIPPING: [],
            ORDER_STATUS.COMPLETED: [],
        }

        status = params.get('status')
        query = None
        if status == "search":
            query = params.get('search')
            orders_by_status['search'] = []

        for order_dict in orders:
            for order_id, order in order_dict.iteritems():
                orders_by_status[order['order_status']].append({order_id: order})
                if query and query.lower() in order['search_options']:
                    orders_by_status['search'].append({order_id: order})

        if status and status.isdigit() and int(status) in orders_by_status:
            status = int(status)
        elif status is None:
            # default status
            for _status, _orders in orders_by_status.iteritems():
                status = _status
                if len(_orders) > 0:
                    break
        elif status != 'search':
            raise
        self.status = status
        self.query = query or ""
        self.orders = orders_by_status[status]
        self.page_title = _("Current Orders")
        self.status_tabs = [
            {'name': _('Pending Orders'),
             'class': 'pending',
             'status': ORDER_STATUS.PENDING},
            {'name': _('Awaiting payment'),
             'class': 'payment',
             'status': ORDER_STATUS.AWAITING_PAYMENT},
            {'name': _('Awaiting Shipping'),
             'class': 'shipping',
             'status': ORDER_STATUS.AWAITING_SHIPPING},
            {'name': _('Completed'),
             'class': 'completed',
             'status': ORDER_STATUS.COMPLETED},
        ]
        if query:
            self.status_tabs.append(
                {'name': query,
                 'class': 'results',
                 'status': 'search'}
            )
        return

    def make_page(self):
        """
        make a pagination
        """
        try:
            self.current_page = int(self.request.GET.get('page', '1'))
            p_size = int(
                self.request.GET.get('page_size',
                                     settings.get_page_size(self.request)))
            p_size = (p_size if p_size in settings.CHOICE_PAGE_SIZE
                      else settings.DEFAULT_PAGE_SIZE)
            self.request.session['page_size'] = p_size
        except:
            self.current_page = 1
        paginator = Paginator(self.orders, settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages
        self.range_start = self.current_page - (
            self.current_page % settings.PAGE_NAV_SIZE)
        self.choice_page_size = settings.CHOICE_PAGE_SIZE
        self.current_page_size = settings.get_page_size(self.request)
        self.prev_10 = (self.current_page-settings.PAGE_NAV_SIZE if
                        self.current_page-settings.PAGE_NAV_SIZE > 1 else
                        1)
        self.next_10 = (self.current_page+settings.PAGE_NAV_SIZE if
                        self.current_page+settings.PAGE_NAV_SIZE <= self.page.paginator.num_pages else
                        self.page.paginator.num_pages)
        self.page_nav = self.page.paginator.page_range[self.range_start:self.range_start+settings.PAGE_NAV_SIZE]

    def get(self, request, orders_type=None):
        self.set_orders_list(request, request.GET)
        self.form = ListOrdersForm(self.status, request.GET)
        if self.form.is_valid():
            order_by1 = self.form.cleaned_data['order_by1']
            order_by2 = self.form.cleaned_data['order_by2']
            self._sort(request, order_by1, order_by2)
        else:
            self._sort(request)
        self.make_page()
        return self.render_to_response(self.__dict__)

    def post(self, request, orders_type=None):
        self.set_orders_list(request, request.POST)
        self.form = ListOrdersForm(self.status, request.POST)
        if self.form.is_valid():
            order_by1 = self.form.cleaned_data['order_by1']
            order_by2 = self.form.cleaned_data['order_by2']
            self._sort(request, order_by1, order_by2)
        self.make_page()
        return self.render_to_response(self.__dict__)

    def _sort(self, request, order_by1=None, order_by2=None):
        sort_fields = get_valid_sort_fields(order_by1, order_by2,
                                   self._get_default_sort_field())
        if not sort_fields: return

        need_shipping_deadline = 'shipping_deadline' in sort_fields \
                               or '-shipping_deadline' in sort_fields
        if need_shipping_deadline:
            for order_dict in self.orders:
                for order_info in order_dict.itervalues():
                    self._set_order_shipping_deadline(request, order_info)

        sorter = Sorter(self.orders)
        sorter.sort(sort_fields,
                    lambda item, field: item.values()[0][field])

    def _get_default_sort_field(self):
        field = None
        if self.status == ORDER_STATUS.PENDING:
            field = 'confirmation_time'
        elif self.status == ORDER_STATUS.AWAITING_PAYMENT:
            field = '-confirmation_time'
        elif self.status == ORDER_STATUS.AWAITING_SHIPPING:
            field = 'shipping_deadline'
        return field

    def _set_order_shipping_deadline(self, request, order_info):
        if not getattr(self, 'cache_shipping_period', None):
            self.cache_shipping_period = {} # shop_id: shipping period days

        order_deadline = None
        for paid_time_dict in order_info.get('paid_time_info'):
            shop_id = paid_time_dict['shop_id']
            paid_time = paid_time_dict.get('timestamp')
            if not paid_time: continue

            if shop_id in self.cache_shipping_period:
                days = self.cache_shipping_period[shop_id]
            else:
                days = get_default_setting('default_shipment_period',
                                           request.user,
                                           get_shop(shop_id))
                self.cache_shipping_period[shop_id] = days

            deadline = paid_time \
                     + datetime.timedelta(days=int(days)).total_seconds()
            if order_deadline is None or deadline < order_deadline:
                order_deadline = deadline

        order_info['shipping_deadline'] = order_deadline

class OrderVenteView(ListOrdersView):
    template_name = 'order_vente.html'

class OrderDetails(OperatorUpperLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_order_details.html"

    def get(self, request, order_id):
        order_details = {}
        if request.user.is_superuser:
            brand_id = 0
        else:
            brand_id = request.user.get_profile().work_for.pk
        self.order_id = order_id
        try:
            shops_id = _get_req_user_shops(self.request.user)
            order_details = get_order_detail(order_id, brand_id, shops_id)
        except UsersServerError, e:
            self.error_msg = (
                "Sorry, the system meets some issues, our engineers have been "
                "notified, please check back later.")
        self.order = order_details
        self.order['confirmation_time'] = format_epoch_time(self.order['confirmation_time'])
        return self.render_to_response(self.__dict__)

class BaseOrderPacking(OperatorUpperLoginRequiredMixin, View):
    template_name = ""


    def _accessable_sale(self, actor_shipment, user, id_shipment=None):
        if id_shipment and int(id_shipment) != int(actor_shipment.id):
            return False

        if user.is_superuser:
            return True
        u_profile = user.get_profile()
        work_for_id = user.get_profile().work_for_id
        if u_profile.role == USERS_ROLE.ADMIN:
            return int(actor_shipment.brand) == work_for_id
        elif u_profile.role == USERS_ROLE.MANAGER:
            manage_shops = u_profile.shops.all()
            if int(actor_shipment.shop) in [s.id for s in manage_shops]:
                return True
            elif (int(actor_shipment.shop) == 0 and
                  u_profile.allow_internet_operate and
                  int(actor_shipment.brand) == work_for_id):
                return True
            else:
                return False
        else:
            manage_shops = u_profile.shops.all()
            if int(actor_shipment.shop) in [s.id for s in manage_shops]:
                return True
            elif (int(actor_shipment.shop) == 0 and
                  len(manage_shops) == 0 and
                  int(actor_shipment.brand) == work_for_id):
                return True
            else:
                return False

    def _populate_shipment(self, spm_actor):
        spm_shop_id = spm_actor.shop
        spm = actor_to_dict(spm_actor)
        if int(spm_shop_id):
            spm['shop_name'] = Shop.objects.get(pk=spm_shop_id).name
            spm['shop_currency'] = Shop.objects.get(pk=spm_shop_id).default_currency
        spm['packing_list'] = [actor_to_dict(item) for item in spm_actor.items]
        sp_carriers = spm_actor.delivery.carriers
        if (len(sp_carriers) > 1 or
            len(sp_carriers) == 1 and len(sp_carriers[0].services) > 1):
            spm['method'] = SCM.MANUAL
        return spm

    def _parse_shipment(self, spms_actor, user, id_shipment=None):
        spms = {'remaining_shipments': [],
                'packing_shipments': []}
        for spm_actor in spms_actor.shipments:
            if not self._accessable_sale(spm_actor, user, id_shipment):
                continue
            spm = self._populate_shipment(spm_actor)

            if int(spm_actor.id) == 0:
                spms['remaining_shipments'].append(spm)
            else:
                spms['packing_shipments'].append(spm)

        return spms

    def _get_deadline(self, request, spms_actor):
        if not getattr(self, 'cache_shipping_period', None):
            self.cache_shipping_period = {} # shop_id: shipping period days
        if not getattr(self, 'cache_payment_period',  None):
            self.cache_payment_period = {} # shop_id: payment period days

        order_status = spms_actor.order_status
        deadline = None
        if int(order_status) in [ORDER_STATUS.PENDING,
                                 ORDER_STATUS.AWAITING_PAYMENT]:
            order_create_date = datetime.datetime.strptime(
                spms_actor.order_create_date, "%Y-%m-%d")
            days = None
            for spm in spms_actor.shipments:
                id_shop = spm.shop
                if id_shop in self.cache_payment_period:
                    period = self.cache_payment_period[id_shop]
                else:
                    period = get_default_setting(
                        'default_shipment_period',
                        request.user,
                        get_shop(id_shop))
                    self.cache_payment_period[id_shop] = period
                # Make the longest payment period as order's payment period.
                if days is None or days < period:
                    days = period
            deadline = order_create_date + datetime.timedelta(days=int(days))
        elif int(order_status) == ORDER_STATUS.AWAITING_SHIPPING:
            for spm in spms_actor.shipments:
                id_shop = spm.shop
                paid_date = datetime.datetime.strptime(
                    spm.paid_date, "%Y-%m-%d")
                if id_shop in self.cache_shipping_period:
                    period = self.cache_shipping_period[id_shop]
                else:
                    period = get_default_setting(
                        'default_shipment_period',
                        request.user,
                        get_shop(id_shop))
                sp_deadline = paid_date + datetime.timedelta(days=int(period))
                if deadline is None or deadline > sp_deadline:
                    deadline = sp_deadline

        if deadline:
            return (deadline.date().strftime("%Y-%m-%d"),
                    (deadline.date() - datetime.datetime.now().date()).days)

    def shop_match_check(self, sale, id_shop):
        if int(id_shop) == 0:
            return sale.type_stock == TARGET_MARKET_TYPES.GLOBAL

        sale_shops = Shop.objects.filter(shopsinsale__sale=sale)
        return int(id_shop) in [s.pk for s in sale_shops]

    def permission_check(self, id_shop, id_brand):
        if self.request.user.is_superuser:
            return False

        req_u_profile = self.request.user.get_profile()

        if req_u_profile.role == USERS_ROLE.ADMIN:
            return req_u_profile.work_for_id == int(id_brand)
        elif req_u_profile.role == USERS_ROLE.MANAGER:
            manage_shops = req_u_profile.shops.all()
            if int(id_shop) in [s.id for s in manage_shops]:
                return True
            elif (int(id_shop) == 0 and
                  req_u_profile.allow_internet_operate and
                  id_brand == req_u_profile.work_for_id):
                return True
            else:
                return False
        else:
            manage_shops = req_u_profile.shops.all()
            if int(id_shop) in [s.id for s in manage_shops]:
                return True
            elif (int(id_shop) == 0 and
                  len(manage_shops) == 0 and
                  id_brand == req_u_profile.work_for_id):
                return True
            else:
                return False

def carrier_service_options():
    carrier_options = []
    service_options = []
    carriers = Carrier.objects.all()
    # carriers option
    for carrier in carriers:
        carrier_options.append(
            {'label': carrier.name,
             'value': carrier.id})

        servs = Service.objects.filter(carrier_id=carrier.id)
        serv_options = [{'label': serv.name,
                         'value': serv.id} for serv in servs]
        service_options.append((carrier.id, serv_options))

    # free shipping option
    carrier_options.append({'label': _("Free Shipping"),
                   'value': FREE_SHIPPING_CARRIER})

    # custom option
    carrier_options.append({'label': _("Others"),
                   'value': CUSTOM_SHIPPING_CARRIER})

    return carrier_options, service_options


class OrderPacking(BaseOrderPacking, TemplateResponseMixin):
    template_name = "_new_order_packing.html"

    def get(self, request, order_id):
        packing = {'order_id': order_id,
                   'shipment_status': [
                       {'label': _("PACKING"),
                        'value': str(SHIPMENT_STATUS.PACKING)},
                       {'label': _("DELIVER"),
                        'value': str(SHIPMENT_STATUS.DELIVER)},
                       {'label': _("DELAYED"),
                        'value': str(SHIPMENT_STATUS.DELAYED)}]
        }
        try:
            id_shipment = request.GET.get('shipment') or None
            xml_packing_list = get_order_packing_list(order_id)
            dict_pl = xmltodict.parse(xml_packing_list)

            spms_actor = ActorShipments(data=dict_pl['shipments'])
            spms = self._parse_shipment(
                spms_actor,
                request.user,
                id_shipment=id_shipment)
            packing['shipments'] = spms
            packing['order_status'] = spms_actor.order_status
            packing['deadline'] = self._get_deadline(request, spms_actor)
            if id_shipment and spms['packing_shipments']:
                self.shipment = spms['packing_shipments'][0]
        except UsersServerError, e:
            self.error_msg = (
                "Sorry, the system meets some issues, our engineers have been "
                "notified, please check back later.")
        self.packing = packing
        self.carrier_options, self.service_options = carrier_service_options()
        return self.render_to_response(self.__dict__)

    def get_template_names(self):
        if self.request.GET.get('shipment'):
            return ["_shipment.html"]
        elif self.request.GET.get('unpacking_reload'):
            return ["_unpacking.html"]
        else:
            return super(OrderPacking, self).get_template_names()

class OrderNewPacking(BaseOrderPacking):
    def post(self, request, *args, **kwargs):
        try:
            rst = self.create_new_packing(request)

        except AssertionError, e:
            logging.error("order_new_packing request error: %s",
                          str(e),
                          exc_info=True)
            rst = {'res': FAILURE,
                   'err': str(e)}
            rst = ujson.dumps(rst)
        except Exception, e:
            logging.error("order_new_packing request error: %s",
                          str(e),
                          exc_info=True)
            rst = {'res': FAILURE,
                   'err': 'SERVER ERROR'}
            rst = ujson.dumps(rst)
        return HttpResponse(rst, mimetype="application/json")

    def param_exist_check(self, param, param_name):
        assert param is not None, 'Miss %s' % param_name


    def create_new_packing(self, request):

        id_order = request.POST.get('id_order')
        id_shop = request.POST.get('id_shop')
        id_brand = request.POST.get('id_brand')

        content = self.packing_items_content(request.POST);

        sp_fee = request.POST.get("shipping_fee")
        hd_fee = request.POST.get("handling_fee")
        shipping_carrier = int(request.POST.get('shipping_carrier'))
        packing_status = int(request.POST.get('packing_status'))
        tracking_name = request.POST.get('tracking_name')
        assert content, "At least one item must be packed"
        self.param_exist_check(sp_fee, 'sp_fee')
        self.param_exist_check(hd_fee, 'hd_fee')
        self.param_exist_check(shipping_carrier, 'shipping_carrier')
        self.param_exist_check(packing_status, 'packing_status')
        self.param_exist_check(tracking_name, 'tracking_name')

        shipping_date = None
        shipping_service = None
        tracking_num = None

        if shipping_carrier not in [FREE_SHIPPING_CARRIER,
                                    CUSTOM_SHIPPING_CARRIER]:
            shipping_service = request.POST.get('shipping_service')
            self.param_exist_check(shipping_service, 'shipping_service')

        if packing_status == SHIPMENT_STATUS.DELIVER:
            tracking_num = request.POST.get('tracking_num')
            self.param_exist_check(tracking_num, 'tracking_num')

        if packing_status != SHIPMENT_STATUS.PACKING:
            shipping_date = request.POST.get("shipping_date")
            self.param_exist_check(shipping_date, 'shipping_date')

        return send_new_shipment(id_order, id_shop, id_brand,
                                 sp_fee, hd_fee, content, shipping_carrier,
                                 packing_status, tracking_name,
                                 shipping_service, shipping_date,
                                 tracking_num)


    def packing_items_content(self, post):
        items_list = post.getlist('content')
        if not isinstance(items_list, list):
            items_list = [items_list]

        content = []
        for item in items_list:
            prod = urlparse.parse_qs(item)
            for key, value in prod.iteritems():
                prod[key] = value[0]
            if prod.get('quantity') is not None:
                content.append(prod)

        return content or None

class OrderUpdatePacking(BaseOrderPacking):
    def post(self, request, *args, **kwargs):
        try:
            rst = self.update_packing(request)
        except AssertionError, e:
            logging.error("order_update_packing request error: %s",
                          str(e),
                          exc_info=True)
            self.error = str(e)
            rst = {'res': FAILURE,
                   'err': str(e)}
            rst = ujson.dumps(rst)
        except Exception, e:
            logging.error("order_update_packing server error: %s",
                          str(e),
                          exc_info=True)
            rst = {'res': FAILURE,
                   'err': _("SERVER ERROR")}
            rst = ujson.dumps(rst)
        return HttpResponse(rst, mimetype="application/json")

    def packing_items_content(self, post):
        '''
        @return: remaining items list in post request.
            [{'id_order_item': xxx,
              'quantity': xxx} ...]
        '''
        items_list = post.get('content')
        if not isinstance(items_list, list):
            items_list = [items_list]

        content = []
        for item in items_list:
            prod = urlparse.parse_qs(item)
            for key, value in prod.iteritems():
                prod[key] = value[0]
            if prod.get('quantity') is not None:
                content.append(prod)

        return content or None

    def update_packing(self, request):
        post = request.POST

        id_shipment = post.get('id_shipment')
        id_shop = post.get('id_shop')
        id_brand = post.get('id_brand')

        if not self.permission_check(id_shop, id_brand):
            raise InvalidRequestError("You have no priority to "
                                      "operate this shipment: %s" % id_shipment)

        sp_fee = post.get("shipping_fee") or None
        hd_fee = post.get("handling_fee") or None
        status = post.get('packing_status') or None
        tracking_num = post.get('tracking_num') or None
        tracking_name = post.get('tracking_name') or None
        shipping_carrier = post.get("shipping_carrier") or None

        content = self.packing_items_content(post)
        sp_date = post.get('shipping_date') or None

        return send_update_shipment(
            id_shipment,
            id_shop,
            id_brand,
            shipping_fee=sp_fee,
            handling_fee=hd_fee,
            status=status,
            tracking_num=tracking_num,
            content=content,
            shipping_date=sp_date,
            tracking_name=tracking_name,
            shipping_carrier=shipping_carrier)


class OrderDeletePacking(BaseOrderPacking):
    def post(self, request, *args, **kwargs):
        try:
            rst = self.delete_packing(request)
        except AssertionError, e:
            logging.error("order_update_packing request error: %s",
                          str(e),
                          exc_info=True)
            self.error = str(e)
            rst = {'res': FAILURE,
                   'err': str(e)}
            rst = ujson.dumps(rst)
        except Exception, e:
            logging.error("order_update_packing server error: %s",
                          str(e),
                          exc_info=True)
            rst = {'res': FAILURE,
                   'err': _("SERVER ERROR")}
            rst = ujson.dumps(rst)
        return HttpResponse(rst, mimetype="application/json")

    def delete_packing(self, request):
        id_shipment = request.POST.get('id_shipment')
        id_shop = request.POST.get('id_shop')
        id_brand = request.POST.get('id_brand')
        assert id_shop is not None, "miss shop info of %s" % id_shipment
        assert id_brand is not None, "miss brand info of %s" % id_shipment

        if not self.permission_check(id_shop, id_brand):
            raise InvalidRequestError("You have no priority to "
                                      "operate shipment: %s" % id_shipment)

        return send_delete_shipment(id_shipment, id_shop, id_brand)


class OrderInvoices(View, TemplateResponseMixin):
    template_name = "_new_order_invoices.html"

    def get(self, request, **kwargs):
        order_id = kwargs.get('order_id')
        shipment = kwargs.get('shipment')
        req_u_profile = request.user.get_profile()
        id_brand = req_u_profile.work_for.id
        shops_id = _get_req_user_shops(request.user)

        resp = remote_invoices(order_id, id_brand, shops_id)
        resp = ujson.loads(resp)


        for invoice in resp['content']:
            if int(invoice['id_shipment']) == int(shipment):
                resp['invoice'] = invoice['html']
                resp['iv_id'] = invoice['id']
                break


        self.obj = resp
        self.order_id = order_id
        return self.render_to_response(self.__dict__)

class SendInvoices(OperatorUpperLoginRequiredMixin, View):
    template_name = ""

    def post(self, request, *args, **kwargs):
        req_u_profile = request.user.get_profile()
        id_order = request.POST.get('id_order')
        id_brand = req_u_profile.work_for.id
        shops_id = _get_req_user_shops(request.user)

        resp = remote_send_invoices(id_order, id_brand, shops_id)
        return HttpResponse(resp, mimetype="application/json")

class OrderDelete(OperatorUpperLoginRequiredMixin, View):
    template_name = ""

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return HttpResponse(ujson.dumps({}),
                                mimetype="application/json")

        req_u_profile = request.user.get_profile()
        if req_u_profile.role == USERS_ROLE.OPERATOR:
            return HttpResponse(ujson.dumps({}),
                                mimetype="application/json")

        id_order = kwargs.get('order_id')
        id_brand = req_u_profile.work_for.id
        shops_id = _get_req_user_shops(request.user)

        resp_dict = {}
        remote_resp = ujson.loads(
                remote_delete_order(id_order, id_brand, shops_id))
        if remote_resp.get('res') != RESP_RESULT.F:
            resp_dict['success'] = 'true'
        return HttpResponse(ujson.dumps(resp_dict),
                            mimetype="application/json")

