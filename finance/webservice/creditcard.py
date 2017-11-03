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
from datetime import datetime
import ujson

from common.error import ErrorCode
from common.error import ThirdPartyError
from common.third_party.paybox import Paybox
from common.utils import is_valid_cc_num
from common.utils import is_valid_cvc
from common.utils import mask_cc_num
from webservice.base import BaseJsonResource
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError


class CCAddResource(BaseJsonResource):
    encrypt = True
    service = SERVICES.USR

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            data = decrypt_json_resp(req.stream,
                                     settings.SERVER_APIKEY_URI_MAP[self.service],
                                     settings.PRIVATE_KEY_PATH)
            data = ujson.loads(data)
            id_card = self.add_card(conn, data)

        except ThirdPartyError, e:
            return {"res": RESP_RESULT.F, "err": e.desc}

        except Exception, e:
            return {"res": RESP_RESULT.F, "err": str(e)}

        return {"res": RESP_RESULT.S, "err": "", "id": id_card}

    def add_card(self, conn, data):
        # validation
        for param in ['id_user', 'pan', 'cvc', 'expiration_date']:
            if not data.get(param):
                raise ValidationError('Missing param %s' % param)

        id_user = data['id_user']
        cardholder_name = data.get('cardholder_name', '')
        pan = data['pan']
        cvc = data['cvc']
        expire = data['expiration_date']
        repeat = data.get('repeat')
        if not is_valid_cc_num(pan):
            raise ValidationError('Invalid param pan')
        if not is_valid_cvc(cvc):
            raise ValidationError('Invalid param cvc')
        try:
            datetime.strptime(expire, '%m%y')
        except:
            raise ValidationError('Invalid param expiration_date')

        results = db_utils.select(conn, 'credit_card',
            where={
                'id_user': id_user,
                'cc_num': mask_cc_num(pan),
                'expiration_date': expire,
                'valid': True,
            })
        if results:
            raise ValidationError('Duplicated Card')

        values = {
            'id_user': id_user,
            'cardholder_name': cardholder_name,
            'cc_num': mask_cc_num(pan),
            'expiration_date': expire,
            'repeat': bool(repeat),
            'valid': False,
        }
        id_card = db_utils.insert(conn, 'credit_card',
                                  values=values, returning='id')[0]

        cli = Paybox()
        token = cli.register_card(id_card, id_user, pan, cvc, expire,
                                  repeat=bool(repeat))
        db_utils.update(conn, 'credit_card',
                        values={'paybox_token': token,
                                'valid': True},
                        where={'id': id_card})
        return id_card


class CCDeleteResource(BaseJsonResource):
    encrypt = True
    service = SERVICES.USR

    def _on_post(self, req, resp, conn, **kwargs):
        data = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[self.service],
                                 settings.PRIVATE_KEY_PATH)
        data = ujson.loads(data)

        id_card = data.get('id_card')
        if not id_card:
            raise ValidationError('Missing post param id_card')

        results = db_utils.select(conn, 'credit_card', where={'id': id_card})
        if not results:
            raise ValidationError('Invalid param id_card')

        try:
            cli = Paybox()
            cli.delete_card(id_card,
                            results[0]['id_user'],
                            results[0]['paybox_token'],
                            results[0]['expiration_date'],
                            repeat=results[0]['repeat'])
        except ThirdPartyError, e:
            return {"res": RESP_RESULT.F, "err": e.desc}
        except Exception, e:
            return {"res": RESP_RESULT.F, "err": str(e)}

        db_utils.update(conn, 'credit_card',
                        values={'valid': False},
                        where={'id': id_card})
        return {"res": RESP_RESULT.S, "err": ""}


class CCListResource(BaseJsonResource):
    encrypt = True
    service = SERVICES.USR

    def _on_get(self, req, resp, conn, **kwargs):
        id_user = req.get_param('id_user')
        if not id_user:
            raise ValidationError('Missing param id_user')

        results = db_utils.select(conn, 'credit_card',
                                  where={'id_user': id_user, 'valid': True})
        cc_list = [{'id_card': one['id'],
                    'pan': one['cc_num'],
                    'expiration_date': one['expiration_date'],
                    } for one in results]
        return {"res": RESP_RESULT.S, "err": "", "data": cc_list}

