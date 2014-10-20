from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from common.data_access import data_access
from views.base import BaseHtmlResource
from views.base import BaseJsonResource


class VesselHomepageResource(BaseHtmlResource):
    template = 'vessel_index.html'

    def _on_get(self, req, resp, **kwargs):
        vessels = []
        ports = []
        if self.users_id:
            result = data_access(REMOTE_API_NAME.GET_USER_FLEET,
                                 req, resp)
            if result.get('res') != RESP_RESULT.F:
                vessels = result['objects']
        return {
            'vessels': vessels,
            'ports': ports,
            'vessel_input': '',
            'port_input': '',
        }


class SearchResource(BaseHtmlResource):
    template = 'vessel_index.html'

    def _on_post(self, req, resp, **kwargs):
        vessels = []
        ports = []
        if req.get_param('vessel_input'):
            vessels = self.search_vessel(req, resp)
        elif req.get_param('port_input'):
            ports = self.search_port(req, resp)
        else:
            pass
        return {
            'vessels': vessels,
            'ports': ports,
            'vessel_input': req.get_param('vessel_input') or '',
            'port_input': req.get_param('port_input') or '',
        }

    def search_vessel(self, req, resp):
        vessels = []
        query = req.get_param('vessel_input')
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
        query = req.get_param('port_input')
        for search_by in ('locode', 'name'):
            result = data_access(REMOTE_API_NAME.SEARCH_PORT,
                                 req, resp,
                                 search_by=search_by, q=query)
            if result.get('res') != RESP_RESULT.F:
                ports = result['objects']
                if len(ports) > 0:
                    break
        return ports


class VesselNavPathResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, **kwargs):
        imo = req.get_param('imo')
        mmsi = req.get_param('mmsi')
        if not imo and not mmsi:
            raise ValidationError('INVALID_REQUEST')

        result = data_access(REMOTE_API_NAME.GET_VESSEL_NAVPATH,
                             req, resp, imo=imo, mmsi=mmsi)
        if result.get('res') != RESP_RESULT.F:
            positions = [(pos['latitude'], pos['longitude'])
                         for pos in result['object']['positions']]
        else:
            positions = []
        return {'positions': positions}


class UserFleetResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, **kwargs):
        action = req.get_param('action')
        imo = req.get_param('imo')
        mmsi = req.get_param('mmsi')
        if action not in ('add', 'delete') or not imo or not mmsi:
            raise ValidationError('INVALID_REQUEST')

        result = data_access(REMOTE_API_NAME.SET_USER_FLEET,
                             req, resp, imo=imo, mmsi=mmsi, action=action)
        return result

