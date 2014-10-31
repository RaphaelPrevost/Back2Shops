import redis

class RedisConnPool(object):
    _pool = None

    def __new__(cls, config):
        if not cls._pool:
            kwargs = {'host': config['HOST'],
                      'port': config['PORT']}
            if config.get('TIMEOUT'):
                kwargs.update({'socket_timeout': config['TIMEOUT']})
            cls._pool = redis.ConnectionPool(**kwargs)
        return cls._pool

def redis_cli(config):
    return redis.Redis(connection_pool=RedisConnPool(config))
