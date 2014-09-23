import datetime
import logging
import settings
import ujson
import xmltodict

from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
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
from common.utils import get_default_setting
from common.utils import get_valid_sort_fields
from common.utils import Sorter
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
from orders.forms import ListOrdersForm
from orders.forms import ShippingForm
from orders.models import Shipping
from sales.models import Sale
from shippings.models import Carrier
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
    template_name = 'order_list.html'
    list_current = True

    def _get_order_thumbnail(self, sale_id):
        """
        Using the thumbnail of the first item from the order as the
        order thumbanil image.
        """
        if len(Sale.objects.filter(pk=sale_id)) == 0:
            logging.error("No sale for id : %s", sale_id)
            return ""
        pro_pics = Sale(sale_id).product.pictures.all()
        if len(pro_pics):
            return pro_pics[0].picture
        else:
            return ""


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
        for order_dict in orders:
            for order_id, order in order_dict.iteritems():
                order['thumbnail_img'] = \
                    self._get_order_thumbnail(order['first_sale_id'])
                orders_by_status[order['order_status']].append({order_id: order})

        status = params.get('status')
        if status and status.isdigit() and int(status) in orders_by_status:
            status = int(status)
        else:
            # default status
            for _status, _orders in orders_by_status.iteritems():
                status = _status
                if len(_orders) > 0:
                    break
        self.status = status
        self.orders = orders_by_status[status]
        self.page_title = _("Current Orders")
        self.status_tabs = [
            {'name': _('Pending Orders'),
             'status': ORDER_STATUS.PENDING},
            {'name': _('Awaiting payment'),
             'status': ORDER_STATUS.AWAITING_PAYMENT},
            {'name': _('Awaiting Shipping'),
             'status': ORDER_STATUS.AWAITING_SHIPPING},
            {'name': _('Completed'),
             'status': ORDER_STATUS.COMPLETED},
        ]
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
        packing_list, remaining_list = self._divide_packing_items(spm_actor)
        spm['packing_list'] = packing_list
        spm['remaining_list'] = remaining_list
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

    def _divide_packing_items(self, spm_actor):
        packing_list = []
        remaining_list = []

        for item in spm_actor.items:
            quantity = int(item.quantity)
            packing_quantity = int(item.packing_quantity)
            currency = Sale.objects.get(pk=item.sale).product.currency.code
            item = actor_to_dict(item)
            item['currency'] = currency

            if packing_quantity < quantity:
                remaining_list.append(item)
            if packing_quantity > 0:
                packing_list.append(item)

        return packing_list, remaining_list

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

    def permission_check(self, sale, id_shop):
        if self.request.user.is_superuser:
            return
        req_u_profile = self.request.user.get_profile()

        if req_u_profile.role == USERS_ROLE.ADMIN:
            return req_u_profile.work_for == sale.mother_brand
        elif req_u_profile.role == USERS_ROLE.MANAGER:
            manage_shops = req_u_profile.shops.all()
            if int(id_shop) in [s.id for s in manage_shops]:
                return True
            elif (int(id_shop) == 0 and
                      req_u_profile.allow_internet_operate and
                          sale.mother_brand == req_u_profile.work_for):
                return True
            else:
                return False
        else:
            manage_shops = req_u_profile.shops.all()
            if int(id_shop) in [s.id for s in manage_shops]:
                return True
            elif (int(id_shop) == 0 and
                          len(manage_shops) == 0 and
                          sale.mother_brand == req_u_profile.work_for):
                return True
            else:
                return False

    def remaining_items_content(self, post, id_shop):
        '''
        @param post:
            id_shipment
            shop_for_$id_shipment

            remaining_item_ckb_$id_shipping_list
            remaining_item_choose_$id_shipping_list
            sale_for_$id_shipping_list

            should in post dict
        @return: remaining items list in post request.
            [{'id_order_item': xxx,
              'quantity': xxx} ...]
        '''
        content = []
        ckb_prefix = "remaining_item_ckb_"
        qtt_prefix = "remaining_item_choose_"
        sale_prefix = "sale_for_"
        items = [key for key, _ in post.iteritems()
                 if key.startswith(ckb_prefix)]

        for item in items:
            id_order_item = item[len(ckb_prefix):]

            quantity = post.get(qtt_prefix + id_order_item)
            assert quantity is not None, "miss quantity of %s" % id_order_item
            assert int(quantity) > 0, "quantity %s must be a positive number" % quantity


            id_sale = post.get(sale_prefix + id_order_item)
            assert id_sale is not None, "miss sale info of %s" % id_order_item

            sale = Sale.objects.get(pk=id_sale)
            if not self.shop_match_check(sale, id_shop):
                raise InvalidRequestError("sale %s doesn't in shop %s"
                                          % (id_sale, id_shop))
            if not self.permission_check(sale, id_shop):
                raise InvalidRequestError("You have no priority to "
                                          "operate sale: %s" % id_sale)

            content.append({'id_order_item': id_order_item,
                            'quantity': quantity})
        return content

    def packing_items_content(self, post):
        '''
        @param post:
            id_shipment
            shop_for_$id_shipment

            packing_item_count_for_$id_shipping_list
            packing_item_out_count_for_$id_shipping_list
            packing_item_ckb_$id_shipping_list (optional)
            order_item_for_$id_shipping_list
            sale_for_$id_shipping_list

            should in post param
        @return: list of packing items.
            [{'id_order_item': xxx, 'id_shipping_list_item': xxx,
              'quantity': xxx} ...]
        '''
        id_shipment = post.get('id_shipment')
        orig_item_prefix = "pack_item_count_for_"
        item_prefix = "pack_item_out_count_for_"
        ckb_prefix = "packing_item_ckb_"

        ord_prefix = "order_item_for_"
        sale_prefix = "sale_for_"
        shop_prefix = "shop_for_"

        id_shop = post.get(shop_prefix + id_shipment)
        assert id_shop is not None, "miss shop info of %s" % id_shipment

        items = [key for key, _ in post.iteritems()
                 if key.startswith(item_prefix)]
        content = []
        for item in items:
            id_shipping_list = item[len(item_prefix):]
            orig_qty = post.get(orig_item_prefix + id_shipping_list)
            assert orig_qty is not None, "miss orig quantity of %s" % id_shipping_list

            ckb = post.get(ckb_prefix + id_shipping_list)
            if ckb != "on":
                qty = 0
            else:
                qty = post.get(item)
            assert int(qty) <= orig_qty and int(qty) >= 0, \
                ("invalid qty of item %s: %s, max qty: %s"
                 % (id_shipping_list, qty, orig_qty))

            id_order_item = post.get(ord_prefix + id_shipping_list)
            assert id_order_item is not None, "miss order item of %s" % id_shipping_list

            id_sale = post.get(sale_prefix + id_shipping_list)
            assert id_sale is not None, "miss sale info of %s" % id_shipping_list

            sale = Sale.objects.get(pk=id_sale)
            if not self.shop_match_check(sale, id_shop):
                raise InvalidRequestError("sale %s doesn't in shop %s"
                                          % (id_sale, id_shop))
            if not self.permission_check(sale, id_shop):
                raise InvalidRequestError("You have no priority to "
                                          "operate sale: %s" % id_sale)

            content.append({'id_order_item': id_order_item,
                            'id_shipping_list_item': id_shipping_list,
                            'quantity': qty})
        return content

