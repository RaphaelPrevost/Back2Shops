# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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

