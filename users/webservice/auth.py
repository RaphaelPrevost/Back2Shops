import binascii
import os

import settings
from common.constants import RESP_RESULT
from common.error import DatabaseError
from common.error import ValidationError
from common import db_utils
from common.utils import get_authenticator
from common.utils import gen_cookie_expiry
from common.utils import get_client_ip
from common.utils import get_hashed_headers
from common.utils import gen_json_response
from common.utils import get_preimage
from common.utils import make_auth_cookie
from common.utils import set_cookie
from webservice.base import BaseResource

class UserLoginResource(BaseResource):

    def on_get(self, req, resp, **kwargs):
        return gen_json_response(resp,
                    {'res': RESP_RESULT.F,
                     'err': 'INVALID_REQUEST'})

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            email = req.get_param('email')
            password = req.get_param('password')

            users_id, auth_token = self.verify(conn, email, password)
            self.on_success_login(req, resp, conn, users_id, auth_token)
            return gen_json_response(resp,
                    {"res": RESP_RESULT.S, "err": ""})

        except ValidationError, e:
            return gen_json_response(resp,
                    {'res': RESP_RESULT.F,
                     'err': str(e)})
        except DatabaseError, e:
            return gen_json_response(resp,
                    {"res": RESP_RESULT.F,
                     "err": "ERR_DB",
                     "ERR_SQLDB": str(e)})

    def verify(self, conn, email, raw_password):
        if not email or not raw_password:
            raise ValidationError('ERR_LOGIN')

        result = db_utils.query(conn, "users",
                                columns=("id", "password", "salt",
                                         "hash_iteration_count",
                                         "hash_algorithm"),
                                where={'email': email.lower()},
                                limit=1)
        if not result or len(result) == 0:
            raise ValidationError('ERR_LOGIN')

        users_id, password, salt, hash_iteration_count, hash_algorithm = result[0]
        auth_token = get_preimage(hash_algorithm, hash_iteration_count,
                                  salt, raw_password)
        if password != get_authenticator(hash_algorithm, auth_token):
            raise ValidationError('ERR_LOGIN')
        return users_id, auth_token

    def on_success_login(self, req, resp, conn, users_id, auth_token):
        ip_address = get_client_ip(req)
        headers = get_hashed_headers(req)
        csrf_token = binascii.b2a_hex(os.urandom(16))
        values = {"users_id": users_id,
                  "ip_address": ip_address,
                  "headers": headers,
                  "csrf_token": csrf_token}
        db_utils.insert(conn, "users_logins", values=values)

        # set cookie
        expiry = gen_cookie_expiry(settings.USER_AUTH_COOKIE_EXPIRES)
        auth_cookie = make_auth_cookie(expiry, csrf_token, auth_token, users_id)
        set_cookie(resp, settings.USER_AUTH_COOKIE_NAME, auth_cookie,
                   domain=settings.USER_AUTH_COOKIE_DOMAIN,
                   expiry=expiry, secure=True)

