import logging
import gevent
import xmltodict
import ujson
import urllib
import urllib2
from lxml import etree
from StringIO import StringIO
from redis.exceptions import RedisError, ConnectionError

import settings
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SProtocol.constants import ALL
from B2SProtocol.constants import GLOBAL_MARKET
from B2SProtocol.constants import ROUTE
from B2SProtocol.constants import ROUTES_VERSION
from B2SProtocol.constants import ROUTES_FOR_BRAND
from B2SProtocol.constants import SALE
from B2SProtocol.constants import SALES_FOR_TYPE
from B2SProtocol.constants import SALES_FOR_CATEGORY
from B2SProtocol.constants import SALES_FOR_SHOP
from B2SProtocol.constants import SALES_FOR_BRAND
from B2SProtocol.constants import SALES_VERSION
from B2SProtocol.constants import SALES_ALL
from B2SProtocol.constants import TYPE
from B2SProtocol.constants import TYPES_VERSION
from B2SProtocol.constants import TYPES_FOR_BRAND
from B2SProtocol.constants import TAXES_VERSION
from B2SProtocol.constants import TAXES_FOR_FO
from B2SProtocol.constants import SHOP
from B2SProtocol.constants import SHOPS_FOR_BRAND
from B2SProtocol.constants import SHOPS_FOR_CITY
from B2SProtocol.constants import SHOPS_VERSION
from B2SProtocol.constants import SHOPS_ALL
from B2SProtocol.constants import SALE_CACHED_QUERY
from B2SProtocol.constants import SALES_QUERY
from B2SProtocol.constants import BARCODE
from B2SProtocol.constants import BARCODE_ATTR_ID
from B2SProtocol.constants import BARCODE_SALE_ID
from B2SProtocol.constants import BARCODE_VARIANT_ID
from B2SProtocol.constants import SHOP_WITH_BARCODE
from B2SProtocol.constants import INVALIDATE_CACHE_LIST
from B2SProtocol.constants import INVALIDATE_CACHE_OBJ
from common.error import ServerError
from common.redis_utils import get_redis_cli
from models.actors.sale import ActorSale
from B2SUtils.base_actor import as_list


class NotExistError(Exception):
    pass

class NoRedisData(Exception):
    pass

