import ujson
import xmltodict
import settings
from common.constants import ADDR_TYPE
from common.constants import FRT_ROUTE_ROLE
from common.constants import CURR_USER_BASKET_COOKIE_NAME
from common.data_access import data_access
from common.utils import get_brief_product_list
from common.utils import get_url_format
from views.base import BaseHtmlResource
from views.base import BaseJsonResource
from views.basket import get_basket, clear_basket
from views.payment import get_payment_url
from views.user import UserResource, UserAuthResource
from B2SUtils.base_actor import as_list
from B2SUtils.common import get_cookie_value
from B2SUtils.common import set_cookie
from B2SUtils.errors import ValidationError
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM
from B2SFrontUtils.constants import REMOTE_API_NAME

def _add_product_list(req, resp, data):
    all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
    data['product_list'] = get_brief_product_list(all_sales)
    return data

def _order_info(order_id, order_data, all_sales):
    shipments = {}
    for item in order_data['order_items']:
        for item_id, item_data in item.iteritems():
            sale_id = str(item_data['sale_id'])
            if sale_id not in all_sales:
                continue
            sale_info = all_sales[sale_id]
            item_info = {
                'item': item_data,
                'variant': _get_valid_attr(
                            sale_info.get('variant'),
                            item_data.get('id_variant')),
                'weight_type': _get_valid_attr(
                            sale_info.get('type', {}).get('attribute'),
                            item_data.get('id_weight_type')),
                'price_type': _get_valid_attr(
                            sale_info.get('type', {}).get('attribute'),
                            item_data.get('id_price_type')),
            }

            for _shipment_info in item_data['shipment_info']:
                shipment_id = _shipment_info.get('shipment_id')
                if not shipment_id:
                    # sth. wrong when create order
                    continue
                shipping_list = _shipment_info.copy()
                shipping_list['item'] = item_info
                shipping_list['status_name'] = SHIPMENT_STATUS.toReverseDict().get(
                                               int(shipping_list['status']))
                if shipment_id not in shipments:
                    shipments[shipment_id] = []
                shipments[shipment_id].append(shipping_list)

    if not shipments:
        return {}
    else:
        return {
            'order_id': order_id,
            'shipments': shipments,
            'status_name': ORDER_STATUS.toReverseDict().get(
                           int(order_data['order_status'])),
        }

def _get_valid_attr(attrlist, attr_id):
    if not attr_id or not attrlist:
        return {}

    attrlist = as_list(attrlist)
    for attr in attrlist:
        if attr['@id'] == str(attr_id):
            return attr
    return {}

def _req_invoices(req, resp, id_order):
    return data_access(REMOTE_API_NAME.REQ_INVOICES, req, resp, order=id_order)

def _get_invoices(req, resp, id_order):
    invoices = data_access(REMOTE_API_NAME.GET_INVOICES, req, resp,
                          order=id_order, brand=settings.BRAND_ID)
    id_invoices = _get_invoice_ids(invoices)
    return invoices, id_invoices

def _get_invoice_ids(invoices_resp):
    err = (invoices_resp.get('error') or invoices_resp.get('err')) if isinstance(invoices_resp, dict) else ""
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
        orders = data_access(REMOTE_API_NAME.GET_ORDERS, req, resp,
                             brand_id=settings.BRAND_ID)
        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        order_list = []
        for order in orders:
            for order_id, order_data in order.iteritems():
                order_info = _order_info(order_id, order_data, all_sales)
                if order_info:
                    order_list.append(order_info)
        order_list.reverse()
        data = {'order_list': order_list,
                'product_list': get_brief_product_list(all_sales)}
        return data


