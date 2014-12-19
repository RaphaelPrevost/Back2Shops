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
import re

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from B2SUtils.errors import ValidationError
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.m17n import gettext as _
from common.utils import get_url_format
from views.base import BaseHtmlResource

email_reexp = r"^([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@([-0-9a-zA-Z]+.)+[a-zA-Z]{2,6}$"
email_pattern = re.compile(email_reexp)
def is_valid_email(email):
    return email and email_pattern.match(email)

class ResetPwdRequestResource(BaseHtmlResource):
    template = "reset_password_request.html"

    def _on_get(self, req, resp, **kwargs):
        return {'msg': ''}

    def _on_post(self, req, resp, **kwargs):
        email = req.get_param('email')
        if not is_valid_email(email):
            raise ValidationError('ERR_EMAIL')

        remote_resp = data_access(REMOTE_API_NAME.SET_USERINFO,
                                  req, resp,
                                  action="passwd",
                                  email=email)
        err = msg = ''
        if remote_resp.get('res') == RESP_RESULT.F:
            err = remote_resp.get('err')
        else:
            msg = _('The reset password email has been sent to %(email)s') \
                  % {'email': email}
        return {'err': err,
                'msg': msg}

class ResetPwdResource(BaseHtmlResource):
    template = "reset_password.html"

    def _on_get(self, req, resp, **kwargs):
        email = req.get_param('email')
        key = req.get_param('key')
        err = ''
        if not key or not is_valid_email(email):
            err = 'INVALID_REQUEST'
        return {
            'email': email,
            'key': key,
            'err': err,
        }

    def _on_post(self, req, resp, **kwargs):
        email = req.get_param('email')
        key = req.get_param('key')
        password = req.get_param('password')
        password2 = req.get_param('password2')

        err = ''
        if not key or not is_valid_email(email):
            err = 'INVALID_REQUEST'
        elif not password or password != password2:
            err = 'ERR_PASSWORD'

        data = {'email': email, 'key': key}
        if err:
            data['err'] = err
            return data
        else:
            remote_resp = data_access(REMOTE_API_NAME.SET_USERINFO,
                                      req, resp,
                                      action="passwd",
                                      email=email,
                                      key=key,
                                      password=password)
            if remote_resp.get('res') == RESP_RESULT.F:
                data['err'] = remote_resp.get('err')
                return data
            else:
                self.redirect(get_url_format(FRT_ROUTE_ROLE.USER_AUTH))
                return

