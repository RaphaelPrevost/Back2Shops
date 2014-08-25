import settings
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import cur_symbol
from common.utils import format_amount
from common.utils import gen_html_resp
from common.utils import get_order_table_info
from common.utils import get_thumbnail
from common.utils import get_url_format
from views.base import BaseHtmlResource
from B2SFrontUtils.constants import REMOTE_API_NAME

common_email_data = {
    'base_url': settings.FRONT_ROOT_URI,
    'service_email': settings.SERVICE_EMAIL,
    'format_amount': format_amount,
    'cur_symbol': cur_symbol,
    'get_thumbnail': get_thumbnail,
    'set_cookies_js': '',
}

class BaseEmailResource(BaseHtmlResource):
    base_template = None

    def _add_common_data(self, resp_dict):
        resp_dict.update(common_email_data)


class NewUserEmailResource(BaseEmailResource):
    template = 'new_user_email.html'
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, **kwargs):
        name = req.get_param('name')
        if not name:
            remote_resp = data_access(REMOTE_API_NAME.GET_USERINFO,
                                      req, resp)
            if 'general' in remote_resp:
                general_values = remote_resp['general']['values'][0]
                name = general_values.get('first_name')
                if not name:
                    name = general_values.get('email', '').split('@')[0]

        return {'name': name}

class OrderEmailResource(BaseEmailResource):
    template = 'order_email.html'
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, **kwargs):
        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        id_order = kwargs.get('id_order')
        if id_order:
            order_resp = data_access(REMOTE_API_NAME.GET_ORDER_DETAIL, req, resp,
                                     id=id_order, brand_id=settings.BRAND_ID)
            order_data = get_order_table_info(id_order, order_resp, all_sales)
        else:
            order_data = {
                'order_id': 0,
                'order_created': '',
                'status_name': '',
                'user_name': '',
                'dest_addr': '',
                'shipments': {},
                'order_invoice_url': '',
            }
        return order_data

