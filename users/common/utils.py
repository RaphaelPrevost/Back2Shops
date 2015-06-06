# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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
import logging
import binascii
import datetime
import hashlib
import hmac
import os
import random
import re
import string
import ujson
import urllib
import urllib2
import xmltodict
from lxml import etree


from common.constants import HASH_ALGORITHM
from common.constants import HASH_ALGORITHM_NAME
from common.error import ServerError
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import EXPIRY_FORMAT
from B2SUtils.common import set_cookie, get_cookie
from B2SUtils.errors import ValidationError
from B2SUtils import db_utils
from B2SProtocol.constants import PAYMENT_TYPES
from B2SProtocol.constants import USER_AUTH_COOKIE_NAME
from B2SRespUtils.generate import _temp_content as render_content
from models.actors.events import ActorEvents

phone_num_reexp = r'^[0-9]+$'
postal_code_reexp = r'^.+$'
addr_reexp = r'^.+$'
city_reexp = r'^.+$'
# yyyy-mm-dd
date_reexp = r"^(([0-9]{3}[1-9]|[0-9]{2}[1-9][0-9]{1}|[0-9]{1}[1-9][0-9]{2}|[1-9][0-9]{3})-(((0[13578]|1[02])-(0[1-9]|[12][0-9]|3[01]))|((0[469]|11)-(0[1-9]|[12][0-9]|30))|(02-(0[1-9]|[1][0-9]|2[0-8]))))|((([0-9]{2})(0[48]|[2468][048]|[13579][26])|((0[48]|[2468][048]|[3579][26])00))-02-29)$"

email_reexp = r"^([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@([-0-9a-zA-Z]+.)+[a-zA-Z]{2,6}$"
email_pattern = re.compile(email_reexp)

def is_valid_email(email):
    return email and email_pattern.match(email)

def generate_random_str(length=10):
    population = string.ascii_letters + string.digits
    times = length / len(population) + 1
    return ''.join(random.sample(population * times, length))

def generate_random_digits_str(length=10, none_zero_start=True):
    if none_zero_start:
        l = length - 1
    population = string.digits
    times = length / len(population) + 1
    r = ''.join(random.sample(population * times, length))
    if none_zero_start:
        r = random.sample(population[1:], 1)[0] + r
    return r

def hashfn(algorithm, text):
    # Retrieves the appropriate hash function
    if algorithm not in HASH_ALGORITHM_NAME:
        raise ValueError("Unknown algorithm.")
    if text == "":
        raise ValueError("Missing text.")
    h = hashlib.new(HASH_ALGORITHM_NAME[algorithm])
    # XXX repeated calls to update() simply concatenate text!
    h.update(text)
    return h.hexdigest()

def get_preimage(algorithm, iterations, salt, password):
    # Computes the pre-image of the authenticator token.
    # This pre-image is used in the user session cookie.
    if iterations <= 0:
        raise ValueError("Bad iterations count.")
    if salt == "" or password == "":
        raise ValueError("Empty salt or password.")
    while iterations > 0:
        salt = result = hashfn(algorithm, salt + password)
        iterations -= 1
    return result

def get_authenticator(algorithm, preimage):
    # Computes the authenticator from a pre-image.
    # This can be used to check the user's cookie.
    return hashfn(algorithm, preimage)

def get_hexdigest(algorithm, iterations, salt, password):
    # This function computes the authenticator.
    # This authenticator is stored in database.
    preimage = get_preimage(algorithm, iterations, salt, password)
    return get_authenticator(algorithm, preimage)

def get_hmac(secret_key, text, algorithm=hashlib.sha256):
    return hmac.new(secret_key, text, algorithm).hexdigest()

def gen_cookie_expiry(utc_expiry):
    return utc_expiry.strftime(EXPIRY_FORMAT)

def make_auth_cookie(expiry, csrf_token, auth_token, users_id):
    secret_key = hmac_secret_key()
    digest = get_hmac(secret_key,
                 ";".join([expiry, csrf_token, auth_token]))
    data = {'exp': expiry,
            'csrf': csrf_token,
            'auth': auth_token,
            'digest': digest,
            'users_id': users_id}
    return '&'.join(['%s=%s' % (k, v) for k, v in data.iteritems()])

