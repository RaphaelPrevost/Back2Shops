import logging
import gevent
import xmltodict
import ujson
import urllib
import urllib2
from collections import defaultdict
from collections import OrderedDict
from redis.exceptions import RedisError, ConnectionError

import settings
from common.redis_utils import get_redis_cli

ALL = 'ALL'
SALE = 'SALE:%s'
SALES_FOR_TYPE = 'SALES_FOR_TYPE:%s'
SALES_FOR_CATEGORY = 'SALES_FOR_CATEGORY:%s'
SALES_FOR_SHOP = 'SALES_FOR_SHOP:%s'
SALES_FOR_BRAND = 'SALES_FOR_BRAND:%s'
SALES_VERSION = 'SALES_VERSION'
SALES_ALL = 'SALES:%s'

SHOP = 'SHOP:%s'
SHOPS_FOR_BRAND = 'SHOPS_FOR_BRAND:%s'
SHOPS_FOR_CITY = 'SHOPS_FOR_CITY:%s'
SHOPS_VERSION = 'SHOPS_VERSION'
SHOPS_ALL = 'SHOPS:%s'

SALE_CACHED_QUERY = 'SALE_CACHED_QUERY:%s'
SALES_QUERY = 'SALES:QUERY:%s'

class NotExsitError(Exception):
    pass

class CacheProxy:
    list_api = None
    obj_api = None
    obj_key = None

    def get(self, **kw):
        try:
            return self._get_from_redis(**kw)
        except Exception, e:
            logging.error("Faled to get from Redis %s", e, exc_info=True)
            return self._get_from_server(**kw)

    def refresh(self, obj_id=None):
        try:
            self._get_from_server(obj_id)
        except Exception, e:
            logging.error('Cache Proxy Refresh Error: %s',
                          (e,),
                          exc_info=True)

    def del_obj(self, obj_id):
        self._rem_attrs_for_obj(obj_id)
        self._del_objs(self.obj_key % obj_id)

    def cached_query_invalidate(self, obj_id, method):
        del_all = method.upper() == 'POST'
        self._del_cached_query(obj_id, del_all)

    def _del_cached_query(self, obj_id, del_all):
        pass

    def _get_from_redis(self, **kw):
        raise NotImplementedError

    def _get_from_server(self, obj_id=None, **kw):
        if obj_id is None:
            query = self._get_query_str(**kw)
            api = self.list_api % query
        else:
            api = self.obj_api % obj_id

        logging.info('fetch from sales server : %s', api)
        req = urllib2.Request(
            settings.SALES_SERVER_API_URL % {'api': api})
        resp = urllib2.urlopen(req)

        is_entire_result = (obj_id is None and query == '')
        return self.parse_xml("".join(resp.readlines()), is_entire_result)

    def _set_to_redis(self, name, value):
        logging.info('save to redis: %s - %s', name, value)
        get_redis_cli().set(name, value)

    def _save_attrs_to_redis(self, key, data):
        """ Save attribute related info into redis to make the query easier.
        key: one option of SALES_FOR_TYPE, SALES_FOR_CATEGORY,
             SALES_FOR_SHOP, SALES_FOR_BRAND, SHOPS_FOR_BRAND,
             SHOPS_FOR_CITY
        data: a list dict,
              key is the attribute id,
              value is a id list to be pushed into redis.
        """
        assert isinstance(data, dict)
        pipe = get_redis_cli().pipeline()
        for id, values in data.iteritems():
            if not id:
                continue
            for v in values:
                pipe.rpush(key % id, v)
        pipe.execute()

    def _save_objs_to_redis(self, data_list):
        """ save parsed xml data list into redis.
        data_list: OrderedDict list.
             dict in the list must contain key '@id'.
        """
        if not data_list:
            return
        pipe = get_redis_cli().pipeline()
        for data in data_list:
            data_id = data['@id']
            data_str = ujson.dumps(data)
            name = self.obj_key % data_id
            self._rem_attrs_for_obj(data_id)
            pipe.set(name, data_str)
        pipe.execute()

    def parse_xml(self, xml, is_entire_result):
        raise NotImplementedError

    def _filter_interact(self, key, id, pre_ids):
        if id is None:
            return pre_ids

        assert isinstance(pre_ids, set)
        name = key % id
        filter_ids = set(get_redis_cli().lrange(name, 0, -1))

        return pre_ids.intersection(filter_ids)

    def _rem_attrs_for_obj(self, id):
        raise NotImplementedError

    def _rem_diff_objs(self, key, current_objs):
        pre_objs = get_redis_cli().lrange(key % ALL, 0, -1)
        diff = set(pre_objs).difference(set(current_objs))
        for obj_id in diff:
            self._rem_attrs_for_obj(obj_id)
        objs_name = [self.obj_key % id for id in diff]
        self._del_objs(*objs_name)

    def _del_objs(self, *objs_name):
        if not objs_name:
            return
        logging.info('delete from redis: %s', objs_name)
        get_redis_cli().delete(*objs_name)

    @property
    def query_options(self):
        return ()

    def _get_query_str(self, **kw):
        return urllib.urlencode([(q, kw[q]) for q in kw.keys()
                                 if q in self.query_options and kw[q]])


