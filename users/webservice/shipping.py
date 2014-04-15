import logging
import xmltodict

from common.constants import SUCCESS
from common.constants import FAILURE
from common.error import NotExistError
from common.error import UserError
from common.error import ErrorCode as E_C
from common.utils import weight_convert
from webservice.base import BaseResource
from webservice.base import BaseXmlResource
from webservice.base import BaseJsonResource
from models.actors.shipping_fees import ActorShippingFees
from models.order import get_order
from models.order import get_order_items
from models.order import _get_order_status
from models.order import user_accessable_order
from models.actors.sale import CachedSale
from models.actors.shipping import ActorCarriers
from models.shipments import conf_shipping_service
from models.shipments import get_shipping_fee
from models.shipments import get_shipments_by_order
from models.shipments import order_item_grouped_quantity
from models.shipments import remote_get_supported_services
from models.shipments import get_shipment_paid_time
from models.shipments import get_shipping_supported_services
from models.shipments import get_shipping_list
from models.shipments import get_shipping_postage
from models.shipments import user_accessable_shipment
from models.shipping_fees import SaleShippingFees
from models.shipping_fees import ShipmentShippingFees
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM
from B2SProtocol.settings import SHIPPING_CURRENCY
from B2SProtocol.settings import SHIPPING_WEIGHT_UNIT
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SRespUtils.generate import gen_xml_resp
from B2SUtils.base_actor import actor_to_dict


