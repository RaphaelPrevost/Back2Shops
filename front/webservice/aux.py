from webservice.base import BaseJsonResource
from common.data_access import data_access
from B2SFrontUtils.constants import REMOTE_API_NAME


class AuxResource(BaseJsonResource):
    def _on_get(self, req, resp, **kwargs):
        remote_resp = data_access(REMOTE_API_NAME.AUX,
                                  req, resp, **req._params)
        return remote_resp