class SalesCacheProxy(CacheProxy):
    list_api = "pub/sales/list?%s"
    obj_api = "pub/sales/info/%s"
    obj_key = SALE

    @property
    def query_options(self):
        return ('category', 'shop', 'brand', 'type')

    def _get_from_redis(self, **kw):
        # do filters.
        sales_id = set(get_redis_cli().lrange(SALES_ALL % ALL, 0, -1))
        sales_id = self._filter_interact(SALES_FOR_CATEGORY,
                                         kw.get('category'),
                                         sales_id)
        sales_id = self._filter_interact(SALES_FOR_SHOP,
                                         kw.get('shop'),
                                         sales_id)
        sales_id = self._filter_interact(SALES_FOR_BRAND,
                                         kw.get('brand'),
                                         sales_id)
        sales_id = self._filter_interact(SALES_FOR_TYPE,
                                         kw.get('type'),
                                         sales_id)

        sales = {}
        for s_id in sales_id:
            sale = get_redis_cli().get(SALE % s_id)
            if sale:
                sale = ujson.loads(sale)
                sales[s_id] = sale

        return sales

    def _rem_attrs_for_obj(self, id):
        cli = get_redis_cli()
        sale = cli.get(SALE % id)
        if not sale:
            cli.lrem(SALES_ALL % ALL, id, 0)
            return
        sale = ujson.loads(sale)
        pipe = cli.pipeline()
        pipe.lrem(SALES_FOR_CATEGORY % sale['category']['@id'], id, 0)
        pipe.lrem(SALES_FOR_TYPE % sale['type']['@id'], id, 0)
        pipe.lrem(SALES_FOR_BRAND % sale['brand']['@id'], id, 0)
        pipe.lrem(SALES_ALL % ALL, id, 0)
        if sale.get('shop'):
            pipe.lrem(SALES_FOR_SHOP % sale['shop']['@id'], id, 0)
        pipe.execute()

    def parse_xml(self, xml, is_entire_result):
        logging.info('parse sales xml: %s, is_entire_result:%s',
                     xml, is_entire_result)
        data = xmltodict.parse(xml)
        data = data.get('sales', data.get('info'))
        version = data['@version']
        if 'sale' not in data.keys():
            sales = []
        else:
            sales = data['sale']
        if isinstance(sales, OrderedDict):
            sales = [sales]

        try:
            self._refresh_redis(version, sales, is_entire_result)
        except (RedisError, ConnectionError), e:
            logging.error('Redis Error: %s', (e,), exc_info=True)
        return dict([(sale['@id'], sale) for sale in sales])

    def _refresh_redis(self, version, sales, is_entire_result):
        # save version
        self._set_to_redis(SALES_VERSION, version)
        # parse sales data to get cate/type/shop/brand info.
        sales_all = defaultdict(list)
        cates_info = defaultdict(list)
        types_info = defaultdict(list)
        shops_info = defaultdict(list)
        brands_info = defaultdict(list)
        for sale in sales:
            sale_id = sale['@id']
            cate_id = sale['category']['@id']
            type_id = sale['type']['@id']
            shop_id = sale.get('shop', {}).get('@id', None)
            brand_id = sale['brand']['@id']

            cates_info[cate_id].append(sale_id)
            types_info[type_id].append(sale_id)
            brands_info[brand_id].append(sale_id)
            shops_info[shop_id].append(sale_id)
            sales_all[ALL].append(sale_id)

        # save sales info into redis
        self._save_objs_to_redis(sales)

        # save cate/type/shop/brand info into redis.
        self._save_attrs_to_redis(SALES_FOR_CATEGORY, cates_info)
        self._save_attrs_to_redis(SALES_FOR_TYPE, types_info)
        self._save_attrs_to_redis(SALES_FOR_BRAND, brands_info)
        self._save_attrs_to_redis(SALES_FOR_SHOP, shops_info)
        if is_entire_result:
            self._rem_diff_objs(SALES_ALL, sales_all[ALL])
        self._save_attrs_to_redis(SALES_ALL, sales_all)

    def _del_cached_query(self, obj_id, del_all):
        cli = get_redis_cli()
        pipe = cli.pipeline()
        if del_all:
            invalid_cached_query = cli.keys(SALE_CACHED_QUERY % '*')
            invalid_query = cli.keys(SALES_QUERY % '*')
            for key in invalid_cached_query + invalid_query:
                pipe.delete(key)
        else:
            key = SALE_CACHED_QUERY % obj_id
            query_list = cli.lrange(key, 0, -1)
            for query in query_list:
                s_id_list = ujson.loads(cli.get(query))
                for s_id in s_id_list:
                    pipe.lrem(SALE_CACHED_QUERY % s_id, query, 0)
            for q in query_list:
                pipe.delete(q)
            pipe.delete(key)
        pipe.execute()


