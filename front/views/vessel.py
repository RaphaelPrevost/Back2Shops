# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import copy
import re
from B2SUtils.base_actor import as_list
from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from common.constants import FRT_ROUTE_ROLE
from common.utils import cur_symbol
from common.utils import format_amount
from common.utils import format_datetime
from common.utils import get_err_msg
from common.utils import get_url_format
from common.utils import get_thumbnail
from common.utils import zero
from common.data_access import data_access
from views.base import BaseHtmlResource as BaseHtmlResource
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

class _BaseHtmlResource(BaseHtmlResource):
    tabs = [
        {'icon': 'trackvessel', 'name': '船队跟踪',
         'url': '/vessel'},
        {'icon': 'trackcontainer', 'name': '货物跟踪',
         'url': '/vessel/container'},
        {'icon': 'myfleets', 'name': '我的船队',
         'url': '/vessel/myfleets'},
        {'icon': 'eta', 'name': '智能ETA',
         'url': ''},
    ]
    cur_tab_index = 0

    def _add_common_data(self, resp_dict):
        resp_dict['users_id'] = self.users_id
        resp_dict['tabs'] = copy.deepcopy(self.tabs)
        resp_dict['cur_tab_index'] = self.cur_tab_index
        if self.cur_tab_index >= 0:
            resp_dict['tabs'][self.cur_tab_index]['current'] = True

        if 'err' not in resp_dict:
            resp_dict['err'] = ''
        resp_dict['err'] = get_err_msg(resp_dict['err'])

        resp_dict['as_list'] = as_list
        resp_dict['cur_symbol'] = cur_symbol
        resp_dict['format_amount'] = format_amount
        resp_dict['format_datetime'] = format_datetime
        resp_dict['get_thumbnail'] = get_thumbnail
        resp_dict['zero'] = zero
        resp_dict.update({
            'auth_url_format': get_url_format(FRT_ROUTE_ROLE.USER_AUTH),
            'logout_url_format': get_url_format(FRT_ROUTE_ROLE.USER_LOGOUT),
            'reset_pwd_req_url_format': get_url_format(FRT_ROUTE_ROLE.RESET_PWD_REQ),
            'user_url_format': get_url_format(FRT_ROUTE_ROLE.USER_INFO),
            'my_account_url_format': get_url_format(FRT_ROUTE_ROLE.MY_ACCOUNT),
        })


class VesselHomepageResource(_BaseHtmlResource):
    template = 'vessel_index.html'

    def _on_get(self, req, resp, **kwargs):
        return self._get_common_data(req, resp, **kwargs)

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
        else:
            pass
        return data

    def _get_common_data(self, req, resp, **kwargs):
        myfleets = []
        if self.users_id:
            result = data_access(REMOTE_API_NAME.GET_USER_FLEET,
                                 req, resp)
            if result.get('res') != RESP_RESULT.F:
                myfleets = result['objects']
        return {
            'vessels': [],
            'myfleets': myfleets,
            'ports': [],
            'vessel_input': '',
        }

class MyFleetsResource(VesselHomepageResource):
    cur_tab_index = 2


class ContainerResource(_BaseHtmlResource):
    template = 'vessel_index.html'
    cur_tab_index = 1

    def _on_get(self, req, resp, **kwargs):
        return self._get_common_data(req, resp, **kwargs)

    def _on_post(self, req, resp, **kwargs):
        data = self._get_common_data(req, resp, **kwargs)

        if req.get_param('search_container'):
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

    def _get_common_data(self, req, resp, **kwargs):
        return {
            'containers': [],
            'container_input': '',
        }


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
                         for pos in result['object'].get('positions', [])]
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

