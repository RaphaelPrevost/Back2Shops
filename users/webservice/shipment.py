# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import datetime
import gevent
import logging
import settings
import ujson

from B2SProtocol.constants import SUCCESS
from B2SProtocol.constants import FAILURE
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM
from common.error import UserError
from common.error import ErrorCode as E_C
from common.utils import push_order_confirmed_event
from webservice.base import BaseJsonResource
from models.order import get_order_status
from models.order import order_exist
from models.order import order_item_quantity
from models.order import _order_need_confirmation
from models.shipments import create_shipment
from models.shipments import create_shipping_list
from models.shipments import decrease_stock
from models.shipments import out_of_stock_errmsg
from models.shipments import order_item_grouped_quantity
from models.shipments import order_item_packing_quantity
from models.shipments import shipping_list_item_quantity
from models.shipments import shipping_list_item_packing_quantity
from models.shipments import stock_req_params
from models.shipments import get_shipment_by_id
from models.shipments import update_shipping_list
from models.shipments import update_shipment
from models.shipments import update_shipping_fee
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp


class ShipmentResource(BaseJsonResource):
    encrypt = True

    post_action_func_map = {'create': 'shipment_create',
                            'modify': 'shipment_update',
                            'delete': 'shipment_delete',
                            'match_check': 'match_check'}

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

    def content_check(self, conn, content, id_shop, id_brand,
                      id_shipment=None):
        if isinstance(content, str):
            content = ujson.loads(content)

        items_id = []
        for item in content:
            id_order_item = item.get('id_order_item')
            quantity = int(item.get('quantity'))
            items_id.append(id_order_item)

            assert id_order_item is not None, 'id_order_item'
            assert quantity is not None, 'quantity'


            orig_packing_quantity = shipping_list_item_packing_quantity(
                conn, id_shipment, id_order_item)
            if orig_packing_quantity is None:
                orig_packing_quantity = 0

            if quantity > orig_packing_quantity:
                item_quantity = order_item_quantity(conn, id_order_item)
                cur_packing = order_item_packing_quantity(conn, id_order_item)

                added_packing = quantity - orig_packing_quantity
                left_packing = item_quantity - cur_packing

                if added_packing > left_packing:
                    logging.error("shipment_err: "
                                  "invalid shipping list quantity %s "
                                  "for order item:%s with shipment %s",
                                  quantity,
                                  id_order_item,
                                  id_shipment,
                                  exc_info=True)
                    raise UserError(E_C.ERR_EINVAL[0], E_C.ERR_EINVAL[1])

        # check items shop/brand is consistence with operator's shop/brand
        from models.order import get_order_items_by_id
        items = get_order_items_by_id(conn, items_id)
        items_shop = []
        items_brand = []
        for item in items:
            items_shop.append(item['id_shop'])
            items_brand.append(item['id_brand'])

        try:
            assert {int(id_shop)} == set(items_shop), ("items shop %s is not "
                                                       "consistence with "
                                                       "operators shop %s"
                                                       % (items_shop, id_shop))
            assert {int(id_brand)} == set(items_brand), ("items brand %s is not "
                                                       "consistence with "
                                                       "operators brand %s"
                                                       % (items_brand, id_brand))
        except AssertionError, e:
            logging.error('spm_content_check_err:%s', e, exc_info=True)
            raise UserError(E_C.ERR_EPERM[0], E_C.ERR_EPERM[1])


    def _update_orig_spl_item(self, conn, id_shipping_list, quantity):
        where = {'id': id_shipping_list}
        values = {'packing_quantity': quantity}
        return update_shipping_list(conn, where, values)

    def shipment_create(self, req, resp, conn):
        id_order = self.request.get_param('order')
        id_shop = self.request.get_param('shop')
        id_brand = self.request.get_param('brand')

        if not order_exist(self.conn, id_order):
            logging.error("%s: order %s", E_C.ERR_ENOENT[1], id_order)
            return {'res': FAILURE,
                    'err': E_C.ERR_ENOENT[1]}

        try:
            content = self.request.get_param('content')
            content = ujson.loads(content)

            self.content_check(conn, content, id_shop, id_brand)

            handling_fee = self.request.get_param('handling_fee')
            shipping_fee = self.request.get_param('shipping_fee')
            packing_status = self.request.get_param('packing_status')
            tracking_name = self.request.get_param('tracking_name')
            tracking_num = self.request.get_param('tracking_num')

            shipping_carrier = self.request.get_param('shipping_carrier')
            shipping_date = self.request.get_param('shipping_date')
            shipping_service = self.request.get_param('shipping_service')

            supported_services = None
            if shipping_service is not None:
                supported_services = {shipping_service: shipping_carrier}

            # create manually shipment
            id_shipment = create_shipment(
                conn,
                id_order,
                id_brand,
                id_shop,
                status=packing_status,
                handling_fee=handling_fee,
                shipping_fee=shipping_fee,
                supported_services=supported_services,
                shipping_date=shipping_date,
                shipping_carrier=shipping_carrier,
                tracking_name=tracking_name,
                calculation_method=SCM.MANUAL,
                tracking_num=tracking_num)

            # create shipping list.
            for item in content:
                id_item = item['id_order_item']
                quantity = item['quantity']
                create_shipping_list(conn, id_item, quantity, quantity,
                                     id_shipment=id_shipment)
            return {'res': SUCCESS,
                    'id_new_shipment': id_shipment}
        except UserError, e:
            conn.rollback()
            logging.error('SPM_CREATE_ERR_%s, order: %s',
                          str(e),
                          id_order,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': e.desc}

        except AssertionError, e:
            conn.rollback()
            logging.error("SPM_CREATE_ERR_MISS_%s, order:%s",
                          str(e),
                          id_order,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': E_C.ERR_EREQ[1],}

        except Exception, e:
            conn.rollback()
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


    def content_update(self, conn, id_shipment, content):
        '''
        Update packing_quantity of shipping_list items.

        @param conn: database connection
        @param id_shipment: shipment id which content items belongs to.
        @param content: shipping list items need to be update.
        @return: None
        '''
        for item in content:
            id_order_item = item['id_order_item']
            quantity = item['quantity']

            where = {'id_item': id_order_item,
                     'id_shipment': id_shipment}
            values = {'packing_quantity': quantity}
            return update_shipping_list(conn, where, values)

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
        id_shop = self.request.get_param('shop')
        id_brand = self.request.get_param('brand')
        try:
            shipment = get_shipment_by_id(conn, id_shipment)
            self.shipment_check(shipment)
            cur_status = shipment['status']
            new_status = self.request.get_param('status')
            shipment_confirmed = (cur_status == SHIPMENT_STATUS.CONFIRMING
                              and new_status not in (SHIPMENT_STATUS.DELETED,
                                                     SHIPMENT_STATUS.CONFIRMING))

            if int(shipment['status']) == SHIPMENT_STATUS.DELIVER:
                self._update_delivered_shipment(conn)
            else:
                content = self.request.get_param('content')
                if content:
                    content = ujson.loads(content)
                    self.content_check(conn, content, id_shop, id_brand,
                                       id_shipment)
                    self.content_update(conn, id_shipment, content)

                # update status, shipping fee, handling fee
                self._update_shipment(conn)

            order_status = get_order_status(conn, shipment['id_order'], id_brand)

            order_need_confirm = _order_need_confirmation(conn,
                                 shipment['id_order'], id_brand)
            if shipment_confirmed:
                params = stock_req_params(conn, id_shipment)
                success, errmsg = decrease_stock(params)
                if not success:
                    raise UserError(E_C.OUT_OF_STOCK[0],
                                    out_of_stock_errmsg(errmsg))

            if shipment_confirmed and not order_need_confirm:
                try:
                    push_order_confirmed_event(conn, shipment['id_order'], id_brand)
                except Exception, e:
                    logging.error('confirmed_event_err: %s, '
                                  'order_id: %s, '
                                  'brand: %s',
                                  e, order_id, brand, exc_info=True)

            return {'res': SUCCESS,
                    'id_shipment': id_shipment,
                    'id_order': shipment['id_order'],
                    'order_status': order_status}
        except UserError, e:
            conn.rollback()
            logging.error('SPM_CREATE_ERR_%s, order: %s',
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': e.desc}

        except AssertionError, e:
            conn.rollback()
            logging.error("SPM_CREATE_ERR_MISS_%s, order:%s",
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': E_C.ERR_EREQ[1],}

        except Exception, e:
            conn.rollback()
            logging.error("SERVER_ERR: %s, order:%s",
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': "SERVER_ERROR"}

    def shipment_delete(self, req, resp, conn):
        id_shipment = self.request.get_param('shipment')
        id_shop = self.request.get_param('shop')
        id_brand = self.request.get_param('brand')
        try:
            shipment = get_shipment_by_id(conn, id_shipment)
            if not shipment:
                raise UserError(E_C.ERR_ENOENT[0], E_C.ERR_ENOENT[1])
            if int(shipment['status']) == SHIPMENT_STATUS.DELIVER:
                raise UserError(E_C.ERR_EPERM[0], E_C.ERR_EPERM[1])
            if int(shipment['id_brand']) != int(id_brand):
                raise UserError(E_C.ERR_EPERM[0], E_C.ERR_EPERM[1])
            if int(shipment['id_shop']) != int(id_shop):
                raise UserError(E_C.ERR_EPERM[0], E_C.ERR_EPERM[1])

            # update shipment status to deleted
            values = {'status': SHIPMENT_STATUS.DELETED,
                      'update_time': datetime.datetime.utcnow()
                      }
            update_shipment(conn, id_shipment, values, shipment=shipment)

            return {'res': SUCCESS,
                    'id_shipment': id_shipment}
        except UserError, e:
            conn.rollback()
            logging.error('SPM_CREATE_ERR_%s, order: %s',
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': e.desc}
        except Exception, e:
            conn.rollback()
            logging.error("SERVER_ERR: %s, order:%s",
                          str(e),
                          id_shipment,
                          exc_info=True)
            return {'res': FAILURE,
                    'err': "SERVER_ERROR"}
