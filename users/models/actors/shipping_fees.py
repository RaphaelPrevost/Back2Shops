from common.utils import as_list
from models.actors.base_actor import BaseActor

class ActorFee(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}

class ActorService(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'desc': 'desc'}
    @property
    def fee(self):
        return ActorFee(data=self.data.get('fee'))

class ActorCarrier(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}
    @property
    def services(self):
        services = as_list(self.data.get('service'))
        return [ActorService(data=service) for service in services]

class ActorShippingFees(BaseActor):
    @property
    def carriers(self):
        carriers = as_list(self.data.get('carrier'))
        return [ActorCarrier(data=carrier) for carrier in carriers]
