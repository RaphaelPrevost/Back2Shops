from webservice.base import BaseJsonResource
from common.data_access import data_access
from common.utils import allowed_countries
from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT


class AuxResource(BaseJsonResource):
    def _on_get(self, req, resp, **kwargs):
        res_name = req.get_param('get')
        remote_resp = data_access(REMOTE_API_NAME.AUX,
                                  req, resp, **req._params)
        white_countries = allowed_countries()
        if remote_resp.get('res') != RESP_RESULT.F \
                and res_name == 'countries' and white_countries:
            accept = remote_resp['accept']
            remote_resp['accept'] = filter(lambda x: x[1]
                                           in white_countries, accept)
        return remote_resp
