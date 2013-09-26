import logging
import urllib2
from redis.exceptions import RedisError

import settings
from common.constants import RESP_RESULT
from common.redis_utils import get_redis_cli

class CacheProxy:

    def get(self, name):
        result = self._get_from_redis(name)
        if result is None:
            result = self.refresh(name)
        return result

    def refresh(self, name):
        result = self._get_from_server(name)
        self._save_to_redis(name, result)
        return result

    def _get_from_redis(self, name):
        logging.info('fetch from redis: %s', name)
        try:
            result = get_redis_cli().get(name)
        except RedisError, e:
            result = None
            logging.error('Redis Error: %s', (e,), exc_info=True)
        return result

    def _save_to_redis(self, name, value):
        logging.info('save to redis: %s', name)
        try:
            get_redis_cli().setex(name, value, settings.SALES_CACHE_TTL)
        except RedisError, e:
            logging.error('Redis Error: %s', (e,), exc_info=True)

    def _get_from_server(self, name):
        logging.info('fetch from sales server : %s', name)
        try:
            #TODO #52 will implement a proper way to communicate with sales server
            req = urllib2.Request(settings.SALES_SERVER_API_URL % {'api': name})
            resp = urllib2.urlopen(req)
            return "".join(resp.readlines())
        except Exception, e:
            logging.error('Server Error: %s', (e,), exc_info=True)
            return '<res error="SERVER_ERR">%s</res>' % RESP_RESULT.F

cache_proxy = CacheProxy()
