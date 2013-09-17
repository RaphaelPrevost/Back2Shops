import binascii
import cgi
import Cookie
import datetime
import hashlib
import hmac
import os
import re
import ujson
import settings
from common.constants import HASH_ALGORITHM
from common.constants import HASH_ALGORITHM_NAME
from common.error import ValidationError
from common import db_utils


email_pattern = re.compile(
    r"^([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@([-0-9a-zA-Z]+.)+[a-zA-Z]{2,6}$")

def is_valid_email(email):
    return email and email_pattern.match(email)

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

_EXPIRY_FORMAT = '%a, %d %b %Y %T UTC'
def gen_cookie_expiry(expiry_timelen):
    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=expiry_timelen)
    return (now + delta).strftime(_EXPIRY_FORMAT)

def make_auth_cookie(expiry, csrf_token, auth_token, users_id):
    secret_key = '' #TODO
    digest = get_hmac(secret_key,
                 ";".join([expiry, csrf_token, auth_token]))
    data = {'exp': expiry,
            'csrf': csrf_token,
            'auth': auth_token,
            'digest': digest,
            'users_id': users_id}
    return '&'.join(['%s=%s' % (k, v) for k, v in data.iteritems()])

def set_cookie(resp, k, v, expiry=None, domain=None, path='/', secure=False):
    if settings.DEBUG:
        domain = None
        secure = False

    values = ['%s="%s"' % (k, v)]
    if expiry:
        values.append('expires=%s' % expiry)
    if domain:
        values.append('domain=%s' % domain)
    if path:
        values.append('path=%s' % path)
    if secure is True:
        values.append('secure')

    resp.set_header('Set-Cookie', ';'.join(values))

def get_cookie(req):
    """ Get cookie from request environment.

    req: request

    return: SimpleCookie instance if cookie exist in request,
            otherwise return None.
    """
    if req.env.has_key('HTTP_COOKIE'):
        cookie = Cookie.SimpleCookie()
        cookie.load(req.env['HTTP_COOKIE'])
        return cookie

def parse_form_params(req, resp, params):
    if req.method == 'GET':
        return
    if 'x-www-form-urlencoded' not in req.content_type:
        return

    # in falcon 0.1.6 req._params doesn't support form params
    try:
        body = req.stream.read(req.content_length)
    except:
        pass
    else:
        form_params = cgi.parse_qs(body)
        for p in form_params:
            form_params[p] = form_params[p][0]
        req._params.update(form_params)

def get_client_ip(req):
    ip_adds = req.get_header('x-forwarded-for') or ''
    return ip_adds.split(',')[0].strip()

def get_hashed_headers(req):
    headers = ";".join([
            req.get_header('Accept') or '',
            req.get_header('Accept-Language') or '',
            req.get_header('Accept-Encoding') or '',
            req.get_header('Accept-Charset') or '',
            req.get_header('User-Agent') or '',
            req.get_header('DNT') or ''])
    return hashfn(HASH_ALGORITHM.SHA256, headers)

def gen_json_response(resp, data_dict):
    resp.content_type = "application/json"
    resp.body = ujson.dumps(data_dict)
    return resp

def _mac_verify(user_auth):
    """ MAC verification.
    """
    secret_key = '' #TODO
    text = ";".join([user_auth['exp'], user_auth['csrf'], user_auth['auth']])
    expected_digest = get_hmac(secret_key, text)
    if user_auth['digest'] != expected_digest:
        raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_MAC')

def _user_verify(conn, users_id, req_method, user_auth, ip, headers):
    """ Verify user information for the request.

    conn: database connection.
    users_id: user's id.
    req_method: request method, string of 'GET' or 'POST'.
    user_auth: pre-image for user's password.
    ip: IP address for the request.
    headers: request header information.
    """
    columns = ('password', 'ip_address', 'headers', 'csrf_token',
               'users_logins.id')
    result = db_utils.join(conn, ('users', 'users_logins'),
                            columns=columns,
                            on=[('users.id', 'users_logins.users_id')],
                            where={'users.id': users_id,
                                   'users_logins.csrf_token': user_auth['csrf']},
                            limit=1)
    if not result or len(result) == 0:
        raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_USER')

    exp_auth, exp_ip, exp_headers, exp_csrf, login_id  = result[0]
    cur_auth = get_authenticator(settings.DEFAULT_PASSWORD_HASH_ALGORITHM,
                                 user_auth['auth'])
    if cur_auth != exp_auth:
        raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_AUTH')

    if ip != exp_ip:
        raise ValidationError('LOGIN_REQUIRED_ERR_IP_CHANGED')

    if headers != exp_headers:
        raise ValidationError('LOGIN_REQUIRED_ERR_HEADERS_CHANGED')

    if req_method == 'POST' and user_auth['csrf'] != exp_csrf:
        raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_CSRF')

    return login_id

def _parse_auth_cookie(auth_cookie):
    """ Parse auth information string, return dict object.

    auth_cookie: string, generated by make_auth_cookie.
    """
    auth_fields = auth_cookie.split('&')
    fields_list = [tuple(field.split('=')) for field in auth_fields]
    return dict(fields_list)

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
        raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_COOKIE')

    # 'USER_AUTH' should be in the cookie.
    required_fields = [settings.USER_AUTH_COOKIE_NAME]
    for field in required_fields:
        if not cookie.has_key(field):
            raise ValidationError('LOGIN_REQUIRED_ERR_INVALID_COOKIE')

    # authenticated information should be contained in 'USER_AUTH'
    auth_fields = ['exp', 'csrf', 'auth', 'digest', 'users_id']
    user_auth = cookie.get(settings.USER_AUTH_COOKIE_NAME).value
    user_auth = _parse_auth_cookie(user_auth)
    for field in auth_fields:
        if not user_auth.has_key(field):
            raise ValidationError('LOGIN_REQUIRED_ERR_AUTH_FAILURE')

    users_id = user_auth['users_id']
    req_method = req.method.upper()
    ip = get_client_ip(req)
    headers = get_hashed_headers(req)

    # cookie verify
    _mac_verify(user_auth)
    login_id = _user_verify(conn, users_id, req_method, user_auth, ip, headers)

    # set new csrf to cookie and database.
    csrf_token = binascii.b2a_hex(os.urandom(16))
    auth_cookie = make_auth_cookie(user_auth['exp'],
                                   csrf_token,
                                   user_auth['auth'],
                                   users_id)
    set_cookie(resp, settings.USER_AUTH_COOKIE_NAME, auth_cookie,
               domain=settings.USER_AUTH_COOKIE_DOMAIN,
               expiry=user_auth['exp'], secure=True)

    db_utils.update(conn,
                    'users_logins',
                    values={'csrf_token': csrf_token},
                    where={'id': login_id})
