from B2SUtils.base_actor import as_list
from B2SUtils.base_actor import BaseActor
from B2SProtocol.constants import SHIPMENT_STATUS

st_desc_map = {
    SHIPMENT_STATUS.PACKING: 'PACKING',
    SHIPMENT_STATUS.DELAYED: 'DELAYED',
    SHIPMENT_STATUS.DELIVER: 'DELIVER',
    SHIPMENT_STATUS.DELETED: 'DELETED',
    SHIPMENT_STATUS.FETCHED: 'FETCHED',
}

class ActorService(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'desc': 'desc'}

class ActorCarrier(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

    @property
    def services(self):
        services_data = as_list(self.data.get('service'))
        return [ActorService(data=service) for service in services_data]

class ActorTracking(BaseActor):
    attrs_map = {'code': 'code',
                 'url': 'url'}


class ActorHandling(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}

class ActorShipping(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}

class ActorFees(BaseActor):
    @property
    def handling(self):
        return ActorHandling(data=self.data.get('handling'))

    @property
    def shipping(self):
        shipping_data = self.data.get('shipping')
        if shipping_data is None:
            return
        return ActorShipping(data=shipping_data)

class ActorDelivery(BaseActor):
    attrs_map = {'status': '@status'}

    @property
    def carriers(self):
        carriers_data = as_list(self.data.get('carrier'))
        return [ActorCarrier(data=carrier) for carrier in carriers_data]

    @property
    def tracking(self):
        tk_data = self.data.get('tracking')
        if tk_data is None:
            return
        return ActorTracking(data=tk_data)

    @property
    def status_desc(self):
        return st_desc_map[int(self.status)]


class ActorAttribute(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}


class ActorType(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}
    @property
    def attribute(self):
        return ActorAttribute(data=self.data.get('attribute'))

class ActorVariant(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

class ActorWeight(BaseActor):
    attrs_map = {'unit': '@unit',
                 'value': '#text'}

class ActorItem(BaseActor):
    attrs_map = {'sale': '@sale',
                 'name': 'name',
                 'currency': 'currency',
                 'quantity': 'quantity',
                 'packing_quantity': 'packing_quantity',
                 'shipping_status': 'shipping_status',
                 'id_order_item': "@id_order_item"}
    @property
    def type(self):
        type_data = self.data.get('type')
        if type_data is None:
            return
        return ActorType(data=type_data)

    @property
    def variant(self):
        variant_data = self.data.get('variant')
        if variant_data is None:
            return
        return ActorVariant(data=variant_data)

    @property
    def weight(self):
        return ActorWeight(data=self.data.get('weight'))

    @property
    def remaining_quantity(self):
        return int(self.quantity) - int(self.packing_quantity)


class ActorShipment(BaseActor):
    attrs_map = {'id': '@id',
                 'method': '@method',
                 'brand': '@brand',
                 'shop': '@shop',
                 'tracking_num': "tracking_num",
                 'shipping_date': "shipping_date",
                 'tracking_name': "tracking_name"}

    @property
    def paid_date(self):
        return self.data.get('@paid_date')

    @property
    def delivery(self):
        return ActorDelivery(data=self.data.get('delivery'))

    @property
    def fees(self):
        fees_data = self.data.get('fees')
        if fees_data is None:
            return
        return ActorFees(data=fees_data)

    @property
    def items(self):
        items_data = as_list(self.data.get('item'))
        return [ActorItem(data=item) for item in items_data]

    @property
    def shipping_carrier(self):
        if self.data.get('shipping_carrier'):
            return int(self.data.get('shipping_carrier'))



class ActorShipments(BaseActor):
    attrs_map = {'order_status': "@order_status",
                 'order_create_date': "@order_create_date"}
    @property
    def shipments(self):
        shipments_data = as_list(self.data.get('shipment'))
        return [ActorShipment(data=spm) for spm in shipments_data]
