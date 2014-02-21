import logging
import ujson
import xmltodict
from collections import defaultdict
from datetime import datetime

from common.error import ServerError
from common.utils import get_from_sale_server
from common.utils import remote_xml_shipping_fee
from common.utils import remote_xml_shipping_services
from common.utils import weight_convert

from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS
from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query
from B2SUtils.db_utils import update
from models.actors.sale import CachedSale
from models.actors.shipping_fees import ActorShippingFees
from models.actors.shipping import ActorShipping
from models.user import get_user_dest_addr

DEFAULT_WEIGHT_UNIT = 'kg'

def create_shipment(conn, id_order, id_shipaddr, id_phone,
                    handling_fee=None,
                    shipping_fee=None,
                    supported_services=None,
                    calculation_method=None):
    sm_values = {
        'id_order': id_order,
        'id_address': id_shipaddr,
        'id_phone': id_phone,
        'status': SHIPMENT_STATUS.PACKING,
        'timestamp': datetime.utcnow(),
        }
    if calculation_method is not None:
        sm_values['calculation_method'] = calculation_method

    sm_id = insert(conn, 'shipments', values=sm_values, returning='id')
    logging.info('shipment created: id: %s, values: %s',
                 sm_id[0], sm_values)

    if handling_fee is not None or shipping_fee is not None:
        _add_shipping_fee(conn, sm_id[0], handling_fee, shipping_fee)

    if supported_services is not None:
        _add_shipping_supported_services(conn,
                                          sm_id[0],
                                          supported_services)

    return sm_id[0]

def _add_shipping_supported_services(conn, id_shipment,
                                      supported_services):
    values = {"id_shipment": id_shipment}

    if isinstance(supported_services, str):
        supported_services = ujson.loads(supported_services)

    if (supported_services and
        len(supported_services) == 1):
        values['id_postage'] = supported_services.keys()[0]

    if isinstance(supported_services, dict):
        supported_services = ujson.dumps(supported_services)
    values['supported_services'] = supported_services

    id = insert(conn,
                'shipping_supported_services',
                values=values,
                returning='id')
    logging.info('shipment supported services added: id: %s, values: %s',
                 id[0], values)

def _add_shipping_fee(conn, id_shipment,
                       handling_fee,
                       shipping_fee):
    values = {
        "id_shipment": id_shipment,
        'handling_fee': handling_fee,
        'shipping_fee': shipping_fee}
    id = insert(conn,
                'shipping_fee',
                values=values,
                returning='id')
    logging.info('shipment fee added: id: %s, values: %s',
                 id[0], values)

