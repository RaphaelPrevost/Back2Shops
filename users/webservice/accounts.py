import binascii
import os
import random

import settings
from common.constants import RESP_RESULT
from common.error import DatabaseError
from common.error import ValidationError
from common import db_utils
from common.utils import get_hexdigest
from common.utils import gen_json_response
from common.utils import is_valid_email
from webservice.base import BaseResource

class UserResource(BaseResource):

    def on_get(self, req, resp, **kwargs):
        return gen_json_response(resp,
                    {'res': RESP_RESULT.F,
                     'err': 'INVALID_REQUEST'})

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            action = self.get_action(req)
            email = self.get_email(req, conn)
            password = self.get_password(req)
            captcha = self.get_captcha(req)

            self.insert(conn, email, password)
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

    def get_action(self, req):
        action = req.get_param('action')
        if action is None or action != 'create':
            raise ValidationError('ERR_ACTION')
        return action

    def get_email(self, req, conn):
        email = req.get_param('email')
        if email is None or not is_valid_email(email):
            raise ValidationError('ERR_EMAIL')

        result = db_utils.query(conn, "users",
                                where={'email': email.lower()},
                                limit=1)
        if result:
            raise ValidationError('EXISTING_EMAIL')
        return email.lower()

    def get_password(self, req):
        password = req.get_param("password")
        if password is None or len(password) < 8:
            raise ValidationError("ERR_PASSWORD")
        return password

    def get_captcha(self, req):
        captcha = req.get_param("captcha")
        if captcha and captcha != settings.USER_CREATION_CAPTCHA:
            raise ValidationError("ERR_CAPTCHA")
        return captcha

    def insert(self, conn, email, raw_password):
        hash_algorithm = settings.DEFAULT_PASSWORD_HASH_ALGORITHM
        hash_iteration_count = random.randint(settings.HASH_MIN_ITERATIONS,
                                              settings.HASH_MAX_ITERATIONS)
        salt = binascii.b2a_hex(os.urandom(64))
        password = get_hexdigest(hash_algorithm, hash_iteration_count,
                                 salt, raw_password)
        values = {"email": email,
                  "password": password,
                  "salt": salt,
                  "hash_algorithm": hash_algorithm,
                  "hash_iteration_count": hash_iteration_count}
        return db_utils.insert(conn, "users", values=values)

