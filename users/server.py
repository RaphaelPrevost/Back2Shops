from gevent import monkey
monkey.patch_all()
import gevent_psycopg2
gevent_psycopg2.monkey_patch()

import argparse
import falcon
import gevent
from gevent.pywsgi import WSGIServer

import settings
from common.utils import parse_form_params
from urls import urlpatterns
from webservice.sales import import_sales_list
from webservice.shops import import_shops_list
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

def load_redis_data():
    gevent.spawn(import_sales_list)
    gevent.spawn(import_shops_list)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='User Server',
                                     add_help=False)
    parser.add_argument('--test', action='store_true', default=False)
    args = parser.parse_args()
    settings.RUNNING_TEST = args.test
    if settings.RUNNING_TEST:
        load_redis_data()
        print 'Start server for running test ...'
    else:
        load_redis_data()

    init_db()

    import logging
    logging.info('user server start on port %s' % settings.SERVER_PORT)

    listener = ('0.0.0.0', settings.SERVER_PORT)
    print "user server is running at http://%s:%s" % listener
    httpd = WSGIServer(listener, app)
    httpd.serve_forever()
