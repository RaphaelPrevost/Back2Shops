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
import gevent_psycopg2
gevent_psycopg2.monkey_patch()

import falcon
import gevent
from gevent.pywsgi import WSGIServer

import settings
from batch import start as batch_start
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
gevent.spawn_later(30, batch_start)

if __name__ == '__main__':
    import logging
    logging.info('vessel server start on port %s' % settings.SERVER_PORT)

    listener = ('0.0.0.0', settings.SERVER_PORT)
    print "vessel server is running at http://%s:%s" % listener
    httpd = WSGIServer(listener, app)
    httpd.serve_forever()

