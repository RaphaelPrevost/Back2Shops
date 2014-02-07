import logging
import ujson
import xmltodict
from collections import defaultdict
from datetime import datetime

from common.constants import SHIPMENT_STATUS
from common.error import ServerError
from common.utils import get_from_sale_server
from common.utils import remote_xml_shipping_fee

from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query
from B2SUtils.db_utils import select
from B2SUtils.db_utils import update
from models.sale import CachedSale
from models.shipping import ActorShipping
from models.shipping_fees import ActorShippingFees
from models.user import get_user_address

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


OZ_GRAM_CONVERSION = 28.3495231
LB_GRAM_CONVERSION = 453.59237
GRAM_KILOGRAM_CONVERSION = 0.001

def oz_to_gram(weight):
    return weight * OZ_GRAM_CONVERSION

def gram_to_kilogram(weight):
    return weight * GRAM_KILOGRAM_CONVERSION

def lb_to_gram(weight):
    return weight * LB_GRAM_CONVERSION

def weight_convert(from_unit, weight):
    if from_unit == 'kg':
        return weight
    if from_unit == 'oz':
        weight_in_gram = oz_to_gram(weight)
        return gram_to_kilogram(weight_in_gram)
    elif from_unit == 'lb':
        weight_in_gram = oz_to_gram(weight)
        return gram_to_kilogram(weight_in_gram)


class BaseShipments:
    def __init__(self, conn, id_order, order_items,
                 id_telephone, id_shipaddr, id_user):
        self.conn = conn
        self.id_order = id_order
        self.id_shipaddr = id_shipaddr
        self.id_telephone = id_telephone
        self.id_user = id_user
        self.order_items = order_items
        self.dest_addr = None
        self.orig_addr = None

