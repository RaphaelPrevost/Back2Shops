import settings
import re

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from B2SUtils.errors import ValidationError
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.m17n import trans_func
from common.utils import get_url_format
from views.base import BaseHtmlResource

email_reexp = r"^([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@([-0-9a-zA-Z]+.)+[a-zA-Z]{2,6}$"
email_pattern = re.compile(email_reexp)
def is_valid_email(email):
    return email and email_pattern.match(email)

class ResetPwdRequestResource(BaseHtmlResource):
    template = "reset_password_request.html"

    def _on_get(self, req, resp, **kwargs):
        return {'msg': ''}

    def _on_post(self, req, resp, **kwargs):
        email = req.get_param('email')
        if not is_valid_email(email):
            raise ValidationError('ERR_EMAIL')

        remote_resp = data_access(REMOTE_API_NAME.SET_USERINFO,
                                  req, resp,
                                  action="passwd",
                                  email=email)
        err = msg = ''
        if remote_resp.get('res') == RESP_RESULT.F:
            err = remote_resp.get('err')
        else:
            msg = trans_func('RESET_PWD_EMAIL_SEND') % {'email': email}
        return {'err': err,
                'msg': msg}

class ResetPwdResource(BaseHtmlResource):
    template = "reset_password.html"

    def _on_get(self, req, resp, **kwargs):
        email = req.get_param('email')
        key = req.get_param('key')
        err = ''
        if not key or not is_valid_email(email):
            err = 'INVALID_REQUEST'
        return {
            'email': email,
            'key': key,
            'err': err,
        }

    def _on_post(self, req, resp, **kwargs):
        email = req.get_param('email')
        key = req.get_param('key')
        password = req.get_param('password')
        password2 = req.get_param('password2')

        err = ''
        if not key or not is_valid_email(email):
            err = 'INVALID_REQUEST'
        elif not password or password != password2:
            err = 'ERR_PASSWORD'

        data = {'email': email, 'key': key}
        if err:
            data['err'] = err
            return data
        else:
            remote_resp = data_access(REMOTE_API_NAME.SET_USERINFO,
                                      req, resp,
                                      action="passwd",
                                      email=email,
                                      key=key,
                                      password=password)
            if remote_resp.get('res') == RESP_RESULT.F:
                data['err'] = remote_resp.get('err')
                return data
            else:
                self.redirect(get_url_format(FRT_ROUTE_ROLE.USER_AUTH))
                return