def get_hashed_headers(req):
    ## chrome supports "sdch" and will add it to accept-encoding when needed
    accept_encoding = req.get_header('Accept-Encoding') or ''
    accept_encoding = ','.join([one for one in accept_encoding.split(',')
                                    if one.strip() != 'sdch'])

    headers = ";".join([
            #req.get_header('Accept') or '',
            req.get_header('Accept-Language') or '',
            accept_encoding,
            req.get_header('Accept-Charset') or '',
            req.get_header('User-Agent') or '',
            req.get_header('DNT') or ''])

    return hashfn(HASH_ALGORITHM.SHA256, headers)

def gen_json_response(resp, data):
    resp.content_type = "application/json"
    resp.body = ujson.dumps(data)
    return resp

def hmac_secret_key():
    path = settings.HMAC_KEY_FILE_PATH
    with open(path, 'r') as f:
        secret_key = f.read()
        f.close()
        return secret_key

def _hmac_verify(user_auth):
    """ MAC verification.
    """
    secret_key = hmac_secret_key()
    text = ";".join([user_auth['exp'], user_auth['csrf'], user_auth['auth']])
    expected_digest = get_hmac(secret_key, text)
    if user_auth['digest'] != expected_digest:
        raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_HMAC')

def _user_verify(conn, users_id, user_auth, ip, headers):
    """ Verify user information for the request.

    conn: database connection.
    users_id: user's id.
    user_auth: pre-image for user's password.
    ip: IP address for the request.
    headers: request header information.
    """

    # XXX enforce expiry time
    expiry = datetime.datetime.strptime(user_auth['exp'], EXPIRY_FORMAT)
    if expiry < datetime.datetime.utcnow():
        raise ValidationError('LOGIN_REQUIRED_ERR_EXPIRED_AUTH')

    columns = ('password', 'hash_algorithm',
               'csrf_token', 'users_logins.id')
    where = {'users.id': users_id,
             'users_logins.headers': headers,
             'users_logins.ip_address': ip,
             'users_logins.cookie_expiry__gt': datetime.datetime.utcnow()}
    result = db_utils.join(conn, ('users', 'users_logins'),
                            columns=columns,
                            on=[('users.id', 'users_logins.users_id')],
                            where=where,
                            limit=1)
    if not result or len(result) == 0:
        raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_USER')

    exp_auth, hash_algo, exp_csrf, login_id = result[0]
    try:
        # XXX use the hash algorithm specified in the user account
        cur_auth = get_authenticator(hash_algo, user_auth['auth'])
        if cur_auth != exp_auth:
            raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_AUTH')

        # XXX always verify the CSRF token
        if user_auth['csrf'] != exp_csrf:
            logging.error("Invalid csrf: cur: %s, exp: %s"
                          % (user_auth['csrf'], exp_csrf))
            raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_CSRF')
    except ValidationError, e:
        # XXX delete the compromised session and propagate the exception
        # TODO: Maybe log the attacker informations somewhere?
        # That would be useful to display some Gmail-like warnings:
        # Somebody from <somewhere> tried to access your account on <datetime>
        logging.error('Delete compromised session for id %s '
                      'with error:%s' % (login_id, str(e)))

        db_utils.delete(conn, 'users_logins', where={'id': login_id})
        raise e

    return login_id

def _parse_auth_cookie(auth_cookie):
    """ Parse auth information string, return dict object.

    auth_cookie: string, generated by make_auth_cookie.
    """
    auth_fields = auth_cookie.split('&')
    fields_list = [tuple(field.split('=')) for field in auth_fields if field]
    return dict(fields_list)

def gen_csrf_token():
    return binascii.b2a_hex(os.urandom(16))