def _create_shipping_list(conn, id_item, quantity,
                          id_shipment=None, picture=None,
                          free_shipping=None):
    shipping_value = {
        'id_item': id_item,
        'quantity': quantity,
        }

    if id_shipment:
        shipping_value['id_shipment'] = id_shipment
    if picture:
        shipping_value['picture'] = picture
    if free_shipping:
        shipping_value['free_shipping'] = free_shipping

    insert(conn, 'shipping_list', values=shipping_value)
    logging.info('shipping_list create: %s', shipping_value)



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
                                      self.id_telephone)
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
        cal_method = SHIPPING_CALCULATION_METHODS.FLAT_RATE
        for sale in sales:
            handling_fee = float(sale.shipping_setting.fees.handling.value)
            shipping_fee = float(sale.shipping_setting.fees.shipping.value)

            id_order_item = sale.order_props['id_order_item']
            for _ in range(int(sale.order_props['quantity'])):
                id_shipment = create_shipment(self.conn,
                                self.id_order,
                                self.id_shipaddr,
                                self.id_telephone,
                                handling_fee=handling_fee,
                                shipping_fee=shipping_fee,
                                calculation_method=cal_method)
                _create_shipping_list(self.conn,
                                      id_order_item,
                                      1,
                                      id_shipment=id_shipment)
        logging.info('shipment_flat_rate_sales_handled: %s', sales)


    def handleGroupCarrierShippingSales(self, sales, free_sales_group):
        logging.info('shipment_carrier_sales_group_handling: %s', sales)
        self._groupShippingSales(
            sales,
            free_sales_group,
            SHIPPING_CALCULATION_METHODS.CARRIER_SHIPPING_RATE)

    def handleCarrierShippingSales(self, sales):
        logging.info('shipment_carrier_sales_separate_handling: %s', sales)
        self.separateShipments(
            sales,
            SHIPPING_CALCULATION_METHODS.CARRIER_SHIPPING_RATE)

    def handleGroupCustomShippingSales(self, sales):
        logging.info('shipment_custom_sales_group_handling: %s', sales)
        self._groupShippingSales(
            sales,
            [],
            SHIPPING_CALCULATION_METHODS.CUSTOM_SHIPPING_RATE)

    def handleCustomShippingSales(self, sales):
        logging.info('shipment_custom_sales_separate_handling: %s', sales)
        self.separateShipments(
            sales,
            SHIPPING_CALCULATION_METHODS.CUSTOM_SHIPPING_RATE)

    def handleInvoiceShippingSales(self, sales):
        cal_method = SHIPPING_CALCULATION_METHODS.INVOICE
        for sale in sales:
            id_order_item = sale.order_props['id_order_item']
            for _ in range(int(sale.order_props['quantity'])):
                id_shipment = create_shipment(self.conn,
                                              self.id_order,
                                              self.id_shipaddr,
                                              self.id_telephone,
                                              calculation_method=cal_method)
                _create_shipping_list(self.conn,
                                      id_order_item,
                                      1,
                                      id_shipment = id_shipment)

    def handleSeparateFreeShippingSales(self, sales):
        cal_method = SHIPPING_CALCULATION_METHODS.FREE_SHIPPING
        for sale in sales:
            id_order_item = sale.order_props['id_order_item']
            for _ in range(int(sale.order_props['quantity'])):
                id_shipment = create_shipment(self.conn,
                                              self.id_order,
                                              self.id_shipaddr,
                                              self.id_telephone,
                                              calculation_method=cal_method)
                _create_shipping_list(self.conn,
                                      id_order_item,
                                      1,
                                      id_shipment=id_shipment,
                                      free_shipping=True)

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
        self.handleSeparateFreeShippingSales(free_sales)

        self.handleGroupCarrierShippingSales(carrier_sales_group,
                                             free_sales_group)
        self.handleGroupCustomShippingSales(custom_sales_group)

    def groupByMostCommonService(self, sales, free_sales_group, cal_method):
        supported_services_count = defaultdict(int)
        service_carrier_map = defaultdict()
        # calculate sales count for each services.
        for sale in sales:
            for service in sale.shipping_setting.supported_services:
                supported_services_count[service] += 1
            service_carrier_map.update(sale.shipping_setting.supported_services)

        # sort services id by count
        def __sort_func(x, y):
            if x[1] == y[1]:
                return cmp(x[0], y[0])
            else:
                return cmp(y[1], x[1])
        service_count_map = supported_services_count.items()
        service_count_map = sorted(service_count_map,
                                   cmp=__sort_func)

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
        free_shipping_fee = None
        if len(group_services) == 1:
            weight = self.totalWeight(group_sales)
            unit = DEFAULT_WEIGHT_UNIT
            dest = self.getDestAddr()
            id_address = self._getShippingFeeOrigAddress(group_sales[0])
            shipping_fee = self.getShippingFee(
                service_carrier_map[group_services[0]],
                group_services[0],
                weight,
                unit,
                dest,
                id_address)

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
                    id_address)
                free_shipping_fee = (float(shipping_fee_with_free_sales) -
                                  float(shipping_fee))

        handling_fee = self.getMaxHandlingFee(group_sales)
        id_shipment = create_shipment(self.conn,
                                      self.id_order,
                                      self.id_shipaddr,
                                      self.id_telephone,
                                      handling_fee=handling_fee,
                                      shipping_fee=shipping_fee,
                                      supported_services=supported_services,
                                      calculation_method=cal_method)
        for sale in group_sales:
            id_order_item = sale.order_props['id_order_item']
            quantity = sale.order_props['quantity']
            _create_shipping_list(self.conn,
                                  id_order_item,
                                  quantity,
                                  id_shipment=id_shipment)

        return ([sale for sale in sales if sale not in group_sales],
                free_shipping_fee,
                id_shipment)

    def separateShipments(self, sales, cal_method):
        for sale in sales:
            service_carrier_map = sale.shipping_setting.supported_services
            shipping_fee = None
            if len(service_carrier_map) == 1:
                weight = self.totalWeight([sale])
                unit = DEFAULT_WEIGHT_UNIT
                dest = self.getDestAddr()
                id_address = self._getShippingFeeOrigAddress(sale)
                shipping_fee = self.getShippingFee(
                    service_carrier_map.values()[0],
                    service_carrier_map.keys()[0],
                    weight,
                    unit,
                    dest,
                    id_address)

            handling_fee = self.getMaxHandlingFee([sale])
            id_order_item = sale.order_props['id_order_item']
            for _ in range(int(sale.order_props['quantity'])):
                id_shipment = create_shipment(
                    self.conn,
                    self.id_order,
                    self.id_shipaddr,
                    self.id_telephone,
                    handling_fee=handling_fee,
                    shipping_fee=shipping_fee,
                    supported_services=service_carrier_map,
                    calculation_method=cal_method)
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
                       dest, id_address):
        logging.info('shipment_shipping_fee: id_carrier: %s, service: %s', (id_carrier, id_service))
        xml_fee = remote_xml_shipping_fee(
            [(id_carrier, [id_service])],
            weight,
            unit,
            dest,
            id_address)
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

    def _getShippingFeeOrigAddress(self, sale):
        """ get sale's shop address for local sale or corporate account
            address for internet sale.

            sale - ActorSale object.
            return - $id_address: destination address id.
        """
        id_shop = int(sale.order_props['id_shop'])
        if id_shop:
            return sale.get_shop(id_shop).id_address
        else:
            return sale.brand.id_address

    def getDestAddr(self):
        """ Get destination address according with user and shipping address.
        """
        if self.dest_addr is None:
            self.dest_addr = get_user_dest_addr(self.conn,
                                                self.id_user,
                                                self.id_shipaddr)
        return self.dest_addr

    def _shippingListForFreeShippingSalesGroup(self, free_sales_group, spm_id, fee):
        for sale in free_sales_group:
            id_order_item = sale.order_props['id_order_item']
            quantity = sale.order_props['quantity']
            _create_shipping_list(self.conn,
                                  id_order_item,
                                  quantity,
                                  id_shipment=spm_id,
                                  free_shipping=True)
        values = {'id_shipment': spm_id,
                  'fee': fee}
        insert(self.conn, 'free_shipping_fee', values=values)

    def _groupShipmentForFreeShippingSales(self, free_sales_group):
        cal_method = SHIPPING_CALCULATION_METHODS.FREE_SHIPPING
        id_shipment = create_shipment(self.conn,
                                      self.id_order,
                                      self.id_shipaddr,
                                      self.id_telephone,
                                      calculation_method=cal_method)
        for sale in free_sales_group:
            id_order_item = sale.order_props['id_order_item']
            quantity = sale.order_props['quantity']
            _create_shipping_list(self.conn,
                                  id_order_item,
                                  quantity,
                                  id_shipment=id_shipment,
                                  free_shipping=True)

    def _groupShippingSales(self, sales, free_sales_group, cal_method):
        if not sales:
            return
        free_shipping_fee = None
        free_sales_shipment = None
        while sales:
            sales, fs_fee, spm_id = self.groupByMostCommonService(sales,
                                                                  free_sales_group,
                                                                  cal_method)
            if fs_fee is not None:
                if (free_shipping_fee is None or
                        (free_shipping_fee is not None and
                         fs_fee < free_shipping_fee)):
                    free_shipping_fee, free_sales_shipment = fs_fee, spm_id
        if free_shipping_fee is not None:
            self._shippingListForFreeShippingSalesGroup(free_sales_group,
                                                free_sales_shipment,
                                                free_shipping_fee)
        elif free_sales_group:
            self._groupShipmentForFreeShippingSales(free_sales_group)


