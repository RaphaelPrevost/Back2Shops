# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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


from gevent import monkey
monkey.patch_all()

from B2SUtils.patch import monkey_patch
monkey_patch()

import B2SFalcon as falcon
import gevent
from gevent.pywsgi import WSGIServer
import os
import signal

import settings
from batch import start as batch_start
from common.data_access import data_access
from common.m17n import init_translators
from common.utils import html_escape_params
from common.utils import send_reload_signal
from common.utils import watching_invalidate_cache_list
from urls import BrandRoutes
from B2SUtils.log import setupLogging
from B2SUtils.common import parse_form_params
from B2SFrontUtils.constants import REMOTE_API_NAME


setupLogging(settings.LOG_CONFIG_FILE)
init_translators()

def get_app(reload_=False):
    # falcon.API instances are callable WSGI apps
    app = falcon.API(before=[parse_form_params, html_escape_params])

    # Resources are represented by long-lived class instances
    routes = BrandRoutes()
    for url, instance in routes.url_res_mapping(reload_).iteritems():
        app.add_route(url, instance)
    return app

app = get_app()
pid = os.getpid()
if not settings.PRODUCTION:
    gevent.spawn(send_reload_signal, pid)
gevent.spawn(watching_invalidate_cache_list, pid)
gevent.spawn(data_access, REMOTE_API_NAME.GET_SALES)
gevent.spawn_later(30, batch_start)

def load_app(server, app=None):
    if not app:
        app = get_app(reload_=True)
    server.application = app

if __name__ == '__main__':
    import logging
    logging.info('frontend instance start on port %s' % settings.SERVER_PORT)

    listener = ('0.0.0.0', settings.SERVER_PORT)
    print "frontend instance is running at http://%s:%s" % listener
    httpd = WSGIServer(listener, None)
    load_app(httpd, app)
    gevent.signal(signal.SIGHUP, load_app, httpd)
    httpd.serve_forever()