class CacheProxy(object):
    list_api = None
    obj_api = None
    obj_key = None

    LIST_API_VALIDATE_PATH = None
    OBJ_API_VALIDATE_PATH = None
    need_decrypt = False

    def get(self, **kw):
        try:
            return self._get_from_redis(**kw)
        except Exception, e:
            if not isinstance(e, NoRedisData):
                logging.error("Failed to get from Redis: %s", e, exc_info=True)
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
        if self.need_decrypt:
            xmltext = decrypt_json_resp(resp,
                    settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                    settings.PRIVATE_KEY_PATH)
        else:
            xmltext = resp.read()

        is_entire_result = (obj_id is None and query == '')
        valid = self.validate_xml(xmltext, obj_id is None)

        if not valid:
            logging.debug("invalidate xml response: %s", xmltext, exc_info=True)
            raise ServerError("invalidate %s" % api)
        return self.parse_xml(xmltext, is_entire_result, **kw)

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

    def parse_xml(self, xml, is_entire_result, **kw):
        raise NotImplementedError

    def validate_xml(self, xml, list_api):
        _path = self.LIST_API_VALIDATE_PATH if list_api \
                else self.OBJ_API_VALIDATE_PATH
        if not _path:
            return True

        with open(_path) as f:
            dtd_content = f.read()
            f.close()

        xml = xml.strip()
        dtd = etree.DTD(StringIO(dtd_content))
        root = etree.XML(xml)
        rst = dtd.validate(root)
        if not rst:
            logging.error(dtd.error_log.filter_from_errors())
        return rst

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

    LIST_API_VALIDATE_PATH = settings.SALES_VALIDATE_PATH
    OBJ_API_VALIDATE_PATH = settings.SALEINFO_VALIDATE_PATH

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
        act_sale = ActorSale(data=sale)
        pipe = cli.pipeline()
        pipe.lrem(SALES_FOR_CATEGORY % act_sale.category.id, id, 0)
        pipe.lrem(SALES_FOR_TYPE % act_sale.type.id, id, 0)
        pipe.lrem(SALES_FOR_BRAND % act_sale.brand.id, id, 0)
        pipe.lrem(SALES_ALL % ALL, id, 0)
        for shop in act_sale.shops:
            pipe.lrem(SALES_FOR_SHOP % shop.id, id, 0)
            for stocks in act_sale.get_stocks_with_upc():
                key = BARCODE % (stocks.upc, shop.id)
                pipe.delete(key)
        if len(act_sale.shops) == 0:
            for stocks in act_sale.get_stocks_with_upc():
                key = BARCODE % (stocks.upc, GLOBAL_MARKET)
                pipe.delete(key)
        pipe.execute()

    def parse_xml(self, xml, is_entire_result, **kw):
        logging.info('parse sales xml: %s, is_entire_result:%s',
                     xml, is_entire_result)
        data = xmltodict.parse(xml)
        data = data.get('sales', data.get('info'))
        version = data['@version']

        sales = as_list(data.get('sale', None))

        try:
            self._refresh_redis(version, sales, is_entire_result)
        except (RedisError, ConnectionError), e:
            logging.error('Redis Error: %s', (e,), exc_info=True)
        return dict([(sale['@id'], sale) for sale in sales])

    def _refresh_redis(self, version, sales, is_entire_result):
        # save version
        self._set_to_redis(SALES_VERSION, version)
        # save sales info into redis
        self._save_objs_to_redis(sales)

        pipe = get_redis_cli().pipeline()
        for sale in sales:
            act_sale = ActorSale(data=sale)
            sale_id = act_sale.id
            pipe.rpush(SALES_FOR_CATEGORY % act_sale.category.id, sale_id)
            pipe.rpush(SALES_FOR_TYPE % act_sale.type.id, sale_id)
            pipe.rpush(SALES_FOR_BRAND % act_sale.brand.id, sale_id)
            for shop in act_sale.shops:
                pipe.rpush(SALES_FOR_SHOP % shop.id, sale_id)
                # cache sales upc information.
                self._cache_sale_barcodes(pipe, shop.id, act_sale)
            if len(act_sale.shops) == 0:
                self._cache_sale_barcodes(pipe, GLOBAL_MARKET, act_sale)
            pipe.rpush(SALES_ALL % ALL, sale_id)
        pipe.execute()

        if is_entire_result:
            self._rem_diff_objs(SALES_ALL, [s['@id'] for s in sales])

    def _cache_sale_barcodes(self, pipe, shop_id, act_sale):
        for stocks in act_sale.get_stocks_with_upc():
            key = BARCODE % (stocks.upc, shop_id)
            pipe.hset(key, BARCODE_VARIANT_ID, stocks.variant)
            pipe.hset(key, BARCODE_SALE_ID, act_sale.id)
            pipe.hset(key, BARCODE_ATTR_ID, stocks.attribute)

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

    LIST_API_VALIDATE_PATH = settings.SHOPS_VALIDATE_PATH
    OBJ_API_VALIDATE_PATH = settings.SHOPINFO_VALIDATE_PATH

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
        pipe.lrem(SHOPS_FOR_CITY % shop['address']['city'], id, 0)
        pipe.lrem(SHOPS_ALL % ALL, id, 0)
        pipe.delete(SHOP_WITH_BARCODE% id)
        pipe.execute()

    def parse_xml(self, xml, is_entire_result, **kw):
        logging.info('parse shops xml: %s, is_entire_result:%s',
                     xml, is_entire_result)
        data = xmltodict.parse(xml)
        data = data.get('shops', data.get('info'))

        version = data['@version']
        shops = as_list(data.get('shop', None))
        try:
            self._refresh_redis(version, shops, is_entire_result)
        except (RedisError, ConnectionError), e:
            logging.error('Redis Error: %s', (e,), exc_info=True)
        return dict([(shop['@id'], shop) for shop in shops])

    def _refresh_redis(self, version, shops, is_entire_result):
        # save version
        self._set_to_redis(SHOPS_VERSION, version)

        # save shops info into redis
        self._save_objs_to_redis(shops)

        pipe = get_redis_cli().pipeline()
        for shop in shops:
            shop_id = shop['@id']
            city = shop['address']['city']
            brand_id = shop['brand']['@id']

            pipe.rpush(SHOPS_FOR_CITY % city, shop_id)
            pipe.rpush(SHOPS_FOR_BRAND % brand_id, shop_id)
            pipe.rpush(SHOPS_ALL % ALL, shop_id)
            pipe.set(SHOP_WITH_BARCODE % shop['upc'], shop_id)
        pipe.execute()

        if is_entire_result:
            self._rem_diff_objs(SHOPS_ALL, [s['@id'] for s in shops])


