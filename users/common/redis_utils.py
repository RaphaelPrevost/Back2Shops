import redis
import settings

class RedisConnPool(object):
    _pool = None

    def __new__(cls):
        if not cls._pool:
            redis_config = settings.CENTRAL_REDIS
            cls._pool = redis.ConnectionPool(host=redis_config['HOST'],
                                             port=redis_config['PORT'])
        return cls._pool


def get_redis_cli():
    return redis.Redis(connection_pool=RedisConnPool())
