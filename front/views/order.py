import settings
import gevent
import ujson
import xmltodict

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM
from B2SUtils.base_actor import as_list
from B2SUtils.common import get_cookie_value
from B2SUtils.common import set_cookie
from B2SUtils.errors import ValidationError
from common.constants import CURR_USER_BASKET_COOKIE_NAME
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.email_utils import send_order_email
from common.utils import format_date
from common.utils import get_basket, clear_basket
from common.utils import get_brief_product
from common.utils import get_order_table_info
from common.utils import get_shipping_info
from common.utils import get_url_format
from common.utils import get_user_contact_info
from common.utils import get_valid_attr
from common.utils import valid_int
from common.utils import valid_int_param
from views.base import BaseHtmlResource
from views.base import BaseJsonResource
from views.email import common_email_data
from views.payment import get_payment_url
from views.user import UserResource, UserAuthResource


def _req_invoices(req, resp, id_order):
    return data_access(REMOTE_API_NAME.REQ_INVOICES, req, resp, order=id_order)

def _get_invoices(req, resp, id_order):
    invoices = data_access(REMOTE_API_NAME.GET_INVOICES, req, resp,
                          order=id_order, brand=settings.BRAND_ID)
    id_invoices = _get_invoice_ids(invoices)
    return invoices, id_invoices

def _get_invoice_ids(invoices_resp):
    err = (invoices_resp.get('error') or invoices_resp.get('err')
          ) if isinstance(invoices_resp, dict) else ""
    if err or 'content' not in invoices_resp:
        id_invoices = []
    else:
        invoices = as_list(invoices_resp['content'])
        id_invoices = [long(iv['id']) for iv in invoices_resp['content']]
    return id_invoices


class OrderListResource(BaseHtmlResource):
    template = "order_list.html"
    show_products_menu = False
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, **kwargs):
        page = req.get_param('page') or 0
        if not valid_int(page, False):
            page = 0

        limit = settings.ORDERS_COUNT_PER_PAGE
        orders = data_access(REMOTE_API_NAME.GET_ORDERS, req, resp,
                             brand_id=settings.BRAND_ID,
                             limit=limit,
                             page=page)
        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        order_list = []
        for order in orders:
            for order_id, order_data in order.iteritems():
                order_info = get_order_table_info(order_id, order_data)
                if order_info:
                    order_list.append(order_info)

        prev_page_url = next_page_url = ""
        if int(page) > 0:
            prev_page_url = "%s?page=%s" % (
                get_url_format(FRT_ROUTE_ROLE.ORDER_LIST), int(page) - 1)
        if len(order_list) > limit:
            next_page_url = "%s?page=%s" % (
                get_url_format(FRT_ROUTE_ROLE.ORDER_LIST), int(page) + 1)

        data = {'user_name': order_list[0]['user_name'] if order_list else '',
                'order_list': order_list[:limit],
                'prev_page_url': prev_page_url,
                'next_page_url': next_page_url,
                }
        return data


class OrderInfoResource(BaseHtmlResource):
    template = "order_info.html"
    show_products_menu = False
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, **kwargs):
        id_order = kwargs.get('id_order')
        if not id_order:
            raise ValidationError('ERR_ID')

        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        order_resp = data_access(REMOTE_API_NAME.GET_ORDER_DETAIL, req, resp,
                                 id=id_order, brand_id=settings.BRAND_ID)
        order_data = get_order_table_info(id_order, order_resp)

        invoice_info = {}
        payment_url = ""
        shipping_info = get_shipping_info(req, resp, id_order)
        if not shipping_info['need_select_carrier']:
            invoice_info, id_invoices = _get_invoices(req, resp, id_order)
            if id_invoices and order_data['order_status'] == ORDER_STATUS.AWAITING_PAYMENT:
                payment_url = get_payment_url(id_order, id_invoices)
            else:
                _req_invoices(req, resp, id_order)
                invoice_info, id_invoices = _get_invoices(req, resp, id_order)
                if id_invoices:
                    payment_url = get_payment_url(id_order, id_invoices)

        if shipping_info['need_select_carrier']:
            step = "select"
        elif payment_url:
            step = "payment"
        else:
            step = "view"
        data = {
            'step': step,
            'invoice_info': invoice_info,
            'payment_url': payment_url,
        }
        data.update(order_data)
        data.update(shipping_info)
        return data


class OrderAuthResource(UserAuthResource):
    template = "order_auth.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        data = super(OrderAuthResource, self)._on_get(req, resp, **kwargs)
        data['succ_redirect_to'] = get_url_format(FRT_ROUTE_ROLE.ORDER_ADDR)

        basket_key, basket_data = get_basket(req, resp)
        if basket_key and basket_data \
                and basket_key != get_cookie_value(req, CURR_USER_BASKET_COOKIE_NAME):
            set_cookie(resp, CURR_USER_BASKET_COOKIE_NAME, basket_key)
        return data


