import cgi
import Cookie
import logging
import urllib

def parse_form_params(req, resp, params):
    if req.method == 'GET':
        for p in req._params:
            req._params[p] = urllib.unquote_plus(req._params[p])
        return
    if req.content_type and 'x-www-form-urlencoded' not in req.content_type:
        return

    # in falcon 0.1.6 req._params doesn't support form params
    try:
        body = req.stream.read(req.content_length)
        form_params = cgi.parse_qs(body)
        for p in form_params:
            form_params[p] = form_params[p][0]
        req._params.update(form_params)

        if req.query_string.strip() == "":
            req.query_string = body
        else:
            req.query_string += "&"
            req.query_string += body
    except:
        pass


def set_cookie(resp, k, v, expiry=None, domain=None, path='/', secure=False):
    values = ['%s="%s"' % (k, v)]
    if expiry:
        values.append('expires="%s"' % expiry)
    if domain:
        values.append('domain=%s' % domain)
    if path:
        values.append('path=%s' % path)
    if secure is True:
        values.append('secure')

    new_value = ';'.join(values)
    if 'set-cookie' in resp._headers:
        old_value = resp._headers['set-cookie']
        resp.set_header('set-cookie', ' '.join([old_value, new_value]))
    else:
        resp.set_header('set-cookie', new_value)

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

def get_cookie_value(req, cookie_name):
    cookies = get_cookie(req)
    if cookies and cookie_name in cookies:
        return cookies[cookie_name].value

def to_round(val, decimal_digits=2):
    if val is None:
        return val
    try:
        # hacky to add a small number for the float exactness issue in python.
        if val < 0:
            return round(float(val)-0.0000001, decimal_digits)
        else:
            return round(float(val)+0.0000001, decimal_digits)
    except:
        logging.error("something wrong with this money value: " + str(val))
    return val