def cookie_verify(conn, req, resp):
    """ Verify cookie to check if user is in login status, update csrf
    token if pass cookie verification.
    Checked:
      * MAC
      * Auth, IP, request headers, csrf(for post request)

    conn: database connection.
    req: request.
    resp: response will send to client.
    """
    cookie = get_cookie(req)
    if not cookie:
        raise ValidationError('LOGIN_REQUIRED_ERR_UNSET_COOKIE')

    # 'USER_AUTH' should be in the cookie.
    required_fields = [USER_AUTH_COOKIE_NAME]
    for field in required_fields:
        if not cookie.has_key(field):
            raise ValidationError('LOGIN_REQUIRED_ERR_EMPTY_COOKIE')

    # authenticated information should be contained in 'USER_AUTH'
    auth_fields = ['exp', 'csrf', 'auth', 'digest', 'users_id']
    user_auth = cookie.get(USER_AUTH_COOKIE_NAME).value
    user_auth = _parse_auth_cookie(user_auth)
    for field in auth_fields:
        if not user_auth.has_key(field):
            raise ValidationError('LOGIN_REQUIRED_ERR_MISSING_DATA: %s' % field)

    # check if the cookie has been tampered with before going any further
    _hmac_verify(user_auth)

    users_id = user_auth['users_id']
    ip = get_client_ip(req)
    headers = get_hashed_headers(req)

    login_id = _user_verify(conn, users_id, user_auth, ip, headers)

    if req.method == 'POST':
        # set new csrf to cookie and database.
        csrf_token = gen_csrf_token()
        auth_cookie = make_auth_cookie(user_auth['exp'],
                                       csrf_token,
                                       user_auth['auth'],
                                       users_id)
        db_utils.update(conn,
                        'users_logins',
                        values={'csrf_token': csrf_token},
                        where={'id': login_id})
        conn.commit()
        set_cookie(resp, USER_AUTH_COOKIE_NAME, auth_cookie, expiry=user_auth['exp'])
    return users_id

def encrypt_password(raw_password):
    hash_algorithm = settings.DEFAULT_PASSWORD_HASH_ALGORITHM
    hash_iteration_count = random.randint(settings.HASH_MIN_ITERATIONS,
                                          settings.HASH_MAX_ITERATIONS)
    salt = binascii.b2a_hex(os.urandom(64))
    auth_token = get_preimage(hash_algorithm, hash_iteration_count,
                              salt, raw_password)
    password = get_authenticator(hash_algorithm, auth_token)

    values = {"password": password,
              "salt": salt,
              "hash_algorithm": hash_algorithm,
              "hash_iteration_count": hash_iteration_count}
    return auth_token, values


def get_api_key(email, salt, hash_iteration_count,
                algorithm=settings.DEFAULT_API_KEY_HASH_ALGORITHM):
    return get_hexdigest(algorithm, hash_iteration_count, salt, email)

def api_key_verify(conn, email, api_key):
    result = db_utils.select(conn, "users",
                             columns=("id", "salt", "hash_iteration_count"),
                             where={'email': email.lower()},
                             limit=1)
    if len(result) == 0:
        raise ValidationError('ERR_EMAIL')

    users_id, salt, hash_count = result[0]
    if api_key != get_api_key(email, salt, hash_count):
        raise ValidationError('ERR_API_KEY')
    return users_id


def remote_xml_shipping_fee(carrier_services, weight, unit, dest,
                            id_address, amount=None):
    uri = 'protected/shipping/fees'
    if isinstance(carrier_services, list):
        carrier_services = ujson.dumps(carrier_services)
    if isinstance(dest, dict):
        dest = ujson.dumps(dest)

    query = {'carrier_services': carrier_services,
             'weight': weight,
             'unit': unit,
             'dest': dest,
             'id_address': id_address}
    if amount:
        query['amount'] = amount
    content = get_from_sale_server(uri, **query)
    return content

def remote_xml_shipping_services(carrier_services=None, id_sale=None):
    uri = 'private/shipping/services/info'
    if isinstance(carrier_services, list):
        carrier_services = ujson.dumps(carrier_services)
        query = {'carrier_services': carrier_services}
    else:
        query = {'id_sale': id_sale}
    content = get_from_sale_server(uri, **query)
    return content

def remote_xml_invoice(query):
    uri = 'private/invoice/get'
    content = get_from_sale_server(uri, **query)
    return content

def remote_increase_stock(params):
    uri = 'protected/stock/inc'
    content = post_to_sale_server(uri, ujson.dumps(params))
    return ujson.loads(content)

def remote_decrease_stock(params):
    uri = 'protected/stock/dec'
    content = post_to_sale_server(uri, ujson.dumps(params))
    return ujson.loads(content)

def remote_xml_eventlist():
    uri = 'private/event/list'
    content = get_from_sale_server(uri)
    return content

