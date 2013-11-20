import logging
import gevent
import settings
import urlparse
import ujson

from common.constants import RESP_RESULT
from common.error import NotExistError
from common.utils import gen_json_response
from models.order import create_order
from models.order import get_order_detail
from models.order import get_orders
from models.order import get_orders_filter_by_mother_brand
from models.order import update_shipping_fee
from models.sale import CachedSale
from models.sale import get_sale_by_barcode
from models.shop import CachedShop
from webservice.base import BaseResource
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from B2SUtils import db_utils
from B2SUtils.db_utils import select
from B2SUtils.errors import ValidationError


class BaseOrderResource(BaseResource):
    def on_post(self, req, resp, conn, **kwargs):
        return gen_json_response(resp,
                                 {'res': RESP_RESULT.F,
                                  'err': 'INVALID_REQUEST'})

    def gen_encrypt_json_resp(self, resp, data_dict):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
            ujson.dumps(data_dict),
            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
            settings.PRIVATE_KEY_PATH)
        return resp


class OrderResource(BaseOrderResource):
    login_required = {'get': False, 'post': True}
    post_action_func_map = {'create': 'order_create'}
    users_id = None

    def _on_post(self, req, resp, conn, **kwargs):
        self.users_id = kwargs.get('users_id')
        action = req.get_param('action')
        if action is None or action not in self.post_action_func_map:
            logging.error('Invalid Order: %s', req.query_string)
            raise ValidationError('ORDER_ERR_INVALID_ACTION')
        func = getattr(self, self.post_action_func_map[action], None)
        assert hasattr(func, '__call__')
        return func(req, resp, conn)

    def order_create(self, req, resp, conn):
        try:
            self._requestValidCheck(conn, req)
            upc_shop = req.get_param('upc_shop')
            if upc_shop:
                return self._posOrder(upc_shop, req, resp, conn)
            else:
                return self._wwwOrder(req, resp, conn)
        except Exception, e:
            logging.error('Create order for %s failed for error: %s',
                          req.query_string, e, exc_info=True)
            return gen_json_response(resp, 0)

    def _posOrder(self, upc_shop, req, resp, conn):
        """ posOrder: CSV string with format
                      barcode,quantity\r\nbarcode,quantity\r\n
        """
        posOrder = req.get_param('posOrder')
        items = posOrder.strip().strip('\\r\\n').split("\\r\\n")
        order_items = []
        id_shop = CachedShop(upc_shop=upc_shop).shop.id
        for item in items:
            order_item = self._posOrderValidCheck(conn, item, id_shop)
            order_items.append(order_item)
        return self._createPosOrder(conn, req, resp, order_items)

    def _createPosOrder(self, conn, req, resp, order_items):
        upc_shop = req.get_param('upc_shop')
        telephone = req.get_param('telephone')
        order_id = create_order(conn, self.users_id, telephone,
                                order_items,  upc_shop=upc_shop)
        return gen_json_response(resp, order_id)


    def _wwwOrder(self, req, resp, conn):
        """ wwwOrder: an urlencoded json array of { "id_sale": xxx, "id_variant": xxx, "quantity": xxx } tuples
        """
        params = urlparse.parse_qs(req.query_string)
        wwwOrder = params.get('wwwOrder', [])
        order_items = []
        for item in wwwOrder:
            order_item = ujson.loads(item)
            self._wwwOrderValidCheck(conn, order_item)
            order_items.append(order_item)
        return self._createWWWOrder(conn, req, resp, order_items)

    def _createWWWOrder(self, conn, req, resp, order_items):
        shipaddr = req.get_param('shipaddr')
        billaddr = req.get_param('billaddr')
        telephone = req.get_param('telephone')
        order_id = create_order(conn, self.users_id, telephone,
                                    order_items, shipaddr=shipaddr,
                                    billaddr=billaddr)
        return gen_json_response(resp, order_id)

    def _requestValidCheck(self, conn, req):
        try:
            assert req.get_param('telephone')
            upc_shop = req.get_param('upc_shop')
            if upc_shop:
                assert req.get_param('posOrder'), 'posOrder'
                self._shopValidCheck(upc_shop=upc_shop)
            else:
                assert req.get_param('wwwOrder'), 'wwwOrder'
                assert req.get_param('shipaddr'), 'shipaddr'
                assert req.get_param('billaddr'), 'billaddr'
                self._addressValidCheck(conn, req.get_param('shipaddr'))
                self._addressValidCheck(conn, req.get_param('billaddr'))
            self._telephoneValidCheck(conn, req.get_param('telephone'))
        except AssertionError, e:
            logging.error('Invalid Order request: %s', req.query_string)
            raise ValidationError('ORDER_ERR_MISSED_PARAM_%s' % e)

    def _posOrderValidCheck(self, conn, order, id_shop):
        barcode, quantity = order.split(',')
        if not barcode or not quantity.isdigit():
            raise ValidationError('ORDER_ERR_WRONG_POS_FORMAT')
        id_sale, id_variant = get_sale_by_barcode(barcode, id_shop)
        self._saleValidCheck(id_sale, id_variant, id_shop, quantity)
        return {'id_sale': id_sale,
                'id_variant': id_variant,
                'quantity': quantity,
                'barcode': barcode}

    def _wwwOrderValidCheck(self, conn, order):
        try:
            try:
                assert order.get('id_shop') is not None, 'id_shop'
                assert order.get('id_sale') is not None, 'id_sale'
                assert order.get('id_variant') is not None, 'id_variant'
                assert order.get('quantity') is not None, 'quantity'
            except AssertionError, e:
                raise

            self._saleValidCheck(order['id_sale'],
                                 order['id_variant'],
                                 order['id_shop'],
                                 order['quantity'])
        except AssertionError, e:
            raise ValidationError('ORDER_ERR_WWW_ORDER_MISSED_%s' % e)

    def _addressValidCheck(self, conn, addr_id):
        where = {'id': addr_id, 'users_id': self.users_id}
        addr = select(conn, 'users_address', where=where)
        if not addr:
            raise NotExistError('ORDER_ERR_ADDR_%s_NOT_EXIST' % addr_id)

    def _telephoneValidCheck(self, conn, id_phone):
        where = {'id': id_phone, 'users_id': self.users_id}
        telephone = select(conn, 'users_phone_num', where=where)
        if not telephone:
            raise NotExistError('ORDER_ERR_PHONE_%s_NOT_EXIST' % id_phone)

    def _shopValidCheck(self, id_shop=None, upc_shop=None):
        if not id_shop and not upc_shop:
            return
        if id_shop and int(id_shop) == 0:
            return

        try:
            assert CachedShop(id_shop, upc_shop), id_shop or upc_shop
        except AssertionError, e:
              raise NotExistError('ORDER_ERR_SHOP_%s_NOT_EXIST' % e)

    def _saleValidCheck(self, id_sale, id_variant, id_shop, quantity):
        sale = CachedSale(id_sale)
        if not sale.valid():
            raise ValidationError('ORDER_ERR_INVALID_SALE_ITEM_%s' % id_sale)
        elif int(id_variant) and not sale.valid_variant(id_variant):
            raise ValidationError('ORDER_ERR_INVALID_SALE_VARIANT_%s' % id_variant)
        elif not sale.valid_shop(id_shop):
            raise ValidationError('ORDER_ERR_INVALID_SALE_SHOP_%s' % id_shop)
        elif int(quantity) <= 0:
            raise ValidationError('ORDER_ERR_INVALID_QUANTITY_%s' % quantity)


