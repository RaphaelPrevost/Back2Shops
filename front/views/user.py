import settings
import gevent
import urllib

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SFrontUtils.geolocation import get_location_by_ip
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import USER_AUTH_COOKIE_NAME
from B2SUtils.common import set_cookie
from B2SUtils.errors import ValidationError
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.email_utils import send_new_user_email
from common.m17n import gettext as _
from common.utils import allowed_countries
from common.utils import get_client_ip
from common.utils import get_order_table_info
from common.utils import get_url_format
from common.utils import get_user_contact_info
from common.utils import unicode2utf8
from views.base import BaseHtmlResource
from views.base import BaseJsonResource
from views.email import common_email_data


def login(req, resp):
    email = req.get_param('email')
    password = req.get_param('password')
    if not email:
        raise ValidationError('ERR_EMAIL')
    if not password:
        raise ValidationError('ERR_PASSWORD')

    remote_resp = data_access(REMOTE_API_NAME.LOGIN,
                              req, resp,
                              email=email,
                              password=password)
    return remote_resp

def register(req, resp):
    email = req.get_param('email')
    password = req.get_param('password')
    password2 = req.get_param('password2')
    if not email:
        raise ValidationError('ERR_EMAIL')
    if not password or password != password2:
        raise ValidationError('ERR_PASSWORD')

    remote_resp = data_access(REMOTE_API_NAME.REGISTER,
                              req, resp,
                              action="create",
                              email=email,
                              password=password)
    return remote_resp


class UserAuthResource(BaseHtmlResource):
    template = "user_auth.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        return {'succ_redirect_to': get_url_format(FRT_ROUTE_ROLE.MY_ACCOUNT)}


class UserLogoutResource(BaseJsonResource):
    def _on_get(self, req, resp, **kwargs):
        set_cookie(resp, USER_AUTH_COOKIE_NAME, "")
        redirect_to = get_url_format(FRT_ROUTE_ROLE.USER_AUTH)
        if 'referer' in req.headers:
            redirect_to = req.headers['referer']
        self.redirect(redirect_to)
        return


class UserResource(BaseHtmlResource):
    template = "user_info.html"
    show_products_menu = False
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, **kwargs):
        return self._get_user_info(req, resp)

    def _get_user_info(self, req, resp):
        remote_resp = data_access(REMOTE_API_NAME.GET_USERINFO,
                                  req, resp)
        err = req.get_param('err') or ''
        user_profile = {}
        if remote_resp.get('res') == RESP_RESULT.F:
            err = remote_resp.get('err')
            first_time = False
        else:
            user_profile = remote_resp
            first_time = not user_profile['general']['values'][0].get('first_name')

            # translate name
            for fs_name, fs in user_profile.iteritems():
                if 'name' in fs:
                    fs['name'] = _(fs['name'])
                if 'fields' in fs:
                    for f_name, f in fs['fields']:
                        f['name'] = _(f['name'])
                        if f['type'] == 'radio':
                            f['accept'] = [[_(n), v] for n, v in f['accept']]

            # filter country list
            white_countries = allowed_countries()
            if white_countries:
                for f_name, f in user_profile['phone']['fields']:
                    if f_name == 'country_num':
                        f['accept'] = filter(lambda x:x[1]
                                             in white_countries, f['accept'])

            # give geolocation country/province if no address values.
            if not all(int(addr['id']) for addr in user_profile['address']['values']):
                geolocation = get_location_by_ip(get_client_ip(req))

                for address in user_profile['address']['values']:
                    if not int(address['id']):
                        country_code = geolocation['country']['iso_code']
                        province_name = geolocation['subdivision']['name']

                        if country_code and province_name:
                            remote_resp = data_access(REMOTE_API_NAME.AUX,
                                                      req, resp,
                                                      get='province_code',
                                                      ccode=country_code,
                                                      pname=province_name)
                            address['country_code'] = unicode2utf8(country_code)
                            if remote_resp and isinstance(remote_resp, str) \
                                    and RESP_RESULT.F not in remote_resp:
                                address['province_code'] = unicode2utf8(remote_resp)

        return {'user_profile': user_profile,
                'err': err,
                'succ_redirect_to': get_url_format(FRT_ROUTE_ROLE.MY_ACCOUNT),
                'first_time': first_time,
                'id_order': req.get_param('id_order') or ''}


class LoginAPIResource(BaseJsonResource):
    def _on_post(self, req, resp, **kwargs):
        return login(req, resp)

class RegisterAPIResource(BaseJsonResource):
    def _on_post(self, req, resp, **kwargs):
        remote_resp = register(req, resp)
        if remote_resp.get('res') == RESP_RESULT.S:
            login(req, resp)
        return remote_resp


class UserAPIResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, **kwargs):
        # combine birthday fields
        if req.get_param('birthday0'):
            req._params['birthday'] = '%s-%02d-%02d' % (
                req.get_param('birthday0'), int(req.get_param('birthday1') or 1),
                int(req.get_param('birthday2') or 1))

        # check country
        white_countries = allowed_countries()
        if white_countries:
            for p in req._params:
                if p.startswith('country_code_') \
                        or p.startswith('country_num_'):
                    if req.get_param(p) not in white_countries:
                        raise ValidationError('ERR_EU_COUNTRY')

        remote_resp = data_access(REMOTE_API_NAME.SET_USERINFO,
                                  req, resp,
                                  action="modify",
                                  **req._params)
        resp_dict = {}
        resp_dict.update(remote_resp)

        if resp_dict.get('res') == RESP_RESULT.F:
            resp_dict['err'] = _(resp_dict['err'])
        else:
            if req.get_param('first_time') == 'True':
                # send email
                email_data = {'name': req.get_param('first_name')}
                email_data.update(common_email_data)
                gevent.spawn(send_new_user_email, req.get_param('email'), email_data)

        return resp_dict


class MyAccountResource(BaseHtmlResource):
    template = "my_account.html"
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, **kwargs):
        user_info = data_access(REMOTE_API_NAME.GET_USERINFO, req, resp)
        general_user_values = user_info['general']['values'][0]
        if not general_user_values.get('first_name') \
                or not general_user_values.get('last_name'):
            user_name = general_user_values['email']
        else:
            user_name = '%s %s %s' % (
                    general_user_values.get('title') or '',
                    general_user_values.get('first_name') or '',
                    general_user_values.get('last_name') or '',
                    )

        limit = settings.ORDERS_COUNT_IN_MY_ACCOUNT
        orders = data_access(REMOTE_API_NAME.GET_ORDERS, req, resp,
                             brand_id=settings.BRAND_ID,
                             limit=limit)
        order_list = []
        for order in orders:
            for order_id, order_data in order.iteritems():
                order_info = get_order_table_info(order_id, order_data)
                if order_info:
                    order_list.append(order_info)

        data = {'user_name': user_name,
                'user_info': general_user_values,
                'order_list': order_list[:limit]}
        data.update(get_user_contact_info(user_info))
        return data

