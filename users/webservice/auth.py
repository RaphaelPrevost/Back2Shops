import binascii
import os
from datetime import datetime, timedelta

import settings
from common.constants import RESP_RESULT
from common.utils import encrypt_password
from common.utils import get_authenticator
from common.utils import gen_cookie_expiry
from common.utils import get_client_ip
from common.utils import gen_csrf_token
from common.utils import get_hashed_headers
from common.utils import get_preimage
from common.utils import make_auth_cookie
from common.utils import set_cookie
from webservice.base import BaseJsonResource
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from B2SRespUtils.generate import gen_json_resp

class UserLoginResource(BaseJsonResource):

    def on_get(self, req, resp, **kwargs):
        return gen_json_resp(resp,
                    {'res': RESP_RESULT.F,
                     'err': 'INVALID_REQUEST'})

    def _on_post(self, req, resp, conn, **kwargs):
        email = req.get_param('email')
        password = req.get_param('password')

        users_id, auth_token = self.verify(conn, email, password)
        self.on_success_login(req, resp, conn, users_id, auth_token)
        return {"res": RESP_RESULT.S, "err": ""}

    def verify(self, conn, email, raw_password):
        if not email or not raw_password:
            raise ValidationError('ERR_LOGIN')

        result = db_utils.select(conn, "users",
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

        if (hash_algorithm != settings.DEFAULT_PASSWORD_HASH_ALGORITHM or
            hash_iteration_count < settings.HASH_MIN_ITERATIONS):
            auth_token = self.auth_update(conn, users_id, raw_password)
        return users_id, auth_token

    def on_success_login(self, req, resp, conn, users_id, auth_token):
        ip_address = get_client_ip(req)
        headers = get_hashed_headers(req)
        csrf_token = gen_csrf_token()
        delta = timedelta(seconds=settings.USER_AUTH_COOKIE_EXPIRES)
        utc_expiry = datetime.utcnow() + delta
        values = {"users_id": users_id,
                  "ip_address": ip_address,
                  "headers": headers,
                  "csrf_token": csrf_token,
                  "cookie_expiry": utc_expiry}
        db_utils.update(conn, "users_logins",
                        values={"cookie_expiry": datetime.utcnow()},
                        where={"users_id": users_id,
                               "ip_address": ip_address,
                               "headers": headers,
                               "cookie_expiry__gt": datetime.utcnow()})
        db_utils.insert(conn, "users_logins", values=values)

        # set cookie
        expiry = gen_cookie_expiry(utc_expiry)
        auth_cookie = make_auth_cookie(expiry, csrf_token, auth_token, users_id)
        set_cookie(resp, settings.USER_AUTH_COOKIE_NAME, auth_cookie,
                   domain=settings.USER_AUTH_COOKIE_DOMAIN,
                   expiry=expiry, secure=True)

    def auth_update(self, conn, users_id, raw_password):
        """ Re-calculate user's encrypted password. Update new password,
        salt, hash_algorithm, hash_iteration_count into database.
        """
        auth_token, result = encrypt_password(raw_password)
        db_utils.update(conn, 'users', values=result, where={'id': users_id})
        return auth_token