class OrderUserResource(UserResource):
    template = "order_user_info.html"
    show_products_menu = False
    login_required = {'get': True, 'post': False}

    def get_auth_url(self):
        return get_url_format(FRT_ROUTE_ROLE.ORDER_AUTH)

    def _on_get(self, req, resp, **kwargs):
        data = super(OrderUserResource, self)._on_get(req, resp, **kwargs)
        data['succ_redirect_to'] = get_url_format(FRT_ROUTE_ROLE.ORDER_ADDR)
        data['id_order'] = req.get_param('id_order') or ''
        return data


class OrderAddressResource(BaseHtmlResource):
    template = "order_address.html"
    show_products_menu = False
    login_required = {'get': True, 'post': False}

    def get_auth_url(self):
        return get_url_format(FRT_ROUTE_ROLE.ORDER_AUTH)

    def _on_get(self, req, resp, **kwargs):
        user_info = data_access(REMOTE_API_NAME.GET_USERINFO,
                                req, resp)
        data = get_user_contact_info(user_info)
        data['id_order'] = req.get_param('id_order') or ''
        return data


class OrderAPIResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, **kwargs):
        if not valid_int_param(req, 'id_phone') \
                or not valid_int_param(req, 'id_shipaddr') \
                or not valid_int_param(req, 'id_billaddr'):
            redirect_to = get_url_format(FRT_ROUTE_ROLE.ORDER_USER)
            return {'redirect_to': redirect_to}

        if req.get_param_as_int('id_order'):
            basket_key = None
            basket_data = None
            data = {
                'action': 'modify',
                'id_order': req.get_param_as_int('id_order'),
                'telephone': req.get_param('id_phone'),
                'shipaddr': req.get_param('id_shipaddr'),
                'billaddr': req.get_param('id_billaddr'),
                }
        else:
            all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
            orders = []
            basket_key, basket_data = get_basket(req, resp)
            for item, quantity in basket_data.iteritems():
                try:
                    item_info = ujson.loads(item)
                except:
                    continue
                id_sale = item_info['id_sale']
                if id_sale not in all_sales:
                    continue

                orders.append({
                    'id_sale': item_info['id_sale'],
                    'id_shop': item_info.get('id_shop'),
                    'quantity': quantity,
                    'id_variant': item_info.get('id_variant') or 0,
                    'id_weight_type': item_info.get('id_attr') or 0,
                    'id_price_type': item_info.get('id_price_type') or 0,
                })
            data = {
                'action': 'create',
                'telephone': req.get_param('id_phone'),
                'shipaddr': req.get_param('id_shipaddr'),
                'billaddr': req.get_param('id_billaddr'),
                'wwwOrder': ujson.dumps(orders),
            }

        order_resp = data_access(REMOTE_API_NAME.CREATE_ORDER,
                                 req, resp, **data)
        if isinstance(order_resp, int) and order_resp > 0:
            if basket_key and basket_data:
                clear_basket(req, resp, basket_key, basket_data)
            id_order = order_resp
            redirect_to = get_url_format(FRT_ROUTE_ROLE.ORDER_INFO) % {
                'id_order': id_order}
            try:
                _req_invoices(req, resp, id_order)
                invoice_info, id_invoices = _get_invoices(req, resp, id_order)
                if settings.BRAND_NAME == "BREUER":
                    redirect_to = get_payment_url(id_order, id_invoices)
            except Exception, e:
                pass
            self._send_email(id_order, req, resp)

        else:
            redirect_to = "%s?err=%s" % (get_url_format(FRT_ROUTE_ROLE.BASKET),
                                         'FAILED_PLACE_ORDER')
        return {'redirect_to': redirect_to}

    def _send_email(self, id_order, req, resp):
        user_resp = data_access(REMOTE_API_NAME.GET_USERINFO, req, resp)
        if 'general' in user_resp:
            general_values = user_resp['general']['values'][0]
            email = general_values.get('email')

            all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
            order_resp = data_access(REMOTE_API_NAME.GET_ORDER_DETAIL, req, resp,
                                     id=id_order, brand_id=settings.BRAND_ID)
            order_data = get_order_table_info(id_order, order_resp, all_sales)
            order_data.update(common_email_data)
            gevent.spawn(send_order_email, email, order_data)


class ShippingAPIResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, **kwargs):
        params_list = []
        for p in req._params:
            if p.startswith("carrier_service_"):
                shipment_id = p.split('_')[-1]
                carrier_id, service_id = req._params[p].split('_')
                params_list.append({
                    'shipment': shipment_id,
                    'carrier': carrier_id,
                    'service': service_id,
                })
        for params in params_list:
            data_access(REMOTE_API_NAME.SET_SHIPPING_CONF,
                        req, resp, **params)
            _req_invoices(req, resp, req.get_param('id_order'))
        return {}