def get_event_configs(event_name):
    xml_eventlist = remote_xml_eventlist()
    eventlist = xmltodict.parse(xml_eventlist)
    actor_events = ActorEvents(data=eventlist['events'])
    for actor_event in actor_events.events:
        if actor_event.name == event_name:
            return actor_event
    raise ValidationError('EVENT_NOT_FOUND')

def push_event(uri, **query):
    if query:
        data = urllib.urlencode(query)
    else:
        data = None

    return post_to_sale_server(uri, data)

def get_from_sale_server(uri, **query):
    if not uri.startswith(settings.SALES_SERVER_API_URL):
        remote_uri = settings.SALES_SERVER_API_URL % {'api': uri}
    else:
        remote_uri = uri
    if query:
        query_str = urllib.urlencode(query)
    else:
        query_str = ''

    try:
        content = get_from_remote('?'.join([remote_uri, query_str]),
                                  settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                  settings.PRIVATE_KEY_PATH)
    except Exception, e:
        logging.error('get_from_sale_server_error: %s', e, exc_info=True)
        raise
    return content

def post_to_sale_server(uri, data=None):
    if not uri.startswith(settings.SALES_SERVER_API_URL):
        remote_uri = settings.SALES_SERVER_API_URL % {'api': uri}
    else:
        remote_uri = uri

    try:
        encrypt = re.search('/(private|protected)/', remote_uri)
        if encrypt and data:
            data = gen_encrypt_json_context(data,
                    settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                    settings.PRIVATE_KEY_PATH)

        req = urllib2.Request(remote_uri, data=data)
        remote_resp = urllib2.urlopen(req)

        if encrypt:
            content = decrypt_json_resp(remote_resp,
                    settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                    settings.PRIVATE_KEY_PATH)
        else:
            content = remote_resp.read()
        return content

    except Exception, e:
        logging.error('post_to_sale_server_error: %s', e, exc_info=True)
        raise



OZ_GRAM_CONVERSION = 28.3495231
LB_GRAM_CONVERSION = 453.59237
GRAM_KILOGRAM_CONVERSION = 0.001

def oz_to_gram(weight):
    return weight * OZ_GRAM_CONVERSION

def gram_to_kilogram(weight):
    return weight * GRAM_KILOGRAM_CONVERSION

def lb_to_gram(weight):
    return weight * LB_GRAM_CONVERSION

def weight_convert(from_unit, weight):
    weight = float(weight)
    if from_unit == 'kg':
        return weight
    elif from_unit == 'g':
        return gram_to_kilogram(weight)
    elif from_unit == 'oz':
        weight_in_gram = oz_to_gram(weight)
        return gram_to_kilogram(weight_in_gram)
    elif from_unit == 'lb':
        weight_in_gram = oz_to_gram(weight)
        return gram_to_kilogram(weight_in_gram)

def remote_payment_init(id_order, id_user, amount, currency, iv_id,
                        iv_numbers, iv_data):
    uri = 'private/payment/init'
    remote_uri = settings.SALES_SERVER_API_URL % {'api': uri}
    if isinstance(iv_id, list):
        iv_id = ujson.dumps(iv_id)

    if isinstance(iv_numbers, list):
        iv_numbers = ujson.dumps(iv_numbers)

    query = {"order": id_order,
             "user": id_user,
             "amount": amount,
             "currency": currency,
             "invoices": iv_id,
             "invoices_num": iv_numbers,
             "invoicesData": iv_data}

    logging.info("remote_payment_init_query: %s", query)
    try:
        query = ujson.dumps(query)
        en_query = gen_encrypt_json_context(
            query,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
            settings.PRIVATE_KEY_PATH)

        resp = get_from_remote(
            remote_uri,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
            settings.PRIVATE_KEY_PATH,
            data=en_query,
            headers={'Content-Type': 'application/json'})
        logging.info("payment_init_response: %s", resp)
        return resp
    except Exception, e:
        logging.error('Failed to get payment init %s,'
                      'error: %s',
                      query, e, exc_info=True)
        raise ServerError('remote_payment_init_err: %s' % str(e))


