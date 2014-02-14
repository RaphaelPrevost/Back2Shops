import xmltodict

from common.error import NotExistError
from webservice.base import BaseEncryptXmlJsonResource
from models.sale import CachedSale
from models.shipments import get_shipment_fee
from models.shipments import get_shipping_shipments_by_order
from models.shipments import get_supported_services
from models.shipments import get_shipping_list
from models.shipping import ActorCarriers
from models.base_actor import actor_to_dict
from B2SProtocol.settings import SHIPPING_CURRENCY
from B2SProtocol.settings import SHIPPING_WEIGHT_UNIT


class ShipmentListResource(BaseEncryptXmlJsonResource):
    template = "shipping_list.xml"
    def _on_get(self, req, resp, conn, **kwargs):
        id_order = req._params.get('id_order')
        shipment_list = get_shipping_shipments_by_order(conn, id_order)

        for shipment in shipment_list:
            id_shipment = shipment['id']
            shipment['carriers'] = self._get_supported_services(
                                                conn, id_shipment)
            shipment['tracking_info'] = self._get_tracking_info(id_shipment)
            shipment['fee_info'] = get_shipment_fee(conn, id_shipment)
            shipment['shipping_list'] = self._get_shipping_list(
                                                conn, id_shipment)

        return {'object_list': shipment_list,
                'shipping_currency': SHIPPING_CURRENCY,
                'shipping_weight_unit': SHIPPING_WEIGHT_UNIT}

    def _get_supported_services(self, conn, id_shipment):
        xml_supported_services = get_supported_services(conn, id_shipment)
        data = xmltodict.parse(xml_supported_services)
        actor_carriers = ActorCarriers(data=data['carriers'])
        return actor_to_dict(actor_carriers).get('carriers', [])

    def _get_tracking_info(self, id_shipment):
        # TODO: populate tracking info when
        #  shipping status is DELIVER
        pass

    def _get_shipping_list(self, conn, id_shipment):
        r = []

        shipping_list = get_shipping_list(conn, id_shipment)
        for shipping in shipping_list:
            id_sale = shipping['id_sale']
            id_variant = shipping['id_variant']
            id_weight_type = shipping['id_weight_type']
            quantity = shipping['quantity']

            sale = CachedSale(id_sale).sale
            weight = (sale.exist('standard_weight') and
                      getattr(sale, 'standard_weight') or
                      None)

            sel_weight_type = None
            try:
                sel_weight_type = sale.get_type_weight(id_weight_type)
                weight = sel_weight_type.weight
            except NotExistError:
                pass

            sel_variant = None
            try:
                sel_variant = sale.get_variant(id_variant)
            except NotExistError:
                pass

            item = actor_to_dict(sale)
            item['quantity'] = quantity
            item['weight'] = weight
            item['sel_variant'] = (sel_variant and
                                   actor_to_dict(sel_variant) or
                                   None)
            item['sel_weight_type'] = (sel_weight_type and
                                       actor_to_dict(sel_weight_type) or
                                       None)
            shipping['sale_item'] = item
            r.append(shipping)

        return r

