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
        encrypt = USR_API_SETTINGS[api_name].get('encrypt')
        if encrypt is None:
            encrypt = re.search('/(private|protected)/', url)
        headers = generate_remote_req_headers(req, resp)

        remote_resp = _request_remote_server(
            url, method, kwargs, headers,
            encrypt, pri_key_path, usr_pub_key_uri)
        if resp and 'set-cookie' in remote_resp.headers:
            set_resp_cookie_header(resp, remote_resp.headers['set-cookie'])
        if encrypt:
            content = decrypt_json_resp(remote_resp, usr_pub_key_uri, pri_key_path)
        else:
            content = remote_resp.read()
        try:
            return ujson.loads(content)
        except:
            return content

    except Exception, e:
        logging.error("Failed to get %s from Users Server %s",
                      url, e, exc_info=True)
        return {'res': RESP_RESULT.F, 'err': 'SERVER_ERR'}


def generate_remote_req_headers(req, resp):
    headers = req.headers.copy() if req else {}
    if 'content-length' in headers:
        headers.pop('content-length')

    if resp and 'set-cookie' in resp._headers:
        req_cookies = Cookie.SimpleCookie()
        req_cookies.load(req.env.get('HTTP_COOKIE') or '')
        resp_cookies = Cookie.SimpleCookie()
        resp_cookies.load(resp._headers['set-cookie'])
        req_cookies.update(resp_cookies)
        headers['cookie'] = '; '.join(['%s="%s"' % (k, c.value)
                                       for k, c in req_cookies.iteritems()])
    return headers

def set_resp_cookie_header(resp, cookie_value):
    if 'set-cookie' not in resp._headers:
        resp.set_header('set-cookie', cookie_value)
        return

    resp_cookies = Cookie.SimpleCookie()
    resp_cookies.load(resp._headers['set-cookie'])
    new_cookies = Cookie.SimpleCookie()
    new_cookies.load(cookie_value)
    resp_cookies.update(new_cookies)

    values = []
    for c in resp_cookies.itervalues():
        values.append(c.output().replace('Set-Cookie: ', ''))
    resp.set_header('set-cookie', ' '.join(values))


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