class BaseShippingListResource(BaseXmlResource):
    template = "shipping_list.xml"
    def _on_get(self, req, resp, conn, **kwargs):
        try:
            self._order_check(conn)
        except UserError, e:
            logging.error("%s" % str(e), exc_info=True)
            return {"error": e.code}

        id_order = req._params.get('id_order')
        order_status = _get_order_status(conn, id_order)
        order_create_date = self._get_order_create_date(conn, id_order)

        shipment_list = get_shipments_by_order(conn, id_order)

        object_list = []
        for shipment in shipment_list:
            if shipment['status'] == SHIPMENT_STATUS.DELETED:
                continue
            id_shipment = shipment['id']
            shipment['carriers'] = self._get_supported_services(
                                                conn, shipment)
            shipment['tracking_info'] = self._get_tracking_info(id_shipment)
            shipment['fee_info'] = self._get_shipping_fee(conn,
                                                          shipment['id'])
            shipment['shipping_list'] = self._get_shipping_list(
                                                conn, id_shipment)
            shipment['postage'] = get_shipping_postage(conn, id_shipment)

            if int(order_status) == ORDER_STATUS.AWAITING_SHIPPING:
                paid_time = get_shipment_paid_time(conn,
                                                   id_shipment)['paid_time']
                shipment['paid_date'] = paid_time.date()

            object_list.append(shipment)

        unpacking_list = self._get_unpacking_shipment(conn, id_order)
        object_list.extend(unpacking_list)
        return {'object_list': object_list,
                'order_status': order_status,
                'order_create_date': order_create_date,
                'shipping_currency': SHIPPING_CURRENCY,
                'shipping_weight_unit': SHIPPING_WEIGHT_UNIT}

    def _on_post(self, req, resp, conn, **kwargs):
        return self._on_get(req, resp, conn, **kwargs)

    def _get_order_create_date(self, conn, id_order):
        order = get_order(conn, id_order)
        return  order['confirmation_time'].date()

    def _get_shipping_fee(self, conn, id_shipment):
        try:
            return get_shipping_fee(conn, id_shipment)
        except AssertionError:
            pass

    def _get_unpacking_shipment(self, conn, id_order):
        order_items = get_order_items(conn, id_order)
        shop_shipment = {}

        for order_item in order_items:
            id_order_item = order_item['item_id']
            quantity = order_item['quantity']
            grouped_quantity = order_item_grouped_quantity(
                conn, id_order_item)
            if quantity == grouped_quantity:
                continue
            elif quantity < grouped_quantity:
                logging.error("shipment_group_err: grouped item quantity "
                              "bigger than orig item quantity for order "
                              "item %s", id_order_item)
                continue
            id_shop = order_item['shop_id']
            id_sale = order_item['sale_id']
            if shop_shipment.get(id_shop) is None:
                id_brand = CachedSale(id_sale).sale.brand.id
                shop_shipment[id_shop] = {
                    'id': 0,
                    'calculation_method': SCM.MANUAL,
                    'id_brand': id_brand,
                    'id_shop': id_shop,
                    'status': SHIPMENT_STATUS.PACKING,
                    'shipping_list': []
                }

            sale_item = self._gen_shipping_sale_item(
                order_item['sale_id'],
                order_item['id_variant'],
                order_item['id_weight_type'],
                quantity-grouped_quantity,
                0)
            shipping = {'id_sale': order_item['sale_id'],
                        'id_item': order_item['item_id'],
                        'sale_item': sale_item}
            shop_shipment[id_shop]['shipping_list'].append(shipping)
        return shop_shipment.values()

    def _get_supported_services(self, conn, shipment):
        cal_method = shipment['calculation_method']
        if cal_method not in [SCM.CARRIER_SHIPPING_RATE,
                              SCM.CUSTOM_SHIPPING_RATE]:
            return []
        id_shipment= shipment['id']
        xml_supported_services = remote_get_supported_services(
            conn, id_shipment)
        data = xmltodict.parse(xml_supported_services)
        actor_carriers = ActorCarriers(data=data['carriers'])
        return actor_to_dict(actor_carriers).get('carriers', [])

    def _get_tracking_info(self, id_shipment):
        # TODO: populate tracking info when
        #  shipping status is DELIVER
        pass

    def _gen_shipping_sale_item(self, id_sale, id_variant, id_weight_type,
                                quantity, packing_quantity):
        sale = CachedSale(id_sale).sale

        weight = sale.standard_weight or None

        sel_weight_type = None
        try:
            sel_weight_type = sale.get_weight_attr(id_weight_type)
            weight = sel_weight_type.weight.value
        except NotExistError:
            pass

        sel_variant = None
        try:
            sel_variant = sale.get_variant(id_variant)
        except NotExistError:
            pass

        weight = weight_convert(sale.weight_unit, weight) * quantity
        item = actor_to_dict(sale)
        item['quantity'] = quantity
        item['packing_quantity'] = packing_quantity
        item['weight'] = weight
        item['sel_variant'] = (sel_variant and
                               actor_to_dict(sel_variant) or
                               None)
        item['sel_weight_type'] = (sel_weight_type and
                                   actor_to_dict(sel_weight_type) or
                                   None)
        return item

    def _get_shipping_list(self, conn, id_shipment):
        r = []

        shipping_list = get_shipping_list(conn, id_shipment)
        for shipping in shipping_list:
            item = self._gen_shipping_sale_item(
                shipping['id_sale'],
                shipping['id_variant'],
                shipping['id_weight_type'],
                shipping['quantity'],
                shipping['packing_quantity'])

            shipping['sale_item'] = item
            r.append(shipping)

        return r

    def _order_check(self, conn):
        pass


class ShippingListResource(BaseShippingListResource):
    encrypt = True

class PubShippingListResource(BaseShippingListResource):
    encrypt = False
    login_required = {'get': True, 'post': True}

    def _on_get(self, req, resp, conn, **kwargs):
        self.users_id = kwargs.get('users_id')
        return super(PubShippingListResource, self)._on_get(
            req, resp, conn, **kwargs)

    def _order_check(self, conn):
        id_order = self.request._params.get('id_order')
        if not user_accessable_order(conn, id_order, self.users_id):
            raise UserError(E_C.PSPL_PRIORITY_ERROR[0],
                            E_C.PSPL_PRIORITY_ERROR[1] % (id_order,
                                                          self.users_id))

