import copy
import gevent
import logging
import ujson
from api import remote_call
from constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import ALL
from B2SProtocol.constants import SALE
from B2SProtocol.constants import SALES_ALL
from B2SProtocol.constants import SALES_FOR_TYPE
from B2SProtocol.constants import SALES_FOR_CATEGORY
from B2SProtocol.constants import SALES_FOR_SHOP
from B2SProtocol.constants import SALES_FOR_BRAND
from B2SProtocol.constants import TYPES_FOR_BRAND

class NoRedisData(Exception):
    pass

class BaseCacheProxy(object):

    # override in subclass
    api_name = ""
    obj_redis_key = ""
    list_redis_key = ""
    filter_args = {}
    local_cache_file = None

    redis_cli = None
    usr_root_uri = None
    local_cache = None

    def __init__(self, redis_cli, usr_root_uri,
                 pri_key_path, usr_pub_key_uri):
        self.redis_cli = redis_cli
        self.usr_root_uri = usr_root_uri
        self.pri_key_path = pri_key_path
        self.usr_pub_key_uri = usr_pub_key_uri

    def get(self, **kw):
        try:
            resp_dict = self._get_from_redis(**kw)
        except Exception, e:
            if not isinstance(e, NoRedisData):
                logging.error("Failed to get from Redis %s", e,
                              exc_info=True)
            resp_dict = self._get_from_server(**kw)

        if resp_dict.get('res') == RESP_RESULT.F:
            resp_dict = self._get_from_local(**kw)
        elif self._need_save_local_cache(**kw):
            self._update_local_cache(resp_dict)
        return resp_dict

    def _get_from_server(self, obj_id=None, **kw):
        resp_dict = remote_call(self.usr_root_uri, self.api_name,
                                self.pri_key_path, self.usr_pub_key_uri,
                                None, None, **kw)
        if resp_dict.get('res') == RESP_RESULT.F:
            return resp_dict
        if obj_id:
            resp_dict = {obj_id: resp_dict.get(obj_id)}
        return resp_dict

    def _get_from_redis(self, obj_id=None, **kw):
        if obj_id:
            obj_ids = [obj_id]
        else:
            obj_ids = self._filter_obj_ids(**kw)

        resp_dict = {}
        for _id in obj_ids:
            obj = self.redis_cli.get(self.obj_redis_key % _id)
            if obj:
                resp_dict[_id] = ujson.loads(obj)
        return resp_dict

    def _get_from_local(self, obj_id=None, **kw):
        resp_dict = {}
        if self.local_cache is None:
            self._read_local_cache()
            if self.local_cache is None:
                return resp_dict

        if obj_id:
            obj = self.local_cache.get(obj_id)
            if obj:
                resp_dict[obj_id] = obj
            return resp_dict

        valid_args = dict([(q, kw[q]) for q in kw
                     if q in self.filter_args and kw[q]])
        for _id, obj in self.local_cache.iteritems():
            if obj and self._match_obj(obj, **valid_args):
                resp_dict[_id] = obj
        return resp_dict

    def _need_save_local_cache(self, **kw):
        return kw.get('brand') and len(kw) == 1

    def _update_local_cache(self, resp_dict):
        if self.local_cache is None:
            self.local_cache = {}
        old_local_cache = copy.deepcopy(self.local_cache)
        self.local_cache.update(resp_dict)
        if old_local_cache != self.local_cache:
            gevent.spawn(self._write_local_cache)

    def _read_local_cache(self):
        try:
            with open(self.local_cache_file, 'r') as f:
                self.local_cache = ujson.load(f)
        except IOError:
            pass

    def _write_local_cache(self):
        try:
            with open(self.local_cache_file, 'w') as f:
                ujson.dump(self.local_cache, f)
        except IOError, e:
            logging.error("Failed to write %s: %s", self.local_cache_file, e,
                          exc_info=True)

    def _match_obj(self, obj, **valid_kwargs):
        raise NotImplementedError

    def _filter_obj_ids(self, **kw):
        obj_ids = set(self.redis_cli.lrange(self.list_redis_key % ALL, 0, -1))
        for arg_name, filter_key in self.filter_args.iteritems():
            obj_ids = self._filter_interact(filter_key,
                                            kw.get(arg_name),
                                            obj_ids)
        return obj_ids

    def _filter_interact(self, key, id_, pre_ids):
        if id_ is None:
            return pre_ids

        assert isinstance(pre_ids, set)
        filter_ids = set(self.redis_cli.lrange(key % id_, 0, -1))
        return pre_ids.intersection(filter_ids)


class RoutesCacheProxy(BaseCacheProxy):
    api_name = REMOTE_API_NAME.GET_ROUTES
    local_cache_file = "static/cache/%s.json" % api_name

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RoutesCacheProxy,
                                  cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def get(self, **kw):
        resp_dict = self._get_from_server(**kw)

        if resp_dict.get('res') == RESP_RESULT.F:
            resp_dict = self._get_from_local(**kw)
        elif self._need_save_local_cache(**kw):
            self._update_local_cache(resp_dict)
        return resp_dict

    def _match_obj(self, obj, **valid_kwargs):
        return True


class SalesCacheProxy(BaseCacheProxy):
    api_name = REMOTE_API_NAME.GET_SALES
    obj_redis_key = SALE
    list_redis_key = SALES_ALL
    filter_args = {
        'category': SALES_FOR_CATEGORY,
        'shop': SALES_FOR_SHOP,
        'brand': SALES_FOR_BRAND,
        'type': SALES_FOR_TYPE,
    }
    local_cache_file = "static/cache/%s.json" % api_name

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SalesCacheProxy,
                                  cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def _match_obj(self, obj, **valid_kwargs):
        for key, value in valid_kwargs.iteritems():
            if key in obj and "@id" in obj[key] and obj[key]['@id'] == value:
                continue
            else:
                return False
        return True


class TypesCacheProxy(BaseCacheProxy):
    api_name = REMOTE_API_NAME.GET_TYPES
    local_cache_file = "static/cache/%s.json" % api_name

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TypesCacheProxy,
                                  cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def _get_from_redis(self, **kw):
        brand_id = kw.get('seller')
        types = self.redis_cli.get(TYPES_FOR_BRAND % brand_id)
        if not types:
            raise NoRedisData()
        return dict([(t["@id"], t) for t in ujson.loads(types)])

    def _need_save_local_cache(self, **kw):
        return kw.get('seller') and len(kw) == 1

    def _match_obj(self, obj, **valid_kwargs):
        return True


cache_proxy = {
    RoutesCacheProxy.api_name: RoutesCacheProxy,
    SalesCacheProxy.api_name: SalesCacheProxy,
    TypesCacheProxy.api_name: TypesCacheProxy,
}
