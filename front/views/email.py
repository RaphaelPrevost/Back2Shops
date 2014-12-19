# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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
import urllib
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

class ResetPwdEmailResource(BaseEmailResource):
    template = 'reset_password_email.html'

    def _on_get(self, req, resp, **kwargs):
        args = urllib.urlencode(req._params)
        return {'user_name': req.get_param('user_name') or '',
                'reset_link': '%s/reset_password?%s'
                              % (settings.FRONT_ROOT_URI, args),
                'reset_link_args': args}

