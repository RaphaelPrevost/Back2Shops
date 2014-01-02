import redis
import settings

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
                                             port=port)
        return cls._pool


def get_redis_cli():
    return redis.Redis(connection_pool=RedisConnPool())