SHIPMENT_FIELDS = ['id', 'id_order', 'id_address',
                   'id_phone', 'mail_tracking_number',
                   'status', 'timestamp', 'calculation_method']
def get_shipping_shipments_by_order(conn, id_order):
    query_str = ("SELECT %s "
                   "FROM shipments "
                  "WHERE id_order=%%s "
                    "AND calculation_method in (%%s, %%s)"
                 % ", ".join(SHIPMENT_FIELDS))
    r = query(conn,
              query_str,
              (id_order,
               SHIPPING_CALCULATION_METHODS.CARRIER_SHIPPING_RATE,
               SHIPPING_CALCULATION_METHODS.CUSTOM_SHIPPING_RATE))
    shipment_list = []
    for item in r:
        shipment_list.append(dict(zip(SHIPMENT_FIELDS, item)))
    return shipment_list

SHIPMENT_SERVICES_FIELDS = [
    'id', 'id_shipment', 'id_postage', 'supported_services']
def get_shipping_supported_services(conn, id_shipment):
    query_str = ("SELECT %s "
                 "FROM shipping_supported_services "
                 "WHERE id_shipment = %%s"
                 % ", ".join(SHIPMENT_SERVICES_FIELDS))
    r = query(conn, query_str, (id_shipment,))
    serv_list = []
    for item in r:
        serv_list.append(dict(zip(SHIPMENT_SERVICES_FIELDS, item)))

    carrier_services_map = defaultdict(list)
    for item in serv_list:
        supported_services = ujson.loads(item['supported_services'])
        for id_service, id_carrier in supported_services.iteritems():
            carrier_services_map[id_carrier].append(id_service)
    return carrier_services_map.items()


