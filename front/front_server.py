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

