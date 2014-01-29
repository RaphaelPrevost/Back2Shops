import logging
import ujson
import xmltodict
from collections import defaultdict
from datetime import datetime

from common.constants import SHIPMENT_STATUS
from common.utils import get_from_sale_server
from common.utils import remote_xml_shipping_fee

from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query
from B2SUtils.db_utils import select
from B2SUtils.db_utils import update
from models.sale import CachedSale
from models.shipping import ActorShipping
from models.shipping_fees import ActorShippingFees

DEFAULT_WEIGHT_UNIT = 'kg'

def create_shipment(conn, id_order, id_shipaddr, id_phone,
                    id_postage=None,
                    shipping_fee=None,
                    supported_services=None):
    if isinstance(supported_services, dict):
        supported_services = ujson.dumps(supported_services)
    sm_values = {
        'id_order': id_order,
        'id_address': id_shipaddr,
        'id_phone': id_phone,
        'status': SHIPMENT_STATUS.PACKING,
        'timestamp': datetime.utcnow(),
        }
    if supported_services:
        sm_values['supported_services'] = supported_services
    if shipping_fee:
        sm_values['shipping_fee'] = shipping_fee
    if id_postage:
        sm_values['id_postage'] = id_postage
    elif (supported_services and
          len(supported_services) == 1 and
          len(supported_services.values()[0]) == 1):
        sm_values['id_postage'] = supported_services.values[0][0]

    sm_id = insert(conn, 'shipments', values=sm_values, returning='id')
    logging.info('shipment create: id: %s, values: %s',
                 sm_id[0], sm_values)
    return sm_id[0]

def _create_shipping_list(conn, id_item, quantity,
                          id_shipment=None, picture=None):
    shipping_value = {
        'id_item': id_item,
        'quantity': quantity,
        }

    if id_shipment:
        shipping_value['id_shipment'] = id_shipment
    if picture:
        shipping_value['picture'] = picture

    insert(conn, 'shipping_list', values=shipping_value)
    logging.info('shipping_list create: %s', shipping_value)

def weight_convert(from_unit, weight):
    #TODO: convert weight value according from unit to DEFAULT_WEIGHT_UNIT
    return weight


class BaseShipments:
    def __init__(self, conn, id_order, order_items, id_telephone, id_shipaddr):
        self.conn = conn
        self.id_order = id_order
        self.id_shipaddr = id_shipaddr
        self.id_telephone = id_telephone
        self.order_items = order_items
        self.dest_addr = None
        self.orig_addr = None


