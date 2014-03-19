import logging
import settings
import ujson
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
from common.orders import get_order_detail
from common.orders import get_order_packing_list
from common.orders import get_order_list
from common.orders import send_shipping_fee
from common.orders import send_delete_shipment
from common.orders import send_new_shipment
from common.orders import send_update_shipment
from orders.forms import ListOrdersForm
from orders.forms import ShippingForm
from orders.models import Shipping
from sales.models import Sale
from shops.models import Shop
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SHIPPING_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM

from B2SUtils.base_actor import actor_to_dict



def is_decimal(val):
    try:
        Decimal(val)
    except ValueError:
        return False
    return True

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


    def set_orders_list(self, request):
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
        for order_dict in orders:
            for order_id, order in order_dict.iteritems():
                order['thumbnail_img'] = \
                    self._get_order_thumbnail(order['first_sale_id'])
        self.orders = orders
        self.page_title = _("Current Orders")
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
        self.set_orders_list(request)
        self.form = ListOrdersForm()
        self.make_page()
        return self.render_to_response(self.__dict__)

    def post(self, request, orders_type=None):
        self.set_orders_list(request)
        self.form = ListOrdersForm(request.POST)
        if self.form.is_valid():
            order_by1 = self.form.cleaned_data['order_by1']
            order_by2 = self.form.cleaned_data['order_by2']
            self._sort_orders(order_by1, order_by2)
        self.make_page()
        return self.render_to_response(self.__dict__)

    def _sort_orders(self, order_by1, order_by2):
        pass


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
        sp_status = actor_shipment.delivery.status
        if int(sp_status) not in [SHIPMENT_STATUS.PACKING,
                             SHIPMENT_STATUS.DELAYED,
                             SHIPMENT_STATUS.DELAYED]:
            return False

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

    def _parse_shipment(self, spms_actor, user, id_shipment=None):
        spms = []
        for spm_actor in spms_actor.shipments:
            if not self._accessable_sale(spm_actor, user, id_shipment):
                continue
            spm = {'id': spm_actor.id,
                   'packing_list': self._get_spm_packing_list(spm_actor),
                   'remaining_list': self._get_spm_remaining_list(spm_actor),
                   'status': spm_actor.delivery.status_desc,
                   'shop': spm_actor.shop,
                   }
            spm.update(actor_to_dict(spm_actor))
            if spm['packing_list'] or spm['remaining_list']:
                spms.append(spm)
        return spms

    def _get_spm_packing_list(self, spm_actor):
        packing_list = []

        auto_shipping_method = [SCM.CARRIER_SHIPPING_RATE,
                                SCM.CUSTOM_SHIPPING_RATE]

        if not spm_actor.method:
            return packing_list

        # packing list condition:
        # * Auto shipping shipment with service selected
        # * Or other shipping method shipment.
        if ((int(spm_actor.method) in auto_shipping_method and
             len(spm_actor.delivery.carriers) == 1 and
             len(spm_actor.delivery.carriers[0].services) == 1) or
            int(spm_actor.method) not in auto_shipping_method):
                for item in spm_actor.items:
                    if (int(item.shipping_status) == SHIPPING_STATUS.PACKING and
                        int(item.quantity) > 0):
                        packing_list.append(actor_to_dict(item))

        return packing_list

    def _get_spm_remaining_list(self, spm_actor):
        remaining_list = []

        for item in spm_actor.items:
            if (int(item.shipping_status) == SHIPPING_STATUS.TO_PACKING and
                int(item.quantity) > 0):
                remaining_list.append(actor_to_dict(item))

        return remaining_list

    def _get_deadline(self, order_id):
        # TODO: implementation
        pass

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


