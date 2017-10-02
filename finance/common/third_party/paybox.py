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
import logging
import requests
import urllib
from datetime import datetime
from common.constants import CUR_CODE
from common.error import ThirdPartyError


#RESP_CODE = {
#    '00000': 'success',
#    # Luhn check failed
#    '00004': 'bad credit card number - fatal error',
#    '00008': 'bad expiration date - fatal error',
#    '00016': 'this subscriber already exists',
#    '00021': 'unauthorized BIN - fatal error',
#    # this is weird, as normally this is only for physical stores
#    # - basically the bank tell us to keep the card, like an ATM can swallow
#    #   a card if the PIN was entered wrong too many times
#    '00104': 'keep the card - fatal error',
#    '00105': 'do not honor - can retry later',
#    '00112': 'invalid transaction - can retry later',
#    # Luhn check was correct, but the number does not exist
#    '00114': 'bad credit card number - fatal error',
#    '00134': 'suspicion of fraud - can retry later',
#    '00141': 'credit card reported lost - fatal error',
#    '00143': 'credit card reported stolen - fatal error',
#    '00151': 'insufficient funds - not enough money on the account, can retry later',
#    '00154': 'the card has already expired - fatal error',
#    # the card was not recorded properly or was manually removed
#    '00156': 'not found',
#    '00157': 'unauthorized transaction - fatal error',
#    '00159': 'possible fraud - fatal error',
#    '00176': 'chargeback',
#}


class Paybox:

    def _post(self, data, **kwargs):
        uri = settings.PAYBOX_DIRECT_REQUEST_URL
        logging.debug("Paybox direct request, uri: %s, data: %s", uri, data)

        try:
            resp = requests.post(
                uri, data=urllib.urlencode(data),
                headers={"Content-Type": 'application/x-www-form-urlencoded'},
                **kwargs)
            logging.debug("Paybox direct response: %s", resp.text)

            resp_data = dict([(k, v[0])
                              for k, v in cgi.parse_qs(resp.text).iteritems()])
            errcode = resp_data.get('CODEREPONSE')
            if errcode != '00000':
                commentaire = resp_data.get('COMMENTAIRE')
                raise ThirdPartyError(errcode, commentaire)
            return resp_data

        except Exception, e:
            logging.debug("Paybox direct request failed: %s", e, exc_info=True)
            raise


    def register_card(self, cc_id, user_id,
                      cc_num, cvc, expiration_date, repeat=False):
        params = self._paybox_direct_params(
            '00056', user_id, cc_id, cc_id,
            cc_num, cvc, expiration_date, 1, repeat=repeat)
        try:
            data = self._post(params)
            return data['PORTEUR']
        except ThirdPartyError, e:
            if e.code == '00016':
                return self.update_card(cc_id, user_id,
                                        cc_num, cvc, expiration_date,
                                        repeat=repeat)
            else:
                raise

    def update_card(self, cc_id, user_id,
                    cc_num, cvc, expiration_date, repeat=False):
        params = self._paybox_direct_params(
            '00057', user_id, cc_id, cc_id,
            cc_num, cvc, expiration_date, 1, repeat=repeat)
        data = self._post(params)
        return data['PORTEUR']

    def delete_card(self, cc_id, user_id,
                    cc_num, expiration_date, repeat=False):
        params = self._paybox_direct_params(
            '00058', user_id, cc_id, cc_id,
            cc_num, '', expiration_date, 1, repeat=repeat)
        self._post(params)

    def one_click_pay(self, trans_id, user_id, order_id,
                      cc_token, expiration_date, amount,
                      currency, repeat=False):
        params = self._paybox_direct_params(
            '00053', user_id, trans_id, order_id,
            cc_token, '', expiration_date, amount, repeat=repeat)
        return self._post(params)

    def _paybox_direct_params(
            self, req_type, user_id, seq_id, refs_id,
            cc_num, cvc, expiration_date, amount, currency='EUR',
            repeat=False):
        data = {
            'VERSION': '00104',
            'SITE': settings.PAYBOX_SITE,
            'RANG': settings.PAYBOX_RANG,
            'CLE': settings.PAYBOX_CLE,
            'ACTIVITE': '024',
            'DATEQ': datetime.now().strftime('%d%m%Y%H%M%S'),

            'TYPE': req_type,
            'NUMQUESTION': seq_id,
            'PORTEUR': cc_num,
            'CVV': cvc,
            'DATEVAL': expiration_date,
            'MONTANT': int(amount * 100),
            'DEVISE': CUR_CODE.toDict().get(currency, ''),
            'REFABONNE': user_id,
            'REFERENCE': refs_id,
        }
        if repeat:
            data['ACTIVITE'] = '027'
        return data