def remote_payment_form(cookie, id_processor, id_trans, **kwargs):
    uri = "webservice/1.0/private/payment/form"
    query = {'cookie': cookie, 'processor': id_processor, }
    param = {'id_trans': id_trans}

    id_processor = int(id_processor)
    if id_processor == PAYMENT_TYPES.PAYPAL:
        query.update({
            'url_notify': settings.PAYMENT_PAYPAL_GATEWAY % param,
            'url_return': settings.PAYMENT_PAYPAL_RETURN % param,
            'url_cancel': settings.PAYMENT_PAYPAL_CANCEL % param,

        })

    elif id_processor == PAYMENT_TYPES.PAYBOX:
        query.update({
            'url_success': settings.PAYMENT_PAYBOX_SUCCESS % param,
            'url_failure': settings.PAYMENT_PAYBOX_FAILURE % param,
            'url_cancel': settings.PAYMENT_PAYBOX_CANCEL % param,
            'url_waiting': settings.PAYMENT_PAYBOX_WAITING % param,
            'url_return': settings.PAYMENT_PAYBOX_GATEWAY % param,
            'user_email': kwargs.get('user_email', ''),
        })

    elif id_processor == PAYMENT_TYPES.STRIPE:
        query.update({
            'user_email': kwargs.get('user_email', ''),
            'url_process': settings.PAYMENT_STRIPE_PROCESS % param,
            'url_success': kwargs.get('url_success', ''),
            'url_failure': kwargs.get('url_failure', ''),
        })

    try:
        query = ujson.dumps(query)
        en_query = gen_encrypt_json_context(
            query,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.FIN],
            settings.PRIVATE_KEY_PATH)

        resp = get_from_remote(
            os.path.join(settings.FIN_ROOT_URI, uri),
            settings.SERVER_APIKEY_URI_MAP[SERVICES.FIN],
            settings.PRIVATE_KEY_PATH,
            data=en_query,
            headers={'Content-Type': 'application/json'})
        return resp

    except Exception, e:
        logging.error('Failed to get payment form %s,'
                      'error: %s',
                      query, e, exc_info=True)
        raise ServerError('remote_payment_form_err: %s' % str(e))

def currency_exchange(from_, to, amount):
    if from_ not in settings.CURRENCY_EX_RATE:
        logging.error("currency_exchange_err: not supported currency "
                      "%s", from_, exc_info=True)
        raise ServerError('currency_exchange_err')

    if to not in settings.CURRENCY_EX_RATE[from_]:
        logging.error("currency_exchange_err: not supported currency "
                      "%s", to, exc_info=True)
        raise ServerError('currency_exchange_err')

    return float(amount) * settings.CURRENCY_EX_RATE[from_][to]

