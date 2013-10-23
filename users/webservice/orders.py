import logging
import urlparse
import ujson
from common.cache import shops_cache_proxy
from common.error import ValidationError
from common.utils import gen_json_response
from models.sale import CachedSale
from models.order import create_www_order
from models.order import create_pos_order
from webservice.base import BaseResource


class OrderResource(BaseResource):
    login_required = {'get': False, 'post': True}
    post_action_func_map = {'create': 'order_create'}
    users_id = None

    def on_get(self, req, resp, conn, **kwargs):
        return gen_json_response(resp,
                    {'res': RESP_RESULT.F,
                     'err': 'INVALID_REQUEST'})

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
        upc_shop = req.get_param('upc_shop')
        if upc_shop:
            return self._posOrder(upc_shop, req, resp, conn)
        else:
            return self._wwwOrder(req, resp, conn)

    def _posOrder(self, upc_shop, req, resp, conn):
        """ posOrder: CSV string with format
                      barcode,quantity\r\nbarcode,quantity\r\n
        """
        posOrder = req.get_param('posOrder')
        items = posOrder.strip().strip('\\r\\n').split("\\r\\n")
        order_items = [item.split(',') for item in items]
        return self._createPosOrder(conn, req, resp, order_items)

    def _createPosOrder(self, conn, req, resp, order_items):
        upc_shop = req.get_param('upc_shop')
        order_id = create_pos_order(conn, self.users_id,
                                    upc_shop, order_items)
        return gen_json_response(resp, order_id)


    def _wwwOrder(self, req, resp, conn):
        """ wwwOrder: an urlencoded json array of { "id_sale": xxx, "id_variant": xxx, "quantity": xxx } tuples
        """
        params = urlparse.parse_qs(req.query_string)
        wwwOrder = params.get('wwwOrder', [])
        order_items = []
        for item in wwwOrder:
            order = ujson.loads(item)
            self._orderValidCheck(order)
            order_items.append(order)
        return self._createWWWOrder(conn, req, resp, order_items)

    def _createWWWOrder(self, conn, req, resp, order_items):
        shipaddr = req.get_param('shipaddr')
        billaddr = req.get_param('billaddr')
        order_id = create_www_order(conn, self.users_id, shipaddr,
                                    billaddr, order_items)
        return gen_json_response(resp, order_id)

    def _orderValidCheck(self, order):
        try:
            if not self._validSale(order['id_sale'], order['id_variant']):
                raise ValidationError('ORDER_ERR_INVALID_SALE_ITEM')
            elif int(order['quantity']) <= 0:
                raise ValidationError('ORDER_ERR_INVALID_QUANTITY')
        except ValidationError, e:
            logging.error('Invalid order: order: %s, error: %s', order, e)
            raise

    def _validSale(self, id_sale, id_variant):
        sale = CachedSale(id_sale)
        if int(id_variant):
            return sale.valid_variant(id_variant)
        else:
            return sale.valid()
