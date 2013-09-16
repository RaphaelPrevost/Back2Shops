import cgi
import datetime
import hashlib
import hmac
import re
import ujson
import settings
from common.constants import HASH_ALGORITHM
from common.constants import HASH_ALGORITHM_NAME

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

def make_auth_cookie(expiry, csrf_token, auth_token):
    secret_key = '' #TODO
    digest = get_hmac(secret_key,
                 ";".join([expiry, csrf_token, auth_token]))
    data = {'exp': expiry,
            'csrf': csrf_token,
            'auth': auth_token,
            'digest': digest}
    return '&'.join(['%s=%s' % (k, v) for k, v in data.iteritems()])

def set_cookie(resp, k, v, expiry=None, domain=None, path='/', secure=False):
    if settings.DEBUG:
        domain = None
        secure = False

    values = ['%s=%s' % (k, v)]
    if expiry:
        values.append('expires=%s' % expiry)
    if domain:
        values.append('domain=%s' % domain)
    if path:
        values.append('path=%s' % path)
    if secure is True:
        values.append('secure')
    resp.set_header('Set-Cookie', ';'.join(values))

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

