from gevent import monkey
monkey.patch_all()
import gevent_psycopg2
gevent_psycopg2.monkey_patch()

import falcon
from gevent.pywsgi import WSGIServer

import settings
from urls import urlpatterns
from B2SUtils.db_utils import init_db_pool
from B2SUtils.log import setupLogging

setupLogging(settings.LOG_CONFIG_FILE)

# falcon.API instances are callable WSGI apps
app = api = falcon.API()

# Resources are represented by long-lived class instances
for url, res in urlpatterns.iteritems():
    api.add_route(url, res())

init_db_pool(settings.DATABASE)

if __name__ == '__main__':
    import logging
    logging.info('finance server start on port %s' % settings.SERVER_PORT)

    listener = ('0.0.0.0', settings.SERVER_PORT)
    print "finance server is running at http://%s:%s" % listener
    httpd = WSGIServer(listener, app)
    httpd.serve_forever()
