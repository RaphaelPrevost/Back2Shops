import redis

class RedisConnPool(object):
    _pool = None

    def __new__(cls, config):
        if not cls._pool:
            cls._pool = redis.ConnectionPool(host=config['HOST'],
                                             port=config['PORT'])
        return cls._pool

def redis_cli(config):
    return redis.Redis(connection_pool=RedisConnPool(config))
