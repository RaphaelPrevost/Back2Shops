from B2SUtils.base_actor import as_list
from B2SUtils.base_actor import BaseActor


class ActorProcessor(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'img': 'img'
                 }

class ActorPayment(BaseActor):
    attrs_map = {'transaction': '@transaction',
                 'version': '@version',
                 }

    @property
    def processors(self):
        procs = as_list(self.data.get('processor'))
        return [ActorProcessor(data=item) for item in procs]