class OrderInfoResource(BaseHtmlResource):
    template = "order_info.html"
    show_products_menu = False
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, **kwargs):
        id_order = kwargs.get('id_order')
        if not id_order:
            raise ValidationError('ERR_ID')
        xml_resp = data_access(REMOTE_API_NAME.GET_SHIPPING_LIST,
                               req, resp, id_order=id_order)
        shipments = xmltodict.parse(xml_resp)['shipments']
        shipment_list = []
        need_select_carrier = False
        for shipment in as_list(shipments['shipment']):
            method = int(shipment['@method'])
            if method == SCM.CARRIER_SHIPPING_RATE:
                if not shipment['delivery'].get('@postage'):
                    xml_resp = data_access(REMOTE_API_NAME.GET_SHIPPING_FEE,
                                           req, resp, shipment=shipment['@id'])

                    carriers = xmltodict.parse(xml_resp)['carriers']
                    shipment['delivery'].update({'carrier': carriers['carrier']})
                    need_select_carrier = True
            else:
                pass

            shipment['delivery'].update({'carrier':
                                         as_list(shipment['delivery'].get('carrier'))})
            for car in shipment['delivery']['carrier']:
                car['service'] = as_list(car['service'])
            shipment['item'] = as_list(shipment['item'])
            shipment['@method'] = SCM.toReverseDict().get(int(shipment['@method']))
            shipment_list.append(shipment)

        data = {
            'order_id': id_order,
            'status_name': ORDER_STATUS.toReverseDict().get(
                           int(shipments['@order_status'])),
            'created': shipments['@order_create_date'],
            'shipments': shipment_list,
            'need_select_carrier': need_select_carrier,
        }

        invoice_info = {}
        payment_url = ""
        if not need_select_carrier:
            invoice_info, id_invoices = _get_invoices(req, resp, id_order)
            if id_invoices:
                payment_url = get_payment_url(id_order, id_invoices)

        if need_select_carrier:
            step = "select"
        elif payment_url:
            step = "payment"
        else:
            step = "view"
        return {
            'step': step,
            'order_info': data,
            'invoice_info': invoice_info,
            'payment_url': payment_url,
        }


class OrderAuthResource(UserAuthResource):
    template = "order_auth.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        data = super(OrderAuthResource, self)._on_get(req, resp, **kwargs)
        _add_product_list(req, resp, data)
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
        _add_product_list(req, resp, data)
        data['succ_redirect_to'] = get_url_format(FRT_ROUTE_ROLE.ORDER_ADDR)
        return data


class OrderAddressResource(BaseHtmlResource):
    template = "order_address.html"
    show_products_menu = False
    login_required = {'get': True, 'post': True}

    def get_auth_url(self):
        return get_url_format(FRT_ROUTE_ROLE.ORDER_AUTH)

    def _get_addresses(self, user_info):
        shipping_address = None
        billing_address = None
        for addr in user_info['address']['values']:
            if addr['addr_type'] == ADDR_TYPE.Billing:
                billing_address = addr
            else:
                shipping_address = addr
        if not billing_address:
            billing_address = shipping_address
        return shipping_address, billing_address

    def _on_get(self, req, resp, **kwargs):
        user_info = data_access(REMOTE_API_NAME.GET_USERINFO,
                                req, resp)
        try:
            shipping_address, billing_address = self._get_addresses(user_info)
            id_phone = user_info['phone']['values'][0]['id']
        except:
            shipping_address = billing_address = None
            id_phone = 0
        data = {'billing_address': billing_address,
                'shipping_address': shipping_address,
                'id_phone': id_phone}
        _add_product_list(req, resp, data)
        return data


class OrderAPIResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, **kwargs):
        if not self._validateInt(req, 'id_phone') \
                or not self._validateInt(req, 'id_shipaddr') \
                or not self._validateInt(req, 'id_billaddr'):
            self.redirect(get_url_format(FRT_ROUTE_ROLE.ORDER_USER))
            return

        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        orders = []
        basket_key, basket_data = get_basket(req, resp)
        for item, quantity in basket_data.iteritems():
            item_info = ujson.loads(item)
            id_sale = item_info['id_sale']
            if id_sale not in all_sales:
                continue

            sale_info = all_sales[id_sale]
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
        else:
            redirect_to = "%s?err=%s" % (get_url_format(FRT_ROUTE_ROLE.BASKET),
                                         'FAILED_PLACE_ORDER')
        return {'redirect_to': redirect_to}

    def _validateInt(self, req, param_name):
        try:
            assert int(req.get_param(param_name)) > 0
            return True
        except:
            return False


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

