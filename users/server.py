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
import gevent_psycopg2
gevent_psycopg2.monkey_patch()

import argparse
import falcon
import gevent
from gevent.pywsgi import WSGIServer

import settings
from urls import urlpatterns
from webservice.sales import import_sales_list
from webservice.shops import import_shops_list
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

def load_redis_data():
    gevent.spawn(import_sales_list)
    gevent.spawn(import_shops_list)

init_db()
load_redis_data()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='User Server',
                                     add_help=False)
    parser.add_argument('--test', action='store_true', default=False)
    args = parser.parse_args()
    settings.RUNNING_TEST = args.test
    if settings.RUNNING_TEST:
        print 'Start server for running test ...'

    import logging
    logging.info('user server start on port %s' % settings.SERVER_PORT)

    listener = ('0.0.0.0', settings.SERVER_PORT)
    print "user server is running at http://%s:%s" % listener
    httpd = WSGIServer(listener, app)
    httpd.serve_forever()

