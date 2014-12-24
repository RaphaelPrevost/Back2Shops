# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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


from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from webservice.vessel.base import BaseVesselResource


class VesselArrivalNotifResource(BaseVesselResource):
    login_required = {'get': True, 'post': True}
    api_path = 'webservice/1.0/private/vessel/reminder'

    def _get_valid_args(self, req, resp, conn, **kwargs):
        if req.method == 'GET':
            return {"id_user": self.users_id}

        action = req.get_param('action')
        imo = req.get_param('imo')
        mmsi = req.get_param('mmsi')
        if action not in ('add', 'delete'):
            raise ValidationError('INVALID_REQUEST')
        if not imo or not mmsi:
            raise ValidationError('INVALID_REQUEST')

        email = db_utils.select(conn, "users",
                    columns=('email',),
                    where={'id': self.users_id})[0][0]
        return {
            "action": action,
            "id_user": self.users_id,
            "email": email,
            "mmsi": mmsi,
            "imo": imo,
        }


class ContainerArrivalNotifResource(BaseVesselResource):
    login_required = {'get': True, 'post': True}
    api_path = 'webservice/1.0/private/container/reminder'

    def _get_valid_args(self, req, resp, conn, **kwargs):
        if req.method == 'GET':
            return {"id_user": self.users_id}

        action = req.get_param('action')
        container = req.get_param('container')
        if action not in ('add', 'delete'):
            raise ValidationError('INVALID_REQUEST')
        if not container:
            raise ValidationError('INVALID_REQUEST')

        email = db_utils.select(conn, "users",
                    columns=('email',),
                    where={'id': self.users_id})[0][0]
        return {
            "action": action,
            "id_user": self.users_id,
            "email": email,
            "container": container,
        }

