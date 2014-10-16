from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from common.data_access import data_access
from views.base import BaseHtmlResource

class VesselHomepageResource(BaseHtmlResource):
    template = 'vessel_index.html'

    def _on_get(self, req, resp, **kwargs):
        vessels = []
        ports = []
        if self.users_id:
            #TODO get my fleet data
            pass
        return {
            'vessels': vessels,
            'ports': ports,
        }


class SearchResource(BaseHtmlResource):
    template = 'vessel_index.html'

    def _on_post(self, req, resp, **kwargs):
        vessels = []
        ports = []
        if req.get_param('vessel'):
            vessels = self.search_vessel(req, resp)
        elif req.get_param('port'):
            ports = self.search_port(req, resp)
        else:
            pass
        return {
            'vessels': vessels,
            'ports': ports,
        }

    def search_vessel(self, req, resp):
        vessels = []
        query = req.get_param('vessel')
        if query.isdigit():
            for search_by in ('imo', 'mmsi'):
                result = data_access(REMOTE_API_NAME.SEARCH_VESSEL,
                                     req, resp,
                                     search_by=search_by, q=query, details='true')
                if result.get('res') != RESP_RESULT.F:
                    vessels = result['objects']
                    if len(vessels) > 0:
                        break
        else:
            result = data_access(REMOTE_API_NAME.SEARCH_VESSEL,
                                  req, resp,
                                  search_by='name', q=query, details='true')
            if result.get('res') != RESP_RESULT.F:
                vessels = result['objects']
        return vessels

    def search_port(self, req, resp):
        ports = []
        query = req.get_param('port')
        for search_by in ('locode', 'name'):
            result = data_access(REMOTE_API_NAME.SEARCH_PORT,
                                 req, resp,
                                 search_by=search_by, q=query)
            if result.get('res') != RESP_RESULT.F:
                ports = result['objects']
                if len(ports) > 0:
                    break
        return ports

