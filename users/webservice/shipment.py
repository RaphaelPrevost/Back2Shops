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
from models.order import order_exist
from models.shipments import create_shipment
from models.shipments import update_or_create_shipping_list
from models.shipments import shipment_item
from models.shipments import get_packing_spl_for_shipment
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

            sp_packing_list = get_packing_spl_for_shipment(conn,
                                                           id_orig_shipment)
            if len(sp_packing_list) > 0:
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
            else:
                id_shipment = id_orig_shipment
                update_shipment(conn,
                                id_shipment,
                                {'calculation_method': SCM.MANUAL,
                                 'status': SHIPMENT_STATUS.PACKING},
                                shipment=orig_shipment)

            # create shipping list.
            for item in content:
                orig_spl_item_id = item['id_shipping_list_item']
                orig_spl_item = get_spl_item_by_id(conn, orig_spl_item_id)
                update_or_create_shipping_list(
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
        tracking_name = self.request.get_param('tracking_name')
        shipping_carrier = self.request.get_param('shipping_carrier')

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
        if tracking_name:
            values['tracking_name'] = tracking_name
        if shipping_carrier is not None:
            values['shipping_carrier'] = shipping_carrier

        if values:
            update_shipment(conn, id_shipment, values)

        values = {}
        if handling_fee:
            values['handling_fee'] = float(handling_fee)
        if shipping_fee:
            values['shipping_fee'] = float(shipping_fee)

        if values:
            update_shipping_fee(conn, id_shipment, values)

    def _update_delivered_shipment(self, conn):
        ''' For delivered shipment, could only update its shipping_date
        and mail_tracking_num.
        '''
        id_shipment = self.request.get_param('shipment')
        shipping_date = self.request.get_param('shipping_date')
        tracking_num = self.request.get_param('tracking')

        values = {}
        if shipping_date:
            if "/" in shipping_date:
                format_ = '%m/%d/%Y'
            else:
                format_ = '%Y-%m-%d'
            sp_date = datetime.datetime.strptime(shipping_date, format_)
            values['shipping_date'] = sp_date
        if tracking_num:
            values['mail_tracking_number'] = tracking_num

        if values:
            update_shipment(conn, id_shipment, values)


    def packing_to_remaining(self, conn, id_shipment, content):
        '''
        Reduce quantity of Packing shipping list items in shipment, make the
        reduced quantity into shipment's remaining list item.

        If there already same order item in current shipment's remaining list,
        just increase the quantity of the related order item's shipping list.

        @param conn: database connection
        @param id_shipment: shipment id which content items belongs to.
        @param content: shipping list items need to be update.
        @return: None
        '''
        for item in content:
            orig_spl_item_id = item['id_shipping_list_item']
            orig_spl_item = get_spl_item_by_id(conn, orig_spl_item_id)

            orig_qty = orig_spl_item['quantity']
            new_qty = int(item['quantity'])

            reduced_qty = orig_qty - new_qty
            if reduced_qty== 0:
                continue

            update_or_create_shipping_list(
                conn,
                item['id_order_item'],
                reduced_qty,
                id_shipment=id_shipment,
                picture=orig_spl_item['picture'],
                free_shipping=orig_spl_item['free_shipping'],
                status=SHIPPING_STATUS.TO_PACKING,
                id_orig_shipping_list=orig_spl_item_id)
            self._update_orig_spl_item(
                conn,
                orig_spl_item_id,
                new_qty)

    def remaining_to_packing(self, conn, id_shipment, content):
        '''
        Packing the items in content.

        If there already same order items in current shipment packing list,
        just update the quantity of the related order item's shipping list.

        @param conn: database connection
        @param id_shipment: shipment id which content items belongs to.
        @param content: shipping list items need to be update.
        @return: None
        '''
        for item in content:
            spl_item_id = item['id_shipping_list_item']
            spl_item = get_spl_item_by_id(conn, spl_item_id)

            qty = spl_item['quantity']
            packing_qty = int(item['quantity'])

            if packing_qty == 0:
                continue

            left_qty = qty - packing_qty

            update_or_create_shipping_list(
                conn,
                item['id_order_item'],
                packing_qty,
                id_shipment=id_shipment,
                picture=spl_item['picture'],
                free_shipping=spl_item['free_shipping'],
                status=SHIPPING_STATUS.PACKING,
                id_orig_shipping_list=spl_item_id)
            self._update_orig_spl_item(
                conn,
                spl_item_id,
                left_qty)

    def shipment_check(self, shipment):
        if not shipment:
            raise UserError(E_C.ERR_ENOENT[0], E_C.ERR_ENOENT[1])

        cur_status = shipment['status']
        new_status = self.request.get_param('status')

        if (cur_status == SHIPMENT_STATUS.DELIVER and
            cur_status != int(new_status)):
            logging.error("Some one trying to change shipment %s "
                          "status from %s to %s", shipment['id'],
                          cur_status, new_status, exc_info=True)
            raise UserError(E_C.ERR_EPERM[0], E_C.ERR_EPERM[1])

    def shipment_update(self, req, resp, conn):
        id_shipment = self.request.get_param('shipment')
        try:
            shipment = get_shipment_by_id(conn, id_shipment)
            self.shipment_check(shipment)

            if int(shipment['status']) == SHIPMENT_STATUS.DELIVER:
                self._update_delivered_shipment(conn)
            else:
                content = self.request.get_param('content')
                remaining_content = self.request.get_param('remaining_content')

                if content:
                    content = ujson.loads(content)
                    self.content_check(conn, content, id_shipment)
                    self.packing_to_remaining(conn, id_shipment, content)
                if remaining_content:
                    remaining_content = ujson.loads(remaining_content)
                    self.content_check(conn, remaining_content, id_shipment)
                    self.remaining_to_packing(conn, id_shipment, remaining_content)

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
            shipment = get_shipment_by_id(conn, id_shipment)
            if not shipment:
                raise UserError(E_C.ERR_ENOENT[0], E_C.ERR_ENOENT[1])
            if int(shipment['status']) == SHIPMENT_STATUS.DELIVER:
                raise UserError(E_C.ERR_EPERM[0], E_C.ERR_EPERM[1])

            # update shipment status to deleted
            values = {'status': SHIPMENT_STATUS.DELETED,
                      'calculation_method': SCM.MANUAL
                      }
            update_shipment(conn, id_shipment, values, shipment=shipment)


            # udpate shipping list status to to_packing.
            where = {'id_shipment': id_shipment}
            values = {'status': SHIPPING_STATUS.TO_PACKING}
            update_shipping_list(conn, where, values)

            return {'res': SUCCESS,
                    'id_shipment': id_shipment}
        except UserError, e:
            logging.error('SPM_CREATE_ERR_%s, order: %s',
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': e.desc}
        except Exception, e:
            logging.error("SERVER_ERR: %s, order:%s",
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': "SERVER_ERROR"}
