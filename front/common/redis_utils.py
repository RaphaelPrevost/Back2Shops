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


import logging
import redis
import settings

from redis.exceptions import RedisError

class RedisConnPool(object):
    _pool = None

    def __new__(cls):
        if not cls._pool:
            redis_config = settings.CENTRAL_REDIS
            if settings.RUNNING_TEST:
                port = redis_config['TEST_PORT']
            else:
                port = redis_config['PORT']

            cls._pool = redis.ConnectionPool(host=redis_config['HOST'],
                                             port=port,
                                             password=redis_config['PASSWORD'])
        return cls._pool


def get_redis_cli(ping=False):
    cli = redis.Redis(connection_pool=RedisConnPool())
    try:
        if ping:
            cli.ping()
        return cli
    except RedisError, e:
        logging.error('Redis Error: ', exc_info=True)