class TypesCacheProxy(CacheProxy):
    list_api = "pub/types/list?%s"
    obj_api = "pub/types/info/%s"
    obj_key = TYPE

    @property
    def query_options(self):
        return ('seller')

    def del_obj(self, obj_id):
        pass

    def _rem_attrs_for_obj(self, id):
        pass

    def _get_from_redis(self, **kw):
        brand_id = kw.get('seller')
        types_id = get_redis_cli().lrange(TYPES_FOR_BRAND % brand_id, 0, -1)
        if not types_id:
            raise NoRedisData()

        types = {}
        for t_id in types_id:
            _type = get_redis_cli().get(TYPE % t_id)
            if _type:
                types[t_id] = ujson.loads(_type)

        return types

    def parse_xml(self, xml, is_entire_result, **kw):
        logging.info('parse types xml: %s, is_entire_result:%s',
                     xml, is_entire_result)
        data = xmltodict.parse(xml)
        data = data.get('types', data.get('info'))
        version = data['@version']
        types = as_list(data.get('type', None))

        try:
            self._refresh_redis(version, types, is_entire_result, **kw)
        except (RedisError, ConnectionError), e:
            logging.error('Redis Error: %s', (e,), exc_info=True)

        return dict([(t['@id'], t) for t in types])

    def _refresh_redis(self, version, types, is_entire_result, **kw):
        # save version
        self._set_to_redis(TYPES_VERSION, version)

        brand_id = kw.get('seller')
        if brand_id:
            pipe = get_redis_cli().pipeline()
            for _type in types:
                pipe.rpush(TYPES_FOR_BRAND % brand_id, _type['@id'])
            pipe.expire(TYPES_FOR_BRAND % brand_id, settings.DEFAULT_REDIS_CACHE_TTL)
            pipe.execute()
        self._save_objs_to_redis(types)

class CatesCacheProxy(TypesCacheProxy):
    def refresh(self, obj_id=None):
        # refresh all types and categories
        super(CatesCacheProxy, self).refresh()


class TaxesCacheProxy(CacheProxy):
    list_api = "private/taxes/get?%s"
    need_decrypt = True

    def refresh(self, obj_id=None):
        super(TaxesCacheProxy, self).refresh()

    def del_obj(self, obj_id):
        self.refresh()

    def _get_from_redis(self, **kw):
        taxes = get_redis_cli().get(TAXES_FOR_FO)
        if not taxes:
            raise NoRedisData()
        return dict([(t["@id"], t) for t in ujson.loads(taxes)])

    def _get_query_str(self, **kw):
        return 'showOnFO=true&toCountry='

    def parse_xml(self, xml, is_entire_result, **kw):
        logging.info('parse taxes xml: %s, is_entire_result:%s',
                     xml, is_entire_result)
        data = xmltodict.parse(xml)
        data = data.get('taxes', {})
        version = data['@version']
        taxes = as_list(data.get('tax', None))

        try:
            self._refresh_redis(version, taxes, is_entire_result, **kw)
        except (RedisError, ConnectionError), e:
            logging.error('Redis Error: %s', (e,), exc_info=True)

        return dict([(t['@id'], t) for t in taxes])

    def _refresh_redis(self, version, taxes, is_entire_result, **kw):
        self._set_to_redis(TAXES_VERSION, version)
        get_redis_cli().set(TAXES_FOR_FO, ujson.dumps(taxes))


class RoutesCacheProxy(CacheProxy):
    list_api = "private/routes/list?%s"
    obj_key = ROUTE
    need_decrypt = True

    def refresh(self, brand=None):
        cli = get_redis_cli()
        cli.rpush(INVALIDATE_CACHE_LIST % brand,
                  INVALIDATE_CACHE_OBJ.ROUTES)

    def del_obj(self, brand):
        self.refresh(brand)

    def _del_cached_query(self, brand, del_all):
        cli = get_redis_cli()
        cli.delete(ROUTES_FOR_BRAND % brand)

    @property
    def query_options(self):
        return ('brand')

    def _get_from_redis(self, **kw):
        brand_id = kw.get('brand')
        routes = get_redis_cli().get(ROUTES_FOR_BRAND % brand_id)
        if not routes:
            raise NoRedisData()
        return ujson.loads(routes)

    def parse_xml(self, xml, is_entire_result, **kw):
        data = xmltodict.parse(xml)
        version = data.get('routes').get('@version')

        try:
            self._refresh_redis(version, data, is_entire_result, **kw)
        except (RedisError, ConnectionError), e:
            logging.error('Redis Error: %s', (e,), exc_info=True)

        return data

    def _refresh_redis(self, version, data, is_entire_result, **kw):
        # save version
        self._set_to_redis(ROUTES_VERSION, version)

        brand_id = kw.get('brand')
        if brand_id:
            get_redis_cli().set(ROUTES_FOR_BRAND % brand_id,
                                ujson.dumps(data))


class SalesFindProxy:
    find_api = "pub/sales/find?%s"
    def get(self, query):
        try:
            sales_list = self.get_from_redis(query)
        except (NotExistError, RedisError, ConnectionError):
            sales_list = self.get_from_remote_server(query)
        return sales_list

    def get_from_redis(self, query):
        query_key = self._get_query_key(query)
        cli = get_redis_cli()
        if not cli.exists(query_key):
            raise NotExistError('Query cache not exist for: %s' % query_key)
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

sale_cache_proxy = SalesCacheProxy()
shop_cache_proxy = ShopsCacheProxy()
find_cache_proxy = SalesFindProxy()
type_cache_proxy = TypesCacheProxy()
cate_cache_proxy = CatesCacheProxy()
tax_cache_proxy = TaxesCacheProxy()
route_cache_proxy = RoutesCacheProxy()
