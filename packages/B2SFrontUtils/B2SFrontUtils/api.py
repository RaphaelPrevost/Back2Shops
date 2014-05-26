import Cookie
import logging
import re
import ujson
import urllib
import urllib2
from constants import USR_API_SETTINGS
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import USER_AUTH_COOKIE_NAME


def remote_call(usr_root_uri, api_name,
                pri_key_path, usr_pub_key_uri,
                req, resp, **kwargs):
    if api_name not in USR_API_SETTINGS:
        raise Exception('wrong api calling: %s' % api_name)

    try:
        url = usr_root_uri + USR_API_SETTINGS[api_name]['url']
        method = USR_API_SETTINGS[api_name]['method']
        headers = generate_remote_req_headers(req)
        encrypt = re.search('/(private|protected)/', url)

        remote_resp = _request_remote_server(
            url, method, kwargs, headers,
            encrypt, pri_key_path, usr_pub_key_uri)
        set_new_auth_cookie(resp, remote_resp.headers)
        if encrypt:
            content = decrypt_json_resp(remote_resp, usr_pub_key_uri, pri_key_path)
        else:
            content = remote_resp.read()
        return ujson.loads(content)

    except Exception, e:
        logging.error("Failed to get %s from Users Server %s",
                      url, e, exc_info=True)
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


def _request_remote_server(uri, method, params, headers,
               encrypt=False, pri_key_path=None, usr_pub_key_uri=None):
    data = None
    headers = headers or {}

    if params:
        query_str = urllib.urlencode(params)
        if method == 'GET':
            uri = '?'.join([uri, query_str])
        else:
            data = query_str

    try:
        if encrypt and data:
            data = gen_encrypt_json_context(
                data, usr_pub_key_uri, pri_key_path)

        req = urllib2.Request(uri, data=data, headers=headers)
        return urllib2.urlopen(req)

    except urllib2.HTTPError, e:
        logging.error('_request_remote_server HTTPError: '
                      'error: %s, '
                      'with uri: %s, data :%s, headers: %s'
                      % (e, uri, data, headers), exc_info=True)
        raise