def remote_get_supported_services(conn, id_shipment):
    carrier_services = get_shipping_supported_services(conn, id_shipment)
    return remote_xml_shipping_services(carrier_services)

SHIPMENT_FEE_FIELDS = [
    'id', 'id_shipment', 'handling_fee', 'shipping_fee'
]
def get_shipping_fee(conn, id_shipment):
    query_str = ("SELECT %s "
                   "FROM shipping_fee "
                  "WHERE id_shipment = %%s"
                 % ", ".join(SHIPMENT_FEE_FIELDS))
    r = query(conn, query_str, (id_shipment,))
    assert len(r) != 0, 'No fee info for shipment %s' % id_shipment
    assert len(r) == 1, ("One shipment should only have one "
                         "fee record: shipment:%s, result: %s"
                         % (id_shipment, r))

    return dict(zip(SHIPMENT_FEE_FIELDS, r[0]))

SHIPPING_ITEM_FIELDS = [
    ('id_item', 'spl.id_item'),
    ('id_shipment', 'spl.id_shipment'),
    ('quantity', 'spl.quantity'),
    ('free_shipping', 'spl.free_shipping'),
    ('id_sale', 'oi.id_sale'),
    ('id_shop', 'oi.id_shop'),
    ('id_variant', 'oi.id_variant'),
    ('id_weight_type', 'oi.id_weight_type')]

def get_shipping_list(conn, id_shipment):
    query_str = ("SELECT %s "
                   "FROM shipping_list as spl "
                   "JOIN order_items as oi "
                     "ON spl.id_item = oi.id "
                  "WHERE spl.id_shipment = %%s"
                 % ", ".join([field[1] for field in SHIPPING_ITEM_FIELDS]))
    r = query(conn, query_str, (id_shipment,))
    shipping_list = []
    for item in r:
        shipping_list.append(dict(
            zip([field[0] for field in SHIPPING_ITEM_FIELDS], item)))
    return shipping_list

def user_accessable_shipment(conn, id_shipment, id_user):
    query_str = ("SELECT * "
                   "FROM shipments as spm "
                   "JOIN orders as o "
                     "ON spm.id_order = o.id "
                  "WHERE spm.id = %s "
                    "AND o.id_user = %s")

    r = query(conn, query_str, (id_shipment, id_user))
    return len(r) > 0

def conf_shipping_service(conn, id_shipment, id_service,
                          fee, fee_for_free=None):
    where = {'id_shipment': id_shipment}
    update(conn,
           "shipping_supported_services",
            values={'id_postage': id_service},
            where=where)

    update(conn,
           "shipping_fee",
           values={"shipping_fee": fee},
           where=where)

    if fee_for_free:
        update(conn,
               "free_shipping_fee",
               values={'fee': fee_for_free},
               where=where)

