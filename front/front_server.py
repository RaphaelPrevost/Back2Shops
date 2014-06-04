from gevent import monkey
monkey.patch_all()

import falcon
import gevent
from gevent.pywsgi import WSGIServer
import signal

import settings
from common.data_access import data_access
from urls import BrandRoutes
from B2SUtils.log import setupLogging
from B2SUtils.common import parse_form_params
from B2SFrontUtils.constants import REMOTE_API_NAME


setupLogging(settings.LOG_CONFIG_FILE)

def get_app():
    # falcon.API instances are callable WSGI apps
    app = falcon.API(before=[parse_form_params])

    # Resources are represented by long-lived class instances
    routes = BrandRoutes()
    for url, instance in routes.url_res_mapping().iteritems():
        app.add_route(url, instance)
    return app

app = get_app()
gevent.spawn(data_access, REMOTE_API_NAME.GET_SALES)

def load_app(server, app=None):
    if not app:
        app = get_app()
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