class wwwOrderShipments(BaseShipments):
    def create(self):
        # groups according with internet/local sales.
        internet_sales = []
        local_sales = []

        for item in self.order_items:
            sale = CachedSale(item['id_sale']).sale
            sale.order_props = item
            if sale.shops:
                local_sales.append(sale)
            else:
                internet_sales.append(sale)

        self.handleInternetSales(internet_sales)
        self.handleLocalSales(local_sales)

    def _getShippingInfo(self, sales):
        shipping_sales = []
        for sale in sales:
            shipping_sale = (sale.id,
                             {'variant': sale.order_props['id_variant'],
                              'weight_type': sale.order_props['id_weight_type']})
            shipping_sales.append(shipping_sale)
        query = {'sales': ujson.dumps(shipping_sales)}

        xml_shipping = get_from_sale_server('private/shipping/info', **query)
        shipping_dict = xmltodict.parse(xml_shipping)
        return ActorShipping(shipping_dict['shipping'])

    def populateShippingInfo(self, sales):
        if not sales:
            return
        shipping = self._getShippingInfo(sales)
        settings = defaultdict()
        for setting in shipping.settings:
            key = '-'.join([str(setting.for_),
                            str(setting.variant and setting.variant.id or 0),
                            str((setting.type and
                                 setting.type.attribute and
                                 setting.type.attribute.id) or 0)])
            settings[key] = setting
        for sale in sales:
            key = '-'.join([str(sale.id),
                            str(sale.order_props['id_variant']),
                            str(sale.order_props['id_weight_type'])])
            if settings.get(key) is None:
                # TODO: raise error for this case?
                logging.error('shipping_info_populate_failure: sale - %s', key)
            sale.shipping_setting = settings[key]

    def handleInternetSales(self, sales):
        self.populateShippingInfo(sales)
        # group according with different corporate brands.
        groups = defaultdict(list)
        for sale in sales:
            groups[sale.brand.id].append(sale)
        for grouped_sales in groups.values():
            self.handleSalesByShipping(grouped_sales)
        logging.info('shipment_internet_sales_handled: %s', groups)

    def handleLocalSales(self, sales):
        self.populateShippingInfo(sales)
        # group according with different shops
        groups = defaultdict(list)
        for sale in sales:
            groups[sale.order_props['id_shop']].append(sale)
        for grouped_sales in groups.values():
            self.handleSalesByShipping(grouped_sales)
        logging.info('shipment_local_sales_handled: %s', groups)

    def handleFlatRateShippingSales(self, sales):
        for sale in sales:
            handling_fee = float(sale.shipping_setting.fees.handling.value)
            shipping_fee = float(sale.shipping_setting.fees.shipping.value)

            id_order_item = sale.order_props['id_order_item']
            for _ in range(int(sale.order_props['quantity'])):
                id_shipment = create_shipment(self.conn,
                                self.id_order,
                                self.id_shipaddr,
                                self.id_telephone,
                                shipping_fee=handling_fee + shipping_fee)
                _create_shipping_list(self.conn,
                                      id_order_item,
                                      1,
                                      id_shipment=id_shipment)
        logging.info('shipment_flat_rate_sales_handled: %s', sales)

    def handleGroupCarrierShippingSales(self, sales):
        logging.info('shipment_carrier_sales_group_handling: %s', sales)
        while sales:
            sales = self.groupByMostCommonService(sales)

    def handleCarrierShippingSales(self, sales):
        logging.info('shipment_carrier_sales_separate_handling: %s', sales)
        self.separateShipments(sales)

    def handleGroupCustomShippingSales(self, sales):
        logging.info('shipment_custom_sales_group_handling: %s', sales)
        while sales:
            sales = self.groupByMostCommonService(sales)

    def handleCustomShippingSales(self, sales):
        logging.info('shipment_custom_sales_separate_handling: %s', sales)
        self.separateShipments(sales)

    def handleInvoiceShippingSales(self, sales):
        for sale in sales:
            id_order_item = sale.order_props['id_order_item']
            for _ in range(int(sale.order_props['quantity'])):
                id_shipment = create_shipment(self.conn,
                                              self.id_order,
                                              self.id_shipaddr,
                                              self.id_telephone)
                _create_shipping_list(self.conn,
                                      id_order_item,
                                      1,
                                      id_shipment = id_shipment)

    def handleSalesByShipping(self, sales):
        if not sales:
            return

        free_sales = []
        flat_sales = []
        carrier_sales = []
        carrier_group_sales = []
        custom_sales = []
        custom_group_sales = []
        invoice_sales = []
        for sale in sales:
            op = sale.shipping_setting.options
            allow_group = eval(op.group_shipment.value)
            is_free_shipping = eval(op.free_shipping.value)
            is_flat_rate = eval(op.flat_rate.value)
            is_carrer_shipping_rate = eval(op.carrier_shipping_rate.value)
            is_custom_shipping_rate = eval(op.custom_shipping_rate.value)
            is_invoice_shipping_rate = eval(op.invoice_shipping_rate.value)

            if is_free_shipping:
                free_sales.append(sale)
            elif is_flat_rate:
                flat_sales.append(sale)
            elif is_carrer_shipping_rate and allow_group:
                carrier_group_sales.append(sale)
            elif is_carrer_shipping_rate and not allow_group:
                carrier_sales.append(sale)
            elif is_custom_shipping_rate and allow_group:
                custom_group_sales.append(sale)
            elif is_custom_shipping_rate and not allow_group:
                custom_sales.append(sale)
            elif is_invoice_shipping_rate:
                invoice_sales.append(sale)
            else:
                logging.error('fake_shipping_setting??: sale - %s, '
                              'options - %s',
                              (sale.id, sale.shipping_setting.options))

        logging.info('shipment_sales_by_shipping:'
                      'free_shipping_sales: %s,'
                      'flat_rate_sales: %s,'
                      'carrier_shipping_rate_separate_sales: %s,'
                      'carrier_shipping_rate_group_sales: %s,'
                      'custom_shipping_rate_separate_sales: %s,'
                      'custom_shipping_rate_group_sales: %s,'
                      'invoice_shipping_rate_sales: %s'
                      % (free_sales, flat_sales,
                       carrier_sales, carrier_group_sales,
                       custom_sales, custom_group_sales,
                       invoice_sales))

        self.handleFlatRateShippingSales(flat_sales)
        self.handleCarrierShippingSales(carrier_sales)
        self.handleCustomShippingSales(custom_sales)
        self.handleInvoiceShippingSales(invoice_sales)

        self.handleGroupCarrierShippingSales(carrier_group_sales)
        self.handleGroupCustomShippingSales(custom_group_sales)

    def groupByMostCommonService(self, sales):
        supported_services_count = defaultdict(int)
        service_carrier_map = defaultdict()
        # calculate sales count for each services.
        for sale in sales:
            for service in sale.shipping_setting.supported_services:
                supported_services_count[service] += 1
            service_carrier_map.update(sale.shipping_setting.supported_services)

        # sort services id by count
        service_count_map = supported_services_count.items()
        service_count_map = sorted(service_count_map,
                                   key=lambda x: x[1],
                                   reverse=True)

        group_sales = []
        group_services = []

        # filter out most common services and sales support these services.
        max_count = None
        for id_service, count in service_count_map:
            if max_count is None:
                for sale in sales:
                    sp_servs = sale.shipping_setting.supported_services
                    if id_service in sp_servs:
                        group_sales.append(sale)
                group_services.append(id_service)
                max_count = count
            elif count == max_count:
                same_support = True
                for sale in group_sales:
                    sp_servs = sale.shipping_setting.supported_services
                    if id_service not in sp_servs:
                        same_support = False
                        break
                if same_support:
                    group_services.append(id_service)
                else:
                    break
            else:
                break

        supported_services = dict([(id_service, service_carrier_map[id_service])
                                   for id_service in group_services])

        shipping_fee = None
        if len(group_services) == 1:
            weight = self.totalWeight(group_sales)
            unit = DEFAULT_WEIGHT_UNIT
            dest = self.getDestAddr()
            orig = self.getOrigAddr()
            shipping_fee = self.getShippingFee(
                service_carrier_map[group_services[0]],
                group_services[0],
                weight,
                unit,
                dest,
                orig)
            handling_fee = self.getMaxHandlingFee(group_sales)
            shipping_fee += handling_fee

        id_shipment = create_shipment(self.conn,
                                      self.id_order,
                                      self.id_shipaddr,
                                      self.id_telephone,
                                      shipping_fee=shipping_fee,
                                      supported_services=supported_services)
        for sale in group_sales:
            id_order_item = sale.order_props['id_order_item']
            quantity = sale.order_props['quantity']
            _create_shipping_list(self.conn,
                                  id_order_item,
                                  quantity,
                                  id_shipment=id_shipment)

        return [sale for sale in sales if sale not in group_sales]

    def separateShipments(self, sales):
        for sale in sales:
            service_carrier_map = sale.shipping_setting.supported_services
            shipping_fee = None
            if len(service_carrier_map) == 1:
                weight = self.totalWeight([sale])
                unit = DEFAULT_WEIGHT_UNIT
                dest = self.getDestAddr()
                orig = self.getOrigAddr()
                shipping_fee = self.getShippingFee(
                    service_carrier_map.values()[0],
                    service_carrier_map.keys()[0],
                    weight,
                    unit,
                    dest,
                    orig)
                handling_fee = self.getMaxHandlingFee([sale])
                shipping_fee += handling_fee

            id_order_item = sale.order_props['id_order_item']
            for _ in range(int(sale.order_props['quantity'])):
                id_shipment = create_shipment(self.conn,
                                              self.id_order,
                                              self.id_shipaddr,
                                              self.id_telephone,
                                              shipping_fee=shipping_fee,
                                              supported_services=service_carrier_map)
                _create_shipping_list(self.conn,
                                      id_order_item,
                                      1,
                                      id_shipment=id_shipment)

    def getMaxHandlingFee(self, sales):
        handlings = [float(sale.shipping_setting.fees.handling.value)
                     for sale in sales
                     if sale.shipping_setting.fees.handling.value.isdigit()]
        return handlings and max(handlings) or 0

    def getShippingFee(self, id_carrier, id_service, weight, unit,
                       desc, orig):
        logging.info('shipment_shipping_fee: id_carrier: %s, service: %s', (id_carrier, id_service))
        xml_fee = remote_xml_shipping_fee(
            [(id_carrier, [id_service])],
            weight,
            unit,
            desc,
            orig)
        dict_fee = xmltodict.parse(xml_fee)
        shipping_fee = ActorShippingFees(dict_fee['carriers'])
        return float(shipping_fee.carriers[0].services[0].fee.value)

    def totalWeight(self, sales):
        weight = 0

        for sale in sales:
            sale_weight = float(sale.shipping_setting.weight.value)
            sale_weight_unit = sale.shipping_setting.weight.unit
            if sale_weight_unit != DEFAULT_WEIGHT_UNIT:
                sale_weight = weight_convert(sale_weight_unit, sale_weight)
            weight += sale_weight

        return weight

    def getOrigAddr(self):
        if self.orig_addr is None:
            #TODO: implementation
            self.orig_addr = 'TODO: implememntation'
        return self.orig_addr

    def getDestAddr(self):
        if self.dest_addr is None:
            #TODO: implementation
            self.dest_addr = 'TODO: implememntation'
        return self.dest_addr