class OrderPacking(BaseOrderPacking, TemplateResponseMixin):
    template_name = "_order_packing.html"

    def get(self, request, order_id):
        packing = {'order_id': order_id,
                   'deadline': self._get_deadline(order_id),
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
            spm_list = self._parse_shipment(
                spms_actor,
                request.user,
                id_shipment=id_shipment)
            packing['shipments'] = spm_list
            if id_shipment and spm_list:
                self.shipment = spm_list[0]
        except UsersServerError, e:
            self.error_msg = (
                "Sorry, the system meets some issues, our engineers have been "
                "notified, please check back later.")
        self.packing = packing
        return self.render_to_response(self.__dict__)

    def get_template_names(self):
        if self.request.GET.get('shipment'):
            return ["_shipment_packing.html"]
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
        id_shipment = request.POST.get('id_shipment')
        content = []
        ckb_prefix = "remaining_item_ckb_"
        qtt_prefix = "remaining_item_choose_"
        sp_fee_prefix = "manual_shipping_fee_for_"
        hd_fee_prefix = "manual_handling_fee_for_"
        ord_prefix = "order_item_for_"
        sale_prefix = "sale_for_"
        shop_prefix = "shop_for_"
        items = [key for key, _ in request.POST.iteritems()
                 if key.startswith(ckb_prefix)]

        id_shop = request.POST.get(shop_prefix + id_shipment)
        assert id_shop is not None, "miss shop info of %s" % id_shipment

        for item in items:
            id_shipping_list = item[len(ckb_prefix):]

            quantity = request.POST.get(qtt_prefix + id_shipping_list)
            assert quantity is not None, "miss quantity of %s" % id_shipping_list
            assert int(quantity) > 0, "quantity %s must be a positive number" % quantity

            id_order_item = request.POST.get(ord_prefix + id_shipping_list)
            assert id_order_item is not None, "miss order item of %s" % id_shipping_list

            id_sale = request.POST.get(sale_prefix + id_shipping_list)
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
                            'quantity': quantity})

        sp_fee = request.POST.get(sp_fee_prefix + id_shipment)
        hd_fee = request.POST.get(hd_fee_prefix + id_shipment)
        assert sp_fee is not None, "miss shipping fee"
        assert hd_fee is not None, "miss handling fee"

        return send_new_shipment(id_order, id_shipment,
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

    def update_packing(self, request):
        id_shipment = request.POST.get('id_shipment')
        sp_fee_prefix = "manual_shipping_fee_for_"
        hd_fee_prefix = "manual_handling_fee_for_"
        tk_num_previx = "tracking_num_for_"
        pk_sts_prefix = "packing_status_for_"
        orig_item_prefix = "pack_item_count_for_"
        item_prefix = "pack_item_out_count_for_"

        ord_prefix = "order_item_for_"
        sale_prefix = "sale_for_"
        shop_prefix = "shop_for_"

        id_shop = request.POST.get(shop_prefix + id_shipment)
        assert id_shop is not None, "miss shop info of %s" % id_shipment

        items = [key for key, _ in request.POST.iteritems()
                 if key.startswith(item_prefix)]
        content = []
        for item in items:
            post = request.POST
            id_shipping_list = item[len(item_prefix):]
            orig_qty = post.get(orig_item_prefix + id_shipping_list)
            assert orig_qty is not None, "miss orig quantity of %s" % id_shipping_list

            qty = post.get(item)
            assert int(qty) <= orig_qty and int(qty) >= 0,\
                ("invalid qty of item %s: %s, max qty: %s"
                 % (id_shipping_list, qty, orig_qty))

            id_order_item = request.POST.get(ord_prefix + id_shipping_list)
            assert id_order_item is not None, "miss order item of %s" % id_shipping_list

            id_sale = request.POST.get(sale_prefix + id_shipping_list)
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

        sp_fee = post.get(sp_fee_prefix + id_shipment) or None
        hd_fee = post.get(hd_fee_prefix + id_shipment) or None
        status = post.get(pk_sts_prefix + id_shipment) or None
        tracking_num = post.get(tk_num_previx + id_shipment) or None
        content = content or None
        sp_date = post.get('shipping_date') or None

        return send_update_shipment(
            id_shipment,
            shipping_fee=sp_fee,
            handling_fee=hd_fee,
            status=status,
            tracking_num=tracking_num,
            content=content,
            shipping_date=sp_date)


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

