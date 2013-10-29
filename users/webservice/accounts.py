import re

import settings
from common.constants import ADDR_TYPE
from common.constants import GENDER
from common.constants import RESP_RESULT
from common import field_utils
from common.utils import cookie_verify
from common.utils import addr_reexp, city_reexp
from common.utils import date_reexp, email_reexp
from common.utils import postal_code_reexp, phone_num_reexp
from common.utils import encrypt_password
from common.utils import gen_json_response
from common.utils import is_valid_email
from webservice.base import BaseResource
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError


class UserResource(BaseResource):
    login_required = {'get': True, 'post': False}
    post_action_func_map = {'create': 'create_account',
                            'modify': 'update_account'}

    def _on_get(self, req, resp, conn, **kwargs):
        users_id = kwargs.get("users_id", None)
        assert users_id is not None
        sql = """select email, locale, title,
                        first_name, last_name, gender, birthday
                 from users
                 left join users_profile
                    on (users.id=users_profile.users_id)
                 where users.id=%s limit 1"""
        users_profile = db_utils.query(conn, sql, (users_id,))[0]
        email = users_profile[0]
        locale = users_profile[1] or 'en-US'
        title = users_profile[2] or ''
        first_name = users_profile[3] or ''
        last_name = users_profile[4] or ''
        gender = users_profile[5] or ''
        birthday = users_profile[6] or ''

        fields_dict = {}
        # email
        fields_dict['email'] = field_utils.TextFieldType("Email",
                    email, email_reexp)

        # locale
        result = db_utils.select(conn, "locale",
                                columns=("name", "name"))
        fields_dict['locale'] = field_utils.SelectFieldType("Locale",
                    locale, dict(result))

        # title
        fields_dict['title'] = field_utils.AjaxFieldType(
                        "Title", title,
                        "/webservice/1.0/pub/JSONAPI?get=titles",
                        depends="locale")

        # firstname and lastname
        fields_dict['first_name'] = field_utils.TextFieldType("First name",
                    first_name, '')
        fields_dict['last_name'] = field_utils.TextFieldType("Last name",
                    last_name, '')

        # gender
        fields_dict['gender'] = field_utils.SelectFieldType("Gender",
                    gender, GENDER.toDict())

        # birthday
        fields_dict['birthday'] = field_utils.TextFieldType("Birthday",
                    birthday and str(birthday.date()) or '', date_reexp)

        # phone number
        columns = ('id', 'country_num', 'phone_num', 'phone_num_desp')
        numbers = db_utils.select(conn,
                "users_phone_num", columns=columns,
                where={'users_id': users_id})
        if len(numbers) == 0:
            numbers = [dict([(c, c == 'id' and '0' or '') for c in columns])]
        else:
            numbers = map(lambda x: {'id': x[0],
                                     'country_num': x[1],
                                     'phone_num': x[2],
                                     'phone_num_desp': x[3]},
                          numbers)
        countries = db_utils.join(conn, ("country_calling_code", "country"),
            on=[('country_calling_code.country_code', 'country.iso')],
            columns=("printable_name", "country_code"))
        fields_dict['phone'] = field_utils.FieldSetType("Phone number",
            {'country_num': field_utils.SelectFieldType(
                            "Calling code", "", dict(countries)),
             'phone_num': field_utils.TextFieldType(
                            "Number", "", phone_num_reexp),
             'phone_num_desp': field_utils.TextFieldType("Description", "", "")
             },
            numbers)

        # address
        columns = ('id', 'addr_type', 'address', 'city', 'postal_code',
                   'country_code', 'province_code', 'address_desp')
        addresses = db_utils.select(conn,
                "users_address", columns=columns,
                where={'users_id': users_id})
        if len(addresses) == 0:
            addresses = [dict([(c, c == 'id' and '0' or '') for c in columns])]
        else:
            addresses = map(lambda x: {'id': x[0],
                                       'addr_type': x[1],
                                       'address': x[2],
                                       'city': x[3],
                                       'postal_code': x[4],
                                       'country_code': x[5],
                                       'province_code': x[6],
                                       'address_desp': x[7]},
                            addresses)
        fields_dict['address'] = field_utils.FieldSetType("Address",
            {'addr_type': field_utils.RadioFieldType(
                        "Address type", "", ADDR_TYPE.toDict()),
             'address': field_utils.TextFieldType(
                        "Address", "", addr_reexp),
             'city': field_utils.TextFieldType(
                        "City", "", city_reexp),
             'postal_code': field_utils.TextFieldType(
                        "Postal code", "", postal_code_reexp),
             'country_code': field_utils.AjaxFieldType(
                        "Country", "",
                        "/webservice/1.0/pub/JSONAPI?get=countries"),
             'province_code': field_utils.AjaxFieldType(
                        "State or Province", "",
                        "/webservice/1.0/pub/JSONAPI?get=provinces",
                        depends="country"),
             'address_desp': field_utils.TextFieldType("Description", "", "")},
            addresses)

        for f in fields_dict:
            fields_dict[f] = fields_dict[f].toDict()
        return gen_json_response(resp, fields_dict)

    def _on_post(self, req, resp, conn, **kwargs):
        action = req.get_param('action')
        if action is None or action not in self.post_action_func_map:
            raise ValidationError('ERR_ACTION')
        func = getattr(self, self.post_action_func_map[action], None)
        assert hasattr(func, '__call__')
        return func(req, resp, conn)

    def update_account(self, req, resp, conn):
        users_id = cookie_verify(conn, req, resp)
        # email
        email = self.get_email(req, conn, users_id)
        db_utils.update(conn, "users", values={'email': email},
                        where={'id': users_id})

        # users_profile columns
        if not req.get_param('last_name'):
            raise ValidationError('INVALID_LAST_NAME')
        if not req.get_param('gender') \
                or req.get_param('gender') not in GENDER.toDict().values():
            raise ValidationError('INVALID_GENDER')
        if not req.get_param('birthday') \
                or not re.match(date_reexp, req.get_param('birthday')):
            raise ValidationError('INVALID_BIRTHDAY')
        values = {
            'users_id': users_id,
            'locale': req.get_param('locale') or '',
            'title': req.get_param('title') or '',
            'first_name': req.get_param('first_name') or '',
            'last_name': req.get_param('last_name') or '',
            'gender': req.get_param('gender') or '',
            'birthday': req.get_param('birthday') or '',
        }
        result = db_utils.update(conn, "users_profile", values=values,
                        where={'users_id': users_id})
        if result == 0:
            db_utils.insert(conn, "users_profile", values=values)

        # users_phone_num columns
        self._update_phone_num(conn, req, users_id)

        # users_address columns
        self._update_address(conn, req, users_id)

        return gen_json_response(resp,
                {"res": RESP_RESULT.S, "err": ""})

    def _update_phone_num(self, conn, req, users_id):
        number_dict = {}
        for p in req._params:
            if p.startswith('country_num_'):
                number_dict[p.replace('country_num_', '')] = {}
        columns = ('country_num', 'phone_num', 'phone_num_desp')
        for num_id in number_dict:
            number_dict[num_id]['users_id'] = users_id
            for c in columns:
                p = req.get_param('%s_%s' % (c, num_id)) or ''
                if c == 'phone_num' and not re.match(phone_num_reexp, p):
                    raise ValidationError('INVALID_PHONE_NUMBER')
                number_dict[num_id][c] = p

            num_referenced = self._is_filed_referenced(
                conn, users_id, 'id_phone', 'users_phone_num', num_id)
            if num_id.isdigit() and int(num_id) == 0 or num_referenced:
                db_utils.insert(conn, "users_phone_num",
                                values=number_dict[num_id])
            else:
                db_utils.update(conn, "users_phone_num",
                                values=number_dict[num_id],
                                where={'id': num_id})

    def _update_address(self, conn, req, users_id):
        addr_dict = {}
        for p in req._params:
            if p.startswith('country_code_'):
                addr_dict[p.replace('country_code_', '')] = {}
        columns = ('addr_type', 'address', 'city', 'postal_code',
                   'country_code', 'province_code', 'address_desp')
        for addr_id in addr_dict:
            addr_dict[addr_id]['users_id'] = users_id
            for c in columns:
                p = req.get_param('%s_%s' % (c, addr_id)) or ''
                if c == 'addr_type' and p.isdigit() \
                        and int(p) not in ADDR_TYPE.toDict().values():
                    raise ValidationError('INVALID_ADDR_TYPE')
                if c == 'address' and not re.match(addr_reexp, p):
                    raise ValidationError('INVALID_ADDRESS')
                if c == 'city' and not re.match(city_reexp, p):
                    raise ValidationError('INVALID_CITY')
                if c == 'postal_code' and not re.match(postal_code_reexp, p):
                    raise ValidationError('INVALID_POSTAL_CODE')
                addr_dict[addr_id][c] = p

            addr_referenced = self._is_filed_referenced(
                conn, users_id, 'id_address', 'users_address', addr_id)
            if addr_id.isdigit() and int(addr_id) == 0 or addr_referenced:
                db_utils.insert(conn, "users_address",
                                values=addr_dict[addr_id])
            else:
                db_utils.update(conn, "users_address",
                                values=addr_dict[addr_id],
                                where={'id': addr_id})

    def _is_filed_referenced(self, conn, users_id, field,
                             field_orig_table, check_id):
        """ Check whether address/phone_num used by user in past and current
        shipments or invoices. And Mark the old address/phone_num as invalid.
        """
        if not check_id.isdigit():
            return False

        assert field in ['id_address', 'id_phone']
        assert field_orig_table in ['users_address', 'users_phone_num']

        shipping_result = db_utils.join(conn,
                                      ('shipments', 'orders'),
                                      columns=(field,),
                                      on=[('shipments.id_order', 'orders.id')],
                                      where={'orders.id_user': users_id})
        billing_result = db_utils.join(conn,
                                     ('invoices', 'orders'),
                                     columns=(field,),
                                     on=[('invoices.id_order', 'orders.id')],
                                     where={'orders.id_user': users_id})

        referenced = ([int(check_id)] in shipping_result or
                      [int(check_id)] in billing_result )

        # mark old address/phone number as invalid.
        if referenced:
            db_utils.update(conn, field_orig_table,
                            values={'valid': False},
                            where={'id': int(check_id)})
        return referenced

    def create_account(self, req, resp, conn):
        email = self.get_email(req, conn)
        password = self.get_password(req)
        captcha = self.get_captcha(req)

        self.insert(conn, email, password)
        return gen_json_response(resp,
                {"res": RESP_RESULT.S, "err": ""})

    def get_email(self, req, conn, users_id=None):
        email = req.get_param('email')
        if email is None or not is_valid_email(email):
            raise ValidationError('ERR_EMAIL')

        result = db_utils.select(conn, "users",
                                columns=("id",),
                                where={'email': email.lower()},
                                limit=1)
        if result and (users_id is None
                    or str(users_id) != str(result[0][0])):
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
        _, result = encrypt_password(raw_password)
        values = {"email": email}
        values.update(result)
        return db_utils.insert(conn, "users", values=values)