class ShippingFeesResource(BaseResource):
    login_required = {'get': True, 'post': False}
    def gen_resp(self, resp, data):
        if isinstance(data, dict) and 'error' in data:
            return gen_xml_resp('error.xml', resp, **data)
        resp.body = data
        resp.content_type = "application/xml"
        return resp

    def _on_get(self, req, resp, conn, **kwargs):
        try:
            id_sale = self.request._params.get('sale')
            id_shipment = self.request._params.get('shipment')
            id_carrier = self.request._params.get('carrier')
            id_service = self.request._params.get('service')
            if not id_sale and not id_shipment:
                raise UserError(E_C.SF_MISS_PARAMS[0],
                                E_C.SF_MISS_PARAMS[1])
            if id_sale:
                id_weight_type = self.request._params.get('weight_type')
                id_shop = self.request._params.get('shop')
                return SaleShippingFees(conn,
                                        self.users_id,
                                        id_sale,
                                        id_weight_type,
                                        id_shop,
                                        id_carrier,
                                        id_service).get()
            else:
                return ShipmentShippingFees(conn,
                                            self.users_id,
                                            id_shipment,
                                            id_carrier,
                                            id_service).get()
        except UserError, e:
            logging.error("%s" % str(e))
            return {'error': e.code}


class ShippingConfResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _request_verify(self):
        id_shipment = self.request._params.get('shipment')
        id_carrier = self.request._params.get('carrier')
        id_service = self.request._params.get('service')

        try:
            assert id_shipment is not None, 'shipment'
            assert id_carrier is not None, 'carrier'
            assert id_service is not None, 'service'
        except AssertionError, e:
            raise UserError(E_C.SP_MISS_PARAMS[0],
                            E_C.SP_MISS_PARAMS[1] % e)

        if not user_accessable_shipment(self.conn,
                                        id_shipment,
                                        self.users_id):
            raise UserError(E_C.SP_PRIORITY_ERROR[0],
                            E_C.SP_PRIORITY_ERROR[1] % (self.users_id,
                                                          id_shipment))

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            self._request_verify()
            id_shipment = self.request._params.get('shipment')
            id_carrier = self.request._params.get('carrier')
            id_service = self.request._params.get('service')
            supported_services = get_shipping_supported_services(
                self.conn, id_shipment)
            supported_services = dict(supported_services)

            if (id_carrier not in supported_services or
                id_service not in supported_services.get(id_carrier, [])):
                raise UserError(E_C.SP_INVALID_SERVICE[0],
                                E_C.SP_INVALID_SERVICE[1] % (id_shipment,
                                                             id_carrier,
                                                             id_service))

            fee, fee_with_free = self._get_shipping_fee(id_shipment,
                                                        id_carrier,
                                                        id_service)
            fee_for_free = None
            if fee_with_free:
                fee_for_free = fee_with_free - fee

            conf_shipping_service(self.conn, id_shipment, id_service,
                                  fee, fee_for_free)

            return SUCCESS
        except UserError, e:
            logging.error("%s" % str(e), exc_info=True)
            return {FAILURE: e.code}

    def _get_shipping_fee(self, id_shipment, id_carrier, id_service):
        xml_fee, xml_fee_with_free = ShipmentShippingFees(self.conn,
                                    self.users_id,
                                    id_shipment,
                                    id_carrier,
                                    id_service,
                                    with_free_shipping_fee=True).get()

        fee = self._get_fee_value(xml_fee)
        fee_with_free = None
        if xml_fee_with_free:
            self._get_fee_value(xml_fee_with_free)
        return fee, fee_with_free

    def _get_fee_value(self, xml_fee):
        dict_fee = xmltodict.parse(xml_fee)
        actor_fee = ActorShippingFees(dict_fee['carriers'])
        return float(actor_fee.carriers[0].services[0].fee.value)

