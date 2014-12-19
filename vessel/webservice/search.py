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


import settings

from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from common.thirdparty.datasource import getContainerDs
from common.thirdparty.datasource import getVesselDs
from webservice.base import BaseJsonResource
from common.utils import query_vessel_details


class SearchVesselResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('name', 'imo', 'mmsi', 'cs') or not q:
            raise ValidationError('INVALID_REQUEST')

        if search_by == 'cs':
            search_by = 'name'
            # TODO: find according name in DB

        results = getVesselDs().searchVessel(**{search_by: q})

        if len(results) > 0 and req.get_param('details') == 'true':
            results = query_vessel_details(conn, search_by, q)

        return {'objects': results,
                'res': RESP_RESULT.S}


class SearchPortResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('name', 'locode') or not q:
            raise ValidationError('INVALID_REQUEST')

        results = getVesselDs().searchPort(**{search_by: q,
                                     'country': req.get_param('country')})
        return {'objects': results,
                'res': RESP_RESULT.S}


class SearchContainerResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('container', 'bill_of_landing') or not q:
            raise ValidationError('INVALID_REQUEST')

        results = []
        container_info = self._get_container_info(conn, search_by, q)
        if len(container_info['shipment_cycle']) > 0:
            results.append(container_info)
        return {'objects': results,
                'res': RESP_RESULT.S}

    def _get_vessel_info(self, conn, vessel_name):
        vessel_info = None
        results = query_vessel_details(conn, 'name', vessel_name,
                                       exact_match=True)
        for v in results:
            if settings.USE_MOCK_FLEETMON_DATA or v['name'] == vessel_name:
                vessel_info = v
                break
        return vessel_info

    def _get_container_info(self, conn, search_by, q):
        container_info = getContainerDs().searchContainer(
                            search_by=search_by, number=q)
        for shipment in container_info['shipment_cycle']:
            if shipment['vessel_name']:
                vessel_info = self._get_vessel_info(conn, shipment['vessel_name'])
                container_info['vessel_info'] = vessel_info
            break
        return container_info

