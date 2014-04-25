from B2SRespUtils.generate import gen_json_resp
from views.base import BaseResource

class BaseJsonResource(BaseResource):
    def gen_resp(self, resp, data):
        return gen_json_resp(resp, data)
