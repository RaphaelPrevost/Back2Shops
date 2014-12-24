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


from webservice.base import BaseJsonResource
from common.data_access import data_access
from common.m17n import gettext as _
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
        if 'name' in remote_resp:
            remote_resp['name'] = _(remote_resp['name'])
        return remote_resp
