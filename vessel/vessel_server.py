from gevent import monkey
monkey.patch_all()
import gevent_psycopg2
gevent_psycopg2.monkey_patch()

import falcon
import gevent
from gevent.pywsgi import WSGIServer

import settings
from urls import urlpatterns
from B2SUtils.common import parse_form_params
from B2SUtils.db_utils import init_db_pool
from B2SUtils.log import setupLogging


setupLogging(settings.LOG_CONFIG_FILE)

# falcon.API instances are callable WSGI apps
app = api = falcon.API(before=[parse_form_params])

# Resources are represented by long-lived class instances
for url, res in urlpatterns.iteritems():
    api.add_route(url, res())

def init_db():
    init_db_pool(settings.DATABASE)

init_db()

if __name__ == '__main__':
    import logging
    logging.info('vessel server start on port %s' % settings.SERVER_PORT)

    listener = ('0.0.0.0', settings.SERVER_PORT)
    print "vessel server is running at http://%s:%s" % listener
    httpd = WSGIServer(listener, app)
    httpd.serve_forever()

