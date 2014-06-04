import binascii
import os
import ujson
from datetime import datetime, timedelta

import settings
from common.redis_utils import get_redis_cli
from common.utils import encrypt_password
from common.utils import get_authenticator
from common.utils import gen_cookie_expiry
from common.utils import get_client_ip
from common.utils import gen_csrf_token
from common.utils import get_hashed_headers
from common.utils import get_preimage
from common.utils import make_auth_cookie
from webservice.base import BaseJsonResource
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import LOGIN_USER_BASKET_KEY
from B2SProtocol.constants import USER_AUTH_COOKIE_NAME
from B2SProtocol.constants import USER_BASKET_COOKIE_NAME
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from B2SUtils.common import set_cookie, get_cookie_value
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
        set_cookie(resp, USER_AUTH_COOKIE_NAME, auth_cookie, expiry=expiry)
        self._set_basket_data(req, resp, users_id)

    def _set_basket_data(self, req, resp, users_id):
        redis_cli = get_redis_cli()
        old_basket_key = redis_cli.get(LOGIN_USER_BASKET_KEY % users_id)
        old_basket_data = redis_cli.get(old_basket_key) if old_basket_key else None
        old_basket_data = ujson.loads(old_basket_data) if old_basket_data else {}

        basket_key = get_cookie_value(req, USER_BASKET_COOKIE_NAME)
        basket_data = redis_cli.get(basket_key) if basket_key else None
        basket_data = ujson.loads(basket_data) if basket_data else {}

        if old_basket_key:
            if basket_key and basket_key != old_basket_key:
                old_basket_data.update(basket_data)
                redis_cli.set(old_basket_key, ujson.dumps(old_basket_data))
                redis_cli.delete(basket_key)
            set_cookie(resp, USER_BASKET_COOKIE_NAME, old_basket_key)
        elif basket_key:
            redis_cli.set(LOGIN_USER_BASKET_KEY % users_id, basket_key)
        else:
            pass

    def auth_update(self, conn, users_id, raw_password):
        """ Re-calculate user's encrypted password. Update new password,
        salt, hash_algorithm, hash_iteration_count into database.
        """
        auth_token, result = encrypt_password(raw_password)
        db_utils.update(conn, 'users', values=result, where={'id': users_id})
        return auth_token