class ShopsCacheProxy(CacheProxy):
    list_api = "pub/shops/list?%s"
    obj_api = "pub/shops/info/%s"
    obj_key = SHOP

    @property
    def query_options(self):
        return ('seller', 'city')

    def _get_from_redis(self, **kw):
        # do filters.
        shops_id = set(get_redis_cli().lrange(SHOPS_ALL % ALL, 0, -1))
        shops_id = self._filter_interact(SHOPS_FOR_BRAND,
                                         kw.get('seller'),
                                         shops_id)
        shops_id = self._filter_interact(SHOPS_FOR_CITY,
                                         kw.get('city'),
                                         shops_id)

        shops = {}
        for s_id in shops_id:
            shop = get_redis_cli().get(SHOP % s_id)
            if shop:
                shop = ujson.loads(shop)
                shops[s_id] = shop

        return shops

    def _rem_attrs_for_obj(self, id):
        cli = get_redis_cli()
        shop = cli.get(SHOP % id)
        if not shop:
            cli.lrem(SHOPS_ALL % ALL, id, 0)
            return
        shop = ujson.loads(shop)
        pipe = cli.pipeline()
        pipe.lrem(SHOPS_FOR_BRAND % shop['brand']['@id'], id, 0)
        pipe.lrem(SHOPS_FOR_CITY % shop['city'], id, 0)
        pipe.lrem(SHOPS_ALL % ALL, id, 0)
        pipe.execute()

    def parse_xml(self, xml, is_entire_result):
        logging.info('parse shops xml: %s, is_entire_result:%s',
                     xml, is_entire_result)
        data = xmltodict.parse(xml)
        data = data.get('shops', data.get('info'))

        version = data['@version']
        if 'shop' not in data.keys():
            shops = []
        else:
            shops = data['shop']

        if isinstance(shops, OrderedDict):
            shops = [shops]
        try:
            self._refresh_redis(version, shops, is_entire_result)
        except (RedisError, ConnectionError), e:
            logging.error('Redis Error: %s', (e,), exc_info=True)
        return dict([(shop['@id'], shop) for shop in shops])

    def _refresh_redis(self, version, shops, is_entire_result):
        # save version
        self._set_to_redis(SHOPS_VERSION, version)

        # parse shops data to get brand/city information.
        cities_info = defaultdict(list)
        brands_info = defaultdict(list)
        shops_all = defaultdict(list)
        for shop in shops:
            shop_id = shop['@id']
            city = shop['city']
            brand_id = shop['brand']['@id']

            cities_info[city].append(shop_id)
            brands_info[brand_id].append(shop_id)
            shops_all[ALL].append(shop_id)

        # save shops info into redis
        self._save_objs_to_redis(shops)

        # save city/brand info into redis.
        self._save_attrs_to_redis(SHOPS_FOR_CITY, cities_info)
        self._save_attrs_to_redis(SHOPS_FOR_BRAND, brands_info)
        if is_entire_result:
            self._rem_diff_objs(SHOPS_ALL, shops_all[ALL])
        self._save_attrs_to_redis(SHOPS_ALL, shops_all)


class SalesFindProxy:
    find_api = "pub/sales/find?%s"
    def get(self, query):
        try:
            sales_list = self.get_from_redis(query)
        except (NotExsitError, RedisError, ConnectionError):
            sales_list = self.get_from_remote_server(query)
        return sales_list

    def get_from_redis(self, query):
        query_key = self._get_query_key(query)
        cli = get_redis_cli()
        if not cli.exists(query_key):
            raise NotExsitError('Query cache not exist for: %s' % query_key)
        sales_id = cli.get(query_key)
        return ujson.loads(sales_id)

    def get_from_remote_server(self, query):
        api = self.find_api % query
        logging.info('sales_query: api %s', api)
        req = urllib2.Request(
            settings.SALES_SERVER_API_URL % {'api': api})
        resp = urllib2.urlopen(req)
        sales_list = self.parse_xml("".join(resp.readlines()))
        gevent.spawn(self._save_query_redis, query, sales_list)
        return sales_list

    def _save_query_redis(self, query, sales_id):
        query_key = self._get_query_key(query)
        cli = get_redis_cli()
        cli.set(query_key, ujson.dumps(sales_id))
        for s_id in sales_id:
            cli.rpush(SALE_CACHED_QUERY % s_id, query_key)

    def _get_query_key(self, query):
        return SALES_QUERY % query

    def parse_xml(self, xml):
        sales = sales_cache_proxy.parse_xml(xml, False)
        return sales.keys()


sales_cache_proxy = SalesCacheProxy()
shops_cache_proxy = ShopsCacheProxy()
find_cache_proxy = SalesFindProxy()
