import Cookie
import logging
import ujson
import urllib
import urllib2
from constants import USR_API_SETTINGS
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import USER_AUTH_COOKIE_NAME


def remote_call(usr_root_uri, api_name, req, resp, **kwargs):
    if api_name not in USR_API_SETTINGS:
        raise Exception('wrong api calling: %s' % api_name)

    try:
        url = usr_root_uri + USR_API_SETTINGS[api_name]['url']
        method = USR_API_SETTINGS[api_name]['method']
        headers = generate_remote_req_headers(req)
        remote_resp = _request_remote_server(url, method, kwargs,
                                             headers=headers)
        set_new_auth_cookie(resp, remote_resp.headers)
        return ujson.loads(remote_resp.read())

    except Exception, e:
        logging.error("Failed to get from Users Server %s", e,
                      exc_info=True)
        return {'res': RESP_RESULT.F, 'err': 'SERVER_ERR'}


def generate_remote_req_headers(req):
    headers = req.headers.copy() if req else {}
    if 'content-length' in headers:
        headers.pop('content-length')
    return headers

def set_new_auth_cookie(resp, remote_resp_headers):
    if not resp or 'set-cookie' not in remote_resp_headers:
        return

    cookies = Cookie.SimpleCookie()
    cookies.load(remote_resp_headers['set-cookie'])
    if cookies and USER_AUTH_COOKIE_NAME in cookies:
        new_auth_cookie = cookies.get(USER_AUTH_COOKIE_NAME)
        if new_auth_cookie:
            _, header_value = new_auth_cookie.output().split(':', 1)
            resp.set_header('set-cookie', header_value.strip())


def _request_remote_server(uri, method, params, headers=None):
    data = None
    headers = headers or {}

    if params:
        query_str = urllib.urlencode(params)
        if method == 'GET':
            uri = '?'.join([uri, query_str])
        else:
            data = query_str

    req = urllib2.Request(uri, data=data, headers=headers)
    try:
        return urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        logging.error('_request_remote_server HTTPError: '
                      'error: %s, '
                      'with uri: %s, data :%s, headers: %s'
                      % (e, uri, data, headers), exc_info=True)
        raise

