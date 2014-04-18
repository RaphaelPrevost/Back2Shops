from B2SUtils.base_actor import BaseActor


class ActorError(BaseActor):
    attrs_map = {'version': '@version',
                 'err': '#text'}