class posOrderShipments(BaseShipments):
    def create(self):
        """ Create fake shipments for posOrder.
        """
        id_shipment = create_shipment(self.conn,
                                      self.id_order,
                                      self.id_shipaddr,
                                      self.id_telephone,
                                      shipping_fee=0)
        for item in self.order_items:
            quantity = item['quantity']
            id_order_item = item['id_order_item']
            _create_shipping_list(self.conn,
                                  id_order_item,
                                  quantity,
                                  id_shipment=id_shipment)


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


    def handleGroupCarrierShippingSales(self, sales, free_sales_group):
        logging.info('shipment_carrier_sales_group_handling: %s', sales)
        self._groupShippingSales(sales, free_sales_group)

    def handleCarrierShippingSales(self, sales):
        logging.info('shipment_carrier_sales_separate_handling: %s', sales)
        self.separateShipments(sales)

    def handleGroupCustomShippingSales(self, sales):
        logging.info('shipment_custom_sales_group_handling: %s', sales)
        self._groupShippingSales(sales, [])

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

    def handleSeparateFreeSales(self, sales):
        for sale in sales:
            id_order_item = sale.order_props['id_order_item']
            handling_fee = self.getMaxHandlingFee([sale])
            for _ in range(int(sale.order_props['quantity'])):
                id_shipment = create_shipment(self.conn,
                                              self.id_order,
                                              self.id_shipaddr,
                                              self.id_telephone,
                                              shipping_fee=handling_fee)
                _create_shipping_list(self.conn,
                                      id_order_item,
                                      1,
                                      id_shipment=id_shipment)

    def handleSalesByShipping(self, sales):
        if not sales:
            return

        free_sales = []
        free_sales_group = []
        flat_sales = []
        carrier_sales = []
        carrier_sales_group = []
        custom_sales = []
        custom_sales_group= []
        invoice_sales = []
        for sale in sales:
            op = sale.shipping_setting.options
            allow_group = eval(op.group_shipment.value)
            is_free_shipping = eval(op.free_shipping.value)
            is_flat_rate = eval(op.flat_rate.value)
            is_carrer_shipping_rate = eval(op.carrier_shipping_rate.value)
            is_custom_shipping_rate = eval(op.custom_shipping_rate.value)
            is_invoice_shipping_rate = eval(op.invoice_shipping_rate.value)

            if is_free_shipping and allow_group:
                free_sales_group.append(sale)
            elif is_free_shipping:
                free_sales.append(sale)
            elif is_flat_rate:
                flat_sales.append(sale)
            elif is_carrer_shipping_rate and allow_group:
                carrier_sales_group.append(sale)
            elif is_carrer_shipping_rate and not allow_group:
                carrier_sales.append(sale)
            elif is_custom_shipping_rate and allow_group:
                custom_sales_group.append(sale)
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
                      'free_shipping_group_sales: %s,'
                      'flat_rate_sales: %s,'
                      'carrier_shipping_rate_separate_sales: %s,'
                      'carrier_shipping_rate_group_sales: %s,'
                      'custom_shipping_rate_separate_sales: %s,'
                      'custom_shipping_rate_group_sales: %s,'
                      'invoice_shipping_rate_sales: %s'
                      % (free_sales, free_sales_group, flat_sales,
                       carrier_sales, carrier_sales_group,
                       custom_sales, custom_sales_group,
                       invoice_sales))

        self.handleFlatRateShippingSales(flat_sales)
        self.handleCarrierShippingSales(carrier_sales)
        self.handleCustomShippingSales(custom_sales)
        self.handleInvoiceShippingSales(invoice_sales)
        self.handleSeparateFreeSales(free_sales)

        self.handleGroupCarrierShippingSales(carrier_sales_group, free_sales_group)
        self.handleGroupCustomShippingSales(custom_sales_group)

    def groupByMostCommonService(self, sales, free_sales_group):
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
        free_sales_fee = None
        if len(group_services) == 1:
            weight = self.totalWeight(group_sales)
            unit = DEFAULT_WEIGHT_UNIT
            dest = self.getDestAddr()
            orig_param = self._getShippingFeeOrigParam(group_sales[0])
            shipping_fee = self.getShippingFee(
                service_carrier_map[group_services[0]],
                group_services[0],
                weight,
                unit,
                dest,
                **orig_param)

            if free_sales_group:
                all_group_sales = []
                all_group_sales.extend(group_sales)
                all_group_sales.extend(free_sales_group)
                weight = self.totalWeight(all_group_sales)
                shipping_fee_with_free_sales = self.getShippingFee(
                    service_carrier_map[group_services[0]],
                    group_services[0],
                    weight,
                    unit,
                    dest,
                    **orig_param)
                free_sales_fee = (float(shipping_fee_with_free_sales) -
                                  float(shipping_fee))

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

        return ([sale for sale in sales if sale not in group_sales],
                free_sales_fee,
                id_shipment)

    def separateShipments(self, sales):
        for sale in sales:
            service_carrier_map = sale.shipping_setting.supported_services
            shipping_fee = None
            if len(service_carrier_map) == 1:
                weight = self.totalWeight([sale])
                unit = DEFAULT_WEIGHT_UNIT
                dest = self.getDestAddr()
                orig_param = self._getShippingFeeOrigParam(sale)
                shipping_fee = self.getShippingFee(
                    service_carrier_map.values()[0],
                    service_carrier_map.keys()[0],
                    weight,
                    unit,
                    dest,
                    **orig_param)
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
                     if sale.shipping_setting.fees.handling.value.replace('.', '', 1).isdigit()]
        return handlings and max(handlings) or 0

    def getShippingFee(self, id_carrier, id_service, weight, unit,
                       desc, id_shop=None, id_corporate_account=None):
        logging.info('shipment_shipping_fee: id_carrier: %s, service: %s', (id_carrier, id_service))
        xml_fee = remote_xml_shipping_fee(
            [(id_carrier, [id_service])],
            weight,
            unit,
            desc,
            id_shop=id_shop,
            id_corporate_account=id_corporate_account)
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

    def _getShippingFeeOrigParam(self, sale):
        """ get sale's shop for local sale or corporate account
            for internet sale.

            sale - ActorSale object.
            return - {'id_shop': $id_shop} for local sale
                     {'id_corporate_account': $id_corporate_account} for
                        internet sale.
        """
        id_shop = int(sale.order_props['id_shop'])
        if id_shop:
            return {'id_shop': id_shop}
        else:
            return {'id_corporate_account': sale.brand.id}

    def getDestAddr(self):
        """ Get destination address according with user and shipping address.
        """
        if self.dest_addr is None:
            user_address = get_user_address(self.conn, self.id_user, self.id_shipaddr)
            if not user_address:
                raise ServerError('shipment_user_dest_addr_not_exist:'
                                  'user: %s, destination address: %s'
                                  % (self.id_user, self.id_shipaddr))
            address = {'address': user_address['address'],
                       'city': user_address['city'],
                       'country': user_address['country_code'],
                       'province': user_address['province_code'],
                       'postalcode': user_address['postal_code']}
            self.dest_addr = ujson.dumps(address)
        return self.dest_addr

    def _shippingListForFreeSalesGroup(self, free_sales_group, spm_id, fee):
        for sale in free_sales_group:
            id_order_item = sale.order_props['id_order_item']
            quantity = sale.order_props['quantity']
            _create_shipping_list(self.conn,
                                  id_order_item,
                                  quantity,
                                  id_shipment=spm_id)
        values = {'id_shipment': spm_id,
                  'fee': fee}
        insert(self.conn, 'free_sales_fee', values=values)

    def _groupShipmentForFreeSales(self, free_sales_group):
        handling_fee = self.getMaxHandlingFee(free_sales_group)
        id_shipment = create_shipment(self.conn,
                                      self.id_order,
                                      self.id_shipaddr,
                                      self.id_telephone,
                                      shipping_fee=handling_fee)
        for sale in free_sales_group:
            id_order_item = sale.order_props['id_order_item']
            quantity = sale.order_props['quantity']
            _create_shipping_list(self.conn,
                                  id_order_item,
                                  quantity,
                                  id_shipment=id_shipment)

    def _groupShippingSales(self, sales, free_sales_group):
        if not sales:
            return
        free_sales_fee = None
        free_sales_shipment = None
        while sales:
            sales, fs_fee, spm_id = self.groupByMostCommonService(sales, free_sales_group)
            if fs_fee is not None:
                if (free_sales_fee is None or
                        (free_sales_fee is not None and
                                 fs_fee < free_sales_fee)):
                    free_sales_fee, free_sales_shipment = fs_fee, spm_id
        if free_sales_fee is not None:
            self._shippingListForFreeSalesGroup(free_sales_group,
                                                free_sales_shipment,
                                                free_sales_fee)
        elif free_sales_group:
            self._groupShipmentForFreeSales(free_sales_group)
