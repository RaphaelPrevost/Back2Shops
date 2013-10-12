import logging
import xmltodict
import ujson
import urllib2
from collections import defaultdict
from collections import OrderedDict
from redis.exceptions import RedisError

import settings
from common.constants import RESP_RESULT
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

class CacheProxy:
    api = None
    obj_key = None

    def get(self, **kw):
        raise NotImplementedError

    def refresh(self):
        try:
            result = self._get_from_server()
        except Exception, e:
            logging.error('Server Error: %s', (e,), exc_info=True)
            return '<res error="SERVER_ERR">%s</res>' % RESP_RESULT.F
        else:
            self._parse_xml(result)
        return result

    def _save_to_redis(self, name, value):
        logging.info('save to redis: %s', name)
        try:
            get_redis_cli().set(name, value)
        except RedisError, e:
            logging.error('Redis Error: %s', (e,), exc_info=True)

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
        try:
            pipe = get_redis_cli().pipeline()
            for id, values in data.iteritems():
                if id is None:
                    continue
                pipe.rpush(key % id, *values)
            pipe.execute()
        except RedisError, e:
            logging.error('Redis Error: %s', (e,), exc_info=True)

    def _save_objs_to_redis(self, data_list):
        """ save parsed xml data list into redis.
        data_list: OrderedDict list.
             dict in the list must contain key '@id'.
        """
        if not data_list:
            return
        try:
            pipe = get_redis_cli().pipeline()
            for data in data_list:
                data_id = data['@id']
                data_str = ujson.dumps(data)
                name = self.obj_key % data_id
                self._rem_attrs_for_obj(data_id)
                pipe.set(name, data_str)
            pipe.execute()
        except RedisError, e:
            logging.error('Redis Error: %s', (e,), exc_info=True)


    def _get_from_server(self):
        logging.info('fetch from sales server : %s', self.api)
        req = urllib2.Request(
            settings.SALES_SERVER_API_URL % {'api': self.api})
        resp = urllib2.urlopen(req)
        return "".join(resp.readlines())

    def _parse_xml(self, xml):
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
        get_redis_cli().delete(*objs_name)


class SalesCacheProxy(CacheProxy):
    api = "pub/sales/list"
    obj_key = SALE

    def get(self, **kw):
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
        sale = get_redis_cli().get(SALE % id)
        if not sale:
            return
        sale = ujson.loads(sale)
        try:
            pipe = get_redis_cli().pipeline()
            pipe.lrem(SALES_FOR_CATEGORY % sale['category']['@id'], id, 0)
            pipe.lrem(SALES_FOR_TYPE % sale['type']['@id'], id, 0)
            pipe.lrem(SALES_FOR_BRAND % sale['brand']['@id'], id, 0)
            pipe.lrem(SALES_ALL % ALL, id, 0)
            if sale.get('shop'):
                pipe.lrem(SALES_FOR_SHOP % sale['shop']['@id'], id, 0)
            pipe.execute()
        except RedisError, e:
            logging.error('Redis Error: %s', (e,), exc_info=True)

    def _parse_xml(self, xml):
        data = xmltodict.parse(xml)['sales']

        # save version
        version = data['@version']
        self._save_to_redis(SALES_VERSION, version)
        if 'sale' not in data.keys():
            sales = []
        else:
            sales = data['sale']

        # parse sales data to get cate/type/shop/brand info.
        if isinstance(sales, OrderedDict):
            sales = [sales]
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
        self._rem_diff_objs(SALES_ALL, sales_all[ALL])
        self._save_attrs_to_redis(SALES_ALL, sales_all)

class ShopsCacheProxy(CacheProxy):
    api = "pub/shops/list"
    obj_key = SHOP

    def get(self, **kw):
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
        shop = get_redis_cli().get(SHOP % id)
        if not shop:
            return
        shop = ujson.loads(shop)
        try:
            pipe = get_redis_cli().pipeline()
            pipe.lrem(SHOPS_FOR_BRAND % shop['brand']['@id'], id, 0)
            pipe.lrem(SHOPS_FOR_CITY % shop['city'], id, 0)
            pipe.lrem(SHOPS_ALL % ALL, id, 0)
            pipe.execute()
        except RedisError, e:
            logging.error('Redis Error: %s', (e,), exc_info=True)

    def _parse_xml(self, xml):
        data = xmltodict.parse(xml)['shops']

        # save version
        version = data['@version']
        self._save_to_redis(SHOPS_VERSION, version)
        if 'shop' not in data.keys():
            shops = []
        else:
            shops = data['shop']

        # parse shops data to get brand/city information.
        if isinstance(shops, OrderedDict):
            shops = [shops]
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
        self._rem_diff_objs(SHOPS_ALL, shops_all[ALL])
        self._save_attrs_to_redis(SHOPS_ALL, shops_all)

sales_cache_proxy = SalesCacheProxy()
shops_cache_proxy = ShopsCacheProxy()
