import ujson
from common.constants import ADDR_TYPE
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_brief_product_list
from common.utils import get_url_format
from views.base import BaseHtmlResource
from views.basket import get_basket
from views.user import UserResource, UserAuthResource
from B2SProtocol.constants import RESP_RESULT
from B2SFrontUtils.constants import REMOTE_API_NAME

def _add_product_list(req, resp, data):
    all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
    data['product_list'] = get_brief_product_list(all_sales)
    return data


class OrderAuthResource(UserAuthResource):
    template = "order_auth.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        data = super(OrderAuthResource, self)._on_get(req, resp, **kwargs)
        _add_product_list(req, resp, data)
        return data


class OrderUserResource(UserResource):
    template = "order_user_info.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        data = self._get_user_info(req, resp)
        if data.get('err').startswith('LOGIN_REQUIRED_ERR'):
            self.redirect(get_url_format(FRT_ROUTE_ROLE.ORDER_AUTH))
            return

        _add_product_list(req, resp, data)
        data['redirect_to'] = get_url_format(FRT_ROUTE_ROLE.ORDER_ADDR)
        return data


class OrderAddressResource(BaseHtmlResource):
    template = "order_address.html"
    show_products_menu = False

    def _get_user_info(self, req, resp):
        remote_resp = data_access(REMOTE_API_NAME.GET_USERINFO,
                                  req, resp)
        err = ''
        if remote_resp.get('res') == RESP_RESULT.F:
            err = remote_resp.get('err') or ''
            if err.startswith('LOGIN_REQUIRED_ERR'):
                self.redirect(get_url_format(FRT_ROUTE_ROLE.ORDER_AUTH))
                return None, err
        return remote_resp, err

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
        user_info, err = self._get_user_info(req, resp)
        if not user_info: return

        if err:
            shipping_address = billing_address = None
            id_phone = 0
        else:
            shipping_address, billing_address = self._get_addresses(user_info)
            id_phone = user_info['phone']['values'][0]['id']

        data = {'billing_address': billing_address,
                'shipping_address': shipping_address,
                'id_phone': id_phone}
        _add_product_list(req, resp, data)
        return data

    def _on_post(self, req, resp, **kwargs):
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
            'telephone': req.get_param('id_phone') or '0',
            'shipaddr': req.get_param('id_shipaddr') or '0',
            'billaddr': req.get_param('id_billaddr') or '0',
            'wwwOrder': ujson.dumps(orders),
        }
        order_resp = data_access(REMOTE_API_NAME.CREATE_ORDER,
                                 req, resp, **data)
        #TODO redirect to my orders page
        self.redirect(get_url_format(FRT_ROUTE_ROLE.ORDER_ADDR))

