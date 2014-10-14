import xmltodict
import ujson

from common.error import UserError
from common.error import ErrorCode as E_C
from common.utils import remote_xml_shipping_services
from common.utils import weight_convert
from common.utils import remote_xml_shipping_fee
from models.actors.sale import CachedSale
from models.actors.shipping import ActorCarriers
from models.shipments import get_shipping_supported_services
from models.shipments import get_shipping_list
from models.user import get_user_dest_addr
from B2SProtocol.settings import SHIPPING_WEIGHT_UNIT
from B2SUtils.base_actor import actor_to_dict


class BaseShippingFees(object):
    def __init__(self, conn, id_user, id_carrier=None, id_service=None):
        self.conn = conn
        self.id_user = id_user
        self.id_carrier = id_carrier
        self.id_service = id_service

    def _get_sale_address(self, sale, id_shop):
        if int(id_shop):
            id_address = sale.get_shop(id_shop).id_address
        else:
            id_address = sale.brand.id_address
        return id_address


class SaleShippingFees(BaseShippingFees):
    def __init__(self, conn, id_user, id_sale, id_weight_type, id_shop,
                 id_carrier=None, id_service=None):
        super(SaleShippingFees, self).__init__(
            conn, id_user, id_carrier, id_service)
        self.id_sale = id_sale
        self.id_weight_type = id_weight_type
        self.id_shop = id_shop

    def get(self):
        if self.id_weight_type is None or self.id_shop is None:
            raise UserError(E_C.SSF_MISS_PARAM[0],
                            E_C.SSF_MISS_PARAM[1] % self.id_sale)

        sale = CachedSale(self.id_sale).sale
        supported_services = self._get_supported_service()
        id_address = self._get_sale_address(sale, self.id_shop)
        weight_unit = SHIPPING_WEIGHT_UNIT
        dest = ujson.dumps(get_user_dest_addr(self.conn, self.id_user))
        weight = self._get_sale_weight(sale)

        return remote_xml_shipping_fee(supported_services,
                                       weight,
                                       weight_unit,
                                       dest,
                                       id_address)

    def _get_sale_weight(self, sale):
        if int(self.id_weight_type):
            return sale.get_weight_attr(self.id_weight_type).weight.value
        else:
            return sale.standard_weight

    def _get_supported_service(self):
        supported_services = self._get_sale_supported_services()

        if self.id_carrier is not None and self.id_service is not None:
            services = supported_services.get(self.id_carrier, [])
            if self.id_service not in services:
                raise UserError(E_C.SSF_NOT_SUPPORT_SERVICE[0],
                                E_C.SSF_NOT_SUPPORT_SERVICE[1] % (
                                    self.id_sale,
                                    self.id_carrier,
                                    self.id_service))
            else:
                supported_services = {self.id_carrier: [self.id_service]}

        return supported_services.items()

    def _get_sale_supported_services(self):
        xml_supported_services = remote_xml_shipping_services(
            id_sale=self.id_sale)
        data = xmltodict.parse(xml_supported_services)
        actor_carriers = ActorCarriers(data=data['carriers'])
        carriers = actor_to_dict(actor_carriers).get('carriers', [])
        return dict([[carrier['id'],
                      [s['id'] for s in carrier['services']]]
                     for carrier in carriers])


class ShipmentShippingFees(BaseShippingFees):
    def __init__(self, conn, id_user, id_shipment,
                 id_carrier=None, id_service=None,
                 with_free_shipping_fee=False):
        super(ShipmentShippingFees, self).__init__(
            conn, id_user, id_carrier, id_service)
        self.id_shipment = id_shipment
        self.with_free_shipping_fee = with_free_shipping_fee

    def get(self):
        supported_services = self._get_supported_service()
        weight_unit = SHIPPING_WEIGHT_UNIT
        dest = ujson.dumps(get_user_dest_addr(self.conn, self.id_user))
        weight, weight_with_free, amount, amount_with_free, \
                    id_address = self._get_weight_and_address()
        if not self.with_free_shipping_fee:
            return remote_xml_shipping_fee(supported_services,
                                           weight,
                                           weight_unit,
                                           dest,
                                           id_address)
        else:
            xml_fee = remote_xml_shipping_fee(supported_services,
                                           weight,
                                           weight_unit,
                                           dest,
                                           id_address)
            xml_fee_with_free = None
            if weight_with_free:
                xml_fee_with_free = remote_xml_shipping_fee(
                    supported_services,
                    weight_with_free,
                    weight_unit,
                    dest,
                    id_address)
            return xml_fee, xml_fee_with_free

    def _get_supported_service(self):
        supported_services = dict(get_shipping_supported_services(
            self.conn, self.id_shipment))

        if (self.id_carrier is not None and
            self.id_service is not None):
            services = supported_services.get(self.id_carrier, [])
            if self.id_service not in services:
                raise UserError(E_C.SPSF_NOT_SUPPORT_SERVICE[0],
                                E_C.SPSF_NOT_SUPPORT_SERVICE[1] % (
                                    self.id_shipment,
                                    self.id_carrier,
                                    self.id_service))
            else:
                supported_services = {self.id_carrier: [self.id_service]}

        return supported_services.items()

    def _get_weight_and_address(self):
        shipping_list = get_shipping_list(self.conn, self.id_shipment)
        spm_weight = 0
        spm_weight_with_free = 0
        id_address = None

        total_amount = 0
        total_amount_with_free = 0
        for shipping in shipping_list:
            if (shipping['free_shipping'] and
                    not self.with_free_shipping_fee):
                continue
            id_sale = shipping['id_sale']
            sale = CachedSale(id_sale).sale
            weight = sale.standard_weight or None
            id_weight_type = shipping['id_weight_type']
            quantity = shipping['quantity']

            if weight is None:
                sel_weight_type = sale.get_weight_attr(id_weight_type)
                weight = sel_weight_type.weight.value

            weight = weight_convert(sale.weight_unit,
                                    float(weight)) * quantity
            if not shipping['free_shipping']:
                spm_weight += weight
            if self.with_free_shipping_fee:
                spm_weight_with_free += weight

            # All shipping list have same orig address
            if id_address is None:
                id_address = self._get_sale_address(sale,
                                                    shipping['id_shop'])

            amount = sale.final_price(shipping['id_variant'],
                                      shipping['id_price_type'])
            if not shipping['free_shipping']:
                total_amount += amount * quantity
            if self.with_free_shipping_fee:
                total_amount_with_free += amount * quantity

        return spm_weight, spm_weight_with_free, \
               total_amount, total_amount_with_free, id_address

