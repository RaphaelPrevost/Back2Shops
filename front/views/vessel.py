import re
from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from common.data_access import data_access
from views.base import BaseHtmlResource
from views.base import BaseJsonResource


def search_vessel(req, resp, query, **kwargs):
    vessels = []
    if query.isdigit():
        for search_by in ('imo', 'mmsi'):
            result = data_access(REMOTE_API_NAME.SEARCH_VESSEL,
                                 req, resp,
                                 search_by=search_by, q=query, **kwargs)
            if result.get('res') != RESP_RESULT.F:
                vessels = result['objects']
                if len(vessels) > 0:
                    break
    elif query:
        result = data_access(REMOTE_API_NAME.SEARCH_VESSEL,
                              req, resp,
                              search_by='name', q=query, **kwargs)
        if result.get('res') != RESP_RESULT.F:
            vessels = result['objects']
    return vessels

def search_port(req, resp, query):
    ports = []
    if query.isdigit():
        return ports

    for search_by in ('locode', 'name'):
        result = data_access(REMOTE_API_NAME.SEARCH_PORT,
                             req, resp,
                             search_by=search_by, q=query)
        if result.get('res') != RESP_RESULT.F:
            ports = result['objects']
            if len(ports) > 0:
                break
    return ports

def search_container(req, resp, query):
    containers = []
    if query.isdigit():
        search_by = 'bill_of_landing'
    elif query:
        search_by = 'container'
    else:
        return containers

    result = data_access(REMOTE_API_NAME.SEARCH_CONTAINER,
                         req, resp,
                         search_by=search_by, q=query)
    if result.get('res') != RESP_RESULT.F:
        containers = result['objects']
    return containers


class VesselHomepageResource(BaseHtmlResource):
    template = 'vessel_index.html'

    def _on_get(self, req, resp, **kwargs):
        return self._get_common_data(req, resp, **kwargs)

    def _get_common_data(self, req, resp, **kwargs):
        myfleets = []
        if self.users_id:
            result = data_access(REMOTE_API_NAME.GET_USER_FLEET,
                                 req, resp)
            if result.get('res') != RESP_RESULT.F:
                myfleets = result['objects']
        return {
            'myfleets': myfleets,
            'vessels': [],
            'ports': [],
            'containers': [],
            'vessel_input': '',
            'container_input': '',
        }


class SearchResource(VesselHomepageResource):
    template = 'vessel_index.html'

    def _on_post(self, req, resp, **kwargs):
        data = self._get_common_data(req, resp, **kwargs)

        if req.get_param('search_vessel'):
            vessel_input = req.get_param('vessel_input') or ''
            query = vessel_input.split(' - ')[0]
            if re.search(r"%s - Vessel\[\w+\]" % query, vessel_input):
                vessels = search_vessel(req, resp, query, details='true')
                ports = []
            elif re.search(r"%s - Port\[\w+\]" % query, vessel_input):
                vessels = []
                ports = search_port(req, resp, query)
            else:
                vessels = search_vessel(req, resp, query, details='true')
                ports = search_port(req, resp, query)
            data.update({
                'vessel_input': vessel_input,
                'vessels': vessels,
                'ports': ports,
            })
        elif req.get_param('search_container'):
            container_input = req.get_param('container_input') or ''
            container_input = container_input.strip()
            containers = search_container(req, resp, container_input)
            data.update({
                'container_input': container_input,
                'containers': containers,
            })
        else:
            pass
        return data


class VesselQuickSearchResource(BaseJsonResource):

    def _on_get(self, req, resp, **kwargs):
        results = []

        q = req.get_param('q') or ''
        q = q.strip()
        vessels = search_vessel(req, resp, q)
        vnames = [("%s - Vessel[%s]" % (v['name'].strip(), v['country_isocode']),
                   v['name'].strip())
                  for v in vessels]
        vnames.sort()
        vnames = vnames[:8]
        results.extend(vnames)

        ports = search_port(req, resp, q)
        pnames = [("%s - Port[%s]" % (p['name'].strip(), p['country_isocode']),
                   p['name'].strip())
                  for p in ports]
        pnames.sort()
        pnames = pnames[:4]
        results.extend(pnames)

        return results

    def handle_cookies(self, resp, data):
        pass


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


class VesselArrivalReminderResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, **kwargs):
        action = req.get_param('action')
        imo = req.get_param('imo')
        mmsi = req.get_param('mmsi')
        if action not in ('add', 'delete') or not imo or not mmsi:
            raise ValidationError('INVALID_REQUEST')

        result = data_access(REMOTE_API_NAME.SET_VESSEL_REMINDER,
                             req, resp, imo=imo, mmsi=mmsi, action=action)
        return result


class ContainerArrivalReminderResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, **kwargs):
        action = req.get_param('action')
        container = req.get_param('container')
        if action not in ('add', 'delete') or not container:
            raise ValidationError('INVALID_REQUEST')

        result = data_access(REMOTE_API_NAME.SET_CONTAINER_REMINDER,
                             req, resp, container=container, action=action)
        return result