def carrier_options():
    option = []
    carriers = Carrier.objects.all()
    # carriers option
    for carrier in carriers:
        option.append({'label': carrier.name,
                       'value': carrier.id})

    # free shipping option
    option.append({'label': _("Free Shipping"),
                   'value': FREE_SHIPPING_CARRIER})

    # custom option
    option.append({'label': _("Others"),
                   'value': CUSTOM_SHIPPING_CARRIER})

    return option

class OrderPacking(BaseOrderPacking, TemplateResponseMixin):
    template_name = "_order_packing.html"

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
        self.carrier_options = carrier_options()
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

    def create_new_packing(self, request):
        id_order = request.POST.get('id_order')
        id_shop = request.POST.get('id_shop')
        id_brand = request.POST.get('id_brand')

        content = self.remaining_items_content(request.POST, id_shop)

        sp_fee = request.POST.get("shipping_fee")
        hd_fee = request.POST.get("handling_fee")
        assert sp_fee is not None, "miss shipping fee"
        assert hd_fee is not None, "miss handling fee"
        assert content, "At least one item must be selected"

        return send_new_shipment(id_order, id_shop, id_brand,
                                 sp_fee, hd_fee, content)



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

    def _sale_valid_check(self, id_sale, id_shop):
        sale = Sale.objects.get(pk=id_sale)
        if not self.shop_match_check(sale, id_shop):
            raise InvalidRequestError("sale %s doesn't in shop %s"
                                      % (id_sale, id_shop))
        if not self.permission_check(sale, id_shop):
            raise InvalidRequestError("You have no priority to "
                                      "operate sale: %s" % id_sale)

    def packing_items_content(self, post, id_shop):
        '''
        @param post:
            id_shipment
            shop_for_$id_shipment

            remaining_item_ckb_$id_shipping_list
            remaining_item_choose_$id_shipping_list
            sale_for_$id_shipping_list

            should in post dict
        @return: remaining items list in post request.
            [{'id_order_item': xxx,
              'quantity': xxx} ...]
        '''
        content = {}
        packing_ckb_prefix = "packing_item_ckb_"
        packing_qtt_prefix = "packing_item_out_count_for_"
        remaining_ckb_prefix = "remaining_item_ckb_"
        remaining_qtt_prefix = "remaining_item_choose_"
        total_count_prefix = "total_count_for_"
        sale_prefix = "sale_for_"

        packing_items = [key for key, _ in post.iteritems()
                 if key.startswith(packing_qtt_prefix)]

        remaining_items = [key for key, _ in post.iteritems()
                         if key.startswith(remaining_ckb_prefix)]

        for item in packing_items:
            id_order_item = item[len(packing_qtt_prefix):]

            packing_qtt = post.get(item)
            assert packing_qtt is not None, "quantity must be a positive number"
            assert int(packing_qtt) > 0, "quantity %s must be a positive number" % packing_qtt

            id_sale = post.get(sale_prefix + id_order_item)
            assert id_sale is not None, "miss sale info of %s" % id_order_item
            self._sale_valid_check(id_sale, id_shop)


            packing_ckb = post.get(packing_ckb_prefix + id_order_item)
            remaining_ckb = post.get(remaining_ckb_prefix + id_order_item)
            total_count = post.get(total_count_prefix + id_order_item)

            if packing_ckb and packing_ckb.lower() == 'on':
                quantity = int(packing_qtt)
            elif remaining_ckb and remaining_ckb.lower() == 'on':
                remaining_count = post.get(remaining_qtt_prefix + id_order_item)
                quantity = int(total_count) - int(remaining_count)
            else:
                quantity = 0

            content[id_order_item] = {'id_order_item': id_order_item,
                                      'quantity': quantity}
        for item in remaining_items:
            id_order_item = item[len(remaining_ckb_prefix):]
            if content.get(id_order_item):
                continue

            id_sale = post.get(sale_prefix + id_order_item)
            assert id_sale is not None, "miss sale info of %s" % id_order_item
            self._sale_valid_check(id_sale, id_shop)

            total_count = post.get(total_count_prefix + id_order_item)
            remaining_count = post.get(remaining_qtt_prefix + id_order_item)
            quantity = int(total_count) - int(remaining_count)
            content[id_order_item] = {'id_order_item': id_order_item,
                                      'quantity': quantity}

        return content.values()

    def update_packing(self, request):
        post = request.POST

        id_shipment = post.get('id_shipment')
        id_shop = post.get('shop_for_' + id_shipment)
        content = self.packing_items_content(post, id_shop)

        sp_fee = post.get("shipping_fee") or None
        hd_fee = post.get("handling_fee") or None
        status = post.get('packing_status') or None
        tracking_num = post.get('tracking_num') or None
        tracking_name = post.get('tracking_name') or None
        shipping_carrier = post.get("shipping_carrier") or None

        content = content or None
        sp_date = post.get('shipping_date') or None

        return send_update_shipment(
            id_shipment,
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
        item_prefix = "pack_item_out_count_for_"

        sale_prefix = "sale_for_"
        shop_prefix = "shop_for_"

        id_shop = request.POST.get(shop_prefix + id_shipment)
        assert id_shop is not None, "miss shop info of %s" % id_shipment

        items = [key for key, _ in request.POST.iteritems()
                 if key.startswith(item_prefix)]

        # check merchant have permission to operate this shipment.
        for item in items:
            id_shipping_list = item[len(item_prefix):]

            id_sale = request.POST.get(sale_prefix + id_shipping_list)
            assert id_sale is not None, "miss sale info of %s" % id_shipping_list

            sale = Sale.objects.get(pk=id_sale)
            if not self.shop_match_check(sale, id_shop):
                raise InvalidRequestError("sale %s doesn't in shop %s"
                                          % (id_sale, id_shop))
            if not self.permission_check(sale, id_shop):
                raise InvalidRequestError("You have no priority to "
                                          "operate sale: %s" % id_sale)

        return send_delete_shipment(id_shipment)


class OrderInvoices(View, TemplateResponseMixin):
    template_name = "_order_invoices.html"

    def get(self, request, order_id):
        req_u_profile = request.user.get_profile()
        id_brand = req_u_profile.work_for.id
        shops_id = _get_req_user_shops(request.user)

        resp = remote_invoices(order_id, id_brand, shops_id)
        resp = ujson.loads(resp)

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

