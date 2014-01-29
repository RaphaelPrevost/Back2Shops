from common.utils import as_list
from models.base_actor import BaseActor


class ActorTypeAttribute(BaseActor):
    attrs_map = {'id': '@id',
                 'name': '@name'}

class ActorType(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}
    @property
    def attribute(self):
        attribute_data = self.data.get('attribute')
        if attribute_data:
            return ActorTypeAttribute(data=attribute_data)

class ActorWeight(BaseActor):
    attrs_map = {'unit': '@unit',
                 'value': '#text'}

class ActorVariant(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

class ActorOption(BaseActor):
    attrs_map = {'name': '@name',
                 'value': '@value'}

class ActorOptions(BaseActor):
    @property
    def option_list(self):
        op_list = as_list(self.data.get('option'))
        return [ActorOption(data=item) for item in op_list]

    @property
    def group_shipment(self):
        return self.option_list[0]

    @property
    def local_pickup(self):
        return self.option_list[1]

    @property
    def void_handling(self):
        return self.option_list[2]

    @property
    def free_shipping(self):
        return self.option_list[3]

    @property
    def flat_rate(self):
        return self.option_list[4]

    @property
    def carrier_shipping_rate(self):
        return self.option_list[5]

    @property
    def custom_shipping_rate(self):
        return self.option_list[6]

    @property
    def invoice_shipping_rate(self):
        return self.option_list[7]

class ActorService(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

class ActorCarrier(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

    @property
    def services(self):
        service_list = as_list(self.data.get('service'))
        return [ActorService(item) for item in service_list]

class ActorHandling(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}

class ActorFeesShipping(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}

class ActorFees(BaseActor):
    @property
    def handling(self):
        return ActorHandling(data=self.data.get('handling'))

    @property
    def shipping(self):
        shipping_data = self.data.get('shipping')
        if shipping_data:
            return ActorFeesShipping(data=shipping_data)

class ActorSetting(BaseActor):
    attrs_map = {'name': 'name',
                 'for_': '@for'}

    _supported_services = None

    @property
    def type(self):
        type_data = self.data.get("type")
        if type_data:
            return ActorType(data=self.data.get("type"))

    @property
    def variant(self):
        variant_data = self.data.get('variant')
        if variant_data:
            return ActorVariant(data=variant_data)

    @property
    def weight(self):
        return ActorWeight(data=self.data.get('weight'))

    @property
    def options(self):
        return ActorOptions(data=self.data.get('options'))

    @property
    def carriers(self):
        carriers_list = as_list(self.data.get('carrier'))
        return [ActorCarrier(data=item) for item in carriers_list]

    @property
    def fees(self):
        return ActorFees(data=self.data.get('fees'))

    @property
    def supported_services(self):
        if self._supported_services is None:
            self.refresh_supported_services()
        return self._supported_services

    def refresh_supported_services(self):
        if not self.carriers:
            return
        supported_services = {}
        for carrier in self.carriers:
            for service in carrier.services:
                supported_services[service.id] = carrier.id
        self._supported_services = supported_services

class ActorShipping(BaseActor):
    @property
    def settings(self):
        setting_list = as_list(self.data.get('settings'))
        return [ActorSetting(data=item) for item in setting_list]

