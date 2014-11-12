import cgi
import Cookie
import datetime
import logging
import urllib
from pytz import timezone

from Cookie import SimpleCookie

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
    sc = 'set-cookie'
    c = SimpleCookie()

    if resp._headers.get(sc):
        c.load(resp._headers.get(sc))

    c[k] = v.strip()
    if expiry:
        c[k]['expires'] = expiry
    if domain:
        c[k]['domain'] = domain
    if path:
        c[k]['path'] = path
    if secure is True:
        c[k]['secure'] = True

    resp.append_header(sc, c[k].OutputString())

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

def parse_ts(ts):
    if isinstance(ts, datetime.datetime) or isinstance(ts, datetime.date):
        return ts
    elif ts is None:
        return None
    elif isinstance(ts, (str, unicode)):
        for pattern in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'):
            try:
                dt = datetime.datetime.strptime(ts[:16], pattern)
                return dt
            except:
                pass
    else:
         return datetime.datetime.fromtimestamp(ts)

def localize_datetime(date, tz_from, tz_to):
    if date.tzinfo is None:
        date = timezone(tz_from).localize(date)
        dt = date.astimezone(timezone(tz_to))
    # use normalize() method to handle daylight savings time
    # and other timezone transitions.
    return dt.tzinfo.normalize(dt)

