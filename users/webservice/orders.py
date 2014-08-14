import logging
import gevent
import settings
import ujson
import urllib2

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import RESP_RESULT
from B2SRespUtils.generate import gen_json_resp
from B2SUtils import db_utils
from B2SUtils.db_utils import select
from B2SUtils.errors import ValidationError
from common.error import NotExistError
from models.actors.sale import CachedSale
from models.actors.sale import get_sale_by_barcode
from models.actors.shop import CachedShop
from models.order import create_order
from models.order import delete_order
from models.order import get_order
from models.order import get_order_detail
from models.order import get_order_items
from models.order import get_order_status
from models.order import get_orders_list
from models.order import modify_order
from models.order import update_shipping_fee
from models.order import user_accessable_order
from webservice.base import BaseJsonResource


class BaseOrderResource(BaseJsonResource):
    encrypt = True

    def on_post(self, req, resp, **kwargs):
        return gen_json_resp(resp,
                             {'res': RESP_RESULT.F,
                              'err': 'INVALID_REQUEST'})


class OrderResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}
    post_action_func_map = {'create': 'order_create', 'modify': 'order_modify'}
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

    def order_modify(self, req, resp, conn):
        ## check params
        try:
            assert req.get_param('id_order')
            assert req.get_param('telephone')
            assert req.get_param('shipaddr'), 'shipaddr'
            assert req.get_param('billaddr'), 'billaddr'
            self._addressValidCheck(conn, req.get_param('shipaddr'))
            self._addressValidCheck(conn, req.get_param('billaddr'))
            self._telephoneValidCheck(conn, req.get_param('telephone'))
        except AssertionError, e:
            logging.error('Invalid Order request: %s', req.query_string)
            raise ValidationError('ORDER_ERR_MISSED_PARAM_%s' % e)

        shipaddr = req.get_param('shipaddr')
        billaddr = req.get_param('billaddr')
        telephone = req.get_param('telephone')
        id_order = req.get_param('id_order')

        ## Can't modify order which status > AWAITING_PAYMENT
        order_status = get_order_status(conn, id_order)
        if int(order_status) > ORDER_STATUS.AWAITING_PAYMENT:
            logging.warn('The order %s can not be modified because its status '
                         'is %s', id_order, order_satus)
            return 0

        ## return id_order directly if no changes.
        order = get_order(conn, id_order)
        if int(order['id_shipaddr']) == int(shipaddr) and \
                int(order['id_billaddr']) == int(billaddr) and \
                int(order['id_phone']) == int(telephone):
            return int(id_order)

        order_items = get_order_items(conn, id_order)
        items = []
        for item in order_items:
            items.append({
                'id_order_item': item['item_id'],
                'id_shop': item['shop_id'],
                'id_sale': item['sale_id'],
                'id_variant': item['id_variant'],
                'quantity': item['quantity'],
                'id_weight_type': item['id_weight_type'],
                'id_price_type': item['id_price_type']
            })
        return modify_order(conn, self.users_id, id_order, telephone, items,
                            shipaddr, billaddr)

    def order_create(self, req, resp, conn):
        try:
            self._requestValidCheck(conn, req)
            upc_shop = req.get_param('upc_shop')
            if upc_shop:
                id_order = self._posOrder(upc_shop, req, resp, conn)
            else:
                id_order = self._wwwOrder(req, resp, conn)
            return id_order
        except Exception, e:
            conn.rollback()
            logging.error('Create order for %s failed for error: %s',
                          req.query_string, e, exc_info=True)
            return 0

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
        return order_id


    def _wwwOrder(self, req, resp, conn):
        """ wwwOrder: an urlencoded json array:
        [{ "id_sale": xxx,
           "id_variant": xxx,
           "quantity": xxx,
           "id_shop": xxx,
           "id_weight_type": xxx,
           "id_price_type": xxx
           },
         { "id_sale": xxx,
           "id_variant": xxx,
           "quantity": xxx,
           "id_shop": xxx,
           "id_weight_type": xxx,
           "id_price_type": xxx
           }]
        """
        wwwOrder = req.get_param('wwwOrder', '[]')
        wwwOrder = ujson.loads(wwwOrder)
        order_items = []
        for order_item in wwwOrder:
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
        return order_id

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
        barcode, quantity, id_price_type = order.split(',')
        if not barcode or not quantity.isdigit():
            raise ValidationError('ORDER_ERR_WRONG_POS_FORMAT')
        id_sale, id_variant = get_sale_by_barcode(barcode, id_shop)
        self._saleValidCheck(id_sale, id_variant, id_shop, quantity)
        return {'id_sale': id_sale,
                'id_variant': id_variant,
                'id_price_type': int(id_price_type),
                'quantity': quantity,
                'id_shop': id_shop,
                'barcode': barcode,
                'id_weight_type': None}

    def _wwwOrderValidCheck(self, conn, order):
        try:
            try:
                assert order.get('id_shop') is not None, 'id_shop'
                assert order.get('id_sale') is not None, 'id_sale'
                assert order.get('id_variant') is not None, 'id_variant'
                assert order.get('quantity') is not None, 'quantity'
                assert order.get('id_weight_type') is not None, 'id_weight_type'
                assert order.get('id_price_type') is not None, 'id_price_type'
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


class ShippingFeeResource(BaseJsonResource):
    login_required = {'get': False, 'post': False}

    def on_get(self, req, resp, **kwargs):
        return gen_json_resp(resp,
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
        brand_id = req.get_param('brand_id', None)
        if brand_id is None:
            raise ValidationError('INVALID_REQUEST')

        shops_id = req.get_param('shops_id', None)
        if shops_id:
            shops_id = ujson.loads(urllib2.unquote(shops_id))

        orders = get_orders_list(conn, brand_id, shops_id)
        return orders

class OrderList4FUserResource(BaseOrderResource):
    encrypt = False
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, conn, **kwargs):
        brand_id = req.get_param('brand_id', None)
        if brand_id is None:
            raise ValidationError('INVALID_REQUEST')

        orders = get_orders_list(conn, brand_id, [], self.users_id)
        return orders


class OrderDetailResource(BaseOrderResource):

    def _on_get(self, req, resp, conn, **kwargs):
        order_id = req.get_param('id')
        brand_id = req.get_param('brand_id', None)
        if not order_id or brand_id is None:
            raise ValidationError('INVALID_REQUEST')

        shops_id = req.get_param('shops_id', None)
        if shops_id:
            shops_id = ujson.loads(urllib2.unquote(shops_id))

        order_detail = get_order_detail(conn, order_id, brand_id, shops_id)
        return order_detail

class OrderDetail4FUserResource(BaseOrderResource):
    encrypt = False
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, conn, **kwargs):
        order_id = req.get_param('id')
        brand_id = req.get_param('brand_id', None)
        if not order_id or brand_id is None \
                or not user_accessable_order(conn, order_id, self.users_id):
            raise ValidationError('INVALID_REQUEST')

        order_detail = get_order_detail(conn, order_id, brand_id, None)
        return order_detail


class OrderDeleteResource(BaseOrderResource):
    def _on_get(self, req, resp, conn, **kwargs):
        order_id = req.get_param('id')
        if order_id:
            delete_order(conn, order_id)
        return {'res': RESP_RESULT.S}


class OrderStatusResource(BaseOrderResource):
    # A stub function for now, needs to implemented later
    def on_get(self, req, resp, **kwargs):
        return gen_json_resp(resp,
                             {'res': RESP_RESULT.F,
                             'err': 'INVALID_REQUEST'})
