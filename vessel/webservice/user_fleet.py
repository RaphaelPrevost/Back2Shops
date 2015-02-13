# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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
import cgi
from StringIO import StringIO

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from webservice.base import BaseJsonResource
from common.utils import query_vessel_details


class UserFleetResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        id_user = req.get_param('id_user')
        if not id_user:
            raise ValidationError('INVALID_REQUEST')

        user_fleets = db_utils.select(conn, "user_fleet",
                                      columns=("imo", "mmsi"),
                                      where={'id_user': id_user})
        results = []
        for fleet in user_fleets:
            if fleet['imo']:
                search_by = 'imo'
                q = fleet['imo']
            else:
                search_by = 'mmsi'
                q = fleet['mmsi']

            details = query_vessel_details(conn, search_by, q)
            if len(details) > 0:
                results.append(details[0])

        return {'objects': results,
                'res': RESP_RESULT.S}

    def _on_post(self, req, resp, conn, **kwargs):
        f = StringIO(req.query_string)
        data = decrypt_json_resp(f,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                                 settings.PRIVATE_KEY_PATH)
        f.close()

        form_params = cgi.parse_qs(data)
        for p in form_params:
            form_params[p] = form_params[p][0]
        action = form_params.get('action')
        id_user = form_params.get('id_user')
        imo = form_params.get('imo')
        mmsi = form_params.get('mmsi')

        if action not in ('add', 'delete'):
            raise ValidationError('INVALID_REQUEST')
        if not id_user or not imo or not mmsi:
            raise ValidationError('INVALID_REQUEST')

        values = {
            'id_user': id_user,
            'imo': imo,
            'mmsi': mmsi,
        }
        if action == 'add':
            user_fleet = db_utils.select(conn, "user_fleet",
                                         columns=("imo", "mmsi"),
                                         where={'id_user': id_user,
                                                'imo': imo,
                                                'mmsi': mmsi})
            if len(user_fleet) == 0:
                db_utils.insert(conn, "user_fleet", values=values)

        elif action == 'delete':
            db_utils.delete(conn, "user_fleet", where=values)

        return {'res': RESP_RESULT.S}