class ShippingFeeResource(BaseResource):
    login_required = {'get': False, 'post': False}

    def on_get(self, req, resp, conn, **kwargs):
        return gen_json_response(resp,
                                 {'res': RESP_RESULT.F,
                                  'err': 'INVALID_REQUEST'})

    def on_post(self, req, resp, **kwargs):
        try:
            logging.info('Shipping_fee_request: %s' % req.stream)
            data = decrypt_json_resp(req.stream,
                                     settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                     settings.PRIVATE_KEY_PATH)
            logging.info("Received shipping fee %s" % data)
            data = ujson.loads(data)
        except Exception, e:
            logging.error("Got exceptions when decrypting shipping fee %s" % e,
                          exc_info=True)
            self.gen_resp(resp, {'res': RESP_RESULT.F})
        else:
            self.gen_resp(resp, {'res': RESP_RESULT.S})
            with db_utils.get_conn() as conn:
                gevent.spawn(update_shipping_fee,
                             conn,
                             data['id_shipment'],
                             data['id_postage'],
                             data['shipping_fee'])

    def gen_resp(self, resp, data_dict):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
                            ujson.dumps(data_dict),
                            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                            settings.PRIVATE_KEY_PATH)
        return resp


class OrderListResource(BaseOrderResource):

    def _on_get(self, req, resp, conn, **kwargs):
        mother_brand_id = req.get_param('mother_brand_id')
        if mother_brand_id:
            orders = get_orders_filter_by_mother_brand(conn, mother_brand_id)
        else:
            orders = get_orders(conn)
        #return gen_json_response(resp, orders)
        return self.gen_encrypt_json_resp(resp, orders)


class OrderDetailResource(BaseOrderResource):

    def _on_get(self, req, resp, conn, **kwargs):
        order_id = req.get_param('id')
        mother_brand_id = req.get_param('mother_brand_id')
        order_detail = get_order_detail(conn, order_id, mother_brand_id)
        # return gen_json_response(resp, order_detail)
        return self.gen_encrypt_json_resp(resp, order_detail)


class OrderDeleteResource(BaseOrderResource):
    # A stub function for now, needs to implemented later
    def on_get(self, req, resp, conn, **kwargs):
        return gen_json_response(resp,
                                 {'res': RESP_RESULT.F,
                                  'err': 'INVALID_REQUEST'})



class OrderStatusResource(BaseOrderResource):
    # A stub function for now, needs to implemented later
    def on_get(self, req, resp, conn, **kwargs):
        return gen_json_response(resp,
                                 {'res': RESP_RESULT.F,
                                  'err': 'INVALID_REQUEST'})