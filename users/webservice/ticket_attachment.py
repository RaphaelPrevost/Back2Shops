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
import magic
import os
import ujson
import urllib2
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import CBCCipher
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote, get_key_from_local
from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from webservice.base import BaseJsonResource

def upload(asset_name, content):
    remote_uri = os.path.join(settings.AST_SERVER,
                              "webservice/1.0/private/upload?name=%s"
                              % urllib2.quote(asset_name))
    try:
        data = gen_encrypt_json_context(
            content.read(),
            settings.SERVER_APIKEY_URI_MAP[SERVICES.AST],
            settings.PRIVATE_KEY_PATH)

        resp = get_from_remote(
            remote_uri,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.AST],
            settings.PRIVATE_KEY_PATH,
            data=data)
        return ujson.loads(resp)
    except Exception, e:
        logging.error("Failed to upload %s" % asset_name,
                      exc_info=True)
        raise

class TicketAttachUploadResource(BaseJsonResource):

    def _on_post(self, req, resp, conn, **kwargs):
        filename = req.get_param('name', required=True)
        result = upload(filename, req.stream)
        if result.get('res') == RESP_RESULT.F:
            raise Exception(result['err'])
        location = result['location']

        attach_id = db_utils.insert(conn, "ticket_attachment",
                                    values={'location': location},
                                    returning='id')
        return {"res": RESP_RESULT.S,
                "err": "",
                "id": attach_id}

class BaseTicketAttachReadResource(BaseJsonResource):
    def _on_get(self, req, resp, conn, **kwargs):
        _id = req.get_param('attachment_id')
        rows = db_utils.select(self.conn, 'ticket_attachment',
                               columns=('id_ticket', 'location'),
                               where={'id': _id},
                               limit=1)
        if not rows or len(rows) == 0:
            raise ValidationError('INVALID_REQUEST')
        id_ticket, location = rows[0]
        self._check_ticket(id_ticket)

        try:
            uri = os.path.join(settings.AST_ROOT_URI, location)
            content = urllib2.urlopen(uri).read()
        except urllib2.HTTPError, e:
            logging.error('get attachment(id=%s) HTTPError: '
                          'error: %s, with uri: %s',
                          _id, e, uri, exc_info=True)
            raise

        pub_key = get_key_from_local(settings.PUB_KEY_PATH)
        return CBCCipher(pub_key).decrypt(content)

    def _check_ticket(self, id_ticket):
        pass

    def gen_resp(self, resp, data):
        if isinstance(data, dict):
            resp = super(BaseTicketAttachReadResource, self).gen_resp(resp, data)
        else:
            resp.body = data
            resp.content_type = magic.Magic(mime=True).from_buffer(data)
        return resp

class TicketAttachReadResource(BaseTicketAttachReadResource):
    encrypt = True

class TicketAttachRead4FUserResource(BaseTicketAttachReadResource):
    login_required = {'get': True, 'post': False}

    def _check_ticket(self, id_ticket):
        if not id_ticket:
            raise ValidationError('INVALID_REQUEST')
        rows = db_utils.select(self.conn, 'ticket',
                               columns=('fo_author', 'fo_recipient'),
                               where={'id': id_ticket},
                               limit=1)
        if not rows or len(rows) == 0:
            raise ValidationError('INVALID_REQUEST')

        fo_author, fo_recipient = rows[0]
        if int(self.users_id) not in (fo_author, fo_recipient):
            raise ValidationError('INVALID_REQUEST')