def get_client_ip(request):
    env = request.env
    try:
        return env['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
    except KeyError:
        return env['REMOTE_ADDR']

def _parse_accept_language(accept_language):
    # accept_languages like 'zh-cn,zh;q=0.8,en;q=0.5,en-us;q=0.3'
    languages = accept_language.split(",")
    locale_q_pairs = []

    for language in languages:
        lang = language.split(";")
        if lang[0] == language:
            # no q => q = 1
            locale_q_pairs.append((language.strip(), "1"))
        else:
            locale_q_pairs.append((lang[0].strip(), lang[1].split("=")[1]))
    return locale_q_pairs

def detect_locale(accept_language):
    locale_q_pairs = _parse_accept_language(accept_language)
    for locale, q in locale_q_pairs:
        locale = locale.split('-')[0].lower()
        if locale in settings.LOCALE_LANGUAGES:
            return locale
    return settings.DEFAULT_LANGUAGE

def cur_symbol(cur_code):
    return {
        'EUR': '€',
    }.get(cur_code, cur_code)

def to_unicode(data):
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            key = to_unicode(key)
            value = to_unicode(value)
            result[key] = value
    elif isinstance(data, list):
        result = []
        for value in data:
            value = to_unicode(value)
            result.append(value)
    elif isinstance(data, basestring):
        result = unicode(data, 'utf-8')
    else:
        result = data
    return result

def invoice_xslt(content, language=settings.DEFAULT_LANGUAGE):
    try:
        xml_input = etree.fromstring(content)
        xslt_root = etree.parse(settings.INVOICE_XSLT_PATH % language)
        transform = etree.XSLT(xslt_root)
        return str(transform(xml_input))
    except Exception, e:
        logging.error("invoice_xslt_err with content: %s, "
                      "error: %s",
                      content,
                      str(e),
                      exc_info=True)
        raise ServerError("Invoice xslt error")

def order_xslt(content, language=settings.DEFAULT_LANGUAGE):
    try:
        xml_input = etree.fromstring(content)
        xslt_root = etree.parse(settings.ORDER_XSLT_PATH % language)
        transform = etree.XSLT(xslt_root)
        return str(transform(xml_input))
    except Exception, e:
        logging.error("order_xslt_err with content: %s, "
                      "error: %s",
                      content,
                      str(e),
                      exc_info=True)
        raise ServerError("Invoice xslt error")

def get_user_info(conn, id_user):
    sql = ("select first_name || ' ' || last_name as fo_user_name,"
           "       email as fo_user_email,"
           "       calling_code || '' || phone_num as fo_user_phone"
           "  from users"
           "  left join users_profile on (users.id = users_profile.users_id)"
           "  left join users_phone_num on (users.id = users_phone_num.users_id)"
           "  left join country_calling_code on (users_phone_num.country_num = country_calling_code.country_code)"
           " where users.id=%s")
    row = db_utils.query(conn, sql, [id_user])[0]
    row_dict = dict(zip(("fo_user_name", "fo_user_email",
                         "fo_user_phone"), row))
    return row_dict

def _push_specific_event(event_name, **params):
    for n in ('email', 'service_email', 'id_brand'):
        assert n in params, "missing param %s" % n

    actor_event = get_event_configs(event_name)
    uri = actor_event.handler.url
    valid_params = {'event': actor_event.id}
    for p in actor_event.handler.parameter:
        valid_params[p.name] = params.get(p.name) or p.value or ""
    push_event(uri, **valid_params)

def push_ticket_event(**params):
    _push_specific_event('TICKETPOSTED', **params)

def push_order_confirming_event(conn, id_order, id_brand):
    id_user, confirmation_time = db_utils.select(conn, "orders",
                                         columns=("id_user", "confirmation_time"),
                                         where={'id': id_order})[0]
    user_info = get_user_info(conn, id_user)
    month, day = confirmation_time.strftime('%b|%d').split('|')
    params = {
        'email': user_info['fo_user_email'],
        'service_email': settings.SERVICE_EMAIL,
        'id_brand': id_brand,
        'id_order': id_order,
        'fo_user_name': user_info['fo_user_name'],
        'order_created_month': month,
        'order_created_day': day,
    }

    from models.order import get_order_items
    items = [item for item in get_order_items(conn, id_order)
             if item['brand_id'] == int(id_brand)]
    order_xml = render_content('order_details.xml',
                                **to_unicode({'order_items': items}))
    _xslt = order_xslt(order_xml)
    params['order_xslt'] = _xslt
    _push_specific_event('USR_ORDER_CONFIRMING', **params)

def push_order_confirmed_event(conn, id_order, id_brand, id_shops=None):
    id_user, confirmation_time = db_utils.select(conn, "orders",
                                         columns=("id_user", "confirmation_time"),
                                         where={'id': id_order})[0]
    user_info = get_user_info(conn, id_user)
    month, day = confirmation_time.strftime('%b|%d').split('|')
    params = {
        'email': user_info['fo_user_email'],
        'service_email': settings.SERVICE_EMAIL,
        'id_brand': id_brand,
        'id_order': id_order,
        'fo_user_name': user_info['fo_user_name'],
        'order_created_month': month,
        'order_created_day': day,
        'order_url': os.path.join(settings.FRONT_ROOT_URI,
                                  'orders/%s' % id_order),
    }

    from models.invoice import get_invoice_by_order
    from models.shipments import get_shipments_by_order
    shipments = get_shipments_by_order(conn, id_order)
    spm_dict = dict([(spm['id'], spm) for spm in shipments])
    invoices = get_invoice_by_order(conn, id_order)
    _xslts = []
    for iv in invoices:
        id_shipment = iv['id_shipment']
        spm = spm_dict.get(id_shipment)
        if not spm:
            continue
        if str(spm['id_brand']) != id_brand:
            continue
        if id_shops and str(spm['id_shop']) not in id_shops:
            continue
        _xslts.append(invoice_xslt(iv['invoice_xml']))

    params['invoices_xslt'] = ''.join(_xslts)
    _push_specific_event('USR_ORDER_CONFIRMED', **params)

