import datetime
import logging
import settings
import ujson

from common.constants import SUCCESS
from common.constants import FAILURE
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM
from B2SProtocol.constants import SHIPPING_STATUS
from common.error import UserError
from common.error import ErrorCode as E_C
from webservice.base import BaseJsonResource
from models.actors.sale import CachedSale
from models.order import order_exist
from models.order import order_item_exist
from models.shipments import create_shipment
from models.shipments import create_shipping_list
from models.shipments import update_or_create_shipping_list
from models.shipments import shipment_item
from models.shipments import get_shipment_by_id
from models.shipments import get_spl_item_by_id
from models.shipments import update_shipping_list
from models.shipments import update_shipment
from models.shipments import update_shipping_fee
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp


class ShipmentResource(BaseJsonResource):
    encrypt = True

    post_action_func_map = {'create': 'shipment_create',
                            'modify': 'shipment_update',
                            'delete': 'shipment_delete'}

    def _on_post(self, req, resp, conn, **kwargs):
        data = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                 settings.PRIVATE_KEY_PATH)
        data = ujson.loads(data)
        req._params.update(data)
        action = req.get_param('action')
        if action is None or action not in self.post_action_func_map:
            logging.error('%s: action %s', E_C.ERR_EREQ[1], action)
            return {'res': FAILURE,
                    'err': E_C.ERR_EREQ[1]}
        func = getattr(self, self.post_action_func_map[action], None)
        assert hasattr(func, '__call__')
        return func(req, resp, conn)


    def content_check(self, conn, content, id_orig_shipment):
        if isinstance(content, str):
            content = ujson.loads(content)

        for item in content:
            id_order_item = item.get('id_order_item')
            id_shipping_list_item = item.get('id_shipping_list_item')
            quantity = item.get('quantity')

            assert id_order_item is not None, 'id_order_item'
            assert id_shipping_list_item is not None, 'id_shipping_list_item'
            assert quantity is not None, 'quantity'

            sp_item = shipment_item(conn, id_shipping_list_item)

            # item exist check.
            if not sp_item:
                logging.error("shipment_err: "
                              "shipment item %s doesn't exist"
                              % id_shipping_list_item)
                raise UserError(E_C.ERR_EINVAL[0], E_C.ERR_EINVAL[1])
            sp_item = sp_item[0]

            # order match check.
            if sp_item['id_order_item'] != int(id_order_item):
                logging.error("shipment_err: "
                              "order in request %s doesn't match "
                              "shipment order %s",
                              sp_item['id_order_item'], id_order_item,
                              exc_info=True)
                raise UserError(E_C.ERR_EINVAL[0], E_C.ERR_EINVAL[1])

            # shipment match check.
            if sp_item['id_shipment'] != int(id_orig_shipment):
                logging.error("shipment_err: "
                              "shipment in request %s doesn't match "
                              "%s",
                              id_orig_shipment,
                              sp_item['id_shipment'],
                              exc_info=True)
                raise UserError(E_C.ERR_EINVAL[0], E_C.ERR_EINVAL[1])


            # quantity match check.
            if sp_item['quantity'] < int(quantity):
                logging.error("shipment_err: "
                              "shipping list quantity %s bigger than "
                              "expected %s",
                              quantity,
                              sp_item['quantity'],
                              exc_info=True)
                raise UserError(E_C.ERR_EINVAL[0], E_C.ERR_EINVAL[1])

    def _update_orig_spl_item(self, conn, id_orig_shipping_list, quantity):
        where = {'id': id_orig_shipping_list}
        values = {'quantity': quantity}
        return update_shipping_list(conn, where, values)

    def shipment_create(self, req, resp, conn):
        id_order = self.request.get_param('order')
        if not order_exist(self.conn, id_order):
            logging.error("%s: order %s", E_C.ERR_ENOENT[1], id_order)
            return {'res': FAILURE,
                    'err': E_C.ERR_ENOENT[1]}

        try:
            id_orig_shipment = self.request.get_param('id_orig_shipment')
            content = self.request.get_param('content')
            content = ujson.loads(content)

            self.content_check(conn, content, id_orig_shipment)
            orig_shipment = get_shipment_by_id(conn, id_orig_shipment)

            handling_fee = self.request.get_param('handling_fee')
            shipping_fee = self.request.get_param('shipping_fee')

            # create manually shipment
            id_shipment = create_shipment(
                conn,
                id_order=id_order,
                id_brand=orig_shipment['id_brand'],
                id_shop=orig_shipment['id_shop'],
                status=SHIPMENT_STATUS.PACKING,
                handling_fee=handling_fee,
                shipping_fee=shipping_fee,
                calculation_method=SCM.MANUAL)


            # create shipping list.
            for item in content:
                orig_spl_item_id = item['id_shipping_list_item']
                orig_spl_item = get_spl_item_by_id(conn, orig_spl_item_id)
                create_shipping_list(
                    conn,
                    item['id_order_item'],
                    item['quantity'],
                    id_shipment=id_shipment,
                    picture=orig_spl_item['picture'],
                    free_shipping=orig_spl_item['free_shipping'],
                    id_orig_shipping_list=orig_spl_item_id)
                self._update_orig_spl_item(
                    conn,
                    orig_spl_item_id,
                    orig_spl_item['quantity'] - int(item['quantity']))
            return {'res': SUCCESS,
                    'id_new_shipment': id_shipment}
        except UserError, e:
            logging.error('SPM_CREATE_ERR_%s, order: %s',
                          str(e),
                          id_order,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': e.desc}

        except AssertionError, e:
            logging.error("SPM_CREATE_ERR_MISS_%s, order:%s",
                          str(e),
                          id_order,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': E_C.ERR_EREQ[1],}

        except Exception, e:
            logging.error("SERVER_ERR: %s, order:%s",
                          str(e),
                          id_order,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': "SERVER_ERROR"}

    def _update_shipment(self, conn):
        id_shipment = self.request.get_param('shipment')
        handling_fee = self.request.get_param('handling_fee')
        shipping_fee = self.request.get_param('shipping_fee')
        status = self.request.get_param('status')
        tracking = self.request.get_param('tracking')
        shipping_date = self.request.get_param('shipping_date')

        values = {}
        if status:
            values['status'] = int(status)
        if tracking:
            values['mail_tracking_number'] = tracking
        if shipping_date:
            if "/" in shipping_date:
                format_ = '%m/%d/%Y'
            else:
                format_ = '%Y-%m-%d'
            sp_date = datetime.datetime.strptime(shipping_date, format_)
            values['shipping_date'] = sp_date
        if values:
            update_shipment(conn, id_shipment, values)

        values = {}
        if handling_fee:
            values['handling_fee'] = float(handling_fee)
        if shipping_fee:
            values['shipping_fee'] = float(shipping_fee)

        if values:
            update_shipping_fee(conn, id_shipment, values)

    def shipment_update(self, req, resp, conn):
        id_shipment = self.request.get_param('shipment')
        try:
            content = self.request.get_param('content')
            if content:
                content = ujson.loads(content)
                self.content_check(conn, content, id_shipment)
                # create shipping list.
                for item in content:
                    orig_spl_item_id = item['id_shipping_list_item']
                    orig_spl_item = get_spl_item_by_id(conn, orig_spl_item_id)

                    orig_qty = orig_spl_item['quantity']
                    new_qty = int(item['quantity'])

                    out_qty = orig_qty - new_qty
                    if out_qty == 0:
                        continue

                    update_or_create_shipping_list(
                        conn,
                        item['id_order_item'],
                        out_qty,
                        id_shipment=id_shipment,
                        picture=orig_spl_item['picture'],
                        free_shipping=orig_spl_item['free_shipping'],
                        status=SHIPPING_STATUS.TO_PACKING,
                        id_orig_shipping_list=orig_spl_item_id)
                    self._update_orig_spl_item(
                        conn,
                        orig_spl_item_id,
                        new_qty)

            # update status, shipping fee, handling fee
            self._update_shipment(conn)

            return {'res': SUCCESS,
                    'id_shipment': id_shipment}
        except UserError, e:
            logging.error('SPM_CREATE_ERR_%s, order: %s',
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': e.desc}

        except AssertionError, e:
            logging.error("SPM_CREATE_ERR_MISS_%s, order:%s",
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': E_C.ERR_EREQ[1],}

        except Exception, e:
            logging.error("SERVER_ERR: %s, order:%s",
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': "SERVER_ERROR"}

    def shipment_delete(self, req, resp, conn):
        id_shipment = self.request.get_param('shipment')
        try:
            values = {'status': SHIPMENT_STATUS.DELETED}
            id_shipment = update_shipment(conn, id_shipment, values)
            return {'res': SUCCESS,
                    'id_shipment': id_shipment}
        except Exception, e:
            logging.error("SERVER_ERR: %s, order:%s",
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': "SERVER_ERROR"}
