from common.constants import ADDR_TYPE
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_brief_product_list
from common.utils import get_url_format
from views.base import BaseHtmlResource
from views.user import UserResource
from B2SProtocol.constants import RESP_RESULT
from B2SFrontUtils.constants import REMOTE_API_NAME

def _add_product_list(req, resp, data):
    all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
    data['product_list'] = get_brief_product_list(all_sales)
    return data


class OrderAuthResource(BaseHtmlResource):
    template = "order_auth.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        data = {}
        _add_product_list(req, resp, data)
        return data


class OrderUserResource(UserResource):
    template = "order_user_info.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        data = super(OrderUserResource, self)._on_get(req, resp, **kwargs)
        if data.get('err').startswith('LOGIN_REQUIRED_ERR'):
            self.redirect(get_url_format(FRT_ROUTE_ROLE.ORDER_AUTH))
            return

        _add_product_list(req, resp, data)
        return data

    def _redirect(self, err):
        if err:
            self.redirect("%s?err=%s"
                    % (get_url_format(FRT_ROUTE_ROLE.ORDER_USER), err))
        else:
            self.redirect(get_url_format(FRT_ROUTE_ROLE.ORDER_ADDR))


class OrderAddressResource(BaseHtmlResource):
    template = "order_address.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        remote_resp = data_access(REMOTE_API_NAME.GET_USERINFO,
                                  req, resp)
        if remote_resp.get('res') == RESP_RESULT.F:
            err = remote_resp.get('err') or ''
            if err.startswith('LOGIN_REQUIRED_ERR'):
                self.redirect(get_url_format(FRT_ROUTE_ROLE.ORDER_AUTH))
                return

        shipping_address = None
        billing_address = None
        for addr in remote_resp['address'].values()[1]:
            if addr['addr_type'] == ADDR_TYPE.Billing:
                billing_address = addr
            else:
                shipping_address = addr
        if not billing_address:
            billing_address = shipping_address

        data = {'billing_address': billing_address,
                'shipping_address': shipping_address}
        _add_product_list(req, resp, data)
        return data

